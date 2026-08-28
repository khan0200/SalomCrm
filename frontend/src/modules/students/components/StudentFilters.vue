<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import {
  X, Check, Tag, Layers, Users, Award, Bookmark, UserCheck, Hash, FileText
} from 'lucide-vue-next'
import type { Student } from '@/types'
import { useCustomTags } from '@/composables/useCustomTags'
import { PICK_NEEDED_LIST, useDocumentHelpers } from '@/composables/useDocumentHelpers'
import { normalizeCertificateScore } from '@/utils/certificateScore'
import { getTariffPrice } from '@/utils/tariff'
import { useCurrency } from '@/composables/useCurrency'

const { formatCurrency } = useCurrency()

const props = withDefaults(defineProps<{
  isOpen: boolean
  options: {
    tariffs: { name: string; price: number }[]
    levels: string[]
    groups: string[]
    leads: string[]
    folders?: { id: string; name: string }[]
  }
  students?: Student[]
  selectedTariffs: string[]
  selectedLevels: string[]
  selectedGroups: string[]
  selectedCerts: string[]
  selectedScores: string[]
  selectedTags: string[]
  selectedLeads: string[]
  selectedMissingDocs?: string[]
  matchingCount?: number
}>(), {
  students: () => [],
  selectedMissingDocs: () => []
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'apply', filters: {
    tariffs: string[]
    levels: string[]
    groups: string[]
    certs: string[]
    scores: string[]
    tags: string[]
    leads: string[]
    missingDocs: string[]
  }): void
}>()

const { getEffectiveMissingDocs } = useDocumentHelpers()
const { tagsRegistry, getTagIcon, fetchTags } = useCustomTags()

// Draft local states
const draftTariffs = ref<string[]>([])
const draftLevels = ref<string[]>([])
const draftGroups = ref<string[]>([])
const draftCerts = ref<string[]>([])
const draftScores = ref<string[]>([])
const draftTags = ref<string[]>([])
const draftLeads = ref<string[]>([])
const draftMissingDocs = ref<string[]>([])

// Active category
const activeCategory = ref<string>('tariff')

// Sync drafts with applied props when opened
watch(() => props.isOpen, (newVal) => {
  if (newVal) {
    fetchTags()
    draftTariffs.value = [...props.selectedTariffs]
    draftLevels.value = [...props.selectedLevels]
    draftGroups.value = [...props.selectedGroups]
    draftCerts.value = [...props.selectedCerts]
    draftScores.value = [...props.selectedScores]
    draftTags.value = [...props.selectedTags]
    draftLeads.value = [...props.selectedLeads]
    draftMissingDocs.value = [...(props.selectedMissingDocs || [])]
    activeCategory.value = 'tariff'
  }
}, { immediate: true })

// Score options condition
const showScoreFilter = computed(() => {
  return draftCerts.value.length === 1 && (draftCerts.value[0] === 'TOPIK' || draftCerts.value[0] === 'IELTS')
})

const activeCertForScore = computed(() => showScoreFilter.value ? draftCerts.value[0] : null)

const scoreOptions = computed(() => {
  if (activeCertForScore.value === 'TOPIK') {
    return ['EXPECTED', '1', '2', '3', '4', '5', '6']
  }
  if (activeCertForScore.value === 'IELTS') {
    return ['EXPECTED', '5.0', '5.5', '6.0', '6.5', '7.0', '7.5', '8.0', '8.5', '9.0']
  }
  return []
})

// Clear score drafts if cert switched
watch(showScoreFilter, (hasScore) => {
  if (!hasScore) {
    draftScores.value = []
    if (activeCategory.value === 'score') {
      activeCategory.value = 'cert'
    }
  }
})

const certOptions = ['NO CERTIFICATE', 'EXPECTED', 'TOPIK', 'SKA', 'IELTS', 'TOEFL', 'SAT', 'CEFR']

// Category Definitions
interface CategoryItem {
  id: string
  label: string
  icon: any
  drafts: string[]
  fullOpts: string[]
  labelMapping: (opt: string) => string
}

