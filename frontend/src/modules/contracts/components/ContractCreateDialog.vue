<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import {
  Search,
  Check,
  Copy,
  Globe,
  ArrowRight,
  ArrowLeft,
  ShieldAlert,
} from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'
import { studentsApi } from '@/api/students'
import { contractsApi, type Contract, type ContractCreatePayload } from '@/api/contracts'
import { CONTRACT_TEMPLATES, type ContractTemplate } from '../contractTemplates'
import { resolveContractVariables } from '../utils/contractVariables'
import { useUiStore } from '@/stores/ui'
import type { Student } from '@/types'

const props = withDefaults(defineProps<{
  isOpen: boolean
  initialTemplateKey?: string
  initialContent?: string
}>(), {
  initialTemplateKey: 'STANDART',
  initialContent: ''
})

const emit = defineEmits<{
  close: []
  created: [contract: Contract]
}>()

const uiStore = useUiStore()

// ── Wizard step ──────────────────────────────────────────────────────────
type Step = 'form' | 'preview' | 'done'
const step = ref<Step>('form')

// ── Template ─────────────────────────────────────────────────────────────
const selectedTemplateKey = ref<string>('STANDART')
const templateList = computed(() => {
  const templates = Object.values(CONTRACT_TEMPLATES)
  return [
    ...templates,
    {
      key: 'BLANK',
      title: "Blank Document",
      subtitle: "Write contract text from scratch",
      priceDisplay: "Custom",
      duration: "Unlimited",
      fullText: "<h1>CONTRACT N: ______</h1><p style=\"text-align:center;\"><strong>AGREEMENT</strong></p><p><br></p>"
    } as ContractTemplate
  ]
})
const selectedTemplate = computed(() => {
  return templateList.value.find(t => t.key === selectedTemplateKey.value) || templateList.value[0]
})

// ── Student: live fullname autocomplete ─────────────────────────────────
const fullNameQuery = ref('')
const isNameFocused = ref(false)
const selectedExistingStudent = ref<Student | null>(null)

const { data: suggestData, isFetching: isSuggestLoading } = useQuery({
  queryKey: ['contract-create-student-suggest', fullNameQuery],
  queryFn: () => studentsApi.getStudents({ search: fullNameQuery.value, page_size: 8 }),
  enabled: computed(() => fullNameQuery.value.trim().length >= 2 && !selectedExistingStudent.value),
  staleTime: 1000 * 30,
})

const suggestions = computed<Student[]>(() => {
  if (selectedExistingStudent.value) return []
  return ((suggestData.value as any)?.results || []).slice(0, 8)
})

const showSuggestions = computed(() => isNameFocused.value && fullNameQuery.value.trim().length >= 2 && suggestions.value.length > 0)

function handleNameBlur() {
  setTimeout(() => { isNameFocused.value = false }, 150)
}

function pickExistingStudent(st: Student) {
  selectedExistingStudent.value = st
  fullNameQuery.value = st.full_name
  isNameFocused.value = false

  passportNumber.value = st.passport || ''
  educationLevel.value = st.level || ''
  dateOfBirth.value = st.birthday || ''
  office.value = st.office || ''
  phone1.value = st.phone1 || ''
  phone2.value = st.phone2 || ''
}

// Typing after a match was picked un-picks it, dropping back to manual entry.
watch(fullNameQuery, (val) => {
  if (selectedExistingStudent.value && val !== selectedExistingStudent.value.full_name) {
    selectedExistingStudent.value = null
  }
})

// ── Manual fields (new OR existing - always editable) ───────────────────
const studentIdAssigned = ref('')
const passportNumber = ref('')
const educationLevel = ref('')
const dateOfBirth = ref('')
const office = ref('')
const phone1 = ref('')
const phone2 = ref('')
const tariffPrice = ref<string>('')
const discount = ref<string>('')

const isNewStudent = computed(() => !selectedExistingStudent.value)

// ── Minor detection (mirrors backend's age calc) ─────────────────────────
const isMinor = computed(() => {
  if (!dateOfBirth.value) return false
  const d = new Date(dateOfBirth.value)
  if (isNaN(d.getTime())) return false
  const today = new Date()
  let age = today.getFullYear() - d.getFullYear()
  const hasHadBirthdayThisYear = (today.getMonth() > d.getMonth()) ||
    (today.getMonth() === d.getMonth() && today.getDate() >= d.getDate())
  if (!hasHadBirthdayThisYear) age -= 1
  return age < 18
})

