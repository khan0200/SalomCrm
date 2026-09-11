<script setup lang="ts">
import { ref, computed } from 'vue'
import {
  Copy,
  Check,
  Search,
  FileText,
  User,
  Phone,
  Users,
  GraduationCap,
  Award,
  Bookmark,
  Folder,
  Tag,
  Sparkles,
  HelpCircle,
  LayoutGrid,
  List,
  CheckCircle2,
  ExternalLink
} from 'lucide-vue-next'
import { wordFillApi, type WordPlaceholderField } from '@/api/wordFill'

const props = withDefaults(
  defineProps<{
    isCollapsible?: boolean
    defaultCollapsed?: boolean
  }>(),
  {
    isCollapsible: true,
    defaultCollapsed: false,
  }
)

// ─── Pre-loaded Master Catalog (Instant 0ms availability) ─────────────────────
const DEFAULT_CATALOG: WordPlaceholderField[] = [
  // Personal
  {
    key: 'full_name',
    label: 'To\'liq ism (Full Name / F.I.SH)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{fullname}}',
    aliases: ['{{full_name}}', '{{name}}', '{{studentname}}'],
    sample: 'ABDUVOIDOV KHAYITALI',
    description: 'Talabaning pasportdagi to\'liq ismi va familiyasi',
  },
  {
    key: 'first_name',
    label: 'Ism (First Name)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{firstname}}',
    aliases: ['{{first_name}}'],
    sample: 'KHAYITALI',
    description: 'Talabaning ismi',
  },
  {
    key: 'last_name',
    label: 'Familiya (Last Name)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{lastname}}',
    aliases: ['{{last_name}}'],
    sample: 'ABDUVOIDOV',
    description: 'Talabaning familiyasi',
  },
  {
    key: 'korean_name',
    label: 'Koreyscha ism (국문이름 / 한글성명)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{koreanname}}',
    aliases: ['{{korean_name}}'],
    sample: '압두보이도프 하이탈리',
    description: 'Talabaning hangeuldagi koreyscha ismi',
  },
  {
    key: 'gender',
    label: 'Jinsi (Gender / Sex / 성별)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{gender}}',
    aliases: ['{{sex}}'],
    sample: 'MALE / 남',
    description: 'Talabaning jinsi (Erkak / Ayol yoki MALE / FEMALE)',
  },
  {
    key: 'birthday',
    label: 'Tug\'ilgan sana (Birth Date / 생년월일)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{dateofbirth}}',
    aliases: ['{{birthday}}', '{{birthdate}}', '{{birth_date}}', '{{dob}}'],
    sample: '2002-05-14',
    description: 'Tug\'ilgan sana (standart YYYY-MM-DD yoki YYYY.MM.DD)',
  },
  {
    key: 'nationality',
    label: 'Fuqaroligi (Nationality / 국적)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{nationality}}',
    aliases: ['{{citizenship}}', '{{country}}'],
    sample: 'UZBEKISTAN',
    description: 'Fuqarolik davlati',
  },
  {
    key: 'id',
    label: 'Talaba ID (Student ID / 학번)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{id}}',
    aliases: ['{{studentid}}', '{{student_id}}'],
    sample: '1024',
    description: 'CRM tizimidagi unikal talaba ID raqami',
  },
  {
    key: 'address',
    label: 'To\'liq manzil (Full Address / 주소)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{address}}',
    aliases: ['{{fulladdress}}', '{{full_address}}'],
    sample: 'Andijon shahar, Bobur shoh ko\'chasi 15-uy',
    description: 'Talabaning ro\'yxatdan o\'tgan to\'liq yashash manzili',
  },
  {
    key: 'address_city',
    label: 'Shahar / Tuman (City / District / 시·군·구)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{city}}',
    aliases: ['{{addresscity}}', '{{address_city}}', '{{district}}'],
    sample: 'Andijon',
    description: 'Manzildan ajratib olingan shahar yoki tuman',
  },
  {
    key: 'address_state',
    label: 'Viloyat / Region (State / Province / 도·시)',
    category: 'personal',
    category_label: 'Shaxsiy ma\'lumotlar',
    primary_tag: '{{state}}',
    aliases: ['{{addressstate}}', '{{address_state}}', '{{region}}'],
    sample: 'Andijon',
    description: 'Manzildan ajratib olingan viloyat',
  },

  // Passport
  {
    key: 'passport',
    label: 'Pasport raqami (Passport No / 여권번호)',
    category: 'passport',
    category_label: 'Pasport ma\'lumotlari',
    primary_tag: '{{passport}}',
    aliases: ['{{passportno}}', '{{passport_no}}', '{{passportnumber}}'],
    sample: 'FA1234567',
    description: 'Xorijga chiqish pasportining seriya va raqami',
  },
  {
    key: 'passport_issue_date',
    label: 'Pasport berilgan sana (Issue Date / 발급일)',
    category: 'passport',
    category_label: 'Pasport ma\'lumotlari',
    primary_tag: '{{passportissuedate}}',
    aliases: ['{{passport_issue_date}}', '{{passportissue}}'],
    sample: '2021-06-10',
    description: 'Pasport berilgan sana',
  },
  {
    key: 'passport_expire_date',
    label: 'Pasport amal qilish muddati (Expiry Date / 만료일)',
    category: 'passport',
    category_label: 'Pasport ma\'lumotlari',
    primary_tag: '{{passportexpiredate}}',
    aliases: ['{{passport_expire_date}}', '{{passportexpire}}'],
    sample: '2031-06-09',
    description: 'Pasportning tugash / amal qilish muddati',
  },

  // Contacts
  {
    key: 'phone1',
    label: 'Asosiy telefon (Phone 1 / 연락처)',
    category: 'contacts',
    category_label: 'Aloqa vositalari',
    primary_tag: '{{phone1}}',
    aliases: ['{{phone}}', '{{telephone}}', '{{phonenumber}}'],
    sample: '+998 90 123 45 67',
    description: 'Talabaning asosiy aloqa telefoni',
  },
  {
    key: 'phone2',
    label: 'Qo\'shimcha telefon (Phone 2 / 비상연락처)',
    category: 'contacts',
    category_label: 'Aloqa vositalari',
    primary_tag: '{{phone2}}',
    aliases: ['{{cellphone}}', '{{additionalphone}}', '{{mobile}}'],
    sample: '+998 91 987 65 43',
    description: 'Qo\'shimcha yoki favqulodda aloqa telefoni',
  },
  {
    key: 'email',
    label: 'Email manzil (Email / 이메일)',
    category: 'contacts',
    category_label: 'Aloqa vositalari',
    primary_tag: '{{email}}',
    aliases: ['{{mail}}', '{{e-mail}}'],
    sample: 'student@gmail.com',
    description: 'Elektron pochta manzili',
  },
  {
    key: 'telegram_username',
    label: 'Telegram username',
    category: 'contacts',
    category_label: 'Aloqa vositalari',
    primary_tag: '{{telegram}}',
    aliases: ['{{telegram_username}}', '{{telegramusername}}'],
    sample: '@student_crm',
    description: 'Talabaning telegram foydalanuvchi nomi',
  },

  // Parents
  {
    key: 'father_name',
    label: 'Otasining ismi (Father\'s Name / 부 성명)',
    category: 'parents',
    category_label: 'Ota-ona ma\'lumotlari',
    primary_tag: '{{fatherfullname}}',
    aliases: ['{{fathername}}', '{{father_name}}', '{{father_fullname}}'],
    sample: 'ALIEV BOTIR',
    description: 'Otasining to\'liq ismi va familiyasi',
  },
  {
    key: 'father_phone',
    label: 'Otasining telefoni (Father\'s Phone / 부 연락처)',
    category: 'parents',
    category_label: 'Ota-ona ma\'lumotlari',
    primary_tag: '{{fatherphone}}',
    aliases: ['{{father_phone}}', '{{fathertelephone}}'],
    sample: '+998 90 111 22 33',
    description: 'Otasining telefon raqami',
  },
  {
    key: 'father_job',
    label: 'Otasining ish joyi (Father\'s Job / 부 직업)',
    category: 'parents',
    category_label: 'Ota-ona ma\'lumotlari',
    primary_tag: '{{fatherjob}}',
    aliases: ['{{father_job}}', '{{fatherwork}}', '{{fatheroccupation}}'],
    sample: 'Tadbirkor / Tadbirkorlik',
    description: 'Otasining kasbi yoki ish joyi',
  },
  {
    key: 'mother_name',
    label: 'Onasining ismi (Mother\'s Name / 모 성명)',
    category: 'parents',
    category_label: 'Ota-ona ma\'lumotlari',
    primary_tag: '{{motherfullname}}',
    aliases: ['{{mothername}}', '{{mother_name}}', '{{mother_fullname}}'],
    sample: 'ALIEVA MARHABO',
    description: 'Onasining to\'liq ismi va familiyasi',
  },
  {
    key: 'mother_phone',
    label: 'Onasining telefoni (Mother\'s Phone / 모 연락처)',
    category: 'parents',
    category_label: 'Ota-ona ma\'lumotlari',
    primary_tag: '{{motherphone}}',
    aliases: ['{{mother_phone}}', '{{mothertelephone}}'],
    sample: '+998 90 444 55 66',
    description: 'Onasining telefon raqami',
  },
  {
    key: 'mother_job',
    label: 'Onasining ish joyi (Mother\'s Job / 모 직업)',
    category: 'parents',
    category_label: 'Ota-ona ma\'lumotlari',
    primary_tag: '{{motherjob}}',
    aliases: ['{{mother_job}}', '{{motherwork}}', '{{motheroccupation}}'],
    sample: 'O\'qituvchi',
    description: 'Onasining kasbi yoki ish joyi',
  },

  // Education
  {
    key: 'educational_background',
    label: 'Ta\'lim darajasi (Educational Background / 최종학력)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{educationalbackground}}',
    aliases: ['{{educational_background}}', '{{educationlevel}}', '{{education_level}}'],
    sample: 'HIGH SCHOOL',
    description: 'Bitirgan ta\'lim darajasi (Maktab / Kollej / Bakalavr)',
  },
  {
    key: 'final_school_name',
    label: 'Bitirgan maktab/universitet (Previous School / 출신학교명)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{finalschoolname}}',
    aliases: ['{{final_school_name}}', '{{previousschool}}', '{{schoolname}}'],
    sample: '5-sonli umumiy o\'rta ta\'lim maktabi',
    description: 'Oldin o\'qigan yoki bitirgan ta\'lim muassasasi',
  },
  {
    key: 'level',
    label: 'Topshirayotgan bosqich (Target Degree / 지원과정)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{level}}',
    aliases: ['{{targetlevel}}', '{{target_degree}}', '{{degree}}'],
    sample: 'BACHELOR',
    description: 'Ariza topshirilayotgan ta\'lim darajasi',
  },
  {
    key: 'major',
    label: 'Yo\'nalish / Mutaxassislik (Major / 전공 / 학과)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{major}}',
    aliases: ['{{applyingmajor}}', '{{specialty}}'],
    sample: 'Business Administration',
    description: 'Topshirilayotgan fakultet yoki mutaxassislik',
  },
  {
    key: 'date_of_entry',
    label: 'O\'qishga kirgan sana (Date of Entry / 입학일자)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{dateofentry}}',
    aliases: ['{{date_of_entry}}', '{{entrydate}}'],
    sample: '2012-09-02',
    description: 'Maktab yoki kollejga kirgan sana',
  },
  {
    key: 'date_of_graduation',
    label: 'Bitirgan sana (Date of Graduation / 졸업일자)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{dateofgraduate}}',
    aliases: ['{{dateofgraduation}}', '{{date_of_graduation}}', '{{graduationdate}}'],
    sample: '2023-05-25',
    description: 'Maktab yoki kollejni bitirgan sana',
  },
  {
    key: 'graduation_expected',
    label: 'Bitirish holati (Graduation Expected / 졸업예정)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{graduationexpected}}',
    aliases: ['{{graduation_expected}}'],
    sample: 'Bitirgan (Graduated)',
    description: 'Bitirgan yoki hali bitirish arafasida ekanligi',
  },
  {
    key: 'degree_no',
    label: 'Diplom / Attestat raqami (Degree / Diploma No / 학위번호)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{degreeno}}',
    aliases: ['{{degree_no}}', '{{diplomano}}'],
    sample: 'UM1234567',
    description: 'Attestat yoki diplom hujjati raqami',
  },
  {
    key: 'gpa',
    label: 'GPA / O\'rtacha baho (GPA / 성적)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{gpa}}',
    aliases: ['{{gpasystem}}'],
    sample: '4.8',
    description: 'Attestat yoki diplomdagi o\'rtacha baho',
  },
  {
    key: 'school_address',
    label: 'Maktab manzili (School Address / 학교 주소)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{schooladdress}}',
    aliases: ['{{school_address}}'],
    sample: 'Andijon shahar, Mustaqillik ko\'chasi 4',
    description: 'Bitirgan maktab yoki kollej manzili',
  },
  {
    key: 'school_phone',
    label: 'Maktab telefoni (School Phone / 학교 연락처)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{schoolphone}}',
    aliases: ['{{school_phone}}'],
    sample: '+998 74 222 33 44',
    description: 'Bitirgan maktab telefon raqami',
  },
  {
    key: 'school_email',
    label: 'Maktab emaili (School Email / 학교 이메일)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{schoolemail}}',
    aliases: ['{{school_email}}'],
    sample: 'school5@mail.uz',
    description: 'Bitirgan maktab elektron pochtasi',
  },
  {
    key: 'school_website',
    label: 'Maktab veb-sayti (School Website / 학교 웹사이트)',
    category: 'education',
    category_label: 'Ta\'lim ma\'lumotlari',
    primary_tag: '{{schoolwebsite}}',
    aliases: ['{{school_website}}'],
    sample: 'www.school5.uz',
    description: 'Bitirgan maktab veb-sayti',
  },

  // Certificates
  {
    key: 'language_certificate',
    label: '1-Til sertifikati turi (TOPIK / IELTS / SKA)',
    category: 'certificates',
    category_label: 'Til sertifikatlari',
    primary_tag: '{{languagecertificate}}',
    aliases: ['{{language_certificate}}', '{{certificate}}'],
    sample: 'IELTS',
    description: 'Birinchi til sertifikati turi',
  },
  {
    key: 'certificate_score',
    label: '1-Sertifikat bali (Score / 급수)',
    category: 'certificates',
    category_label: 'Til sertifikatlari',
    primary_tag: '{{certificatescore}}',
    aliases: ['{{certificate_score}}', '{{score}}'],
    sample: '6.5',
    description: 'Til sertifikati bali yoki darajasi',
  },
  {
    key: 'certificate_test_date',
    label: '1-Sertifikat topshirilgan sana (Test Date / 응시일)',
    category: 'certificates',
    category_label: 'Til sertifikatlari',
    primary_tag: '{{certificatetestdate}}',
    aliases: ['{{certificate_test_date}}'],
    sample: '2024-01-15',
    description: 'Imtihon topshirilgan sana',
  },
  {
    key: 'certificate_valid_date',
    label: '1-Sertifikat amal qilish muddati (Valid Date / 유효기간)',
    category: 'certificates',
    category_label: 'Til sertifikatlari',
    primary_tag: '{{certificatevaliddate}}',
    aliases: ['{{certificate_valid_date}}'],
    sample: '2026-01-15',
    description: 'Sertifikatning tugash sanasi',
  },

  // University
  {
    key: 'university_1',
    label: '1-Universitet (Applying University 1 / 지망대학 1)',
    category: 'university',
    category_label: 'Universitet tanlovlari',
    primary_tag: '{{university1}}',
    aliases: ['{{university}}', '{{university_1}}'],
    sample: 'Sejong University',
    description: 'Birinchi tanlangan universitet nomi',
  },
  {
    key: 'university_1_major',
    label: '1-Universitet yo\'nalishi (Major 1 / 지망학과 1)',
    category: 'university',
    category_label: 'Universitet tanlovlari',
    primary_tag: '{{university1major}}',
    aliases: ['{{university_1_major}}'],
    sample: 'Computer Science and Engineering',
    description: '1-universitetdagi tanlangan yo\'nalish',
  },
  {
    key: 'university_1_status',
    label: '1-Universitet holati (University 1 Status)',
    category: 'university',
    category_label: 'Universitet tanlovlari',
    primary_tag: '{{university1status}}',
    aliases: ['{{university_1_status}}'],
    sample: 'Submitted',
    description: '1-universitet arizasining holati',
  },
  {
    key: 'university_2',
    label: '2-Universitet (Applying University 2 / 지망대학 2)',
    category: 'university',
    category_label: 'Universitet tanlovlari',
    primary_tag: '{{university2}}',
    aliases: ['{{university_2}}'],
    sample: 'Dongguk University',
    description: 'Ikkinchi tanlangan universitet nomi',
  },
  {
    key: 'university_2_major',
    label: '2-Universitet yo\'nalishi (Major 2 / 지망학과 2)',
    category: 'university',
    category_label: 'Universitet tanlovlari',
    primary_tag: '{{university2major}}',
    aliases: ['{{university_2_major}}'],
    sample: 'Global Business',
    description: '2-universitetdagi tanlangan yo\'nalish',
  },

  // Management / CRM
  {
    key: 'tariff',
    label: 'Tarif (Tariff / Standart, Premium, E-Visa)',
    category: 'management',
    category_label: 'Boshqa / CRM',
    primary_tag: '{{tariff}}',
    aliases: [],
    sample: 'STANDART',
    description: 'Talabaning agentlikdagi xizmat tarifi',
  },
  {
    key: 'student_group',
    label: 'Guruh (Student Group)',
    category: 'management',
    category_label: 'Boshqa / CRM',
    primary_tag: '{{studentgroup}}',
    aliases: ['{{student_group}}'],
    sample: 'Guruh 14',
    description: 'Talabaning guruhi',
  },
  {
    key: 'coordinator',
    label: 'Koordinator (Coordinator)',
    category: 'management',
    category_label: 'Boshqa / CRM',
    primary_tag: '{{coordinator}}',
    aliases: [],
    sample: 'Rustamov Aziz',
    description: 'Biriktirilgan koordinator mas\'ul xodimi',
  },
  {
    key: 'office',
    label: 'Ofis / Filial (Office)',
    category: 'management',
    category_label: 'Boshqa / CRM',
    primary_tag: '{{office}}',
    aliases: [],
    sample: 'ANDIJON OFFIS',
    description: 'Talaba ro\'yxatga olingan ofis / filial',
  },

  // System
  {
    key: 'today_date',
    label: 'Bugungi sana (Today / Application Date / 신청일)',
    category: 'system',
    category_label: 'Tizim / Sanalar',
    primary_tag: '{{today}}',
    aliases: ['{{todaydate}}', '{{today_date}}', '{{date}}'],
    sample: '2026-09-12',
    description: 'Hujjat to\'ldirilayotgan joriy sana',
  },
]

