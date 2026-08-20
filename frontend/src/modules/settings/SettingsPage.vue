<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import {
  Tag,
  GraduationCap,
  Users,
  Contact,
  PlusCircle,
  Pencil,
  Trash2,
  X,
  Loader2,
  School,
  Bookmark,
  Search,
  Folder as FolderIcon,
  Building2,
  CreditCard,
  Check
} from 'lucide-vue-next'
import { settingsApi, type TariffOption, type GeneralOption, type UniversityStatusOption, type CustomTag } from '@/api/settings'
import { useUiStore } from '@/stores/ui'
import { useQueryClient } from '@tanstack/vue-query'

const uiStore = useUiStore()
const queryClient = useQueryClient()

const invalidateGlobalCaches = async () => {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: ['folders'] }),
    queryClient.invalidateQueries({ queryKey: ['student-options'] }),
    queryClient.invalidateQueries({ queryKey: ['settings-universities'] }),
    queryClient.invalidateQueries({ queryKey: ['students'] }),
    queryClient.invalidateQueries({ queryKey: ['all-students-roster'] }),
    queryClient.invalidateQueries({ queryKey: ['status-students'] }),
    queryClient.invalidateQueries({ queryKey: ['payment-overview'] }),
    queryClient.invalidateQueries({ queryKey: ['payment-history'] }),
  ])
}

const CUSTOM_TAG_ICONS = [
  { emoji: '🏷️', label: 'Default Tag' },
  { emoji: '⭐', label: 'Star' },
  { emoji: '🔥', label: 'Fire / Urgent' },
  { emoji: '⚡', label: 'Lightning' },
  { emoji: '✅', label: 'Verified' },
  { emoji: '⚠️', label: 'Warning' },
  { emoji: '🛑', label: 'Stop / Hold' },
  { emoji: '🎯', label: 'Target' },
  { emoji: '💼', label: 'Briefcase' },
  { emoji: '📁', label: 'Folder' },
  { emoji: '✈️', label: 'Flight' },
  { emoji: '🌐', label: 'Global' },
  { emoji: '🏆', label: 'Trophy' },
  { emoji: '💡', label: 'Idea' },
  { emoji: '🔔', label: 'Notification' },
  { emoji: '🚀', label: 'Rocket' },
  { emoji: '🎉', label: 'Party' },
  { emoji: '❤️', label: 'Heart' },
  { emoji: '👍', label: 'Thumbs Up' },
  { emoji: '🤝', label: 'Handshake' },
  { emoji: '📈', label: 'Growth' },
  { emoji: '🔍', label: 'Review' },
  { emoji: '🛡️', label: 'Security' },
  { emoji: '🇰🇷', label: 'South Korea' },
]

