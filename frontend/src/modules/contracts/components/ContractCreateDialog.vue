<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import {
  FileSignature,
  User,
  Search,
  CheckCircle,
  FileText,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Check,
  Copy,
  Globe
} from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'
import { studentsApi } from '@/api/students'
import { contractsApi, type Contract } from '@/api/contracts'
import { CONTRACT_TEMPLATES, type ContractTemplate } from '../contractTemplates'
import { resolveContractVariables } from '../utils/contractVariables'
import { useAuthStore } from '@/stores/auth'
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

// State
const selectedTemplateKey = ref<string>('STANDART')
const selectedStudentId = ref<string>('')
const studentSearch = ref<string>('')
const customContractNumber = ref<string>('')
const customTitle = ref<string>('')
const isSubmitting = ref<boolean>(false)
const errorMessage = ref<string>('')

const authStore = useAuthStore()
const uiStore = useUiStore()

const tenantSlug = computed(() => {
  return (
    authStore.currentTenant?.slug ||
    (authStore.user?.tenant as any)?.slug ||
    (authStore.user as any)?.tenant_slug ||
    authStore.currentTenant?.name?.toLowerCase().replace(/\s+/g, '') ||
    'unibridge'
  )
})

const onlineContractUrl = computed(() => {
  const origin = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000'
  return `${origin}/contracts/online/${tenantSlug.value}`
})

const isCopiedOnlineLink = ref(false)

async function copyOnlineContractLink() {
  const url = onlineContractUrl.value
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
    isCopiedOnlineLink.value = true
    uiStore.addToast({
      type: 'success',
      title: 'Havola nusxalandi!',
      message: `${url} buferga nusxalandi. Talabaga yuborishingiz mumkin.`,
      duration: 4000
    })
    setTimeout(() => {
      isCopiedOnlineLink.value = false
    }, 2500)
  } catch (err) {
    console.error('Failed to copy online link:', err)
  }
}

// Available Templates List
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

// Selected Template Object
const selectedTemplate = computed(() => {
  return templateList.value.find(t => t.key === selectedTemplateKey.value) || templateList.value[0]
})

// Fetch Students for Dropdown
const { data: studentsData, isLoading: isStudentsLoading } = useQuery({
  queryKey: ['contract-create-students', studentSearch],
  queryFn: () => studentsApi.getStudents({ search: studentSearch.value, page_size: 50 }),
  staleTime: 1000 * 60 * 2,
})

const studentList = computed<Student[]>(() => {
  return (studentsData.value as any)?.results || []
})

const selectedStudent = computed<Student | null>(() => {
  if (!selectedStudentId.value) return null
  return studentList.value.find(s => s.id === selectedStudentId.value) || null
})

// Auto-populate Title & Contract Number when student or template changes
watch(
  [selectedTemplate, selectedStudent],
  ([tpl, st]) => {
    const studentName = st?.full_name ? st.full_name.toUpperCase() : ''
    const tplTitle = tpl ? tpl.title.replace(' SHARTNOMASI', '') : 'SHARTNOMA'

    if (studentName) {
      customTitle.value = `${tplTitle} - ${studentName}`
    } else {
      customTitle.value = `${tplTitle} SHARTNOMASI`
    }

    if (!customContractNumber.value) {
      const year = new Date().getFullYear()
      const randSeq = Math.floor(1000 + Math.random() * 9000)
      customContractNumber.value = `SH-${year}-${randSeq}`
    }
  },
  { immediate: true }
)

// Reset state when modal opens
watch(
  () => props.isOpen,
  (val) => {
    if (val) {
      errorMessage.value = ''
      selectedStudentId.value = ''
      studentSearch.value = ''
      selectedTemplateKey.value = props.initialTemplateKey || 'STANDART'
      const year = new Date().getFullYear()
      const randSeq = Math.floor(1000 + Math.random() * 9000)
      customContractNumber.value = `SH-${year}-${randSeq}`
    }
  }
)

