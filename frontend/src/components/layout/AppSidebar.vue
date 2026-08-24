<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import {
  Users,
  CreditCard,
  ClipboardList,
  FileText,
  ShieldCheck,
  Settings,
  LogOut,
  Sun,
  Moon
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUiStore()

interface NavItem {
  name: string
  path: string
  icon: any
  isExternal?: boolean
  target?: string
}

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    { name: 'STUDENTS', path: '/students', icon: Users },
    { name: 'STATUS', path: '/status', icon: ClipboardList },
    { name: 'DOCUMENTS', path: '/documents', icon: FileText },
  ]

  if (authStore.canAccessPayments) {
    items.push({ name: 'PAYMENTS', path: '/payments', icon: CreditCard })
  }

  items.push({ name: 'VISACHECK', path: '/visacheck', icon: ShieldCheck })

  if (authStore.canAccessSettings) {
    items.push({ name: 'SETTINGS', path: '/settings', icon: Settings })
  }

  if (authStore.isSuperAdmin) {
    items.push({ name: 'TENANTS', path: '/tenants', icon: Settings })
  }

  return items
})

const isActive = (itemPath: string) => {
  if (itemPath.startsWith('http')) return false

  // If item has query parameters (e.g. /students?tab=documents)
  if (itemPath.includes('?')) {
    const [pathPart, queryPart] = itemPath.split('?')
    if (route.path !== pathPart) return false
    const searchParams = new URLSearchParams(queryPart)
    for (const [key, val] of searchParams.entries()) {
      if (route.query[key] !== val) return false
    }
    return true
  }

  // Exact path match
  if (route.path === itemPath) {
    // If route has specific query params targeted by another item, exclude base item
    if (itemPath === '/students' && route.query.tab === 'documents') {
      return false
    }
    return true
  }

  return route.path.startsWith(itemPath + '/')
}

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <aside
    class="relative flex flex-col h-full w-[76px] bg-white dark:bg-[#111315] border-r border-zinc-200 dark:border-zinc-800/80 overflow-hidden shrink-0 z-20 select-none"
    aria-label="Main navigation"
  >
    <!-- Logo & Brand Header -->
    <div class="flex items-center justify-center h-14 shrink-0 border-b border-zinc-100 dark:border-zinc-800/80">
      <router-link to="/students" class="flex items-center justify-center group" title="Salom CRM">
        <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-blue-500/25 group-hover:scale-105 transition-transform">
          <svg class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
          </svg>
        </div>
      </router-link>
    </div>

    <!-- Navigation Items -->
    <nav class="flex-1 overflow-y-auto overflow-x-hidden py-3 px-1 space-y-1.5 scrollbar-none">
      <template v-for="item in navItems" :key="item.name">
        <!-- External link -->
        <a
          v-if="item.isExternal"
          :href="item.path"
          :target="item.target"
          rel="noopener noreferrer"
          class="group flex flex-col items-center justify-center w-full py-1 px-1 relative focus:outline-none cursor-pointer"
        >
          <div class="w-[52px] h-[36px] flex items-center justify-center rounded-xl transition-all duration-300 text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-white">
            <component :is="item.icon" class="h-4.5 w-4.5" :stroke-width="2" />
          </div>
          <span class="mt-1 text-[8px] font-bold tracking-wider text-center truncate max-w-[72px] uppercase text-zinc-500 group-hover:text-zinc-900 dark:text-zinc-400 dark:group-hover:text-white transition-colors">
            {{ item.name }}
          </span>
        </a>

        <!-- Internal Route Link -->
        <router-link
          v-else
          :to="item.path"
          class="group flex flex-col items-center justify-center w-full py-1 px-1 relative focus:outline-none cursor-pointer"
        >
          <div
            class="w-[52px] h-[36px] flex items-center justify-center rounded-xl transition-all duration-300 relative"
            :class="[
              isActive(item.path)
                ? 'bg-gradient-to-tr from-blue-500 to-indigo-600 text-white shadow-md shadow-blue-500/25 scale-[1.05]'
                : 'text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-zinc-800 dark:hover:text-white'
            ]"
          >
            <component
              :is="item.icon"
              class="h-4.5 w-4.5"
              :stroke-width="isActive(item.path) ? 2.5 : 2"
            />
          </div>
          <span
            class="mt-1 text-[8px] font-bold tracking-wider text-center truncate max-w-[72px] transition-all duration-300 uppercase"
            :class="[
              isActive(item.path)
                ? 'text-blue-600 dark:text-blue-400 font-extrabold scale-[1.02]'
                : 'text-zinc-500 group-hover:text-zinc-900 dark:text-zinc-400 dark:group-hover:text-white'
            ]"
          >
            {{ item.name }}
          </span>
        </router-link>
      </template>
    </nav>

    <!-- Footer Controls -->
    <div class="shrink-0 border-t border-zinc-100 dark:border-zinc-800/80 p-2 flex flex-col items-center gap-3 pb-3">
      <!-- Theme toggle -->
      <button
        @click="uiStore.toggleTheme"
        class="w-8 h-8 flex items-center justify-center rounded-xl text-zinc-500 hover:text-zinc-900 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:text-white dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        :title="uiStore.isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
      >
        <Sun v-if="uiStore.isDark" class="w-4 h-4 text-amber-400" />
        <Moon v-else class="w-4 h-4 text-zinc-600" />
      </button>

      <!-- User Avatar -->
      <div
        class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white select-none shadow-xs hover:ring-2 hover:ring-blue-500/40 transition-all cursor-default"
        style="background: linear-gradient(135deg, #3b7ff5, #6366f1)"
        :title="`${authStore.user?.full_name || 'User'} (${authStore.user?.role || ''})`"
      >
        {{ authStore.user?.full_name ? authStore.user.full_name.slice(0, 2).toUpperCase() : 'UA' }}
      </div>

      <!-- Logout -->
      <button
        @click="handleLogout"
        class="w-7 h-7 flex items-center justify-center rounded-lg text-zinc-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors cursor-pointer"
        title="Sign Out"
      >
        <LogOut class="w-3.5 h-3.5" />
      </button>
    </div>
  </aside>
</template>
