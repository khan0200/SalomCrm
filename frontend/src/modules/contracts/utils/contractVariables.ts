// Dynamic Contract Variables Catalog & Resolver

export interface ContractVariableDef {
  key: string
  token: string
  label: string
  category: 'student' | 'contract' | 'financial' | 'education'
  example: string
}

export const CONTRACT_VARIABLES: ContractVariableDef[] = [
  // Primary Student details (Online Signing & Contracts)
  { key: 'fullname', token: '{{fullname}}', label: 'To\'liq ism-sharif (F.I.O)', category: 'student', example: 'ABDURAZZAKOV JASURBEK' },
  { key: 'passportnumber', token: '{{passportnumber}}', label: 'Pasport raqami', category: 'student', example: 'FA1234567' },
  { key: 'studentid', token: '{{studentid}}', label: 'Shartnoma N (Student ID)', category: 'contract', example: 'UB-1042' },
  { key: 'date', token: '{{date}}', label: 'Imzolangan sana (YYYY-MM-DD)', category: 'contract', example: '2026-09-15' },
  { key: 'leveltostudy', token: '{{leveltostudy}}', label: 'Ta\'lim bosqichi', category: 'education', example: 'Bakalavr' },
  { key: 'branch', token: '{{branch}}', label: 'Qabul ofisi / Filial', category: 'contract', example: 'Andijon filiali' },
  { key: 'dateofbirth', token: '{{dateofbirth}}', label: 'Tug\'ilgan sana', category: 'student', example: '15.04.2004' },
  { key: 'phone1', token: '{{phone1}}', label: 'Mobil telefon 1', category: 'student', example: '+998 90 123 45 67' },
  { key: 'phone2', token: '{{phone2}}', label: 'Mobil telefon 2', category: 'student', example: '+998 93 987 65 43' },
  { key: 'signature', token: '{{signature}}', label: 'Elektron imzo (rasm)', category: 'contract', example: '[Elektron imzo]' },
  { key: 'verification_code', token: '{{verification_code}}', label: 'Tasdiqlash kodi', category: 'contract', example: 'XXXX-XXXX-STUDENTID' },

  // Aliases & Extended Student details
  { key: 'student_name', token: '{{student_name}}', label: 'Talaba F.I.Sh (alias)', category: 'student', example: 'ALISHER ABDULLAEV' },
  { key: 'passport_number', token: '{{passport_number}}', label: 'Pasport raqami (alias)', category: 'student', example: 'FA1234567' },
  { key: 'passport_issue_date', token: '{{passport_issue_date}}', label: 'Berilgan sana', category: 'student', example: '12.05.2021' },
  { key: 'passport_expire_date', token: '{{passport_expire_date}}', label: 'Amal qilish muddati', category: 'student', example: '12.05.2031' },
  { key: 'date_of_birth', token: '{{date_of_birth}}', label: 'Tug\'ilgan sana (alias)', category: 'student', example: '15/04/2004' },
  { key: 'phone', token: '{{phone}}', label: 'Telefon (alias)', category: 'student', example: '+998 90 123 45 67' },
  { key: 'address', token: '{{address}}', label: 'Manzil', category: 'student', example: 'Toshkent sh., Yunusobod t., 12-uy' },
  { key: 'nationality', token: '{{nationality}}', label: 'Fuqaroligi', category: 'student', example: 'O\'zbekiston Respublikasi' },

  // Education details
  { key: 'university', token: '{{university}}', label: 'Universitet', category: 'education', example: 'Gimcheon University' },
  { key: 'major', token: '{{major}}', label: 'Yo\'nalish', category: 'education', example: 'Kompyuter muhandisligi' },
  { key: 'level', token: '{{level}}', label: 'Ta\'lim bosqichi (alias)', category: 'education', example: 'Bakalavr' },

  // Contract metadata
  { key: 'contract_number', token: '{{contract_number}}', label: 'Shartnoma raqami', category: 'contract', example: 'SH-2026-0042' },
  { key: 'contract_date', token: '{{contract_date}}', label: 'Tuzilgan sana', category: 'contract', example: '13.09.2026' },
  { key: 'consultant_name', token: '{{consultant_name}}', label: 'Mas\'ul mutaxassis', category: 'contract', example: 'M.Abdulpattayev' },

  // Contractor / Agency details
  { key: 'contractor_company', token: '{{contractor_company}}', label: 'Bajaruvchi korxona', category: 'contract', example: 'MCHJ "IT STATION" (UniBridge)' },
  { key: 'contractor_director', token: '{{contractor_director}}', label: 'Bajaruvchi direktor', category: 'contract', example: 'ABDULPATTAYEV M.A' },
  { key: 'contractor_inn', token: '{{contractor_inn}}', label: 'Bajaruvchi INN', category: 'contract', example: '309 961 634' },
  { key: 'contractor_oked', token: '{{contractor_oked}}', label: 'Bajaruvchi OKED', category: 'contract', example: '62010' },
  { key: 'contractor_certificate', token: '{{contractor_certificate}}', label: 'Bajaruvchi guvohnoma', category: 'contract', example: '5114456, 1995739' },
  { key: 'contractor_phone', token: '{{contractor_phone}}', label: 'Bajaruvchi telefon', category: 'contract', example: '+998 93 105 0011' },
  { key: 'contractor_bank', token: '{{contractor_bank}}', label: 'Bajaruvchi bank nomi', category: 'contract', example: 'UZMILLIY TOSHKENT FILIALI (M.O\')' },
  { key: 'contractor_account', token: '{{contractor_account}}', label: 'Bajaruvchi H/R', category: 'contract', example: '2020 8000 9055 7879 0001' },
  { key: 'contractor_mfo', token: '{{contractor_mfo}}', label: 'Bajaruvchi MFO', category: 'contract', example: '00450' },
  { key: 'contractor_address', token: '{{contractor_address}}', label: 'Bajaruvchi yuridik manzil', category: 'contract', example: 'Andijon viloyati, Marxamat tumani' },

  // Financial details (matching CRM financial ledger: Tariff, Discount, Payment Done, Withdrawal, Balance)
  { key: 'tariff_price', token: '{{tariff_price}}', label: 'Tarif narxi (Asl narx)', category: 'financial', example: '13 000 000 so\'m' },
  { key: 'contract_price', token: '{{contract_price}}', label: 'Shartnoma narxi (alias)', category: 'financial', example: '13 000 000 so\'m' },
  { key: 'discount', token: '{{discount}}', label: 'Chegirma', category: 'financial', example: '1 000 000 so\'m' },
  { key: 'chegirma', token: '{{chegirma}}', label: 'Chegirma (alias)', category: 'financial', example: '1 000 000 so\'m' },
  { key: 'net_price', token: '{{net_price}}', label: 'To\'lanishi lozim summa (Tarif - Chegirma)', category: 'financial', example: '12 000 000 so\'m' },
  { key: 'total_price', token: '{{total_price}}', label: 'Shartnoma to\'lov summasi (alias)', category: 'financial', example: '12 000 000 so\'m' },
  { key: 'payment_done', token: '{{payment_done}}', label: 'Amalda to\'langan summa (Payment done)', category: 'financial', example: '0 so\'m' },
  { key: 'balance', token: '{{balance}}', label: 'Qoldiq balans (Balance)', category: 'financial', example: '-12 000 000 so\'m' },
  { key: 'remaining_debt', token: '{{remaining_debt}}', label: 'Qoldiq qarzdorlik', category: 'financial', example: '12 000 000 so\'m' },
  { key: 'withdrawal', token: '{{withdrawal}}', label: 'Qaytarilgan summa (Withdrawal)', category: 'financial', example: '0 so\'m' },
  { key: 'first_payment', token: '{{first_payment}}', label: 'Oldindan to\'lov (1-to\'lov)', category: 'financial', example: '6 000 000 so\'m' },
  { key: 'second_payment', token: '{{second_payment}}', label: 'Ikkinchi to\'lov (2-to\'lov)', category: 'financial', example: '6 000 000 so\'m' },
]