async function handleCreate() {
  if (!customTitle.value.trim()) {
    errorMessage.value = "Iltimos, shartnoma nomini kiriting"
    return
  }

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    let templateContent = selectedTemplate.value.fullText || '<p></p>'
    if (props.initialContent && selectedTemplate.value.key === props.initialTemplateKey) {
      templateContent = props.initialContent
    }
    
    // Resolve dynamic variables into template content
    const resolvedContent = resolveContractVariables(
      templateContent,
      selectedStudent.value,
      {
        contractNumber: customContractNumber.value,
        templateName: selectedTemplate.value.key,
        price: selectedTemplate.value.priceDisplay,
      }
    )

    const payload = {
      student: selectedStudent.value?.id || null,
      contract_number: customContractNumber.value,
      title: customTitle.value,
      template_name: selectedTemplate.value.key,
      content: resolvedContent,
      status: 'draft'
    }

    const created = await contractsApi.createContract(payload)
    emit('created', created)
    emit('close')
  } catch (err: any) {
    console.error('Failed to create contract:', err)
    errorMessage.value = err.response?.data?.detail || "Shartnomani saqlashda xatolik yuz berdi"
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <BaseModal
    :is-open="isOpen"
    title="New Contract"
    subtitle="Select template and student to create contract"
    max-width="max-w-3xl"
    @close="emit('close')"
  >
    <div class="p-6 space-y-6">
      <!-- Online Contract Quick Copy Banner -->
      <div class="p-3.5 rounded-2xl bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950/40 dark:to-indigo-950/30 border border-blue-200/80 dark:border-blue-900/50 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs shadow-2xs">
        <div class="flex items-center gap-2.5 min-w-0">
          <div class="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-xs">
            <Globe class="w-3.5 h-3.5" />
          </div>
          <div class="min-w-0">
            <div class="font-bold text-blue-900 dark:text-blue-200 text-[11px] uppercase tracking-wider flex items-center gap-1.5">
              <span>Talabalar uchun onlayn portal havolasi</span>
              <span class="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            </div>
            <div class="font-mono text-xs font-semibold text-blue-700 dark:text-blue-300 truncate" :title="onlineContractUrl">
              {{ onlineContractUrl }}
            </div>
          </div>
        </div>
        <button
          type="button"
          @click="copyOnlineContractLink"
          class="shrink-0 inline-flex items-center justify-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs shadow-xs transition-all cursor-pointer select-none"
          :class="{ '!bg-emerald-600 hover:!bg-emerald-700': isCopiedOnlineLink }"
        >
          <Check v-if="isCopiedOnlineLink" class="w-3.5 h-3.5 text-emerald-100" />
          <Copy v-else class="w-3.5 h-3.5" />
          <span>{{ isCopiedOnlineLink ? 'Nusxalandi!' : 'Havolani nusxalash' }}</span>
        </button>
      </div>

      <!-- Error Alert -->
      <div v-if="errorMessage" class="p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-xl text-xs text-rose-600 dark:text-rose-300 flex items-center gap-2">
        <span class="font-bold">Error:</span> {{ errorMessage }}
      </div>

      <!-- Step 1: Select Template -->
      <div class="space-y-3">
        <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">
          1. Select Template
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
                <span class="font-extrabold text-xs tracking-tight truncate">
                  {{ tpl.key }}
                </span>
                <span v-if="selectedTemplateKey === tpl.key" class="w-4 h-4 rounded-full bg-blue-500 text-white flex items-center justify-center shrink-0">
                  <Check class="w-2.5 h-2.5" />
                </span>
              </div>
              <p class="text-[10px] text-zinc-400 line-clamp-2 leading-tight">
                {{ tpl.subtitle }}
              </p>
            </div>

            <div class="mt-2.5 pt-2 border-t border-zinc-200/60 dark:border-zinc-700/60 flex items-center justify-between text-[10.5px]">
              <span class="font-bold text-zinc-900 dark:text-zinc-100 font-mono">
                {{ tpl.priceDisplay }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Step 2: Select Student -->
      <div class="space-y-3">
        <label class="block text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">
          2. Select Student (Optional, for auto-fill)
        </label>

        <!-- Search Bar -->
        <div class="relative">
          <Search class="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            v-model="studentSearch"
            type="text"
            placeholder="Search student by name, passport or ID..."
            class="w-full pl-9 pr-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        <!-- Student Dropdown / Scroll list -->
        <div class="max-h-40 overflow-y-auto rounded-xl border border-zinc-200 dark:border-zinc-800 divide-y divide-zinc-100 dark:divide-zinc-800">
          <div
            v-if="studentList.length === 0"
            class="p-4 text-center text-xs text-zinc-400"
          >
            {{ isStudentsLoading ? "Loading students..." : "No students found" }}
          </div>

          <button
            v-for="st in studentList"
            :key="st.id"
            type="button"
            @click="selectedStudentId = (selectedStudentId === st.id ? '' : st.id)"
            class="w-full px-3 py-2 text-left text-xs transition-colors flex items-center justify-between hover:bg-zinc-50 dark:hover:bg-zinc-800 cursor-pointer"
            :class="selectedStudentId === st.id ? 'bg-blue-50/70 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 font-semibold' : 'text-zinc-700 dark:text-zinc-300'"
          >
            <div class="flex items-center gap-2 min-w-0">
              <div class="w-6 h-6 rounded-full bg-zinc-200 dark:bg-zinc-700 text-zinc-600 dark:text-zinc-300 flex items-center justify-center shrink-0 text-[10px] font-bold">
                {{ st.full_name?.charAt(0) || 'T' }}
              </div>
              <div class="truncate">
                <span class="font-bold">{{ st.full_name }}</span>
                <span class="text-[11px] text-zinc-400 ml-2 font-mono">{{ st.passport || st.id }}</span>
              </div>
            </div>

            <div class="flex items-center gap-2 text-[11px] shrink-0 text-zinc-400">
              <span v-if="st.tariff" class="px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-800 text-[10px]">
                {{ st.tariff }}
              </span>
              <span v-if="selectedStudentId === st.id" class="text-blue-600 dark:text-blue-400 font-bold">
                Selected ✓
              </span>
            </div>
          </button>
        </div>
      </div>

      <!-- Step 3: Contract Metadata (Title & Number) -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
            Contract Number
          </label>
          <input
            v-model="customContractNumber"
            type="text"
            placeholder="SH-2026-0001"
            class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-mono font-bold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div>
          <label class="block text-xs font-semibold text-zinc-600 dark:text-zinc-400 mb-1">
            Contract Title
          </label>
          <input
            v-model="customTitle"
            type="text"
            placeholder="STANDART - Student Name"
            class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs font-bold text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      <!-- Preview Tip Badge -->
      <div class="p-3 bg-blue-50/60 dark:bg-blue-950/30 rounded-xl border border-blue-100 dark:border-blue-900/50 flex items-center gap-2.5 text-xs text-blue-700 dark:text-blue-300">
        <Sparkles class="w-4 h-4 text-blue-500 shrink-0" />
        <span>
          The contract will be auto-filled with the selected student's details and opened in the document editor.
        </span>
      </div>

      <!-- Footer Buttons -->
      <div class="flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 text-xs font-semibold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          Cancel
        </button>

        <button
          type="button"
          @click="handleCreate"
          :disabled="isSubmitting"
          class="inline-flex items-center gap-2 px-5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-bold transition-all shadow-xs cursor-pointer"
        >
          <span v-if="isSubmitting">Creating...</span>
          <span v-else class="flex items-center gap-1.5">
            <span>Create & Edit</span>
            <ArrowRight class="w-3.5 h-3.5" />
          </span>
        </button>
      </div>
    </div>
  </BaseModal>
</template>
