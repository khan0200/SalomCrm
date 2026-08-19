<script setup lang="ts">
import { ref, watch } from 'vue'
import type { Student } from '@/types'
import BaseDrawer from '@/components/common/BaseDrawer.vue'
import { useCurrency } from '@/composables/useCurrency'
import {
  User, BookOpen, GraduationCap, Award, Landmark,
  DollarSign, CheckSquare, FileText, ExternalLink,
  Copy, Check, Plus, Edit3, Save, X
} from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  student: Student | null
  options?: any
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update-student', data: Partial<Student>): void
  (e: 'open-add-payment', studentId: string): void
}>()

const { formatCurrency } = useCurrency()

const isFullscreen = ref(false)
const copiedField = ref<string | null>(null)
const activeTab = ref<'personal' | 'education' | 'universities' | 'financial' | 'documents'>('personal')

// Inline edit state
const isEditing = ref(false)
const editForm = ref<Partial<Student>>({})

watch(() => props.student, (newVal) => {
  if (newVal) {
    editForm.value = JSON.parse(JSON.stringify(newVal))
  }
}, { immediate: true })

const copyText = (field: string, text?: string | null) => {
  if (!text) return
  navigator.clipboard.writeText(text)
  copiedField.value = field
  setTimeout(() => copiedField.value = null, 1500)
}

const handleSave = () => {
  emit('update-student', editForm.value)
  isEditing.value = false
}

const getStatusBadge = (status?: string | null) => {
  switch (status?.toLowerCase()) {
    case 'accepted': return 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
    case 'applying': case 'applied': return 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
    case 'failed': return 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
    default: return 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300'
  }
}
</script>

