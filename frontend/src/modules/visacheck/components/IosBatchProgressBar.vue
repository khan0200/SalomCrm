<script setup lang="ts">
import { computed } from 'vue'
import { Check, RefreshCw } from 'lucide-vue-next'

const props = defineProps<{
  active: boolean
  total: number
  completed: number
  failed: number
  currentStudentName?: string
}>()

const isFinished = computed(() => props.total > 0 && props.completed >= props.total)

const percentage = computed(() => {
  if (!props.total) return 0
  const pct = Math.round((props.completed / props.total) * 100)
  return Math.min(100, Math.max(0, pct))
})
</script>

<template>
  <Transition
    enter-active-class="transition-all duration-500 ease-[cubic-bezier(0.16,1,0.3,1)]"
    enter-from-class="opacity-0 translate-y-8 scale-95"
    enter-to-class="opacity-100 translate-y-0 scale-100"
    leave-active-class="transition-all duration-400 ease-[cubic-bezier(0.16,1,0.3,1)]"
    leave-from-class="opacity-100 translate-y-0 scale-100"
    leave-to-class="opacity-0 translate-y-6 scale-95"
  >
    <div
      v-if="active && total > 0"
      class="fixed bottom-6 sm:bottom-8 left-1/2 -translate-x-1/2 z-[90] pointer-events-auto select-none"
    >
      <!-- Apple Dynamic Island / Live Activity Glass Capsule -->
      <div
        class="relative flex flex-col gap-2.5 px-4.5 py-3 sm:px-5 sm:py-3.5 rounded-[22px] min-w-[290px] sm:min-w-[340px] max-w-[92vw] text-white shadow-2xl overflow-hidden bg-zinc-950/90 dark:bg-black/90 backdrop-blur-xl border border-white/15"
      >
        <!-- Top Status Row -->
        <div class="flex items-center justify-between gap-3 sm:gap-4">
          <div class="flex items-center gap-2.5 min-w-0">
            <!-- Spinner / Check icon -->
            <div class="relative flex items-center justify-center size-5 shrink-0">
              <div
                v-if="isFinished"
                class="flex items-center justify-center size-5 rounded-full bg-emerald-500/20 text-emerald-400"
              >
                <Check class="size-3.5" />
              </div>
              <div
                v-else
                class="flex items-center justify-center size-5 text-emerald-400"
              >
                <RefreshCw class="size-4 animate-spin" />
              </div>
            </div>

            <!-- Title / Student Name -->
            <div class="flex flex-col min-w-0">
              <span class="text-xs sm:text-sm font-bold tracking-tight text-zinc-100 truncate">
                {{ isFinished ? 'Tekshiruv yakunlandi' : (currentStudentName || 'Viza tekshirilmoqda...') }}
              </span>
              <span class="text-[10px] text-zinc-400 font-mono">
                {{ completed }} / {{ total }} ta tekshirildi
                <span v-if="failed > 0" class="text-rose-400">({{ failed }} ta xato)</span>
              </span>
            </div>
          </div>

          <!-- Percentage Counter -->
          <div class="flex items-baseline gap-1 shrink-0 font-mono">
            <span class="text-base sm:text-lg font-black text-emerald-400">
              {{ percentage }}%
            </span>
          </div>
        </div>

        <!-- Progress Bar -->
        <div class="relative h-2 w-full bg-white/10 rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-emerald-500 via-emerald-400 to-teal-400 rounded-full transition-all duration-300"
            :style="{ width: `${percentage}%` }"
          />
        </div>
      </div>
    </div>
  </Transition>
</template>