export function formatCurrencyString(val: string | number | null | undefined): string {
  if (val === null || val === undefined || val === '') return '0 so\'m'
  const num = typeof val === 'number' ? val : parseFloat(String(val).replace(/[^0-9.-]+/g, ''))
  if (isNaN(num)) return String(val)
  return new Intl.NumberFormat('uz-UZ').format(num) + ' so\'m'
}

export function formatDateString(val: string | Date | null | undefined): string {
  if (!val) {
    const now = new Date()
    return `${String(now.getDate()).padStart(2, '0')}.${String(now.getMonth() + 1).padStart(2, '0')}.${now.getFullYear()}`
  }
  if (typeof val === 'string' && val.includes('.')) return val
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return String(val)
    return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`
  } catch {
    return String(val)
  }
}

export function formatDateIso(val: string | Date | null | undefined): string {
  if (!val) {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  }
  if (typeof val === 'string') {
    const s = val.trim()
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) return s
    if (/^\d{4}-\d{2}-\d{2}T/.test(s)) return s.split('T')[0]
    const ddmmyyyy = s.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/)
    if (ddmmyyyy) {
      return `${ddmmyyyy[3]}-${ddmmyyyy[2].padStart(2, '0')}-${ddmmyyyy[1].padStart(2, '0')}`
    }
  }
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return String(val)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
  } catch {
    return String(val)
  }
}

export interface AgencyRequisites {
  company_name: string
  director_name: string
  inn: string
  oked: string
  certificate_number: string
  phone: string
  address: string
  bank_name: string
  bank_account: string
  mfo: string
}

export const SODIQ_REQUISITES: AgencyRequisites = {
  company_name: '"UNIGATE" MAS\'ULIYATI CHEKLANGAN JAMIYAT',
  director_name: 'Abdug’afforov Sodiqjon Baxodir o’g’li',
  inn: '310785901',
  oked: '',
  certificate_number: '',
  phone: '(+998) 88 778-00-88',
  address: "Andijon viloyati, Andijon Shahar, O’zbegim MFY, Buyuk Turon ko’chasi, 4-uy, 16-xonadon",
  bank_name: 'SQB - Sanoat Qurilish Bank - Andijon BХO',
  bank_account: '2020 8000 3056 9675 2001',
  mfo: '00440',
}

export const UNIBRIDGE_REQUISITES: AgencyRequisites = {
  company_name: 'MCHJ "IT STATION"',
  director_name: 'ABDULPATTAYEV M.A',
  inn: '309 961 634',
  oked: '62010',
  certificate_number: '5114456, 1995739',
  phone: '+998 93 105 0011',
  address: 'Andijon viloyati, Marxamat tumani, Marxamat shahri Barhayot MFY, А.Тemur ko`chasi',
  bank_name: 'UzMilliy Toshkent Filliali',
  bank_account: '2020 8000 9055 7879 0001',
  mfo: '00450',
}

