<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import {
  Building2,
  Landmark,
  User,
  Phone,
  MapPin,
  CreditCard,
  Hash,
  FileText,
  Pencil,
  Check,
  Copy,
  Save,
  X,
  Loader2,
  ShieldCheck
} from 'lucide-vue-next'
import { tenantsApi } from '@/api/tenants'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

export interface AgencyRequisites {
  company_name: string
  director_name: string
  inn: string
  oked: string
  certificate_number: string
  phone: string
  address: string
  bank_name: string
  bank_account: string
  mfo: string
}

const SODIQ_REQUISITES: AgencyRequisites = {
  company_name: '"UNIGATE" MAS\'ULIYATI CHEKLANGAN JAMIYAT',
  director_name: 'Abdug’afforov Sodiqjon Baxodir o’g’li',
  inn: '310785901',
  oked: '',
  certificate_number: '',
  phone: '(+998) 88 778-00-88',
  address: "Andijon viloyati, Andijon Shahar, O’zbegim MFY, Buyuk Turon ko’chasi, 4-uy, 16-xonadon",
  bank_name: 'SQB - Sanoat Qurilish Bank - Andijon BХO',
  bank_account: '2020 8000 3056 9675 2001',
  mfo: '00440'
}

const UNIBRIDGE_REQUISITES: AgencyRequisites = {
  company_name: 'MCHJ "IT STATION"',
  director_name: 'ABDULPATTAYEV M.A',
  inn: '309 961 634',
  oked: '62010',
  certificate_number: '5114456, 1995739',
  phone: '+998 93 105 0011',
  address: 'Andijon viloyati, Marxamat tumani, Marxamat shahri Barhayot MFY, А.Тemur ko`chasi',
  bank_name: 'UzMilliy Toshkent Filliali',
  bank_account: '2020 8000 9055 7879 0001',
  mfo: '00450'
}

const DEFAULT_REQUISITES: AgencyRequisites = UNIBRIDGE_REQUISITES

const props = defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'updated', requisites: AgencyRequisites): void
}>()

const authStore = useAuthStore()
const uiStore = useUiStore()

const isEditing = ref(false)
const isLoading = ref(false)
const isSaving = ref(false)
const copiedField = ref<string | null>(null)

const form = ref<AgencyRequisites>({ ...DEFAULT_REQUISITES })
const savedData = ref<AgencyRequisites>({ ...DEFAULT_REQUISITES })

const tenantId = computed(() => {
  return (
    // Super Admin "viewing as" another tenant must win - the admin's own
    // `user.tenant` is null, so this used to always fall through to the
    // hardcoded 'unibridge' default below regardless of the active tenant.
    authStore.activeTenantId ||
    authStore.currentTenant?.id ||
    (authStore.user?.tenant as any)?.id ||
    (typeof authStore.user?.tenant === 'string' ? authStore.user.tenant : '') ||
    'unibridge'
  )
})

async function loadRequisites() {
  if (!tenantId.value) return
  isLoading.value = true
  try {
    const tenant = await tenantsApi.getTenant(tenantId.value)
    const isSodiq = tenantId.value === 'sodiq' || tenant?.slug === 'sodiq'
    const fallback = isSodiq ? SODIQ_REQUISITES : UNIBRIDGE_REQUISITES

    const req = tenant?.settings?.requisites as Partial<AgencyRequisites> | undefined
    if (req && typeof req === 'object') {
      const merged: AgencyRequisites = {
        company_name: req.company_name || fallback.company_name,
        director_name: req.director_name || fallback.director_name,
        inn: req.inn || fallback.inn,
        oked: req.oked !== undefined ? req.oked : fallback.oked,
        certificate_number: req.certificate_number !== undefined ? req.certificate_number : fallback.certificate_number,
        phone: req.phone || fallback.phone,
        address: req.address || fallback.address,
        bank_name: req.bank_name || fallback.bank_name,
        bank_account: req.bank_account || fallback.bank_account,
        mfo: req.mfo || fallback.mfo,
      }
      form.value = { ...merged }
      savedData.value = { ...merged }
    } else {
      form.value = { ...fallback }
      savedData.value = { ...fallback }
    }
  } catch (err) {
    console.error('Failed to load agency requisites:', err)
  } finally {
    isLoading.value = false
  }
}

watch(
  () => props.isOpen,
  (val) => {
    if (val) {
      isEditing.value = false
      loadRequisites()
    }
  },
  { immediate: true }
)

function handleCancelEdit() {
  form.value = { ...savedData.value }
  isEditing.value = false
}

