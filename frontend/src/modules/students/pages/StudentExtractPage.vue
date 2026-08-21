<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  ArrowLeft,
  Upload,
  FileText,
  Cpu,
  Copy,
  Edit2,
  Trash2,
  CheckCircle2,
  Loader2,
  Check,
  AlertCircle,
  X
} from 'lucide-vue-next'
import { studentsApi } from '@/api/students'
import { settingsApi } from '@/api/settings'
import { useUiStore } from '@/stores/ui'
import type { Student } from '@/types'

const route = useRoute()
const router = useRouter()
const uiStore = useUiStore()
const queryClient = useQueryClient()

const studentId = computed(() => route.params.id as string)

// Fetch student details
const { data: student, isLoading: isStudentLoading, refetch: refetchStudent } = useQuery<Student>({
  queryKey: ['student-detail', studentId.value],
  queryFn: () => studentsApi.getStudentDetail(studentId.value),
  enabled: !!studentId.value,
})

// Fetch schools directory for auto-populating school details
const { data: dbSchools } = useQuery({
  queryKey: ['schools-directory'],
  queryFn: () => settingsApi.getSchools(),
})

// Upload & Extraction states
const isDragging = ref(false)
const selectedFile = ref<File | null>(null)
const previewUrl = ref<string | null>(null)
const isExtracting = ref(false)
const extractError = ref<string | null>(null)

interface ExtractedField {
  key: string
  value: string
}

const extractedDocType = ref<string | null>(null)
const extractedFieldsList = ref<ExtractedField[]>([])
const rawOcrText = ref<string>('')
const savedFields = ref<Record<string, boolean>>({})

// Modal / Edit state
const isEditModalOpen = ref(false)
const editingIndex = ref<number | null>(null)
const editValue = ref('')

// Field Mapping Dictionary
const FIELD_MAPPING: Record<string, keyof Student> = {
  'FULL NAME': 'full_name',
  'FULL_NAME': 'full_name',
  'PASSPORT NUMBER': 'passport',
  'PASSPORT_NUMBER': 'passport',
  'DATE OF BIRTH': 'birthday',
  'DATE_OF_BIRTH': 'birthday',
  'DATE OF ISSUE': 'passport_issue_date',
  'DATE_OF_ISSUE': 'passport_issue_date',
  'DATE OF EXPIRATION': 'passport_expire_date',
  'DATE_OF_EXPIRATION': 'passport_expire_date',
  'SEX': 'gender',
  'GENDER': 'gender',
  'EMAIL': 'email',
  'PHONE NUMBER 1': 'phone1',
  'PHONE_NUMBER_1': 'phone1',
  'PHONE NUMBER 2': 'phone2',
  'PHONE_NUMBER_2': 'phone2',
  'PHONE 1': 'phone1',
  'PHONE 2': 'phone2',
  'ADDRESS': 'address',
  'FINAL SCHOOL NAME': 'final_school_name',
  'FINAL_SCHOOL_NAME': 'final_school_name',
  'NAME OF SCHOOL': 'final_school_name',
  'EDUCATIONAL INSTITUTION': 'final_school_name',
  'MAJOR': 'major',
  'SPECIALTY': 'major',
  'GPA': 'gpa',
  'DEGREE NO': 'degree_no',
  'DEGREE_NO': 'degree_no',
  'DIPLOMA NUMBER': 'degree_no',
  'DATE OF ENTRY': 'date_of_entry',
  'DATE_OF_ENTRY': 'date_of_entry',
  'DATE OF GRADUATION': 'date_of_graduation',
  'DATE_OF_GRADUATION': 'date_of_graduation',
  'FATHER FULLNAME': 'father_name',
  'FATHER_FULLNAME': 'father_name',
  'MOTHER FULLNAME': 'mother_name',
  'MOTHER_FULLNAME': 'mother_name'
}

// File drop & selection handlers
const handleDrop = (e: DragEvent) => {
  isDragging.value = false
  const files = e.dataTransfer?.files
  if (files && files.length > 0) {
    processFile(files[0])
  }
}

const handleFileInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    processFile(target.files[0])
  }
}