const categories = computed<CategoryItem[]>(() => {
  const tariffOpts = ['NO_TARIFF', ...(props.options.tariffs?.map(t => t.name) || [])]
  const levelOpts = ['NO_LEVEL', ...(props.options.levels || [])]
  const groupOpts = ['NO_GROUP', ...(props.options.groups || [])]
  const leadOpts = ['NO_LEADBY', ...(props.options.leads || [])]
  const dynamicTagOpts = Array.from(new Set([
    'Call', 'Apply', 'Documents', 'Payment',
    ...tagsRegistry.value.map(t => t.name)
  ]))

  const list: CategoryItem[] = [
    {
      id: 'tariff',
      label: 'Tariff',
      icon: Tag,
      drafts: draftTariffs.value,
      fullOpts: tariffOpts,
      labelMapping: (opt) => {
        if (opt === 'NO_TARIFF') return 'No Tariff'
        const price = getTariffPrice(opt, null, props.options.tariffs || [])
        return price > 0 ? `${opt} — ${formatCurrency(price)}` : opt
      }
    },
    {
      id: 'level',
      label: 'Level',
      icon: Layers,
      drafts: draftLevels.value,
      fullOpts: levelOpts,
      labelMapping: (opt) => opt === 'NO_LEVEL' ? 'No Level' : opt
    },
    {
      id: 'group',
      label: 'Group',
      icon: Users,
      drafts: draftGroups.value,
      fullOpts: groupOpts,
      labelMapping: (opt) => opt === 'NO_GROUP' ? 'No Group' : opt
    },
    {
      id: 'cert',
      label: 'Certificate',
      icon: Award,
      drafts: draftCerts.value,
      fullOpts: certOptions,
      labelMapping: (opt) => opt
    }
  ]

  if (showScoreFilter.value) {
    list.push({
      id: 'score',
      label: `${activeCertForScore.value} Score`,
      icon: Hash,
      drafts: draftScores.value,
      fullOpts: scoreOptions.value,
      labelMapping: (opt) => opt === 'EXPECTED' ? 'Expected' : `${activeCertForScore.value} ${opt}`
    })
  }

  list.push(
    {
      id: 'missing',
      label: 'Missing Docs',
      icon: FileText,
      drafts: draftMissingDocs.value,
      fullOpts: PICK_NEEDED_LIST,
      labelMapping: (opt) => opt
    },
    {
      id: 'tag',
      label: 'Tasks / Tags',
      icon: Bookmark,
      drafts: draftTags.value,
      fullOpts: dynamicTagOpts,
      labelMapping: (opt) => `${getTagIcon(opt)} ${opt}`
    },
    {
      id: 'lead',
      label: 'Lead By',
      icon: UserCheck,
      drafts: draftLeads.value,
      fullOpts: leadOpts,
      labelMapping: (opt) => opt === 'NO_LEADBY' ? 'No Lead by' : opt
    }
  )

  return list
})

const currentCategory = computed(() => {
  return categories.value.find(c => c.id === activeCategory.value) || categories.value[0]
})

const toggleDraftOption = (catId: string, val: string) => {
  if (catId === 'tariff') {
    draftTariffs.value = draftTariffs.value.includes(val)
      ? draftTariffs.value.filter(x => x !== val)
      : [...draftTariffs.value, val]
  } else if (catId === 'level') {
    draftLevels.value = draftLevels.value.includes(val)
      ? draftLevels.value.filter(x => x !== val)
      : [...draftLevels.value, val]
  } else if (catId === 'group') {
    draftGroups.value = draftGroups.value.includes(val)
      ? draftGroups.value.filter(x => x !== val)
      : [...draftGroups.value, val]
  } else if (catId === 'cert') {
    draftCerts.value = draftCerts.value.includes(val)
      ? draftCerts.value.filter(x => x !== val)
      : [...draftCerts.value, val]
  } else if (catId === 'score') {
    draftScores.value = draftScores.value.includes(val)
      ? draftScores.value.filter(x => x !== val)
      : [...draftScores.value, val]
  } else if (catId === 'missing') {
    draftMissingDocs.value = draftMissingDocs.value.includes(val)
      ? draftMissingDocs.value.filter(x => x !== val)
      : [...draftMissingDocs.value, val]
  } else if (catId === 'tag') {
    draftTags.value = draftTags.value.includes(val)
      ? draftTags.value.filter(x => x !== val)
      : [...draftTags.value, val]
  } else if (catId === 'lead') {
    draftLeads.value = draftLeads.value.includes(val)
      ? draftLeads.value.filter(x => x !== val)
      : [...draftLeads.value, val]
  }
}

