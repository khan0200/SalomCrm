<script setup lang="ts">
import { computed } from 'vue'
import type { Student } from '@/types'
import { Users } from 'lucide-vue-next'

const props = defineProps<{
  students: Student[]
}>()

const emit = defineEmits<{
  (e: 'open-add-payment', studentId: string): void
}>()

function formatAmount(val: number | string | null | undefined) {
  if (val === null || val === undefined) return '0'
  const num = typeof val === 'string' ? parseFloat(val) : val
  return new Intl.NumberFormat('uz-UZ').format(Math.round(num || 0))
}

const hasTariff = (s: Student) => !!s.tariff && s.tariff !== 'No Tariff' && s.tariff !== 'NO_TARIFF'

// A student is "NEW" when no real Payment row exists yet (neither a payment
// nor a discount) - the balance alone can't tell NEW from Qarzdor because
// balance already nets the tariff price in before any payment is made, so a
// never-paid student's balance is usually negative too, just like a debtor's.
const hasAnyPaymentHistory = (s: Student) => {
  const paid = Number(s.total_payments) || 0
  const discount = Number(s.discount) || 0
  return paid > 0 || discount > 0
}

type ColumnKey = 'new' | 'debtor' | 'full' | 'b2b'

// Card border matches the Status module's Kanban card style (border-2
// border-dashed, colored per column) instead of a plain thin border.
const COLUMNS: { key: ColumnKey; label: string; headerClass: string; countClass: string; cardBorderClass: string }[] = [
  { key: 'new', label: 'NEW', headerClass: 'text-zinc-500 dark:text-zinc-400', countClass: 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500 dark:text-zinc-400', cardBorderClass: 'border-zinc-400 dark:border-zinc-500' },
  { key: 'debtor', label: 'QARZDOR', headerClass: 'text-amber-600 dark:text-amber-400', countClass: 'bg-amber-100 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400', cardBorderClass: 'border-amber-500 dark:border-amber-400' },
  { key: 'full', label: 'FULL', headerClass: 'text-emerald-600 dark:text-emerald-400', countClass: 'bg-emerald-100 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400', cardBorderClass: 'border-emerald-500 dark:border-emerald-400' },
  { key: 'b2b', label: 'B2B', headerClass: 'text-violet-600 dark:text-violet-400', countClass: 'bg-violet-100 dark:bg-violet-950/50 text-violet-600 dark:text-violet-400', cardBorderClass: 'border-violet-500 dark:border-violet-400' },
]

const studentsByColumn = computed(() => {
  const groups: Record<ColumnKey, Student[]> = { new: [], debtor: [], full: [], b2b: [] }
  for (const s of props.students) {
    if (!hasTariff(s)) {
      groups.b2b.push(s)
    } else if (!hasAnyPaymentHistory(s)) {
      groups.new.push(s)
    } else if ((Number(s.balance) || 0) < 0) {
      groups.debtor.push(s)
    } else {
      groups.full.push(s)
    }
  }
  return groups
})
</script>

<template>
  <div class="overflow-x-auto scrollbar-thin">
    <div class="flex gap-3 pb-2 w-full">
      <div
        v-for="col in COLUMNS"
        :key="col.key"
        class="flex flex-col min-w-[280px] flex-1 max-h-[calc(100vh-280px)] bg-zinc-50/70 dark:bg-zinc-900/60 border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden select-none"
      >
        <!-- Column header -->
        <div class="flex items-center justify-between px-3.5 py-3 border-b border-zinc-200 dark:border-zinc-800 shrink-0 bg-white/60 dark:bg-zinc-850/60">
          <h3 class="text-xs font-bold uppercase tracking-wider" :class="col.headerClass">
            {{ col.label }}
          </h3>
          <span
            class="text-[10.5px] font-bold px-2 py-0.5 rounded-full"
            :class="col.countClass"
          >
            {{ studentsByColumn[col.key].length }}
          </span>
        </div>

        <!-- Card list -->
        <div class="flex-1 min-h-0 overflow-y-auto scrollbar-thin px-2.5 py-2.5">
          <div
            v-if="studentsByColumn[col.key].length === 0"
            class="flex flex-col items-center justify-center gap-1.5 py-10 text-center"
          >
            <Users class="w-5 h-5 text-zinc-300 dark:text-zinc-700" />
            <p class="text-[11px] text-zinc-400 dark:text-zinc-500 font-medium">No students</p>
          </div>

          <div v-else class="flex flex-col gap-1.5">
            <button
              v-for="student in studentsByColumn[col.key]"
              :key="student.id"
              type="button"
              @click="emit('open-add-payment', student.id)"
              class="text-left rounded-xl border-2 border-dashed bg-white dark:bg-zinc-900 p-3 shadow-md hover:shadow-lg transition-all cursor-pointer w-full hover:-translate-y-0.5 group"
              :class="col.cardBorderClass"
            >
              <!-- Name + Archive badge -->
              <div class="flex items-center justify-between gap-2">
                <div class="font-bold text-[13px] uppercase text-zinc-900 dark:text-zinc-100 truncate tracking-wide group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {{ student.full_name }}
                </div>
                <span
                  v-if="student.is_permanently_deleted"
                  class="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase bg-rose-600/15 text-rose-700 dark:text-rose-400 border border-rose-600/25 shrink-0"
                >
                  Deleted
                </span>
                <span
                  v-else-if="student.is_deleted"
                  class="px-1.5 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20 shrink-0"
                >
                  Archive
                </span>
              </div>

              <!-- ID + Tariff badges -->
              <div class="flex flex-wrap gap-1 mt-2">
                <span class="text-[11px] font-bold px-1.5 py-0.5 rounded-[5px] bg-[#0066cc] text-white font-mono shadow-2xs">
                  {{ student.id }}
                </span>
                <span
                  v-if="hasTariff(student)"
                  class="text-[11px] font-bold px-2 py-0.5 rounded-[5px] bg-[#10b981] text-white uppercase shadow-2xs truncate max-w-[140px]"
                >
                  {{ student.tariff }}
                </span>
              </div>

              <!-- Balance (NEW + Qarzdor only) -->
              <div v-if="col.key === 'new' || col.key === 'debtor'" class="flex flex-wrap gap-1 mt-1.5">
                <span
                  class="text-[11px] font-bold px-2 py-0.5 rounded-[5px] text-white shadow-2xs font-mono"
                  :class="(Number(student.balance) || 0) < 0 ? 'bg-[#ef4444]' : 'bg-[#10b981]'"
                >
                  {{ (Number(student.balance) || 0) > 0 ? '+' : '' }}{{ formatAmount(student.balance) }}
                </span>
                <span
                  v-if="student.discount !== null && student.discount !== undefined && Number(student.discount) > 0"
                  class="text-[11px] font-bold px-2 py-0.5 rounded-[5px] bg-[#be185d] text-white font-mono shadow-2xs"
                >
                  {{ formatAmount(student.discount) }}
                </span>
              </div>

              <!-- Discount only (FULL + B2B) -->
              <div v-else class="flex flex-wrap gap-1 mt-1.5">
                <span
                  v-if="student.discount !== null && student.discount !== undefined && Number(student.discount) > 0"
                  class="text-[11px] font-bold px-2 py-0.5 rounded-[5px] bg-[#be185d] text-white font-mono shadow-2xs"
                >
                  {{ formatAmount(student.discount) }}
                </span>
              </div>

              <!-- Payments Done / Withdrawal (Qarzdor, FULL, B2B) -->
              <div v-if="col.key !== 'new'" class="pt-2 mt-2 border-t border-zinc-100 dark:border-zinc-800 flex flex-col gap-0.5">
                <div class="flex items-center justify-between text-[10.5px]">
                  <span class="text-zinc-400 dark:text-zinc-500 font-semibold uppercase tracking-wide">Payments Done:</span>
                  <span class="font-bold font-mono text-zinc-700 dark:text-zinc-300">{{ formatAmount(student.total_payments) }} UZS</span>
                </div>
                <div
                  v-if="(Number(student.total_withdrawals) || 0) > 0"
                  class="flex items-center justify-between text-[10.5px]"
                >
                  <span class="text-rose-400 dark:text-rose-500 font-semibold uppercase tracking-wide">Withdrawal:</span>
                  <span class="font-bold font-mono text-rose-600 dark:text-rose-400">{{ formatAmount(student.total_withdrawals) }} UZS</span>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
