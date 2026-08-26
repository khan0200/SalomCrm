<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import {
  FileSpreadsheet,
  Upload,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Download,
  RefreshCw,
  Sparkles,
  Settings2,
  Users,
  Search,
  Check,
  Eye,
  SlidersHorizontal,
  ChevronDown,
  Trash2,
  FileText,
  Info
} from 'lucide-vue-next'
import { excelFillApi, type ExcelAnalysisResult, type ColumnMappingConfig, type ExcelSheet } from '@/api/excelFill'
import { studentsApi } from '@/api/students'
import type { Student } from '@/types'

// ─── Step State ─────────────────────────────────────────────────────────────
const currentStep = ref<1 | 2 | 3 | 4>(1)

// ─── File & Template State ──────────────────────────────────────────────────
const uploadedFile = ref<File | null>(null)
const isAnalyzing = ref(false)
const analysisError = ref<string | null>(null)
const analysisData = ref<ExcelAnalysisResult | null>(null)
const selectedSheetName = ref<string>('')
const isDragging = ref(false)

// ─── Mappings State ─────────────────────────────────────────────────────────
const columnMappings = ref<ColumnMappingConfig[]>([])
const onlyMappedFilter = ref(false)
const manualHeaderRow = ref<number | null>(null)

// ─── Student Selection State ────────────────────────────────────────────────
const searchQuery = ref('')
const selectedStudentIds = ref<Set<string>>(new Set())
const selectedLevelFilter = ref<string>('ALL')
const selectedTariffFilter = ref<string>('ALL')

// ─── Generation & Output State ──────────────────────────────────────────────
const fillMode = ref<'append' | 'overwrite'>('append')
const autoIncrementSeq = ref(true)
const startRowOverride = ref<number | null>(null)
const isGenerating = ref(false)
const generationSuccess = ref(false)
const downloadUrl = ref<string | null>(null)
const downloadedFileName = ref<string>('')

// ─── Fetch Students from Master CRM ─────────────────────────────────────────
const { data: allStudentsData, isLoading: isLoadingStudents } = useQuery({
  queryKey: ['all-students-master-excel-fill'],
  queryFn: () => studentsApi.getStudents({
    page: 1,
    page_size: 5000,
    folder: 'all',
    include_archive: false,
  }),
  staleTime: 1000 * 60 * 5,
})

const allStudents = computed<Student[]>(() => (allStudentsData.value?.results || []).filter(s => !s.is_deleted))

// Filter students for Step 3
const filteredStudents = computed(() => {
  let list = allStudents.value
  
  if (selectedLevelFilter.value !== 'ALL') {
    list = list.filter(s => s.level === selectedLevelFilter.value)
  }
  if (selectedTariffFilter.value !== 'ALL') {
    list = list.filter(s => s.tariff === selectedTariffFilter.value)
  }

  const query = searchQuery.value.trim().toLowerCase()
  if (query) {
    list = list.filter(s =>
      s.full_name?.toLowerCase().includes(query) ||
      s.korean_name?.toLowerCase().includes(query) ||
      s.passport?.toLowerCase().includes(query) ||
      s.id?.toLowerCase().includes(query) ||
      s.phone1?.toLowerCase().includes(query)
    )
  }

  return list
})

// Current selected sheet object
const currentSheet = computed<ExcelSheet | null>(() => {
  if (!analysisData.value?.sheets) return null
  return analysisData.value.sheets.find(s => s.name === selectedSheetName.value) || analysisData.value.sheets[0] || null
})

// ─── File Upload & Inspection Handler ────────────────────────────────────────
const handleFileUpload = async (file: File) => {
  if (!file.name.toLowerCase().match(/\.(xlsx|xlsm|xltx)$/)) {
    analysisError.value = "Faqat .xlsx yoki .xlsm formatidagi Excel fayllari qabul qilinadi"
    return
  }

  uploadedFile.value = file
  isAnalyzing.value = true
  analysisError.value = null

  try {
    const res = await excelFillApi.analyzeTemplate(file)
    analysisData.value = res
    if (res.sheets.length > 0) {
      selectedSheetName.value = res.sheets[0].name
      initMappingsFromSheet(res.sheets[0])
    }
  } catch (err: any) {
    console.error('Error analyzing template:', err)
    analysisError.value = err.response?.data?.error || err.message || "Faylni tahlil qilishda xatolik yuz berdi"
  } finally {
    isAnalyzing.value = false
  }
}

const onDropFile = (e: DragEvent) => {
  isDragging.value = false
  if (e.dataTransfer?.files && e.dataTransfer.files.length > 0) {
    handleFileUpload(e.dataTransfer.files[0])
  }
}

const onFileInputChange = (e: Event) => {
  const target = e.target as HTMLInputElement
  if (target.files && target.files.length > 0) {
    handleFileUpload(target.files[0])
  }
}