const processFile = (file: File) => {
  selectedFile.value = file
  extractError.value = null
  extractedDocType.value = null
  extractedFieldsList.value = []
  rawOcrText.value = ''
  savedFields.value = {}

  if (file.type.startsWith('image/')) {
    previewUrl.value = URL.createObjectURL(file)
  } else if (file.type === 'application/pdf') {
    previewUrl.value = 'pdf'
  } else {
    previewUrl.value = 'doc'
  }
}

// Global Ctrl+V Screenshot Paste Handler
const handlePaste = (e: ClipboardEvent) => {
  // If user is typing in a modal or input, let the browser handle it
  if (isEditModalOpen.value) return
  const target = e.target as HTMLElement
  if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) return

  const items = e.clipboardData?.items
  if (!items) return

  for (let i = 0; i < items.length; i++) {
    const item = items[i]
    if (item.type.indexOf('image') !== -1) {
      const file = item.getAsFile()
      if (file) {
        processFile(file)
        uiStore.addToast({
          type: 'info',
          title: 'Screenshot Pasted',
          message: `Loaded image from clipboard (${(file.size / 1024).toFixed(1)} KB)`
        })
        e.preventDefault()
        break
      }
    }
  }
}

onMounted(() => {
  window.addEventListener('paste', handlePaste)
})

onUnmounted(() => {
  window.removeEventListener('paste', handlePaste)
  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
})

const removeFile = () => {
  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
  selectedFile.value = null
  previewUrl.value = null
  extractedDocType.value = null
  extractedFieldsList.value = []
  extractError.value = null
  savedFields.value = {}
}

// Trigger Document Extraction via Django Python OCR
const triggerExtraction = async () => {
  if (!selectedFile.value) return

  isExtracting.value = true
  extractError.value = null
  extractedFieldsList.value = []
  savedFields.value = {}

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('student_id', studentId.value)

    const response = await studentsApi.extractDocument(formData)

    extractedDocType.value = response.document_type || 'GENERAL DOCUMENT'
    rawOcrText.value = response.ocr_text || ''

    const fieldsArr: ExtractedField[] = []
    if (response.fields && typeof response.fields === 'object') {
      for (const [k, v] of Object.entries(response.fields)) {
        if (v && String(v).trim()) {
          fieldsArr.push({ key: k, value: String(v).trim() })
        }
      }
    }
    extractedFieldsList.value = fieldsArr

    uiStore.addToast({
      type: 'success',
      title: 'Extraction Complete',
      message: `Extracted ${fieldsArr.length} field(s) from document scan.`
    })
  } catch (err: any) {
    console.error('Extraction failed:', err)
    extractError.value = err.response?.data?.error || 'Failed to extract document information.'
    uiStore.addToast({
      type: 'error',
      title: 'Extraction Failed',
      message: extractError.value || 'Error'
    })
  } finally {
    isExtracting.value = false
  }
}

// Check if an extracted field already matches the current student in the database
const isFieldAlreadyMatching = (fieldKey: string, fieldValue: string): boolean => {
  if (!student.value) return false
  const cleanKey = fieldKey.replace(/_/g, ' ').toUpperCase().trim()
  const dbField = FIELD_MAPPING[cleanKey] || FIELD_MAPPING[fieldKey]
  if (!dbField) return false

  const currentVal = student.value[dbField]
  if (currentVal === null || currentVal === undefined) return false

  let curStr = String(currentVal).trim().toUpperCase()
  let newStr = String(fieldValue).trim().toUpperCase()

  if (dbField === 'gender') {
    newStr = newStr.startsWith('M') ? 'MALE' : (newStr.startsWith('F') ? 'FEMALE' : newStr)
  }
  if (dbField === 'passport') {
    newStr = newStr.replace(/\s/g, '')
    curStr = curStr.replace(/\s/g, '')
  }

  return curStr === newStr && newStr !== ''
}

// Copy to Clipboard
const copiedField = ref<string | null>(null)
const handleCopy = async (val: string, key: string) => {
  try {
    await navigator.clipboard.writeText(val)
    copiedField.value = key
    setTimeout(() => {
      copiedField.value = null
    }, 1500)
  } catch {
    // fallback
  }
}

// Delete Field locally
const handleDeleteField = (index: number) => {
  extractedFieldsList.value.splice(index, 1)
}

// Open Edit Modal
const openEditModal = (index: number) => {
  editingIndex.value = index
  editValue.value = extractedFieldsList.value[index].value
  isEditModalOpen.value = true
}