// ─── University App Form "Most Common" Fields ───────────────────────────────
// Excludes CRM-internal fields: Student ID (universities don't ask for it),
// Telegram, secondary/tertiary certificates (only cert 1), secondary universities
// (universities 2-5), and CRM management fields (tariff, group, coordinator, etc.)
const COMMON_FIELD_KEYS = new Set([
  // Personal
  'full_name',
  'first_name',
  'last_name',
  'korean_name',
  'gender',
  'birthday',
  'nationality',
  'address',
  'address_city',
  'address_state',
  // Passport
  'passport',
  'passport_issue_date',
  'passport_expire_date',
  // Contacts
  'phone1',
  'phone2',
  'email',
  // Parents
  'father_name',
  'father_phone',
  'father_job',
  'mother_name',
  'mother_phone',
  'mother_job',
  // Education
  'educational_background',
  'final_school_name',
  'level',
  'major',
  'date_of_entry',
  'date_of_graduation',
  'degree_no',
  'gpa',
  'school_address',
  'school_phone',
  // Certificates (only primary certificate 1)
  'language_certificate',
  'certificate_score',
  'certificate_test_date',
  'certificate_valid_date',
  // University (only target University 1)
  'university_1',
  'university_1_major',
  // System
  'today_date',
])

DEFAULT_CATALOG.forEach(item => {
  item.is_common = COMMON_FIELD_KEYS.has(item.key)
})

