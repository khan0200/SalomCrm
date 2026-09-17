export const DEFAULT_TARIFF_PRICES: Record<string, number> = {
  'STANDART': 13000000,
  'PREMIUM': 32500000,
  'VISA PLUS': 65000000,
  'E-VISA (TIL SERTIFIKATISIZ)': 24000000,
  'E-VISA (TIL SERTIFIKATLI)': 16000000,
  'REGIONAL VISA': 24000000,
  'ZERO RISK': 18500000,
}

/**
 * Calculates the price of a tariff for a student from custom tariff prices
 * configured in settings, normalising the known E-VISA variant spellings onto
 * their canonical tariff names.
 *
 * The two E-VISA variants are separate named tariffs; there is no generic
 * 'E-VISA' priced from the language certificate, so `languageCertificate` is
 * ignored and kept only so existing call sites keep compiling.
 */
export function getTariffPrice(
  tariff: string | null | undefined,
  languageCertificate?: string | null | undefined,
  prices?: Record<string, number> | Array<{ name: string; price?: number | string } | string | any>
): number {
  if (!tariff || tariff === 'Select') return 0
  const cleanTariff = tariff.trim().toUpperCase()

  const priceMap: Record<string, number> = Array.isArray(prices)
    ? prices.reduce((acc, curr) => {
        if (curr && curr.name) acc[curr.name.trim().toUpperCase()] = Number(curr.price) || 0
        return acc
      }, {} as Record<string, number>)
    : (prices || DEFAULT_TARIFF_PRICES)

  // 1. If tariff name specifically indicates with/without certificate in its title
  if (
    cleanTariff.includes('TIL SERTIFIKATLI') ||
    cleanTariff.includes('(TIL SERTIFIKATLI)') ||
    cleanTariff.includes('SERTIFIKATLI') ||
    cleanTariff.includes('WITH CERTIFICATE')
  ) {
    const targetName = 'E-VISA (TIL SERTIFIKATLI)'
    const foundMatch = Object.entries(priceMap).find(([k]) => k.trim().toUpperCase() === targetName)
    if (foundMatch && Number(foundMatch[1]) > 0) return Number(foundMatch[1])

    const directMatch = Object.entries(priceMap).find(([k]) => k.trim().toUpperCase() === cleanTariff)
    if (directMatch && Number(directMatch[1]) > 0) return Number(directMatch[1])

    return 16000000
  }

  if (
    cleanTariff.includes('TIL SERTIFIKATISIZ') ||
    cleanTariff.includes('(TIL SERTIFIKATISIZ)') ||
    cleanTariff.includes('SERTIFIKATSIZ') ||
    cleanTariff.includes('WITHOUT CERTIFICATE')
  ) {
    const targetName = 'E-VISA (TIL SERTIFIKATISIZ)'
    const foundMatch = Object.entries(priceMap).find(([k]) => k.trim().toUpperCase() === targetName)
    if (foundMatch && Number(foundMatch[1]) > 0) return Number(foundMatch[1])

    const directMatch = Object.entries(priceMap).find(([k]) => k.trim().toUpperCase() === cleanTariff)
    if (directMatch && Number(directMatch[1]) > 0) return Number(directMatch[1])

    return 24000000
  }

  // 2. Exact match in the configured prices. A configured price of 0 means
  // "not really priced here", so it falls through to the defaults below.
  const directMatch = Object.entries(priceMap).find(([k]) => k.trim().toUpperCase() === cleanTariff)
  if (directMatch && Number(directMatch[1]) > 0) {
    return Number(directMatch[1])
  }

  // 3. Fallback defaults
  const fallback = DEFAULT_TARIFF_PRICES[cleanTariff]
  return fallback !== undefined ? fallback : 0
}
