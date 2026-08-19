<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { X, Maximize2, Minimize2 } from 'lucide-vue-next'

const props = withDefaults(defineProps<{
  isOpen: boolean
  title?: string
  subtitle?: string
  width?: string
  allowFullscreen?: boolean
  isFullscreen?: boolean
}>(), {
  width: 'max-w-3xl',
  allowFullscreen: false,
  isFullscreen: false
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'toggle-fullscreen'): void
}>()

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.isOpen) {
    emit('close')
  }
}

onMounted(() => window.addEventListener('keydown', handleKeyDown))
onUnmounted(() => window.removeEventListener('keydown', handleKeyDown))
</script>

<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="fixed inset-0 z-50 overflow-hidden flex justify-end"
    >
      <!-- Backdrop -->
      <transition
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition duration-200 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          class="fixed inset-0 bg-black/40 backdrop-blur-xs transition-opacity"
          @click="emit('close')"
        />
      </transition>

      <!-- Panel -->
      <transition
        enter-active-class="transform transition duration-300 ease-[cubic-bezier(0.16,1,0.3,1)]"
        enter-from-class="translate-x-full"
        enter-to-class="translate-x-0"
        leave-active-class="transform transition duration-200 ease-[cubic-bezier(0.16,1,0.3,1)]"
        leave-from-class="translate-x-0"
        leave-to-class="translate-x-full"
      >
        <div
          class="relative w-full h-full bg-white dark:bg-zinc-900 border-l border-zinc-200 dark:border-zinc-800 shadow-2xl z-10 flex flex-col overflow-hidden"
          :class="isFullscreen ? 'max-w-none' : width"
        >
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 bg-zinc-50/75 dark:bg-zinc-900/75 shrink-0">
            <slot name="header">
              <div>
                <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100">{{ title }}</h3>
                <p v-if="subtitle" class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5">{{ subtitle }}</p>
              </div>
            </slot>
            <div class="flex items-center gap-1">
              <button
                v-if="allowFullscreen"
                @click="emit('toggle-fullscreen')"
                class="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer"
                :title="isFullscreen ? 'Restore' : 'Maximize'"
              >
                <component :is="isFullscreen ? Minimize2 : Maximize2" class="w-4 h-4" />
              </button>
              <button
                @click="emit('close')"
                class="rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-100 hover:text-zinc-700 dark:hover:bg-zinc-800 dark:hover:text-zinc-200 transition-colors cursor-pointer"
                title="Close"
              >
                <X class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto p-6">
            <slot />
          </div>

          <!-- Footer -->
          <div v-if="$slots.footer" class="px-6 py-3.5 border-t border-zinc-200 dark:border-zinc-800 bg-zinc-50/75 dark:bg-zinc-900/75 flex items-center justify-end gap-2.5 shrink-0">
            <slot name="footer" />
          </div>
        </div>
      </transition>
    </div>
  </Teleport>
</template>