async function handleSave() {
  if (!tenantId.value) return
  isSaving.value = true
  try {
    await tenantsApi.updateTenant(tenantId.value, {
      settings: {
        requisites: { ...form.value }
      }
    })

    savedData.value = { ...form.value }
    isEditing.value = false

    // Update local store reference if available
    if (authStore.currentTenant && typeof authStore.currentTenant === 'object') {
      if (!authStore.currentTenant.settings) {
        authStore.currentTenant.settings = {}
      }
      authStore.currentTenant.settings.requisites = { ...form.value }
    }

    emit('updated', form.value)

    uiStore.addToast({
      type: 'success',
      title: 'Rekvizitlar saqlandi',
      message: 'Agentlik rekvizitlari muvaffaqiyatli yangilandi.',
      duration: 3500
    })
  } catch (err: any) {
    console.error('Failed to update requisites:', err)
    uiStore.addToast({
      type: 'error',
      title: 'Xatolik',
      message: err?.response?.data?.detail || 'Rekvizitlarni saqlashda xatolik yuz berdi.',
      duration: 4000
    })
  } finally {
    isSaving.value = false
  }
}

async function copyToClipboard(key: string, text: string) {
  if (!text) return
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(text)
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
    copiedField.value = key
    setTimeout(() => {
      if (copiedField.value === key) {
        copiedField.value = null
      }
    }, 2000)
  } catch (err) {
    console.error('Copy failed:', err)
  }
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="Agentlik Rekvizitlari"
    subtitle="Shartnomalar va rasmiy hujjatlarda ishlatiladigan korxona ma'lumotlari"
    max-width="max-w-2xl"
    @close="emit('close')"
  >
    <!-- Loading State -->
    <div v-if="isLoading" class="py-12 flex flex-col items-center justify-center gap-3">
      <Loader2 class="w-8 h-8 text-blue-600 animate-spin" />
      <p class="text-xs text-zinc-500 font-medium">Rekvizitlar yuklanmoqda...</p>
    </div>

    <div v-else class="space-y-5">
      <!-- Top banner / Mode Switcher -->
      <div class="flex items-center justify-between p-3 rounded-xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/40">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-blue-600/10 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <Building2 class="w-4 h-4" />
          </div>
          <div>
            <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
              {{ form.company_name || 'Agentlik nomi' }}
            </div>
            <div class="text-[11px] text-zinc-500 dark:text-zinc-400 flex items-center gap-2 mt-0.5">
              <span>INN: {{ form.inn || '—' }}</span>
              <span class="inline-block w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700"></span>
              <span>MFO: {{ form.mfo || '—' }}</span>
            </div>
          </div>
        </div>

        <button
          v-if="!isEditing"
          type="button"
          @click="isEditing = true"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 border border-zinc-200 dark:border-zinc-700 text-xs font-semibold shadow-2xs transition-all cursor-pointer select-none"
        >
          <Pencil class="w-3.5 h-3.5 text-zinc-500" />
          <span>Tahrirlash</span>
        </button>

        <span
          v-else
          class="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 text-[11px] font-semibold"
        >
          Tahrirlash rejimi
        </span>
      </div>

      <!-- VIEW MODE: Clean, copyable cards -->
      <div v-if="!isEditing" class="grid grid-cols-1 md:grid-cols-2 gap-3">
        <!-- 1. Tashkilot nomi -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              Korxona / Agentlik nomi
            </span>
            <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block break-words">
              {{ form.company_name || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('company_name', form.company_name)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'company_name' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'company_name'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 2. Direktor -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              Direktor F.I.Sh
            </span>
            <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block truncate">
              {{ form.director_name || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('director_name', form.director_name)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'director_name' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'director_name'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 3. INN (STIR) -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              INN (STIR)
            </span>
            <span class="text-xs font-mono font-bold text-zinc-900 dark:text-zinc-100 block">
              {{ form.inn || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('inn', form.inn)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'inn' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'inn'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 4. OKED -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              OKED kodi
            </span>
            <span class="text-xs font-mono font-bold text-zinc-900 dark:text-zinc-100 block">
              {{ form.oked || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('oked', form.oked)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'oked' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'oked'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 5. Guvohnoma raqami -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              Guvohnoma (Litsenziya)
            </span>
            <span class="text-xs font-mono font-bold text-zinc-900 dark:text-zinc-100 block">
              {{ form.certificate_number || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('certificate_number', form.certificate_number)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'certificate_number' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'certificate_number'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 6. Telefon raqami -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              Telefon raqami
            </span>
            <span class="text-xs font-mono font-bold text-zinc-900 dark:text-zinc-100 block">
              {{ form.phone || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('phone', form.phone)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'phone' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'phone'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 7. Bank nomi -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group md:col-span-2">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              Xizmat ko'rsatuvchi Bank va Filial
            </span>
            <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block">
              {{ form.bank_name || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('bank_name', form.bank_name)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'bank_name' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'bank_name'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 8. Hisob raqami (H/R) -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              Hisob raqami (H/R)
            </span>
            <span class="text-xs font-mono font-bold text-blue-600 dark:text-blue-400 block tracking-wider">
              {{ form.bank_account || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('bank_account', form.bank_account)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'bank_account' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'bank_account'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 9. MFO -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              Bank MFO kodi
            </span>
            <span class="text-xs font-mono font-bold text-zinc-900 dark:text-zinc-100 block">
              {{ form.mfo || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('mfo', form.mfo)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'mfo' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'mfo'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>

        <!-- 10. Yuridik Manzil -->
        <div class="p-3 rounded-xl bg-zinc-50 dark:bg-zinc-850/60 border border-zinc-200/70 dark:border-zinc-800 flex items-start justify-between gap-2 group md:col-span-2">
          <div class="min-w-0">
            <span class="text-[10px] font-medium uppercase tracking-wider text-zinc-400 block mb-0.5">
              Yuridik manzil
            </span>
            <span class="text-xs font-medium text-zinc-800 dark:text-zinc-200 block">
              {{ form.address || '—' }}
            </span>
          </div>
          <button
            type="button"
            @click="copyToClipboard('address', form.address)"
            class="p-1 rounded text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-200/60 dark:hover:bg-zinc-750 transition-colors shrink-0 cursor-pointer"
            :title="copiedField === 'address' ? 'Nusxalandi' : 'Nusxalash'"
          >
            <Check v-if="copiedField === 'address'" class="w-3.5 h-3.5 text-emerald-500" />
            <Copy v-else class="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <!-- EDIT MODE: Structured inputs -->
      <form v-else @submit.prevent="handleSave" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          <!-- Company Name -->
          <div class="md:col-span-2 space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              Korxona / Agentlik nomi <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.company_name"
              type="text"
              required
              placeholder="Masalan: MCHJ 'IT STATION' (UniBridge)"
              class="w-full px-3 py-1.5 text-xs rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <!-- Director -->
          <div class="space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              Direktor F.I.Sh <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.director_name"
              type="text"
              required
              placeholder="Masalan: ABDULPATTAYEV M.A"
              class="w-full px-3 py-1.5 text-xs rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors uppercase"
            />
          </div>

          <!-- Phone -->
          <div class="space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              Telefon raqami
            </label>
            <input
              v-model="form.phone"
              type="text"
              placeholder="+998 93 105 0011"
              class="w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <!-- INN -->
          <div class="space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              INN (STIR) <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.inn"
              type="text"
              required
              placeholder="309 961 634"
              class="w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <!-- OKED -->
          <div class="space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              OKED kodi
            </label>
            <input
              v-model="form.oked"
              type="text"
              placeholder="62010"
              class="w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <!-- Certificate -->
          <div class="md:col-span-2 space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              Guvohnoma (Litsenziya) raqami
            </label>
            <input
              v-model="form.certificate_number"
              type="text"
              placeholder="5114456, 1995739"
              class="w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <!-- Bank Name -->
          <div class="md:col-span-2 space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              Bank nomi va filiali <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.bank_name"
              type="text"
              required
              placeholder="UZMILLIY TOSHKENT FILIALI (M.O')"
              class="w-full px-3 py-1.5 text-xs rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <!-- Bank Account (H/R) -->
          <div class="space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              Hisob raqami (H/R) <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.bank_account"
              type="text"
              required
              placeholder="2020 8000 9055 7879 0001"
              class="w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <!-- MFO -->
          <div class="space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              MFO kodi <span class="text-red-500">*</span>
            </label>
            <input
              v-model="form.mfo"
              type="text"
              required
              placeholder="00450"
              maxlength="5"
              class="w-full px-3 py-1.5 text-xs font-mono rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <!-- Address -->
          <div class="md:col-span-2 space-y-1">
            <label class="text-[11px] font-bold text-zinc-700 dark:text-zinc-300">
              Yuridik manzil <span class="text-red-500">*</span>
            </label>
            <textarea
              v-model="form.address"
              rows="2"
              required
              placeholder="Andijon viloyati, Marxamat tumani, Marxamat shahri..."
              class="w-full px-3 py-1.5 text-xs rounded-lg border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-blue-500 transition-colors"
            ></textarea>
          </div>
        </div>
      </form>
    </div>

    <!-- Modal Footer -->
    <template #footer>
      <div class="flex items-center justify-between w-full">
        <div class="text-[11px] text-zinc-400 flex items-center gap-1.5">
          <ShieldCheck class="w-3.5 h-3.5 text-blue-500 shrink-0" />
          <span>Barcha shartnomalar va hisob-fakturalarga qo'llaniladi</span>
        </div>

        <div class="flex items-center gap-2">
          <button
            v-if="isEditing"
            type="button"
            @click="handleCancelEdit"
            :disabled="isSaving"
            class="px-3.5 py-1.5 text-xs font-medium text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors cursor-pointer select-none"
          >
            Bekor qilish
          </button>
          <button
            v-if="isEditing"
            type="button"
            @click="handleSave"
            :disabled="isSaving"
            class="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg shadow-xs transition-all cursor-pointer select-none"
          >
            <Loader2 v-if="isSaving" class="w-3.5 h-3.5 animate-spin" />
            <Save v-else class="w-3.5 h-3.5" />
            <span>{{ isSaving ? 'Saqlanmoqda...' : 'Saqlash' }}</span>
          </button>
          <button
            v-else
            type="button"
            @click="emit('close')"
            class="px-4 py-1.5 text-xs font-medium bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-200 rounded-lg transition-colors cursor-pointer select-none"
          >
            Yopish
          </button>
        </div>
      </div>
    </template>
  </BaseModal>
</template>
