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
  if (props.variableValues && props.variableValues['{{client_name}}']) {
    return props.variableValues['{{client_name}}']
  }
  return props.element.clientName || '_________________________'
})

const passportDisplay = computed(() => {
  if (props.variableValues && props.variableValues['{{passport_number}}']) {
    return props.variableValues['{{passport_number}}']
  }
  return props.element.clientPassport || '____ _________'
})

const dateDisplay = computed(() => {
  if (props.variableValues && props.variableValues['{{contract_date}}']) {
    return props.variableValues['{{contract_date}}']
  }
  return props.element.signedDate || '«___» ____________ 2026 Yil'
})
</script>

<template>
  <div
    class="canvas-signature-element w-full h-full border-t-2 border-zinc-900 pt-3 text-xs font-serif text-zinc-900"
    style="font-family: 'Times New Roman', Times, serif;"
  >
    <div class="grid grid-cols-2 gap-4 h-full">
      <!-- Left: Contractor (Bajaruvchi) -->
      <div class="border-r border-zinc-300 pr-3 flex flex-col justify-between">
        <div>
          <h4 class="font-bold text-center uppercase tracking-wider text-xs mb-2">BAJARUVCHI</h4>
          <p class="font-bold text-[11px] leading-tight">MCHJ "IT STATION" (UniBridge)</p>
          <p class="text-[10px] text-zinc-600 mt-1">INN: 309 961 634 | GUVOHNOMA: 5114456</p>
          <p class="text-[10px] text-zinc-600">Andijon viloyati, Marxamat tumani</p>
          <p class="text-[10px] text-zinc-600">Tel: +998 93 105 0011</p>
          <p class="text-[10px] text-zinc-600">H/R: 2020 8000 9055 7879 0001</p>
          <p class="font-bold text-[10px] mt-1">Direktor: M.Abdulpattayev</p>
        </div>

        <div class="mt-4 pt-4 flex items-end justify-between border-t border-dashed border-zinc-400">
          <div class="text-[10px] text-zinc-400 italic">M.O' (Muhr o'rni)</div>
          <div class="text-[11px] font-bold">Imzo: ______________</div>
        </div>
      </div>

      <!-- Right: Client (Mijoz) -->
      <div class="pl-2 flex flex-col justify-between">
        <div>
          <h4 class="font-bold text-center uppercase tracking-wider text-xs mb-2">MIJOZ</h4>
          <p class="text-[11px] leading-tight">
            <strong>F.I.O:</strong> {{ clientNameDisplay }}
          </p>
          <p class="text-[10px] text-zinc-600 mt-1">
            <strong>Passport:</strong> {{ passportDisplay }}
          </p>
          <p class="text-[10px] text-zinc-600">
            <strong>Manzil:</strong> {{ element.clientAddress || '_________________________________' }}
          </p>
          <p class="text-[10px] text-zinc-600">
            <strong>Tel:</strong> {{ element.clientPhone || '_________________________________' }}
          </p>
          <p class="text-[10px] text-zinc-600">
            <strong>Sana:</strong> {{ dateDisplay }}
          </p>
        </div>

        <div class="mt-4 pt-4 flex items-end justify-between border-t border-dashed border-zinc-400">
          <div class="text-[9px] text-zinc-500 italic max-w-[140px] leading-tight">
            *Rozilik va to'liq tanishib chiqilganligini tasdiqlaydi.
          </div>
          <div class="text-[11px] font-bold">Imzo: ______________</div>
        </div>
      </div>
    </div>
  </div>
</template>