// ── Guardian sub-form (minors only) ──────────────────────────────────────
const guardianFullName = ref('')
const guardianPassportNumber = ref('')
const guardianRelation = ref('')
const guardianPhone = ref('')
const guardianAddress = ref('')

// ── Contract metadata ─────────────────────────────────────────────────────
const customContractNumber = ref('')
const customTitle = ref('')

watch(
  [selectedTemplate, fullNameQuery],
  ([tpl, name]) => {
    const tplTitle = tpl ? tpl.title.replace(' SHARTNOMASI', '') : 'SHARTNOMA'
    customTitle.value = name.trim() ? `${tplTitle} - ${name.trim().toUpperCase()}` : `${tplTitle} SHARTNOMASI`
  }
)

// ── Resolved preview content ──────────────────────────────────────────────
const previewStudentShape = computed(() => ({
  full_name: fullNameQuery.value.trim().toUpperCase(),
  passport_number: passportNumber.value.trim().toUpperCase(),
  date_of_birth: dateOfBirth.value,
  level: educationLevel.value,
  office: office.value,
  phone1: phone1.value,
  phone2: phone2.value,
  tariff_price: tariffPrice.value || selectedTemplate.value?.priceDisplay,
  discount: discount.value || 0,
}))

const previewHtml = computed(() => {
  const templateContent = selectedTemplate.value?.fullText || '<p></p>'
  return resolveContractVariables(
    templateContent,
    previewStudentShape.value,
    {
      contractNumber: customContractNumber.value,
      templateName: selectedTemplate.value?.key,
      price: selectedTemplate.value?.priceDisplay,
    }
  )
})

// ── Validation ─────────────────────────────────────────────────────────────
const errorMessage = ref('')

function validateForm(): string {
  if (!fullNameQuery.value.trim()) return "Talabaning to'liq ismini kiriting"
  if (!passportNumber.value.trim()) return "Pasport raqamini kiriting"
  if (!dateOfBirth.value.trim()) return "Tug'ilgan sanani kiriting"
  if (isNewStudent.value && !studentIdAssigned.value.trim()) return "Yangi talaba uchun Student ID kiriting"
  if (isMinor.value) {
    if (!guardianFullName.value.trim()) return "Kafil (ota-ona/vasiy) F.I.O. kiriting"
    if (!guardianPassportNumber.value.trim()) return "Kafilning pasport raqamini kiriting"
    if (!guardianRelation.value.trim()) return "Kafilning talabaga qarindoshligini kiriting"
    if (!guardianPhone.value.trim()) return "Kafil telefon raqamini kiriting"
    if (!guardianAddress.value.trim()) return "Kafil yashash manzilini kiriting"
  }
  return ''
}

function goToPreview() {
  const err = validateForm()
  if (err) {
    errorMessage.value = err
    return
  }
  errorMessage.value = ''
  step.value = 'preview'
}

// ── Submit / create ────────────────────────────────────────────────────────
const isSubmitting = ref(false)
const createdContract = ref<Contract | null>(null)
const isCopiedSignLink = ref(false)

const signLinkUrl = computed(() => {
  if (!createdContract.value?.sign_token) return ''
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000'
  return `${origin}/sign/${createdContract.value.sign_token}`
})

async function copySignLink() {
  const url = signLinkUrl.value
  if (!url) return
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(url)
    } else {
      const textArea = document.createElement('textarea')
      textArea.value = url
      document.body.appendChild(textArea)
      textArea.select()
      document.execCommand('copy')
      document.body.removeChild(textArea)
    }
    isCopiedSignLink.value = true
    uiStore.addToast({
      type: 'success',
      title: 'Havola nusxalandi!',
      message: `${url} buferga nusxalandi. Talabaga yuborishingiz mumkin.`,
      duration: 4000
    })
    setTimeout(() => { isCopiedSignLink.value = false }, 2500)
  } catch (err) {
    console.error('Failed to copy sign link:', err)
  }
}

