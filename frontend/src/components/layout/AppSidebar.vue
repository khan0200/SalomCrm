<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import {
  Users, CreditCard, CheckSquare, ShieldAlert,
  ChevronLeft, ChevronRight, GraduationCap
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const uiStore = useUiStore()

const navigation = computed(() => {
  const items = [
    { name: 'Students', path: '/students', icon: Users },
    { name: 'Payments', path: '/payments', icon: CreditCard },
    { name: 'Status', path: '/status', icon: CheckSquare },
  ]
  if (authStore.isSuperAdmin) {
    items.push({ name: 'Tenants', path: '/tenants', icon: ShieldAlert })
  }
  return items
})

const isActive = (path: string) => {
  return route.path === path || route.path.startsWith(path + '/')
}
</script>

<template>
  <aside
    class="flex flex-col bg-white dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 shrink-0 transition-all duration-200 z-20 select-none"
    :class="uiStore.isSidebarCollapsed ? 'w-16' : 'w-60'"
  >
    <!-- Logo & Brand Header -->
    <div class="h-16 flex items-center justify-between px-4 border-b border-zinc-200 dark:border-zinc-800">
      <div class="flex items-center gap-2.5 min-w-0" v-if="!uiStore.isSidebarCollapsed">
        <div class="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center text-white shadow-sm shrink-0">
          <GraduationCap class="w-5 h-5" />
        </div>
        <div class="min-w-0">
          <h1 class="font-black text-sm text-zinc-900 dark:text-zinc-100 tracking-tight leading-none">Salom CRM</h1>
          <span class="text-[10px] font-bold text-brand-500 uppercase tracking-widest">Version 3.0</span>
        </div>
      </div>
      <div v-else class="w-8 h-8 mx-auto rounded-lg bg-brand-500 flex items-center justify-center text-white shadow-sm">
        <GraduationCap class="w-5 h-5" />
      </div>

      <button
        @click="uiStore.toggleSidebar"
        class="p-1.5 rounded-lg text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer"
        :class="uiStore.isSidebarCollapsed ? 'hidden' : ''"
      >
        <ChevronLeft class="w-4 h-4" />
      </button>
    </div>

    <!-- Navigation Links -->
    <nav class="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
      <router-link
        v-for="item in navigation"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all group cursor-pointer"
        :class="[
          isActive(item.path)
            ? 'bg-brand-500 text-white shadow-sm shadow-brand-500/30 font-bold'
            : 'text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 dark:text-zinc-400 dark:hover:text-zinc-100 dark:hover:bg-zinc-800/60'
        ]"
        :title="uiStore.isSidebarCollapsed ? item.name : undefined"
      >
        <component
          :is="item.icon"
          class="w-4.5 h-4.5 shrink-0"
          :class="isActive(item.path) ? 'text-white' : 'text-zinc-400 group-hover:text-zinc-600 dark:group-hover:text-zinc-300'"
        />
        <span v-if="!uiStore.isSidebarCollapsed" class="truncate">{{ item.name }}</span>
      </router-link>
    </nav>

    <!-- Sidebar Footer with Collapse Expand for small mode -->
    <div v-if="uiStore.isSidebarCollapsed" class="p-3 border-t border-zinc-200 dark:border-zinc-800 flex justify-center">
      <button
        @click="uiStore.toggleSidebar"
        class="p-2 rounded-xl text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer"
        title="Expand Sidebar"
      >
        <ChevronRight class="w-4 h-4" />
      </button>
    </div>
  </aside>
</template>
