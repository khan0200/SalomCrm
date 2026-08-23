<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { X, Calendar } from 'lucide-vue-next'

const props = defineProps<{
  isOpen: boolean
  type: 'PUT' | 'TAKE'
  studentId: string | null
  studentName?: string
  initialValue?: string | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', payload: { studentId: string; type: 'PUT' | 'TAKE'; date: string }): void
}>()

const curYear = ref('2026')
const curMonth = ref('06')
const curDay = ref('11')

const getDaysInMonth = (year: number, month: number) => {
  return new Date(year, month, 0).getDate()
}

const currentYearNum = new Date().getFullYear()
const yearsList = computed(() => {
  const list = []
  for (let y = currentYearNum - 3; y <= currentYearNum + 5; y++) {
    list.push(String(y))
  }
  return list
})

const monthsList = [
  { value: '01', label: '01 - Jan' },
  { value: '02', label: '02 - Feb' },
  { value: '03', label: '03 - Mar' },
  { value: '04', label: '04 - Apr' },
  { value: '05', label: '05 - May' },
  { value: '06', label: '06 - Jun' },
  { value: '07', label: '07 - Jul' },
  { value: '08', label: '08 - Aug' },
  { value: '09', label: '09 - Sep' },
  { value: '10', label: '10 - Oct' },
  { value: '11', label: '11 - Nov' },
  { value: '12', label: '12 - Dec' },
]

const daysList = computed(() => {
  const maxDays = getDaysInMonth(parseInt(curYear.value), parseInt(curMonth.value))
  const list = []
  for (let d = 1; d <= maxDays; d++) {
    list.push(String(d).padStart(2, '0'))
  }
  return list
})

watch(() => props.isOpen, (open) => {
  if (open) {
    if (props.initialValue && props.initialValue.includes('-')) {
      const parts = props.initialValue.split('-')
      if (parts.length === 3) {
        curYear.value = parts[0]
        curMonth.value = parts[1].padStart(2, '0')
        curDay.value = parts[2].padStart(2, '0')
        return
      }
    }
    const today = new Date()
    curYear.value = String(today.getFullYear())
    curMonth.value = String(today.getMonth() + 1).padStart(2, '0')
    curDay.value = String(today.getDate()).padStart(2, '0')
  }
})

const handleYearChange = (year: string) => {
  curYear.value = year
  const days = getDaysInMonth(parseInt(year), parseInt(curMonth.value))
  if (parseInt(curDay.value) > days) {
    curDay.value = String(days).padStart(2, '0')
  }
}

const handleMonthChange = (month: string) => {
  curMonth.value = month
  const days = getDaysInMonth(parseInt(curYear.value), parseInt(month))
  if (parseInt(curDay.value) > days) {
    curDay.value = String(days).padStart(2, '0')
  }
}

const formattedDatePreview = computed(() => {
  return `${curYear.value}-${curMonth.value}-${curDay.value}`
})

const handleSave = () => {
  if (!props.studentId) return
  emit('save', {
    studentId: props.studentId,
    type: props.type,
    date: formattedDatePreview.value
  })
  emit('close')
}
</script>

<template>
  <div v-if="isOpen" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <!-- Backdrop Overlay -->
    <div
      @click="emit('close')"
      class="fixed inset-0 bg-black/50 transition-opacity duration-200"
    />

    <!-- Modal Panel -->
    <div class="relative w-full max-w-sm overflow-hidden rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-6 shadow-2xl z-10 flex flex-col select-none">
      <div class="flex items-center justify-between mb-4">
        <div>
          <h3 class="text-base font-bold text-zinc-900 dark:text-zinc-100 flex items-center gap-2">
            <Calendar class="w-4 h-4 text-blue-600 dark:text-blue-400" />
            <span>Enter {{ type }} Date</span>
          </h3>
          <p v-if="studentName" class="text-xs text-zinc-500 dark:text-zinc-400 mt-0.5 font-medium">
            {{ studentName }}
          </p>
        </div>
        <button
          @click="emit('close')"
          class="rounded-lg p-1.5 text-zinc-400 hover:text-zinc-700 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <X class="w-4 h-4" />
        </button>
      </div>

      <div class="grid grid-cols-3 gap-2 mb-5">
        <!-- Year Select -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Year</label>
          <select
            :value="curYear"
            @change="handleYearChange(($event.target as HTMLSelectElement).value)"
            class="w-full px-2 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 text-xs font-bold focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option v-for="y in yearsList" :key="y" :value="y">{{ y }}</option>
          </select>
        </div>

        <!-- Month Select -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Month</label>
          <select
            :value="curMonth"
            @change="handleMonthChange(($event.target as HTMLSelectElement).value)"
            class="w-full px-2 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 text-xs font-bold focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option v-for="m in monthsList" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </div>

        <!-- Day Select -->
        <div class="flex flex-col gap-1">
          <label class="text-[10px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider">Day</label>
          <select
            v-model="curDay"
            class="w-full px-2 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800 text-zinc-900 dark:text-zinc-100 text-xs font-bold focus:outline-none focus:border-blue-500 cursor-pointer"
          >
            <option v-for="d in daysList" :key="d" :value="d">{{ d }}</option>
          </select>
        </div>
      </div>

      <!-- Preview -->
      <div class="p-2.5 rounded-xl bg-zinc-100/80 dark:bg-zinc-800/80 border border-zinc-200 dark:border-zinc-700 text-center mb-5">
        <span class="text-[10px] text-zinc-500 font-semibold block uppercase">Selected Date:</span>
        <span class="text-sm font-extrabold text-blue-600 dark:text-blue-400 font-mono tracking-wider">
          {{ formattedDatePreview }}
        </span>
      </div>

      <!-- Actions -->
      <div class="flex items-center justify-end gap-2">
        <button
          type="button"
          @click="emit('close')"
          class="px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 bg-transparent text-xs font-bold text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-800 cursor-pointer transition-colors"
        >
          Cancel
        </button>
        <button
          type="button"
          @click="handleSave"
          class="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold cursor-pointer transition-colors shadow-xs"
        >
          Save
        </button>
      </div>
    </div>
  </div>
</template>
