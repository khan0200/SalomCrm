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
import { useCustomTags } from '@/composables/useCustomTags'
import { useUniversityStatuses, STATUS_COLOR_OPTIONS } from '@/composables/useUniversityStatuses'
import { useUiStore } from '@/stores/ui'
import { useQueryClient } from '@tanstack/vue-query'

const { tagsRegistry: customTagsRegistry, fetchTags } = useCustomTags()
const {
  statusesRegistry,
  setStatuses,
  fetchStatuses,
  resolveColor,
  getStatusDotClass,
  getStatusBadgeClass
} = useUniversityStatuses()

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

const fetchAllOptions = async (silent = false) => {
  try {
    if (!silent) {
      loading.value = true
    }
    const [
      tariffsRes,
      levelsRes,
      groupsRes,
      leadsRes,
      coordinatorsRes,
      universitiesRes,
      foldersRes,
      methodsRes,
      receiversRes,
      notesRes,
      statusesRes
    ] = await Promise.allSettled([
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

    if (tariffsRes.status === 'fulfilled') tariffs.value = tariffsRes.value || []
    if (levelsRes.status === 'fulfilled') levels.value = levelsRes.value || []
    if (groupsRes.status === 'fulfilled') groups.value = groupsRes.value || []
    if (leadsRes.status === 'fulfilled') leads.value = leadsRes.value || []
    if (coordinatorsRes.status === 'fulfilled') coordinators.value = coordinatorsRes.value || []
    if (universitiesRes.status === 'fulfilled') universities.value = universitiesRes.value || []
    if (foldersRes.status === 'fulfilled') folders.value = foldersRes.value || []
    if (methodsRes.status === 'fulfilled') paymentMethods.value = methodsRes.value || []
    if (receiversRes.status === 'fulfilled') paymentReceivers.value = receiversRes.value || []
    if (notesRes.status === 'fulfilled') paymentNoteTemplates.value = notesRes.value || []
    if (statusesRes.status === 'fulfilled') {
      universityStatuses.value = statusesRes.value || []
      setStatuses(statusesRes.value || [])
    }

    await fetchTags(true)
  } catch (err: any) {
    console.error('Error loading settings:', err)
  } finally {
    if (!silent) {
      loading.value = false
    }
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
const filteredPaymentMethods = computed(() => paymentMethods.value.filter(p => p.name.toLowerCase().includes(query.value)))
const filteredPaymentReceivers = computed(() => paymentReceivers.value.filter(p => p.name.toLowerCase().includes(query.value)))
const filteredPaymentNoteTemplates = computed(() => paymentNoteTemplates.value.filter(p => p.name.toLowerCase().includes(query.value)))
const filteredUniversityStatuses = computed(() => universityStatuses.value.filter(u => u.name.toLowerCase().includes(query.value)))
const filteredTags = computed(() => customTagsRegistry.value.filter(t => t.name.toLowerCase().includes(query.value)))

// Action Handlers
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
  editingId.value = item.id
  formName.value = item.name
  formPrice.value = item.price ? String(item.price) : ''
  formColorClass.value = item.color_class || 'text-blue-500'
  modalError.value = null
  isModalOpen.value = true
}

const handleOpenAddTag = () => {
  tagModalMode.value = 'add'
  editingTag.value = null
  tagFormName.value = ''
  tagFormEmoji.value = '🏷️'
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
  isTagModalOpen.value = false

  const icon = tagFormEmoji.value
  const isEdit = tagModalMode.value === 'edit' && editingTag.value
  const origName = editingTag.value?.name
  const prevTags = [...customTagsRegistry.value]

  // Optimistic instant UI update
  if (isEdit) {
    const idx = customTagsRegistry.value.findIndex(t => t.name === origName)
    if (idx !== -1) {
      customTagsRegistry.value[idx] = { ...customTagsRegistry.value[idx], name, icon }
    }
    uiStore.addToast({ type: 'success', message: 'Custom tag updated' })
  } else {
    customTagsRegistry.value.push({ name, icon })
    uiStore.addToast({ type: 'success', message: 'Custom tag created' })
  }

  try {
    if (isEdit) {
      if (editingTag.value?.id) {
        await settingsApi.updateTag(editingTag.value.id, { name, icon })
      } else {
        const found = prevTags.find(t => t.name === origName)
        if (found?.id) {
          await settingsApi.updateTag(found.id, { name, icon })
        } else {
          await settingsApi.createTag({ name, icon })
        }
      }
    } else {
      await settingsApi.createTag({ name, icon })
    }
    await fetchTags(true)
    invalidateGlobalCaches()
  } catch (err: any) {
    customTagsRegistry.value = prevTags
    console.error('Error saving custom tag:', err)
    uiStore.addToast({ type: 'error', message: err.response?.data?.detail || 'Failed to save tag' })
  }
}

const handleDeleteTag = async (tagOrName: CustomTag | string) => {
  const tagName = typeof tagOrName === 'string' ? tagOrName : tagOrName.name
  const tagItem = typeof tagOrName === 'object' ? tagOrName : customTagsRegistry.value.find(t => t.name === tagName)
  if (!confirm(`Are you sure you want to delete custom tag "${tagName}"?`)) return

  // Instant optimistic removal
  const prevTags = [...customTagsRegistry.value]
  customTagsRegistry.value = customTagsRegistry.value.filter(t => t.name !== tagName)
  uiStore.addToast({ type: 'success', message: `Tag "${tagName}" deleted` })

  try {
    if (tagItem?.id) {
      await settingsApi.deleteTag(tagItem.id)
    }
    fetchTags(true)
    invalidateGlobalCaches()
  } catch (err: any) {
    customTagsRegistry.value = prevTags
    console.error('Error deleting tag:', err)
    uiStore.addToast({ type: 'error', message: 'Failed to delete tag' })
  }
}

const handleDelete = async (type: string, id: string, name: string) => {
  if (!confirm(`Are you sure you want to delete "${name}"?`)) return

  // 1. Snapshot previous state for rollback if network fails
  const prevTariffs = [...tariffs.value]
  const prevLevels = [...levels.value]
  const prevGroups = [...groups.value]
  const prevLeads = [...leads.value]
  const prevCoordinators = [...coordinators.value]
  const prevUniversities = [...universities.value]
  const prevFolders = [...folders.value]
  const prevMethods = [...paymentMethods.value]
  const prevReceivers = [...paymentReceivers.value]
  const prevNotes = [...paymentNoteTemplates.value]
  const prevStatuses = [...universityStatuses.value]

  // 2. Instantaneous optimistic removal from local state (NO loading spinner / delay!)
  if (type === 'tariff') tariffs.value = tariffs.value.filter(item => item.id !== id)
  else if (type === 'level') levels.value = levels.value.filter(item => item.id !== id)
  else if (type === 'group') groups.value = groups.value.filter(item => item.id !== id)
  else if (type === 'lead') leads.value = leads.value.filter(item => item.id !== id)
  else if (type === 'coordinator') coordinators.value = coordinators.value.filter(item => item.id !== id)
  else if (type === 'university') universities.value = universities.value.filter(item => item.id !== id)
  else if (type === 'folder') folders.value = folders.value.filter(item => item.id !== id)
  else if (type === 'payment_method') paymentMethods.value = paymentMethods.value.filter(item => item.id !== id)
  else if (type === 'payment_receiver') paymentReceivers.value = paymentReceivers.value.filter(item => item.id !== id)
  else if (type === 'payment_note_template') paymentNoteTemplates.value = paymentNoteTemplates.value.filter(item => item.id !== id)
  else if (type === 'university_status') universityStatuses.value = universityStatuses.value.filter(item => item.id !== id)

  uiStore.addToast({ type: 'success', title: 'Deleted', message: `"${name}" removed.` })

  // 3. Asynchronous background server delete
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

    invalidateGlobalCaches()
  } catch (err: any) {
    // Revert local state on error
    tariffs.value = prevTariffs
    levels.value = prevLevels
    groups.value = prevGroups
    leads.value = prevLeads
    coordinators.value = prevCoordinators
    universities.value = prevUniversities
    folders.value = prevFolders
    paymentMethods.value = prevMethods
    paymentReceivers.value = prevReceivers
    paymentNoteTemplates.value = prevNotes
    universityStatuses.value = prevStatuses
    uiStore.addToast({ type: 'error', title: 'Delete Failed', message: err.message || 'Failed to delete item.' })
  }
}

const handleSubmit = async (e: Event) => {
  e.preventDefault()
  if (!formName.value.trim()) {
    modalError.value = 'Name is required.'
    return
  }
  const name = formName.value.trim()
  const type = modalType.value
  const isEdit = modalMode.value === 'edit' && editingId.value
  const id = editingId.value

  // Close modal instantly
  isModalOpen.value = false
  uiStore.addToast({ type: 'success', title: 'Success', message: `Saved "${name}".` })

  try {
    if (type === 'tariff') {
      const price = Number(formPrice.value.replace(/[^0-9.-]+/g, ''))
      if (isNaN(price) || price < 0) throw new Error('Price must be a valid positive number.')
      if (isEdit && id) {
        const idx = tariffs.value.findIndex(t => t.id === id)
        if (idx !== -1) tariffs.value[idx] = { ...tariffs.value[idx], name, price }
        await settingsApi.updateTariff(id, { name, price })
      } else {
        const created = await settingsApi.createTariff({ name, price })
        tariffs.value.push(created)
      }
    } else if (type === 'level') {
      if (isEdit && id) {
        const idx = levels.value.findIndex(l => l.id === id)
        if (idx !== -1) levels.value[idx] = { ...levels.value[idx], name }
        await settingsApi.updateLevel(id, { name })
      } else {
        const created = await settingsApi.createLevel({ name })
        levels.value.push(created)
      }
    } else if (type === 'group') {
      if (isEdit && id) {
        const idx = groups.value.findIndex(g => g.id === id)
        if (idx !== -1) groups.value[idx] = { ...groups.value[idx], name }
        await settingsApi.updateGroup(id, { name })
      } else {
        const created = await settingsApi.createGroup({ name })
        groups.value.push(created)
      }
    } else if (type === 'lead') {
      if (isEdit && id) {
        const idx = leads.value.findIndex(l => l.id === id)
        if (idx !== -1) leads.value[idx] = { ...leads.value[idx], name }
        await settingsApi.updateLead(id, { name })
      } else {
        const created = await settingsApi.createLead({ name })
        leads.value.push(created)
      }
    } else if (type === 'coordinator') {
      if (isEdit && id) {
        const idx = coordinators.value.findIndex(c => c.id === id)
        if (idx !== -1) coordinators.value[idx] = { ...coordinators.value[idx], name }
        await settingsApi.updateCoordinator(id, { name })
      } else {
        const created = await settingsApi.createCoordinator({ name })
        coordinators.value.push(created)
      }
    } else if (type === 'university') {
      if (isEdit && id) {
        const idx = universities.value.findIndex(u => u.id === id)
        if (idx !== -1) universities.value[idx] = { ...universities.value[idx], name }
        await settingsApi.updateUniversity(id, { name })
      } else {
        const created = await settingsApi.createUniversity({ name })
        universities.value.push(created)
      }
    } else if (type === 'folder') {
      const created = await settingsApi.createFolder(name)
      folders.value.push(created)
    } else if (type === 'payment_method') {
      const created = await settingsApi.createPaymentMethod({ name })
      paymentMethods.value.push(created)
    } else if (type === 'payment_receiver') {
      const created = await settingsApi.createPaymentReceiver({ name })
      paymentReceivers.value.push(created)
    } else if (type === 'payment_note_template') {
      const created = await settingsApi.createPaymentNote({ name })
      paymentNoteTemplates.value.push(created)
    } else if (type === 'university_status') {
      const color_class = formColorClass.value
      if (isEdit && id) {
        const idx = universityStatuses.value.findIndex(s => s.id === id)
        if (idx !== -1) universityStatuses.value[idx] = { ...universityStatuses.value[idx], name, color_class }
        const regIdx = statusesRegistry.value.findIndex(s => s.id === id || s.name.toUpperCase() === name.toUpperCase())
        if (regIdx !== -1) {
          statusesRegistry.value[regIdx] = { ...statusesRegistry.value[regIdx], name, color_class }
        } else {
          statusesRegistry.value.push({ id: String(id), name, color_class })
        }
        await settingsApi.updateUniversityStatus(id, { name, color_class })
      } else {
        const created = await settingsApi.createUniversityStatus({ name, color_class })
        universityStatuses.value.push(created)
        statusesRegistry.value.push({ id: String(created.id), name: created.name, color_class: created.color_class })
      }
      setStatuses(universityStatuses.value)
    }

    // Silent background sync
    fetchAllOptions(true)
    invalidateGlobalCaches()
  } catch (err: any) {
    console.error('Submit error:', err)
    uiStore.addToast({ type: 'error', title: 'Save Failed', message: err.message || 'Failed to save option.' })
    fetchAllOptions(true)
  }
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
      <div class="lg:col-span-4 xl:col-span-3 bg-white dark:bg-[#111315] p-1.5 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xs space-y-0.5">
        <button
          v-for="tab in Object.values(TABS_CONFIG)"
          :key="tab.id"
          @click="activeTab = tab.id as TabType"
          class="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-left text-xs font-bold transition-all cursor-pointer select-none"
          :class="[
            activeTab === tab.id
              ? 'bg-blue-50/80 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400 border border-blue-200/60 dark:border-blue-800/60 shadow-2xs'
              : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-50 dark:hover:bg-zinc-850 hover:text-zinc-900 dark:hover:text-zinc-200 border border-transparent'
          ]"
        >
          <div class="flex items-center gap-2.5 min-w-0">
            <div
              class="w-7 h-7 rounded-md flex items-center justify-center shrink-0 border"
              :class="tab.colorClass"
            >
              <component :is="tab.icon" class="w-3.5 h-3.5" />
            </div>
            <div class="truncate">
              <div class="font-bold truncate text-[12px]">{{ tab.label }}</div>
              <div class="text-[10px] font-medium text-zinc-400 dark:text-zinc-500 truncate leading-tight">{{ tab.subLabel }}</div>
            </div>
          </div>
          <span
            class="px-1.5 py-0.2 rounded-full text-[9.5px] font-bold font-mono ml-2 shrink-0"
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
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl flex items-center justify-center border shrink-0 shadow-2xs" :class="activeConfig.colorClass">
              <component :is="activeConfig.icon" class="w-5 h-5" />
            </div>
            <div>
              <h2 class="text-base font-bold text-zinc-900 dark:text-zinc-100">
                {{ activeConfig.label }}
              </h2>
              <p class="text-xs text-zinc-500 font-medium mt-0.5">{{ activeConfig.description }}</p>
            </div>
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
                @click="handleDeleteTag(tag)"
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

        <!-- 10. Payment Settings (3-Column Layout matching screenshot) -->
        <div v-else-if="activeTab === 'payment_setting'" class="grid grid-cols-1 md:grid-cols-3 gap-5 items-start">
          <!-- Column 1: PAYMENT METHODS -->
          <div class="bg-white dark:bg-[#15171a] rounded-2xl border border-zinc-200 dark:border-zinc-800 p-4.5 flex flex-col min-h-[380px] shadow-2xs">
            <div class="flex items-center justify-between pb-3.5 mb-3.5 border-b border-zinc-100 dark:border-zinc-800">
              <h3 class="text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">Payment Methods</h3>
              <button
                type="button"
                @click="handleOpenAdd('payment_method')"
                class="text-xs font-bold text-orange-500 hover:text-orange-600 dark:text-orange-400 flex items-center gap-1 cursor-pointer transition-colors"
              >
                <PlusCircle class="w-4 h-4" />
                <span>Add</span>
              </button>
            </div>

            <div class="space-y-2.5 flex-1 overflow-y-auto">
              <div
                v-if="filteredPaymentMethods.length === 0"
                class="py-12 text-center text-xs text-zinc-400 italic"
              >
                No payment methods added
              </div>

              <div
                v-for="pm in filteredPaymentMethods"
                :key="pm.id"
                class="group flex items-center justify-between px-3.5 py-3 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-750 text-xs font-bold text-zinc-800 dark:text-zinc-200 hover:border-orange-400 dark:hover:border-orange-500 transition-all shadow-2xs"
              >
                <span class="truncate">{{ pm.name }}</span>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <button
                    type="button"
                    @click="handleOpenEdit('payment_method', pm)"
                    class="p-1 text-zinc-400 hover:text-blue-600 transition-colors cursor-pointer"
                    title="Edit"
                  >
                    <Pencil class="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    @click="handleDelete('payment_method', pm.id, pm.name)"
                    class="p-1 text-zinc-400 hover:text-rose-500 transition-colors cursor-pointer"
                    title="Delete"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Column 2: PAYMENT RECEIVERS -->
          <div class="bg-white dark:bg-[#15171a] rounded-2xl border border-zinc-200 dark:border-zinc-800 p-4.5 flex flex-col min-h-[380px] shadow-2xs">
            <div class="flex items-center justify-between pb-3.5 mb-3.5 border-b border-zinc-100 dark:border-zinc-800">
              <h3 class="text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">Payment Receivers</h3>
              <button
                type="button"
                @click="handleOpenAdd('payment_receiver')"
                class="text-xs font-bold text-orange-500 hover:text-orange-600 dark:text-orange-400 flex items-center gap-1 cursor-pointer transition-colors"
              >
                <PlusCircle class="w-4 h-4" />
                <span>Add</span>
              </button>
            </div>

            <div class="space-y-2.5 flex-1 overflow-y-auto">
              <div
                v-if="filteredPaymentReceivers.length === 0"
                class="py-12 text-center text-xs text-zinc-400 italic"
              >
                No payment receivers added
              </div>

              <div
                v-for="pr in filteredPaymentReceivers"
                :key="pr.id"
                class="group flex items-center justify-between px-3.5 py-3 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-750 text-xs font-bold text-zinc-800 dark:text-zinc-200 hover:border-orange-400 dark:hover:border-orange-500 transition-all shadow-2xs"
              >
                <span class="truncate">{{ pr.name }}</span>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <button
                    type="button"
                    @click="handleOpenEdit('payment_receiver', pr)"
                    class="p-1 text-zinc-400 hover:text-blue-600 transition-colors cursor-pointer"
                    title="Edit"
                  >
                    <Pencil class="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    @click="handleDelete('payment_receiver', pr.id, pr.name)"
                    class="p-1 text-zinc-400 hover:text-rose-500 transition-colors cursor-pointer"
                    title="Delete"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Column 3: QUICK NOTE TEMPLATES -->
          <div class="bg-white dark:bg-[#15171a] rounded-2xl border border-zinc-200 dark:border-zinc-800 p-4.5 flex flex-col min-h-[380px] shadow-2xs">
            <div class="flex items-center justify-between pb-3.5 mb-3.5 border-b border-zinc-100 dark:border-zinc-800">
              <h3 class="text-xs font-bold text-zinc-700 dark:text-zinc-300 uppercase tracking-wider">Quick Note Templates</h3>
              <button
                type="button"
                @click="handleOpenAdd('payment_note_template')"
                class="text-xs font-bold text-orange-500 hover:text-orange-600 dark:text-orange-400 flex items-center gap-1 cursor-pointer transition-colors"
              >
                <PlusCircle class="w-4 h-4" />
                <span>Add</span>
              </button>
            </div>

            <div class="space-y-2.5 flex-1 overflow-y-auto">
              <div
                v-if="filteredPaymentNoteTemplates.length === 0"
                class="py-12 text-center text-xs text-zinc-400 italic"
              >
                No quick note templates added
              </div>

              <div
                v-for="pnt in filteredPaymentNoteTemplates"
                :key="pnt.id"
                class="group flex items-center justify-between px-3.5 py-3 rounded-xl bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-750 text-xs font-bold text-zinc-800 dark:text-zinc-200 hover:border-orange-400 dark:hover:border-orange-500 transition-all shadow-2xs"
              >
                <span class="truncate">{{ pnt.name }}</span>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                  <button
                    type="button"
                    @click="handleOpenEdit('payment_note_template', pnt)"
                    class="p-1 text-zinc-400 hover:text-blue-600 transition-colors cursor-pointer"
                    title="Edit"
                  >
                    <Pencil class="w-3.5 h-3.5" />
                  </button>
                  <button
                    type="button"
                    @click="handleDelete('payment_note_template', pnt.id, pnt.name)"
                    class="p-1 text-zinc-400 hover:text-rose-500 transition-colors cursor-pointer"
                    title="Delete"
                  >
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 11. University Statuses -->
        <div v-else-if="activeTab === 'university_status'" class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            v-for="item in filteredUniversityStatuses"
            :key="item.id"
            class="group flex items-center justify-between gap-3 p-3 bg-zinc-50/70 dark:bg-zinc-850 border border-zinc-200 dark:border-zinc-700/80 hover:border-blue-400 rounded-xl shadow-2xs transition-all"
          >
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-3.5 h-3.5 rounded-full shrink-0 shadow-xs" :class="resolveColor(item.color_class).dotClass" />
              <div class="text-xs font-bold text-zinc-900 dark:text-zinc-100 truncate">{{ item.name }}</div>
              <span class="ml-1.5 px-2.5 py-0.5 rounded-full text-[10.5px] font-extrabold uppercase shadow-2xs border" :class="resolveColor(item.color_class).badgeClass">
                {{ item.name }}
              </span>
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

          <!-- Color Options with Live Preview for University Status -->
          <div v-if="modalType === 'university_status'" class="space-y-2.5">
            <!-- Live Preview -->
            <div class="p-3 bg-zinc-100 dark:bg-zinc-850 rounded-xl border border-zinc-200 dark:border-zinc-700/80 flex items-center justify-between">
              <span class="text-xs font-bold text-zinc-600 dark:text-zinc-400">Live Status Preview:</span>
              <span class="inline-flex items-center px-3 py-1 rounded-full text-[11px] font-extrabold uppercase shadow-2xs border" :class="resolveColor(formColorClass).badgeClass">
                <span>{{ formName || 'STATUS PREVIEW' }}</span>
              </span>
            </div>

            <label class="block font-bold text-zinc-700 dark:text-zinc-300">Choose Status Color</label>
            <div class="grid grid-cols-4 sm:grid-cols-6 gap-2 p-2 bg-zinc-50 dark:bg-zinc-850/60 rounded-xl border border-zinc-200 dark:border-zinc-700/80 max-h-40 overflow-y-auto">
              <button
                v-for="color in STATUS_COLOR_OPTIONS"
                :key="color.key"
                type="button"
                @click="formColorClass = color.key"
                class="flex flex-col items-center gap-1 p-1.5 rounded-lg border transition-all cursor-pointer"
                :class="formColorClass === color.key ? 'border-blue-500 bg-white dark:bg-zinc-800 shadow-xs ring-2 ring-blue-500/20' : 'border-transparent hover:bg-zinc-200/50 dark:hover:bg-zinc-750'"
                :title="color.label"
              >
                <div class="w-5 h-5 rounded-full shadow-2xs flex items-center justify-center text-white" :class="color.dotClass">
                  <Check v-if="formColorClass === color.key" class="w-3 h-3 stroke-[3]" />
                </div>
                <span class="text-[9.5px] font-bold text-zinc-600 dark:text-zinc-400 truncate w-full text-center">{{ color.label }}</span>
              </button>
            </div>
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