// ─── Initialize / Switch Sheet Mappings ─────────────────────────────────────
const initMappingsFromSheet = (sheet: ExcelSheet) => {
  columnMappings.value = sheet.columns
    .filter(col => col.header_name && col.header_name.trim() !== '')
    .map(col => {
      // Detect smart format rules based on field
      const isDateField = ['birthday', 'passport_issue_date', 'passport_expire_date'].includes(col.suggested_field)
      const isGenderField = col.suggested_field === 'gender'

      // Check if header or sheet has Korean language indicators
      const isKoreanHeader = /[\uac00-\ud7a3]/.test(col.header_name || '')

      return {
        col_idx: col.col_idx,
        col_letter: col.col_letter,
        header_name: col.header_name,
        field: col.suggested_field || '_skip',
        static_value: '',
        fallback: '',
        format_rules: {
          dateFormat: isKoreanHeader ? 'YYYY.MM.DD' : 'YYYY-MM-DD',
          genderFormat: isKoreanHeader ? '남/여' : 'MALE/FEMALE',
          phoneFormat: 'original',
        }
      }
    })
}

watch(selectedSheetName, (newSheet) => {
  if (analysisData.value && newSheet) {
    const s = analysisData.value.sheets.find(item => item.name === newSheet)
    if (s) initMappingsFromSheet(s)
  }
})

// Mapped vs Skipped count
const mappedCount = computed(() => columnMappings.value.filter(m => m.field !== '_skip').length)
const skippedCount = computed(() => columnMappings.value.filter(m => m.field === '_skip').length)

// Filtered mappings list (never show columns without headers)
const visibleMappings = computed(() => {
  let list = columnMappings.value.filter(m => m.header_name && m.header_name.trim() !== '')
  if (onlyMappedFilter.value) {
    list = list.filter(m => m.field !== '_skip')
  }
  return list
})

// Group CRM fields by category for clean dropdown
const categorizedCrmFields = computed(() => {
  if (!analysisData.value?.available_fields) return {}
  const groups: Record<string, { key: string; label: string }[]> = {
    'Tizim / Maxsus': [],
    'Shaxsiy ma\'lumotlar': [],
    'Pasport ma\'lumotlari': [],
    'Aloqa ma\'lumotlari': [],
    'Ota-ona ma\'lumotlari': [],
    'Ta\'lim va Sertifikatlar': [],
  }

  analysisData.value.available_fields.forEach(f => {
    if (f.category === 'system') groups['Tizim / Maxsus'].push(f)
    else if (f.category === 'personal') groups['Shaxsiy ma\'lumotlar'].push(f)
    else if (f.category === 'passport') groups['Pasport ma\'lumotlari'].push(f)
    else if (f.category === 'contacts') groups['Aloqa ma\'lumotlari'].push(f)
    else if (f.category === 'parents') groups['Ota-ona ma\'lumotlari'].push(f)
    else if (f.category === 'education') groups['Ta\'lim va Sertifikatlar'].push(f)
  })

  return groups
})

// ─── Student Selection Handlers ─────────────────────────────────────────────
const toggleSelectAllStudents = () => {
  if (selectedStudentIds.value.size === filteredStudents.value.length) {
    selectedStudentIds.value.clear()
  } else {
    filteredStudents.value.forEach(s => selectedStudentIds.value.add(s.id))
  }
}

const toggleStudentSelection = (id: string) => {
  if (selectedStudentIds.value.has(id)) {
    selectedStudentIds.value.delete(id)
  } else {
    selectedStudentIds.value.add(id)
  }
}

const isStudentSelected = (id: string) => selectedStudentIds.value.has(id)

// ─── Validation: Detect Missing Fields in Selected Students ─────────────────
const validationReport = computed(() => {
  const activeFields = columnMappings.value
    .map(m => m.field)
    .filter(f => !['_skip', '_sequence_no', '_static_value'].includes(f))

  const selectedList = allStudents.value.filter(s => selectedStudentIds.value.has(s.id))
  const issues: { field: string; missingCount: number; studentNames: string[] }[] = []

  activeFields.forEach(fieldKey => {
    const missingStudents = selectedList.filter(s => {
      const val = (s as any)[fieldKey]
      return val === null || val === undefined || String(val).trim() === ''
    })

    if (missingStudents.length > 0) {
      const fieldObj = analysisData.value?.available_fields.find(f => f.key === fieldKey)
      issues.push({
        field: fieldObj?.label || fieldKey,
        missingCount: missingStudents.length,
        studentNames: missingStudents.slice(0, 3).map(s => s.full_name || s.id)
      })
    }
  })

  return issues
})

