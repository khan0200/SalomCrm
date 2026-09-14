import type { OnlineTariff } from '@/api/onlineContracts'

/**
 * Generates an official, beautifully formatted Uzbek consulting agreement sample HTML
 * for a tariff. Used when downloading sample contracts if tariff.contract_text is not provided.
 */
export function getTariffSampleContractHtml(
  companyName: string,
  tariff: OnlineTariff
): string {
  if (tariff.contract_text && tariff.contract_text.trim().length > 40) {
    return tariff.contract_text
  }

  const formattedPrice = tariff.price
    ? Number(tariff.price).toLocaleString('uz-UZ') + " so'm"
    : "Kelishilgan miqdorda"

  const currentDate = new Date().toLocaleDateString('uz-UZ', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return `
    <div style="font-family: 'Times New Roman', Times, serif; font-size: 13.5px; line-height: 1.65; color: #0f172a; padding: 24px 28px;">
      <!-- Header -->
      <div style="text-align: center; margin-bottom: 24px; border-bottom: 1.5px solid #0f172a; padding-bottom: 16px;">
        <h2 style="margin: 0 0 6px 0; font-size: 15pt; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">
          KONSALTING VA TA'LIM XIZMATLARI KO'RSATISH SHARTNOMASI
        </h2>
        <div style="font-size: 11pt; font-weight: 600; color: #334155; margin-bottom: 4px;">
          (NAMUNAVIY RASMIY SHARTNOMA LOYIHASI)
        </div>
        <div style="font-size: 10pt; color: #64748b;">
          Tarif: <strong>${tariff.name}</strong> | Sana: <strong>${currentDate}</strong>
        </div>
      </div>

      <!-- Parties -->
      <p style="text-align: justify; text-indent: 1.25cm; margin: 12px 0;">
        Bir tomondan <strong>"${companyName || 'Konsalting Kompaniyasi'}"</strong> (keyingi o'rinlarda <em>"Ijrochi"</em> deb ataladi), o'z Nizomi va amaldagi qonunchilik asosida ish yurituvchi, ikkinchi tomondan ushbu xizmatdan foydalanuvchi jismoniy shaxs (keyingi o'rinlarda <em>"Buyurtmachi"</em> deb ataladi), birgalikda <em>"Tomonlar"</em> deb ataluvchilar, quyidagilar bo'yicha mazkur shartnomani tuzdilar:
      </p>

      <!-- 1. Shartnoma mavzusi -->
      <h3 style="font-size: 12pt; font-weight: bold; margin: 18px 0 8px 0; text-align: center;">
        1. SHARTNOMA MAVZUSI
      </h3>
      <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
        1.1. Mazkur shartnomaga muvofiq, Ijrochi Buyurtmachining buyurtmasiga asosan <strong>"${tariff.name}"</strong> dasturi doirasida xorijiy ta'lim muassasalariga hujjat topshirish, viza jarayonlari bo'yicha konsalting, axborot va tashkiliy ko'mak ko'rsatish xizmatlarini o'z zimmasiga oladi, Buyurtmachi esa ushbu xizmatlar haqini belgilangan tartibda to'lash majburiyatini oladi.
      </p>
      <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
        1.2. Ko'rsatiladigan xizmatlar hajmi, muddati va bosqichlari belgilangan qonuniy me'yorlar hamda xorijiy hamkorlar talablari asosida amalga oshiriladi.
      </p>

      <!-- 2. Shartnoma narxi va to'lov tartibi -->
      <h3 style="font-size: 12pt; font-weight: bold; margin: 18px 0 8px 0; text-align: center;">
        2. SHARTNOMA NARXI VA TO'LOV TARTIBI
      </h3>
      <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
        2.1. Mazkur shartnoma bo'yicha <strong>"${tariff.name}"</strong> dasturi xizmatlarining umumiy qiymati <strong>${formattedPrice}</strong>ni tashkil etadi.
      </p>
      <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
        2.2. To'lovlar O'zbekiston Respublikasi milliy valyutasi — so'mda, naqd pulsiz shaklda (bank o'tkazmasi, to'lov tizimlari yoki bank kartalari orqali) Ijrochining hisob-raqamiga to'lanadi.
      </p>
      <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
        2.3. To'lov shartlari Buyurtmachi tomonidan onlayn tasdiqlangach, belgilangan grafik asosida amalga oshiriladi.
      </p>

      <!-- 3. Tomonlarning huquq va majburiyatlari -->
      <h3 style="font-size: 12pt; font-weight: bold; margin: 18px 0 8px 0; text-align: center;">
        3. TOMONLARNING HUQUQ VA MAJBURIYATLARI
      </h3>
      <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
        <strong>3.1. Ijrochining majburiyatlari:</strong>
        <br/>• Buyurtmachiga ta'lim dasturlari, talablar va viza jarayonlari bo'yicha to'liq va ishonchli konsalting xizmati ko'rsatish;
        <br/>• Buyurtmachi tomonidan taqdim etilgan barcha hujjatlarning maxfiyligini qat'iy saqlash;
        <br/>• Xizmat ko'rsatish jarayonida yuzaga keladigan masalalar bo'yicha o'z vaqtida xabardor qilib borish.
      </p>
      <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
        <strong>3.2. Buyurtmachining majburiyatlari:</strong>
        <br/>• Ijrochi talab qilgan barcha haqqoniy va to'g'ri hujjatlar, pasport ma'lumotlarini o'z vaqtida taqdim etish;
        <br/>• Xizmatlar uchun to'lovni shartnomada belgilangan muddatda to'lash;
        <br/>• Belgilangan suhbat va uchrashuvlarga o'z vaqtida qatnashish.
      </p>

      <!-- 4. Nizolarni hal qilish va maxsus shartlar -->
      <h3 style="font-size: 12pt; font-weight: bold; margin: 18px 0 8px 0; text-align: center;">
        4. NIZOLARNI HAL QILISH VA YAKUNIY QOIDALAR
      </h3>
      <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
        4.1. Mazkur shartnoma yuzasidan kelib chiqadigan barcha nizolar va kelishmovchiliklar Tomonlar o'rtasida muzokaralar yo'li bilan hal etiladi. Kelishuvga erishilmagan taqdirda, O'zbekiston Respublikasi qonunchiligiga muvofiq tegishli sudda ko'rib chiqiladi.
      </p>
      <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
        4.2. Ushbu shartnoma onlayn tizimda tasdiqlanganda elektron raqamli imzo orqali yuridik kuchga ega bo'ladi va tomonlarning har biri uchun qat'iy majburiy hisoblanadi.
      </p>

      <!-- Signatures table -->
      <div style="margin-top: 36px; padding-top: 20px; border-top: 1px solid #cbd5e1; page-break-inside: avoid;">
        <table style="width: 100%; border-collapse: collapse; font-size: 11pt;">
          <tr>
            <td style="width: 50%; vertical-align: top; padding-right: 15px;">
              <strong>IJROCHI:</strong><br/>
              <strong>${companyName || 'Konsalting Kompaniyasi'}</strong><br/>
              Rasmiy xizmat ko'rsatish portali<br/>
              M.O'. ____________________ (Imzo)
            </td>
            <td style="width: 50%; vertical-align: top; padding-left: 15px;">
              <strong>BUYURTMACHI:</strong><br/>
              Jismoniy shaxs (Abituriyent / Talaba)<br/>
              Pasport: ____________________<br/>
              Imzo: ____________________
            </td>
          </tr>
        </table>
      </div>
    </div>
  `
}