// ── Tab Configurations (1-to-1 UniApp2) ──────────────────────────────
const TABS_CONFIG = {
  tariff: {
    id: 'tariff',
    label: 'Tariff Options',
    subLabel: 'Pricing plans',
    description: 'Configure student pricing structures and subscription package options.',
    icon: Tag,
    colorClass: 'text-blue-500 bg-blue-50 dark:bg-blue-950/20 border-blue-100 dark:border-blue-900/30',
    activeColorClass: 'bg-blue-500/10 text-blue-500 dark:bg-blue-500/20',
    btnBgClass: 'bg-blue-600 hover:bg-blue-700 text-white',
    addText: 'Add Tariff',
  },
  level: {
    id: 'level',
    label: 'Education Levels',
    subLabel: 'Academic levels',
    description: 'Configure available academic levels of study (e.g. BACHELOR, MASTER, LANGUAGE).',
    icon: GraduationCap,
    colorClass: 'text-purple-500 bg-purple-50 dark:bg-purple-950/20 border-purple-100 dark:border-purple-900/30',
    activeColorClass: 'bg-purple-500/10 text-purple-500 dark:bg-purple-500/20',
    btnBgClass: 'bg-purple-600 hover:bg-purple-700 text-white',
    addText: 'Add Level',
  },
  group: {
    id: 'group',
    label: 'Student Groups',
    subLabel: 'Cohort groups',
    description: 'Organize students into intake cohorts or study groups for bulk tracking.',
    icon: Users,
    colorClass: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-950/20 border-emerald-100 dark:border-emerald-900/30',
    activeColorClass: 'bg-emerald-500/10 text-emerald-500 dark:bg-emerald-500/20',
    btnBgClass: 'bg-emerald-600 hover:bg-emerald-700 text-white',
    addText: 'Add Group',
  },
  lead: {
    id: 'lead',
    label: 'Lead Sources',
    subLabel: 'Marketing channels',
    description: 'Track acquisition campaigns and external platforms referring potential students.',
    icon: Contact,
    colorClass: 'text-amber-500 bg-amber-50 dark:bg-amber-950/20 border-amber-100 dark:border-amber-900/30',
    activeColorClass: 'bg-amber-500/10 text-amber-500 dark:bg-amber-500/20',
    btnBgClass: 'bg-amber-600 hover:bg-amber-700 text-white',
    addText: 'Add Lead Source',
  },
  coordinator: {
    id: 'coordinator',
    label: 'Kordinators',
    subLabel: 'Staff advisors',
    description: 'Manage counselor staff and regional advisors assigned to student dossiers.',
    icon: Users,
    colorClass: 'text-rose-500 bg-rose-50 dark:bg-rose-950/20 border-rose-100 dark:border-rose-900/30',
    activeColorClass: 'bg-rose-500/10 text-rose-500 dark:bg-rose-500/20',
    btnBgClass: 'bg-rose-600 hover:bg-rose-700 text-white',
    addText: 'Add Kordinator',
  },
  tag: {
    id: 'tag',
    label: 'Custom Tags',
    subLabel: 'Workflow labels',
    description: 'Manage workflow tags with colored emoji badges to mark student pipeline stages.',
    icon: Bookmark,
    colorClass: 'text-indigo-500 bg-indigo-50 dark:bg-indigo-950/20 border-indigo-100 dark:border-indigo-900/30',
    activeColorClass: 'bg-indigo-500/10 text-indigo-500 dark:bg-indigo-500/20',
    btnBgClass: 'bg-indigo-600 hover:bg-indigo-700 text-white',
    addText: 'Add Custom Tag',
  },
  university: {
    id: 'university',
    label: 'Universities',
    subLabel: 'Partner institutions',
    description: 'Catalog partner universities, language academies, and global colleges.',
    icon: School,
    colorClass: 'text-sky-500 bg-sky-50 dark:bg-sky-950/20 border-sky-100 dark:border-sky-900/30',
    activeColorClass: 'bg-sky-500/10 text-sky-500 dark:bg-sky-500/20',
    btnBgClass: 'bg-sky-600 hover:bg-sky-700 text-white',
    addText: 'Add University',
  },
  folder: {
    id: 'folder',
    label: 'Student Folders',
    subLabel: 'Workflow Folders',
    description: 'Create custom folders to organize students. Students can be reassigned between folders under quick actions.',
    icon: FolderIcon,
    colorClass: 'text-rose-500 bg-rose-50 dark:bg-rose-950/20 border-rose-100 dark:border-rose-900/30',
    activeColorClass: 'bg-rose-500/10 text-rose-500 dark:bg-rose-500/20',
    btnBgClass: 'bg-rose-600 hover:bg-rose-700 text-white',
    addText: 'Add Folder',
  },
  office: {
    id: 'office',
    label: 'Office Branches',
    subLabel: 'Offices',
    description: 'Configure branch locations for client intake (e.g. Andijon, Toshkent).',
    icon: Building2,
    colorClass: 'text-cyan-500 bg-cyan-50 dark:bg-cyan-950/20 border-cyan-100 dark:border-cyan-900/30',
    activeColorClass: 'bg-cyan-500/10 text-cyan-500 dark:bg-cyan-500/20',
    btnBgClass: 'bg-cyan-600 hover:bg-cyan-700 text-white',
    addText: 'Add Office',
  },
  payment_setting: {
    id: 'payment_setting',
    label: 'Payments Settings',
    subLabel: 'Payment options',
    description: 'Configure payment methods, transaction receivers, and note templates.',
    icon: CreditCard,
    colorClass: 'text-orange-500 bg-orange-50 dark:bg-orange-950/20 border-orange-100 dark:border-orange-900/30',
    activeColorClass: 'bg-orange-500/10 text-orange-500 dark:bg-orange-500/20',
    btnBgClass: 'bg-orange-600 hover:bg-orange-700 text-white',
    addText: 'Add Option',
  },
  university_status: {
    id: 'university_status',
    label: 'University Statuses',
    subLabel: 'Status stages',
    description: 'Define student pipeline statuses for university admissions (e.g. Chosen, Accepted).',
    icon: Bookmark,
    colorClass: 'text-pink-500 bg-pink-50 dark:bg-pink-950/20 border-pink-100 dark:border-pink-900/30',
    activeColorClass: 'bg-pink-500/10 text-pink-500 dark:bg-pink-500/20',
    btnBgClass: 'bg-pink-600 hover:bg-pink-700 text-white',
    addText: 'Add Status',
  },
}

type TabType = keyof typeof TABS_CONFIG

const activeTab = ref<TabType>('tariff')
const searchQuery = ref('')
const loading = ref(false)

