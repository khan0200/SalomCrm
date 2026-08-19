import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ToastMessage {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title?: string
  message: string
  duration?: number
}

export const useUiStore = defineStore('ui', () => {
  const getInitialTheme = (): boolean => {
    try {
      const saved = localStorage.getItem('theme')
      if (saved) return saved === 'dark'
      return window.matchMedia('(prefers-color-scheme: dark)').matches
    } catch {
      return false
    }
  }

  // Theme state
  const isDark = ref<boolean>(getInitialTheme())

  // Apply theme class to document
  if (isDark.value) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }

  const toggleTheme = () => {
    isDark.value = !isDark.value
    if (isDark.value) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('theme', 'light')
    }
  }

  const isSidebarCollapsed = ref<boolean>(false)
  const toggleSidebar = () => {
    isSidebarCollapsed.value = !isSidebarCollapsed.value
  }

  // Toasts
  const toasts = ref<ToastMessage[]>([])

  const addToast = (toast: Omit<ToastMessage, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9)
    const newToast: ToastMessage = { ...toast, id }
    toasts.value.push(newToast)

    const duration = toast.duration ?? 4000
    if (duration > 0) {
      setTimeout(() => {
        removeToast(id)
      }, duration)
    }
  }

  const removeToast = (id: string) => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }

  return {
    isDark,
    toggleTheme,
    isSidebarCollapsed,
    toggleSidebar,
    toasts,
    addToast,
    removeToast,
  }
})
