// Dynamic Contract Variables Catalog & Resolver

export interface ContractVariableDef {
  key: string
  token: string
  label: string
  category: 'student' | 'contract' | 'financial' | 'education'
  example: string
}

export const CONTRACT_VARIABLES: ContractVariableDef[] = [
  { key: 'fullname', token: '{{fullname}}', label: 'To\'liq ism-sharif (F.I.O)', category: 'student', example: 'ABDURAZZAKOV JASURBEK' },
  { key: 'passportnumber', token: '{{passportnumber}}', label: 'Pasport raqami', category: 'student', example: 'FA1234567' },
  { key: 'email', token: '{{email}}', label: 'Email manzil', category: 'student', example: 'student@salomkorea.uz' },
  { key: 'studentId', token: '{{studentId}}', label: 'Shartnoma N (Student ID)', category: 'contract', example: 'UB-1042' },
  { key: 'date', token: '{{date}}', label: 'Imzolangan sana (YYYY-MM-DD)', category: 'contract', example: '2026-09-15' },
  { key: 'leveltostudy', token: '{{leveltostudy}}', label: 'Ta\'lim bosqichi', category: 'education', example: 'Bakalavr' },
  { key: 'branch', token: '{{branch}}', label: 'Qabul ofisi / Filial', category: 'contract', example: 'Andijon filiali' },
  { key: 'dateofbirth', token: '{{dateofbirth}}', label: 'Tug\'ilgan sana', category: 'student', example: '15.04.2004' },
  { key: 'phone1', token: '{{phone1}}', label: 'Mobil telefon 1', category: 'student', example: '+998 90 123 45 67' },
  { key: 'phone2', token: '{{phone2}}', label: 'Mobil telefon 2', category: 'student', example: '+998 93 987 65 43' },
  { key: 'signature', token: '{{signature}}', label: 'Elektron imzo (rasm)', category: 'contract', example: '[Elektron imzo]' },
  { key: 'discount', token: '{{discount}}', label: 'Chegirma', category: 'financial', example: '1 000 000 so\'m' },
]

export function formatCurrencyString(val: string | number | null | undefined): string {
  if (val === null || val === undefined || val === '') return '0 so\'m'
  const num = typeof val === 'number' ? val : parseFloat(String(val).replace(/[^0-9.-]+/g, ''))
  if (isNaN(num)) return String(val)
  return new Intl.NumberFormat('uz-UZ').format(num) + ' so\'m'
}

export function formatDateDot(val: string | Date | null | undefined): string {
  if (!val) return ''
  if (typeof val === 'string') {
    const s = val.trim()
    if (!s) return ''
    if (/^\d{2}\.\d{2}\.\d{4}$/.test(s)) return s
    const isoMatch = s.match(/^(\d{4})[\-\/\.](\d{1,2})[\-\/\.](\d{1,2})/)
    if (isoMatch) {
      const y = isoMatch[1]
      const m = isoMatch[2].padStart(2, '0')
      const d = isoMatch[3].padStart(2, '0')
      return `${d}.${m}.${y}`
    }
  }
  try {
    const d = new Date(val)
    if (isNaN(d.getTime())) return String(val)
    return `${String(d.getDate()).padStart(2, '0')}.${String(d.getMonth() + 1).padStart(2, '0')}.${d.getFullYear()}`
  } catch {
    return String(val)
  }
}

