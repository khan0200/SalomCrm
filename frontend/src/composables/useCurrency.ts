export function useCurrency() {
  const formatAmount = (val: number | string | null | undefined): string => {
    if (val === null || val === undefined || val === '') return '0'
    const num = typeof val === 'number' ? val : parseFloat(String(val).replace(/[^\d.-]/g, ''))
    if (isNaN(num)) return '0'
    return new Intl.NumberFormat('en-US').format(Math.round(num))
  }

  const formatCurrency = (val: number | string | null | undefined): string => {
    return `${formatAmount(val)} UZS`
  }

  const parseAmount = (val: number | string | null | undefined): number => {
    if (val === null || val === undefined || val === '') return 0
    const cleaned = String(val).replace(/[^\d.-]/g, '')
    return parseFloat(cleaned) || 0
  }

  const formatAmountInput = (val: number | string | null | undefined): string => {
    if (val === null || val === undefined || val === '') return ''
    const cleaned = String(val).replace(/[^\d.]/g, '')
    if (!cleaned) return ''
    const [intPart, ...rest] = cleaned.split('.')
    const formattedInt = intPart === '' ? '' : new Intl.NumberFormat('en-US').format(Number(intPart))
    return rest.length > 0 ? `${formattedInt}.${rest.join('').slice(0, 2)}` : formattedInt
  }

  return {
    formatAmount,
    formatCurrency,
    parseAmount,
    formatAmountInput,
  }
}
