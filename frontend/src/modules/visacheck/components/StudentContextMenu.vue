<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import {
  RefreshCw, Eye, Edit3, Pin, Flag, FileDown,
  Copy, Trash2, Check, ExternalLink, Calendar, User, Hash
} from 'lucide-vue-next'
import type { VisaStudent } from '@/api/visa'

const props = defineProps<{
  isOpen: boolean
  x: number
  y: number
  student: VisaStudent | null
  isChecking?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'check', student: VisaStudent): void
  (e: 'details', student: VisaStudent): void
  (e: 'edit', student: VisaStudent): void
  (e: 'toggle-pin', student: VisaStudent): void
  (e: 'toggle-flag', student: VisaStudent): void
  (e: 'download-pdf', student: VisaStudent): void
  (e: 'delete', student: VisaStudent): void
}>()

const copiedField = ref<string | null>(null)

async function copyText(text: string | undefined | null, fieldKey: string) {
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copiedField.value = fieldKey
    setTimeout(() => {
      if (copiedField.value === fieldKey) copiedField.value = null
    }, 1500)
  } catch { /* ignore */ }
}

const isPdfEligible = computed(() => {
  if (!props.student) return false
  const s = (props.student.status || '').toUpperCase()
  return s.includes('APPROV') || s.includes('VISA USED')
})