export function formatDateString(val: string | Date | null | undefined): string {
  if (!val) {
    const now = new Date()
    return `${String(now.getDate()).padStart(2, '0')}.${String(now.getMonth() + 1).padStart(2, '0')}.${now.getFullYear()}`
  }
  return formatDateDot(val)
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
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">F.I.O:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em; padding-bottom: 2px; color: #2563eb; font-weight: bold;">&nbsp;{{fullname}}</span></p>')
  // Extra line for long names
  parts.push('<p style="border-bottom: 1px solid #000; margin: 0.28em 0; min-height: 1.1em; padding-bottom: 2px;">&nbsp;</p>')

  // 3. PASSPORT RAQAMI:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">PASSPORT RAQAMI:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em; padding-bottom: 2px; color: #2563eb; font-weight: bold;">&nbsp;{{passportnumber}}</span></p>')

  // 4. TUG\'ILGAN SANA:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TUG\'ILGAN SANA:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em; padding-bottom: 2px; color: #2563eb; font-weight: bold;">&nbsp;{{dateofbirth}}</span></p>')

  // 5. EMAIL:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">EMAIL:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em; padding-bottom: 2px; color: #2563eb; font-weight: bold;">&nbsp;{{email}}</span></p>')

  // 6. TEL:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TEL:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em; padding-bottom: 2px; color: #2563eb; font-weight: bold;">&nbsp;{{phone1}}</span></p>')

  // 7. TEL:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TEL:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em; padding-bottom: 2px; color: #2563eb; font-weight: bold;">&nbsp;{{phone2}}</span></p>')

  // 8. TA\'LIM BOSQICHI:
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TA\'LIM BOSQICHI:</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em; padding-bottom: 2px; color: #2563eb; font-weight: bold;">&nbsp;{{leveltostudy}}</span></p>')
  // Extra line
  parts.push('<p style="border-bottom: 1px solid #000; margin: 0.28em 0; min-height: 1.1em; padding-bottom: 2px;">&nbsp;</p>')

  // 9. TASDIQLASH KODI (IMZO):
  parts.push('<p style="display: flex; align-items: flex-end; margin: 0.28em 0;"><span style="font-weight: bold; white-space: nowrap;">TASDIQLASH KODI (IMZO):</span><span style="flex: 1; border-bottom: 1px solid #000; margin-left: 6px; min-height: 1.1em; padding-bottom: 2px; color: #2563eb; font-weight: bold;">&nbsp;{{signature}}</span></p>')

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
    email?: string
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

  const rawFullName = (student?.full_name || student?.fullName || student?.student_name || student?.client_name || '').toUpperCase().trim()
  const rawPassport = (student?.passport || student?.passport_number || student?.student_passport || student?.passportNumber || '').toUpperCase().trim()
  const rawDob = formatDateDot(student?.birthday || student?.date_of_birth || student?.dateOfBirth || '')
  const rawPhone1 = student?.phone1 || student?.student_phone || student?.phone || student?.phone_1 || ''
  const rawPhone2 = student?.phone2 || student?.phone_2 || ''
  const rawLevel = student?.level || student?.education_level || student?.educationLevel || student?.level_to_study || contractMeta?.educationLevel || (student ? 'Bakalavr' : '')
  const rawBranch = student?.office || student?.tenant_office_name || student?.branch || student?.office_name || contractMeta?.office || ''
  const rawEmail = student?.email || student?.student_email || student?.student_account?.email || (student?.snapshot_data && (student.snapshot_data.email || student.snapshot_data?.student_email)) || contractMeta?.email || ''

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
    passport_issue_date: formatDateDot(student?.passport_issue_date) || '',
    passport_expire_date: formatDateDot(student?.passport_expire_date) || '',

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
    studentId: contractNum,
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

    discount: discountVal > 0 ? formatCurrencyString(discountVal) : (student ? '0 so\'m' : ''),
    chegirma: discountVal > 0 ? formatCurrencyString(discountVal) : (student ? '0 so\'m' : ''),

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

export const VARIABLE_FALLBACK_PLACEHOLDERS: Record<string, string> = {
  fullname: '_________________________',
  full_name: '_________________________',
  student_name: '_________________________',
  client_name: '_________________________',
  fio: '_________________________',

  passportnumber: '____ _________',
  passport_number: '____ _________',
  passport: '____ _________',
  student_passport: '____ _________',
  passport_issue_date: '____.__.__',
  passport_expire_date: '____.__.__',

  dateofbirth: '__.__.____',
  date_of_birth: '__.__.____',
  birthday: '__.__.____',
  birth_date: '__.__.____',

  phone1: '+998 __ ___ __ __',
  phone_1: '+998 __ ___ __ __',
  phone: '+998 __ ___ __ __',
  student_phone: '+998 __ ___ __ __',
  phone2: '+998 __ ___ __ __',
  phone_2: '+998 __ ___ __ __',

  studentId: '______',
  studentid: '______',
  student_id: '______',
  contract_number: '______',
  contract_no: '______',
  shartnoma_raqami: '______',
  talaba_id: '______',

  date: '"___" _________ 2026 YIL',
  contract_date: '"___" _________ 2026 YIL',
  signed_date: '"___" _________ 2026 YIL',
  sana: '"___" _________ 2026 YIL',
  imzolangan_sana: '"___" _________ 2026 YIL',

  signature: '______________',
  imzo: '______________',
  e_signature: '______________',
  student_signature: '______________',
  signature_data: '______________',

  verification_code: '____-____-____',
  tasdiqlash_kodi: '____-____-____',
  confirmation_code: '____-____-____',

  leveltostudy: '________________',
  level_to_study: '________________',
  education_level: '________________',
  level: '________________',

  branch: '________________',
  office: '________________',
  filial: '________________',
  office_name: '________________',

  address: '_________________________________',
  email: '_____________________',
  nationality: 'O\'zbekiston Respublikasi',
  university: '_____________________',
  major: '_____________________',

  discount: '________________ so\'m',
  chegirma: '________________ so\'m',
}

