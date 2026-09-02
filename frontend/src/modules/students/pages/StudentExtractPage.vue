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
  CheckCheck,
  Loader2,
  Check,
  AlertCircle,
  X,
  Sparkles,
  Sliders,
  Eye,
  EyeOff,
  Award,
  Calendar,
  ArrowRight
} from 'lucide-vue-next'
import { studentsApi } from '@/api/students'
import { settingsApi } from '@/api/settings'
import { useUiStore } from '@/stores/ui'
import { BUILTIN_SCHOOL_DIRECTORY } from '@/data/schoolsData'
import type { Student } from '@/types'

const route = useRoute()
const router = useRouter()
const uiStore = useUiStore()
const queryClient = useQueryClient()

const studentId = computed(() => (route.params.id as string) || '')

// Fetch student details
const { data: student, isLoading: isStudentLoading, refetch: refetchStudent } = useQuery<Student>({
  queryKey: ['student-detail', studentId],
  queryFn: () => studentsApi.getStudentDetail(studentId.value),
  enabled: computed(() => !!studentId.value),
})

// Fetch schools directory for auto-populating school details
const { data: dbSchools } = useQuery({
  queryKey: ['schools-directory'],
  queryFn: () => settingsApi.getSchools(),
})

// AI Settings State (stored in localStorage)
const isSettingsOpen = ref(false)
const showApiKey = ref(false)
const geminiModelSelect = ref('gemini-3.7-flash')
const customModelId = ref('')

const KNOWN_GEMINI_MODELS = [
  'gemini-3.7-flash',
  'gemini-3.5-flash',
  'gemini-3.1-pro',
  'gemini-3.1-flash-lite',
  'gemini-2.5-flash',
  'gemini-2.5-pro',
  'gemini-2.0-flash',
  'gemini-1.5-pro',
  'gemini-1.5-flash',
  'gemini-2.5-flash-lite'
]

const aiSettings = ref({
  provider: 'openai', // 'openai' | 'gemini'
  apiKey: '',
  openaiApiKey: '',
  model: 'gemini-3.7-flash',
  openaiModel: 'gpt-4o',
  normalizeDates: true,
  mergeNames: true,
  extractStructured: true
})

const tempSettings = ref({ ...aiSettings.value })

const toggleSettings = () => {
  if (!isSettingsOpen.value) {
    tempSettings.value = { ...aiSettings.value }
    if (aiSettings.value.model) {
      if (KNOWN_GEMINI_MODELS.includes(aiSettings.value.model)) {
        geminiModelSelect.value = aiSettings.value.model
      } else {
        geminiModelSelect.value = 'custom'
        customModelId.value = aiSettings.value.model
      }
    }
  }
  isSettingsOpen.value = !isSettingsOpen.value
}

const handleSaveSettings = () => {
  if (tempSettings.value.provider === 'gemini' && geminiModelSelect.value === 'custom') {
    tempSettings.value.model = customModelId.value || 'gemini-2.5-flash'
  } else if (tempSettings.value.provider === 'gemini') {
    tempSettings.value.model = geminiModelSelect.value
  }

  aiSettings.value = { ...tempSettings.value }
  try {
    localStorage.setItem('ai_settings', JSON.stringify(aiSettings.value))
    uiStore.addToast({
      type: 'success',
      title: 'AI Settings Saved',
      message: 'AI provider and model configuration updated.'
    })
    isSettingsOpen.value = false
  } catch (e) {
    console.error('Failed to save AI settings to localStorage', e)
    uiStore.addToast({
      type: 'error',
      title: 'Save Failed',
      message: 'Could not save AI settings locally.'
    })
  }
}

// Upload & Extraction states
const isDragging = ref(false)
const selectedFile = ref<File | null>(null)
const previewUrl = ref<string | null>(null)
const isExtracting = ref(false)
const extractError = ref<string | null>(null)

interface ExtractedField {
  key: string
  value: string
  confidence?: number
  validated?: boolean
  source?: string
}

const extractedDocType = ref<string | null>(null)
const extractedFieldsList = ref<ExtractedField[]>([])
const rawOcrText = ref<string>('')
const extractionLatency = ref<number | null>(null)
const ocrEngineUsed = ref<string | null>(null)
const savedFields = ref<Record<string, boolean>>({})

// Modal / Edit state
const isEditModalOpen = ref(false)
const editingIndex = ref<number | null>(null)
const editValue = ref('')