// ─── Component State ────────────────────────────────────────────────────────
const catalog = ref<WordPlaceholderField[]>(DEFAULT_CATALOG)
const searchQuery = ref('')
const selectedCategory = ref<string>('common') // Default is 'common' (Most Common)!
const isCollapsed = ref(props.defaultCollapsed)
const copiedTag = ref<string | null>(null)
let copyTimeout: any = null

const getCategoryBadgeClass = (category: string) => {
  switch (category) {
    case 'personal':
      return 'bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-800'
    case 'passport':
      return 'bg-violet-50 dark:bg-violet-950/60 text-violet-700 dark:text-violet-300 border border-violet-200 dark:border-violet-800'
    case 'contacts':
      return 'bg-emerald-50 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800'
    case 'parents':
      return 'bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800'
    case 'education':
      return 'bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800'
    case 'certificates':
      return 'bg-rose-50 dark:bg-rose-950/60 text-rose-700 dark:text-rose-300 border border-rose-200 dark:border-rose-800'
    case 'university':
      return 'bg-cyan-50 dark:bg-cyan-950/60 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800'
    default:
      return 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 border border-zinc-200 dark:border-zinc-700'
  }
}

// Load from server if available to ensure live parity
wordFillApi.getPlaceholderCatalog()
  .then(res => {
    if (res && res.length > 0) {
      catalog.value = res.map(item => ({
        ...item,
        is_common: item.is_common ?? COMMON_FIELD_KEYS.has(item.key),
      }))
    }
  })
  .catch(() => {
    // Fallback to built-in list silently
  })