async function handleCreate() {
  isSubmitting.value = true
  errorMessage.value = ''

  try {
    const resolvedContent = previewHtml.value

    const payload: ContractCreatePayload = {
      student: selectedExistingStudent.value?.id || null,
      contract_number: customContractNumber.value || undefined,
      title: customTitle.value || 'SHARTNOMA',
      template_name: selectedTemplate.value?.key,
      content: resolvedContent,
      status: 'draft',
      passport_number: passportNumber.value.trim().toUpperCase(),
      full_name: fullNameQuery.value.trim().toUpperCase(),
      education_level: educationLevel.value.trim() || undefined,
      date_of_birth: dateOfBirth.value.trim(),
      office: office.value.trim() || undefined,
      phone1: phone1.value.trim() || undefined,
      phone2: phone2.value.trim() || undefined,
      tariff_name: selectedTemplate.value?.key,
      tariff_price: tariffPrice.value || undefined,
      discount: discount.value || undefined,
    }

    if (isNewStudent.value && studentIdAssigned.value.trim()) {
      payload.student_id_assigned = studentIdAssigned.value.trim().toUpperCase()
    }

    if (isMinor.value) {
      payload.guardian_full_name = guardianFullName.value.trim().toUpperCase()
      payload.guardian_passport_number = guardianPassportNumber.value.trim().toUpperCase()
      payload.guardian_relation = guardianRelation.value.trim()
      payload.guardian_phone = guardianPhone.value.trim()
      payload.guardian_address = guardianAddress.value.trim()
    }

    const created = await contractsApi.createContract(payload)
    createdContract.value = created
    step.value = 'done'
    emit('created', created)
  } catch (err: any) {
    console.error('Failed to create contract:', err)
    errorMessage.value = err.response?.data?.detail || "Shartnomani saqlashda xatolik yuz berdi"
    step.value = 'form'
  } finally {
    isSubmitting.value = false
  }
}

