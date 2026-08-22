<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { X, RefreshCw, AlertTriangle, Fingerprint, User2, Cake, Hash, ShieldCheck, Database, CheckCircle2 } from 'lucide-vue-next'
import { visaApi, type VisaType, type VisaStudent } from '@/api/visa'
import { useUiStore } from '@/stores/ui'

const uiStore = useUiStore()

const props = defineProps<{
  isOpen: boolean
  editingStudent?: VisaStudent | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const isEdit = computed(() => Boolean(props.editingStudent))
const submitting = ref(false)
const checkingVisa = ref(false)
const isLookingUp = ref(false)
const autofilledFromMain = ref(false)
const errorMessage = ref('')
const spaceWarning = ref(false)
let spaceWarningTimer: any = null
let lookupTimer: any = null

const form = reactive({
  fullName: '',
  passport: '',
  birthday: '',
  studentId: '',
  visaType: 'Embassy' as VisaType,
  applicationNo: '',
  tariff: '',
  university: ''
})

function formatPassportInput(raw: string): string {
  return raw.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 20)
}

function formatDateInput(raw: string): string {
  let value = raw.replace(/\D/g, '')
  if (value.length > 8) value = value.slice(0, 8)
  if (value.length > 4) value = `${value.slice(0, 4)}-${value.slice(4)}`
  if (value.length > 7) value = `${value.slice(0, 7)}-${value.slice(7)}`
  return value
}

function formatNameInput(raw: string): string {
  return (raw || '').toUpperCase().replace(/^\s+/g, '').replace(/\s{2,}/g, ' ')
}

function showSpaceWarning() {
  spaceWarning.value = true
  if (spaceWarningTimer) clearTimeout(spaceWarningTimer)
  spaceWarningTimer = setTimeout(() => { spaceWarning.value = false }, 3000)
}

function handleFullNameKeydown(e: KeyboardEvent) {
  if (e.key === ' ' || e.code === 'Space') {
    const input = e.target as HTMLInputElement
    const selStart = input.selectionStart || 0
    if (selStart === 0 || input.value.slice(selStart - 1, selStart) === ' ') {
      e.preventDefault()
      showSpaceWarning()
    }
  }
}

function handleFullNameInput(e: Event) {
  const input = e.target as HTMLInputElement
  const raw = input.value
  if (/\s{2,}/.test(raw) || /^\s+/.test(raw)) showSpaceWarning()
  const formatted = formatNameInput(raw)
  form.fullName = formatted
  if (input.value !== formatted) input.value = formatted
}

function handlePassportInput(e: Event) {
  const input = e.target as HTMLInputElement
  const val = formatPassportInput(input.value)
  form.passport = val

  // Auto-lookup in main database when creating a new student
  if (!isEdit.value && val.length >= 5) {
    if (lookupTimer) clearTimeout(lookupTimer)
    lookupTimer = setTimeout(triggerMainDbLookup, 400)
  }
}

async function triggerMainDbLookup() {
  const pp = form.passport.trim().toUpperCase()
  if (pp.length < 5 || isEdit.value) return

  isLookingUp.value = true
  try {
    const res = await visaApi.lookupMainDatabase(pp)
    if (res.found && res.student) {
      if (!form.fullName || autofilledFromMain.value) form.fullName = res.student.full_name || ''
      if (!form.birthday || autofilledFromMain.value) form.birthday = res.student.birthday || ''
      if (!form.studentId || autofilledFromMain.value) form.studentId = res.student.id || ''
      if (res.student.tariff) form.tariff = res.student.tariff
      if (res.student.university) form.university = res.student.university
      autofilledFromMain.value = true
    } else {
      autofilledFromMain.value = false
    }
  } catch {
    autofilledFromMain.value = false
  } finally {
    isLookingUp.value = false
  }
}

function handleBirthdayInput(e: Event) {
  const input = e.target as HTMLInputElement
  const formatted = formatDateInput(input.value)
  form.birthday = formatted
  if (input.value !== formatted) input.value = formatted
}

function setVisaType(value: VisaType) {
  form.visaType = value
  if (value !== 'E-Visa' && value !== 'Regional') form.applicationNo = ''
}

function resetForm() {
  form.fullName = ''
  form.passport = ''
  form.birthday = ''
  form.studentId = ''
  form.visaType = 'Embassy'
  form.applicationNo = ''
  form.tariff = ''
  form.university = ''
  errorMessage.value = ''
  spaceWarning.value = false
  autofilledFromMain.value = false
  isLookingUp.value = false
}

