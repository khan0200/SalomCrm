<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { FileSpreadsheet } from 'lucide-vue-next'
import ExcelFillPage from '@/modules/excel_fill/ExcelFillPage.vue'

// ─────────────────────────────────────────────────────────────────────────────
// WORD FILL IS TEMPORARILY DISABLED
//
// The engine, its API layer and its tests are all still in the repo and passing;
// only this entry point is switched off. To bring it back:
//   1. uncomment the WordFillPage import below,
//   2. uncomment the 'word' entry in TABS,
//   3. uncomment the <WordFillPage> panel in the template,
//   4. uncomment the /students/word-fill/ routes in backend/apps/students/urls.py.
// Nothing else needs to change.
// ─────────────────────────────────────────────────────────────────────────────
// import { FileType2 } from 'lucide-vue-next'
// import WordFillPage from '@/modules/word_fill/WordFillPage.vue'

type TabKey = 'excel' | 'word'

const route = useRoute()
const router = useRouter()

const TABS = [
  {
    key: 'excel' as TabKey,
    label: 'Excel Fill',
    icon: FileSpreadsheet,
    hint: 'Bitta jadvalga ko\'p talaba',
    activeClass: 'text-emerald-600 dark:text-emerald-400',
    accentClass: 'bg-emerald-500',
  },
  // {
  //   key: 'word' as TabKey,
  //   label: 'Word Fill',
  //   icon: FileType2,
  //   hint: 'Har talabaga alohida ariza',
  //   activeClass: 'text-blue-600 dark:text-blue-400',
  //   accentClass: 'bg-blue-500',
  // },
]

/**
 * The active tab lives in the query string so a tab is linkable, survives a
 * refresh, and the browser's back button steps between tabs. Unknown values
 * (e.g. a bookmarked ?tab=word while Word Fill is off) fall back to Excel.
 */
const activeTab = computed<TabKey>(() => {
  const requested = route.query.tab
  const known = TABS.some(t => t.key === requested)
  return known ? (requested as TabKey) : 'excel'
})

/** The tab strip is pointless while only one engine is available. */
const showTabBar = computed(() => TABS.length > 1)

const selectTab = (key: TabKey) => {
  if (key === activeTab.value) return
  router.replace({ name: 'app-form', query: { tab: key } })
}
</script>

<template>
  <div class="h-full flex flex-col bg-zinc-50 dark:bg-[#0c0d0e] overflow-hidden">
    <!-- Tab bar -->
    <div
      v-if="showTabBar"
      class="bg-white dark:bg-[#111315] border-b border-zinc-200 dark:border-zinc-800/80 px-6 shrink-0"
    >
      <nav class="flex items-end gap-1" role="tablist" aria-label="App Form">
        <button
          v-for="tab in TABS"
          :key="tab.key"
          role="tab"
          :aria-selected="activeTab === tab.key"
          @click="selectTab(tab.key)"
          class="relative flex items-center gap-2.5 px-4 pt-3.5 pb-3 text-sm font-bold transition-colors cursor-pointer"
          :class="activeTab === tab.key
            ? tab.activeClass
            : 'text-zinc-500 dark:text-zinc-400 hover:text-zinc-800 dark:hover:text-zinc-200'"
        >
          <component :is="tab.icon" class="w-4 h-4" />
          <span class="flex flex-col items-start leading-tight">
            {{ tab.label }}
            <span class="text-[10px] font-medium text-zinc-400 dark:text-zinc-500">{{ tab.hint }}</span>
          </span>
          <span
            v-if="activeTab === tab.key"
            class="absolute inset-x-2 -bottom-px h-0.5 rounded-full"
            :class="tab.accentClass"
          />
        </button>
      </nav>
    </div>

    <!-- Panels: each engine keeps its own wizard state while the other is hidden -->
    <div class="flex-1 min-h-0">
      <KeepAlive>
        <ExcelFillPage v-if="activeTab === 'excel'" />
      </KeepAlive>
    </div>
  </div>
</template>