// Field Mapping Dictionary
const FIELD_MAPPING: Record<string, keyof Student> = {
  'FULL NAME': 'full_name',
  'FULL_NAME': 'full_name',
  'STUDENT NAME': 'full_name',
  'PASSPORT NUMBER': 'passport',
  'PASSPORT_NUMBER': 'passport',
  'PASSPORT': 'passport',
  'DATE OF BIRTH': 'birthday',
  'DATE_OF_BIRTH': 'birthday',
  'BIRTHDAY': 'birthday',
  'DOB': 'birthday',
  'DATE OF ISSUE': 'passport_issue_date',
  'DATE_OF_ISSUE': 'passport_issue_date',
  'ISSUE DATE': 'passport_issue_date',
  'DATE OF EXPIRATION': 'passport_expire_date',
  'DATE_OF_EXPIRATION': 'passport_expire_date',
  'EXPIRATION DATE': 'passport_expire_date',
  'SEX': 'gender',
  'GENDER': 'gender',
  'EMAIL': 'email',
  'PHONE NUMBER 1': 'phone1',
  'PHONE_NUMBER_1': 'phone1',
  'PHONE NUMBER 2': 'phone2',
  'PHONE_NUMBER_2': 'phone2',
  'PHONE 1': 'phone1',
  'PHONE 2': 'phone2',
  'PHONE': 'phone1',
  'CONTACT': 'phone1',
  'TELEFON': 'phone1',
  'ADDRESS': 'address',
  'HOME ADDRESS': 'address',
  'MANZIL': 'address',
  'MANZILI': 'address',
  'YASHASH MANZILI': 'address',
  'PLACE OF BIRTH': 'address',
  'PLACE_OF_BIRTH': 'address',
  // Educational Background mappings
  'FINAL SCHOOL NAME': 'final_school_name',
  'FINAL_SCHOOL_NAME': 'final_school_name',
  'NAME OF SCHOOL': 'final_school_name',
  'NAME OF SCHOOL / EDUCATIONAL INSTITUTION': 'final_school_name',
  'EDUCATIONAL INSTITUTION': 'final_school_name',
  'SCHOOL NAME': 'final_school_name',
  'EDUCATIONAL BACKGROUND': 'final_school_name',
  'UNIVERSITY': 'final_school_name',
  'COLLEGE': 'final_school_name',
  'MAKTAB': 'final_school_name',
  'LITSEY': 'final_school_name',
  'MAJOR': 'major',
  'MAJOR OR SPECIALTY': 'major',
  'SPECIALTY': 'major',
  'SPECIALITY': 'major',
  'MUTAXASSISLIK': 'major',
  'YONALISH': 'major',
  'GPA': 'gpa',
  'GRADE POINT AVERAGE': 'gpa',
  'AVERAGE GRADE': 'gpa',
  'DEGREE NO': 'degree_no',
  'DEGREE_NO': 'degree_no',
  'DEGREE NUMBER': 'degree_no',
  'DIPLOMA NO': 'degree_no',
  'DIPLOMA_NO': 'degree_no',
  'DIPLOMA NUMBER': 'degree_no',
  'CERTIFICATE NO': 'degree_no',
  'CERTIFICATE_NO': 'degree_no',
  'CERTIFICATE NUMBER': 'degree_no',
  'SHAHODATNOMA NO': 'degree_no',
  'DATE OF ENTRY': 'date_of_entry',
  'DATE_OF_ENTRY': 'date_of_entry',
  'ENTRY DATE': 'date_of_entry',
  'YEAR OF ENTRY': 'date_of_entry',
  'KIRGAN YILI': 'date_of_entry',
  'DATE OF GRADUATION': 'date_of_graduation',
  'DATE_OF_GRADUATION': 'date_of_graduation',
  'GRADUATION DATE': 'date_of_graduation',
  'YEAR OF GRADUATION': 'date_of_graduation',
  'BITIRGAN YILI': 'date_of_graduation',
  'TAMOMLAGAN YILI': 'date_of_graduation',
  // Parent mappings
  'FATHER FULLNAME': 'father_name',
  'FATHER_FULLNAME': 'father_name',
  'FATHER NAME': 'father_name',
  'FATHER_NAME': 'father_name',
  'DADAM': 'father_name',
  'OTASI': 'father_name',
  'OTASINING ISMI': 'father_name',
  'FATHER PHONE': 'father_phone',
  'FATHER_PHONE': 'father_phone',
  'FATHER PHONE 1': 'father_phone',
  'FATHER PHONE 2': 'father_phone',
  'FATHER PHONE NUMBER': 'father_phone',
  'FATHER_PHONE_NUMBER': 'father_phone',
  'DADAM RAQAMI': 'father_phone',
  'OTAM RAQAMI': 'father_phone',
  'MOTHER FULLNAME': 'mother_name',
  'MOTHER_FULLNAME': 'mother_name',
  'MOTHER NAME': 'mother_name',
  'MOTHER_NAME': 'mother_name',
  'ONASI': 'mother_name',
  'ONASINING ISMI': 'mother_name',
  'OYIM': 'mother_name',
  'MOTHER PHONE': 'mother_phone',
  'MOTHER_PHONE': 'mother_phone',
  'MOTHER PHONE 1': 'mother_phone',
  'MOTHER PHONE 2': 'mother_phone',
  'MOTHER PHONE NUMBER': 'mother_phone',
  'MOTHER_PHONE_NUMBER': 'mother_phone',
  'OYIM RAQAMI': 'mother_phone',
  'ONAM RAQAMI': 'mother_phone',
  // Certificate mappings
  'CERTIFICATE TYPE': 'language_certificate',
  'CERTIFICATE_TYPE': 'language_certificate',
  'LANGUAGE CERTIFICATE': 'language_certificate',
  'LANGUAGE_CERTIFICATE': 'language_certificate',
  'CERTIFICATE SCORE': 'certificate_score',
  'CERTIFICATE_SCORE': 'certificate_score',
  'SCORE': 'certificate_score',
  'CERTIFICATE TEST DATE': 'certificate_test_date',
  'CERTIFICATE_TEST_DATE': 'certificate_test_date',
  'TEST DATE': 'certificate_test_date',
  'TEST_DATE': 'certificate_test_date',
  'CERTIFICATE VALID DATE': 'certificate_valid_date',
  'CERTIFICATE_VALID_DATE': 'certificate_valid_date',
  'VALID DATE': 'certificate_valid_date',
  'VALID_DATE': 'certificate_valid_date',
  'VALID UNTIL': 'certificate_valid_date',
  'VALID_UNTIL': 'certificate_valid_date'
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

// High-performance Client-Side Canvas Image Compressor
const compressImageClient = async (file: File, maxDim = 1920, quality = 0.86): Promise<File> => {
  return new Promise((resolve) => {
    // If already small JPEG (< 300KB), return as is
    if (file.size < 300 * 1024 && file.type === 'image/jpeg') {
      return resolve(file)
    }

    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        let { width, height } = img

        // Scale proportionally if larger than maxDim
        if (width > maxDim || height > maxDim) {
          if (width > height) {
            height = Math.round((height * maxDim) / width)
            width = maxDim
          } else {
            width = Math.round((width * maxDim) / height)
            height = maxDim
          }
        }

        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        const ctx = canvas.getContext('2d')

        if (!ctx) {
          return resolve(file)
        }

        // Enable smooth image scaling
        ctx.imageSmoothingEnabled = true
        ctx.imageSmoothingQuality = 'high'
        ctx.drawImage(img, 0, 0, width, height)

        canvas.toBlob(
          (blob) => {
            if (blob && blob.size < file.size) {
              const fileName = (file.name || 'screenshot').replace(/\.[^/.]+$/, '') + '.jpg'
              const compressedFile = new File([blob], fileName, {
                type: 'image/jpeg',
                lastModified: Date.now()
              })
              resolve(compressedFile)
            } else {
              resolve(file)
            }
          },
          'image/jpeg',
          quality
        )
      }
      img.onerror = () => resolve(file)
      img.src = e.target?.result as string
    }
    reader.onerror = () => resolve(file)
    reader.readAsDataURL(file)
  })
}

const processFile = async (file: File) => {
  // Only accept images (JPG, PNG, WEBP)
  if (!file.type.startsWith('image/')) {
    uiStore.addToast({
      type: 'error',
      title: 'Invalid File',
      message: 'Please upload an image file (JPG, PNG, or WebP) or paste a screenshot.'
    })
    return
  }

  // Compress image instantly in browser before upload
  const processed = await compressImageClient(file)

  selectedFile.value = processed
  extractError.value = null
  extractedDocType.value = null
  extractedFieldsList.value = []
  rawOcrText.value = ''
  extractionLatency.value = null
  ocrEngineUsed.value = null
  savedFields.value = {}

  if (previewUrl.value && previewUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(previewUrl.value)
  }
  previewUrl.value = URL.createObjectURL(processed)
}

// Global Ctrl+V Screenshot Paste Handler
const handlePaste = (e: ClipboardEvent) => {
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
        break
      }
    }
  }
}

