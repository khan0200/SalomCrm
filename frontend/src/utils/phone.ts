/**
 * Utility functions for formatting and validating Uzbek phone numbers.
 * Standard local format: XX-XXX-XX-XX (e.g. 90-123-45-67 or 99-820-00-41)
 */

/**
 * Extracts the 9 local digits from a phone string (which may have +998 or 998 country code prefix).
 * Correctly avoids stripping '998' when it is part of a 9-digit local number (e.g. 99-820-00-41).
 */
export function extractLocalPhoneDigits(value?: string | null): string {
  if (!value) return ''
  const trimmed = String(value).trim()
  if (!trimmed) return ''

  let digits = trimmed.replace(/\D/g, '')
  if (!digits) return ''

  // Only strip a leading 998 if:
  // 1) The input explicitly started with '+' and has 998 (e.g. +998 99 820 00 41 or +998901234567)
  // 2) The raw digit string starts with 998 AND has more than 9 digits (e.g. 998901234567 or 998998200041)
  if ((trimmed.startsWith('+') && digits.startsWith('998')) || (digits.startsWith('998') && digits.length > 9)) {
    digits = digits.slice(3)
  }

  return digits.slice(0, 9)
}

/**
 * Formats a phone number into Uzbek standard local format: XX-XXX-XX-XX (e.g. 90-123-45-67).
 * If the input is empty or contains no digits, returns empty string.
 */
export function formatPhoneValue(value?: string | null): string {
  if (!value) return ''
  const digits = extractLocalPhoneDigits(value)
  if (!digits) return ''

  const first = digits.slice(0, 2)
  const second = digits.slice(2, 5)
  const third = digits.slice(5, 7)
  const fourth = digits.slice(7, 9)
  return [first, second, third, fourth].filter(Boolean).join('-')
}

/**
 * Formats user input keystroke-by-keystroke into standard local dash-grouped format: XX-XXX-XX-XX.
 */
export function formatUzPhoneInput(raw: string): string {
  const digits = extractLocalPhoneDigits(raw)
  let local = ''
  for (let i = 0; i < digits.length; i++) {
    if (i === 2 || i === 5 || i === 7) local += '-'
    local += digits[i]
  }
  return local
}

/**
 * Checks if the string contains a complete 9-digit Uzbek phone number.
 */
export function isCompleteUzPhone(value?: string | null): boolean {
  return extractLocalPhoneDigits(value).length === 9
}