const adjustedStyle = computed(() => {
  const menuWidth = 240
  const menuHeight = 360
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
        class="fixed z-[100] w-60 rounded-2xl bg-white/95 dark:bg-zinc-900/95 backdrop-blur-xl border border-zinc-200/90 dark:border-zinc-700/80 shadow-2xl p-1.5 text-xs text-zinc-700 dark:text-zinc-200 select-none animate-in fade-in zoom-in-95 duration-100"
        :style="adjustedStyle"
        @contextmenu.prevent
      >
        <!-- Header: Student info -->
        <div class="px-3 py-2 border-b border-zinc-100 dark:border-zinc-800 mb-1">
          <div class="font-bold text-zinc-900 dark:text-white truncate">
            {{ student.full_name }}
          </div>
          <div class="text-[11px] font-mono text-zinc-400 mt-0.5 flex items-center gap-1.5">
            <span>{{ student.passport }}</span>
            <span v-if="student.student_id" class="text-blue-500">#{{ student.student_id }}</span>
          </div>
        </div>

        <!-- Action Items -->
        <div class="space-y-0.5">
          <!-- Check Visa -->
          <button
            type="button"
            :disabled="isChecking"
            class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-blue-50 dark:hover:bg-blue-950/40 hover:text-blue-600 dark:hover:text-blue-400 font-semibold transition-colors cursor-pointer disabled:opacity-50"
            @click="emit('check', student); emit('close')"
          >
            <div class="flex items-center gap-2.5">
              <RefreshCw class="size-4 text-blue-500" :class="{ 'animate-spin': isChecking }" />
              <span>Viza tekshirish</span>
            </div>
            <span class="text-[10px] text-zinc-400 font-mono">Check</span>
          </button>

          <!-- View Details -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 font-semibold transition-colors cursor-pointer"
            @click="emit('details', student); emit('close')"
          >
            <div class="flex items-center gap-2.5">
              <Eye class="size-4 text-amber-500" />
              <span>Batafsil ko'rish</span>
            </div>
            <span class="text-[10px] text-zinc-400 font-mono">Details</span>
          </button>

          <!-- Edit Student -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 font-semibold transition-colors cursor-pointer"
            @click="emit('edit', student); emit('close')"
          >
            <div class="flex items-center gap-2.5">
              <Edit3 class="size-4 text-emerald-500" />
              <span>Tahrirlash</span>
            </div>
            <span class="text-[10px] text-zinc-400 font-mono">Edit</span>
          </button>

          <!-- Toggle Pin -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 font-semibold transition-colors cursor-pointer"
            @click="emit('toggle-pin', student); emit('close')"
          >
            <div class="flex items-center gap-2.5">
              <Pin
                class="size-4"
                :class="student.pinned ? 'text-amber-500 fill-amber-500' : 'text-zinc-400'"
              />
              <span>{{ student.pinned ? 'Pinni bekor qilish' : 'Yuqoriga pin qilish' }}</span>
            </div>
          </button>

          <!-- Toggle Flag -->
          <button
            type="button"
            class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-zinc-100 dark:hover:bg-zinc-800 font-semibold transition-colors cursor-pointer"
            @click="emit('toggle-flag', student); emit('close')"
          >
            <div class="flex items-center gap-2.5">
              <Flag
                class="size-4"
                :class="student.flag ? 'text-rose-500 fill-rose-500' : 'text-zinc-400'"
              />
              <span>{{ student.flag ? 'Bayroqchani olish' : 'Bayroqcha bilan belgilash' }}</span>
            </div>
          </button>

          <!-- Download PDF (if eligible) -->
          <button
            v-if="isPdfEligible"
            type="button"
            class="w-full flex items-center justify-between px-3 py-2 rounded-xl hover:bg-emerald-50 dark:hover:bg-emerald-950/40 hover:text-emerald-600 dark:hover:text-emerald-400 font-semibold transition-colors cursor-pointer"
            @click="emit('download-pdf', student); emit('close')"
          >
            <div class="flex items-center gap-2.5">
              <FileDown class="size-4 text-emerald-500" />
              <span>Viza PDF yuklab olish</span>
            </div>
          </button>
        </div>

        <!-- Copy Submenu Divider -->
        <div class="my-1 border-t border-zinc-100 dark:border-zinc-800" />

        <!-- Quick Copy Actions -->
        <div class="space-y-0.5">
          <button
            type="button"
            class="w-full flex items-center justify-between px-3 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-[11px]"
            @click.stop="copyText(student.passport, 'passport')"
          >
            <span class="text-zinc-500 dark:text-zinc-400">Pasport nusxalash</span>
            <Check v-if="copiedField === 'passport'" class="size-3.5 text-emerald-500" />
            <span v-else class="font-mono text-zinc-800 dark:text-zinc-200">{{ student.passport }}</span>
          </button>

          <button
            type="button"
            class="w-full flex items-center justify-between px-3 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-[11px]"
            @click.stop="copyText(student.full_name, 'name')"
          >
            <span class="text-zinc-500 dark:text-zinc-400">Ismni nusxalash</span>
            <Check v-if="copiedField === 'name'" class="size-3.5 text-emerald-500" />
            <Copy v-else class="size-3 text-zinc-400" />
          </button>

          <button
            v-if="student.birthday"
            type="button"
            class="w-full flex items-center justify-between px-3 py-1.5 rounded-lg hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer text-[11px]"
            @click.stop="copyText(student.birthday, 'birthday')"
          >
            <span class="text-zinc-500 dark:text-zinc-400">Tug'ilgan sana</span>
            <Check v-if="copiedField === 'birthday'" class="size-3.5 text-emerald-500" />
            <span v-else class="font-mono text-zinc-800 dark:text-zinc-200">{{ student.birthday }}</span>
          </button>
        </div>

        <!-- Delete Divider -->
        <div class="my-1 border-t border-zinc-100 dark:border-zinc-800" />

        <!-- Delete Action -->
        <button
          type="button"
          class="w-full flex items-center justify-between px-3 py-2 rounded-xl text-rose-600 dark:text-rose-400 hover:bg-rose-50 dark:hover:bg-rose-950/40 font-semibold transition-colors cursor-pointer"
          @click="emit('delete', student); emit('close')"
        >
          <div class="flex items-center gap-2.5">
            <Trash2 class="size-4" />
            <span>O'chirish</span>
          </div>
          <span class="text-[10px] opacity-70 font-mono">Delete</span>
        </button>
      </div>
    </Transition>
  </Teleport>
</template>
