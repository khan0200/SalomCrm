<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import {
  AlertTriangle, ClipboardCheck, X, ArrowUpRight, ArrowRight,
  WifiOff, Sparkles, AlertCircle, CheckCircle2, XCircle, FileCheck,
  RefreshCw, RotateCcw, Clock, ShieldCheck
} from 'lucide-vue-next'

export interface SessionChange {
  fullName: string
  passport: string
  oldStatus: string
  newStatus: string
}

export interface SessionNoAnswer {
  fullName: string
  passport: string
  reason?: string
}

export interface SessionSummary {
  total: number
  changed: number
  unchanged: number
  noAnswer: number
}

const props = defineProps<{
  isOpen: boolean
  changes: SessionChange[]
  noAnswers: SessionNoAnswer[]
  summary: SessionSummary
  isRetrying?: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'retry-no-answers'): void
}>()

const activeTab = ref<'changes' | 'no-answers'>('changes')

watch(() => props.isOpen, (open) => {
  if (open) {
    if (props.changes.length > 0) activeTab.value = 'changes'
    else if (props.noAnswers.length > 0) activeTab.value = 'no-answers'
    else activeTab.value = 'changes'
  }
})

function getStatusBadgeType(statusValue: string): 'success' | 'error' | 'warning' | 'primary' | 'neutral' {
  const s = (statusValue || '').toLowerCase().trim()
  if (s.includes('approved') || s.includes('visa used') || s.includes('issued') || s.includes('tasdiqlangan')) return 'success'
  if (s.includes('cancel') || s.includes('reject') || s.includes('rad etil') || s.includes('bekor')) return 'error'
  if (s.includes('supplement submitted')) return 'primary'
  if (s.includes('supplement') || s.includes('received') || s.includes('qabul')) return 'warning'
  if (s.includes('pending') || s.includes('unknown') || s.includes('error')) return 'neutral'
  return 'primary'
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="fixed inset-0 z-[80] flex items-center justify-center p-4 sm:p-6 bg-black/60 backdrop-blur-sm select-none"
        @mousedown.self="emit('close')"
      >
        <div
          class="w-full max-w-2xl bg-white dark:bg-[#121824] border border-zinc-200 dark:border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
        >
          <!-- Header -->
          <div class="p-5 sm:p-6 pb-4 border-b border-zinc-100 dark:border-white/10 flex items-start justify-between gap-4">
            <div class="flex items-start gap-3.5">
              <div
                class="flex items-center justify-center size-12 rounded-2xl shrink-0 shadow-inner"
                :class="noAnswers.length > 0 ? 'bg-amber-500/10 text-amber-500' : 'bg-emerald-500/10 text-emerald-500'"
              >
                <AlertTriangle v-if="noAnswers.length > 0" class="size-6" />
                <ClipboardCheck v-else class="size-6" />
              </div>
              <div class="space-y-1">
                <h3 class="text-lg font-bold text-zinc-900 dark:text-white leading-tight">
                  Viza tekshiruvi hisoboti
                </h3>
                <p class="text-xs text-zinc-500 dark:text-zinc-400">
                  Jami <span class="font-bold text-zinc-900 dark:text-white">{{ summary.total }} ta</span> talaba tekshirildi (1 marta avtomatik qayta urinish bilan).
                </p>
              </div>
            </div>

            <button
              type="button"
              class="p-2 rounded-xl text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-white/10 transition-colors cursor-pointer"
              aria-label="Yopish"
              @click="emit('close')"
            >
              <X class="size-5" />
            </button>
          </div>

          <!-- Body -->
          <div class="p-5 sm:p-6 space-y-5 overflow-y-auto flex-1">
            <!-- 4 Summary KPI Metric Cards -->
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              <!-- Total Checked -->
              <div class="p-3.5 rounded-2xl border border-zinc-200 dark:border-white/10 bg-zinc-50 dark:bg-white/[0.02] flex flex-col justify-between">
                <span class="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Jami</span>
                <span class="text-2xl font-black text-zinc-900 dark:text-white mt-1">{{ summary.total }}</span>
              </div>

              <!-- Status Changed -->
              <div class="p-3.5 rounded-2xl border border-emerald-500/20 bg-emerald-500/5 flex flex-col justify-between">
                <span class="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider">O'zgargan</span>
                <div class="flex items-center gap-1.5 mt-1">
                  <span class="text-2xl font-black text-emerald-600 dark:text-emerald-400">{{ changes.length }}</span>
                  <ArrowUpRight v-if="changes.length > 0" class="size-4 text-emerald-500" />
                </div>
              </div>

              <!-- Unchanged -->
              <div class="p-3.5 rounded-2xl border border-zinc-200 dark:border-white/10 bg-zinc-50 dark:bg-white/[0.02] flex flex-col justify-between">
                <span class="text-[11px] font-semibold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">O'zgarmagan</span>
                <span class="text-2xl font-black text-zinc-700 dark:text-zinc-300 mt-1">{{ summary.unchanged }}</span>
              </div>

              <!-- No Answer / Timeout -->
              <div
                class="p-3.5 rounded-2xl border flex flex-col justify-between"
                :class="noAnswers.length > 0 ? 'border-rose-500/30 bg-rose-500/5' : 'border-zinc-200 dark:border-white/10 bg-zinc-50 dark:bg-white/[0.02]'"
              >
                <span
                  class="text-[11px] font-semibold uppercase tracking-wider"
                  :class="noAnswers.length > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-zinc-500 dark:text-zinc-400'"
                >
                  Javobsiz
                </span>
                <div class="flex items-center gap-1.5 mt-1">
                  <span
                    class="text-2xl font-black"
                    :class="noAnswers.length > 0 ? 'text-rose-600 dark:text-rose-400' : 'text-zinc-700 dark:text-zinc-300'"
                  >
                    {{ noAnswers.length }}
                  </span>
                  <WifiOff v-if="noAnswers.length > 0" class="size-4 text-rose-500" />
                </div>
              </div>
            </div>

            <!-- Tab Controls -->
            <div class="flex items-center gap-2 border-b border-zinc-200 dark:border-white/10 pb-2">
              <button
                type="button"
                class="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer"
                :class="activeTab === 'changes'
                  ? 'bg-emerald-600 text-white shadow-xs'
                  : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-white/5'"
                @click="activeTab = 'changes'"
              >
                <Sparkles class="size-3.5" />
                <span>Viza o'zgarishlari</span>
                <span
                  class="px-1.5 py-0.5 rounded-full text-[10px] font-bold"
                  :class="activeTab === 'changes' ? 'bg-white/20 text-white' : 'bg-zinc-200 dark:bg-white/10 text-zinc-700 dark:text-zinc-300'"
                >
                  {{ changes.length }}
                </span>
              </button>

              <button
                type="button"
                class="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer"
                :class="activeTab === 'no-answers'
                  ? 'bg-rose-600 text-white shadow-xs'
                  : 'text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-white/5'"
                @click="activeTab = 'no-answers'"
              >
                <AlertCircle class="size-3.5" />
                <span>Javob olinmaganlar</span>
                <span
                  class="px-1.5 py-0.5 rounded-full text-[10px] font-bold"
                  :class="activeTab === 'no-answers' ? 'bg-white/20 text-white' : 'bg-zinc-200 dark:bg-white/10 text-zinc-700 dark:text-zinc-300'"
                >
                  {{ noAnswers.length }}
                </span>
              </button>
            </div>

            <!-- TAB 1: Status Changes -->
            <div
              v-if="activeTab === 'changes'"
              class="space-y-2.5 max-h-[46vh] overflow-y-auto pr-1"
            >
              <div
                v-if="changes.length === 0"
                class="py-10 text-center space-y-2 border border-dashed border-zinc-200 dark:border-white/10 rounded-2xl bg-zinc-50/50 dark:bg-white/[0.01]"
              >
                <CheckCircle2 class="size-8 text-zinc-400 mx-auto" />
                <p class="text-xs text-zinc-500 dark:text-zinc-400 font-medium">
                  Ushbu tekshiruvda viza statuslarida yangi o'zgarish qayd etilmadi.
                </p>
              </div>

              <div
                v-for="change in changes"
                :key="change.passport || change.fullName"
                class="group relative overflow-hidden rounded-2xl border border-zinc-200 dark:border-white/10 bg-zinc-50/50 dark:bg-white/[0.02] p-3.5 transition-all flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-l-4"
                :class="{
                  'border-l-emerald-500': getStatusBadgeType(change.newStatus) === 'success',
                  'border-l-rose-500': getStatusBadgeType(change.newStatus) === 'error',
                  'border-l-blue-500': getStatusBadgeType(change.newStatus) === 'primary',
                  'border-l-amber-500': getStatusBadgeType(change.newStatus) === 'warning'
                }"
              >
                <!-- Left: Name & Passport -->
                <div class="space-y-0.5">
                  <div class="flex items-center gap-2">
                    <CheckCircle2 v-if="getStatusBadgeType(change.newStatus) === 'success'" class="size-4 text-emerald-500 shrink-0" />
                    <XCircle v-else-if="getStatusBadgeType(change.newStatus) === 'error'" class="size-4 text-rose-500 shrink-0" />
                    <AlertCircle v-else-if="getStatusBadgeType(change.newStatus) === 'warning'" class="size-4 text-amber-500 shrink-0" />
                    <FileCheck v-else class="size-4 text-blue-500 shrink-0" />
                    <span class="font-bold text-zinc-900 dark:text-zinc-100 text-sm leading-snug break-words">
                      {{ change.fullName }}
                    </span>
                  </div>
                  <p v-if="change.passport" class="text-[11px] font-mono text-zinc-500 dark:text-zinc-400 pl-6">
                    {{ change.passport }}
                  </p>
                </div>

                <!-- Right: Old -> New status pill -->
                <div class="flex items-center gap-2 self-start sm:self-center shrink-0">
                  <span class="px-2.5 py-1 rounded-lg text-xs font-semibold bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
                    {{ change.oldStatus }}
                  </span>
                  <ArrowRight class="size-3.5 text-zinc-400 shrink-0" />
                  <span
                    class="px-2.5 py-1 rounded-lg text-xs font-bold shadow-xs"
                    :class="{
                      'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20': getStatusBadgeType(change.newStatus) === 'success',
                      'bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20': getStatusBadgeType(change.newStatus) === 'error',
                      'bg-blue-500/10 text-blue-700 dark:text-blue-300 border border-blue-500/20': getStatusBadgeType(change.newStatus) === 'primary',
                      'bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20': getStatusBadgeType(change.newStatus) === 'warning'
                    }"
                  >
                    {{ change.newStatus }}
                  </span>
                </div>
              </div>
            </div>

            <!-- TAB 2: No Answers -->
            <div
              v-if="activeTab === 'no-answers'"
              class="space-y-2.5 max-h-[46vh] overflow-y-auto pr-1"
            >
              <div
                v-if="noAnswers.length === 0"
                class="py-10 text-center space-y-2 border border-dashed border-emerald-500/20 rounded-2xl bg-emerald-500/5"
              >
                <ShieldCheck class="size-8 text-emerald-500 mx-auto" />
                <p class="text-xs text-emerald-700 dark:text-emerald-400 font-bold">
                  Barcha tanlangan talabalarning viza ma'lumotlari portal orqali muvaffaqiyatli olindi!
                </p>
              </div>

              <div
                v-for="noAns in noAnswers"
                :key="noAns.passport"
                class="group relative overflow-hidden rounded-2xl border border-rose-500/20 bg-rose-500/[0.03] dark:bg-rose-500/[0.05] p-3.5 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-l-4 border-l-rose-500"
              >
                <div class="space-y-1">
                  <div class="flex items-center gap-2">
                    <WifiOff class="size-4 text-rose-500 shrink-0" />
                    <span class="font-bold text-zinc-900 dark:text-zinc-100 text-sm">
                      {{ noAns.fullName }}
                    </span>
                    <span class="font-mono text-xs px-2 py-0.5 rounded bg-zinc-200/60 dark:bg-white/10 text-zinc-700 dark:text-zinc-300">
                      {{ noAns.passport }}
                    </span>
                  </div>
                  <p class="text-xs text-rose-600 dark:text-rose-400 pl-6 flex items-center gap-1.5">
                    <Clock class="size-3 shrink-0" />
                    <span>10s timeout bo'ldi — 1 marta qayta tekshirildi, lekin javob bermadi</span>
                  </p>
                </div>

                <div class="self-start sm:self-center shrink-0">
                  <span class="px-2.5 py-1 rounded-lg text-xs font-bold bg-rose-500/10 text-rose-700 dark:text-rose-300 border border-rose-500/20">
                    Javob olinmadi
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Footer -->
          <div class="p-5 sm:p-6 pt-4 border-t border-zinc-100 dark:border-white/10 flex items-center justify-between gap-3 bg-zinc-50/50 dark:bg-white/[0.01]">
            <div>
              <button
                v-if="noAnswers.length > 0"
                type="button"
                :disabled="isRetrying"
                class="px-4 py-2.5 rounded-xl font-bold text-xs bg-amber-500 hover:bg-amber-600 text-white flex items-center gap-1.5 transition-colors disabled:opacity-50 cursor-pointer shadow-xs"
                @click="emit('retry-no-answers')"
              >
                <RotateCcw class="size-3.5" :class="{ 'animate-spin': isRetrying }" />
                <span>Javobsizlarni qayta tekshirish ({{ noAnswers.length }})</span>
              </button>
            </div>

            <button
              type="button"
              class="px-6 py-2.5 rounded-xl font-bold text-xs bg-[#0B4133] hover:bg-[#0d4e3d] text-white transition-colors cursor-pointer shadow-md"
              @click="emit('close')"
            >
              Tushunarli
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
