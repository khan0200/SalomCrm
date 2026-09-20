export interface CancellationReasonOption {
  number: string
  korean: string
  uzbek: string
  english: string
  russian?: string
}

/**
 * Official 11 refusal / cancellation reasons established by the Embassy of the
 * Republic of Korea (거부사유 / Viza inkor etilishi sababi / visa.go.kr 불허사유).
 */
export const CANCELLATION_REASONS: CancellationReasonOption[] = [
  {
    number: '1',
    korean: '귀하는 유효한 여권 등을 소지하지 않았거나, 필요한 서류를 제출하지 않았습니다.',
    uzbek: 'Siz yaroqli pasportga ega emassiz yoki zaruriy hujjatlarni topshirmagansiz.',
    english: 'You do not possess a valid passport or failed to submit required documents.',
    russian: 'У вас отсутствует действительный паспорт / проездной документ или не представлены необходимые документы.'
  },
  {
    number: '2',
    korean: '귀하는 출입국관리법 제11조(입국의 금지) 제1항에 해당합니다.',
    uzbek: "Migratsiya qonunining 11-bo'lim (davlatga kirishga oid taqiq) 1-bandiga sizning taalluqliligingiz bor.",
    english: 'You fall under Article 11, Paragraph 1 (Entry Prohibition) of the Immigration Act.',
    russian: 'Вы попадаете под 11-ю статью 1 параграфа «Закона об иммиграционном контроле» (запрет на въезд).'
  },
  {
    number: '3',
    korean: '귀하는 과거 대한민국 체류 중 대한민국 법률을 위반한 사실이 있습니다.',
    uzbek: 'Koreya Respublikasiga avvalgi tashrifingizda Koreya Respublikasining qonunchiligini buzgansiz.',
    english: 'You have a record of violating the laws of the Republic of Korea during your previous stay.',
    russian: 'Вы нарушали законодательство Республики Корея в период предыдущих пребываниях в Р.К.'
  },
  {
    number: '4',
    korean: '귀하의 입국목적을 소명할 충분한 서류를 제출하지 않았습니다.',
    uzbek: 'Tashrif maqsadingizni yoritib berishda yetarli hujjat(lar)ni topshirmagansiz.',
    english: 'You failed to submit sufficient documents to prove the purpose of entry.',
    russian: 'Вы не предоставили дополнительных документов, подтверждающих цель вашей поездки в Р.К.'
  },
  {
    number: '5',
    korean: '귀하는 대한민국 출입국관리법 제10조에 따른 체류자격의 요건을 충족시키지 못했습니다.',
    uzbek: "Tashrif maqsadingiz Koreya Respublikasining migratsiya qonuni 10-bo'limida keltirilgan Koreya Respublikasida istiqomat qilishga oid talablarga mos kelmaydi.",
    english: 'You failed to meet the requirements for the status of stay pursuant to Article 10 of the Immigration Act.',
    russian: 'Цель вашей поездки не соответствует условиям статуса пребывания, утвержденным Иммиграционным законодательством Республики Корея.'
  },
  {
    number: '6',
    korean: '귀하가 제출한 서류는 진정성이 확인되지 않습니다.',
    uzbek: 'Siz topshirgan hujjatlarning haqiqiyligi tasdiqlanmadi (soxtalashtirilgan yoki noaniq).',
    english: 'The authenticity of the documents you submitted could not be verified.',
    russian: 'Невозможно было установить подлинность предоставленных вами документов.'
  },
  {
    number: '7',
    korean: '귀하의 입국목적을 충분히 소명하지 못하였습니다.',
    uzbek: "Siz tashrif maqsadingizni to'liq yoritib bera olmagansiz.",
    english: 'You failed to sufficiently explain the purpose of your entry.',
    russian: 'Цель вашей поездки не достаточно обоснована.'
  },
  {
    number: '8',
    korean: '가족관계 및 경제적 여건이 예정한 체류기간 내에 귀국할 것임을 소명하지 못하였습니다.(소득·자산 불충분 등)',
    uzbek: "Siz belgilangan istiqomat muddatida o'z davlatingizga qaytib kela olishingizni tasdiqlab bera olmagansiz (daromad/sarmoya, ota-ona daromadi yetarli emasligi sababli).",
    english: 'You failed to demonstrate, through your family ties and economic circumstances, that you would return home within the intended period of stay.',
    russian: 'Ваше семейное и финансовое положение недостаточно убедительны, чтобы вы смогли вернуться обратно на родину по окончании периода пребывания.'
  },
  {
    number: '9',
    korean: '귀하를 초청한 자의 초청자격이 부적격합니다.',
    uzbek: "Sizni taklif qiluvchining taklif qilish vakolati to'liq emas.",
    english: 'The inviter lacks the qualification or competence to invite.',
    russian: 'Приглашающая сторона недостаточно компетентна в оформлении пригласительного письма.'
  },
  {
    number: '10',
    korean: '귀하를 초청한 자와의 관계를 입증하지 못했습니다.',
    uzbek: 'Siz taklif qiluvchi bilan aloqadorligingizni asoslab bera olmagansiz.',
    english: 'You failed to substantiate your relationship with the inviter.',
    russian: 'Вы не смогли подтвердить отношение с приглашающей стороной.'
  },
  {
    number: '11',
    korean: '기타',
    uzbek: 'Boshqa sabablar (qo\'shimcha izohda ko\'rsatiladi).',
    english: 'Other (details specified in note).',
    russian: 'Другое.'
  }
]

export function getReasonByNumber(num: string | number | undefined | null): CancellationReasonOption | undefined {
  if (num === undefined || num === null) return undefined
  const s = String(num).trim()
  return CANCELLATION_REASONS.find(r => r.number === s)
}

export function getReasonUzbek(num: string | number | undefined | null): string {
  const reason = getReasonByNumber(num)
  return reason ? reason.uzbek : ''
}

