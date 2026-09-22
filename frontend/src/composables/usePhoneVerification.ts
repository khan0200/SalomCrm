/**
 * usePhoneVerification — Firebase Phone Auth composable
 *
 * Shartnoma sahifasida phone1 va guardian_phone ni SMS OTP bilan tasdiqlash uchun
 * qayta ishlatiladigan composable. Har bir telefon turi uchun alohida instance
 * yaratilishi mumkin (phone_type parametri orqali).
 *
 * Ishlatilishi:
 *   const phone1Verifier = usePhoneVerification('phone1', tenantSlug)
 *   const guardianVerifier = usePhoneVerification('guardian_phone', tenantSlug)
 *
 *   await phone1Verifier.sendOtp('+998901234567')
 *   await phone1Verifier.confirmOtp('123456')
 *   const token = phone1Verifier.sessionToken.value
 */

import { ref, computed } from 'vue'
import {
  RecaptchaVerifier,
  signInWithPhoneNumber,
  type ConfirmationResult,
} from 'firebase/auth'
import { auth } from '@/lib/firebase'
import apiClient from '@/api/client'

export type PhoneType = 'phone1' | 'guardian_phone'

export interface PhoneVerificationState {
  isVerified: boolean
  sessionToken: string
  phone: string
}

export function usePhoneVerification(phoneType: PhoneType, tenantSlug: string) {
  // State
  const step = ref<'idle' | 'sending' | 'code_sent' | 'verifying' | 'verified'>('idle')
  const loading = ref(false)
  const error = ref<string | null>(null)
  const sessionToken = ref<string | null>(null)
  const verifiedPhone = ref<string | null>(null)

  // Firebase internals
  let confirmationResult: ConfirmationResult | null = null
  let recaptchaVerifier: RecaptchaVerifier | null = null

  const isVerified = computed(() => step.value === 'verified' && !!sessionToken.value)

  /**
   * reCAPTCHA container element'ini render qiladi.
   * `containerId` — HTML da id="..." bo'lgan element.
   * Masalan: <div id="recaptcha-phone1"></div>
   */
  function initRecaptcha(containerId: string) {
    // Eski instance'ni tozalash
    if (recaptchaVerifier) {
      try {
        recaptchaVerifier.clear()
      } catch {
        // ignore
      }
      recaptchaVerifier = null
    }

    recaptchaVerifier = new RecaptchaVerifier(auth, containerId, {
      size: 'invisible',
      callback: () => {
        // reCAPTCHA muvaffaqiyatli — SMS yuboriladi
      },
      'expired-callback': () => {
        error.value = 'reCAPTCHA muddati tugadi. Qayta urinib ko\'ring.'
        step.value = 'idle'
      },
    })
  }

  /**
   * Telefon raqamga SMS OTP yuboradi.
   * @param phone — local format "90-123-45-67" yoki E.164 "+998901234567"
   * @param containerId — reCAPTCHA container element ID (default: 'recaptcha-container')
   */
  async function sendOtp(phone: string, containerId = 'recaptcha-container') {
    loading.value = true
    error.value = null
    step.value = 'sending'

    try {
      // E.164 formatga o'tkazish (O'zbekiston +998 yoki xalqaro raqamlar, masalan +82 Koreya)
      const trimmed = phone.trim()
      const allDigits = trimmed.replace(/\D/g, '')
      let e164Phone = ''

      if (trimmed.startsWith('+998') || trimmed.startsWith('998') || (!trimmed.startsWith('+') && allDigits.length === 9)) {
        const uzDigits = allDigits.replace(/^998/, '').slice(0, 9)
        if (uzDigits.length !== 9) {
          throw new Error("O'zbekiston telefon raqami 9 ta raqamdan iborat bo'lishi kerak.")
        }
        e164Phone = `+998${uzDigits}`
      } else if (trimmed.startsWith('+')) {
        if (allDigits.length < 7 || allDigits.length > 15) {
          throw new Error("Xalqaro telefon raqami kamida 7 va ko'pi bilan 15 ta raqamdan iborat bo'lishi kerak.")
        }
        e164Phone = `+${allDigits}`
      } else {
        if (allDigits.length < 7 || allDigits.length > 15) {
          throw new Error("Telefon raqami noto'g'ri formatda kiritildi.")
        }
        e164Phone = `+${allDigits}`
      }

      initRecaptcha(containerId)

      confirmationResult = await signInWithPhoneNumber(auth, e164Phone, recaptchaVerifier!)
      step.value = 'code_sent'
    } catch (err: any) {
      step.value = 'idle'
      // Firebase xato kodlarini o'zbekchaga tarjima qilish
      const code = err?.code || ''
      if (code === 'auth/invalid-phone-number') {
        error.value = 'Telefon raqam noto\'g\'ri formatda.'
      } else if (code === 'auth/too-many-requests') {
        error.value = 'Juda ko\'p urinish. Bir oz kutib qayta urinib ko\'ring.'
      } else if (code === 'auth/quota-exceeded') {
        error.value = 'SMS kvotasi tugagan. Administratorga murojaat qiling.'
      } else if (code === 'auth/operation-not-allowed' || String(err?.message || '').includes('SMS unable to be sent until this region enabled')) {
        error.value = 'Firebase: Ushbu davlat (hudud) uchun SMS yuborish yoqilmagan (SMS Region Policy). Iltimos, Firebase konsolida ushbu davlatni yoqing yoki test raqamlari ro\'yxatiga qo\'shing.'
      } else {
        error.value = err?.message || 'SMS yuborishda xatolik yuz berdi.'
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Foydalanuvchi kiritgan OTP kodni tekshiradi va backend'da session_token oladi.
   * @param code — 6 xonali OTP kod
   * @param phoneLocal — foydalanuvchi kiritgan raqam (local format) — backend matching uchun
   */
  async function confirmOtp(code: string, phoneLocal: string) {
    if (!confirmationResult) {
      error.value = 'Avval SMS kodni yuboring.'
      return
    }

    loading.value = true
    error.value = null
    step.value = 'verifying'

    try {
      // 1. Firebase client-side verification
      const credential = await confirmationResult.confirm(code)
      const idToken = await credential.user.getIdToken()

      // 2. Backend server-side verification → session_token olish
      const { data } = await apiClient.post('/contracts/online/verify-phone/', {
        id_token: idToken,
        phone: phoneLocal,
        phone_type: phoneType,
        tenant_slug: tenantSlug,
      })

      sessionToken.value = data.session_token
      verifiedPhone.value = data.phone
      step.value = 'verified'

      return data
    } catch (err: any) {
      step.value = 'code_sent'  // kod kiritish sahifasida qolsin

      const firebaseCode = err?.code || ''
      if (firebaseCode === 'auth/invalid-verification-code') {
        error.value = 'Tasdiqlash kodi noto\'g\'ri. Qayta kiriting.'
      } else if (firebaseCode === 'auth/code-expired') {
        error.value = 'Tasdiqlash kodining muddati tugagan. Yangi kod so\'rang.'
      } else {
        // Backend xatosi yoki boshqa xato
        error.value = err?.response?.data?.detail || err?.message || 'Tasdiqlashda xatolik yuz berdi.'
      }
      throw err
    } finally {
      loading.value = false
    }
  }

  /** Holatni reset qilish (boshqa raqam kiritmoqchi bo'lganda) */
  function reset() {
    step.value = 'idle'
    error.value = null
    sessionToken.value = null
    verifiedPhone.value = null
    confirmationResult = null
    if (recaptchaVerifier) {
      try { recaptchaVerifier.clear() } catch { /* ignore */ }
      recaptchaVerifier = null
    }
  }

  return {
    // State
    step,
    loading,
    error,
    isVerified,
    sessionToken,
    verifiedPhone,
    // Methods
    sendOtp,
    confirmOtp,
    reset,
  }
}