const clearAll = () => {
  draftTariffs.value = []
  draftLevels.value = []
  draftGroups.value = []
  draftCerts.value = []
  draftScores.value = []
  draftTags.value = []
  draftLeads.value = []
  draftMissingDocs.value = []
}

const handleApply = () => {
  emit('apply', {
    tariffs: draftTariffs.value,
    levels: draftLevels.value,
    groups: draftGroups.value,
    certs: draftCerts.value,
    scores: draftScores.value,
    tags: draftTags.value,
    leads: draftLeads.value,
    missingDocs: draftMissingDocs.value
  })
}

const hasDrafts = computed(() => {
  return draftTariffs.value.length > 0 ||
    draftLevels.value.length > 0 ||
    draftGroups.value.length > 0 ||
    draftCerts.value.length > 0 ||
    draftScores.value.length > 0 ||
    draftTags.value.length > 0 ||
    draftLeads.value.length > 0 ||
    draftMissingDocs.value.length > 0
})

// Dynamic Matching Students Count calculation based on unapplied draft filters
const matchingStudentsCount = computed(() => {
  if (!props.students || props.students.length === 0) {
    return props.matchingCount || 0
  }

  return props.students.filter(student => {
    // 1. Tariff filter
    if (draftTariffs.value.length > 0) {
      const matchNoTariff = draftTariffs.value.includes('NO_TARIFF') && !student.tariff
      const matchTariff = student.tariff && draftTariffs.value.includes(student.tariff)
      if (!matchNoTariff && !matchTariff) return false
    }

    // 2. Level filter
    if (draftLevels.value.length > 0) {
      const matchNoLevel = draftLevels.value.includes('NO_LEVEL') && !student.level && !student.level2
      const matchLevel1 = student.level && draftLevels.value.includes(student.level)
      const matchLevel2 = student.level2 && draftLevels.value.includes(student.level2)
      if (!matchNoLevel && !matchLevel1 && !matchLevel2) return false
    }

    // 3. Group filter
    if (draftGroups.value.length > 0) {
      const matchNoGroup = draftGroups.value.includes('NO_GROUP') && !student.student_group
      const matchGroup = student.student_group && draftGroups.value.includes(student.student_group)
      if (!matchNoGroup && !matchGroup) return false
    }

    // 4. Certificate filter
    if (draftCerts.value.length > 0) {
      let matchesCert = false
      if (draftCerts.value.includes('NO CERTIFICATE')) {
        if (!student.language_certificate || student.language_certificate === 'NO CERTIFICATE') {
          matchesCert = true
        }
      }
      if (draftCerts.value.includes('EXPECTED')) {
        const hasExp = (student.certificate_score?.toUpperCase() === 'EXPECTED') ||
          (student.certificate_score_2?.toUpperCase() === 'EXPECTED') ||
          (student.certificate_score_3?.toUpperCase() === 'EXPECTED')
        if (hasExp) matchesCert = true
      }
      const hasAnySelected = [student.language_certificate, student.language_certificate_2, student.language_certificate_3]
        .some(cert => cert && cert !== 'NO CERTIFICATE' && draftCerts.value.includes(cert))
      if (hasAnySelected) matchesCert = true

      if (!matchesCert) return false
    }

    // 5. Score sub-filter
    if (draftScores.value.length > 0 && draftCerts.value.length === 1) {
      const cert = draftCerts.value[0] || ''
      const scores = [student.certificate_score, student.certificate_score_2, student.certificate_score_3]
      const certs = [student.language_certificate, student.language_certificate_2, student.language_certificate_3]
      const normalizedDraftScores = draftScores.value.map(normalizeCertificateScore)
      const matchesScore = certs.some((c, i) => {
        if (!c || c === 'NO CERTIFICATE') return false
        if (c.toUpperCase() !== cert.toUpperCase()) return false
        const score = normalizeCertificateScore(scores[i])
        return normalizedDraftScores.includes(score)
      })
      if (!matchesScore) return false
    }

    // 6. Tags filter
    if (draftTags.value.length > 0) {
      const matchesTag = draftTags.value.some(tag => {
        if (tag === 'Custom') {
          const predefined = ['Call', 'Apply', 'Documents', 'Payment']
          return student.task_tags && student.task_tags.some(t => !predefined.includes(t))
        }
        return student.task_tags && student.task_tags.includes(tag)
      })
      if (!matchesTag) return false
    }

    // 7. Lead By filter (case-insensitive -- lead_by is free-text and the
    // same source can be saved with different casing, e.g. "Ali Uncle" vs
    // "ALI UNCLE")
    if (draftLeads.value.length > 0) {
      const draftLeadsLower = draftLeads.value.map(l => l.toLowerCase())
      const matchNoLead = draftLeadsLower.includes('no_leadby') && !student.lead_by
      const matchLead = !!student.lead_by && draftLeadsLower.includes(student.lead_by.toLowerCase())
      if (!matchNoLead && !matchLead) return false
    }

    // 8. Missing Docs filter
    if (draftMissingDocs.value.length > 0) {
      const missingList = getEffectiveMissingDocs(student)
      const matchesMissing = draftMissingDocs.value.some(d => missingList.includes(d))
      if (!matchesMissing) return false
    }

    return true
  }).length
})