<template>
  <BaseDrawer
    :is-open="isOpen"
    :title="student?.full_name || 'Student Profile'"
    :subtitle="`ID: ${student?.id || ''} &bull; Tariff: ${student?.tariff || 'No Tariff'}`"
    width="max-w-4xl"
    :allow-fullscreen="true"
    :is-fullscreen="isFullscreen"
    @toggle-fullscreen="isFullscreen = !isFullscreen"
    @close="emit('close')"
  >
    <div v-if="student" class="space-y-6 text-xs select-none">
      <!-- Top Quick Header & Financial Badge Card -->
      <div class="p-4 rounded-2xl bg-zinc-50 dark:bg-zinc-800/50 border border-zinc-200 dark:border-zinc-800 flex flex-wrap items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="w-12 h-12 rounded-xl bg-brand-500 text-white font-mono font-bold flex items-center justify-center text-sm shadow-sm">
            {{ student.id }}
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="text-base font-bold text-zinc-900 dark:text-zinc-100">{{ student.full_name }}</h2>
              <button
                @click="copyText('id', student.id)"
                class="p-1 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 cursor-pointer"
                title="Copy Student ID"
              >
                <Check v-if="copiedField === 'id'" class="w-3.5 h-3.5 text-emerald-500" />
                <Copy v-else class="w-3.5 h-3.5" />
              </button>
            </div>
            <p v-if="student.korean_name" class="text-zinc-500 font-medium mt-0.5">{{ student.korean_name }}</p>
          </div>
        </div>

        <!-- Financial Position Pill -->
        <div class="flex items-center gap-3">
          <div class="flex flex-col items-end">
            <span class="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Balance</span>
            <span
              class="text-sm font-black"
              :class="student.balance < 0 ? 'text-rose-600 dark:text-rose-400' : (student.balance === 0 ? 'text-zinc-800 dark:text-zinc-200' : 'text-emerald-600 dark:text-emerald-400')"
            >
              {{ formatCurrency(student.balance) }}
            </span>
          </div>
          <button
            @click="emit('open-add-payment', student.id)"
            class="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
          >
            <Plus class="w-3.5 h-3.5" />
            <span>Pay</span>
          </button>
          <button
            v-if="!isEditing"
            @click="isEditing = true"
            class="px-3 py-2 rounded-xl bg-zinc-200 dark:bg-zinc-700 hover:bg-zinc-300 dark:hover:bg-zinc-600 text-zinc-800 dark:text-zinc-200 font-bold text-xs flex items-center gap-1.5 transition-colors cursor-pointer"
          >
            <Edit3 class="w-3.5 h-3.5" />
            <span>Edit</span>
          </button>
          <button
            v-else
            @click="handleSave"
            class="px-3 py-2 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-bold text-xs flex items-center gap-1.5 shadow-xs transition-colors cursor-pointer"
          >
            <Save class="w-3.5 h-3.5" />
            <span>Save</span>
          </button>
        </div>
      </div>

      <!-- Navigation Tabs -->
      <div class="flex items-center gap-2 border-b border-zinc-200 dark:border-zinc-800 pb-2 overflow-x-auto">
        <button
          @click="activeTab = 'personal'"
          class="px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5"
          :class="activeTab === 'personal' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-xs' : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'"
        >
          <User class="w-3.5 h-3.5" />
          <span>Personal & Family</span>
        </button>
        <button
          @click="activeTab = 'education'"
          class="px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5"
          :class="activeTab === 'education' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-xs' : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'"
        >
          <GraduationCap class="w-3.5 h-3.5" />
          <span>Education & Certs</span>
        </button>
        <button
          @click="activeTab = 'universities'"
          class="px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5"
          :class="activeTab === 'universities' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-xs' : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'"
        >
          <Landmark class="w-3.5 h-3.5" />
          <span>Universities</span>
        </button>
        <button
          @click="activeTab = 'financial'"
          class="px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5"
          :class="activeTab === 'financial' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-xs' : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'"
        >
          <DollarSign class="w-3.5 h-3.5" />
          <span>Financials</span>
        </button>
        <button
          @click="activeTab = 'documents'"
          class="px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer flex items-center gap-1.5"
          :class="activeTab === 'documents' ? 'bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 shadow-xs' : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'"
        >
          <CheckSquare class="w-3.5 h-3.5" />
          <span>Documents & Hand Counts</span>
        </button>
      </div>

      <!-- TAB 1: Personal & Family Information -->
      <div v-if="activeTab === 'personal'" class="space-y-6">
        <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-4">
          <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <User class="w-4 h-4 text-brand-500" />
            <span>Personal Information</span>
          </h3>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Passport Number</label>
              <input
                v-if="isEditing"
                v-model="editForm.passport"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-mono font-bold uppercase"
              />
              <div v-else class="font-mono font-bold text-zinc-800 dark:text-zinc-200">{{ student.passport || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Passport Issue Date</label>
              <input
                v-if="isEditing"
                v-model="editForm.passport_issue_date"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.passport_issue_date || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Passport Expiry Date</label>
              <input
                v-if="isEditing"
                v-model="editForm.passport_expire_date"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.passport_expire_date || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Gender</label>
              <select
                v-if="isEditing"
                v-model="editForm.gender"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              >
                <option value="">Select...</option>
                <option value="MALE">MALE</option>
                <option value="FEMALE">FEMALE</option>
              </select>
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.gender || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Birthday</label>
              <input
                v-if="isEditing"
                v-model="editForm.birthday"
                type="text"
                placeholder="YYYY-MM-DD"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.birthday || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Email</label>
              <input
                v-if="isEditing"
                v-model="editForm.email"
                type="email"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.email || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Phone 1</label>
              <input
                v-if="isEditing"
                v-model="editForm.phone1"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.phone1 || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Phone 2</label>
              <input
                v-if="isEditing"
                v-model="editForm.phone2"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.phone2 || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Address</label>
              <input
                v-if="isEditing"
                v-model="editForm.address"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium uppercase"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.address || '—' }}</div>
            </div>
          </div>
        </div>

        <!-- Family Information -->
        <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-4">
          <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <User class="w-4 h-4 text-emerald-500" />
            <span>Family & Parents Information</span>
          </h3>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Father's Name</label>
              <input
                v-if="isEditing"
                v-model="editForm.father_name"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.father_name || '—' }}</div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Father's Phone</label>
              <input
                v-if="isEditing"
                v-model="editForm.father_phone"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.father_phone || '—' }}</div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Father's Job / Profession</label>
              <input
                v-if="isEditing"
                v-model="editForm.father_job"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.father_job || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Mother's Name</label>
              <input
                v-if="isEditing"
                v-model="editForm.mother_name"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.mother_name || '—' }}</div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Mother's Phone</label>
              <input
                v-if="isEditing"
                v-model="editForm.mother_phone"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.mother_phone || '—' }}</div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Mother's Job / Profession</label>
              <input
                v-if="isEditing"
                v-model="editForm.mother_job"
                type="text"
                class="w-full px-3 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 font-medium"
              />
              <div v-else class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.mother_job || '—' }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 2: Education & Language Certificates -->
      <div v-if="activeTab === 'education'" class="space-y-6">
        <!-- Education Details -->
        <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-4">
          <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <GraduationCap class="w-4 h-4 text-brand-500" />
            <span>Academic Background</span>
          </h3>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Level</label>
              <div class="font-bold text-zinc-800 dark:text-zinc-200">{{ student.level || '—' }}</div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Secondary Level</label>
              <div class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.level2 || '—' }}</div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Major</label>
              <div class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.major || '—' }}</div>
            </div>

            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Final School Name</label>
              <div class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.final_school_name || '—' }}</div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">GPA / GPA System</label>
              <div class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.gpa || '—' }} ({{ student.gpa_system || '—' }})</div>
            </div>
            <div>
              <label class="block text-[11px] font-bold text-zinc-400 mb-1">Degree / Diploma No</label>
              <div class="font-medium text-zinc-800 dark:text-zinc-200">{{ student.degree_no || '—' }}</div>
            </div>
          </div>
        </div>

        <!-- Language Certificates (Slots 1, 2, 3) -->
        <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-4">
          <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Award class="w-4 h-4 text-amber-500" />
            <span>Language Certificates</span>
          </h3>

          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <!-- Slot 1 -->
            <div class="p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40">
              <div class="text-[10px] font-bold uppercase text-brand-500 mb-1">Certificate #1</div>
              <div class="font-bold text-sm text-zinc-900 dark:text-zinc-100">{{ student.language_certificate || 'NO CERTIFICATE' }}</div>
              <div class="mt-2 text-xs">
                <span class="text-zinc-400">Score:</span> <strong class="text-zinc-800 dark:text-zinc-200">{{ student.certificate_score || '—' }}</strong>
              </div>
            </div>

            <!-- Slot 2 -->
            <div class="p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40">
              <div class="text-[10px] font-bold uppercase text-brand-500 mb-1">Certificate #2</div>
              <div class="font-bold text-sm text-zinc-900 dark:text-zinc-100">{{ student.language_certificate_2 || 'None' }}</div>
              <div class="mt-2 text-xs">
                <span class="text-zinc-400">Score:</span> <strong class="text-zinc-800 dark:text-zinc-200">{{ student.certificate_score_2 || '—' }}</strong>
              </div>
            </div>

            <!-- Slot 3 -->
            <div class="p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40">
              <div class="text-[10px] font-bold uppercase text-brand-500 mb-1">Certificate #3</div>
              <div class="font-bold text-sm text-zinc-900 dark:text-zinc-100">{{ student.language_certificate_3 || 'None' }}</div>
              <div class="mt-2 text-xs">
                <span class="text-zinc-400">Score:</span> <strong class="text-zinc-800 dark:text-zinc-200">{{ student.certificate_score_3 || '—' }}</strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 3: Universities Selection (1 to 5) -->
      <div v-if="activeTab === 'universities'" class="space-y-4">
        <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-3">
          <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Landmark class="w-4 h-4 text-brand-500" />
            <span>Target Universities Choices</span>
          </h3>

          <div class="space-y-2.5">
            <!-- Choice 1 -->
            <div class="p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-700 flex items-center justify-between">
              <div>
                <span class="text-[10px] font-bold text-zinc-400 uppercase">Choice 1</span>
                <h4 class="font-bold text-sm text-zinc-900 dark:text-zinc-100">{{ student.university_1 || 'Not Selected' }}</h4>
                <p v-if="student.university_1_major" class="text-xs text-zinc-500 mt-0.5">Major: {{ student.university_1_major }}</p>
              </div>
              <span class="px-2.5 py-1 rounded-full text-xs font-bold" :class="getStatusBadge(student.university_1_status)">
                {{ student.university_1_status || 'Chosen' }}
              </span>
            </div>

            <!-- Choice 2 -->
            <div class="p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-700 flex items-center justify-between">
              <div>
                <span class="text-[10px] font-bold text-zinc-400 uppercase">Choice 2</span>
                <h4 class="font-bold text-sm text-zinc-900 dark:text-zinc-100">{{ student.university_2 || 'Not Selected' }}</h4>
                <p v-if="student.university_2_major" class="text-xs text-zinc-500 mt-0.5">Major: {{ student.university_2_major }}</p>
              </div>
              <span v-if="student.university_2" class="px-2.5 py-1 rounded-full text-xs font-bold" :class="getStatusBadge(student.university_2_status)">
                {{ student.university_2_status || 'Chosen' }}
              </span>
            </div>

            <!-- Choice 3 -->
            <div class="p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-700 flex items-center justify-between">
              <div>
                <span class="text-[10px] font-bold text-zinc-400 uppercase">Choice 3</span>
                <h4 class="font-bold text-sm text-zinc-900 dark:text-zinc-100">{{ student.university_3 || 'Not Selected' }}</h4>
                <p v-if="student.university_3_major" class="text-xs text-zinc-500 mt-0.5">Major: {{ student.university_3_major }}</p>
              </div>
              <span v-if="student.university_3" class="px-2.5 py-1 rounded-full text-xs font-bold" :class="getStatusBadge(student.university_3_status)">
                {{ student.university_3_status || 'Chosen' }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 4: Financial Summary -->
      <div v-if="activeTab === 'financial'" class="space-y-4">
        <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-4">
          <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <DollarSign class="w-4 h-4 text-emerald-500" />
            <span>Financial Position & Ledger Summary</span>
          </h3>

          <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div class="p-4 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40">
              <span class="text-[10.5px] font-bold text-zinc-400 uppercase">Tariff Package</span>
              <div class="text-base font-black text-zinc-900 dark:text-zinc-100 mt-1">{{ student.tariff || 'No Tariff' }}</div>
            </div>

            <div class="p-4 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40">
              <span class="text-[10.5px] font-bold text-zinc-400 uppercase">Total Discount</span>
              <div class="text-base font-black text-amber-600 dark:text-amber-400 mt-1">{{ formatCurrency(student.discount) }}</div>
            </div>

            <div class="p-4 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40">
              <span class="text-[10.5px] font-bold text-zinc-400 uppercase">Balance (Net Position)</span>
              <div
                class="text-base font-black mt-1"
                :class="student.balance < 0 ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'"
              >
                {{ formatCurrency(student.balance) }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- TAB 5: Documents & Hand Counts -->
      <div v-if="activeTab === 'documents'" class="space-y-4">
        <div class="p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 space-y-4">
          <h3 class="font-bold text-sm text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <CheckSquare class="w-4 h-4 text-brand-500" />
            <span>Missing Documents Required</span>
          </h3>

          <div v-if="student.pick_needed && student.pick_needed.length > 0" class="flex flex-wrap gap-2">
            <span
              v-for="item in student.pick_needed"
              :key="item"
              class="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-rose-50 border border-rose-200 text-rose-700 dark:bg-rose-950/40 dark:border-rose-800 dark:text-rose-300"
            >
              ⚠️ {{ item }}
            </span>
          </div>
          <div v-else class="text-emerald-600 dark:text-emerald-400 font-bold flex items-center gap-1.5">
            <Check class="w-4 h-4" />
            <span>All required documents are complete!</span>
          </div>

          <!-- Hand Counts -->
          <div class="pt-4 border-t border-zinc-100 dark:border-zinc-800 grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="p-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40 text-center">
              <div class="text-[10px] font-bold text-zinc-400 uppercase">Birth Cert (BC)</div>
              <div class="text-base font-bold text-zinc-800 dark:text-zinc-200 mt-0.5">{{ student.bc_hand_count || 0 }}</div>
            </div>
            <div class="p-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40 text-center">
              <div class="text-[10px] font-bold text-zinc-400 uppercase">Marriage Cert (MC)</div>
              <div class="text-base font-bold text-zinc-800 dark:text-zinc-200 mt-0.5">{{ student.mc_hand_count || 0 }}</div>
            </div>
            <div class="p-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40 text-center">
              <div class="text-[10px] font-bold text-zinc-400 uppercase">Apostille (Apos)</div>
              <div class="text-base font-bold text-zinc-800 dark:text-zinc-200 mt-0.5">{{ student.apos_hand_count || 0 }}</div>
            </div>
            <div class="p-3 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/40 text-center">
              <div class="text-[10px] font-bold text-zinc-400 uppercase">3x4 Photos (Pic)</div>
              <div class="text-base font-bold text-zinc-800 dark:text-zinc-200 mt-0.5">{{ student.pic_hand_count || 0 }} / 8</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </BaseDrawer>
</template>