// ─── Generate & Download Filled Excel ───────────────────────────────────────
const handleGenerateExcel = async () => {
  if (!uploadedFile.value || selectedStudentIds.value.size === 0) return

  isGenerating.value = true
  generationSuccess.value = false

  try {
    const blob = await excelFillApi.generateFilledExcel({
      file: uploadedFile.value,
      sheet_name: selectedSheetName.value,
      column_mappings: columnMappings.value,
      student_ids: Array.from(selectedStudentIds.value),
      fill_mode: fillMode.value,
      start_row: startRowOverride.value || undefined,
      auto_increment_sequence: autoIncrementSeq.value,
    })

    const originalName = uploadedFile.value.name.replace(/\.[^/.]+$/, '')
    const fileName = `Filled_${originalName}_${new Date().toISOString().slice(0, 10)}.xlsx`
    downloadedFileName.value = fileName

    const url = window.URL.createObjectURL(blob)
    downloadUrl.value = url

    // Trigger instant browser download
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)

    generationSuccess.value = true
  } catch (err: any) {
    console.error('Error generating filled Excel:', err)
    let errMsg = err.message || 'Server error'
    if (err.response?.data instanceof Blob) {
      try {
        const text = await err.response.data.text()
        const parsed = JSON.parse(text)
        if (parsed.error) errMsg = parsed.error
      } catch (e) {
        // ignore
      }
    } else if (err.response?.data?.error) {
      errMsg = err.response.data.error
    }
    alert("Excel faylni to'ldirishda xatolik yuz berdi: " + errMsg)
  } finally {
    isGenerating.value = false
  }
}

// Reset wizard
const resetWizard = () => {
  currentStep.value = 1
  uploadedFile.value = null
  analysisData.value = null
  analysisError.value = null
  columnMappings.value = []
  selectedStudentIds.value.clear()
  generationSuccess.value = false
  downloadUrl.value = null
}
</script>