// Option individual counter
const getOptionCount = (catId: string, opt: string): number => {
  if (!props.students || props.students.length === 0) return 0
  return props.students.filter(s => {
    if (catId === 'tariff') {
      if (opt === 'NO_TARIFF') return !s.tariff
      return s.tariff === opt
    }
    if (catId === 'level') {
      if (opt === 'NO_LEVEL') return !s.level && !s.level2
      return s.level === opt || s.level2 === opt
    }
    if (catId === 'group') {
      if (opt === 'NO_GROUP') return !s.student_group
      return s.student_group === opt
    }
    if (catId === 'cert') {
      if (opt === 'NO CERTIFICATE') return !s.language_certificate || s.language_certificate === 'NO CERTIFICATE'
      if (opt === 'EXPECTED') return (s.certificate_score?.toUpperCase() === 'EXPECTED') || (s.certificate_score_2?.toUpperCase() === 'EXPECTED') || (s.certificate_score_3?.toUpperCase() === 'EXPECTED')
      return s.language_certificate === opt || s.language_certificate_2 === opt || s.language_certificate_3 === opt
    }
    if (catId === 'score') {
      const cert = activeCertForScore.value || ''
      const scores = [s.certificate_score, s.certificate_score_2, s.certificate_score_3]
      const certs = [s.language_certificate, s.language_certificate_2, s.language_certificate_3]
      const normalizedOpt = normalizeCertificateScore(opt)
      return certs.some((c, i) => {
        if (!c || c === 'NO CERTIFICATE') return false
        if (c.toUpperCase() !== cert.toUpperCase()) return false
        return normalizeCertificateScore(scores[i]) === normalizedOpt
      })
    }
    if (catId === 'missing') {
      const missingList = getEffectiveMissingDocs(s)
      return missingList.includes(opt)
    }
    if (catId === 'tag') {
      if (opt === 'Custom') {
        const predefined = ['Call', 'Apply', 'Documents', 'Payment']
        return s.task_tags && s.task_tags.some(t => !predefined.includes(t))
      }
      return s.task_tags && s.task_tags.includes(opt)
    }
    if (catId === 'lead') {
      if (opt === 'NO_LEADBY') return !s.lead_by
      return !!s.lead_by && s.lead_by.toLowerCase() === opt.toLowerCase()
    }
    return true
  }).length
}

// Close on Escape
const onKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen) {
    emit('close')
  }
}

onMounted(() => window.addEventListener('keydown', onKeyDown))
onUnmounted(() => window.removeEventListener('keydown', onKeyDown))
</script>

