export interface CancellationReasonOption {
  number: string
  korean: string
  uzbek: string
  english: string
}

/**
 * Standard refusal / cancellation reasons established by the Ministry of Justice
 * and Korean diplomatic missions (visa.go.kr 불허사유).
 */
export const CANCELLATION_REASONS: CancellationReasonOption[] = [
  {
    number: '1',
    korean: '유효한 여권을 소지하지 않았거나, 입국목적 및 체류기간을 소명하지 못함',
    uzbek: 'Amaldagi pasport mavjud emas yoki kirish maqsadi va qolish muddati asoslanmagan',
    english: 'Does not hold a valid passport or failed to clarify the purpose and period of stay'
  },
  {
    number: '2',
    korean: '출입국관리법 제11조(입국의 금지 등) 각 호의 어느 하나에 해당함',
    uzbek: 'Immigratsiya qonunining 11-moddasi (kirishni taqiqlash) bandlariga to\'g\'ri keladi',
    english: 'Falls under any subparagraph of Article 11 (Entry Prohibition) of the Immigration Act'
  },
  {
    number: '3',
    korean: '과거 대한민국 법률을 위반한 사실이 있음',
    uzbek: 'Ilgari Koreya Respublikasi qonunlarini buzganlik holati mavjud',
    english: 'Has a history of violating the laws of the Republic of Korea'
  },
  {
    number: '4',
    korean: '입국목적을 소명할 수 있는 자료를 제출하지 못함',
    uzbek: 'Kirish maqsadini tasdiqlovchi yetarli asos/hujjatlar taqdim etilmagan',
    english: 'Failed to submit materials that prove the purpose of entry'
  },
  {
    number: '5',
    korean: '대한민국 체류 중 필요한 경비 및 귀국경비 부담 능력이 없음',
    uzbek: 'Koreyada yashash, ta\'lim va vataniga qaytish xarajatlarini qoplash mablag\'i yetarli emas',
    english: 'Lacks the financial ability to bear living expenses during stay and return costs'
  },
  {
    number: '6',
    korean: '초청자(가족, 대학 등)와의 관계를 소명하지 못함',
    uzbek: 'Taklif qiluvchi muassasa (universitet) yoki shaxs bilan aloqasi asoslanmagan',
    english: 'Failed to substantiate relationship with the inviter (family, university, etc.)'
  },
  {
    number: '7',
    korean: '제출한 서류의 진위가 불분명하거나 위·변조됨',
    uzbek: 'Taqdim etilgan hujjatlarning haqiqiyligi noaniq yoki soxtalashtirilgan/o\'zgartirilgan',
    english: 'The authenticity of submitted documents is unclear, forged, or altered'
  },
  {
    number: '8',
    korean: '입국목적에 부합하는 체류자격 요건을 갖추지 못함',
    uzbek: 'Kirish maqsadiga mos keluvchi viza toifasi va talablariga javob bermaydi',
    english: 'Does not meet the eligibility requirements for the status of stay corresponding to purpose'
  },
  {
    number: '9',
    korean: '과거 불법체류 등 체류질서를 위반할 우려가 상당함',
    uzbek: 'Ilgari noqonuniy qolish yoki immigratsiya tartibini buzish xavfi mavjud',
    english: 'High risk of illegal stay or violation of immigration order based on past history'
  },
  {
    number: '10',
    korean: '기타 사유',
    uzbek: 'Boshqa rasmiy sabablar',
    english: 'Other official refusal reasons'
  }
]