watch(() => props.isOpen, (open) => {
  if (!open) { resetForm(); return }
  if (props.editingStudent) {
    const s = props.editingStudent
    form.fullName = s.full_name || ''
    form.passport = s.passport || ''
    form.birthday = s.birthday || ''
    form.studentId = s.student_id || s.id || ''
    form.visaType = s.visa_type || 'Embassy'
    form.applicationNo = s.application_no || ''
    form.tariff = s.tariff || ''
    form.university = s.university || ''
  } else {
    resetForm()
  }
})

async function handleSubmit() {
  errorMessage.value = ''
  const fullName = form.fullName.replace(/\s+/g, ' ').trim().toUpperCase()
  const passport = form.passport.toUpperCase().trim()
  const birthday = form.birthday.trim()

  if (!fullName) { errorMessage.value = 'Talaba to\'liq ismini kiriting.'; return }
  if (!passport || !/^[A-Z0-9]{5,20}$/.test(passport)) {
    errorMessage.value = 'Pasport formati to\'g\'ri emas (masalan, FA1234567).'
    return
  }
  if (!birthday || !/^\d{4}-\d{2}-\d{2}$/.test(birthday)) {
    errorMessage.value = 'Tug\'ilgan sana YYYY-MM-DD formatida bo\'lishi kerak.'
    return
  }

  submitting.value = true
  try {
    const payload: Partial<VisaStudent> = {
      full_name: fullName,
      passport,
      birthday,
      visa_type: form.visaType,
      application_no: form.applicationNo ? form.applicationNo.trim().toUpperCase() : ''
    }
    if (form.studentId.trim()) payload.student_id = form.studentId.trim().toUpperCase()
    if (form.tariff.trim()) payload.tariff = form.tariff.trim()
    if (form.university.trim()) payload.university = form.university.trim()

    // Isolated VisaStudent database operation
    if (isEdit.value && props.editingStudent) {
      await visaApi.updateVisaStudent(props.editingStudent.passport, payload)
    } else {
      await visaApi.createVisaStudent(payload)
    }

    submitting.value = false
    checkingVisa.value = true

    // Check visa status on visa.go.kr and auto-persist to Visa database
    try {
      await visaApi.checkVisa({
        passport,
        full_name: fullName,
        birth_date: birthday,
        visa_type: form.visaType,
        application_no: form.applicationNo ? form.applicationNo.trim().toUpperCase() : undefined
      })
    } catch { /* non-blocking */ }
    finally { checkingVisa.value = false }

    uiStore.addToast({
      type: 'success',
      message: isEdit.value ? 'Talaba yangilandi ✓' : 'Talaba qo\'shildi va viza tekshirildi ✓'
    })

    emit('saved')
    emit('close')
  } catch (err: any) {
    errorMessage.value = err.response?.data?.error || err.message || 'Xatolik yuz berdi.'
    submitting.value = false
    checkingVisa.value = false
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        class="visacheck-page fixed inset-0 z-[60] flex items-end sm:items-center justify-center sm:p-4"
        @mousedown.self="emit('close')"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" />

        <!-- Sheet / Modal -->
        <Transition
          enter-active-class="transition duration-300 ease-[cubic-bezier(0.32,0.72,0,1)]"
          enter-from-class="translate-y-full sm:translate-y-0 sm:scale-95 sm:opacity-0"
          enter-to-class="translate-y-0 sm:scale-100 sm:opacity-100"
          leave-active-class="transition duration-200 ease-in"
          leave-from-class="translate-y-0 sm:scale-100 sm:opacity-100"
          leave-to-class="translate-y-full sm:translate-y-0 sm:scale-95 sm:opacity-0"
        >
          <div
            v-if="isOpen"
            class="relative w-full sm:max-w-md bg-white dark:bg-[#141618] rounded-t-xl sm:rounded-lg shadow-2xl overflow-hidden flex flex-col max-h-[92vh]"
          >
            <!-- Drag pill (mobile) -->
            <div class="flex justify-center pt-3 pb-1 sm:hidden">
              <div class="w-10 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700" />
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-3">
              <div>
                <h2 class="text-base font-bold tracking-tight text-zinc-900 dark:text-white">
                  {{ isEdit ? 'Edit Student' : 'New Student' }}
                </h2>
                <p class="text-[11px] text-zinc-400">
                  {{ isEdit ? 'Talaba ma\'lumotlarini tahrirlash' : 'Visa Check bazasiga talaba qo\'shish' }}
                </p>
              </div>
              <button
                type="button"
                @click="emit('close')"
                class="size-8 rounded-md flex items-center justify-center bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-colors"
              >
                <X class="size-4" />
              </button>
            </div>

            <!-- Divider -->
            <div class="h-px bg-zinc-100 dark:bg-zinc-800 mx-5" />

            <!-- Form Body -->
            <form @submit.prevent="handleSubmit" class="overflow-y-auto flex-1 px-5 py-3 space-y-3">

              <!-- Visa Type Segment -->
              <div>
                <p class="text-[10px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-widest mb-1.5">Visa Type</p>
                <div class="flex gap-2">
                  <button
                    v-for="vt in ['Embassy', 'E-Visa', 'Regional']"
                    :key="vt"
                    type="button"
                    @click="setVisaType(vt as VisaType)"
                    class="flex-1 py-2 rounded-md text-xs font-bold transition-all border"
                    :class="form.visaType === vt
                      ? 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 border-transparent shadow-sm'
                      : 'bg-transparent text-zinc-500 dark:text-zinc-400 border-zinc-200 dark:border-zinc-700 hover:border-zinc-400 dark:hover:border-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200'"
                  >
                    {{ vt }}
                  </button>
                </div>
              </div>

              <!-- Passport Input -->
              <div class="space-y-1">
                <div class="flex items-center justify-between">
                  <label class="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-600 dark:text-zinc-400">
                    <Fingerprint class="size-3 text-zinc-400" />
                    Passport Number
                    <span class="text-rose-400 ml-0.5">*</span>
                  </label>
                  <span v-if="isLookingUp" class="text-[10px] text-blue-500 flex items-center gap-1">
                    <RefreshCw class="size-2.5 animate-spin" /> Qidirilmoqda...
                  </span>
                </div>
                <input
                  type="text"
                  :value="form.passport"
                  @input="handlePassportInput"
                  placeholder="FA1234567"
                  required
                  autocomplete="off"
                  class="w-full h-10 px-3.5 rounded-md border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white font-mono text-sm tracking-widest uppercase placeholder-zinc-400 focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-500 focus:bg-white dark:focus:bg-zinc-800 transition-all"
                />

                <!-- Autofill banner if found in main DB -->
                <Transition
                  enter-active-class="transition-all duration-200"
                  enter-from-class="opacity-0 -translate-y-1"
                  enter-to-class="opacity-100 translate-y-0"
                >
                  <div v-if="autofilledFromMain" class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md bg-emerald-50 dark:bg-emerald-950/30 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-[11px] font-medium">
                    <CheckCircle2 class="size-3.5 shrink-0 text-emerald-600" />
                    <span>Asosiy CRM bazasidan topildi va to'ldirildi ✓</span>
                  </div>
                </Transition>
              </div>

              <!-- Full Name -->
              <div class="space-y-1">
                <label class="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-600 dark:text-zinc-400">
                  <User2 class="size-3 text-zinc-400" />
                  Full Name
                  <span class="text-rose-400 ml-0.5">*</span>
                  <span class="ml-auto text-[10px] font-normal text-zinc-400">Pasportdagi kabi</span>
                </label>
                <input
                  type="text"
                  :value="form.fullName"
                  @input="handleFullNameInput"
                  @keydown="handleFullNameKeydown"
                  placeholder="ABDUVOHIDOV KUVONCHBEK"
                  required
                  autocomplete="off"
                  class="w-full h-10 px-3.5 rounded-md border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white text-sm uppercase placeholder-zinc-400 focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-500 focus:bg-white dark:focus:bg-zinc-800 transition-all"
                />
                <Transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
                  <div v-if="spaceWarning" class="flex items-center gap-1.5 text-amber-600 dark:text-amber-400 text-[11px] font-medium">
                    <AlertTriangle class="size-3 shrink-0" />
                    Ketma-ket probel taqiqlangan
                  </div>
                </Transition>
              </div>

              <!-- Birthday -->
              <div class="space-y-1">
                <label class="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-600 dark:text-zinc-400">
                  <Cake class="size-3 text-zinc-400" />
                  Birthday
                  <span class="text-rose-400 ml-0.5">*</span>
                  <span class="ml-auto text-[10px] font-mono text-zinc-400">YYYY-MM-DD</span>
                </label>
                <input
                  type="text"
                  :value="form.birthday"
                  @input="handleBirthdayInput"
                  placeholder="2004-05-12"
                  maxlength="10"
                  required
                  autocomplete="off"
                  class="w-full h-10 px-3.5 rounded-md border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white font-mono text-sm placeholder-zinc-400 focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-500 focus:bg-white dark:focus:bg-zinc-800 transition-all"
                />
              </div>

              <!-- Application No (conditional) -->
              <Transition
                enter-active-class="transition-all duration-200 overflow-hidden"
                enter-from-class="opacity-0 max-h-0"
                enter-to-class="opacity-100 max-h-24"
                leave-active-class="transition-all duration-150 overflow-hidden"
                leave-from-class="opacity-100 max-h-24"
                leave-to-class="opacity-0 max-h-0"
              >
                <div v-if="form.visaType === 'E-Visa' || form.visaType === 'Regional'" class="space-y-1">
                  <label class="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-600 dark:text-zinc-400">
                    <Hash class="size-3 text-zinc-400" />
                    Application Number
                  </label>
                  <input
                    type="text"
                    v-model="form.applicationNo"
                    placeholder="AP2026123456"
                    autocomplete="off"
                    class="w-full h-10 px-3.5 rounded-md border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white font-mono uppercase text-sm placeholder-zinc-400 focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-500 focus:bg-white dark:focus:bg-zinc-800 transition-all"
                  />
                </div>
              </Transition>

              <!-- Student ID -->
              <div class="space-y-1">
                <label class="flex items-center gap-1.5 text-[11px] font-semibold text-zinc-600 dark:text-zinc-400">
                  <Hash class="size-3 text-zinc-400" />
                  Student ID
                  <span class="ml-auto text-[10px] font-normal text-zinc-400">Ixtiyoriy</span>
                </label>
                <input
                  type="text"
                  v-model="form.studentId"
                  placeholder="M445"
                  autocomplete="off"
                  class="w-full h-10 px-3.5 rounded-md border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-900 text-zinc-900 dark:text-white font-mono uppercase text-sm placeholder-zinc-400 focus:outline-none focus:border-zinc-400 dark:focus:border-zinc-500 focus:bg-white dark:focus:bg-zinc-800 transition-all"
                />
              </div>

              <!-- Error -->
              <Transition enter-active-class="transition-all duration-200" enter-from-class="opacity-0 -translate-y-1" enter-to-class="opacity-100 translate-y-0">
                <div v-if="errorMessage" class="flex items-start gap-2.5 p-3 rounded-md bg-rose-50 dark:bg-rose-950/30 border border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs">
                  <AlertTriangle class="size-4 shrink-0 mt-0.5 text-rose-500" />
                  <span>{{ errorMessage }}</span>
                </div>
              </Transition>
            </form>

            <!-- Footer -->
            <div class="px-5 pb-4 pt-2 flex items-center gap-2.5">
              <!-- Cancel -->
              <button
                type="button"
                @click="emit('close')"
                :disabled="submitting || checkingVisa"
                class="h-10 px-4 rounded-md text-sm font-semibold text-zinc-600 dark:text-zinc-300 bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 transition-all disabled:opacity-40 select-none shrink-0"
              >
                Bekor
              </button>

              <!-- Submit -->
              <button
                type="button"
                @click="handleSubmit"
                :disabled="submitting || checkingVisa"
                class="flex-1 h-10 rounded-md text-sm font-bold transition-all flex items-center justify-center gap-2 disabled:opacity-60 select-none active:scale-[0.98]"
                :class="checkingVisa
                  ? 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30'
                  : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/30'"
              >
                <template v-if="checkingVisa">
                  <ShieldCheck class="size-4 animate-pulse" />
                  <span>Tekshirilmoqda...</span>
                </template>
                <template v-else-if="submitting">
                  <RefreshCw class="size-4 animate-spin" />
                  <span>Saqlanmoqda...</span>
                </template>
                <template v-else>
                  <span>{{ isEdit ? 'Saqlash' : 'Qo\'shish va Tekshirish' }}</span>
                </template>
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>