const saveEditValue = () => {
  if (editingIndex.value !== null && extractedFieldsList.value[editingIndex.value]) {
    extractedFieldsList.value[editingIndex.value].value = editValue.value.trim()
  }
  isEditModalOpen.value = false
  editingIndex.value = null
}

// Save Field to Student Profile in Django Backend
const savingFieldKey = ref<string | null>(null)
const handleSaveFieldToProfile = async (fieldKey: string, value: string) => {
  const cleanKey = fieldKey.replace(/_/g, ' ').toUpperCase().trim()
  const dbField = FIELD_MAPPING[cleanKey] || FIELD_MAPPING[fieldKey]

  if (!dbField) {
    uiStore.addToast({
      type: 'error',
      title: 'Mapping Not Found',
      message: `No database column mapped for field: ${fieldKey}`
    })
    return
  }

  if (!student.value) return

  let finalValue: any = value.trim()

  // Normalizations
  if (dbField === 'gender') {
    const char = finalValue.toUpperCase()[0]
    finalValue = char === 'M' ? 'MALE' : (char === 'F' ? 'FEMALE' : finalValue)
  } else if (dbField === 'passport') {
    finalValue = finalValue.replace(/\s/g, '').toUpperCase()
  } else if (dbField === 'phone1' || dbField === 'phone2') {
    const digits = finalValue.replace(/\D/g, '')
    let cleanDigits = digits
    if (cleanDigits.startsWith('998') && cleanDigits.length === 12) {
      cleanDigits = cleanDigits.slice(3)
    } else if (cleanDigits.length > 9) {
      cleanDigits = cleanDigits.slice(-9)
    }
    if (cleanDigits.length === 9) {
      finalValue = `${cleanDigits.slice(0, 2)}-${cleanDigits.slice(2, 5)}-${cleanDigits.slice(5, 7)}-${cleanDigits.slice(7, 9)}`
    }
  } else if (['full_name', 'address', 'final_school_name', 'major', 'father_name', 'mother_name'].includes(dbField as string)) {
    finalValue = finalValue.toUpperCase()
  }

  savingFieldKey.value = fieldKey
  try {
    const updatePayload: Partial<Student> = {
      [dbField]: finalValue
    }

    // Auto-lookup schools directory if saving final_school_name
    if (dbField === 'final_school_name' && dbSchools.value && Array.isArray(dbSchools.value)) {
      updatePayload.educational_background = finalValue
      const cleanSchool = finalValue.toUpperCase().trim()
      const match = dbSchools.value.find((s: any) => {
        const name = (s.name || '').toUpperCase().trim()
        return name === cleanSchool || cleanSchool.includes(name) || name.includes(cleanSchool)
      })
      if (match) {
        if (match.address) updatePayload.school_address = match.address
        if (match.website) updatePayload.school_website = match.website
        if (match.phone) updatePayload.school_phone = match.phone
        if (match.email) updatePayload.school_email = match.email
      }
    }

    // Default GPA system to 5 if GPA saved
    if (dbField === 'gpa') {
      const gpaNum = parseFloat(finalValue)
      if (!isNaN(gpaNum) && gpaNum <= 5.0 && !student.value.gpa_system) {
        updatePayload.gpa_system = '5'
      }
    }

    await studentsApi.updateStudent(studentId.value, updatePayload)
    savedFields.value[fieldKey] = true

    await refetchStudent()
    queryClient.invalidateQueries({ queryKey: ['students'] })

    uiStore.addToast({
      type: 'success',
      title: 'Field Saved',
      message: `Updated "${cleanKey}" to ${finalValue}`
    })
  } catch (err: any) {
    console.error('Failed to save field:', err)
    uiStore.addToast({
      type: 'error',
      title: 'Save Failed',
      message: err.response?.data?.detail || 'Could not save field to profile.'
    })
  } finally {
    savingFieldKey.value = null
  }
}

// Student initials helper
const getInitials = (name?: string) => {
  if (!name) return 'ST'
  const parts = name.trim().split(' ').filter(Boolean)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + (parts[1]?.[0] || '')).toUpperCase()
}
</script>