// Data states
const tariffs = ref<TariffOption[]>([])
const levels = ref<GeneralOption[]>([])
const groups = ref<GeneralOption[]>([])
const leads = ref<GeneralOption[]>([])
const coordinators = ref<GeneralOption[]>([])
const universities = ref<GeneralOption[]>([])
const folders = ref<GeneralOption[]>([])
const offices = ref<GeneralOption[]>([
  { id: '1', name: 'ANDIJON OFFIS' },
  { id: '2', name: 'TOSHKENT OFFIS' }
])
const paymentMethods = ref<GeneralOption[]>([])
const paymentReceivers = ref<GeneralOption[]>([])
const paymentNoteTemplates = ref<GeneralOption[]>([])
const universityStatuses = ref<UniversityStatusOption[]>([])
const customTagsRegistry = ref<CustomTag[]>([
  { name: 'Call', icon: '📞' },
  { name: 'Apply', icon: '🎓' },
  { name: 'Documents', icon: '📄' },
  { name: 'Payment', icon: '💰' }
])

// Modal State
const isModalOpen = ref(false)
const modalType = ref<string>('tariff')
const modalMode = ref<'add' | 'edit'>('add')
const editingId = ref<string | null>(null)
const formName = ref('')
const formPrice = ref('')
const formColorClass = ref('text-blue-500')
const submitting = ref(false)
const modalError = ref<string | null>(null)

// Tag Modal State
const isTagModalOpen = ref(false)
const tagModalMode = ref<'add' | 'edit'>('add')
const editingTag = ref<CustomTag | null>(null)
const tagFormName = ref('')
const tagFormEmoji = ref('🏷️')
const isTagEmojiPickerOpen = ref(false)

const formatCurrency = (val: number) => {
  return String(Math.round(val)).replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' UZS'
}

