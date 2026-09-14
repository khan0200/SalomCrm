import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { UserProfile, Tenant } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const getInitialUser = (): UserProfile | null => {
    try {
      const saved = localStorage.getItem('user_profile')
      return saved ? JSON.parse(saved) : null
    } catch {
      return null
    }
  }

  const user = ref<UserProfile | null>(getInitialUser())
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const activeTenantId = ref<string | null>(localStorage.getItem('active_tenant_id'))

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isSuperAdmin = computed(() => !!user.value?.is_superuser || user.value?.role === 'SUPER_ADMIN')
  const isHeadManager = computed(() => isSuperAdmin.value || user.value?.role === 'HEAD_MANAGER')
  const isManager = computed(() => isHeadManager.value || user.value?.role === 'MANAGER')
  const isStaff = computed(() => isAuthenticated.value && !isManager.value)

  // Role-based permissions
  const canEdit = computed(() => isManager.value)
  const canDelete = computed(() => isManager.value)
  const canAccessPayments = computed(() => isManager.value)
  const canAccessSettings = computed(() => isManager.value)

  const currentTenant = computed<Tenant | null>(() => {
    if (!user.value) return null
    if (user.value.tenant && typeof user.value.tenant === 'object') {
      return user.value.tenant as Tenant
    }
    const rawUser = user.value as any
    const tName = rawUser.tenant_name || (typeof rawUser.tenant === 'string' ? rawUser.tenant : null)
    if (tName) {
      return {
        id: String(rawUser.tenant || tName),
        name: rawUser.tenant_name || String(rawUser.tenant || tName),
        slug: String(rawUser.tenant || tName),
        is_active: true,
        created_at: ''
      }
    }
    return null
  })

  const login = async (credentials: { email: string; password: string }) => {
    const data = await authApi.login(credentials)
    token.value = data.access
    user.value = data.user

    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('user_profile', JSON.stringify(data.user))

    if (data.user.tenant?.id) {
      activeTenantId.value = data.user.tenant.id
      localStorage.setItem('active_tenant_id', data.user.tenant.id)
    }
  }

  const loginWithTelegram = async (telegramData: any) => {
    const data = await authApi.loginWithTelegram(telegramData)
    token.value = data.access
    user.value = data.user

    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    localStorage.setItem('user_profile', JSON.stringify(data.user))

    if (data.user.tenant?.id) {
      activeTenantId.value = data.user.tenant.id
      localStorage.setItem('active_tenant_id', data.user.tenant.id)
    }
  }

  const logout = () => {
    user.value = null
    token.value = null
    activeTenantId.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_profile')
    localStorage.removeItem('active_tenant_id')
    window.location.href = '/login'
  }

  const setActiveTenant = (tenantId: string | null) => {
    activeTenantId.value = tenantId
    if (tenantId) {
      localStorage.setItem('active_tenant_id', tenantId)
    } else {
      localStorage.removeItem('active_tenant_id')
    }
    window.location.reload()
  }

  const fetchUser = async () => {
    if (!token.value) return
    try {
      const data = await authApi.getMe()
      user.value = data
      localStorage.setItem('user_profile', JSON.stringify(data))
      const tenantId = (data.tenant as any)?.id || (typeof data.tenant === 'string' ? data.tenant : null)
      if (tenantId && !activeTenantId.value) {
        activeTenantId.value = tenantId
        localStorage.setItem('active_tenant_id', tenantId)
      }
    } catch (err) {
      logout()
    }
  }

  return {
    user,
    token,
    activeTenantId,
    isAuthenticated,
    isSuperAdmin,
    isHeadManager,
    isManager,
    isStaff,
    canEdit,
    canDelete,
    canAccessPayments,
    canAccessSettings,
    currentTenant,
    login,
    loginWithTelegram,
    logout,
    setActiveTenant,
    fetchUser,
  }
})
