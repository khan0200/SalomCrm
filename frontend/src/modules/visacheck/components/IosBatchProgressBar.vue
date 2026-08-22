<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  active: boolean
  total: number
  completed: number
  failed?: number
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
      class="visacheck-page fixed bottom-6 sm:bottom-8 left-1/2 -translate-x-1/2 z-[100] pointer-events-auto select-none"
    >
      <!-- Apple Dynamic Island / Live Activity Glass Capsule -->
      <div
        class="relative flex flex-col gap-2 px-4 py-2.5 sm:px-5 sm:py-3 rounded-xl min-w-[280px] sm:min-w-[320px] max-w-[92vw] text-white shadow-2xl overflow-hidden bg-black/90 backdrop-blur-xl border border-white/15"
      >
        <!-- Top Status Row -->
        <div class="flex items-center justify-between gap-3 sm:gap-4">
          <div class="flex items-center gap-2.5 min-w-0">
            <!-- Left Animated Indicator: Ring or Checkmark -->
            <div class="relative flex items-center justify-center size-4.5 sm:size-5 shrink-0">
              <!-- Finished Checkmark -->
              <div
                v-if="isFinished"
                class="flex items-center justify-center size-4.5 sm:size-5 rounded-full bg-emerald-500/20 text-emerald-400 shadow-[0_0_10px_rgba(16,185,129,0.5)]"
              >
                <svg
                  class="size-3.5 sm:size-4 stroke-current stroke-[2.5]"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <path
                    d="M5 13l4 4L19 7"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
              </div>

              <!-- Animated iOS Ring Spinner -->
              <div
                v-else
                class="relative flex items-center justify-center size-4.5 sm:size-5"
              >
                <svg
                  class="size-full animate-spin"
                  viewBox="0 0 24 24"
                  fill="none"
                >
                  <circle
                    cx="12"
                    cy="12"
                    r="9.5"
                    stroke="rgba(255, 255, 255, 0.12)"
                    stroke-width="2"
                  />
                  <circle
                    cx="12"
                    cy="12"
                    r="9.5"
                    stroke="url(#iosEmeraldGradient)"
                    stroke-width="2.2"
                    stroke-linecap="round"
                    stroke-dasharray="35 60"
                  />
                  <defs>
                    <linearGradient
                      id="iosEmeraldGradient"
                      x1="0%"
                      y1="0%"
                      x2="100%"
                      y2="100%"
                    >
                      <stop offset="0%" stop-color="#34D399" />
                      <stop offset="100%" stop-color="#059669" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>

            <!-- Label & Counter -->
            <div class="flex items-center gap-2 truncate">
              <span class="text-[13px] sm:text-sm font-medium tracking-tight text-neutral-100">
                {{ isFinished ? 'Tekshirildi' : 'Tekshirilmoqda' }}
              </span>

              <!-- Badge / Capsule Counter -->
              <span
                class="inline-flex items-center justify-center px-2 py-0.5 rounded-full bg-white/[0.08] border border-white/[0.12] text-[11px] font-mono font-semibold tracking-tight text-emerald-400 shadow-sm"
              >
                {{ completed }} / {{ total }}
              </span>
            </div>
          </div>

          <!-- Right Percentage Display -->
          <div class="shrink-0 text-right">
            <span class="text-[12px] sm:text-[13px] font-mono font-bold tracking-tight text-neutral-300 tabular-nums">
              {{ percentage }}%
            </span>
          </div>
        </div>

        <!-- Thin Progress Track -->
        <div class="relative w-full h-[3px] bg-white/[0.1] rounded-full overflow-hidden">
          <div
            class="h-full bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 rounded-full transition-all duration-300 ease-out shadow-[0_0_8px_rgba(52,211,153,0.7)]"
            :style="{ width: `${percentage}%` }"
          />
        </div>
      </div>
    </div>
  </Transition>
</template>