/**
 * Resolves requisites based on the current tenant profile or settings
 */
export function resolveTenantRequisites(customUserOrTenant?: any): AgencyRequisites {
  let req: any = null
  let isSodiq = false
  try {
    let u = customUserOrTenant
    if (!u && typeof localStorage !== 'undefined') {
      const userStr = localStorage.getItem('user_profile')
      if (userStr) u = JSON.parse(userStr)
    }
    if (u) {
      req = u?.tenant?.settings?.requisites || u?.settings?.requisites
      const tId = u?.tenant?.id || u?.tenant?.slug || u?.tenant_id || u?.id || u?.slug || (typeof u?.tenant === 'string' ? u?.tenant : '')
      const tName = (u?.tenant?.name || u?.name || '').toLowerCase()
      if (tId === 'sodiq' || tName.includes('sodiq') || tName.includes('unigate')) {
        isSodiq = true
      }
    }
  } catch {}

  const fallback = isSodiq ? SODIQ_REQUISITES : UNIBRIDGE_REQUISITES
  return {
    company_name: req?.company_name || fallback.company_name,
    director_name: req?.director_name || fallback.director_name,
    inn: req?.inn || fallback.inn,
    oked: req?.oked !== undefined ? req.oked : fallback.oked,
    certificate_number: req?.certificate_number !== undefined ? req.certificate_number : fallback.certificate_number,
    phone: req?.phone || fallback.phone,
    address: req?.address || fallback.address,
    bank_name: req?.bank_name || fallback.bank_name,
    bank_account: req?.bank_account || fallback.bank_account,
    mfo: req?.mfo || fallback.mfo,
  }
}

/**
 * Builds HTML representation of company requisites for contract canvas papers
 * matches exact typography and structure (BAJARUVCHI, INN, GUVOHNOMA, MANZIL, TEL, BANK, (M.O'), OKED|MFO, H/R, DIREKTOR)
 */