const fetchAllOptions = async () => {
  try {
    loading.value = true
    const [
      tariffsData,
      levelsData,
      groupsData,
      leadsData,
      coordinatorsData,
      universitiesData,
      foldersData,
      methodsData,
      receiversData,
      notesData,
      statusesData
    ] = await Promise.all([
      settingsApi.getTariffs(),
      settingsApi.getLevels(),
      settingsApi.getGroups(),
      settingsApi.getLeads(),
      settingsApi.getCoordinators(),
      settingsApi.getUniversities(),
      settingsApi.getFolders(),
      settingsApi.getPaymentMethods(),
      settingsApi.getPaymentReceivers(),
      settingsApi.getPaymentNotes(),
      settingsApi.getUniversityStatuses(),
    ])

    tariffs.value = tariffsData || []
    levels.value = levelsData || []
    groups.value = groupsData || []
    leads.value = leadsData || []
    coordinators.value = coordinatorsData || []
    universities.value = universitiesData || []
    folders.value = foldersData || []
    paymentMethods.value = methodsData || []
    paymentReceivers.value = receiversData || []
    paymentNoteTemplates.value = notesData || []
    universityStatuses.value = statusesData || []

    const savedTags = localStorage.getItem('customTagsRegistry')
    if (savedTags) {
      try {
        customTagsRegistry.value = JSON.parse(savedTags)
      } catch (e) {
        console.error(e)
      }
    }
  } catch (err: any) {
    console.error('Error loading settings:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAllOptions()
})

// Search filtered lists
const query = computed(() => searchQuery.value.trim().toLowerCase())
const filteredTariffs = computed(() => tariffs.value.filter(t => t.name.toLowerCase().includes(query.value)))
const filteredLevels = computed(() => levels.value.filter(l => l.name.toLowerCase().includes(query.value)))
const filteredGroups = computed(() => groups.value.filter(g => g.name.toLowerCase().includes(query.value)))
const filteredLeads = computed(() => leads.value.filter(l => l.name.toLowerCase().includes(query.value)))
const filteredCoordinators = computed(() => coordinators.value.filter(c => c.name.toLowerCase().includes(query.value)))
const filteredUniversities = computed(() => universities.value.filter(u => u.name.toLowerCase().includes(query.value)))
const filteredFolders = computed(() => folders.value.filter(f => f.name.toLowerCase().includes(query.value)))
const filteredOffices = computed(() => offices.value.filter(o => o.name.toLowerCase().includes(query.value)))
const filteredPaymentMethods = computed(() => paymentMethods.value.filter(pm => pm.name.toLowerCase().includes(query.value)))
const filteredPaymentReceivers = computed(() => paymentReceivers.value.filter(pr => pr.name.toLowerCase().includes(query.value)))
const filteredPaymentNoteTemplates = computed(() => paymentNoteTemplates.value.filter(pnt => pnt.name.toLowerCase().includes(query.value)))
const filteredUniversityStatuses = computed(() => universityStatuses.value.filter(us => us.name.toLowerCase().includes(query.value)))
const filteredTags = computed(() => customTagsRegistry.value.filter(t => t.name.toLowerCase().includes(query.value)))

// Modal handlers
const handleOpenAdd = (type: string) => {
  modalType.value = type
  modalMode.value = 'add'
  editingId.value = null
  formName.value = ''
  formPrice.value = ''
  formColorClass.value = 'text-blue-500'
  modalError.value = null
  isModalOpen.value = true
}

const handleOpenEdit = (type: string, item: any) => {
  modalType.value = type
  modalMode.value = 'edit'
  editingId.value = String(item.id)
  formName.value = item.name
  formPrice.value = type === 'tariff' ? String(item.price) : ''
  formColorClass.value = item.color_class || 'text-blue-500'
  modalError.value = null
  isModalOpen.value = true
}

const handleDelete = async (type: string, id: string, name: string) => {
  if (!confirm(`Are you sure you want to delete "${name}"?`)) return
  try {
    if (type === 'tariff') await settingsApi.deleteTariff(id)
    else if (type === 'level') await settingsApi.deleteLevel(id)
    else if (type === 'group') await settingsApi.deleteGroup(id)
    else if (type === 'lead') await settingsApi.deleteLead(id)
    else if (type === 'coordinator') await settingsApi.deleteCoordinator(id)
    else if (type === 'university') await settingsApi.deleteUniversity(id)
    else if (type === 'folder') await settingsApi.deleteFolder(id)
    else if (type === 'payment_method') await settingsApi.deletePaymentMethod(id)
    else if (type === 'payment_receiver') await settingsApi.deletePaymentReceiver(id)
    else if (type === 'payment_note_template') await settingsApi.deletePaymentNote(id)
    else if (type === 'university_status') await settingsApi.deleteUniversityStatus(id)
    await fetchAllOptions()
    await invalidateGlobalCaches()
    uiStore.addToast({ type: 'success', title: 'Deleted', message: `"${name}" removed successfully.` })
  } catch (err: any) {
    uiStore.addToast({ type: 'error', title: 'Delete Failed', message: err.message || 'Failed to delete item.' })
  }
}

const handleSubmit = async (e: Event) => {
  e.preventDefault()
  if (!formName.value.trim()) {
    modalError.value = 'Name is required.'
    return
  }
  submitting.value = true
  modalError.value = null

  try {
    const name = formName.value.trim()
    if (modalType.value === 'tariff') {
      const price = Number(formPrice.value.replace(/[^0-9.-]+/g, ''))
      if (isNaN(price) || price < 0) throw new Error('Price must be a valid positive number.')
      if (modalMode.value === 'add') await settingsApi.createTariff({ name, price })
      else if (editingId.value) await settingsApi.updateTariff(editingId.value, { name, price })
    } else if (modalType.value === 'level') {
      if (modalMode.value === 'add') await settingsApi.createLevel({ name })
      else if (editingId.value) await settingsApi.updateLevel(editingId.value, { name })
    } else if (modalType.value === 'group') {
      if (modalMode.value === 'add') await settingsApi.createGroup({ name })
      else if (editingId.value) await settingsApi.updateGroup(editingId.value, { name })
    } else if (modalType.value === 'lead') {
      if (modalMode.value === 'add') await settingsApi.createLead({ name })
      else if (editingId.value) await settingsApi.updateLead(editingId.value, { name })
    } else if (modalType.value === 'coordinator') {
      if (modalMode.value === 'add') await settingsApi.createCoordinator({ name })
      else if (editingId.value) await settingsApi.updateCoordinator(editingId.value, { name })
    } else if (modalType.value === 'university') {
      if (modalMode.value === 'add') await settingsApi.createUniversity({ name })
      else if (editingId.value) await settingsApi.updateUniversity(editingId.value, { name })
    } else if (modalType.value === 'folder') {
      if (modalMode.value === 'add') await settingsApi.createFolder(name)
    } else if (modalType.value === 'payment_method') {
      if (modalMode.value === 'add') await settingsApi.createPaymentMethod({ name })
    } else if (modalType.value === 'payment_receiver') {
      if (modalMode.value === 'add') await settingsApi.createPaymentReceiver({ name })
    } else if (modalType.value === 'payment_note_template') {
      if (modalMode.value === 'add') await settingsApi.createPaymentNote({ name })
    } else if (modalType.value === 'university_status') {
      if (modalMode.value === 'add') await settingsApi.createUniversityStatus({ name, color_class: formColorClass.value })
      else if (editingId.value) await settingsApi.updateUniversityStatus(editingId.value, { name, color_class: formColorClass.value })
    }

    isModalOpen.value = false
    await fetchAllOptions()
    await invalidateGlobalCaches()
    uiStore.addToast({ type: 'success', title: 'Success', message: `Saved "${name}" successfully.` })
  } catch (err: any) {
    modalError.value = err.response?.data?.detail || err.message || 'Failed to save option.'
  } finally {
    submitting.value = false
  }
}

// Custom Tag Modals
const handleOpenAddTag = () => {
  tagModalMode.value = 'add'
  editingTag.value = null
  tagFormName.value = ''
  tagFormEmoji.value = CUSTOM_TAG_ICONS[0].emoji
  isTagEmojiPickerOpen.value = false
  isTagModalOpen.value = true
}

const handleOpenEditTag = (tag: CustomTag) => {
  tagModalMode.value = 'edit'
  editingTag.value = tag
  tagFormName.value = tag.name
  tagFormEmoji.value = tag.icon
  isTagEmojiPickerOpen.value = false
  isTagModalOpen.value = true
}

const handleSaveTag = async () => {
  const name = tagFormName.value.trim()
  if (!name) return
  if (tagModalMode.value === 'add') {
    customTagsRegistry.value.push({ name, icon: tagFormEmoji.value })
  } else if (tagModalMode.value === 'edit' && editingTag.value) {
    const orig = editingTag.value.name
    const idx = customTagsRegistry.value.findIndex(t => t.name === orig)
    if (idx !== -1) {
      customTagsRegistry.value[idx] = { name, icon: tagFormEmoji.value }
    }
  }
  localStorage.setItem('customTagsRegistry', JSON.stringify(customTagsRegistry.value))
  await invalidateGlobalCaches()
  isTagModalOpen.value = false
}

const handleDeleteTag = async (tagName: string) => {
  if (!confirm(`Delete tag "${tagName}"?`)) return
  customTagsRegistry.value = customTagsRegistry.value.filter(t => t.name !== tagName)
  localStorage.setItem('customTagsRegistry', JSON.stringify(customTagsRegistry.value))
  await invalidateGlobalCaches()
}

const getTabCount = (tabId: string) => {
  if (tabId === 'tariff') return tariffs.value.length
  if (tabId === 'level') return levels.value.length
  if (tabId === 'group') return groups.value.length
  if (tabId === 'lead') return leads.value.length
  if (tabId === 'coordinator') return coordinators.value.length
  if (tabId === 'tag') return customTagsRegistry.value.length
  if (tabId === 'university') return universities.value.length
  if (tabId === 'folder') return folders.value.length
  if (tabId === 'office') return offices.value.length
  if (tabId === 'payment_setting') return paymentMethods.value.length + paymentReceivers.value.length + paymentNoteTemplates.value.length
  if (tabId === 'university_status') return universityStatuses.value.length
  return 0
}

const activeConfig = computed(() => TABS_CONFIG[activeTab.value])
</script>

<template>
  <div class="space-y-5 animate-page-in">
    <!-- Header Bar -->
    <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-white dark:bg-[#111315] p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xs">
      <div>
        <h1 class="text-xl font-extrabold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
          <span>System Settings & Registry</span>
        </h1>
        <p class="text-xs text-zinc-500 font-medium mt-0.5">Configure tariffs, academic levels, cohorts, lead sources, and payment methods</p>
      </div>

      <div class="flex items-center gap-3 w-full sm:w-auto">
        <!-- Search -->
        <div class="relative flex-1 sm:w-64">
          <Search class="w-4 h-4 text-zinc-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Search option names..."
            class="w-full pl-9 pr-3 py-2 bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 rounded-xl text-xs text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20"
          />
        </div>

        <!-- Add Button -->
        <button
          v-if="activeTab === 'tag'"
          @click="handleOpenAddTag"
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 transition-all cursor-pointer shrink-0 bg-blue-600 hover:bg-blue-700 text-white"
        >
          <PlusCircle class="w-4 h-4" />
          <span>{{ activeConfig.addText }}</span>
        </button>

        <button
          v-else-if="activeTab !== 'payment_setting'"
          @click="handleOpenAdd(activeTab)"
          class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-bold shadow-md shadow-blue-500/20 transition-all cursor-pointer shrink-0"
          :class="activeConfig.btnBgClass"
        >
          <PlusCircle class="w-4 h-4" />
          <span>{{ activeConfig.addText }}</span>
        </button>
      </div>
    </div>

    <!-- Master-Detail Navigation & Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
      <!-- Left Category Navigation Tabs (w-[280px]) -->
      <div class="lg:col-span-4 xl:col-span-3 bg-white dark:bg-[#111315] p-2 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xs space-y-1">
        <button
          v-for="tab in Object.values(TABS_CONFIG)"
          :key="tab.id"
          @click="activeTab = tab.id as TabType"
          class="w-full flex items-center justify-between p-3 rounded-xl text-left text-xs font-bold transition-all cursor-pointer select-none"
          :class="[
            activeTab === tab.id
              ? 'bg-blue-50/80 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border border-blue-200/60 dark:border-blue-800/60 shadow-2xs'
              : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-850 hover:text-zinc-900 dark:hover:text-zinc-200 border border-transparent'
          ]"
        >
          <div class="flex items-center gap-3 min-w-0">
            <div
              class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border"
              :class="tab.colorClass"
            >
              <component :is="tab.icon" class="w-4 h-4" />
            </div>
            <div class="truncate">
              <div class="font-bold truncate">{{ tab.label }}</div>
              <div class="text-[10.5px] font-medium text-zinc-400 dark:text-zinc-500 truncate">{{ tab.subLabel }}</div>
            </div>
          </div>
          <span
            class="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono ml-2 shrink-0"
            :class="activeTab === tab.id ? 'bg-blue-600 text-white shadow-xs' : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500'"
          >
            {{ getTabCount(tab.id) }}
          </span>
        </button>
      </div>

      <!-- Right Active Category Content Panel -->
      <div class="lg:col-span-8 xl:col-span-9 bg-white dark:bg-[#111315] p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xs min-h-[480px] flex flex-col">
        <!-- Tab Content Header -->
        <div class="border-b border-zinc-100 dark:border-zinc-800 pb-4 mb-4 flex items-center justify-between">
          <div>
            <h2 class="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
              <component :is="activeConfig.icon" class="w-5 h-5 text-blue-600" />
              <span>{{ activeConfig.label }}</span>
            </h2>
            <p class="text-xs text-zinc-500 font-medium mt-0.5">{{ activeConfig.description }}</p>
          </div>
        </div>

        <div v-if="loading" class="flex-1 flex items-center justify-center py-16">
          <Loader2 class="w-8 h-8 text-blue-600 animate-spin" />
        </div>

        <!-- 1. Tariff Options -->
        <div v-else-if="activeTab === 'tariff'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredTariffs"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-blue-400 dark:hover:border-blue-500 rounded-xl shadow-2xs transition-all"
          >
            <div class="min-w-0">
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide truncate">{{ item.name }}</div>
              <div class="inline-flex items-center gap-1 mt-1 text-[10px] font-bold px-2 py-0.5 bg-blue-50 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 rounded-md font-mono">
                {{ formatCurrency(item.price) }}
              </div>
            </div>
            <div class="flex items-center gap-1 shrink-0 opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleOpenEdit('tariff', item)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white dark:hover:bg-zinc-750 rounded-lg text-blue-600 transition-all cursor-pointer"
                title="Edit"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button
                @click="handleDelete('tariff', item.id, item.name)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white dark:hover:bg-zinc-750 rounded-lg text-rose-600 transition-all cursor-pointer"
                title="Delete"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 2. Education Levels -->
        <div v-else-if="activeTab === 'level'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredLevels"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-purple-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-purple-50 dark:bg-purple-950/30 text-purple-600">
                <GraduationCap class="w-3.5 h-3.5" />
              </div>
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide truncate">{{ item.name }}</div>
            </div>
            <div class="flex items-center gap-1 shrink-0 opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleOpenEdit('level', item)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-blue-600 transition-all cursor-pointer"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button
                @click="handleDelete('level', item.id, item.name)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-rose-600 transition-all cursor-pointer"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 3. Student Groups -->
        <div v-else-if="activeTab === 'group'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredGroups"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-emerald-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-emerald-50 dark:bg-emerald-950/30 text-emerald-600">
                <Users class="w-3.5 h-3.5" />
              </div>
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide truncate">{{ item.name }}</div>
            </div>
            <div class="flex items-center gap-1 shrink-0 opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleOpenEdit('group', item)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-blue-600 transition-all cursor-pointer"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button
                @click="handleDelete('group', item.id, item.name)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-rose-600 transition-all cursor-pointer"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 4. Lead Sources -->
        <div v-else-if="activeTab === 'lead'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredLeads"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-amber-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-amber-50 dark:bg-amber-950/30 text-amber-600">
                <Contact class="w-3.5 h-3.5" />
              </div>
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate">{{ item.name }}</div>
            </div>
            <div class="flex items-center gap-1 shrink-0 opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleOpenEdit('lead', item)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-blue-600 transition-all cursor-pointer"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button
                @click="handleDelete('lead', item.id, item.name)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-rose-600 transition-all cursor-pointer"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 5. Coordinators -->
        <div v-else-if="activeTab === 'coordinator'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredCoordinators"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-rose-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-rose-50 dark:bg-rose-950/30 text-rose-600">
                <Users class="w-3.5 h-3.5" />
              </div>
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate">{{ item.name }}</div>
            </div>
            <div class="flex items-center gap-1 shrink-0 opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleOpenEdit('coordinator', item)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-blue-600 transition-all cursor-pointer"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button
                @click="handleDelete('coordinator', item.id, item.name)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-rose-600 transition-all cursor-pointer"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 6. Custom Tags -->
        <div v-else-if="activeTab === 'tag'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="tag in filteredTags"
            :key="tag.name"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-indigo-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/20 border border-indigo-100 dark:border-indigo-900/30 flex items-center justify-center text-lg shrink-0">
                {{ tag.icon }}
              </div>
              <span class="text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate">{{ tag.name }}</span>
            </div>
            <div class="flex items-center gap-1 shrink-0 opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleOpenEditTag(tag)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-blue-600 transition-all cursor-pointer"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button
                @click="handleDeleteTag(tag.name)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-rose-600 transition-all cursor-pointer"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 7. Universities -->
        <div v-else-if="activeTab === 'university'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredUniversities"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-sky-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-sky-50 dark:bg-sky-950/30 text-sky-600">
                <School class="w-3.5 h-3.5" />
              </div>
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate">{{ item.name }}</div>
            </div>
            <div class="flex items-center gap-1 shrink-0 opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleOpenEdit('university', item)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-blue-600 transition-all cursor-pointer"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button
                @click="handleDelete('university', item.id, item.name)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-rose-600 transition-all cursor-pointer"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 8. Student Folders -->
        <div v-else-if="activeTab === 'folder'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredFolders"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-rose-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-rose-50 dark:bg-rose-950/30 text-rose-600">
                <FolderIcon class="w-3.5 h-3.5" />
              </div>
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate">{{ item.name }}</div>
            </div>
            <div class="flex items-center gap-1 shrink-0 opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleDelete('folder', item.id, item.name)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-rose-600 transition-all cursor-pointer"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        <!-- 9. Office Branches -->
        <div v-else-if="activeTab === 'office'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredOffices"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-cyan-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 bg-cyan-50 dark:bg-cyan-950/30 text-cyan-600">
                <Building2 class="w-3.5 h-3.5" />
              </div>
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 uppercase tracking-wide truncate">{{ item.name }}</div>
            </div>
          </div>
        </div>

        <!-- 10. Payment Settings (Sub-sections) -->
        <div v-else-if="activeTab === 'payment_setting'" class="space-y-6">
          <!-- 10.1 Payment Methods -->
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <h3 class="text-xs font-bold text-zinc-800 dark:text-zinc-200 uppercase tracking-wider">Payment Methods</h3>
              <button
                @click="handleOpenAdd('payment_method')"
                class="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
              >
                <PlusCircle class="w-3.5 h-3.5" />
                <span>Add Method</span>
              </button>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              <div
                v-for="pm in filteredPaymentMethods"
                :key="pm.id"
                class="group flex items-center justify-between p-2.5 px-3 rounded-xl bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 text-xs font-bold"
              >
                <span>{{ pm.name }}</span>
                <button
                  @click="handleDelete('payment_method', pm.id, pm.name)"
                  class="opacity-0 group-hover:opacity-100 text-rose-500 hover:text-rose-700 transition-opacity cursor-pointer"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          <!-- 10.2 Payment Receivers -->
          <div class="space-y-3 border-t border-zinc-100 dark:border-zinc-800 pt-4">
            <div class="flex items-center justify-between">
              <h3 class="text-xs font-bold text-zinc-800 dark:text-zinc-200 uppercase tracking-wider">Payment Receivers</h3>
              <button
                @click="handleOpenAdd('payment_receiver')"
                class="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
              >
                <PlusCircle class="w-3.5 h-3.5" />
                <span>Add Receiver</span>
              </button>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              <div
                v-for="pr in filteredPaymentReceivers"
                :key="pr.id"
                class="group flex items-center justify-between p-2.5 px-3 rounded-xl bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 text-xs font-bold"
              >
                <span>{{ pr.name }}</span>
                <button
                  @click="handleDelete('payment_receiver', pr.id, pr.name)"
                  class="opacity-0 group-hover:opacity-100 text-rose-500 hover:text-rose-700 transition-opacity cursor-pointer"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          <!-- 10.3 Payment Note Templates -->
          <div class="space-y-3 border-t border-zinc-100 dark:border-zinc-800 pt-4">
            <div class="flex items-center justify-between">
              <h3 class="text-xs font-bold text-zinc-800 dark:text-zinc-200 uppercase tracking-wider">Quick Note Templates (Pills)</h3>
              <button
                @click="handleOpenAdd('payment_note_template')"
                class="text-xs font-bold text-blue-600 hover:text-blue-700 flex items-center gap-1 cursor-pointer"
              >
                <PlusCircle class="w-3.5 h-3.5" />
                <span>Add Note Pill</span>
              </button>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2.5">
              <div
                v-for="pnt in filteredPaymentNoteTemplates"
                :key="pnt.id"
                class="group flex items-center justify-between p-2.5 px-3 rounded-xl bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 text-xs font-bold"
              >
                <span>{{ pnt.name }}</span>
                <button
                  @click="handleDelete('payment_note_template', pnt.id, pnt.name)"
                  class="opacity-0 group-hover:opacity-100 text-rose-500 hover:text-rose-700 transition-opacity cursor-pointer"
                >
                  <Trash2 class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 11. University Statuses -->
        <div v-else-if="activeTab === 'university_status'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredUniversityStatuses"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-pink-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-3.5 h-3.5 rounded-full bg-blue-500" />
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate">{{ item.name }}</div>
            </div>
            <div class="flex items-center gap-1 shrink-0 opacity-80 sm:opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                @click="handleOpenEdit('university_status', item)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-blue-600 transition-all cursor-pointer"
              >
                <Pencil class="w-3.5 h-3.5" />
              </button>
              <button
                @click="handleDelete('university_status', item.id, item.name)"
                class="w-7 h-7 flex items-center justify-center border border-zinc-200 dark:border-zinc-700 hover:bg-white rounded-lg text-rose-600 transition-all cursor-pointer"
              >
                <Trash2 class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Option Modal Dialog -->
    <div
      v-if="isModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs select-none"
    >
      <div class="bg-white dark:bg-[#181a1d] border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-page-in">
        <div class="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
          <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
            {{ modalMode === 'add' ? 'Add New' : 'Edit' }} {{ modalType.replace('_', ' ') }}
          </h3>
          <button @click="isModalOpen = false" class="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 cursor-pointer">
            <X class="w-4 h-4" />
          </button>
        </div>

        <form @submit="handleSubmit" class="p-5 space-y-4 text-xs">
          <div v-if="modalError" class="p-2.5 bg-rose-50 dark:bg-rose-950/30 text-rose-600 rounded-xl border border-rose-200 dark:border-rose-800 text-xs font-semibold">
            {{ modalError }}
          </div>

          <div class="space-y-1.5">
            <label class="block font-bold text-zinc-700 dark:text-zinc-300">Name / Title</label>
            <input
              v-model="formName"
              type="text"
              required
              placeholder="Enter name..."
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 rounded-xl text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div v-if="modalType === 'tariff'" class="space-y-1.5">
            <label class="block font-bold text-zinc-700 dark:text-zinc-300">Price (UZS)</label>
            <input
              v-model="formPrice"
              type="number"
              required
              placeholder="e.g. 13000000"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 rounded-xl text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              @click="isModalOpen = false"
              class="px-4 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="submitting"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md shadow-blue-500/20 cursor-pointer disabled:opacity-50"
            >
              {{ submitting ? 'Saving...' : 'Save Option' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Custom Tag Modal Dialog with Emoji Selector -->
    <div
      v-if="isTagModalOpen"
      class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-xs select-none"
    >
      <div class="bg-white dark:bg-[#181a1d] border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-page-in">
        <div class="px-5 py-4 border-b border-zinc-100 dark:border-zinc-800 flex items-center justify-between">
          <h3 class="text-sm font-bold text-zinc-900 dark:text-zinc-100">
            {{ tagModalMode === 'add' ? 'Add Custom Tag' : 'Edit Tag' }}
          </h3>
          <button @click="isTagModalOpen = false" class="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 cursor-pointer">
            <X class="w-4 h-4" />
          </button>
        </div>

        <div class="p-5 space-y-4 text-xs">
          <div class="space-y-1.5">
            <label class="block font-bold text-zinc-700 dark:text-zinc-300">Tag Emoji Badge</label>
            <div class="flex flex-wrap gap-2 p-3 bg-zinc-50 dark:bg-zinc-850 rounded-xl border border-zinc-200 dark:border-zinc-700 max-h-36 overflow-y-auto">
              <button
                v-for="item in CUSTOM_TAG_ICONS"
                :key="item.emoji"
                type="button"
                @click="tagFormEmoji = item.emoji"
                class="w-8 h-8 rounded-lg text-lg flex items-center justify-center border transition-all cursor-pointer"
                :class="tagFormEmoji === item.emoji ? 'border-blue-600 bg-blue-50 dark:bg-blue-950/40 shadow-xs' : 'border-transparent hover:bg-zinc-200/60 dark:hover:bg-zinc-700'"
              >
                {{ item.emoji }}
              </button>
            </div>
          </div>

          <div class="space-y-1.5">
            <label class="block font-bold text-zinc-700 dark:text-zinc-300">Tag Label</label>
            <input
              v-model="tagFormName"
              type="text"
              required
              placeholder="e.g. VIP Student"
              class="w-full px-3 py-2 bg-zinc-50 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700 rounded-xl text-zinc-800 dark:text-zinc-200 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div class="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              @click="isTagModalOpen = false"
              class="px-4 py-2 border border-zinc-200 dark:border-zinc-700 rounded-xl font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              @click="handleSaveTag"
              class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-xl shadow-md shadow-blue-500/20 cursor-pointer"
            >
              Save Tag
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
