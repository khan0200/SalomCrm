<script setup lang="ts">
import { computed } from 'vue'
import type { SignatureCanvasElement } from '../../types/contractCanvas'

const props = defineProps<{
  element: SignatureCanvasElement
  isSelected: boolean
  zoomLevel: number
  variableValues?: Record<string, string>
}>()

const clientNameDisplay = computed(() => {
  if (props.variableValues) {
    const val = props.variableValues['{{fullname}}'] || props.variableValues['fullname'] || props.variableValues['{{client_name}}'] || props.variableValues['client_name']
    if (val) return val
  }
  return props.element.clientName || '_________________________'
})

const passportDisplay = computed(() => {
  if (props.variableValues) {
    const val = props.variableValues['{{passportnumber}}'] || props.variableValues['passportnumber'] || props.variableValues['{{passport_number}}'] || props.variableValues['passport_number']
    if (val) return val
  }
  return props.element.clientPassport || '____ _________'
})

const dateDisplay = computed(() => {
  if (props.variableValues) {
    const val = props.variableValues['{{contract_date}}'] || props.variableValues['contract_date'] || props.variableValues['{{date}}'] || props.variableValues['date']
    if (val) return val
  }
  return props.element.signedDate || '«___» ____________ 2026 Yil'
})

const scaledFontSizePx = computed(() => {
  return Math.max(5, Math.round(12 * (props.zoomLevel / 100) * 10) / 10)
})

const borderTopWidthPx = computed(() => {
  return Math.max(1, Math.round(2 * (props.zoomLevel / 100) * 10) / 10)
})
</script>

<template>
  <div
    class="canvas-signature-element w-full h-full border-zinc-900 font-serif text-zinc-900"
    :style="{
      fontFamily: '\'Times New Roman\', Times, serif',
      fontSize: `${scaledFontSizePx}px`,
      borderTop: `${borderTopWidthPx}px solid #18181b`,
      paddingTop: `${Math.max(2, Math.round(10 * (props.zoomLevel / 100)))}px`
    }"
  >
    <div class="grid grid-cols-2 h-full" :style="{ gap: `${Math.max(4, Math.round(16 * (props.zoomLevel / 100)))}px` }">
      <!-- Left: Contractor (Bajaruvchi) -->
      <div
        class="border-zinc-300 flex flex-col justify-between"
        :style="{
          borderRight: '1px solid #d4d4d8',
          paddingRight: `${Math.max(2, Math.round(12 * (props.zoomLevel / 100)))}px`
        }"
      >
        <div>
          <h4 class="font-bold text-center uppercase tracking-wider mb-[0.4em]">BAJARUVCHI</h4>
          <p class="font-bold text-[0.92em] leading-tight">MCHJ "IT STATION" (UniBridge)</p>
          <p class="text-[0.83em] text-zinc-600 mt-[0.2em]">INN: 309 961 634 | GUVOHNOMA: 5114456</p>
          <p class="text-[0.83em] text-zinc-600">Andijon viloyati, Marxamat tumani</p>
          <p class="text-[0.83em] text-zinc-600">Tel: +998 93 105 0011</p>
          <p class="text-[0.83em] text-zinc-600">H/R: 2020 8000 9055 7879 0001</p>
          <p class="font-bold text-[0.83em] mt-[0.2em]">Direktor: M.Abdulpattayev</p>
        </div>

        <div
          class="flex items-end justify-between border-t border-dashed border-zinc-400"
          :style="{
            marginTop: `${Math.max(3, Math.round(12 * (props.zoomLevel / 100)))}px`,
            paddingTop: `${Math.max(3, Math.round(12 * (props.zoomLevel / 100)))}px`
          }"
        >
          <div class="text-[0.83em] text-zinc-400 italic">M.O' (Muhr o'rni)</div>
          <div class="text-[0.92em] font-bold">Imzo: ______________</div>
        </div>
      </div>

      <!-- Right: Client (Mijoz) -->
      <div
        class="flex flex-col justify-between"
        :style="{ paddingLeft: `${Math.max(2, Math.round(8 * (props.zoomLevel / 100)))}px` }"
      >
        <div>
          <h4 class="font-bold text-center uppercase tracking-wider mb-[0.4em]">MIJOZ</h4>
          <p class="text-[0.92em] leading-tight">
            <strong>F.I.O:</strong> {{ clientNameDisplay }}
          </p>
          <p class="text-[0.83em] text-zinc-600 mt-[0.2em]">
            <strong>Passport:</strong> {{ passportDisplay }}
          </p>
          <p class="text-[0.83em] text-zinc-600">
            <strong>Manzil:</strong> {{ element.clientAddress || '_________________________________' }}
          </p>
          <p class="text-[0.83em] text-zinc-600">
            <strong>Tel:</strong> {{ element.clientPhone || '_________________________________' }}
          </p>
          <p class="text-[0.83em] text-zinc-600">
            <strong>Sana:</strong> {{ dateDisplay }}
          </p>
        </div>

        <div
          class="flex items-end justify-between border-t border-dashed border-zinc-400"
          :style="{
            marginTop: `${Math.max(3, Math.round(12 * (props.zoomLevel / 100)))}px`,
            paddingTop: `${Math.max(3, Math.round(12 * (props.zoomLevel / 100)))}px`
          }"
        >
          <div class="text-[0.75em] text-zinc-500 italic max-w-[140px] leading-tight">
            *Rozilik va to'liq tanishib chiqilganligini tasdiqlaydi.
          </div>
          <div class="text-[0.92em] font-bold">Imzo: ______________</div>
        </div>
      </div>
    </div>
  </div>
</template>