// ─── Categories & Icons ─────────────────────────────────────────────────────
const CATEGORIES = [
  { id: 'common', label: '🔥 Most Common (Asosiy)', icon: Sparkles },
  { id: 'personal', label: 'Shaxsiy', icon: User },
  { id: 'passport', label: 'Pasport', icon: FileText },
  { id: 'contacts', label: 'Aloqa', icon: Phone },
  { id: 'parents', label: 'Ota-ona', icon: Users },
  { id: 'education', label: 'Ta\'lim', icon: GraduationCap },
  { id: 'certificates', label: 'Til sertifikati', icon: Award },
  { id: 'university', label: 'Universitet', icon: Bookmark },
  { id: 'all', label: 'Barcha maydonlar', icon: LayoutGrid },
]

const getCategoryCount = (catId: string) => {
  if (catId === 'common') return catalog.value.filter(item => item.is_common).length
  if (catId === 'all') return catalog.value.length
  return catalog.value.filter(item => item.category === catId).length
}

// ─── Filtering ──────────────────────────────────────────────────────────────
const filteredFields = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return catalog.value.filter(item => {
    if (selectedCategory.value === 'common') {
      if (!item.is_common) return false
    } else if (selectedCategory.value !== 'all') {
      if (item.category !== selectedCategory.value) return false
    }

    if (!q) return true

    const textToSearch = [
      item.label,
      item.key,
      item.primary_tag,
      item.description,
      item.sample,
      ...(item.aliases || [])
    ].join(' ').toLowerCase()

    return textToSearch.includes(q)
  })
})