<template>
  <div class="h-full flex flex-col bg-zinc-50 dark:bg-[#0c0d0e] overflow-hidden">
    <!-- Top Header Banner -->
    <header class="bg-white dark:bg-[#111315] border-b border-zinc-200 dark:border-zinc-800/80 px-6 py-4 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-600 flex items-center justify-center text-white shadow-md shadow-emerald-500/20">
          <FileSpreadsheet class="w-5 h-5" />
        </div>
        <div>
          <h1 class="text-lg font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            Excel Fill Engine
            <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              AI Powered
            </span>
          </h1>
          <p class="text-xs text-zinc-500 dark:text-zinc-400">
            Universitetlarning murakkab Excel shablonlarini asl formatini buzmasdan avtomatik to'ldirish
          </p>
        </div>
      </div>

      <!-- Step Stepper -->
      <div class="flex items-center gap-2 bg-zinc-100 dark:bg-zinc-800/60 p-1 rounded-xl border border-zinc-200/60 dark:border-zinc-700/60">
        <button
          v-for="s in [
            { num: 1, label: '1. Shablon' },
            { num: 2, label: '2. Ustunlar' },
            { num: 3, label: '3. Talabalar' },
            { num: 4, label: '4. Yuklab olish' }
          ]"
          :key="s.num"
          :disabled="s.num > 1 && !uploadedFile"
          @click="currentStep = s.num as any"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all"
          :class="[
            currentStep === s.num
              ? 'bg-white dark:bg-zinc-700 text-emerald-600 dark:text-emerald-400 shadow-xs font-bold'
              : s.num < currentStep
                ? 'text-zinc-700 dark:text-zinc-300 hover:bg-white/50 dark:hover:bg-zinc-700/50'
                : 'text-zinc-400 dark:text-zinc-500 cursor-not-allowed'
          ]"
        >
          <span
            class="w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold"
            :class="currentStep === s.num ? 'bg-emerald-500 text-white' : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-400'"
          >
            {{ s.num }}
          </span>
          {{ s.label }}
        </button>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="flex-1 overflow-y-auto p-6 scrollbar-thin">
      <div class="max-w-6xl mx-auto">
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- STEP 1: UPLOAD TEMPLATE & INSPECT -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-if="currentStep === 1" class="space-y-6">
          <!-- Upload Area Card -->
          <div
            class="border-2 border-dashed rounded-2xl p-8 text-center transition-all bg-white dark:bg-[#111315]"
            :class="[
              isDragging
                ? 'border-emerald-500 bg-emerald-50/50 dark:bg-emerald-950/20'
                : 'border-zinc-300 dark:border-zinc-800 hover:border-zinc-400 dark:hover:border-zinc-700'
            ]"
            @dragover.prevent="isDragging = true"
            @dragleave.prevent="isDragging = false"
            @drop.prevent="onDropFile"
          >
            <div class="max-w-md mx-auto flex flex-col items-center">
              <div class="w-16 h-16 rounded-2xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800/60 flex items-center justify-center text-emerald-600 dark:text-emerald-400 mb-4 shadow-sm">
                <Upload class="w-8 h-8" />
              </div>
              <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 mb-1">
                Universitetning Excel shablonini yuklang
              </h3>
              <p class="text-xs text-zinc-500 dark:text-zinc-400 mb-5">
                .xlsx yoki .xlsm formatidagi har qanday universitet fayli (Koreyscha, Inglizcha, Ruscha)
              </p>

              <label class="cursor-pointer inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all">
                <FileSpreadsheet class="w-4 h-4" />
                Kompyuterdan tanlash
                <input type="file" class="hidden" accept=".xlsx, .xlsm, .xltx" @change="onFileInputChange" />
              </label>
            </div>
          </div>

          <!-- Loading state -->
          <div v-if="isAnalyzing" class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-8 text-center space-y-3">
            <RefreshCw class="w-8 h-8 text-emerald-500 animate-spin mx-auto" />
            <h4 class="text-sm font-bold text-zinc-800 dark:text-zinc-200">
              Excel shabloni tahlil qilinmoqda...
            </h4>
            <p class="text-xs text-zinc-500 dark:text-zinc-400">
              Sarlavhalar, yashirin ustunlar va CRM maydonlari aniqlanmoqda
            </p>
          </div>

          <!-- Error Alert -->
          <div v-if="analysisError" class="bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-2xl p-4 flex items-center gap-3 text-rose-700 dark:text-rose-300 text-xs">
            <AlertTriangle class="w-5 h-5 shrink-0" />
            <span>{{ analysisError }}</span>
          </div>

          <!-- Inspection Result Card -->
          <div v-if="analysisData && currentSheet && !isAnalyzing" class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 space-y-5">
            <div class="flex items-center justify-between border-b border-zinc-100 dark:border-zinc-800/80 pb-4">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-lg bg-emerald-100 dark:bg-emerald-950/60 flex items-center justify-center text-emerald-600">
                  <CheckCircle2 class="w-5 h-5" />
                </div>
                <div>
                  <h4 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
                    {{ uploadedFile?.name }}
                  </h4>
                  <p class="text-xs text-zinc-500 dark:text-zinc-400">
                    Hajmi: {{ (uploadedFile?.size ? uploadedFile.size / 1024 : 0).toFixed(1) }} KB • Jami varaqlar: {{ analysisData.sheets.length }} ta
                  </p>
                </div>
              </div>

              <!-- Sheet Selector -->
              <div v-if="analysisData.sheets.length > 1" class="flex items-center gap-2">
                <span class="text-xs font-semibold text-zinc-500">Varaq:</span>
                <select
                  v-model="selectedSheetName"
                  class="bg-zinc-100 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-xs font-bold rounded-lg px-3 py-1.5 text-zinc-800 dark:text-zinc-200"
                >
                  <option v-for="sheet in analysisData.sheets" :key="sheet.name" :value="sheet.name">
                    {{ sheet.name }} ({{ sheet.columns.length }} ustun)
                  </option>
                </select>
              </div>
            </div>

            <!-- Sheet Stats Grid -->
            <div class="grid grid-cols-3 gap-4">
              <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-100 dark:border-zinc-800">
                <span class="text-[11px] font-semibold text-zinc-400 block">Sarlavha qatori</span>
                <span class="text-base font-extrabold text-zinc-900 dark:text-zinc-100">{{ currentSheet.detected_header_row }}-qator</span>
              </div>
              <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-100 dark:border-zinc-800">
                <span class="text-[11px] font-semibold text-zinc-400 block">Aniqlangan ustunlar</span>
                <span class="text-base font-extrabold text-emerald-600 dark:text-emerald-400">{{ mappedCount }} ta mos keldi</span>
              </div>
              <div class="p-3.5 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-100 dark:border-zinc-800">
                <span class="text-[11px] font-semibold text-zinc-400 block">Jami ustunlar</span>
                <span class="text-base font-extrabold text-zinc-900 dark:text-zinc-100">{{ currentSheet.columns.length }} ta ustun</span>
              </div>
            </div>

            <!-- Preview Table of Excel Sheet -->
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-zinc-700 dark:text-zinc-300 flex items-center gap-1.5">
                  <Eye class="w-3.5 h-3.5 text-zinc-400" />
                  Excel varag'ining dastlabki ko'rinishi:
                </span>
                <span class="text-[10px] text-zinc-400">
                  (Yashil rangda sarlavha qatori belgilandi)
                </span>
              </div>

              <div class="border border-zinc-200 dark:border-zinc-800 rounded-xl overflow-x-auto max-h-56 scrollbar-thin">
                <table class="w-full text-[11px] border-collapse">
                  <tbody>
                    <tr
                      v-for="row in currentSheet.preview_rows"
                      :key="row.row_idx"
                      class="border-b border-zinc-100 dark:border-zinc-800/60"
                      :class="row.row_idx === currentSheet.detected_header_row ? 'bg-emerald-50/80 dark:bg-emerald-950/40 font-bold text-emerald-900 dark:text-emerald-200' : 'text-zinc-600 dark:text-zinc-400'"
                    >
                      <td class="px-2.5 py-1 bg-zinc-100 dark:bg-zinc-800/80 text-zinc-400 text-center font-mono w-10 text-[10px] select-none border-r border-zinc-200 dark:border-zinc-800">
                        {{ row.row_idx }}
                      </td>
                      <td
                        v-for="(val, idx) in row.values.slice(0, 12)"
                        :key="idx"
                        class="px-3 py-1.5 border-r border-zinc-100 dark:border-zinc-800/60 whitespace-nowrap max-w-[160px] truncate"
                      >
                        {{ val || '-' }}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Proceed to Step 2 Button -->
            <div class="flex justify-end pt-2">
              <button
                @click="currentStep = 2"
                class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all"
              >
                Ustunlarni sozlashga o'tish
                <ArrowRight class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- STEP 2: COLUMN MAPPING & CONFIGURATION -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-if="currentStep === 2" class="space-y-5">
          <!-- Filter & Stats Bar -->
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 flex items-center justify-between">
            <div class="flex items-center gap-4 text-xs">
              <span class="font-bold text-zinc-800 dark:text-zinc-200">
                Ustunlar tahlili:
              </span>
              <span class="px-2.5 py-1 rounded-lg bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 font-bold border border-emerald-200 dark:border-emerald-800">
                {{ mappedCount }} ta to'ldiriladi
              </span>
              <span class="px-2.5 py-1 rounded-lg bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 font-medium">
                {{ skippedCount }} ta o'tkazib yuboriladi
              </span>
            </div>

            <div class="flex items-center gap-3">
              <label class="flex items-center gap-2 text-xs font-semibold text-zinc-600 dark:text-zinc-400 cursor-pointer select-none">
                <input
                  type="checkbox"
                  v-model="onlyMappedFilter"
                  class="rounded text-emerald-600 focus:ring-emerald-500 border-zinc-300 dark:border-zinc-700"
                />
                Faqat to'ldiriladigan ustunlarni ko'rsatish
              </label>
            </div>
          </div>

          <!-- Column Mapping Cards Grid -->
          <div class="space-y-3">
            <div
              v-for="mapping in visibleMappings"
              :key="mapping.col_idx"
              class="bg-white dark:bg-[#111315] border rounded-2xl p-4 transition-all"
              :class="[
                mapping.field !== '_skip'
                  ? 'border-zinc-200 dark:border-zinc-800/90 shadow-xs'
                  : 'border-zinc-200/60 dark:border-zinc-800/40 opacity-60 bg-zinc-50/50 dark:bg-zinc-900/30'
              ]"
            >
              <div class="flex items-start justify-between gap-4">
                <!-- Left: Excel Column Header & Info -->
                <div class="flex items-start gap-3 min-w-[260px] max-w-[340px]">
                  <div
                    class="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-xs shrink-0"
                    :class="mapping.field !== '_skip' ? 'bg-emerald-100 dark:bg-emerald-950/80 text-emerald-700 dark:text-emerald-300' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500'"
                  >
                    {{ mapping.col_letter }}
                  </div>
                  <div>
                    <h5 class="text-xs font-bold text-zinc-900 dark:text-zinc-100 leading-tight">
                      {{ mapping.header_name || '(Bo\'sh sarlavha)' }}
                    </h5>
                    <span class="text-[10px] text-zinc-400 block mt-0.5">
                      Excel ustuni {{ mapping.col_idx }}
                    </span>
                  </div>
                </div>

                <!-- Middle: CRM Field Selector -->
                <div class="flex-1">
                  <select
                    v-model="mapping.field"
                    class="w-full bg-zinc-50 dark:bg-zinc-800/70 border border-zinc-300 dark:border-zinc-700 text-xs font-semibold rounded-xl px-3 py-2 text-zinc-800 dark:text-zinc-200 focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                    :class="mapping.field !== '_skip' ? 'border-emerald-300 dark:border-emerald-700/60' : ''"
                  >
                    <option value="_skip">❌ O'tkazib yuborish (Bo'sh qoldirish)</option>
                    <optgroup v-for="(fields, groupName) in categorizedCrmFields" :key="groupName" :label="groupName">
                      <option v-for="f in fields" :key="f.key" :value="f.key">
                        {{ f.label }}
                      </option>
                    </optgroup>
                  </select>
                </div>

                <!-- Right: Extra Configuration (Static Value, Dates, Gender, Phone) -->
                <div class="min-w-[280px] flex items-center gap-2">
                  <!-- If Static value -->
                  <div v-if="mapping.field === '_static_value'" class="w-full">
                    <input
                      type="text"
                      v-model="mapping.static_value"
                      placeholder="Barchaga yoziladigan matn (masalan Salom CRM)"
                      class="w-full bg-zinc-50 dark:bg-zinc-800 border border-amber-300 dark:border-amber-700/60 text-xs rounded-xl px-3 py-1.5 text-zinc-800 dark:text-zinc-200 placeholder-zinc-400"
                    />
                  </div>

                  <!-- If Date Field -->
                  <div v-else-if="['birthday', 'passport_issue_date', 'passport_expire_date', 'certificate_valid_date'].includes(mapping.field)" class="w-full flex items-center gap-1.5">
                    <select
                      v-model="mapping.format_rules.dateFormat"
                      class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-[11px] font-semibold rounded-lg px-2.5 py-1.5 text-zinc-700 dark:text-zinc-300"
                    >
                      <option value="YYYY-MM-DD">Format: 2004-11-15</option>
                      <option value="YYYY.MM.DD">Format: 2004.11.15</option>
                      <option value="YYYYMMDD">Format: 20041115</option>
                      <option value="DD.MM.YYYY">Format: 15.11.2004</option>
                    </select>
                  </div>

                  <!-- If Gender Field -->
                  <div v-else-if="mapping.field === 'gender'" class="w-full">
                    <select
                      v-model="mapping.format_rules.genderFormat"
                      class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-300 dark:border-zinc-700 text-[11px] font-semibold rounded-lg px-2.5 py-1.5 text-zinc-700 dark:text-zinc-300"
                    >
                      <option value="MALE/FEMALE">MALE / FEMALE</option>
                      <option value="남/여">남 / 여 (Koreyscha)</option>
                      <option value="남성/여성">남성 / 여성 (To'liq)</option>
                      <option value="Male/Female">Male / Female</option>
                      <option value="M/F">M / F</option>
                    </select>
                  </div>

                  <!-- Fallback Placeholder -->
                  <div v-else-if="mapping.field !== '_skip' && mapping.field !== '_sequence_no'" class="w-full">
                    <input
                      type="text"
                      v-model="mapping.fallback"
                      placeholder="Bo'sh bo'lsa: masalan '-' yoki 'X'"
                      class="w-full bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700/60 text-[11px] rounded-lg px-2.5 py-1.5 text-zinc-700 dark:text-zinc-300 placeholder-zinc-400"
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom Step Buttons -->
          <div class="flex items-center justify-between pt-4">
            <button
              @click="currentStep = 1"
              class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all"
            >
              <ArrowLeft class="w-4 h-4" />
              Ortga (Shablon)
            </button>

            <button
              @click="currentStep = 3"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all"
            >
              Talabalarni tanlashga o'tish
              <ArrowRight class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- STEP 3: SELECT STUDENTS & PRE-VALIDATION -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-if="currentStep === 3" class="space-y-5">
          <!-- Selection & Search Toolbar -->
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4 space-y-3">
            <div class="flex items-center justify-between gap-4">
              <!-- Search Input -->
              <div class="relative flex-1">
                <Search class="w-4 h-4 text-zinc-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  v-model="searchQuery"
                  placeholder="Talaba ismi, pasport, ID yoki telefon bo'yicha qidirish..."
                  class="w-full pl-9 pr-4 py-2 bg-zinc-50 dark:bg-zinc-800/70 border border-zinc-200 dark:border-zinc-700/80 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 placeholder-zinc-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <!-- Select All / Count Badge -->
              <div class="flex items-center gap-3">
                <button
                  @click="toggleSelectAllStudents"
                  class="px-3.5 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold text-zinc-700 dark:text-zinc-300 transition-colors"
                >
                  {{ selectedStudentIds.size === filteredStudents.length ? 'Hammasini bekor qilish' : 'Barchasini tanlash' }}
                </button>
                <div class="px-3.5 py-2 rounded-xl bg-emerald-50 dark:bg-emerald-950/60 border border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300 text-xs font-bold">
                  {{ selectedStudentIds.size }} / {{ allStudents.length }} ta tanlandi
                </div>
              </div>
            </div>
          </div>

          <!-- Pre-export Validation Warning Panel (if any missing fields) -->
          <div
            v-if="validationReport.length > 0 && selectedStudentIds.size > 0"
            class="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800/60 rounded-2xl p-4 space-y-2"
          >
            <div class="flex items-center gap-2 text-amber-800 dark:text-amber-200 font-bold text-xs">
              <AlertTriangle class="w-4 h-4 text-amber-600 shrink-0" />
              Eksportdan oldingi ogohlantirish (Kamchiliklar aniqlandi):
            </div>
            <div class="grid grid-cols-2 gap-2 pt-1">
              <div
                v-for="(issue, idx) in validationReport.slice(0, 4)"
                :key="idx"
                class="bg-white/80 dark:bg-zinc-900/80 p-2 rounded-lg border border-amber-200/60 dark:border-amber-800/40 text-[11px] text-zinc-700 dark:text-zinc-300"
              >
                <span class="font-bold text-amber-700 dark:text-amber-400">{{ issue.field }}:</span>
                {{ issue.missingCount }} ta talabada to'ldirilmagan ({{ issue.studentNames.join(', ') }}...)
              </div>
            </div>
            <p class="text-[10px] text-amber-600 dark:text-amber-400 pt-1">
              * Eslatma: Ushbu ma'lumotlar bo'sh bo'lgan talabalar uchun Excel katakchalari shunchaki bo'sh yoki belgilangan belgi bilan qoldiriladi.
            </p>
          </div>

          <!-- Students List Table -->
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden shadow-xs">
            <div class="overflow-x-auto max-h-96 scrollbar-thin">
              <table class="w-full text-xs text-left">
                <thead class="bg-zinc-50 dark:bg-zinc-800/60 text-zinc-500 border-b border-zinc-200 dark:border-zinc-800 sticky top-0 z-10 select-none">
                  <tr>
                    <th class="p-3 w-10 text-center">
                      <input
                        type="checkbox"
                        :checked="selectedStudentIds.size > 0 && selectedStudentIds.size === filteredStudents.length"
                        @change="toggleSelectAllStudents"
                        class="rounded text-emerald-600 focus:ring-emerald-500"
                      />
                    </th>
                    <th class="p-3 font-bold">ID & F.I.SH</th>
                    <th class="p-3 font-bold">Koreyscha ism</th>
                    <th class="p-3 font-bold">Pasport</th>
                    <th class="p-3 font-bold">Tug'ilgan sana</th>
                    <th class="p-3 font-bold">Telefon</th>
                    <th class="p-3 font-bold">Sertifikat</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-zinc-100 dark:divide-zinc-800/60">
                  <tr
                    v-for="student in filteredStudents"
                    :key="student.id"
                    @click="toggleStudentSelection(student.id)"
                    class="cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/40 transition-colors"
                    :class="isStudentSelected(student.id) ? 'bg-emerald-50/50 dark:bg-emerald-950/20' : ''"
                  >
                    <td class="p-3 text-center" @click.stop>
                      <input
                        type="checkbox"
                        :checked="isStudentSelected(student.id)"
                        @change="toggleStudentSelection(student.id)"
                        class="rounded text-emerald-600 focus:ring-emerald-500"
                      />
                    </td>
                    <td class="p-3">
                      <div class="font-bold text-zinc-900 dark:text-zinc-100">{{ student.full_name }}</div>
                      <div class="text-[10px] text-zinc-400 font-mono">{{ student.id }}</div>
                    </td>
                    <td class="p-3 text-zinc-700 dark:text-zinc-300 font-medium">
                      {{ student.korean_name || '-' }}
                    </td>
                    <td class="p-3 font-mono text-zinc-800 dark:text-zinc-200">
                      {{ student.passport || '-' }}
                    </td>
                    <td class="p-3 text-zinc-600 dark:text-zinc-400">
                      {{ student.birthday || '-' }}
                    </td>
                    <td class="p-3 text-zinc-600 dark:text-zinc-400 font-mono">
                      {{ student.phone1 || '-' }}
                    </td>
                    <td class="p-3 text-zinc-600 dark:text-zinc-400">
                      <span v-if="student.language_certificate" class="px-2 py-0.5 rounded bg-blue-50 dark:bg-blue-950/50 text-blue-700 dark:text-blue-300 font-semibold text-[10px]">
                        {{ student.language_certificate }} {{ student.certificate_score }}
                      </span>
                      <span v-else class="text-zinc-400">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Bottom Step Navigation -->
          <div class="flex items-center justify-between pt-4">
            <button
              @click="currentStep = 2"
              class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all"
            >
              <ArrowLeft class="w-4 h-4" />
              Ortga (Ustunlar)
            </button>

            <button
              :disabled="selectedStudentIds.size === 0"
              @click="currentStep = 4"
              class="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Yuklab olish bosqichiga o'tish ({{ selectedStudentIds.size }} ta)
              <ArrowRight class="w-4 h-4" />
            </button>
          </div>
        </div>

        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <!-- STEP 4: GENERATION OPTIONS & DOWNLOAD -->
        <!-- ═════════════════════════════════════════════════════════════════════ -->
        <div v-if="currentStep === 4" class="space-y-6">
          <!-- Summary Box -->
          <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl p-6 space-y-6">
            <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <Settings2 class="w-4 h-4 text-emerald-500" />
              Faylga yozish parametrlari
            </h3>

            <div class="grid grid-cols-2 gap-6">
              <!-- Fill Mode Selection -->
              <div class="space-y-3">
                <label class="text-xs font-bold text-zinc-700 dark:text-zinc-300 block">
                  Yozish rejimi (Fill Mode):
                </label>

                <div class="space-y-2">
                  <label
                    class="flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition-all"
                    :class="fillMode === 'append' ? 'border-emerald-500 bg-emerald-50/40 dark:bg-emerald-950/20' : 'border-zinc-200 dark:border-zinc-800'"
                  >
                    <input type="radio" v-model="fillMode" value="append" class="mt-0.5 text-emerald-600 focus:ring-emerald-500" />
                    <div>
                      <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block">
                        Davomidan qo'shish (Append) — Tavsiya etiladi
                      </span>
                      <span class="text-[11px] text-zinc-500 dark:text-zinc-400">
                        Jadvaldagi mavjud qatorlarga teginmasdan, eng pastki birinchi bo'sh qatordan boshlab yozadi.
                      </span>
                    </div>
                  </label>

                  <label
                    class="flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition-all"
                    :class="fillMode === 'overwrite' ? 'border-amber-500 bg-amber-50/40 dark:bg-amber-950/20' : 'border-zinc-200 dark:border-zinc-800'"
                  >
                    <input type="radio" v-model="fillMode" value="overwrite" class="mt-0.5 text-amber-600 focus:ring-amber-500" />
                    <div>
                      <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block">
                        Namunaviy qatorlarni almashtirish (Overwrite)
                      </span>
                      <span class="text-[11px] text-zinc-500 dark:text-zinc-400">
                        Sarlavhadan keyingi namunaviy talabalar o'rniga yangi tanlangan talabalarni yozadi.
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              <!-- Sequence Number & Summary -->
              <div class="space-y-4">
                <div class="p-4 rounded-xl bg-zinc-50 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 space-y-3">
                  <div class="flex items-center justify-between">
                    <div>
                      <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 block">
                        Tartib raqamini avtomatik davom ettirish
                      </span>
                      <span class="text-[11px] text-zinc-500 dark:text-zinc-400">
                        № ustunini 1, 2, 3... yoki mavjud raqamdan davom ettiradi
                      </span>
                    </div>
                    <input
                      type="checkbox"
                      v-model="autoIncrementSeq"
                      class="rounded text-emerald-600 focus:ring-emerald-500 w-4 h-4"
                    />
                  </div>

                  <hr class="border-zinc-200 dark:border-zinc-800" />

                  <div class="text-xs space-y-1.5 text-zinc-600 dark:text-zinc-400">
                    <div class="flex justify-between">
                      <span>Shablon fayl:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ uploadedFile?.name }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Varaq nomi:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ selectedSheetName }}</span>
                    </div>
                    <div class="flex justify-between">
                      <span>Tanlangan talabalar:</span>
                      <span class="font-bold text-emerald-600 dark:text-emerald-400">{{ selectedStudentIds.size }} nafar</span>
                    </div>
                    <div class="flex justify-between">
                      <span>To'ldiriladigan ustunlar:</span>
                      <span class="font-bold text-zinc-900 dark:text-zinc-100">{{ mappedCount }} ta</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="flex items-center justify-between pt-4 border-t border-zinc-100 dark:border-zinc-800">
              <button
                @click="currentStep = 3"
                class="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-xs font-bold transition-all"
              >
                <ArrowLeft class="w-4 h-4" />
                Ortga (Talabalar)
              </button>

              <button
                :disabled="isGenerating || selectedStudentIds.size === 0"
                @click="handleGenerateExcel"
                class="inline-flex items-center gap-2 px-8 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold shadow-lg shadow-emerald-600/25 transition-all disabled:opacity-50"
              >
                <RefreshCw v-if="isGenerating" class="w-4 h-4 animate-spin" />
                <Download v-else class="w-4 h-4" />
                {{ isGenerating ? "Fayl to'ldirilmoqda..." : "Faylni to'ldirish va yuklab olish (.xlsx)" }}
              </button>
            </div>
          </div>

          <!-- Success Download Card -->
          <div v-if="generationSuccess" class="bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 rounded-2xl p-6 text-center space-y-4">
            <div class="w-12 h-12 rounded-full bg-emerald-500 text-white flex items-center justify-center mx-auto shadow-md shadow-emerald-500/30">
              <Check class="w-6 h-6 stroke-[3]" />
            </div>
            <div>
              <h4 class="text-base font-extrabold text-emerald-900 dark:text-emerald-100">
                Excel fayl muvaffaqiyatli to'ldirildi va yuklab olindi!
              </h4>
              <p class="text-xs text-emerald-700 dark:text-emerald-300 mt-1">
                Fayl nomi: <span class="font-mono font-bold">{{ downloadedFileName }}</span>
              </p>
            </div>

            <div class="flex items-center justify-center gap-4 pt-2">
              <button
                @click="resetWizard"
                class="px-5 py-2.5 rounded-xl bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 text-xs font-bold text-zinc-700 dark:text-zinc-200 hover:bg-zinc-50 dark:hover:bg-zinc-700 transition-colors"
              >
                Yangi fayl to'ldirish
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
