from django.db import migrations


GUARDIAN_TARIFF_NAME = "Kafillik shartnomasi (18 yoshga to'lmaganlar uchun)"

GUARDIAN_CONTRACT_HTML = """
<div style="font-family: 'Times New Roman', Times, serif; font-size: 13.5px; line-height: 1.65; color: #0f172a; padding: 24px 28px;">
  <!-- Header -->
  <div style="text-align: center; margin-bottom: 22px; border-bottom: 1.5px solid #0f172a; padding-bottom: 16px;">
    <h2 style="margin: 0 0 6px 0; font-size: 15pt; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;">
      Kafillik to'g'risida shartnoma
    </h2>
    <div style="font-size: 10.5pt; font-weight: 600; color: #334155; margin-bottom: 4px;">
      (18 yoshga to'lmagan talaba nomidan ota-ona / vasiy tomonidan tuziladigan ilova hujjat)
    </div>
    <div style="font-size: 10pt; color: #64748b;">
      Asosiy shartnoma № <strong>{{studentId}}</strong> ilovasi &nbsp;|&nbsp; {{branch}}, &laquo;{{date}}&raquo;
    </div>
  </div>

  <!-- Preamble -->
  <p style="text-align: justify; text-indent: 1.25cm; margin: 10px 0;">
    Quyida imzo chekuvchi ota-ona / qonuniy vakil / vasiy (bundan buyon &mdash; <strong>&laquo;Kafil&raquo;</strong>):
  </p>
  <table style="width: 100%; border-collapse: collapse; font-size: 11.5pt; margin: 6px 0 14px 0;">
    <tr>
      <td style="width: 50%; padding: 3px 8px 3px 0; border-bottom: 1px solid #94a3b8;">F.I.O: ____________________________________</td>
      <td style="width: 50%; padding: 3px 0 3px 8px; border-bottom: 1px solid #94a3b8;">Talabaga qarindoshligi: ______________________</td>
    </tr>
    <tr>
      <td style="padding: 8px 8px 3px 0; border-bottom: 1px solid #94a3b8;">Pasport: ____________________________________</td>
      <td style="padding: 8px 0 3px 8px; border-bottom: 1px solid #94a3b8;">Telefon: ______________________________________</td>
    </tr>
    <tr>
      <td colspan="2" style="padding: 8px 0 3px 0; border-bottom: 1px solid #94a3b8;">Yashash manzili: ____________________________________________________________</td>
    </tr>
  </table>
  <p style="text-align: justify; text-indent: 1.25cm; margin: 10px 0;">
    va ikkinchi tomondan &laquo;Korxona&raquo; o'rtasida, quyidagi voyaga yetmagan talaba nomidan tuzilgan
    № <strong>{{studentId}}</strong> raqamli, &laquo;{{date}}&raquo; sanadagi ta'lim konsalting xizmati ko'rsatish
    shartnomasi (bundan buyon &mdash; <strong>&laquo;Asosiy shartnoma&raquo;</strong>) bilan bog'liq holda tuzildi:
  </p>
  <table style="width: 100%; border-collapse: collapse; font-size: 11.5pt; margin: 6px 0 16px 0;">
    <tr>
      <td style="width: 60%; padding: 3px 8px 3px 0; border-bottom: 1px solid #94a3b8;">Talaba (voyaga yetmagan): <strong>{{fullname}}</strong></td>
      <td style="width: 40%; padding: 3px 0 3px 8px; border-bottom: 1px solid #94a3b8;">Tug'ilgan sana: <strong>{{dateofbirth}}</strong></td>
    </tr>
    <tr>
      <td colspan="2" style="padding: 8px 0 3px 0; border-bottom: 1px solid #94a3b8;">Pasport: <strong>{{passportnumber}}</strong></td>
    </tr>
  </table>

  <!-- 1 -->
  <h3 style="font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;">1. Shartnoma predmeti</h3>
  <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
    1.1. Kafil, O'zbekiston Respublikasi Fuqarolik kodeksining 27-moddasiga muvofiq, voyaga yetmagan Talaba tomonidan
    Asosiy shartnomaning tuzilishiga o'zining yozma roziligini beradi va Talabaning Asosiy shartnoma bo'yicha barcha
    majburiyatlarini, jumladan to'lov majburiyatlarini, o'z zimmasiga to'liq javobgarlik sifatida oladi.
  </p>
  <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
    1.2. Kafilning roziligisiz Asosiy shartnoma haqiqiy hisoblanmaydi va Fuqarolik kodeksining 27-moddasiga ko'ra
    bekor qilinishi mumkin bo'lgan bitim sifatida e'tirof etiladi.
  </p>

  <!-- 2 -->
  <h3 style="font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;">2. Kafilning huquq va majburiyatlari</h3>
  <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
    2.1. Kafil Asosiy shartnoma bo'yicha barcha to'lovlarning o'z vaqtida va to'liq amalga oshirilishini ta'minlaydi
    hamda Talabaning shartnoma shartlariga rioya etishini nazorat qiladi.
  </p>
  <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
    2.2. Kafil Korxona bilan Talabaga oid barcha xabarlar va bildirishnomalarni olish huquqiga ega.
  </p>

  <!-- 3 -->
  <h3 style="font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;">3. Kafilning javobgarligi</h3>
  <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
    3.1. Talaba Asosiy shartnoma bo'yicha o'z majburiyatini (jumladan, to'lovni) bajarmagan yoki lozim darajada
    bajarmagan taqdirda, Kafil Korxona oldida Talaba bilan birgalikda (solidar) javobgar bo'ladi.
  </p>
  <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
    3.2. Kafil Asosiy shartnomaning barcha bandlari, shu jumladan bekor qilish va qaytarish shartlari bilan
    tanishganini va ularga to'liq roziligini o'z imzosi bilan tasdiqlaydi.
  </p>

  <!-- 4 -->
  <h3 style="font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;">4. Elektron shaklda tuzilishi</h3>
  <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
    4.1. Tomonlar ushbu Kafillik shartnomasi Korxonaning axborot tizimi orqali elektron shaklda tuzilishi va
    Kafilning grafik (qo'lda chizilgan) imzosi, elektron pochta orqali tasdiqlash kodi hamda tizim tomonidan
    qayd etilgan sana, IP-manzil va qurilma ma'lumotlari birgalikda qo'lyozma imzoga tenglashtirilishini tan
    oladilar. Elektron nusxa qog'oz nusxa bilan bir xil yuridik kuchga ega (&laquo;Elektron tijorat to'g'risida&raquo;gi
    O'RQ-792-son Qonun, 14&ndash;15-moddalar).
  </p>

  <!-- 5 -->
  <h3 style="font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;">5. Amal qilish muddati</h3>
  <p style="text-align: justify; text-indent: 1.25cm; margin: 8px 0;">
    5.1. Ushbu Kafillik shartnomasi Asosiy shartnoma amal qilish muddati davomida yoki Talaba 18 (o'n sakkiz)
    yoshga to'lgunga qadar, qaysi biri keyin kelsa, o'sha vaqtgacha amalda bo'ladi.
  </p>

  <!-- Signatures -->
  <div style="margin-top: 28px; padding-top: 18px; border-top: 1px solid #cbd5e1; page-break-inside: avoid;">
    <table style="width: 100%; border-collapse: collapse; font-size: 11pt;">
      <tr>
        <td style="width: 50%; vertical-align: top; padding-right: 15px;">
          <strong>KORXONA VAKILI:</strong><br/>
          ____________________________<br/>
          Imzo: ______________________<br/>
          Sana: {{date}}
        </td>
        <td style="width: 50%; vertical-align: top; padding-left: 15px;">
          <strong>KAFIL (ota-ona / vasiy):</strong><br/>
          F.I.O: ______________________<br/>
          Imzo: ______________________<br/>
          Sana: {{date}}
        </td>
      </tr>
    </table>
    <p style="margin-top: 14px; font-size: 10.5pt; color: #475569;">
      Talaba bilan tanishtirildi: <strong>{{fullname}}</strong> &nbsp; Imzo/tasdiq: ______________________
    </p>
  </div>
</div>
""".strip()


def add_guardian_tariff(apps, schema_editor):
    Tenant = apps.get_model('tenants', 'Tenant')
    TariffOption = apps.get_model('students', 'TariffOption')

    for tenant in Tenant.objects.all():
        exists = TariffOption.objects.filter(
            tenant=tenant, name=GUARDIAN_TARIFF_NAME
        ).exists()
        if exists:
            continue
        TariffOption.objects.create(
            tenant=tenant,
            name=GUARDIAN_TARIFF_NAME,
            price=0,
            contract_text=GUARDIAN_CONTRACT_HTML,
            is_active=False,
        )


def remove_guardian_tariff(apps, schema_editor):
    TariffOption = apps.get_model('students', 'TariffOption')
    TariffOption.objects.filter(name=GUARDIAN_TARIFF_NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0018_student_tariff_price'),
    ]

    operations = [
        migrations.RunPython(add_guardian_tariff, remove_guardian_tariff),
    ]