export function buildCompanyRequisitesHtml(req: AgencyRequisites): string {
  const parts: string[] = []

  // 1. Header: BAJARUVCHI
  parts.push('<p style="text-align: center; margin: 0.3em 0 0.8em; font-weight: bold; letter-spacing: 0.5px;">BAJARUVCHI</p>')

  // 2. Company & INN: MCHJ "IT STATION" INN: 309 961 634
  const company = (req.company_name || '').toUpperCase().trim()
  const inn = (req.inn || '').trim()
  let companyInn = company
  if (inn && !companyInn.includes('INN:')) {
    companyInn = companyInn ? `${companyInn} INN: ${inn}` : `INN: ${inn}`
  }
  if (companyInn) {
    parts.push(`<p style="margin: 0.28em 0;">${companyInn}</p>`)
  }

  // 3. Guvohnoma raqami: GUVOHNOMA RAQAMI: 5114456, 1995739
  const cert = (req.certificate_number || '').toUpperCase().trim()
  if (cert) {
    const certText = cert.startsWith('GUVOHNOMA') ? cert : `GUVOHNOMA RAQAMI: ${cert}`
    parts.push(`<p style="margin: 0.28em 0;">${certText}</p>`)
  }

  // 4. Address: formatted into clean uppercase lines
  const addr = (req.address || '').trim()
  if (addr) {
    const addrParts = addr.split(',').map(p => p.trim()).filter(Boolean)
    if (addrParts.length <= 1) {
      parts.push(`<p style="margin: 0.28em 0;">${addr.toUpperCase()}</p>`)
    } else {
      let current = ''
      for (let i = 0; i < addrParts.length; i++) {
        const isLast = i === addrParts.length - 1
        const partWithComma = addrParts[i] + (isLast ? '' : ',')
        if (!current) {
          current = partWithComma
        } else if ((current + ' ' + partWithComma).length <= 42) {
          current += ' ' + partWithComma
        } else {
          parts.push(`<p style="margin: 0.28em 0;">${current.toUpperCase()}</p>`)
          current = partWithComma
        }
      }
      if (current) {
        parts.push(`<p style="margin: 0.28em 0;">${current.toUpperCase()}</p>`)
      }
    }
  }

  // 5. Phone: TELEFON: +998 93 105 0011
  const phone = (req.phone || '').trim()
  if (phone) {
    const phoneText = phone.toUpperCase().startsWith('TEL') ? phone : `TELEFON: ${phone}`
    parts.push(`<p style="margin: 0.28em 0;">${phoneText}</p>`)
  }

  // 6. Bank & (M.O')
  let bankName = (req.bank_name || '').toUpperCase().trim()
  if (bankName.startsWith("MA'LUMOTLARI:") || bankName.startsWith("MA’LUMOTLARI:")) {
    bankName = bankName.replace(/^MA[’']LUMOTLARI:\s*/i, '')
  } else if (bankName.startsWith("BANK MA'LUMOTLARI:") || bankName.startsWith("BANK MA’LUMOTLARI:")) {
    bankName = bankName.replace(/^BANK\s+MA[’']LUMOTLARI:\s*/i, '')
  }

  const bankWords = bankName ? bankName.split(/\s+/) : []
  if (bankWords.length >= 3) {
    const lastWord = bankWords.pop()
    const firstWords = bankWords.join(' ')
    parts.push(`<p style="margin: 0.28em 0;">MA’LUMOTLARI: ${firstWords}</p>`)
    parts.push(`
<p style="display: flex; justify-content: space-between; align-items: baseline; margin: 0.28em 0; overflow: hidden;">
  <span>${lastWord}</span>
  <span style="font-weight: normal; font-size: 0.85em; float: right;">(M.O')</span>
</p>`.trim())
  } else if (bankWords.length > 0) {
    parts.push(`
<p style="display: flex; justify-content: space-between; align-items: baseline; margin: 0.28em 0; overflow: hidden;">
  <span>MA’LUMOTLARI: ${bankName}</span>
  <span style="font-weight: normal; font-size: 0.85em; float: right;">(M.O')</span>
</p>`.trim())
  } else {
    parts.push(`
<p style="display: flex; justify-content: space-between; align-items: baseline; margin: 0.28em 0; overflow: hidden;">
  <span>MA’LUMOTLARI:</span>
  <span style="font-weight: normal; font-size: 0.85em; float: right;">(M.O')</span>
</p>`.trim())
  }

  // 7. OKED & MFO: OKED: 62010 | MFO: 00450
  const oked = (req.oked || '').trim()
  const mfo = (req.mfo || '').trim()
  const okedStr = oked ? `OKED: ${oked}` : ''
  const mfoStr = mfo ? `MFO: ${mfo}` : ''
  if (okedStr && mfoStr) {
    parts.push(`<p style="margin: 0.28em 0;">${okedStr} | ${mfoStr}</p>`)
  } else if (okedStr || mfoStr) {
    parts.push(`<p style="margin: 0.28em 0;">${okedStr || mfoStr}</p>`)
  }

  // 8. H/R: 2020 8000 9055 7879 0001
  const hr = (req.bank_account || '').trim()
  if (hr) {
    const hrText = hr.toUpperCase().startsWith('H/R') ? hr : `H/R: ${hr}`
    parts.push(`<p style="margin: 0.28em 0;">${hrText}</p>`)
  }

  // 9. DIREKTOR: ABDULPATTAYEV M.A
  const director = (req.director_name || '').toUpperCase().trim()
  if (director) {
    const dirText = director.startsWith('DIREKTOR') ? director : `DIREKTOR: ${director}`
    parts.push(`<p style="margin: 0.28em 0;">${dirText}</p>`)
  }

  return parts.join('\n')
}

/**
 * Builds HTML representation of client requisites (MIJOZ) matching official contract papers:
 * MIJOZ, F.I.O, PASSPORT RAQAMI, TUG'ILGAN SANA, EMAIL, TEL, TEL, TA'LIM BOSQICHI, TASDIQLASH KODI (IMZO)
 */
export function buildClientRequisitesHtml(): string {
  const parts: string[] = []

  // 1. Header: MIJOZ
  parts.push('<p style="text-align: center; margin: 0.3em 0 0.8em; font-weight: bold; letter-spacing: 0.5px;">MIJOZ</p>')

  // 2. F.I.O:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">F.I.O:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em;">&nbsp;</span></p>')
  // Extra line for long names
  parts.push('<p style="border-bottom: 1px solid #000; margin: 0.28em 0; min-height: 1.1em;">&nbsp;</p>')

  // 3. PASSPORT RAQAMI:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">PASSPORT RAQAMI:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em;">&nbsp;</span></p>')

  // 4. TUG'ILGAN SANA:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TUG\'ILGAN SANA:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em;">&nbsp;</span></p>')

  // 5. EMAIL:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">EMAIL:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em;">&nbsp;</span></p>')

  // 6. TEL:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TEL:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em;">&nbsp;</span></p>')

  // 7. TEL:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TEL:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em;">&nbsp;</span></p>')

  // 8. TA'LIM BOSQICHI:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TA\'LIM BOSQICHI:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em;">&nbsp;</span></p>')
  // Extra line
  parts.push('<p style="border-bottom: 1px solid #000; margin: 0.28em 0; min-height: 1.1em;">&nbsp;</p>')

  // 9. TASDIQLASH KODI (IMZO):
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TASDIQLASH KODI (IMZO):</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em;">&nbsp;</span></p>')

  return parts.join('\n')
}

/**
 * Builds a key-value dictionary of values from student data and contract metadata
 */
export function buildVariableValues(
  student?: any,
  contractMeta?: {
    contractNumber?: string
    templateName?: string
    price?: number | string
    discount?: number | string
    consultantName?: string
    signatureData?: string
    verificationCode?: string
    office?: string
    educationLevel?: string
  }
): Record<string, string> {
  const priceVal = contractMeta?.price !== undefined && contractMeta?.price !== null && contractMeta?.price !== ''
    ? parseFloat(String(contractMeta.price))
    : (student?.tariff_price !== undefined && student?.tariff_price !== null && student?.tariff_price !== ''
        ? parseFloat(String(student.tariff_price))
        : 0)

  const discountVal = contractMeta?.discount !== undefined && contractMeta?.discount !== null && contractMeta?.discount !== ''
    ? parseFloat(String(contractMeta.discount))
    : (student?.discount ? parseFloat(String(student.discount)) : 0)
  const netVal = Math.max(0, priceVal - discountVal)
  const firstPayVal = netVal > 0 ? (netVal / 2) : 0
  const secondPayVal = Math.max(0, netVal - firstPayVal)

  const paymentsDoneVal = student?.payments_sum !== undefined && student?.payments_sum !== null
    ? parseFloat(String(student.payments_sum))
    : (student?.total_paid !== undefined && student?.total_paid !== null
        ? parseFloat(String(student.total_paid))
        : 0)

  const withdrawalsVal = student?.withdrawals_sum !== undefined && student?.withdrawals_sum !== null
    ? Math.abs(parseFloat(String(student.withdrawals_sum)))
    : (student?.withdrawals !== undefined && student?.withdrawals !== null
        ? Math.abs(parseFloat(String(student.withdrawals)))
        : 0)

  const balanceVal = student?.balance !== undefined && student?.balance !== null
    ? parseFloat(String(student.balance))
    : ((paymentsDoneVal + discountVal) - priceVal - withdrawalsVal)

  const remainingDebtVal = balanceVal < 0 ? Math.abs(balanceVal) : 0

  const req = resolveTenantRequisites()
  const isSodiq = (req.inn === SODIQ_REQUISITES.inn) || (req.company_name === SODIQ_REQUISITES.company_name)

  const rawFullName = (student?.full_name || student?.fullName || student?.student_name || '').toUpperCase().trim()
  const rawPassport = (student?.passport || student?.passport_number || student?.passportNumber || '').toUpperCase().trim()
  const rawDob = student?.birthday || student?.date_of_birth || student?.dateOfBirth || ''
  const rawPhone1 = student?.phone1 || student?.phone || student?.phone_1 || ''
  const rawPhone2 = student?.phone2 || student?.phone_2 || ''
  const rawLevel = student?.level || student?.education_level || student?.educationLevel || student?.level_to_study || contractMeta?.educationLevel || 'Bakalavr'
  const rawBranch = student?.office || student?.branch || student?.office_name || contractMeta?.office || ''
  const rawEmail = student?.email || student?.student_email || ''

  const rawSignature = contractMeta?.signatureData || student?.signature_data || student?.signatureData || ''
  const rawVerifCode = contractMeta?.verificationCode || student?.verification_code || student?.verificationCode || ''

  const signatureHtml = rawSignature
    ? (rawSignature.startsWith('data:image/')
        ? `<img src="${rawSignature}" style="max-height: 42px; max-width: 150px; object-fit: contain; vertical-align: middle; display: inline-block;" alt="Imzo" />`
        : rawSignature)
    : ''

  const rawStudentId = (
    contractMeta?.contractNumber ||
    student?.student_id_assigned ||
    student?.student_id ||
    student?.contract_number ||
    student?.id ||
    ''
  ).trim()
  const contractNum = rawStudentId || 'Pending Student ID'
  const contractDateIso = formatDateIso(student?.signed_at || student?.created_at || new Date())
  const formattedPrice = formatCurrencyString(priceVal)

  const map: Record<string, string> = {
    // 1. Primary Student fields (as specified in user requirements)
    fullname: rawFullName,
    full_name: rawFullName,
    student_name: rawFullName,
    client_name: rawFullName,
    fio: rawFullName,

    passportnumber: rawPassport,
    passport_number: rawPassport,
    passport: rawPassport,
    passport_issue_date: student?.passport_issue_date || '',
    passport_expire_date: student?.passport_expire_date || '',

    leveltostudy: rawLevel,
    level_to_study: rawLevel,
    education_level: rawLevel,
    level: rawLevel,

    branch: rawBranch,
    office: rawBranch,
    filial: rawBranch,
    office_name: rawBranch,

    dateofbirth: rawDob,
    date_of_birth: rawDob,
    birthday: rawDob,
    birth_date: rawDob,

    phone1: rawPhone1,
    phone_1: rawPhone1,
    phone: rawPhone1,

    phone2: rawPhone2,
    phone_2: rawPhone2,

    email: rawEmail,
    address: student?.address || '',
    nationality: 'O\'zbekiston Respublikasi',
    university: student?.university_1 || '',
    major: student?.university_1_major || student?.major || '',

    // 2. Signatures & Verification
    signature: signatureHtml,
    imzo: signatureHtml,
    e_signature: signatureHtml,
    student_signature: signatureHtml,
    signature_data: rawSignature,

    verification_code: rawVerifCode,
    tasdiqlash_kodi: rawVerifCode,
    confirmation_code: rawVerifCode,

    // 3. Contract Metadata & Identifiers
    studentid: contractNum,
    student_id: contractNum,
    contract_number: contractNum,
    contract_no: contractNum,
    shartnoma_raqami: contractNum,
    talaba_id: contractNum,

    date: contractDateIso,
    contract_date: contractDateIso,
    signed_date: contractDateIso,
    sana: contractDateIso,
    imzolangan_sana: contractDateIso,
    consultant_name: contractMeta?.consultantName || (isSodiq ? 'Abdug’afforov S.' : 'M.Abdulpattayev'),

    // 4. Financial (matching CRM financial ledger: Tariff, Discount, Payment Done, Withdrawal, Balance)
    contract_price: formattedPrice,
    tariff_price: formattedPrice,
    price: formattedPrice,
    tariff: contractMeta?.templateName || student?.tariff_name || student?.tariff || '',
    tariff_name: contractMeta?.templateName || student?.tariff_name || student?.tariff || '',

    discount: discountVal > 0 ? formatCurrencyString(discountVal) : '0 so\'m',
    chegirma: discountVal > 0 ? formatCurrencyString(discountVal) : '0 so\'m',

    net_price: formatCurrencyString(netVal),
    total_price: formatCurrencyString(netVal),
    payable_amount: formatCurrencyString(netVal),
    tolanishi_kerak: formatCurrencyString(netVal),

    payment_done: formatCurrencyString(paymentsDoneVal),
    paid_amount: formatCurrencyString(paymentsDoneVal),
    tolangan_summa: formatCurrencyString(paymentsDoneVal),

    balance: (balanceVal < 0 ? '-' : '') + formatCurrencyString(Math.abs(balanceVal)),
    qoldiq_balans: (balanceVal < 0 ? '-' : '') + formatCurrencyString(Math.abs(balanceVal)),
    remaining_debt: formatCurrencyString(remainingDebtVal),
    qoldiq_qarz: formatCurrencyString(remainingDebtVal),

    withdrawal: formatCurrencyString(withdrawalsVal),
    qaytarilgan_summa: formatCurrencyString(withdrawalsVal),

    first_payment: formatCurrencyString(firstPayVal),
    second_payment: formatCurrencyString(secondPayVal),

    // 5. Agency / Contractor requisites
    contractor_company: req.company_name,
    contractor_director: req.director_name,
    contractor_inn: req.inn,
    contractor_oked: req.oked,
    contractor_certificate: req.certificate_number,
    contractor_phone: req.phone,
    contractor_bank: req.bank_name,
    contractor_account: req.bank_account,
    contractor_mfo: req.mfo,
    contractor_address: req.address,
  }

  // Also include double-brace versions e.g. '{{fullname}}' for direct map lookup
  const result: Record<string, string> = { ...map }
  for (const [k, v] of Object.entries(map)) {
    result[`{{${k}}}`] = v
  }

  return result
}

/**
 * Universal Contract Variable Replacer
 * Replaces:
 * - {{var}} tokens (case-insensitive, optional whitespace)
 * - [[var]] and %var% tokens
 * - Blue canvas variable preview spans: <span class="...bg-blue-50...">{{var}}</span>
 * - Standard MIJOZ requisites table (F.I.O, PASSPORT RAQAMI, TUG'ILGAN SANA, EMAIL, TEL, TA'LIM BOSQICHI, TASDIQLASH KODI (IMZO))
 * - Plain text "TASDIQLASH KODI (IMZO): ______"
 */
export function replaceVariablesInHtml(html: string, values: Record<string, string>): string {
  if (!html) return ''
  let result = html

  // 1. Normalize values map: ensure every key is stripped of {{, }}, [[, ]], %
  const cleanMap: Record<string, string> = {}
  for (const [k, v] of Object.entries(values)) {
    const rawKey = k.replace(/^\{\{|\}\}$|^\[\[|\]\]$|^%|%$/g, '').trim().toLowerCase()
    cleanMap[rawKey] = v !== undefined && v !== null ? String(v) : ''
  }

  // 2. Replace any variable wrapper spans from canvas editor
  result = result.replace(
    /<span[^>]*class="[^"]*bg-blue-50[^"]*"[^>]*>\s*(?:\{\{)?\s*([a-zA-Z0-9_]+)\s*(?:\}\})?\s*<\/span>/gi,
    (match, key) => {
      const lower = key.toLowerCase()
      if (cleanMap[lower] !== undefined && cleanMap[lower] !== '') {
        return cleanMap[lower]
      }
      return match
    }
  )

  // 3. Replace mustache {{var}}, brackets [[var]], and %var%
  result = result.replace(
    /\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/gi,
    (match, key) => {
      const lower = key.toLowerCase()
      if (cleanMap[lower] !== undefined && cleanMap[lower] !== '') {
        return cleanMap[lower]
      }
      return match
    }
  )

  result = result.replace(
    /\[\[\s*([a-zA-Z0-9_]+)\s*\]\]/gi,
    (match, key) => {
      const lower = key.toLowerCase()
      if (cleanMap[lower] !== undefined && cleanMap[lower] !== '') {
        return cleanMap[lower]
      }
      return match
    }
  )

  result = result.replace(
    /%\s*([a-zA-Z0-9_]+)\s*%/gi,
    (match, key) => {
      const lower = key.toLowerCase()
      if (cleanMap[lower] !== undefined && cleanMap[lower] !== '') {
        return cleanMap[lower]
      }
      return match
    }
  )

  // Direct string replacements for any specific bracket keys in cleanMap
  for (const [k, v] of Object.entries(values)) {
    if (k.startsWith('{{') && k.endsWith('}}') && v) {
      result = result.split(k).join(v)
    }
  }

  // 4. Intelligent substitution for MIJOZ requisites block & standard contract lines
  const studentName = cleanMap['fullname'] || cleanMap['full_name'] || cleanMap['student_name']
  const passportNum = cleanMap['passportnumber'] || cleanMap['passport_number'] || cleanMap['passport']
  const dob = cleanMap['dateofbirth'] || cleanMap['date_of_birth'] || cleanMap['birthday']
  const phone1 = cleanMap['phone1'] || cleanMap['phone_1'] || cleanMap['phone']
  const phone2 = cleanMap['phone2'] || cleanMap['phone_2']
  const level = cleanMap['leveltostudy'] || cleanMap['level_to_study'] || cleanMap['education_level'] || cleanMap['level']
  const email = cleanMap['email']
  const signature = cleanMap['signature'] || cleanMap['imzo'] || cleanMap['signature_data']
  const verifCode = cleanMap['verification_code'] || cleanMap['tasdiqlash_kodi']
  const studentId = cleanMap['studentid'] || cleanMap['student_id'] || cleanMap['contract_number'] || cleanMap['contract_no'] || cleanMap['talaba_id']
  const dateVal = cleanMap['date'] || cleanMap['contract_date'] || cleanMap['signed_date'] || cleanMap['sana'] || cleanMap['imzolangan_sana']

  if (studentName) {
    // Header FUQARO line
    result = result.replace(
      /FUQARO:&nbsp;/gi,
      `FUQARO: <strong>${studentName}</strong>`
    )
    result = result.replace(
      /FUQARO:\s*<\/p>\s*<p[^>]*>\(O‘quvchining \(Mijozning\) F\.I\.SH\)/gi,
      `FUQARO: <strong>${studentName}</strong></p><p style="text-align:center;font-size:11px;color:#555;margin:2px 0 12px;">(O‘quvchining (Mijozning) F.I.SH)`
    )

    // F.I.O: <span ...>&nbsp;</span>
    result = result.replace(
      /(<span[^>]*>\s*F\.I\.O:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${studentName}</strong>&nbsp;</u>$2`
    )
    result = result.replace(
      /(F\.I\.O:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${studentName}</strong>&nbsp;</u>$2`
    )
    result = result.replace(
      /<strong>F\.I\.O:<\/strong>\s*<span[^>]*>&nbsp;<\/span>/gi,
      `<strong>F.I.O:</strong> <u>&nbsp;<strong>${studentName}</strong>&nbsp;</u>`
    )
  }

  if (passportNum) {
    result = result.replace(
      /(<span[^>]*>\s*PASSPORT(?:\s+RAQAMI)?:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${passportNum}</strong>&nbsp;</u>$2`
    )
    result = result.replace(
      /(PASSPORT(?:\s+RAQAMI)?:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${passportNum}</strong>&nbsp;</u>$2`
    )
    result = result.replace(
      /<strong>PASSPORT:<\/strong>\s*<span[^>]*>&nbsp;<\/span>\s*<span[^>]*>&nbsp;<\/span>/gi,
      `<strong>PASSPORT:</strong> <u>&nbsp;<strong>${passportNum}</strong>&nbsp;</u>`
    )
  }

  if (dob) {
    result = result.replace(
      /(<span[^>]*>\s*TUG[‘'']ILGAN\s+SANA:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${dob}</strong>&nbsp;</u>$2`
    )
    result = result.replace(
      /(TUG[‘'']ILGAN\s+SANA:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${dob}</strong>&nbsp;</u>$2`
    )
  }

  if (email) {
    result = result.replace(
      /(<span[^>]*>\s*EMAIL:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;${email}&nbsp;</u>$2`
    )
    result = result.replace(
      /(EMAIL:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;${email}&nbsp;</u>$2`
    )
  }

  if (phone1) {
    result = result.replace(
      /(<span[^>]*>\s*TEL:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/i,
      `$1<u>&nbsp;${phone1}&nbsp;</u>$2`
    )
    result = result.replace(
      /(TEL:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/i,
      `$1<u>&nbsp;${phone1}&nbsp;</u>$2`
    )
  }

  if (phone2) {
    result = result.replace(
      /(<span[^>]*>\s*TEL:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/i,
      `$1<u>&nbsp;${phone2}&nbsp;</u>$2`
    )
    result = result.replace(
      /(TEL:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/i,
      `$1<u>&nbsp;${phone2}&nbsp;</u>$2`
    )
  }

  if (level) {
    result = result.replace(
      /(<span[^>]*>\s*TA['’]LIM\s+BOSQICHI:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${level}</strong>&nbsp;</u>$2`
    )
    result = result.replace(
      /(TA['’]LIM\s+BOSQICHI:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${level}</strong>&nbsp;</u>$2`
    )
  }

  if (studentId) {
    result = result.replace(
      /SHARTNOMA\s+(?:N|№):\s*<span[^>]*>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<\/span>/gi,
      `SHARTNOMA N: <u>&nbsp;<strong>${studentId}</strong>&nbsp;</u>`
    )
    result = result.replace(/SHARTNOMA\s+(?:N|№):\s*_{1,}/gi, `SHARTNOMA N: <strong>${studentId}</strong>`)
  }

  if (dateVal) {
    result = result.replace(
      /SANA:\s*(?:&ldquo;|“|"|«)\s*_{1,}\s*(?:&rdquo;|”|"|»)\s*_{1,}\s*20\d\d\s*(?:YIL|yil)?/gi,
      `SANA: <strong>${dateVal}</strong>`
    )
    result = result.replace(
      /SANA:\s*&ldquo;____&rdquo;\s*_______________________\s*2026\s*YIL/gi,
      `SANA: <strong>${dateVal}</strong>`
    )
    result = result.replace(
      /SANA:\s*&ldquo;___&rdquo;\s*_______________________\s*2026\s*YIL/gi,
      `SANA: <strong>${dateVal}</strong>`
    )
    result = result.replace(
      /SANA:\s*_{2,}/gi,
      `SANA: <strong>${dateVal}</strong>`
    )
  }

  // 5. Signature & Verification Code in TASDIQLASH KODI (IMZO):
  if (signature || verifCode) {
    let sigSnippet = ''
    if (signature && signature.startsWith('data:image/')) {
      sigSnippet += `<img src="${signature}" style="max-height: 38px; max-width: 140px; object-fit: contain; vertical-align: middle; display: inline-block; margin-right: 8px;" alt="Imzo" />`
    } else if (signature && signature.includes('<img')) {
      sigSnippet += signature + ' '
    }
    if (verifCode && verifCode !== 'Pending Verification') {
      sigSnippet += `<strong style="font-family: monospace; font-size: 10.5px; vertical-align: middle;">${verifCode}</strong>`
    }

    if (sigSnippet) {
      // In MIJOZ block: TASDIQLASH KODI (IMZO): <span ...>&nbsp;</span>
      result = result.replace(
        /(<span[^>]*>\s*TASDIQLASH\s+KODI\s*\(IMZO\):\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
        `$1<span style="display: inline-flex; align-items: center;">${sigSnippet}</span>$2`
      )
      result = result.replace(
        /(TASDIQLASH\s+KODI\s*\(IMZO\):\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
        `$1<span style="display: inline-flex; align-items: center;">${sigSnippet}</span>$2`
      )
      // Also if plain text has TASDIQLASH KODI (IMZO): _____
      result = result.replace(
        /TASDIQLASH\s+KODI\s*\(IMZO\):\s*_{3,}/gi,
        `TASDIQLASH KODI (IMZO): ${sigSnippet}`
      )
    }
  }

  // 6. Contractor agency substitutions for Sodiq / UNIGATE if applicable
  const contractorCompany = cleanMap['contractor_company']
  if (contractorCompany && contractorCompany.includes('UNIGATE')) {
    result = result.replace(/&#9962;\s*Uni\s*Bridge/gi, '&#9962; Sodiq Consulting')
    result = result.replace(/Uni\s*Bridge/gi, 'Sodiq Consulting')
    if (cleanMap['contractor_director']) {
      result = result.replace(
        /Nizomga asosan\s*&ldquo;UniBridge&rdquo;\s*nomida ish ko[‘']ruvchi,\s*&ldquo;IT STATION&rdquo;\s*MCHJ nomidan direktor<br>\s*<strong>M\.Abdulpattayev va<\/strong>/gi,
        `Nizomga asosan "UNIGATE" MCHJ nomidan direktor<br><strong>${cleanMap['contractor_director']} va</strong>`
      )
      result = result.replace(/DIREKTOR:\s*ABDULPATTAYEV\s*M\.A/gi, `DIREKTOR: ${cleanMap['contractor_director']}`)
    }
    if (cleanMap['contractor_inn']) {
      result = result.replace(
        /MCHJ\s*&ldquo;IT STATION&rdquo;\s*INN:\s*309\s*961\s*634/gi,
        `<strong>${contractorCompany}</strong><br>INN: ${cleanMap['contractor_inn']}`
      )
      result = result.replace(
        /MCHJ\s*[“"]IT STATION[”"]\s*INN:\s*309\s*961\s*634/gi,
        `<strong>${contractorCompany}</strong><br>INN: ${cleanMap['contractor_inn']}`
      )
    }
    result = result.replace(/GUVOHNOMA RAQAMI:\s*5114456,\s*1995739/gi, '')
    if (cleanMap['contractor_address']) {
      result = result.replace(
        /ANDIJON VILOYATI,\s*MARXAMAT TUMANI,.*?A\.TEMUR KO[‘`']CHASI/gis,
        cleanMap['contractor_address']
      )
    }
    if (cleanMap['contractor_phone']) {
      result = result.replace(/TELEFON:\s*\+998\s*93\s*105\s*0011/gi, `TELEFON: ${cleanMap['contractor_phone']}`)
    }
    if (cleanMap['contractor_bank']) {
      result = result.replace(/MA[‘']LUMOTLARI:\s*UZMILLIY TOSHKENT FILLIALI.*?<\/span>/gis, `BANK: ${cleanMap['contractor_bank']}`)
    }
    if (cleanMap['contractor_mfo']) {
      result = result.replace(/OKED:\s*62010\s*\|\s*MFO:\s*00450/gi, `MFO: ${cleanMap['contractor_mfo']}`)
    }
    if (cleanMap['contractor_account']) {
      result = result.replace(/H\/R:\s*2020\s*8000\s*9055\s*7879\s*0001/gi, `H/R: ${cleanMap['contractor_account']}`)
    }
  }

  return result
}

/**
 * Replaces all {{variables}} and pre-fills signature lines in template HTML with actual student/contract values.
 */
export function resolveContractVariables(
  html: string,
  student?: any,
  contractMeta?: {
    contractNumber?: string
    templateName?: string
    price?: number | string
    consultantName?: string
    signatureData?: string
    verificationCode?: string
    office?: string
    educationLevel?: string
  }
): string {
  if (!html) return ''
  const values = buildVariableValues(student, contractMeta)
  return replaceVariablesInHtml(html, values)
}