<template>
  <div v-if="isOpen" class="relative">
    <!-- Click Outside Overlay Backdrop for Desktop -->
    <div
      class="fixed inset-0 z-40 bg-transparent hidden md:block cursor-default"
      @click="emit('close')"
    />

    <!-- Mobile Backdrop -->
    <div
      class="fixed inset-0 z-50 bg-black/40 backdrop-blur-xs md:hidden cursor-default"
      @click="emit('close')"
    />

    <!-- Filter Panel Container (Desktop Popover & Mobile Bottom Sheet) -->
    <div
      class="fixed z-50 rounded-t-[20px] bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 shadow-2xl bottom-0 inset-x-0 max-h-[85vh] flex flex-col md:absolute md:top-2 md:bottom-auto md:left-0 md:right-auto md:w-[680px] md:h-[480px] md:rounded-2xl overflow-hidden select-none"
    >
      <!-- Mobile Drag Handle -->
      <div class="h-5 flex items-center justify-center shrink-0 md:hidden cursor-pointer" @click="emit('close')">
        <div class="w-10 h-1 bg-zinc-300 dark:bg-zinc-700 rounded-full" />
      </div>

      <!-- Panel Header -->
      <div class="px-5 py-3.5 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between shrink-0">
        <div>
          <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">Filter Students</h3>
          <p class="text-[11px] text-zinc-500 font-medium">Refine your active student registry list</p>
        </div>

        <div class="flex items-center gap-3">
          <button
            v-if="hasDrafts"
            type="button"
            @click="clearAll"
            class="text-xs font-bold text-rose-600 hover:text-rose-700 transition-colors cursor-pointer"
          >
            Clear All
          </button>

          <button
            type="button"
            @click="emit('close')"
            class="p-1 rounded-lg border border-zinc-200 dark:border-zinc-700 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-all cursor-pointer h-7 w-7 flex items-center justify-center"
          >
            <X class="h-4 w-4" />
          </button>
        </div>
      </div>

      <!-- Master-Detail Body -->
      <div class="flex-1 flex flex-col md:flex-row overflow-hidden min-h-0">
        <!-- Desktop Left Category Navigation -->
        <div class="hidden md:flex flex-col w-[210px] border-r border-zinc-100 dark:border-zinc-800 overflow-y-auto bg-zinc-50/50 dark:bg-zinc-900/30 py-2">
          <button
            v-for="cat in categories"
            :key="cat.id"
            type="button"
            @click="activeCategory = cat.id"
            class="flex items-center justify-between px-4 py-3 text-xs font-semibold select-none text-left cursor-pointer transition-all border-l-3"
            :class="[
              activeCategory === cat.id
                ? 'bg-blue-50/70 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 border-blue-600 dark:border-blue-500 font-bold'
                : 'text-zinc-600 dark:text-zinc-400 border-transparent hover:bg-zinc-100/50 dark:hover:bg-zinc-800/40 hover:text-zinc-900 dark:hover:text-zinc-200'
            ]"
          >
            <div class="flex items-center gap-2.5">
              <component
                :is="cat.icon"
                class="w-4 h-4 shrink-0"
                :class="activeCategory === cat.id ? 'text-blue-600 dark:text-blue-400' : 'text-zinc-400'"
              />
              <span>{{ cat.label }}</span>
            </div>

            <span
              v-if="cat.drafts.length > 0"
              class="px-1.5 py-0.5 text-[9px] font-extrabold bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400 rounded-full leading-none"
            >
              {{ cat.drafts.length }}
            </span>
          </button>
        </div>

        <!-- Mobile Horizontal Category Nav -->
        <div class="flex md:hidden overflow-x-auto border-b border-zinc-100 dark:border-zinc-800 scrollbar-none px-3 py-2 gap-2 shrink-0 bg-zinc-50 dark:bg-zinc-900">
          <button
            v-for="cat in categories"
            :key="cat.id"
            type="button"
            @click="activeCategory = cat.id"
            class="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold select-none cursor-pointer whitespace-nowrap transition-all border"
            :class="[
              activeCategory === cat.id
                ? 'bg-blue-50 border-blue-300 text-blue-700 dark:bg-blue-950/40 dark:border-blue-800 dark:text-blue-400'
                : 'bg-white dark:bg-zinc-800 border-zinc-200 dark:border-zinc-700 text-zinc-600 dark:text-zinc-300'
            ]"
          >
            <span>{{ cat.label }}</span>
            <span
              v-if="cat.drafts.length > 0"
              class="px-1.5 py-0.5 text-[9px] font-bold bg-blue-600 text-white rounded-full leading-none"
            >
              {{ cat.drafts.length }}
            </span>
          </button>
        </div>

        <!-- Right Options List Pane -->
        <div class="flex-1 flex flex-col min-h-0 bg-white dark:bg-[#111315]">
          <div class="flex-1 flex flex-col min-h-0 p-4 sm:p-5 space-y-3">
            <h4 class="text-[10px] font-bold uppercase tracking-wider text-zinc-400 select-none">
              {{ currentCategory.label }} Options
            </h4>

            <!-- Selected Chips -->
            <div v-if="currentCategory.drafts.length > 0" class="flex flex-wrap gap-1.5 max-h-20 overflow-y-auto pb-2 border-b border-zinc-100 dark:border-zinc-800">
              <div
                v-for="val in currentCategory.drafts"
                :key="val"
                class="inline-flex items-center gap-1 px-2.5 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-[10px] font-semibold text-zinc-800 dark:text-zinc-200 rounded-full border border-zinc-200 dark:border-zinc-700 shadow-2xs"
              >
                <span class="truncate max-w-[140px]">{{ currentCategory.labelMapping(val) }}</span>
                <button
                  type="button"
                  @click="toggleDraftOption(currentCategory.id, val)"
                  class="hover:bg-red-500/10 text-zinc-400 hover:text-red-500 rounded-full h-3.5 w-3.5 flex items-center justify-center transition-colors cursor-pointer"
                >
                  <X class="h-2.5 w-2.5" />
                </button>
              </div>
            </div>

            <!-- Options Checkbox List -->
            <div class="flex-1 overflow-y-auto space-y-1 pr-1 min-h-0 scrollbar-thin">
              <div v-if="currentCategory.fullOpts.length === 0" class="text-xs text-zinc-400 italic text-center py-8">
                No options available
              </div>

              <label
                v-else
                v-for="opt in currentCategory.fullOpts"
                :key="opt"
                class="flex items-center gap-2.5 px-3 py-2 rounded-xl hover:bg-zinc-50 dark:hover:bg-zinc-850 transition-colors select-none text-xs text-zinc-800 dark:text-zinc-200 cursor-pointer"
              >
                <input
                  type="checkbox"
                  :checked="currentCategory.drafts.includes(opt)"
                  @change="toggleDraftOption(currentCategory.id, opt)"
                  class="h-4 w-4 rounded border-zinc-300 dark:border-zinc-600 text-blue-600 focus:ring-blue-500 cursor-pointer"
                />
                <span class="font-semibold">{{ currentCategory.labelMapping(opt) }}</span>
                <span class="text-[11px] text-zinc-400 font-mono ml-auto mr-1">({{ getOptionCount(currentCategory.id, opt) }})</span>
                <Check
                  v-if="currentCategory.drafts.includes(opt)"
                  class="h-4 w-4 text-blue-600 dark:text-blue-400 shrink-0"
                />
              </label>
            </div>
          </div>
        </div>
      </div>

      <!-- Panel Footer -->
      <div class="px-5 py-3.5 border-t border-zinc-100 dark:border-zinc-800 bg-zinc-50/70 dark:bg-zinc-900/50 flex items-center gap-3 shrink-0">
        <button
          type="button"
          @click="emit('close')"
          class="flex-1 md:flex-initial flex items-center justify-center px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-800 text-zinc-700 dark:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-700 text-xs font-bold transition-all cursor-pointer shadow-2xs h-9"
        >
          Cancel
        </button>

        <button
          type="button"
          @click="handleApply"
          class="flex-2 md:flex-initial flex items-center justify-center gap-2 rounded-xl bg-blue-600 hover:bg-blue-700 px-5 py-2 text-xs font-bold text-white transition-all cursor-pointer shadow-md shadow-blue-500/20 h-9 md:ml-auto"
        >
          Show {{ matchingStudentsCount }} Students
        </button>
      </div>
    </div>
  </div>
</template>
