<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { Eye, Edit3, Pin } from 'lucide-vue-next'
import type { VisaStudent } from '@/api/visa'

const props = defineProps<{
  isOpen: boolean
  x: number
  y: number
  student: VisaStudent | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'details', student: VisaStudent): void
  (e: 'edit', student: VisaStudent): void
  (e: 'toggle-pin', student: VisaStudent): void
}>()

const adjustedStyle = computed(() => {
  const menuWidth = 220
  const menuHeight = 140
  const winW = typeof window !== 'undefined' ? window.innerWidth : 1200
  const winH = typeof window !== 'undefined' ? window.innerHeight : 800

  let left = props.x
  let top = props.y

  if (left + menuWidth > winW - 10) {
    left = winW - menuWidth - 10
  }
  if (top + menuHeight > winH - 10) {
    top = winH - menuHeight - 10
  }

  return {
    left: `${Math.max(10, left)}px`,
    top: `${Math.max(10, top)}px`
  }
})

function onDocClick(e: MouseEvent) {
  if (!props.isOpen) return
  const target = e.target as HTMLElement
  if (!target.closest('[data-context-menu]')) {
    emit('close')
  }
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.isOpen) {
    emit('close')
  }
}

function onScroll() {
  if (props.isOpen) emit('close')
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
  document.addEventListener('contextmenu', onDocClick)
  document.addEventListener('keydown', onKeyDown)
  window.addEventListener('scroll', onScroll, { passive: true })
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('contextmenu', onDocClick)
  document.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-100 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-75 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen && student"
        data-context-menu
        class="visacheck-page fixed z-[100] w-56 rounded-lg bg-white/95 dark:bg-[#16181b]/95 backdrop-blur-xl border border-zinc-200/80 dark:border-zinc-700/80 shadow-2xl p-1.5 text-xs text-zinc-800 dark:text-zinc-200 select-none"
        :style="adjustedStyle"
        @contextmenu.prevent
      >
        <div class="space-y-0.5">
          <!-- 1. Batafsil ko'rish (Details) -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800/80 font-semibold transition-colors cursor-pointer"
            @click="emit('details', student); emit('close')"
          >
            <div class="flex items-center gap-2.5">
              <Eye class="size-4 text-amber-500 shrink-0" />
              <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-100">Batafsil ko'rish</span>
            </div>
            <span class="text-[11px] text-zinc-400 font-medium">Details</span>
          </button>

          <!-- 2. Tahrirlash (Edit) -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800/80 font-semibold transition-colors cursor-pointer"
            @click="emit('edit', student); emit('close')"
          >
            <div class="flex items-center gap-2.5">
              <Edit3 class="size-4 text-emerald-500 shrink-0" />
              <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-100">Tahrirlash</span>
            </div>
            <span class="text-[11px] text-zinc-400 font-medium">Edit</span>
          </button>

          <!-- 3. Yuqoriga pin qilish / Pinni bekor qilish -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-3 py-2 rounded-md hover:bg-zinc-100 dark:hover:bg-zinc-800/80 font-semibold transition-colors cursor-pointer"
            @click="emit('toggle-pin', student); emit('close')"
          >
            <div class="flex items-center gap-2.5">
              <Pin
                class="size-4 shrink-0 transition-colors"
                :class="student.pinned ? 'text-amber-500 fill-amber-500' : 'text-zinc-400 dark:text-zinc-400'"
              />
              <span class="text-xs font-semibold text-zinc-800 dark:text-zinc-100">
                {{ student.pinned ? 'Pinni bekor qilish' : 'Yuqoriga pin qilish' }}
              </span>
            </div>
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
