<script setup lang="ts">
import { X, Scale, ExternalLink } from 'lucide-vue-next'

defineProps<{
  isOpen: boolean
}>()

const emit = defineEmits<{
  close: []
}>()

const laws = [
  {
    title: "«Elektron tijorat to'g'risida»gi Qonun",
    code: "O'RQ-792, 29.09.2022",
    url: 'https://lex.uz/docs/-6213382',
    articles: [
      {
        num: '14-modda',
        text: "Elektron tijoratda shartnoma elektron hujjat shaklida rasmiylashtiriladi. Hujjatni imzolagan shaxsning roziligini ifodalaydigan hamda uni identifikatsiya va autentifikatsiya qilish imkonini beradigan elektron tasdiqlash usullari (SMS, Face-ID va boshqalar) ham imzo sifatida tan olinadi.",
      },
      {
        num: '15-modda',
        text: "Elektron hujjatlar qog'ozda rasmiylashtirilgan va o'z qo'li bilan imzolangan hujjatlarga tenglashtiriladi hamda ulardan shartnoma tuzilganligining dalili sifatida foydalanilishi mumkin.",
      },
      {
        num: '19-modda',
        text: "Shartnoma elektron raqamli imzo bilan tasdiqlanadigan elektron hujjat, elektron tijorat ishtirokchisining roziligi bildirilgan elektron xabar yoki oferta shartlarini bajarishga doir harakatlarni bajarish orqali tuzilishi mumkin.",
      },
    ],
  },
  {
    title: "«Elektron raqamli imzo to'g'risida»gi Qonun",
    code: "O'RQ-793, 12.10.2022",
    url: 'https://lex.uz/docs/-6234904',
    articles: [
      {
        num: '4-modda',
        text: "Elektron raqamli imzo bilan tasdiqlangan hujjat, imzoning haqiqiyligi tasdiqlangan taqdirda, qog'oz hujjatdagi qo'lda qo'yilgan imzoga tenglashtiriladi.",
      },
    ],
  },
  {
    title: "O'zbekiston Respublikasi Fuqarolik kodeksi",
    code: '21.12.1995, 1-qism',
    url: 'https://lex.uz/docs/-111189',
    articles: [
      {
        num: 'Bitimlarning yozma shakli',
        text: "Elektron aloqa vositalari orqali ifodalangan iroda, agar tomonlarni aniq belgilash mumkin bo'lsa, yozma shaklga tenglashtiriladi.",
      },
    ],
  },
]
</script>

<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-[60] flex items-center justify-center p-2 sm:p-4 bg-black/60 backdrop-blur-xs animate-in fade-in duration-200"
    @click.self="emit('close')"
  >
    <div
      class="bg-white dark:bg-zinc-900 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[88vh] flex flex-col overflow-hidden border border-zinc-200 dark:border-zinc-800"
    >
      <!-- Header -->
      <div class="px-6 py-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between bg-zinc-50 dark:bg-zinc-850">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-blue-100 dark:bg-blue-950/60 text-blue-600 dark:text-blue-400 flex items-center justify-center">
            <Scale class="w-4 h-4" />
          </div>
          <div>
            <h3 class="text-sm font-bold text-zinc-900 dark:text-white">
              Elektron imzoning yuridik asoslari
            </h3>
            <p class="text-xs text-zinc-500">
              Telefon, planshet va kompyuterda qo'yilgan imzoni tartibga soluvchi qonun moddalari
            </p>
          </div>
        </div>
        <button
          type="button"
          @click="emit('close')"
          class="p-2 rounded-xl text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors cursor-pointer"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <div v-for="law in laws" :key="law.title" class="space-y-3">
          <div class="flex items-start justify-between gap-3">
            <div>
              <h4 class="text-sm font-bold text-black dark:text-white leading-snug">
                {{ law.title }}
              </h4>
              <p class="text-[11px] text-zinc-500 font-medium">{{ law.code }}</p>
            </div>
            <a
              :href="law.url"
              target="_blank"
              rel="noopener noreferrer"
              class="shrink-0 inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-zinc-300 dark:border-zinc-700 text-[11px] font-bold text-zinc-700 dark:text-zinc-300 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
            >
              lex.uz <ExternalLink class="w-3 h-3" />
            </a>
          </div>

          <div class="space-y-2.5 pl-3 border-l-2 border-zinc-200 dark:border-zinc-800">
            <div v-for="art in law.articles" :key="art.num">
              <p class="text-xs font-bold text-zinc-800 dark:text-zinc-200">{{ art.num }}</p>
              <p class="text-xs text-zinc-600 dark:text-zinc-400 leading-relaxed">{{ art.text }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 border-t border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 flex justify-end">
        <button
          type="button"
          @click="emit('close')"
          class="px-6 py-2.5 rounded-xl bg-black hover:bg-zinc-800 dark:bg-white dark:hover:bg-zinc-200 text-white dark:text-black text-xs font-bold shadow-xs transition-all cursor-pointer"
        >
          Tushunarli
        </button>
      </div>
    </div>
  </div>
</template>
