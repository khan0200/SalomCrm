import { ref, computed } from 'vue'
import { settingsApi, type GeneralOption } from '@/api/settings'
import {
  Building2, Building, Landmark, Store, MapPin, Globe, Briefcase, Warehouse,
  Home, Hotel, School, Compass, Navigation, Factory, Castle, Shield,
  Award, Sparkles, Star, Layers, Flag, Signpost, Pin, Laptop
} from 'lucide-vue-next'

export const OFFICE_ICON_OPTIONS = [
  { key: 'Building2', label: 'Office Tower', icon: Building2 },
  { key: 'Building', label: 'Corporate', icon: Building },
  { key: 'Landmark', label: 'Headquarters', icon: Landmark },
  { key: 'Store', label: 'Branch / Store', icon: Store },
  { key: 'MapPin', label: 'Location Pin', icon: MapPin },
  { key: 'Globe', label: 'International', icon: Globe },
  { key: 'Briefcase', label: 'Business Suite', icon: Briefcase },
  { key: 'Warehouse', label: 'Regional Hub', icon: Warehouse },
  { key: 'Home', label: 'Main Base', icon: Home },
  { key: 'Hotel', label: 'Liaison Center', icon: Hotel },
  { key: 'School', label: 'Academy / Campus', icon: School },
  { key: 'Compass', label: 'District Office', icon: Compass },
  { key: 'Navigation', label: 'Outpost', icon: Navigation },
  { key: 'Factory', label: 'Operations Unit', icon: Factory },
  { key: 'Castle', label: 'Central Center', icon: Castle },
  { key: 'Shield', label: 'Verified Office', icon: Shield },
  { key: 'Award', label: 'Premier Branch', icon: Award },
  { key: 'Sparkles', label: 'Flagship Center', icon: Sparkles },
  { key: 'Star', label: 'Priority Branch', icon: Star },
  { key: 'Layers', label: 'Multi-Floor', icon: Layers },
  { key: 'Flag', label: 'Representative', icon: Flag },
  { key: 'Signpost', label: 'City Office', icon: Signpost },
  { key: 'Pin', label: 'Station', icon: Pin },
  { key: 'Laptop', label: 'Remote / Virtual', icon: Laptop },
]

export const OFFICE_ICON_MAP: Record<string, any> = {
  Building2,
  Building,
  Landmark,
  Store,
  MapPin,
  Globe,
  Briefcase,
  Warehouse,
  Home,
  Hotel,
  School,
  Compass,
  Navigation,
  Factory,
  Castle,
  Shield,
  Award,
  Sparkles,
  Star,
  Layers,
  Flag,
  Signpost,
  Pin,
  Laptop,
}

export const resolveOfficeIcon = (iconKey?: string | null) => {
  if (iconKey && OFFICE_ICON_MAP[iconKey]) {
    return OFFICE_ICON_MAP[iconKey]
  }
  return Building2
}

// Global reactive state shared across all components
const officesRegistry = ref<GeneralOption[]>([])
const isFetched = ref(false)
const isLoading = ref(false)

export function useOffices() {
  const setOffices = (data: GeneralOption[]) => {
    officesRegistry.value = Array.isArray(data) ? data : []
    isFetched.value = true
  }

  const clearOffices = () => {
    officesRegistry.value = []
    isFetched.value = false
  }

  const fetchOffices = async (force = false) => {
    if (isFetched.value && !force) return
    try {
      isLoading.value = true
      const data = await settingsApi.getOffices()
      setOffices(Array.isArray(data) ? data : [])
      isFetched.value = true
    } catch (e) {
      console.warn('Could not fetch offices from server', e)
    } finally {
      isLoading.value = false
    }
  }

  // Map of office name (normalized) -> office object
  const officeMap = computed(() => {
    const map = new Map<string, GeneralOption>()
    officesRegistry.value.forEach(o => {
      if (o && o.name) {
        map.set(o.name.trim().toLowerCase(), o)
        map.set(o.name.trim(), o)
      }
    })
    return map
  })

  const getOfficeByName = (name?: string | null): GeneralOption | undefined => {
    if (!name) return undefined
    const clean = String(name).trim()
    return officeMap.value.get(clean) || officeMap.value.get(clean.toLowerCase())
  }

  const getOfficeIcon = (name?: string | null) => {
    const office = getOfficeByName(name)
    return resolveOfficeIcon(office?.icon)
  }

  return {
    officesRegistry,
    isFetched,
    isLoading,
    fetchOffices,
    setOffices,
    clearOffices,
    getOfficeByName,
    getOfficeIcon,
    resolveOfficeIcon,
  }
}
