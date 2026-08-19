<script setup lang="ts">
import { useUiStore } from '@/stores/ui'
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-vue-next'

const uiStore = useUiStore()

const getIcon = (type: string) => {
  switch (type) {
    case 'success': return CheckCircle2
    case 'error': return AlertCircle
    case 'warning': return AlertTriangle
    default: return Info
  }
}

const getStyles = (type: string) => {
  switch (type) {
    case 'success':
      return 'bg-emerald-50 border-emerald-200 text-emerald-900 dark:bg-emerald-950/80 dark:border-emerald-800 dark:text-emerald-200'
    case 'error':
      return 'bg-rose-50 border-rose-200 text-rose-900 dark:bg-rose-950/80 dark:border-rose-800 dark:text-rose-200'
    case 'warning':
      return 'bg-amber-50 border-amber-200 text-amber-900 dark:bg-amber-950/80 dark:border-amber-800 dark:text-amber-200'
    default:
      return 'bg-blue-50 border-blue-200 text-blue-900 dark:bg-blue-950/80 dark:border-blue-800 dark:text-blue-200'
  }
}
</script>

<template>
  <div class="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-sm pointer-events-none">
    <transition-group
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform translate-y-2 opacity-0"
      enter-to-class="transform translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform opacity-100"
      leave-to-class="transform opacity-0"
    >
      <div
        v-for="toast in uiStore.toasts"
        :key="toast.id"
        :class="[
          'pointer-events-auto flex items-start gap-3 p-3.5 rounded-xl border shadow-lg backdrop-blur-md transition-all text-xs',
          getStyles(toast.type)
        ]"
      >
        <component :is="getIcon(toast.type)" class="w-4 h-4 mt-0.5 shrink-0" />
        <div class="flex-1 min-w-0">
          <h4 v-if="toast.title" class="font-bold mb-0.5">{{ toast.title }}</h4>
          <p class="leading-relaxed opacity-90">{{ toast.message }}</p>
        </div>
        <button
          @click="uiStore.removeToast(toast.id)"
          class="shrink-0 p-1 hover:opacity-75 transition-opacity cursor-pointer"
        >
          <X class="w-3.5 h-3.5" />
        </button>
      </div>
    </transition-group>
  </div>
</template>