<template>
  <div class="min-h-screen bg-zinc-50 dark:bg-zinc-950 p-4 md:p-6 space-y-4">
    <!-- Student Header Banner with Back Button -->
    <div
      v-if="student"
      class="p-3.5 sm:p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs flex items-center justify-between gap-4"
    >
      <div class="flex items-center gap-3">
        <!-- Back Button next to Square Avatar -->
        <button
          @click="router.push('/students')"
          class="p-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 transition-all cursor-pointer shadow-2xs hover:scale-[1.02] active:scale-[0.98]"
          title="Back to Students Dashboard"
        >
          <ArrowLeft class="w-4 h-4" />
        </button>

        <div class="w-11 h-11 sm:w-12 sm:h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-500 flex items-center justify-center font-black text-base sm:text-lg shrink-0">
          {{ getInitials(student.full_name) }}
        </div>
        <div class="min-w-0">
          <h2 class="text-sm sm:text-base font-extrabold text-zinc-900 dark:text-zinc-100 tracking-tight truncate">
            {{ student.full_name || 'Unnamed Student' }}
          </h2>
          <div class="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs font-semibold text-zinc-500 dark:text-zinc-400 mt-0.5">
            <span>ID: <strong class="text-brand-500 font-mono">{{ student.id }}</strong></span>
            <span class="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700 hidden sm:inline-block" />
            <span>Passport: <strong class="text-zinc-800 dark:text-zinc-200">{{ student.passport || '—' }}</strong></span>
            <span class="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700 hidden sm:inline-block" />
            <span>Tariff: <strong class="text-zinc-800 dark:text-zinc-200">{{ student.tariff || '—' }}</strong></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Two-Column Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5">
      <!-- Left Column: Upload & Scan Preview (5 cols) -->
      <div class="lg:col-span-5 space-y-4">
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 shadow-xs relative overflow-hidden flex flex-col min-h-[480px]">
          <h3 class="text-xs font-extrabold uppercase tracking-wider text-brand-500 flex items-center gap-2 mb-4">
            <Upload class="w-4 h-4" />
            Document Scan Upload
          </h3>

          <!-- Upload Dropzone (When no file selected) -->
          <div
            v-if="!selectedFile"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="handleDrop"
            :class="[
              'flex-1 border-2 border-dashed rounded-2xl flex flex-col items-center justify-center p-6 text-center transition-all cursor-pointer select-none',
              isDragging
                ? 'border-brand-500 bg-brand-500/5 dark:bg-brand-500/10'
                : 'border-zinc-200 dark:border-zinc-800 hover:border-brand-500/50 hover:bg-zinc-50 dark:hover:bg-zinc-850/50'
            ]"
            @click="($refs.fileInput as HTMLInputElement)?.click()"
          >
            <input
              ref="fileInput"
              type="file"
              accept=".pdf,.jpg,.jpeg,.png,.webp"
              class="hidden"
              @change="handleFileInput"
            />
            <div class="w-14 h-14 rounded-2xl bg-brand-500/10 text-brand-500 flex items-center justify-center mb-3">
              <Upload class="w-6 h-6" />
            </div>
            <h4 class="text-xs font-bold text-zinc-800 dark:text-zinc-200 mb-1">
              Click to browse or drop document scan
            </h4>
            <p class="text-[11px] text-zinc-400 max-w-[240px] mb-3">
              Supports Passport photo, Diploma, Shahodatnoma, or PDF files.
            </p>
            <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[10px] font-bold text-zinc-500 dark:text-zinc-400">
              <span>Paste screenshot:</span>
              <kbd class="px-1.5 py-0.5 rounded bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 font-mono text-[9px] text-zinc-800 dark:text-zinc-200 shadow-2xs">Ctrl</kbd>
              <span>+</span>
              <kbd class="px-1.5 py-0.5 rounded bg-white dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 font-mono text-[9px] text-zinc-800 dark:text-zinc-200 shadow-2xs">V</kbd>
            </div>
          </div>

          <!-- File Preview & Action (When file is selected) -->
          <div v-else class="flex-1 flex flex-col justify-between space-y-4">
            <!-- Preview Box -->
            <div class="relative flex-1 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-950 overflow-hidden flex items-center justify-center p-2 min-h-[300px]">
              <button
                @click="removeFile"
                class="absolute top-3 right-3 p-1.5 rounded-xl bg-zinc-900/70 hover:bg-rose-600 text-white backdrop-blur-xs transition-colors z-10 cursor-pointer shadow-md"
                title="Remove file"
              >
                <X class="w-4 h-4" />
              </button>

              <img
                v-if="previewUrl && previewUrl !== 'pdf' && previewUrl !== 'doc'"
                :src="previewUrl"
                alt="Document Preview"
                class="max-h-[360px] w-auto object-contain rounded-xl shadow-sm"
              />
              <div v-else class="text-center space-y-2 p-6">
                <FileText class="w-12 h-12 text-brand-500 mx-auto" />
                <p class="text-xs font-bold text-zinc-800 dark:text-zinc-200">
                  {{ selectedFile.name }}
                </p>
                <p class="text-[10px] text-zinc-400 font-mono">
                  {{ (selectedFile.size / 1024).toFixed(1) }} KB
                </p>
              </div>
            </div>

            <!-- Extract Action Button -->
            <button
              :disabled="isExtracting"
              @click="triggerExtraction"
              class="w-full py-3.5 px-4 rounded-xl bg-brand-500 hover:bg-brand-600 active:scale-[0.98] disabled:opacity-50 text-white font-extrabold text-xs shadow-lg shadow-brand-500/25 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <Loader2 v-if="isExtracting" class="w-4 h-4 animate-spin" />
              <Cpu v-else class="w-4 h-4" />
              <span>{{ isExtracting ? 'Extracting with Python OCR...' : 'Extract Information from Document' }}</span>
            </button>
          </div>

          <!-- Loading Shimmer Overlay -->
          <div
            v-if="isExtracting"
            class="absolute inset-0 bg-white/90 dark:bg-zinc-900/90 backdrop-blur-xs flex flex-col items-center justify-center p-6 z-20 space-y-3"
          >
            <div class="p-3.5 rounded-2xl bg-brand-500/10 text-brand-500 border border-brand-500/20">
              <Loader2 class="w-7 h-7 animate-spin" />
            </div>
            <h4 class="text-xs font-extrabold text-zinc-900 dark:text-zinc-100">
              Analyzing Document Structure
            </h4>
            <p class="text-[11px] text-zinc-500 dark:text-zinc-400 text-center max-w-xs">
              Reading text blocks, recognizing MRZ checksums, and detecting profile fields in RAM...
            </p>
            <div class="w-48 h-1.5 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden relative mt-2">
              <div class="absolute inset-0 w-1/2 bg-brand-500 rounded-full animate-pulse" />
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Extracted Profile Fields (7 cols) -->
      <div class="lg:col-span-7 space-y-4">
        <div class="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 shadow-xs flex flex-col min-h-[480px] space-y-4">
          <!-- Card Header -->
          <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-3">
            <h3 class="text-xs font-extrabold uppercase tracking-wider text-brand-500 flex items-center gap-2">
              <FileText class="w-4 h-4" />
              Extracted Profile Fields
            </h3>
            <span
              v-if="extractedDocType"
              class="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-[10px] uppercase font-extrabold tracking-wider"
            >
              Type: {{ extractedDocType }}
            </span>
          </div>

          <!-- Empty State -->
          <div
            v-if="!extractedDocType && !isExtracting"
            class="flex-1 flex flex-col items-center justify-center p-12 text-center text-zinc-400 space-y-3"
          >
            <div class="w-14 h-14 rounded-2xl bg-zinc-100 dark:bg-zinc-800 text-zinc-400 flex items-center justify-center">
              <FileText class="w-6 h-6" />
            </div>
            <div>
              <h4 class="text-xs font-bold text-zinc-700 dark:text-zinc-300 mb-1">
                Waiting for document
              </h4>
              <p class="text-[11px] max-w-xs text-zinc-400">
                Upload a passport or certificate scan on the left and click Extract to parse profile details.
              </p>
            </div>
          </div>

          <!-- Error Alert -->
          <div
            v-if="extractError"
            class="p-3.5 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-800 text-rose-800 dark:text-rose-200 text-xs font-bold flex items-center gap-2"
          >
            <AlertCircle class="w-4 h-4 shrink-0" />
            <span>{{ extractError }}</span>
          </div>

          <!-- Extracted Field Cards List -->
          <div
            v-if="extractedFieldsList.length > 0 && !isExtracting"
            class="space-y-2.5 flex-1"
          >
            <div
              v-for="(field, idx) in extractedFieldsList"
              :key="idx"
              :class="[
                'p-3 rounded-xl border flex items-center justify-between gap-3 transition-all',
                savedFields[field.key] || isFieldAlreadyMatching(field.key, field.value)
                  ? 'border-emerald-500/40 bg-emerald-50/50 dark:bg-emerald-950/20'
                  : 'border-zinc-200 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-850/60 hover:border-zinc-300 dark:hover:border-zinc-700'
              ]"
            >
              <!-- Field Details -->
              <div class="min-w-0 flex-1">
                <span class="text-[10px] font-extrabold uppercase tracking-wider text-brand-500 block">
                  {{ field.key.replace(/_/g, ' ') }}
                </span>
                <span
                  class="text-xs font-bold text-zinc-900 dark:text-zinc-100 mt-0.5 block truncate max-w-sm"
                  :title="field.value"
                >
                  {{ field.value }}
                </span>
              </div>

              <!-- Field Actions -->
              <div class="flex items-center gap-1.5 shrink-0">
                <button
                  @click="handleCopy(field.value, field.key)"
                  class="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg text-zinc-500 dark:text-zinc-400 transition-colors cursor-pointer"
                  title="Copy to clipboard"
                >
                  <Check v-if="copiedField === field.key" class="w-3.5 h-3.5 text-emerald-500" />
                  <Copy v-else class="w-3.5 h-3.5" />
                </button>

                <button
                  @click="openEditModal(idx)"
                  class="p-1.5 hover:bg-zinc-200 dark:hover:bg-zinc-700 rounded-lg text-zinc-500 dark:text-zinc-400 transition-colors cursor-pointer"
                  title="Edit field value"
                >
                  <Edit2 class="w-3.5 h-3.5" />
                </button>

                <button
                  @click="handleDeleteField(idx)"
                  class="p-1.5 hover:bg-rose-500/10 rounded-lg text-zinc-400 hover:text-rose-600 transition-colors cursor-pointer"
                  title="Remove field"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </button>

                <!-- Save to Profile Button -->
                <button
                  :disabled="savedFields[field.key] || isFieldAlreadyMatching(field.key, field.value) || savingFieldKey === field.key"
                  @click="handleSaveFieldToProfile(field.key, field.value)"
                  :class="[
                    'px-3 py-1.5 rounded-lg text-[10px] font-extrabold uppercase transition-all flex items-center gap-1 select-none border cursor-pointer',
                    savedFields[field.key] || isFieldAlreadyMatching(field.key, field.value)
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 cursor-default'
                      : 'bg-emerald-600 hover:bg-emerald-500 border-emerald-600 text-white shadow-xs active:scale-[0.96]'
                  ]"
                >
                  <Loader2 v-if="savingFieldKey === field.key" class="w-3 h-3 animate-spin" />
                  <template v-else-if="savedFields[field.key] || isFieldAlreadyMatching(field.key, field.value)">
                    <CheckCircle2 class="w-3 h-3 text-emerald-500" />
                    <span>Saved</span>
                  </template>
                  <template v-else>
                    <span>Save to &gt;&gt;</span>
                  </template>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Edit Value Modal -->
    <div
      v-if="isEditModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs"
    >
      <div class="w-full max-w-sm bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 shadow-2xl space-y-4">
        <div class="flex items-center justify-between">
          <h4 class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
            Edit Extracted Value
          </h4>
          <button @click="isEditModalOpen = false" class="text-zinc-400 hover:text-zinc-600 cursor-pointer">
            <X class="w-4 h-4" />
          </button>
        </div>

        <input
          v-model="editValue"
          type="text"
          class="w-full px-3 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-xs font-medium text-zinc-900 dark:text-zinc-100 outline-none focus:border-brand-500"
          @keyup.enter="saveEditValue"
        />

        <div class="flex items-center justify-end gap-2">
          <button
            @click="isEditModalOpen = false"
            class="px-3 py-1.5 rounded-lg border border-zinc-200 dark:border-zinc-800 text-xs font-bold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer"
          >
            Cancel
          </button>
          <button
            @click="saveEditValue"
            class="px-4 py-1.5 rounded-lg bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold cursor-pointer"
          >
            Update Value
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