onMounted(() => {
  window.addEventListener('paste', handlePaste)
  try {
    const stored = localStorage.getItem('ai_settings')
    if (stored) {
      const parsed = JSON.parse(stored)
      aiSettings.value = { ...aiSettings.value, ...parsed }
      tempSettings.value = { ...aiSettings.value }
      if (parsed.model) {
        if (KNOWN_GEMINI_MODELS.includes(parsed.model)) {
          geminiModelSelect.value = parsed.model
        } else {
          geminiModelSelect.value = 'custom'
          customModelId.value = parsed.model
        }
      }
    }
  } catch (e) {
    console.warn('Failed to parse ai_settings from local storage', e)
  }
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
  rawOcrText.value = ''
  extractionLatency.value = null
  ocrEngineUsed.value = null
  extractError.value = null
  savedFields.value = {}
}

const normalizeDate = (val: string): string => {
  if (!val) return val
  const s = String(val).trim()
  if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s

  // DD MM YYYY, DD.MM.YYYY, DD/MM/YYYY, DD-MM-YYYY
  const m1 = s.match(/^(\d{1,2})[\s\.\/\-](\d{1,2})[\s\.\/\-](\d{4})$/)
  if (m1) {
    let d = parseInt(m1[1], 10)
    let m = parseInt(m1[2], 10)
    const y = parseInt(m1[3], 10)
    if (m > 12 && d <= 12) {
      const temp = d
      d = m
      m = temp
    }
    return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
  }

  // YYYY MM DD, YYYY.MM.DD, YYYY/MM/DD
  const m2 = s.match(/^(\d{4})[\s\.\/\-](\d{1,2})[\s\.\/\-](\d{1,2})$/)
  if (m2) {
    const y = parseInt(m2[1], 10)
    const m = parseInt(m2[2], 10)
    const d = parseInt(m2[3], 10)
    return `${y}-${String(m).padStart(2, '0')}-${String(d).padStart(2, '0')}`
  }

  // DD Mon YYYY e.g. 15 OCT 2007 or 15 OKT 2007
  const monthsMap: Record<string, number> = {
    JAN: 1, FEB: 2, MAR: 3, APR: 4, MAY: 5, JUN: 6,
    JUL: 7, AUG: 8, SEP: 9, OCT: 10, NOV: 11, DEC: 12,
    YAN: 1, FEV: 2, MART: 3, IYUN: 6, IYUL: 7, AVG: 8, SEN: 9, OKT: 10, NOY: 11, DEK: 12
  }
  const m3 = s.match(/^(\d{1,2})[\s\.\/\-]([A-Za-z]{3,5})[\s\.\/\-](\d{4})$/)
  if (m3) {
    const d = parseInt(m3[1], 10)
    const mon = m3[2].toUpperCase().slice(0, 3)
    const y = parseInt(m3[3], 10)
    if (monthsMap[mon]) {
      return `${y}-${String(monthsMap[mon]).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    }
  }

  return s
}

// Trigger AI extraction
const triggerExtraction = async () => {
  if (!selectedFile.value) return

  isExtracting.value = true
  extractError.value = null
  savedFields.value = {}

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('student_id', studentId.value)

    // Pass configured AI Settings
    formData.append('provider', aiSettings.value.provider)
    const activeModel = aiSettings.value.provider === 'openai'
      ? (aiSettings.value.openaiModel || 'gpt-4o')
      : (geminiModelSelect.value === 'custom' ? customModelId.value : (aiSettings.value.model || 'gemini-3.7-flash'))
    formData.append('model', activeModel)

    const activeApiKey = aiSettings.value.provider === 'openai'
      ? aiSettings.value.openaiApiKey
      : aiSettings.value.apiKey
    if (activeApiKey && activeApiKey.trim()) {
      formData.append('api_key', activeApiKey.trim())
    }

    const response = await studentsApi.extractDocument(formData)

    let docType = response.document_type || 'GENERAL DOCUMENT'
    let fieldsObj = response.fields || {}
    let detailsObj = response.field_details || {}

    // Client-side Parent Passport Safeguard (if not already isolated by backend)
    const docTypeUpper = (docType || '').toUpperCase()
    const isParentDoc = response.is_parent_passport || docTypeUpper.includes('PARENT') || docTypeUpper.includes('MOTHER') || docTypeUpper.includes('FATHER')
    if (!isParentDoc && student.value?.birthday && fieldsObj.DATE_OF_BIRTH && (docTypeUpper.includes('PASSPORT') || docTypeUpper.includes('ID'))) {
      const matchDoc = String(fieldsObj.DATE_OF_BIRTH).match(/\b(19\d\d|20\d\d)\b/)
      const matchStu = String(student.value.birthday).match(/\b(19\d\d|20\d\d)\b/)
      if (matchDoc && matchStu) {
        const docYear = parseInt(matchDoc[1], 10)
        const stuYear = parseInt(matchStu[1], 10)
        if (stuYear - docYear >= 15) {
          const sex = String(fieldsObj.SEX || '').toUpperCase()
          const fullName = (fieldsObj.FULL_NAME || fieldsObj.FATHER_FULLNAME || fieldsObj.MOTHER_FULLNAME || '').trim()
          const isFemale = sex.startsWith('F') || ['QIZI', 'KIZI', 'OVNA', 'EVNA', 'KYZY', 'AXON', 'KHON', 'QIZ'].some(q => fullName.toUpperCase().includes(q))
          const parentKey = isFemale ? 'MOTHER_FULLNAME' : 'FATHER_FULLNAME'
          docType = isFemale ? 'MOTHER_PASSPORT' : 'FATHER_PASSPORT'
          fieldsObj = { [parentKey]: fullName }
          detailsObj = { [parentKey]: { value: fullName, confidence: 0.98, validated: true, source: 'PARENT_PASSPORT' } }
        }
      }
    }

    extractedDocType.value = docType
    rawOcrText.value = response.ocr_text || ''
    extractionLatency.value = response.metadata?.latency_ms || null
    ocrEngineUsed.value = response.metadata?.ocr_engine || null

    const fieldsArr: ExtractedField[] = []

    if (fieldsObj && typeof fieldsObj === 'object') {
      for (const [k, v] of Object.entries(fieldsObj)) {
        if (v && String(v).trim()) {
          let fieldVal = String(v).trim()
          if (k.toUpperCase().includes('DATE') || k.toUpperCase().includes('BIRTH') || k.toUpperCase().includes('ENTRY') || k.toUpperCase().includes('GRADUATION')) {
            fieldVal = normalizeDate(fieldVal)
          }
          const detail = detailsObj[k]
          fieldsArr.push({
            key: k,
            value: fieldVal,
            confidence: detail?.confidence,
            validated: detail?.validated,
            source: detail?.source
          })
        }
      }
    }
    extractedFieldsList.value = fieldsArr
  } catch (err: any) {
    console.error('Extraction failed:', err)
    extractError.value = err.response?.data?.error || 'Failed to extract document information.'
  } finally {
    isExtracting.value = false
  }
}

// Save All Fields at once
const isSavingAll = ref(false)
const handleSaveAllFields = async () => {
  if (!student.value || extractedFieldsList.value.length === 0) return
  isSavingAll.value = true
  const updatePayload: Partial<Student> = {}
  const savedKeys: string[] = []

  for (const field of extractedFieldsList.value) {
    if (savedFields.value[field.key]) continue
    const cleanKey = field.key.replace(/_/g, ' ').toUpperCase().trim()
    const dbField = FIELD_MAPPING[cleanKey] || FIELD_MAPPING[field.key]
    if (!dbField) continue

    let finalValue: any = field.value.trim()
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
    } else if (['birthday', 'passport_issue_date', 'passport_expire_date', 'date_of_entry', 'date_of_graduation'].includes(dbField as string)) {
      finalValue = normalizeDate(finalValue)
    } else if (['full_name', 'address', 'final_school_name', 'major', 'father_name', 'mother_name'].includes(dbField as string)) {
      finalValue = finalValue.toUpperCase()
    }

    updatePayload[dbField] = finalValue
    savedKeys.push(field.key)
  }

  if (Object.keys(updatePayload).length === 0) {
    isSavingAll.value = false
    return
  }

  try {
    await studentsApi.updateStudent(studentId.value, updatePayload)
    for (const k of savedKeys) {
      savedFields.value[k] = true
    }
    await refetchStudent()
    queryClient.invalidateQueries({ queryKey: ['students'] })
    uiStore.addToast({
      type: 'success',
      title: 'All Fields Saved',
      message: `Successfully saved ${savedKeys.length} field(s) to student profile.`
    })
  } catch (err: any) {
    console.error('Failed to save all fields:', err)
    uiStore.addToast({
      type: 'error',
      title: 'Save All Failed',
      message: err.response?.data?.detail || 'Could not save all fields.'
    })
  } finally {
    isSavingAll.value = false
  }
}

// Language Certificate Identification & Auto-Filler Logic
const certBadgeColor = (type?: string) => {
  const t = (type || '').toUpperCase()
  if (t === 'TOPIK') return 'bg-[#de350b] text-white'
  if (t === 'IELTS') return 'bg-[#00b8d9] text-white'
  if (t === 'SAT') return 'bg-[#ff5630] text-white'
  if (t === 'SKA') return 'bg-indigo-600 text-white'
  if (t === 'TOEFL') return 'bg-purple-600 text-white'
  if (t === 'CEFR') return 'bg-emerald-600 text-white'
  return 'bg-amber-500 text-white'
}

const isCertificateDetected = computed(() => {
  if (!extractedDocType.value && extractedFieldsList.value.length === 0) return false
  const docType = (extractedDocType.value || '').toUpperCase()
  if (
    docType.includes('CERTIFICATE') ||
    docType.includes('TOPIK') ||
    docType.includes('IELTS') ||
    docType.includes('SAT') ||
    docType.includes('SKA') ||
    docType.includes('TOEFL') ||
    docType.includes('CEFR') ||
    docType.includes('SCORE REPORT')
  ) {
    return true
  }
  const keys = extractedFieldsList.value.map(f => f.key.toUpperCase())
  return keys.some(k => k.includes('CERTIFICATE') || k === 'CERTIFICATE_TYPE' || k === 'CERTIFICATE_SCORE')
})

const detectedCertData = computed(() => {
  const getVal = (possibleKeys: string[]) => {
    const found = extractedFieldsList.value.find(f =>
      possibleKeys.includes(f.key.toUpperCase().replace(/\s+/g, '_'))
    )
    return found ? found.value : ''
  }

  let type = getVal(['CERTIFICATE_TYPE', 'LANGUAGE_CERTIFICATE', 'CERTIFICATE', 'TEST_TYPE'])
  if (!type && extractedDocType.value) {
    for (const t of ['TOPIK', 'IELTS', 'SAT', 'SKA', 'TOEFL', 'CEFR']) {
      if (extractedDocType.value.toUpperCase().includes(t)) {
        type = t
        break
      }
    }
  }
  type = (type || '').toUpperCase().trim()

  let score = getVal(['CERTIFICATE_SCORE', 'SCORE', 'TOTAL_SCORE', 'BAND_SCORE', 'OVERALL_SCORE', 'OVERALL_BAND_SCORE', 'LEVEL', 'GRADE'])
  if (type === 'TOPIK' && score) {
    const m = score.match(/([1-6])/)
    if (m) score = m[1]
  }

  const testDate = normalizeDate(getVal(['CERTIFICATE_TEST_DATE', 'TEST_DATE', 'DATE_OF_TEST', 'DATE_OF_THE_ASSESSMENT', 'TEST_HELD_DATE', 'DATE_OF_EXAM']))
  let validDate = normalizeDate(getVal(['CERTIFICATE_VALID_DATE', 'VALID_DATE', 'VALID_UNTIL', 'EXPIRATION_DATE', 'PERIOD_OF_VALIDITY', 'VALID_TO']))

  // Auto-calculate +2 years minus 1 day if test_date exists but valid_date is missing
  if (testDate && !validDate && /^\d{4}-\d{2}-\d{2}$/.test(testDate)) {
    try {
      const parts = testDate.split('-').map(Number)
      const d = new Date(parts[0] + 2, parts[1] - 1, parts[2] - 1)
      const vy = d.getFullYear()
      const vm = String(d.getMonth() + 1).padStart(2, '0')
      const vd = String(d.getDate()).padStart(2, '0')
      validDate = `${vy}-${vm}-${vd}`
    } catch (e) {}
  }

  return {
    type,
    score,
    test_date: testDate,
    valid_date: validDate
  }
})

const certSlots = computed(() => [
  {
    slot: 1 as const,
    label: 'Certificate 1',
    currentType: student.value?.language_certificate,
    currentScore: student.value?.certificate_score,
    currentTestDate: student.value?.certificate_test_date,
    currentValidDate: student.value?.certificate_valid_date,
    isEmpty: !student.value?.language_certificate || student.value?.language_certificate === 'NO CERTIFICATE'
  },
  {
    slot: 2 as const,
    label: 'Certificate 2',
    currentType: student.value?.language_certificate_2,
    currentScore: student.value?.certificate_score_2,
    currentTestDate: student.value?.certificate_2_test_date,
    currentValidDate: student.value?.certificate_2_valid_date,
    isEmpty: !student.value?.language_certificate_2 || student.value?.language_certificate_2 === 'NO CERTIFICATE'
  },
  {
    slot: 3 as const,
    label: 'Certificate 3',
    currentType: student.value?.language_certificate_3,
    currentScore: student.value?.certificate_score_3,
    currentTestDate: student.value?.certificate_3_test_date,
    currentValidDate: student.value?.certificate_3_valid_date,
    isEmpty: !student.value?.language_certificate_3 || student.value?.language_certificate_3 === 'NO CERTIFICATE'
  }
])

const recommendedCertSlot = computed<1 | 2 | 3>(() => {
  if (certSlots.value[0].isEmpty) return 1
  if (certSlots.value[1].isEmpty) return 2
  if (certSlots.value[2].isEmpty) return 3
  return 1
})

const savingCertSlot = ref<number | null>(null)
const savedCertSlot = ref<number | null>(null)

const handleSaveToCertSlot = async (slot: 1 | 2 | 3) => {
  if (!student.value || !detectedCertData.value.type) return
  savingCertSlot.value = slot

  const cData = detectedCertData.value
  const updatePayload: Partial<Student> = {}

  if (slot === 1) {
    updatePayload.language_certificate = cData.type
    updatePayload.certificate_score = cData.score || null
    updatePayload.certificate_test_date = cData.test_date || null
    updatePayload.certificate_valid_date = cData.valid_date || null
  } else if (slot === 2) {
    updatePayload.language_certificate_2 = cData.type
    updatePayload.certificate_score_2 = cData.score || null
    updatePayload.certificate_2_test_date = cData.test_date || null
    updatePayload.certificate_2_valid_date = cData.valid_date || null
  } else {
    updatePayload.language_certificate_3 = cData.type
    updatePayload.certificate_score_3 = cData.score || null
    updatePayload.certificate_3_test_date = cData.test_date || null
    updatePayload.certificate_3_valid_date = cData.valid_date || null
  }

  try {
    await studentsApi.updateStudent(studentId.value, updatePayload)
    savedCertSlot.value = slot
    await refetchStudent()
    queryClient.invalidateQueries({ queryKey: ['students'] })
    uiStore.addToast({
      type: 'success',
      title: `Saved to Certificate ${slot}`,
      message: `Successfully updated Certificate ${slot} to ${cData.type} (Score: ${cData.score || '—'})`
    })

    // Mark all certificate-related fields as saved
    extractedFieldsList.value.forEach(f => {
      const k = f.key.toUpperCase()
      if (k.includes('CERTIFICATE') || k.includes('SCORE') || k.includes('TEST_DATE') || k.includes('VALID_DATE')) {
        savedFields.value[f.key] = true
      }
    })
  } catch (err: any) {
    console.error(`Failed to save to Certificate ${slot}:`, err)
    uiStore.addToast({
      type: 'error',
      title: 'Save Failed',
      message: err.response?.data?.detail || `Could not save to Certificate ${slot}.`
    })
  } finally {
    savingCertSlot.value = null
  }
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
  } else if (['birthday', 'passport_issue_date', 'passport_expire_date', 'date_of_entry', 'date_of_graduation'].includes(dbField as string)) {
    finalValue = normalizeDate(finalValue)
  } else if (['full_name', 'address', 'final_school_name', 'major', 'father_name', 'mother_name'].includes(dbField as string)) {
    finalValue = finalValue.toUpperCase()
  }

  savingFieldKey.value = fieldKey
  try {
    const updatePayload: Partial<Student> = {
      [dbField]: finalValue
    }

    // Auto-lookup schools directory if saving final_school_name
    if (dbField === 'final_school_name') {
      updatePayload.educational_background = finalValue
      const cleanSchool = finalValue.toUpperCase().trim()

      let match: any = null
      if (dbSchools.value && Array.isArray(dbSchools.value)) {
        match = dbSchools.value.find((s: any) => {
          const name = (s.name || '').toUpperCase().trim()
          return name === cleanSchool || cleanSchool.includes(name) || name.includes(cleanSchool)
        })
      }
      if (!match) {
        match = Object.values(BUILTIN_SCHOOL_DIRECTORY).find((s: any) => {
          const name = (s.name || '').toUpperCase().trim()
          return name === cleanSchool || cleanSchool.includes(name) || name.includes(cleanSchool)
        })
      }

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
  <div class="space-y-4">
    <!-- Student Header Banner with Back Button & AI Settings Toggle -->
    <div
      class="p-3.5 sm:p-4 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xs flex items-center justify-between gap-4 flex-wrap"
    >
      <div class="flex items-center gap-3 min-w-0">
        <!-- Back Button -->
        <button
          @click="router.push('/students')"
          class="p-2.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-850 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 transition-all cursor-pointer shadow-2xs hover:scale-[1.02] active:scale-[0.98] shrink-0"
          title="Back to Students Dashboard"
        >
          <ArrowLeft class="w-4 h-4" />
        </button>

        <template v-if="student">
          <div class="w-11 h-11 sm:w-12 sm:h-12 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-600 dark:text-blue-400 flex items-center justify-center font-black text-base sm:text-lg shrink-0">
            {{ getInitials(student.full_name) }}
          </div>
          <div class="min-w-0">
            <h2 class="text-sm sm:text-base font-extrabold text-zinc-900 dark:text-zinc-100 tracking-tight truncate">
              {{ student.full_name || 'Unnamed Student' }}
            </h2>
            <div class="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs font-semibold text-zinc-500 dark:text-zinc-400 mt-0.5">
              <span>ID: <strong class="text-blue-600 dark:text-blue-400 font-mono">{{ student.id }}</strong></span>
              <span class="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700 hidden sm:inline-block" />
              <span>Passport: <strong class="text-zinc-800 dark:text-zinc-200">{{ student.passport || '—' }}</strong></span>
              <span class="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-700 hidden sm:inline-block" />
              <span>Tariff: <strong class="text-zinc-800 dark:text-zinc-200">{{ student.tariff || '—' }}</strong></span>
            </div>
          </div>
        </template>
        <template v-else-if="isStudentLoading">
          <div class="flex items-center gap-3 min-w-0">
            <div class="w-11 h-11 rounded-2xl bg-zinc-100 dark:bg-zinc-800 animate-pulse shrink-0"></div>
            <div class="space-y-1.5">
              <div class="w-36 h-4 bg-zinc-200 dark:bg-zinc-800 rounded-md animate-pulse"></div>
              <div class="w-24 h-3 bg-zinc-100 dark:bg-zinc-800 rounded-md animate-pulse"></div>
            </div>
          </div>
        </template>
        <template v-else>
          <div class="min-w-0">
            <h2 class="text-sm sm:text-base font-extrabold text-zinc-900 dark:text-zinc-100 tracking-tight">
              Fill by Document (Student ID: {{ studentId }})
            </h2>
          </div>
        </template>
      </div>

      <!-- Right Header Actions: Active Model Badge + AI Settings Button -->
      <div class="flex items-center gap-2.5 shrink-0">
        <span class="hidden md:inline-flex px-3 py-1.5 rounded-xl bg-zinc-100 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-[11px] font-bold text-zinc-600 dark:text-zinc-300 shadow-2xs font-mono">
          Model: <span class="text-brand-500 font-extrabold ml-1">{{ aiSettings.provider === 'openai' ? `OpenAI (${aiSettings.openaiModel})` : `Gemini (${geminiModelSelect === 'custom' ? customModelId : aiSettings.model})` }}</span>
        </span>

        <button
          @click="toggleSettings"
          :class="[
            'inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all shadow-2xs cursor-pointer active:scale-[0.98]',
            isSettingsOpen
              ? 'bg-brand-500 text-white shadow-brand-500/25'
              : 'bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-750 text-zinc-800 dark:text-zinc-200 border border-zinc-200 dark:border-zinc-700'
          ]"
        >
          <Sliders class="w-3.5 h-3.5" />
          <span>AI Settings</span>
        </button>
      </div>
    </div>

    <!-- Collapsible AI Settings Panel -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2 scale-[0.99]"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 -translate-y-2 scale-[0.99]"
    >
      <div
        v-if="isSettingsOpen"
        class="p-5 rounded-2xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 shadow-xl space-y-5"
      >
        <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800 pb-3">
          <h3 class="text-xs font-extrabold text-brand-500 uppercase tracking-wider flex items-center gap-2">
            <Cpu class="w-4 h-4" />
            AI Extraction Configuration
          </h3>
          <span class="text-[10px] text-zinc-400 font-mono font-semibold">Changes sync locally</span>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <!-- Active Provider Selector -->
          <div class="space-y-1.5">
            <label class="text-[11px] uppercase font-bold tracking-wider text-zinc-500 dark:text-zinc-400">
              Active Provider
            </label>
            <div class="bg-zinc-100 dark:bg-zinc-850 p-1 rounded-xl border border-zinc-200 dark:border-zinc-700 flex h-10 shadow-inner">
              <button
                type="button"
                @click="tempSettings.provider = 'gemini'"
                :class="[
                  'flex-1 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-1.5',
                  tempSettings.provider === 'gemini'
                    ? 'bg-white dark:bg-zinc-900 text-purple-600 dark:text-purple-400 shadow-sm border border-zinc-200 dark:border-zinc-800'
                    : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100'
                ]"
              >
                <span>Google Gemini</span>
              </button>
              <button
                type="button"
                @click="tempSettings.provider = 'openai'"
                :class="[
                  'flex-1 rounded-lg text-xs font-bold transition-all cursor-pointer flex items-center justify-center gap-1.5',
                  tempSettings.provider === 'openai'
                    ? 'bg-white dark:bg-zinc-900 text-emerald-600 dark:text-emerald-400 shadow-sm border border-zinc-200 dark:border-zinc-800'
                    : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100'
                ]"
              >
                <span>OpenAI GPT</span>
              </button>
            </div>
          </div>

          <!-- AI Model Selector -->
          <div class="space-y-1.5">
            <label class="text-[11px] uppercase font-bold tracking-wider text-zinc-500 dark:text-zinc-400">
              AI Model
            </label>
            <div v-if="tempSettings.provider === 'openai'">
              <select
                v-model="tempSettings.openaiModel"
                class="bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-900 dark:text-zinc-100 p-2.5 rounded-xl focus:outline-none focus:border-brand-500 font-semibold cursor-pointer w-full h-10 shadow-2xs"
              >
                <option value="gpt-4o">GPT-4o (Recommended) — High Accuracy</option>
                <option value="gpt-4o-mini">GPT-4o Mini — Fastest & Cheapest</option>
              </select>
            </div>
            <div v-else class="space-y-2">
              <select
                v-model="geminiModelSelect"
                @change="tempSettings.model = geminiModelSelect === 'custom' ? (customModelId || 'gemini-3.7-flash') : geminiModelSelect"
                class="bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 text-xs text-zinc-900 dark:text-zinc-100 p-2.5 rounded-xl focus:outline-none focus:border-brand-500 font-semibold cursor-pointer w-full h-10 shadow-2xs"
              >
                <optgroup label="🌟 Gemini 3.x Series (Newest)">
                  <option value="gemini-3.7-flash">Gemini 3.7 Flash (Recommended — State-of-the-Art)</option>
                  <option value="gemini-3.5-flash">Gemini 3.5 Flash</option>
                  <option value="gemini-3.1-pro">Gemini 3.1 Pro</option>
                  <option value="gemini-3.1-flash-lite">Gemini 3.1 Flash Lite</option>
                </optgroup>
                <optgroup label="⚡ Gemini 2.x Series">
                  <option value="gemini-2.5-flash">Gemini 2.5 Flash</option>
                  <option value="gemini-2.5-pro">Gemini 2.5 Pro</option>
                  <option value="gemini-2.0-flash">Gemini 2.0 Flash</option>
                  <option value="gemini-2.5-flash-lite">Gemini 2.5 Flash Lite</option>
                </optgroup>
                <optgroup label="Legacy & Custom">
                  <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                  <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                  <option value="custom">Custom Model ID...</option>
                </optgroup>
              </select>
              <input
                v-if="geminiModelSelect === 'custom'"
                v-model="customModelId"
                @input="tempSettings.model = customModelId"
                type="text"
                placeholder="Enter custom Gemini model ID (e.g. gemini-2.5-flash)..."
                class="w-full px-3 py-2 text-xs bg-zinc-50 dark:bg-zinc-850 rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>
        </div>

        <!-- Custom API Key Input -->
        <div class="space-y-1.5">
          <label class="text-[11px] uppercase font-bold tracking-wider text-zinc-500 dark:text-zinc-400 flex items-center justify-between">
            <span>{{ tempSettings.provider === 'openai' ? 'OpenAI API Key (Optional)' : 'Gemini API Key (Required for Gemini)' }}</span>
            <span class="text-[10px] text-zinc-400 font-normal">Leave blank to use default server key</span>
          </label>
          <div class="relative">
            <input
              v-if="tempSettings.provider === 'openai'"
              v-model="tempSettings.openaiApiKey"
              :type="showApiKey ? 'text' : 'password'"
              placeholder="Enter custom OpenAI API key (sk-proj-...)..."
              class="w-full pl-3.5 pr-10 py-2.5 text-xs bg-zinc-50 dark:bg-zinc-850 rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:border-brand-500 font-mono"
            />
            <input
              v-else
              v-model="tempSettings.apiKey"
              :type="showApiKey ? 'text' : 'password'"
              placeholder="Enter your Gemini API key (AIzaSy...)..."
              class="w-full pl-3.5 pr-10 py-2.5 text-xs bg-zinc-50 dark:bg-zinc-850 rounded-xl border border-zinc-200 dark:border-zinc-700 text-zinc-900 dark:text-zinc-100 placeholder:text-zinc-400 focus:outline-none focus:border-brand-500 font-mono"
            />
            <button
              type="button"
              @click="showApiKey = !showApiKey"
              class="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 cursor-pointer p-1"
            >
              <Eye v-if="showApiKey" class="w-4 h-4" />
              <EyeOff v-else class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- Extraction Options Toggles -->
        <div class="pt-2 border-t border-zinc-100 dark:border-zinc-800 flex flex-wrap items-center justify-between gap-4">
          <div class="flex items-center gap-6">
            <label class="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                v-model="tempSettings.normalizeDates"
                class="rounded border-zinc-300 text-brand-500 focus:ring-brand-500 h-4 w-4"
              />
              <span class="text-xs font-semibold text-zinc-700 dark:text-zinc-300">Normalize Dates (YYYY-MM-DD)</span>
            </label>
            <label class="flex items-center gap-2 cursor-pointer select-none">
              <input
                type="checkbox"
                v-model="tempSettings.mergeNames"
                class="rounded border-zinc-300 text-brand-500 focus:ring-brand-500 h-4 w-4"
              />
              <span class="text-xs font-semibold text-zinc-700 dark:text-zinc-300">Auto-Format Uppercase</span>
            </label>
          </div>

          <!-- Save / Cancel Buttons -->
          <div class="flex items-center gap-2">
            <button
              type="button"
              @click="isSettingsOpen = false"
              class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-800 text-xs font-bold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="handleSaveSettings"
              class="px-5 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold shadow-md shadow-brand-500/20 cursor-pointer transition-all active:scale-[0.98]"
            >
              Save Settings
            </button>
          </div>
        </div>
      </div>
    </Transition>

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
              accept=".jpg,.jpeg,.png,.webp"
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
              Supports Passport photo, Diploma, Shahodatnoma, or any screenshot.
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

              <!-- Image Visual Preview -->
              <img
                v-if="previewUrl"
                :src="previewUrl"
                alt="Document Preview"
                class="max-h-[380px] w-auto object-contain rounded-xl shadow-sm"
              />

              <!-- Fallback -->
              <div v-else class="text-center space-y-2 p-6">
                <FileText class="w-12 h-12 text-brand-500 mx-auto" />
                <p class="text-xs font-bold text-zinc-800 dark:text-zinc-200">
                  {{ selectedFile?.name }}
                </p>
                <p class="text-[10px] text-zinc-400 font-mono">
                  {{ selectedFile ? (selectedFile.size / 1024).toFixed(1) : '0' }} KB
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
              <span>{{ isExtracting ? 'Extracting with AI...' : 'Extract Information from Document' }}</span>
            </button>
          </div>

          <!-- Enhanced Loading Shimmer Overlay -->
          <div
            v-if="isExtracting"
            class="absolute inset-0 bg-white/95 dark:bg-zinc-950/95 backdrop-blur-md flex flex-col items-center justify-center p-6 z-20 space-y-6 transition-all duration-300"
          >
            <!-- AI Pulse Icon with Scanning Line -->
            <div class="relative w-20 h-20 flex items-center justify-center">
              <div class="absolute inset-0 bg-brand-500/20 rounded-full animate-ping opacity-75"></div>
              <div class="absolute inset-2 bg-brand-500/40 rounded-full animate-pulse"></div>
              <div class="relative w-14 h-14 bg-white dark:bg-zinc-900 border-2 border-brand-500 rounded-2xl shadow-[0_0_25px_rgba(59,130,246,0.5)] flex items-center justify-center overflow-hidden">
                 <Sparkles class="w-6 h-6 text-brand-500 animate-pulse relative z-10" />
                 <!-- Scanning line effect -->
                 <div class="absolute inset-0 bg-gradient-to-b from-transparent via-brand-500/40 to-transparent h-[200%] animate-scanline"></div>
              </div>
            </div>

            <div class="text-center space-y-2">
              <h4 class="text-sm font-extrabold text-zinc-900 dark:text-zinc-100 flex items-center justify-center gap-2">
                Analyzing Document with AI
              </h4>
              <p class="text-xs text-zinc-500 dark:text-zinc-400 max-w-[280px] mx-auto leading-relaxed">
                Applying optical character recognition and natural language processing to extract structured profile fields...
              </p>
            </div>

            <!-- Indeterminate Progress Bar -->
            <div class="w-64 h-1.5 bg-zinc-200 dark:bg-zinc-800 rounded-full overflow-hidden relative shadow-inner">
              <div class="absolute top-0 bottom-0 left-0 w-1/2 bg-brand-500 rounded-full animate-indeterminate"></div>
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
            <div class="flex items-center gap-2">
              <button
                v-if="extractedFieldsList.length > 0 && !isExtracting"
                @click="handleSaveAllFields"
                :disabled="isSavingAll"
                class="px-2.5 py-1 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] uppercase font-extrabold tracking-wider transition-all flex items-center gap-1.5 cursor-pointer shadow-xs active:scale-[0.96] disabled:opacity-50"
              >
                <Loader2 v-if="isSavingAll" class="w-3.5 h-3.5 animate-spin" />
                <CheckCheck v-else class="w-3.5 h-3.5" />
                <span>Save All Fields</span>
              </button>
              <span
                v-if="extractionLatency"
                class="px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-500 text-[10px] font-mono font-bold"
              >
                {{ extractionLatency }}ms
              </span>
              <span
                v-if="extractedDocType"
                class="px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 text-[10px] uppercase font-extrabold tracking-wider"
              >
                Type: {{ extractedDocType }}
              </span>
            </div>
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
            <!-- Parent Passport Alert Banner -->
            <div
              v-if="extractedDocType && (extractedDocType.includes('MOTHER') || extractedDocType.includes('FATHER') || extractedDocType.includes('PARENT'))"
              class="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-900 dark:text-amber-200 text-xs flex items-start gap-2.5"
            >
              <span class="text-base leading-none">👨‍👩‍👧</span>
              <div class="space-y-0.5">
                <p class="font-extrabold text-[11px] uppercase tracking-wide text-amber-700 dark:text-amber-300">
                  {{ extractedDocType.includes('MOTHER') ? "Mother's Passport Detected" : "Father's Passport Detected" }} (15+ Years Older)
                </p>
                <p class="text-[11px] text-amber-800/80 dark:text-amber-300/80">
                  The document owner is 15+ years older than the student. Personal identity fields (Passport No, DOB, Sex) have been isolated so they will not overwrite the student's personal identity records.
                </p>
              </div>
            </div>

            <!-- Language Certificate Auto-Filler Banner & Card (Compact) -->
            <div
              v-if="isCertificateDetected && detectedCertData.type"
              class="p-3 rounded-xl bg-amber-500/10 dark:bg-amber-500/10 border border-amber-500/30 dark:border-amber-500/25 text-zinc-900 dark:text-zinc-100 shadow-xs space-y-2.5"
            >
              <!-- Top Compact Header with Inline Metadata -->
              <div class="flex items-center justify-between flex-wrap gap-2">
                <!-- Left: Title, Type Badge & Score -->
                <div class="flex items-center gap-2 flex-wrap">
                  <div class="w-6 h-6 rounded-lg bg-amber-500/20 text-amber-600 dark:text-amber-400 flex items-center justify-center shrink-0">
                    <Award class="w-3.5 h-3.5" />
                  </div>
                  <span class="text-xs font-black uppercase tracking-wider text-amber-800 dark:text-amber-300">
                    Language Certificate:
                  </span>
                  <span class="px-2 py-0.5 rounded-md text-[11px] font-black uppercase shadow-2xs" :class="certBadgeColor(detectedCertData.type)">
                    {{ detectedCertData.type }}
                  </span>
                  <span class="px-2 py-0.5 rounded-md text-[11px] font-mono font-black bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
                    {{ detectedCertData.type === 'TOPIK' ? `Level ${detectedCertData.score || '—'}` : `Score: ${detectedCertData.score || '—'}` }}
                  </span>
                </div>

                <!-- Right: Test Date & Validity Date -->
                <div class="flex items-center gap-3 text-[11px] font-medium text-zinc-600 dark:text-zinc-400">
                  <span v-if="detectedCertData.test_date" class="flex items-center gap-1">
                    <Calendar class="w-3.5 h-3.5 text-zinc-400" />
                    <span class="text-zinc-400 text-[10px] font-bold uppercase">Test:</span>
                    <span class="font-bold text-zinc-700 dark:text-zinc-300">{{ detectedCertData.test_date }}</span>
                  </span>
                  <span v-if="detectedCertData.valid_date" class="flex items-center gap-1">
                    <Calendar class="w-3.5 h-3.5 text-emerald-500" />
                    <span class="text-zinc-400 text-[10px] font-bold uppercase">Valid:</span>
                    <span class="font-bold text-emerald-600 dark:text-emerald-400">{{ detectedCertData.valid_date }}</span>
                  </span>
                </div>
              </div>

              <!-- Compact Save Slots (3 columns side-by-side) -->
              <div class="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  v-for="item in certSlots"
                  :key="item.slot"
                  type="button"
                  @click="handleSaveToCertSlot(item.slot)"
                  :disabled="savingCertSlot === item.slot || savedCertSlot === item.slot"
                  :class="[
                    'px-2.5 py-2 rounded-lg border text-left transition-all cursor-pointer flex items-center justify-between gap-2 group/btn select-none',
                    savedCertSlot === item.slot
                      ? 'border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 shadow-2xs'
                      : item.slot === recommendedCertSlot && item.isEmpty
                        ? 'border-amber-500/80 bg-white dark:bg-zinc-800 hover:border-amber-500 hover:shadow-xs ring-1 ring-amber-500/25 active:scale-[0.98]'
                        : 'border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-850 hover:border-zinc-300 dark:hover:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 active:scale-[0.98]'
                  ]"
                >
                  <div class="min-w-0 flex-1">
                    <div class="flex items-center gap-1.5">
                      <span class="text-[11px] font-black uppercase tracking-wider flex items-center gap-1" :class="savedCertSlot === item.slot ? 'text-emerald-600' : 'text-zinc-800 dark:text-zinc-200'">
                        <Award class="w-3 h-3" :class="item.slot === 1 ? 'text-amber-500' : item.slot === 2 ? 'text-cyan-500' : 'text-orange-500'" />
                        <span>Cert {{ item.slot }}</span>
                      </span>
                      <span
                        v-if="item.slot === recommendedCertSlot && item.isEmpty && savedCertSlot !== item.slot"
                        class="px-1 py-0.2 rounded text-[7.5px] font-black uppercase tracking-tight bg-amber-500 text-white"
                      >
                        Rec
                      </span>
                    </div>
                    <div class="text-[10px] truncate leading-tight mt-0.5">
                      <span v-if="savedCertSlot === item.slot" class="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-0.5">
                        <CheckCircle2 class="w-3 h-3" />
                        Applied!
                      </span>
                      <span v-else-if="item.isEmpty" class="italic text-zinc-400 dark:text-zinc-500">
                        Empty (Click to apply)
                      </span>
                      <span v-else class="text-zinc-600 dark:text-zinc-400 font-medium truncate block">
                        {{ item.currentType }} ({{ item.currentScore || '—' }})
                      </span>
                    </div>
                  </div>

                  <div class="shrink-0 flex items-center">
                    <Loader2 v-if="savingCertSlot === item.slot" class="w-3.5 h-3.5 animate-spin text-amber-500" />
                    <span
                      v-else-if="savedCertSlot !== item.slot"
                      class="px-2 py-1 rounded text-[9.5px] font-black uppercase tracking-wide bg-zinc-100 dark:bg-zinc-700/80 text-zinc-600 dark:text-zinc-300 group-hover/btn:bg-amber-500 group-hover/btn:text-white transition-colors flex items-center gap-1"
                    >
                      <span>Apply</span>
                      <ArrowRight class="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>
              </div>
            </div>

            <div
              v-for="(field, idx) in extractedFieldsList"
              :key="idx"
              :class="[
                'p-3 rounded-xl border flex items-center justify-between gap-3 transition-all',
                savedFields[field.key]
                  ? 'border-emerald-500/40 bg-emerald-50/50 dark:bg-emerald-950/20'
                  : 'border-zinc-200 dark:border-zinc-800 bg-zinc-50/60 dark:bg-zinc-850/60 hover:border-zinc-300 dark:hover:border-zinc-700'
              ]"
            >
              <!-- Field Details -->
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-1.5 flex-wrap mb-0.5">
                  <span class="text-[10px] font-extrabold uppercase tracking-wider text-brand-500">
                    {{ field.key.replace(/_/g, ' ') }}
                  </span>
                </div>
                <span
                  class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block break-words"
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
                  :disabled="savedFields[field.key] || savingFieldKey === field.key"
                  @click="handleSaveFieldToProfile(field.key, field.value)"
                  :class="[
                    'px-3 py-1.5 rounded-lg text-[10px] font-extrabold uppercase transition-all flex items-center gap-1 select-none border cursor-pointer',
                    savedFields[field.key]
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20 cursor-default'
                      : 'bg-emerald-600 hover:bg-emerald-500 border-emerald-600 text-white shadow-xs active:scale-[0.96]'
                  ]"
                >
                  <Loader2 v-if="savingFieldKey === field.key" class="w-3 h-3 animate-spin" />
                  <template v-else-if="savedFields[field.key]">
                    <CheckCircle2 class="w-3 h-3 text-emerald-500" />
                    <span>Saved</span>
                  </template>
                  <template v-else>
                    <span>Save To &gt;&gt;</span>
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

<style scoped>
@keyframes indeterminate {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(50%); }
  100% { transform: translateX(200%); }
}
.animate-indeterminate {
  animation: indeterminate 1.5s infinite ease-in-out;
}
@keyframes scanline {
  0% { transform: translateY(-100%); }
  100% { transform: translateY(100%); }
}
.animate-scanline {
  animation: scanline 2s infinite linear;
}
</style>
