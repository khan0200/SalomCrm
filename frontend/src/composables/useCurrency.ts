export function useCurrency() {
  const formatAmount = (val: number | string | null | undefined): string => {
    if (val === null || val === undefined || isNaN(Number(val))) return '0'
    return new Intl.NumberFormat('en-US').format(Math.round(Number(val)))
  }

  const formatCurrency = (val: number | string | null | undefined): string => {
    return `${formatAmount(val)} UZS`
  }

  const parseAmount = (val: string): number => {
    if (!val) return 0
    const cleaned = val.replace(/[^\d.-]/g, '')
    return parseFloat(cleaned) || 0
  }

  const formatAmountInput = (val: string): string => {
    const cleaned = val.replace(/[^\d.]/g, '')
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