// ── Reset on open ──────────────────────────────────────────────────────────
watch(
  () => props.isOpen,
  (val) => {
    if (val) {
      step.value = 'form'
      errorMessage.value = ''
      selectedTemplateKey.value = props.initialTemplateKey || 'STANDART'
      fullNameQuery.value = ''
      selectedExistingStudent.value = null
      isNameFocused.value = false
      studentIdAssigned.value = ''
      passportNumber.value = ''
      educationLevel.value = ''
      dateOfBirth.value = ''
      office.value = ''
      phone1.value = ''
      phone2.value = ''
      tariffPrice.value = ''
      discount.value = ''
      guardianFullName.value = ''
      guardianPassportNumber.value = ''
      guardianRelation.value = ''
      guardianPhone.value = ''
      guardianAddress.value = ''
      customContractNumber.value = ''
      customTitle.value = ''
      createdContract.value = null
      isCopiedSignLink.value = false
      nextTick(() => {
        const year = new Date().getFullYear()
        const randSeq = Math.floor(1000 + Math.random() * 9000)
        customContractNumber.value = `SH-${year}-${randSeq}`
      })
    }
  }
)
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="New Contract"
    subtitle="Talaba ma'lumotlarini kiritib onlayn imzolash havolasini yarating"
    max-width="max-w-3xl"
    @close="emit('close')"
  >
    <!-- STEP: done - show the per-contract signing link -->
    <div v-if="step === 'done'" class="p-6 space-y-5">
      <div class="flex flex-col items-center text-center py-2">
        <div class="w-12 h-12 rounded-full bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mb-3">
          <Check class="w-6 h-6" />
        </div>
        <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">Shartnoma yaratildi</h3>
        <p class="text-xs text-zinc-500 dark:text-zinc-400 mt-1">
          Quyidagi havolani talabaga yuboring - u hisob ochmasdan, faqat tug'ilgan sana va pasport raqamini
          tasdiqlab, hujjatini tekshirtirib, imzo chekadi.
        </p>
      </div>

      <div v-if="signLinkUrl" class="p-3.5 rounded-2xl bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/40 dark:to-indigo-950/30 border border-blue-200/80 dark:border-blue-900/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-2xs">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
            <Globe class="w-3.5 h-3.5" />
          </div>
          <div class="min-w-0">
            <div class="font-bold text-blue-900 dark:text-blue-200 text-[11px] uppercase tracking-wider">
              Imzolash havolasi
            </div>
            <div class="font-mono text-xs font-semibold text-blue-700 dark:text-blue-300 truncate" :title="signLinkUrl">
              {{ signLinkUrl }}
            </div>
          </div>
        </div>
        <button
          type="button"
          @click="copySignLink"
          class="shrink-0 inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition-all cursor-pointer select-none"
          :class="{ '!bg-emerald-600 hover:!bg-emerald-700': isCopiedSignLink }"
        >
          <Check v-if="isCopiedSignLink" class="w-3.5 h-3.5 text-emerald-100" />
          <Copy v-else class="w-3.5 h-3.5" />
          <span>{{ isCopiedSignLink ? 'Nusxalandi!' : 'Havolani nusxalash' }}</span>
        </button>
      </div>

      <div class="flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          Yopish
        </button>
      </div>
    </div>

    <!-- STEP: preview - read-only render before generating the link -->
    <div v-else-if="step === 'preview'" class="p-6 space-y-5">
      <div v-if="errorMessage" class="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-xs text-rose-600 dark:text-rose-300 flex items-center gap-2">
        <span class="font-bold">Xatolik:</span> {{ errorMessage }}
      </div>

      <div class="flex items-center justify-between">
        <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">
          Shartnoma ko'rinishi (preview)
        </label>
        <span v-if="isMinor" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-amber-50 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400 text-[10px] font-bold">
          <ShieldAlert class="w-3 h-3" /> 18 yoshdan kichik - kafil ma'lumotlari qo'shiladi
        </span>
      </div>

      <div class="max-h-[50vh] overflow-y-auto rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-4 text-[13px] leading-relaxed">
        <div v-html="previewHtml" />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">Contract Number</label>
          <input
            v-model="customContractNumber"
            type="text"
            class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono font-bold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
          />
        </div>
        <div>
          <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">Contract Title</label>
          <input
            v-model="customTitle"
            type="text"
            class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-bold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <div class="flex items-center justify-between gap-3 pt-2">
        <button
          type="button"
          @click="step = 'form'"
          class="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <ArrowLeft class="w-3.5 h-3.5" /> Orqaga
        </button>

        <button
          type="button"
          @click="handleCreate"
          :disabled="isSubmitting"
          class="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
        >
          <span v-if="isSubmitting">Yaratilmoqda...</span>
          <span v-else class="flex items-center gap-1.5">
            <span>Imzolash havolasini yaratish</span>
            <ArrowRight class="w-3.5 h-3.5" />
          </span>
        </button>
      </div>
    </div>

    <!-- STEP: form - staff enters everything -->
    <div v-else class="p-6 space-y-6">
      <div v-if="errorMessage" class="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-xs text-rose-600 dark:text-rose-300 flex items-center gap-2">
        <span class="font-bold">Xatolik:</span> {{ errorMessage }}
      </div>

      <!-- Tariff -->
      <div class="space-y-3">
        <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">
          1. Tarif
        </label>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          <div
            v-for="tpl in templateList"
            :key="tpl.key"
            @click="selectedTemplateKey = tpl.key"
            class="p-3 rounded-xl border transition-all cursor-pointer select-none relative flex flex-col justify-between group"
            :class="[
              selectedTemplateKey === tpl.key
                ? 'bg-blue-50/90 dark:bg-blue-950/40 border-blue-500 text-blue-600 dark:text-blue-400 shadow-sm ring-1 ring-blue-500'
                : 'bg-zinc-50 dark:bg-zinc-800/60 border-zinc-200 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-600'
            ]"
          >
            <div>
              <div class="flex items-center justify-between gap-1 mb-1">
                <span class="font-extrabold text-xs tracking-tight truncate">{{ tpl.key }}</span>
                <span v-if="selectedTemplateKey === tpl.key" class="w-4 h-4 rounded-full bg-blue-500 text-white flex items-center justify-center shrink-0">
                  <Check class="w-2.5 h-2.5" />
                </span>
              </div>
              <p class="text-[10px] text-zinc-400 line-clamp-2 leading-tight">{{ tpl.subtitle }}</p>
            </div>
            <div class="mt-2.5 pt-2 border-t border-zinc-200/60 dark:border-zinc-700/60 flex items-center justify-between text-[10.5px]">
              <span class="font-bold text-zinc-900 dark:text-zinc-100 font-mono">{{ tpl.priceDisplay }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Student fullname with live autocomplete -->
      <div class="space-y-3">
        <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">
          2. Talaba to'liq ismi
        </label>
        <div class="relative">
          <Search class="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            v-model="fullNameQuery"
            type="text"
            placeholder="Ism Familiyani kiriting..."
            autocomplete="off"
            @focus="isNameFocused = true"
            @blur="handleNameBlur"
            class="w-full pl-9 pr-3 py-2.5 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-sm font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 uppercase"
          />

          <div
            v-if="showSuggestions"
            class="absolute z-20 mt-1.5 w-full rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-lg max-h-56 overflow-y-auto divide-y divide-zinc-100 dark:divide-zinc-800"
          >
            <button
              v-for="st in suggestions"
              :key="st.id"
              type="button"
              @mousedown.prevent="pickExistingStudent(st)"
              class="w-full px-3 py-2 text-left text-xs transition-colors flex items-center justify-between hover:bg-zinc-50 dark:hover:bg-zinc-800 cursor-pointer"
            >
              <div class="flex items-center gap-2 min-w-0">
                <div class="w-6 h-6 rounded-full bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-300 flex items-center justify-center shrink-0 text-[10px] font-bold">
                  {{ st.full_name?.charAt(0) || 'T' }}
                </div>
                <div class="truncate">
                  <span class="font-bold text-zinc-800 dark:text-zinc-200">{{ st.full_name }}</span>
                  <span class="text-[11px] text-zinc-400 ml-2 font-mono">{{ st.id }}</span>
                </div>
              </div>
              <span v-if="st.tariff" class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-[10px] text-zinc-500 shrink-0">
                {{ st.tariff }}
              </span>
            </button>
          </div>
        </div>

        <div v-if="selectedExistingStudent" class="flex items-center gap-2 text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold">
          <Check class="w-3.5 h-3.5" /> Mavjud talaba tanlandi (ID: {{ selectedExistingStudent.id }}) - ma'lumotlar avtomatik to'ldirildi
        </div>
        <div v-else-if="fullNameQuery.trim()" class="text-[11px] text-zinc-400">
          Mos talaba topilmadi - yangi talaba sifatida qo'lda to'ldiriladi
        </div>
      </div>

      <!-- Full field set -->
      <div class="space-y-3">
        <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">
          3. Talaba ma'lumotlari
        </label>

        <div v-if="isNewStudent" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="sm:col-span-2">
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Student ID (CRM uchun)</label>
            <input
              v-model="studentIdAssigned"
              type="text"
              placeholder="masalan: UB120"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono font-bold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 uppercase"
            />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Pasport raqami</label>
            <input
              v-model="passportNumber"
              type="text"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 uppercase"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Tug'ilgan sana</label>
            <input
              v-model="dateOfBirth"
              type="date"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Ta'lim darajasi</label>
            <input
              v-model="educationLevel"
              type="text"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Ofis / Filial</label>
            <input
              v-model="office"
              type="text"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Telefon 1</label>
            <input
              v-model="phone1"
              type="text"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Telefon 2</label>
            <input
              v-model="phone2"
              type="text"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Narx</label>
            <input
              v-model="tariffPrice"
              type="text"
              :placeholder="String(selectedTemplate?.priceDisplay || '')"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Chegirma</label>
            <input
              v-model="discount"
              type="text"
              placeholder="0"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      <!-- Guardian sub-form, only for minors -->
      <div v-if="isMinor" class="space-y-3 p-4 rounded-xl border border-amber-200 dark:border-amber-900/50 bg-amber-50/50 dark:bg-amber-950/20">
        <label class="flex items-center gap-2 text-xs font-bold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
          <ShieldAlert class="w-3.5 h-3.5" />
          4. Kafil (ota-ona/vasiy) ma'lumotlari - 18 yoshdan kichik talaba
        </label>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div class="sm:col-span-2">
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Kafil F.I.O.</label>
            <input
              v-model="guardianFullName"
              type="text"
              class="w-full px-3 py-2 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 uppercase"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Kafil pasport raqami</label>
            <input
              v-model="guardianPassportNumber"
              type="text"
              class="w-full px-3 py-2 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono font-semibold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 uppercase"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Qarindoshligi</label>
            <input
              v-model="guardianRelation"
              type="text"
              placeholder="Ota / Ona / Vasiy"
              class="w-full px-3 py-2 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Kafil telefon raqami</label>
            <input
              v-model="guardianPhone"
              type="text"
              class="w-full px-3 py-2 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label class="block text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 mb-1">Yashash manzili</label>
            <input
              v-model="guardianAddress"
              type="text"
              class="w-full px-3 py-2 bg-white dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          Bekor qilish
        </button>

        <button
          type="button"
          @click="goToPreview"
          class="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
        >
          <span>Ko'rib chiqish</span>
          <ArrowRight class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  </BaseModal>
</template>
