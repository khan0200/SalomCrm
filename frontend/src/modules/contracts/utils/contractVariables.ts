// Dynamic Contract Variables Catalog & Resolver

export interface ContractVariableDef {
  key: string
  token: string
  label: string
  category: 'student' | 'contract' | 'financial' | 'education'
  example: string
}

export const CONTRACT_VARIABLES: ContractVariableDef[] = [
  // Student details
  { key: 'student_name', token: '{{student_name}}', label: 'Talaba F.I.Sh', category: 'student', example: 'ALISHER ABDULLAEV' },
  { key: 'passport_number', token: '{{passport_number}}', label: 'Pasport raqami', category: 'student', example: 'FA1234567' },
  { key: 'passport_issue_date', token: '{{passport_issue_date}}', label: 'Berilgan sana', category: 'student', example: '12.05.2021' },
  { key: 'passport_expire_date', token: '{{passport_expire_date}}', label: 'Amal qilish muddati', category: 'student', example: '12.05.2031' },
  { key: 'date_of_birth', token: '{{date_of_birth}}', label: 'Tug\'ilgan sana', category: 'student', example: '15/04/2004' },
  { key: 'phone', token: '{{phone}}', label: 'Telefon', category: 'student', example: '+998 90 123 45 67' },
  { key: 'phone2', token: '{{phone2}}', label: 'Qo\'shimcha telefon', category: 'student', example: '+998 93 987 65 43' },
  { key: 'address', token: '{{address}}', label: 'Manzil', category: 'student', example: 'Toshkent sh., Yunusobod t., 12-uy' },
  { key: 'nationality', token: '{{nationality}}', label: 'Fuqaroligi', category: 'student', example: 'O\'zbekiston Respublikasi' },

  // Education details
  { key: 'university', token: '{{university}}', label: 'Universitet', category: 'education', example: 'Gimcheon University' },
  { key: 'major', token: '{{major}}', label: 'Yo\'nalish', category: 'education', example: 'Kompyuter muhandisligi' },
  { key: 'level', token: '{{level}}', label: 'Ta\'lim bosqichi', category: 'education', example: 'Bakalavr' },

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

  // Financial details
  { key: 'contract_price', token: '{{contract_price}}', label: 'Shartnoma narxi', category: 'financial', example: '13 000 000 so\'m' },
  { key: 'discount', token: '{{discount}}', label: 'Chegirma', category: 'financial', example: '1 000 000 so\'m' },
  { key: 'total_price', token: '{{total_price}}', label: 'Jami to\'lov', category: 'financial', example: '12 000 000 so\'m' },
  { key: 'first_payment', token: '{{first_payment}}', label: 'Oldindan to\'lov', category: 'financial', example: '6 500 000 so\'m' },
  { key: 'second_payment', token: '{{second_payment}}', label: 'Ikkinchi to\'lov', category: 'financial', example: '6 500 000 so\'m' },
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

/**
 * Builds a key-value dictionary of values from student data and contract metadata
 */
export function buildVariableValues(student?: any, contractMeta?: { contractNumber?: string; templateName?: string; price?: number | string; consultantName?: string }): Record<string, string> {
  const priceVal = contractMeta?.price ? parseFloat(String(contractMeta.price)) : 0
  const discountVal = student?.discount ? parseFloat(String(student.discount)) : 0
  const totalVal = Math.max(0, priceVal - discountVal)
  const firstPayVal = priceVal > 0 ? (priceVal / 2) : 0
  const secondPayVal = Math.max(0, totalVal - firstPayVal)

  let req: any = null
  let isSodiq = false
  try {
    const userStr = typeof localStorage !== 'undefined' ? localStorage.getItem('user_profile') : null
    if (userStr) {
      const u = JSON.parse(userStr)
      req = u?.tenant?.settings?.requisites
      const tId = u?.tenant?.id || u?.tenant_id || (typeof u?.tenant === 'string' ? u?.tenant : '')
      if (tId === 'sodiq') isSodiq = true
    }
  } catch {}

  const defaultReq = isSodiq ? {
    company_name: '"UNIGATE" MAS\'ULIYATI CHEKLANGAN JAMIYAT',
    director_name: "Abdug’afforov Sodiqjon Baxodir o’g’li",
    inn: '310785901',
    oked: '',
    certificate_number: '',
    phone: '(+998) 88 778-00-88',
    address: "Andijon viloyati, Andijon Shahar, O’zbegim MFY, Buyuk Turon ko’chasi, 4-uy, 16-xonadon",
    bank_name: 'SQB - Sanoat Qurilish Bank - Andijon BХO',
    bank_account: '2020 8000 3056 9675 2001',
    mfo: '00440'
  } : {
    company_name: 'MCHJ "IT STATION"',
    director_name: 'ABDULPATTAYEV M.A',
    inn: '309 961 634',
    oked: '62010',
    certificate_number: '5114456, 1995739',
    phone: '+998 93 105 0011',
    address: 'Andijon viloyati, Marxamat tumani, Marxamat shahri Barhayot MFY, А.Тemur ko`chasi',
    bank_name: 'UzMilliy Toshkent Filliali',
    bank_account: '2020 8000 9055 7879 0001',
    mfo: '00450'
  }

  const contractorCompany = req?.company_name || defaultReq.company_name
  const contractorDirector = req?.director_name || defaultReq.director_name
  const contractorInn = req?.inn || defaultReq.inn
  const contractorOked = req?.oked !== undefined ? req.oked : defaultReq.oked
  const contractorCert = req?.certificate_number !== undefined ? req.certificate_number : defaultReq.certificate_number
  const contractorPhone = req?.phone || defaultReq.phone
  const contractorBank = req?.bank_name || defaultReq.bank_name
  const contractorAccount = req?.bank_account || defaultReq.bank_account
  const contractorMfo = req?.mfo || defaultReq.mfo
  const contractorAddress = req?.address || defaultReq.address

  return {
    student_name: (student?.full_name || '').toUpperCase().trim(),
    passport_number: (student?.passport || '').toUpperCase().trim(),
    passport_issue_date: student?.passport_issue_date || '',
    passport_expire_date: student?.passport_expire_date || '',
    date_of_birth: student?.birthday || '',
    phone: student?.phone1 || '',
    phone2: student?.phone2 || '',
    address: student?.address || '',
    nationality: 'O\'zbekiston Respublikasi',
    university: student?.university_1 || '',
    major: student?.university_1_major || student?.major || '',
    level: student?.level || 'Bakalavr',
    contract_number: contractMeta?.contractNumber || 'SH-' + new Date().getFullYear() + '-0001',
    contract_date: formatDateString(new Date()),
    consultant_name: contractMeta?.consultantName || (isSodiq ? 'Abdug’afforov S.' : 'M.Abdulpattayev'),
    contract_price: formatCurrencyString(priceVal),
    discount: discountVal > 0 ? formatCurrencyString(discountVal) : '0 so\'m',
    total_price: formatCurrencyString(totalVal),
    first_payment: formatCurrencyString(firstPayVal),
    second_payment: formatCurrencyString(secondPayVal),

    // Contractor / Agency requisites
    contractor_company: contractorCompany,
    contractor_director: contractorDirector,
    contractor_inn: contractorInn,
    contractor_oked: contractorOked,
    contractor_certificate: contractorCert,
    contractor_phone: contractorPhone,
    contractor_bank: contractorBank,
    contractor_account: contractorAccount,
    contractor_mfo: contractorMfo,
    contractor_address: contractorAddress,
  }
}

/**
 * Replaces all {{variables}} and pre-fills signature lines in template HTML with actual student/contract values.
 */
export function resolveContractVariables(html: string, student?: any, contractMeta?: { contractNumber?: string; templateName?: string; price?: number | string; consultantName?: string }): string {
  if (!html) return ''
  const values = buildVariableValues(student, contractMeta)

  let resolved = html

  // 1. Replace explicit mustache tokens {{token}}
  for (const [key, val] of Object.entries(values)) {
    const tokenRegex = new RegExp(`\\{\\{\\s*${key}\\s*\\}\\}`, 'gi')
    resolved = resolved.replace(tokenRegex, val || '')
  }

  // 2. Intelligent substitution for standard contract header and signature sections if student exists
  if (values.student_name) {
    // Header contract number line
    if (values.contract_number) {
      resolved = resolved.replace(
        /SHARTNOMA N:\s*<span[^>]*>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<\/span>/gi,
        `SHARTNOMA N: <u>&nbsp;<strong>${values.contract_number}</strong>&nbsp;</u>`
      )
      resolved = resolved.replace(/SHARTNOMA N:\s*______/gi, `SHARTNOMA N: <strong>${values.contract_number}</strong>`)
    }

    // FUQARO: header line
    resolved = resolved.replace(
      /FUQARO:&nbsp;/gi,
      `FUQARO: <strong>${values.student_name}</strong>`
    )
    resolved = resolved.replace(
      /FUQARO:\s*<\/p>\s*<p[^>]*>\(O‘quvchining \(Mijozning\) F\.I\.SH\)/gi,
      `FUQARO: <strong>${values.student_name}</strong></p><p style="text-align:center;font-size:11px;color:#555;margin:2px 0 12px;">(O‘quvchining (Mijozning) F.I.SH)`
    )

    // SANA: line
    if (values.contract_date) {
      resolved = resolved.replace(
        /SANA:\s*&ldquo;____&rdquo;\s*_______________________\s*2026\s*YIL/gi,
        `SANA: <strong>${values.contract_date}</strong>`
      )
      resolved = resolved.replace(
        /SANA:\s*&ldquo;___&rdquo;\s*_______________________\s*2026\s*YIL/gi,
        `SANA: <strong>${values.contract_date}</strong>`
      )
    }

    // MIJOZ table signature block in footer
    resolved = resolved.replace(
      /<strong>F\.I\.O:<\/strong>\s*<span[^>]*>&nbsp;<\/span>/gi,
      `<strong>F.I.O:</strong> <u>&nbsp;<strong>${values.student_name}</strong>&nbsp;</u>`
    )
    resolved = resolved.replace(
      /F\.I\.O:\s*<span[^>]*>&nbsp;<\/span>/gi,
      `<strong>F.I.O:</strong> <u>&nbsp;<strong>${values.student_name}</strong>&nbsp;</u>`
    )

    if (values.passport_number) {
      resolved = resolved.replace(
        /<strong>PASSPORT:<\/strong>\s*<span[^>]*>&nbsp;<\/span>\s*<span[^>]*>&nbsp;<\/span>/gi,
        `<strong>PASSPORT:</strong> <u>&nbsp;<strong>${values.passport_number}</strong>&nbsp;</u>`
      )
      resolved = resolved.replace(
        /PASSPORT:\s*<span[^>]*>&nbsp;<\/span>\s*<span[^>]*>&nbsp;<\/span>/gi,
        `<strong>PASSPORT:</strong> <u>&nbsp;<strong>${values.passport_number}</strong>&nbsp;</u>`
      )
    }

    if (values.address) {
      resolved = resolved.replace(
        /<strong>YASHASH MANZIL:<\/strong>\s*<span[^>]*>&nbsp;<\/span>/gi,
        `<strong>YASHASH MANZIL:</strong> <u>&nbsp;${values.address}&nbsp;</u>`
      )
      resolved = resolved.replace(
        /YASHASH MANZIL:\s*<span[^>]*>&nbsp;<\/span>/gi,
        `<strong>YASHASH MANZIL:</strong> <u>&nbsp;${values.address}&nbsp;</u>`
      )
    }

    if (values.date_of_birth) {
      resolved = resolved.replace(
        /<strong>TUG‘ILGAN SANA:<\/strong>.*?<\/span>/gis,
        `<strong>TUG‘ILGAN SANA:</strong> <u>&nbsp;${values.date_of_birth}&nbsp;</u>`
      )
      resolved = resolved.replace(
        /TUG‘ILGAN SANA:.*?<\/span>/gis,
        `<strong>TUG‘ILGAN SANA:</strong> <u>&nbsp;${values.date_of_birth}&nbsp;</u>`
      )
    }

    if (values.phone) {
      resolved = resolved.replace(
        /<strong>TEL:<\/strong>\s*<span[^>]*>&nbsp;<\/span>/i,
        `<strong>TEL:</strong> <u>&nbsp;${values.phone}&nbsp;</u>`
      )
      resolved = resolved.replace(
        /TEL:\s*<span[^>]*>&nbsp;<\/span>/i,
        `<strong>TEL:</strong> <u>&nbsp;${values.phone}&nbsp;</u>`
      )
    }

    if (values.phone2) {
      resolved = resolved.replace(
        /<strong>TEL:<\/strong>\s*<span[^>]*>&nbsp;<\/span>/i,
        `<strong>TEL:</strong> <u>&nbsp;${values.phone2}&nbsp;</u>`
      )
      resolved = resolved.replace(
        /TEL:\s*<span[^>]*>&nbsp;<\/span>/i,
        `<strong>TEL:</strong> <u>&nbsp;${values.phone2}&nbsp;</u>`
      )
    }
  }

  // 3. Intelligent contractor substitution for BAJARUVCHI block
  if (values.contractor_company && values.contractor_company.includes('UNIGATE')) {
    // Sodiq / UNIGATE substitutions
    resolved = resolved.replace(/&#9962;\s*Uni\s*Bridge/gi, '&#9962; Sodiq Consulting')
    resolved = resolved.replace(/Uni\s*Bridge/gi, 'Sodiq Consulting')
    resolved = resolved.replace(
      /Nizomga asosan\s*&ldquo;UniBridge&rdquo;\s*nomida ish ko[‘']ruvchi,\s*&ldquo;IT STATION&rdquo;\s*MCHJ nomidan direktor<br>\s*<strong>M\.Abdulpattayev va<\/strong>/gi,
      `Nizomga asosan "UNIGATE" MCHJ nomidan direktor<br><strong>${values.contractor_director} va</strong>`
    )
    resolved = resolved.replace(
      /MCHJ\s*&ldquo;IT STATION&rdquo;\s*INN:\s*309\s*961\s*634/gi,
      `<strong>${values.contractor_company}</strong><br>INN: ${values.contractor_inn}`
    )
    resolved = resolved.replace(
      /MCHJ\s*[“"]IT STATION[”"]\s*INN:\s*309\s*961\s*634/gi,
      `<strong>${values.contractor_company}</strong><br>INN: ${values.contractor_inn}`
    )
    resolved = resolved.replace(/GUVOHNOMA RAQAMI:\s*5114456,\s*1995739/gi, '')
    resolved = resolved.replace(
      /ANDIJON VILOYATI,\s*MARXAMAT TUMANI,.*?A\.TEMUR KO[‘`']CHASI/gis,
      values.contractor_address
    )
    resolved = resolved.replace(/TELEFON:\s*\+998\s*93\s*105\s*0011/gi, `TELEFON: ${values.contractor_phone}`)
    resolved = resolved.replace(/MA[‘']LUMOTLARI:\s*UZMILLIY TOSHKENT FILLIALI.*?<\/span>/gis, `BANK: ${values.contractor_bank}`)
    resolved = resolved.replace(/OKED:\s*62010\s*\|\s*MFO:\s*00450/gi, `MFO: ${values.contractor_mfo}`)
    resolved = resolved.replace(/H\/R:\s*2020\s*8000\s*9055\s*7879\s*0001/gi, `H/R: ${values.contractor_account}`)
    resolved = resolved.replace(/DIREKTOR:\s*ABDULPATTAYEV\s*M\.A/gi, `DIREKTOR: ${values.contractor_director}`)
  }

  return resolved
}
