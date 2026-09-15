<script setup lang="ts">
import { ref } from 'vue'
import {
  Type,
  Heading1,
  Heading2,
  FileText,
  Table as TableIcon,
  PenTool,
  Minus,
  CheckSquare,
  Variable,
  Calendar,
  Sparkles,
  Building2,
  UserCheck,
} from 'lucide-vue-next'
import type { CanvasElement, PageMargins } from '../../types/contractCanvas'
import { CONTRACT_VARIABLES, resolveTenantRequisites, buildCompanyRequisitesHtml, buildClientRequisitesHtml } from '../../utils/contractVariables'

const props = defineProps<{
  margins: PageMargins
}>()

const emit = defineEmits<{
  'add-element': [element: CanvasElement]
  close: []
}>()

const activeTab = ref<'text' | 'table' | 'contract' | 'variables'>('text')

function generateId(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`
}

// 1. Text Elements
function insertText(type: 'heading1' | 'heading2' | 'paragraph') {
  const contentWidth = 210 - props.margins.left - props.margins.right
  if (type === 'heading1') {
    emit('add-element', {
      id: generateId('heading'),
      type: 'heading',
      headingLevel: 1,
      x: props.margins.left,
      y: props.margins.top + 10,
      width: contentWidth,
      height: 9,
      zIndex: 1,
      content: '<h1><strong>Sarlavha 1</strong></h1>',
      style: {
        fontFamily: 'Times New Roman',
        fontSize: 16,
        fontWeight: 'bold',
        textAlign: 'center',
        color: '#111827',
      },
    })
  } else if (type === 'heading2') {
    emit('add-element', {
      id: generateId('heading'),
      type: 'heading',
      headingLevel: 2,
      x: props.margins.left,
      y: props.margins.top + 10,
      width: contentWidth,
      height: 8,
      zIndex: 1,
      content: '<h2><strong>Bo\'lim sarlavhasi</strong></h2>',
      style: {
        fontFamily: 'Times New Roman',
        fontSize: 14,
        fontWeight: 'bold',
        textAlign: 'left',
        color: '#111827',
      },
    })
  } else {
    emit('add-element', {
      id: generateId('text'),
      type: 'text',
      x: props.margins.left,
      y: props.margins.top + 10,
      width: contentWidth,
      height: 8,
      zIndex: 1,
      content: '<p>Yangi matn bloki. Tahrirlash uchun ikki marta bosing.</p>',
      style: {
        fontFamily: 'Times New Roman',
        fontSize: 12,
        textAlign: 'justify',
        color: '#111827',
        lineHeight: 1.5,
      },
    })
  }
}

// 2. Table Elements
function insertTablePreset(rows: number, cols: number, borderStyle: string, density: 'compact' | 'normal' | 'spacious' = 'normal') {
  const contentWidth = 210 - props.margins.left - props.margins.right
  const colW = contentWidth / cols
  const colWidths = Array(cols).fill(Math.round(colW * 10) / 10)
  const rowHeights = Array(rows).fill(10)

  const cells = Array.from({ length: rows }, () =>
    Array.from({ length: cols }, () => ({
      id: generateId('cell'),
      content: '&nbsp;',
    }))
  )

  emit('add-element', {
    id: generateId('table'),
    type: 'table',
    x: props.margins.left,
    y: props.margins.top + 10,
    width: contentWidth,
    height: Math.max(20, rows * 10),
    zIndex: 1,
    rows,
    cols,
    colWidths,
    rowHeights,
    cells,
    borderWidth: borderStyle === 'none' ? '0px' : '1px',
    borderColor: '#94a3b8',
    borderStyle: borderStyle === 'none' ? 'none' : 'solid',
    density,
  })
}

// 3. Official Signature Block
function insertSignatureBlock() {
  const contentWidth = 210 - props.margins.left - props.margins.right
  emit('add-element', {
    id: generateId('signature'),
    type: 'signature',
    signerRole: 'dual',
    x: props.margins.left,
    y: 200,
    width: contentWidth,
    height: 70,
    zIndex: 1,
    contractorCompany: 'MCHJ "IT STATION" (UniBridge)',
    contractorDirector: 'M.Abdulpattayev',
    contractorInn: '309 961 634',
    clientName: '_________________________',
    clientPassport: '____ _________',
    signedDate: '«___» ____________ 2026 Yil',
  })
}

// 4. Line / Divider
function insertLine(orientation: 'horizontal' | 'vertical') {
  const contentWidth = 210 - props.margins.left - props.margins.right
  emit('add-element', {
    id: generateId('line'),
    type: 'line',
    orientation,
    x: props.margins.left,
    y: props.margins.top + 10,
    width: orientation === 'horizontal' ? contentWidth : 2,
    height: orientation === 'horizontal' ? 2 : 40,
    zIndex: 1,
    strokeWidth: 1,
    strokeColor: '#111827',
    strokeStyle: 'solid',
  })
}

// 5. Checkbox
function insertCheckbox(checked: boolean) {
  emit('add-element', {
    id: generateId('checkbox'),
    type: 'checkbox',
    checked,
    label: 'Tanlov varianti',
    x: props.margins.left,
    y: props.margins.top + 10,
    width: 60,
    height: 7,
    zIndex: 1,
    fontSize: 12,
    style: {
      fontFamily: 'Times New Roman',
      fontSize: 12,
      fontWeight: 'normal',
      fontStyle: 'normal',
      textDecoration: 'none',
      color: '#111827',
    },
  })
}

// 6. Variable Insertion
function insertVariableElement(varKey: string, label: string) {
  const cleanKey = varKey.replace(/^\{\{|\}\}$/g, '')
  emit('add-element', {
    id: generateId('var'),
    type: 'text',
    x: props.margins.left,
    y: props.margins.top + 10,
    width: 60,
    height: 10,
    zIndex: 1,
    content: `{{${cleanKey}}}`,
    variableKey: cleanKey,
    style: {
      fontFamily: 'Times New Roman',
      fontSize: 12,
      color: '#1d4ed8',
    },
  })
}

// 7. Company Requisites Insertion
function insertCompanyRequisites() {
  const req = resolveTenantRequisites()
  const contentWidth = props.margins ? (210 - props.margins.left - props.margins.right) : 180
  const blockWidth = Math.min(88, Math.floor(contentWidth / 2) - 2)
  emit('add-element', {
    id: generateId('req'),
    type: 'text',
    x: props.margins ? props.margins.left : 15,
    y: (props.margins ? props.margins.top : 15) + 10,
    width: blockWidth,
    height: 72,
    zIndex: 1,
    content: buildCompanyRequisitesHtml(req),
    style: {
      fontFamily: 'Times New Roman',
      fontSize: 11,
      fontWeight: 'bold',
      fontStyle: 'normal',
      textAlign: 'left',
      color: '#000000',
      lineHeight: 1.35,
    },
  })
}

// 8. Client Requisites Insertion (MIJOZ)
function insertClientRequisites() {
  const contentWidth = props.margins ? (210 - props.margins.left - props.margins.right) : 180
  const blockWidth = Math.min(88, Math.floor(contentWidth / 2) - 2)
  emit('add-element', {
    id: generateId('client_req'),
    type: 'text',
    x: props.margins ? (210 - props.margins.right - blockWidth) : 107,
    y: (props.margins ? props.margins.top : 15) + 10,
    width: blockWidth,
    height: 72,
    zIndex: 1,
    content: buildClientRequisitesHtml(),
    style: {
      fontFamily: 'Times New Roman',
      fontSize: 11,
      fontWeight: 'bold',
      fontStyle: 'normal',
      textAlign: 'left',
      color: '#000000',
      lineHeight: 1.35,
    },
  })
}
</script>

<template>
  <div
    class="canvas-add-element-menu w-72 bg-white dark:bg-zinc-900 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-2xl p-3 z-50 animate-scale-in text-xs select-none"
    @pointerdown.stop
  >
    <!-- Header Tabs -->
    <div class="flex items-center gap-1 border-b border-zinc-100 dark:border-zinc-800 pb-2 mb-2.5">
      <button
        type="button"
        @click="activeTab = 'text'"
        class="flex-1 py-1 rounded-lg font-bold text-center transition-all cursor-pointer"
        :class="activeTab === 'text' ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400' : 'text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800'"
      >
        Text
      </button>
      <button
        type="button"
        @click="activeTab = 'table'"
        class="flex-1 py-1 rounded-lg font-bold text-center transition-all cursor-pointer"
        :class="activeTab === 'table' ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400' : 'text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800'"
      >
        Table
      </button>
      <button
        type="button"
        @click="activeTab = 'contract'"
        class="flex-1 py-1 rounded-lg font-bold text-center transition-all cursor-pointer"
        :class="activeTab === 'contract' ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400' : 'text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800'"
      >
        Objects
      </button>
      <button
        type="button"
        @click="activeTab = 'variables'"
        class="flex-1 py-1 rounded-lg font-bold text-center transition-all cursor-pointer"
        :class="activeTab === 'variables' ? 'bg-blue-50 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400' : 'text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800'"
      >
        Variables
      </button>
    </div>

    <!-- 1. Text Tab -->
    <div v-if="activeTab === 'text'" class="space-y-1.5">
      <button
        type="button"
        @click="insertText('heading1'); emit('close')"
        class="w-full text-left p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-950/40 transition-colors flex items-center gap-2.5 cursor-pointer group"
      >
        <div class="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-800 group-hover:bg-blue-100 flex items-center justify-center font-bold text-base text-zinc-700 dark:text-zinc-300 group-hover:text-blue-600">
          H1
        </div>
        <div>
          <div class="font-bold text-zinc-900 dark:text-zinc-100">Heading 1</div>
          <div class="text-[10px] text-zinc-400">16pt Bold — Asosiy shartnoma sarlavhasi</div>
        </div>
      </button>

      <button
        type="button"
        @click="insertText('heading2'); emit('close')"
        class="w-full text-left p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-950/40 transition-colors flex items-center gap-2.5 cursor-pointer group"
      >
        <div class="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-800 group-hover:bg-blue-100 flex items-center justify-center font-bold text-sm text-zinc-700 dark:text-zinc-300 group-hover:text-blue-600">
          H2
        </div>
        <div>
          <div class="font-bold text-zinc-900 dark:text-zinc-100">Heading 2</div>
          <div class="text-[10px] text-zinc-400">14pt Bold — Bo'lim sarlavhasi</div>
        </div>
      </button>

      <button
        type="button"
        @click="insertText('paragraph'); emit('close')"
        class="w-full text-left p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-blue-500 hover:bg-blue-50/50 dark:hover:bg-blue-950/40 transition-colors flex items-center gap-2.5 cursor-pointer group"
      >
        <div class="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-800 group-hover:bg-blue-100 flex items-center justify-center font-bold text-xs text-zinc-700 dark:text-zinc-300 group-hover:text-blue-600">
          <Type class="w-4 h-4" />
        </div>
        <div>
          <div class="font-bold text-zinc-900 dark:text-zinc-100">Text Box / Paragraph</div>
          <div class="text-[10px] text-zinc-400">12pt Regular — Oddiy bandlar va matnlar</div>
        </div>
      </button>
    </div>

    <!-- 2. Table Tab -->
    <div v-else-if="activeTab === 'table'" class="space-y-1.5">
      <div class="grid grid-cols-2 gap-1.5">
        <button
          type="button"
          @click="insertTablePreset(3, 3, 'solid'); emit('close')"
          class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/40 text-left cursor-pointer"
        >
          <div class="font-bold text-xs text-zinc-800 dark:text-zinc-200">3 × 3</div>
          <div class="text-[10px] text-zinc-400">Standard</div>
        </button>
        <button
          type="button"
          @click="insertTablePreset(3, 2, 'solid'); emit('close')"
          class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/40 text-left cursor-pointer"
        >
          <div class="font-bold text-xs text-zinc-800 dark:text-zinc-200">2 × 3</div>
          <div class="text-[10px] text-zinc-400">2 Columns</div>
        </button>
        <button
          type="button"
          @click="insertTablePreset(1, 2, 'none'); emit('close')"
          class="p-2 rounded-xl border border-blue-200 dark:border-blue-900/60 bg-blue-50/40 text-left cursor-pointer col-span-2 hover:bg-blue-100"
        >
          <div class="font-bold text-xs text-blue-700 dark:text-blue-300">Signatures (2 × 1)</div>
          <div class="text-[10px] text-zinc-500">Border-free signature table</div>
        </button>
        <button
          type="button"
          @click="insertTablePreset(4, 4, 'solid'); emit('close')"
          class="p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-blue-500 hover:bg-blue-50 dark:hover:bg-blue-950/40 text-left cursor-pointer col-span-2"
        >
          <div class="font-bold text-xs text-zinc-800 dark:text-zinc-200">4 × 4</div>
          <div class="text-[10px] text-zinc-400">Large Data Table</div>
        </button>
      </div>
    </div>

    <!-- 3. Objects Tab (Signatures, Line, Checkbox) -->
    <div v-else-if="activeTab === 'contract'" class="space-y-1.5">
      <button
        type="button"
        @click="insertSignatureBlock(); emit('close')"
        class="w-full text-left p-2 rounded-xl border border-blue-200 dark:border-blue-800 bg-blue-50/50 dark:bg-blue-950/40 hover:bg-blue-100 transition-colors flex items-center gap-2.5 cursor-pointer"
      >
        <div class="w-8 h-8 rounded-lg bg-blue-600 text-white flex items-center justify-center font-bold">
          <PenTool class="w-4 h-4" />
        </div>
        <div>
          <div class="font-bold text-blue-900 dark:text-blue-200">Dual Signature Block</div>
          <div class="text-[10px] text-zinc-500">Bajaruvchi va Mijoz rekvizitlari & muhr o'rni</div>
        </div>
      </button>

      <button
        type="button"
        @click="insertLine('horizontal'); emit('close')"
        class="w-full text-left p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-blue-500 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors flex items-center gap-2.5 cursor-pointer"
      >
        <div class="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-zinc-600 dark:text-zinc-300">
          <Minus class="w-4 h-4" />
        </div>
        <div>
          <div class="font-bold text-zinc-800 dark:text-zinc-200">Horizontal Line</div>
          <div class="text-[10px] text-zinc-400">Ajratuvchi chiziq (Divider)</div>
        </div>
      </button>

      <button
        type="button"
        @click="insertCheckbox(true); emit('close')"
        class="w-full text-left p-2 rounded-xl border border-zinc-200 dark:border-zinc-800 hover:border-blue-500 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors flex items-center gap-2.5 cursor-pointer"
      >
        <div class="w-8 h-8 rounded-lg bg-zinc-100 dark:bg-zinc-800 flex items-center justify-center text-blue-600">
          <CheckSquare class="w-4 h-4" />
        </div>
        <div>
          <div class="font-bold text-zinc-800 dark:text-zinc-200">Checkbox (☑ / ☐)</div>
          <div class="text-[10px] text-zinc-400">Belgilash katagi</div>
        </div>
      </button>

      <button
        type="button"
        @click="insertCompanyRequisites(); emit('close')"
        class="w-full text-left p-2 rounded-xl border border-indigo-200 dark:border-indigo-800 bg-indigo-50/50 dark:bg-indigo-950/40 hover:bg-indigo-100 transition-colors flex items-center gap-2.5 cursor-pointer"
      >
        <div class="w-8 h-8 rounded-lg bg-indigo-600 text-white flex items-center justify-center font-bold">
          <Building2 class="w-4 h-4" />
        </div>
        <div>
          <div class="font-bold text-indigo-900 dark:text-indigo-200">Bajaruvchi rekvizitlari</div>
          <div class="text-[10px] text-zinc-500">Kompaniya rasmiy rekvizitlar bloki</div>
        </div>
      </button>

      <button
        type="button"
        @click="insertClientRequisites(); emit('close')"
        class="w-full text-left p-2 rounded-xl border border-emerald-200 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/40 hover:bg-emerald-100 transition-colors flex items-center gap-2.5 cursor-pointer"
      >
        <div class="w-8 h-8 rounded-lg bg-emerald-600 text-white flex items-center justify-center font-bold">
          <UserCheck class="w-4 h-4" />
        </div>
        <div>
          <div class="font-bold text-emerald-900 dark:text-emerald-200">Mijoz rekvizitlari</div>
          <div class="text-[10px] text-zinc-500">Mijoz (F.I.O, Passport, Imzo) bloki</div>
        </div>
      </button>
    </div>

    <!-- 4. Variables Tab -->
    <div v-else-if="activeTab === 'variables'" class="space-y-1 max-h-56 overflow-y-auto pr-1">
      <button
        v-for="v in CONTRACT_VARIABLES"
        :key="v.key"
        type="button"
        @click="insertVariableElement(v.key, v.label); emit('close')"
        class="w-full text-left px-2.5 py-1.5 rounded-lg border border-zinc-100 dark:border-zinc-800 hover:border-blue-400 hover:bg-blue-50/60 dark:hover:bg-blue-950/40 transition-colors flex items-center justify-between cursor-pointer group"
      >
        <div>
          <div class="font-bold text-[11px] text-zinc-800 dark:text-zinc-200 group-hover:text-blue-600">{{ v.label }}</div>
          <div class="font-mono text-[9px] text-zinc-400">{{ v.key }}</div>
        </div>
        <span class="text-[10px] text-blue-500 font-bold opacity-0 group-hover:opacity-100 transition-opacity">+ Add</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.animate-scale-in {
  animation: scaleIn 0.12s ease-out;
}
@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.96) translateY(-4px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}
</style>