export function getVariablePlaceholder(key: string): string {
  return ''
}

export interface ReplaceVariablesOptions {
  skipHeuristics?: boolean
  excludedVariables?: Set<string> | string[]
}

/**
 * Universal Contract Variable Replacer
 * Replaces:
 * - {{var}} tokens (case-insensitive, optional whitespace)
 * - [[var]] and %var% tokens
 * - Blue canvas variable preview spans: <span class="...bg-blue-50...">{{var}}</span> or color: #2563eb / #1d4ed8
 * - Standard MIJOZ requisites table (F.I.O, PASSPORT RAQAMI, TUG'ILGAN SANA, EMAIL, TEL, TA'LIM BOSQICHI, TASDIQLASH KODI (IMZO))
 * - Plain text "TASDIQLASH KODI (IMZO): ______"
 */
export function replaceVariablesInHtml(
  html: string,
  values: Record<string, string>,
  options?: ReplaceVariablesOptions
): string {
  if (!html) return ''
  let result = html

  // 1. Normalize values map: ensure every key is stripped of {{, }}, [[, ]], %
  const cleanMap: Record<string, string> = {}
  for (const [k, v] of Object.entries(values || {})) {
    const rawKey = k.replace(/^\{\{|\}\}$|^\[\[|\]\]$|^%|%$/g, '').trim().toLowerCase()
    cleanMap[rawKey] = v !== undefined && v !== null ? String(v) : ''
  }

  const resolveTokenValue = (key: string): string => {
    const lower = key.toLowerCase()
    if (cleanMap[lower] !== undefined && cleanMap[lower] !== '') {
      return cleanMap[lower]
    }
    return getVariablePlaceholder(lower)
  }

  // 2. Replace any variable wrapper spans from canvas editor (bg-blue-50, #2563eb, #1d4ed8)
  result = result.replace(
    /<span[^>]*style="[^"]*color:\s*(?:#2563eb|#1d4ed8|rgb\(37,\s*99,\s*235\)|rgb\(29,\s*78,\s*216\))[^"]*"[^>]*>\s*(?:\{\{)?\s*([a-zA-Z0-9_]+)\s*(?:\}\})?\s*<\/span>/gi,
    (_, key) => resolveTokenValue(key)
  )
  result = result.replace(
    /<p[^>]*style="[^"]*color:\s*(?:#2563eb|#1d4ed8|rgb\(37,\s*99,\s*235\)|rgb\(29,\s*78,\s*216\))[^"]*"[^>]*>\s*(?:\{\{)?\s*([a-zA-Z0-9_]+)\s*(?:\}\})?\s*<\/p>/gi,
    (_, key) => {
      const val = resolveTokenValue(key)
      return `<p>${val || '&nbsp;'}</p>`
    }
  )
  result = result.replace(
    /<span[^>]*class="[^"]*bg-blue-50[^"]*"[^>]*>\s*(?:\{\{)?\s*([a-zA-Z0-9_]+)\s*(?:\}\})?\s*<\/span>/gi,
    (_, key) => resolveTokenValue(key)
  )

  // 3. Replace mustache {{var}}, brackets [[var]], and %var%
  result = result.replace(
    /\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/gi,
    (_, key) => resolveTokenValue(key)
  )

  result = result.replace(
    /\[\[\s*([a-zA-Z0-9_]+)\s*\]\]/gi,
    (_, key) => resolveTokenValue(key)
  )

  result = result.replace(
    /%\s*([a-zA-Z0-9_]+)\s*%/gi,
    (_, key) => resolveTokenValue(key)
  )

  // Direct string replacements for any specific bracket keys in cleanMap
  for (const [k, v] of Object.entries(values || {})) {
    if (k.startsWith('{{') && k.endsWith('}}') && v) {
      result = result.split(k).join(v)
    }
  }

  // 4. Intelligent substitution for MIJOZ requisites block & standard contract lines
  // Skip heuristics if:
  // - options.skipHeuristics is explicitly true, OR
  // - the input snippet itself contains dynamic variable tokens ({{...}}, [[...]], %...%)
  const hasVariableTokens = /\{\{\s*[a-zA-Z0-9_]+\s*\}\}|\[\[\s*[a-zA-Z0-9_]+\s*\]\]|%\s*[a-zA-Z0-9_]+\s*%/i.test(html)
  const shouldSkipHeuristics = Boolean(options?.skipHeuristics) || hasVariableTokens

  const excluded = new Set<string>()
  if (options?.excludedVariables) {
    for (const item of options.excludedVariables) {
      if (item) excluded.add(item.toLowerCase().trim())
    }
  }

  const isExcluded = (...keys: string[]): boolean => {
    return shouldSkipHeuristics || keys.some(k => excluded.has(k.toLowerCase()))
  }

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

  if (studentName && !isExcluded('fullname', 'full_name', 'student_name', 'fio', 'client_name')) {
    // Header FUQARO line
    result = result.replace(
      /FUQARO:&nbsp;/gi,
      `FUQARO: <strong>${studentName}</strong>`
    )
    result = result.replace(
      /FUQARO:\s*<\/p>\s*<p[^>]*>\(O‘quvchining \(Mijozning\) F\.I\.SH\)/gi,
      `FUQARO: <strong>${studentName}</strong></p><p style="text-align:center;font-size:11px;color:#555;margin:2px 0 12px;">(O‘quvchining (Mijozning) F.I.SH)`
    )
    result = result.replace(
      /FUQARO:\s*_{2,}/gi,
      `FUQARO: <strong>${studentName}</strong>`
    )
    result = result.replace(
      /Fuqaro:\s*_{2,}/gi,
      `Fuqaro: <strong>${studentName}</strong>`
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

  if (passportNum && !isExcluded('passportnumber', 'passport_number', 'passport')) {
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

  if (dob && !isExcluded('dateofbirth', 'date_of_birth', 'birthday', 'birth_date')) {
    result = result.replace(
      /(<span[^>]*>\s*TUG[‘'']ILGAN\s+SANA:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${dob}</strong>&nbsp;</u>$2`
    )
    result = result.replace(
      /(TUG[‘'']ILGAN\s+SANA:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${dob}</strong>&nbsp;</u>$2`
    )
  }

  if (email && !isExcluded('email')) {
    result = result.replace(
      /(<span[^>]*>\s*EMAIL:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;${email}&nbsp;</u>$2`
    )
    result = result.replace(
      /(EMAIL:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;${email}&nbsp;</u>$2`
    )
  }

  if (phone1 && !isExcluded('phone1', 'phone_1', 'phone')) {
    result = result.replace(
      /(<span[^>]*>\s*TEL:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/i,
      `$1<u>&nbsp;${phone1}&nbsp;</u>$2`
    )
    result = result.replace(
      /(TEL:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/i,
      `$1<u>&nbsp;${phone1}&nbsp;</u>$2`
    )
  }

  if (phone2 && !isExcluded('phone2', 'phone_2')) {
    result = result.replace(
      /(<span[^>]*>\s*TEL:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/i,
      `$1<u>&nbsp;${phone2}&nbsp;</u>$2`
    )
    result = result.replace(
      /(TEL:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/i,
      `$1<u>&nbsp;${phone2}&nbsp;</u>$2`
    )
  }

  if (level && !isExcluded('leveltostudy', 'level_to_study', 'education_level', 'level')) {
    result = result.replace(
      /(<span[^>]*>\s*TA['’]LIM\s+BOSQICHI:\s*<\/span>\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${level}</strong>&nbsp;</u>$2`
    )
    result = result.replace(
      /(TA['’]LIM\s+BOSQICHI:\s*<span[^>]*>)(?:&nbsp;|\s*)(<\/span>)/gi,
      `$1<u>&nbsp;<strong>${level}</strong>&nbsp;</u>$2`
    )
  }

  if (studentId && !isExcluded('studentid', 'student_id', 'contract_number', 'contract_no', 'talaba_id', 'shartnoma_raqami')) {
    result = result.replace(
      /SHARTNOMA\s+(?:N|№):\s*<span[^>]*>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<\/span>/gi,
      `SHARTNOMA N: <u>&nbsp;<strong>${studentId}</strong>&nbsp;</u>`
    )
    result = result.replace(/SHARTNOMA\s+(?:N|№):\s*_{1,}/gi, `SHARTNOMA N: <strong>${studentId}</strong>`)
  }

  if (dateVal && !isExcluded('date', 'contract_date', 'signed_date', 'sana', 'imzolangan_sana')) {
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
  if (!isExcluded('signature', 'imzo', 'student_signature', 'signature_data', 'verification_code', 'tasdiqlash_kodi') && (signature || verifCode)) {
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