// ─── Quick Copy Action ──────────────────────────────────────────────────────
const copyToClipboard = async (tag: string) => {
  let copied = false
  try {
    if (navigator?.clipboard?.writeText) {
      await navigator.clipboard.writeText(tag)
      copied = true
    }
  } catch (err) {
    console.warn('navigator.clipboard failed, attempting textarea fallback', err)
  }

  if (!copied) {
    try {
      const el = document.createElement('textarea')
      el.value = tag
      el.setAttribute('readonly', '')
      el.style.position = 'fixed'
      el.style.left = '-9999px'
      el.style.top = '-9999px'
      document.body.appendChild(el)
      el.select()
      copied = document.execCommand('copy')
      document.body.removeChild(el)
    } catch (fallbackErr) {
      console.error('Copy fallback failed:', fallbackErr)
    }
  }

  copiedTag.value = tag
  clearTimeout(copyTimeout)
  copyTimeout = setTimeout(() => {
    if (copiedTag.value === tag) {
      copiedTag.value = null
    }
  }, 2000)
}

// ─── Download Example File ──────────────────────────────────────────────────
const isDownloadingExample = ref(false)
const downloadExampleTemplate = async () => {
  isDownloadingExample.value = true
  try {
    // Try public static file first for speed
    const link = document.createElement('a')
    link.href = '/APPFORM.docx'
    link.setAttribute('download', 'APPFORM.docx')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch {
    try {
      const blob = await wordFillApi.downloadExampleTemplate()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'APPFORM.docx'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (apiErr) {
      alert("Namuna faylni yuklab olishda xatolik yuz berdi")
    }
  } finally {
    isDownloadingExample.value = false
  }
}
</script>

<template>
  <div class="bg-white dark:bg-[#111315] border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-sm p-4 sm:p-5 space-y-4 transition-all">
    <!-- Search & Controls Bar -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
      <!-- Prominent Search input -->
      <div class="relative flex-1">
        <Search class="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-blue-600 dark:text-blue-400 pointer-events-none" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Maydon nomi yoki teg bo'yicha qidirish (masalan: fullname, pasport, telefon, sana, manzil)..."
          class="w-full pl-12 pr-11 py-3 text-sm font-medium rounded-2xl bg-zinc-50/90 dark:bg-zinc-900/90 border-2 border-zinc-200 dark:border-zinc-700 hover:border-blue-400/60 dark:hover:border-blue-500/50 focus:border-blue-600 dark:focus:border-blue-500 focus:bg-white dark:focus:bg-[#151719] text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 shadow-xs focus:outline-none focus:ring-4 focus:ring-blue-500/15 transition-all"
        />
        <button
          v-if="searchQuery"
          type="button"
          @click="searchQuery = ''"
          class="absolute right-3.5 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center rounded-full bg-zinc-200/80 hover:bg-zinc-300 dark:bg-zinc-700 hover:dark:bg-zinc-600 text-zinc-600 dark:text-zinc-300 text-xs font-bold cursor-pointer transition-all"
          title="Qidiruvni tozalash"
        >
          ✕
        </button>
      </div>

      <!-- Count Badge -->
      <div class="flex items-center justify-between sm:justify-end gap-2 px-4 py-3 rounded-2xl bg-zinc-100/80 dark:bg-zinc-800/60 border border-zinc-200/70 dark:border-zinc-700/60 shrink-0">
        <span class="text-xs text-zinc-500 dark:text-zinc-400 font-medium">Ko'rsatilmoqda:</span>
        <span class="px-2.5 py-0.5 rounded-lg bg-blue-600 text-white font-bold text-xs shadow-xs">
          {{ filteredFields.length }} ta
        </span>
      </div>
    </div>

      <!-- Category Filter Pills -->
      <div class="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
        <button
          v-for="cat in CATEGORIES"
          :key="cat.id"
          type="button"
          @click="selectedCategory = cat.id"
          class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer"
          :class="[
            selectedCategory === cat.id
              ? 'bg-blue-600 text-white shadow-xs font-bold'
              : 'bg-zinc-100 dark:bg-zinc-800/80 hover:bg-zinc-200 dark:hover:bg-zinc-700/80 text-zinc-700 dark:text-zinc-300'
          ]"
        >
          <component :is="cat.icon" class="w-3.5 h-3.5" />
          <span>{{ cat.label }}</span>
          <span
            class="px-1.5 py-0.2 rounded-full text-[10px]"
            :class="selectedCategory === cat.id ? 'bg-white/20 text-white' : 'bg-zinc-200 dark:bg-zinc-700 text-zinc-500 dark:text-zinc-400'"
          >
            {{ getCategoryCount(cat.id) }}
          </span>
        </button>
      </div>

      <!-- Tag Table View (Only & Primary Presentation) -->
      <div class="overflow-x-auto border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-xs bg-white dark:bg-[#111315]">
        <table class="w-full text-left border-collapse text-xs">
          <thead class="bg-zinc-50/90 dark:bg-[#151719] border-b border-zinc-200 dark:border-zinc-800 text-[11px] font-bold text-zinc-500 dark:text-zinc-400 uppercase tracking-wider select-none">
            <tr>
              <th class="py-3 px-3 w-12 text-center">№</th>
              <th class="py-3 px-4 min-w-[240px]">Maydon nomi (Field Name)</th>
              <th class="py-3 px-4 min-w-[240px]">Word Tegi (1-bosishda nusxalash)</th>
              <th class="py-3 px-4 min-w-[180px]">Muqobil teglar</th>
              <th class="py-3 px-4 min-w-[200px]">Namuna qiymat</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-zinc-200/80 dark:divide-zinc-800/70">
            <tr
              v-for="(field, idx) in filteredFields"
              :key="field.key"
              class="hover:bg-blue-50/40 dark:hover:bg-blue-950/20 transition-colors group"
            >
              <!-- Index -->
              <td class="py-3 px-3 text-center text-[11px] font-mono font-medium text-zinc-400">
                {{ idx + 1 }}
              </td>

              <!-- Field Name & Description -->
              <td class="py-3 px-4">
                <div class="font-bold text-zinc-900 dark:text-zinc-100">
                  {{ field.label }}
                </div>
                <div class="text-[11px] text-zinc-500 dark:text-zinc-400 mt-0.5 leading-snug">
                  {{ field.description }}
                </div>
              </td>

              <!-- Primary Tag Button -->
              <td class="py-3 px-4 whitespace-nowrap">
                <button
                  type="button"
                  @click="copyToClipboard(field.primary_tag)"
                  class="w-full sm:w-auto inline-flex items-center justify-between gap-3 px-3 py-1.5 rounded-xl font-mono text-xs font-bold border transition-all cursor-pointer shadow-2xs group/btn"
                  :class="[
                    copiedTag === field.primary_tag
                      ? 'bg-emerald-50 dark:bg-emerald-950/80 border-emerald-400 text-emerald-700 dark:text-emerald-300 ring-2 ring-emerald-500/20'
                      : 'bg-blue-50/80 dark:bg-blue-950/50 hover:bg-blue-100 dark:hover:bg-blue-900/60 border-blue-200 dark:border-blue-800 text-blue-700 dark:text-blue-300'
                  ]"
                  :title="`'${field.primary_tag}' tegini nusxalash uchun bosing`"
                >
                  <span class="tracking-wide text-xs">{{ field.primary_tag }}</span>
                  <span class="inline-flex items-center gap-1 text-[11px] font-sans shrink-0">
                    <template v-if="copiedTag === field.primary_tag">
                      <Check class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400 stroke-[2.5]" />
                      <span class="font-bold text-emerald-700 dark:text-emerald-300">Nusxalandi!</span>
                    </template>
                    <template v-else>
                      <Copy class="w-3.5 h-3.5 opacity-60 group-hover/btn:opacity-100 transition-opacity" />
                      <span class="font-semibold text-zinc-500 dark:text-zinc-400 group-hover/btn:text-blue-600 text-[10px]">Nusxa</span>
                    </template>
                  </span>
                </button>
              </td>

              <!-- Aliases -->
              <td class="py-3 px-4">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <button
                    v-for="alias in field.aliases"
                    :key="alias"
                    type="button"
                    @click="copyToClipboard(alias)"
                    class="px-2 py-0.5 rounded-lg font-mono text-[11px] transition-all cursor-pointer border"
                    :class="[
                      copiedTag === alias
                        ? 'bg-emerald-100 dark:bg-emerald-900/80 text-emerald-800 dark:text-emerald-200 border-emerald-400 font-bold'
                        : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-300 border-zinc-200 dark:border-zinc-700 hover:border-blue-400 hover:text-blue-600'
                    ]"
                    :title="`'${alias}' muqobil tegini nusxalash`"
                  >
                    {{ alias }}
                  </button>
                  <span v-if="!field.aliases || field.aliases.length === 0" class="text-zinc-400 text-xs">—</span>
                </div>
              </td>

              <!-- Sample Value -->
              <td class="py-3 px-4 text-xs font-medium text-zinc-700 dark:text-zinc-300">
                <span class="px-2 py-1 rounded-md bg-zinc-100/80 dark:bg-zinc-800/80 font-mono text-[11px] text-zinc-700 dark:text-zinc-300 border border-zinc-200/60 dark:border-zinc-700/60 inline-block max-w-[240px] truncate" :title="field.sample">
                  {{ field.sample }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty Search Result -->
      <div v-if="filteredFields.length === 0" class="text-center py-8 space-y-2">
        <p class="text-xs text-zinc-500 dark:text-zinc-400">
          "<strong>{{ searchQuery }}</strong>" so'rovi bo'yicha hech qanday maydon topilmadi.
        </p>
        <button
          type="button"
          @click="searchQuery = ''; selectedCategory = 'all'"
          class="text-xs text-blue-600 dark:text-blue-400 font-bold hover:underline cursor-pointer"
        >
          Filtrlarni tozalash
        </button>
      </div>
  </div>
</template>
