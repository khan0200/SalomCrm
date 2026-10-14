import json
import re
from django.core.management.base import BaseCommand
from apps.students.models import Contract, TariffOption

class Command(BaseCommand):
    help = "Unify colliding elements on Page 1, Page 2, and Page 4 across ALL tariffs and contracts"

    def handle(self, *args, **options):
        merged_p2_content = """<div class="contract-section">
  <div style="direction: ltr; text-transform: uppercase; margin-bottom: 4px;">
    <p style="margin: 0 0 4px 0;"><span style="color: rgb(0, 0, 0);"><b>Bajaruvchining huquq va majburiyatlari</b></span></p>
  </div>
  <ul style="direction: ltr; text-transform: none; margin: 0 0 10px 0; padding-left: 1.6em;">
    <li style="list-style: disc; margin-bottom: 2px;"><span>Bajaruvchi Mijoz hujjatlarini o'z vaqtida tegishli universitetlarga topshiradi, unga maslahat beradi hamda konsultatsiya taqdim etadi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Bajaruvchi Mijozning fikri o'zgarishi yoki boshqa xolat sababli o'qishni davom ettirolmagan taqdirda Universitet yoki boshqalarga qilingan har qanday turdagi to'lovlarni qaytarib berishga ma'sul emas.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Mijozga viza chiqmagan taqdirda Universitetga to‘langan invoice to‘lovini shahsan o‘zi qaytarib oladi, Bajaruvchi bu jarayonda Mijozga yordam beradi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Bajaruvchi Mijoz Universitetga invoys to‘lovlarini amalga oshirganidan so‘ng bajaruvchi 3 oy ichida Koreya Elchixonasiga viza uchun hujjat topshirib, natijasini olib beradi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Agar Bajaruvchining xatosi sababli mijozning hujjatlari noto‘g‘ri topshirilgan bo‘lsa, mijoz o‘qishga qabul qilinmasa: qayta xizmat bepul ko‘rsatiladi yoki to‘lov qaytarib beriladi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Bajaruvchi Mijoz tomonidan taqdim etilgan hujjat va ma’lumotlarning to‘g‘riligiga javobgar emas. Soxta yoki noto‘g‘ri ma’lumot aniqlangan taqdirda Bajaruvchi xizmat ko‘rsatishni to‘xtatish huquqiga ega.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Universitet va Janubiy Koreya immigratsiya organlari, Elchixona tomonidan qabul qilinadigan yakuniy qarorlar Bajaruvchiga bog‘liq emas. Ushbu tashkilotlar qarorlari uchun Bajaruvchi javobgar hisoblanmaydi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Mijoz talab qilingan hujjatlarni o‘z vaqtida taqdim etmagan taqdirda, jarayon muddati uzayishi mumkin va buning uchun Bajaruvchi javobgar emas.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Bajaruvchi yuqorida ko‘rsatilmagan xizmatlardan tashqari xizmatlarni ko‘rsatishga majbur emas.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Mijoz tomonidan belgilangan muddatda to‘lov amalga oshirilmagan taqdirda Bajaruvchi xizmatni vaqtinchalik to‘xtatish huquqiga ega.</span></li>
  </ul>
  <div style="direction: ltr; text-transform: uppercase; margin-top: 8px; margin-bottom: 4px;">
    <p style="margin: 0 0 4px 0;"><b><span style="color: rgb(0, 0, 0);">Mijozning huquq va majburiyatlari</span></b></p>
  </div>
  <ul style="direction: ltr; text-transform: none; margin: 0; padding-left: 1.6em;">
    <li style="list-style: disc; margin-bottom: 2px;"><span>Mijoz Janubiy Koreya Respublikasi Universitetlari haqida ma'lumot, o'qish sharoitlari, talablari va shartnoma uchun invoys to'lovlari bilan tanishish huquqiga ega.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Mijoz Koreya Respublikasi Universitetlaridan biriga qabul qilinganligi haqida tasdiqlovchi hujjat (Admission letter, Acceptance letter) ni talab qilish huquqiga ega. (Shartnoma imzolanganidan so'ng, natijalar o'rtacha 3-6 oy muddatda universitet tomonidan e’lon qilinadi).</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Mijoz Universitet va Janubiy Koreya elchixonasi tomonidan talab qilingan barcha hujjatlarni Bajaruvchiga o‘z vaqtida taqdim etishga, muddati o‘tgan va yaroqsiz hujjatlarni yangilab berishga majbur.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Mijozga Elchixona tomonidan Viza berilmagan, Koreyada o'qish fikridan qaytgan xolatlarda Universitetga to‘langan to‘lov (Invoysda ko‘rsatiladi) 45-90 kun muddat ichida shaxsan o'zi orqali qaytarib oladi va shunday huquqga ega.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Universitet tomonidan o‘quvchilarga yotoqxona yashash majburiy qilingan taqdirda, Mijoz yotoqxona to‘lovini shahsan o‘zi amalga oshiradi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Yotoqxonada turish majburiy qilinmagan xolatlarda, Universitetga yaqin joydan kvartira topishga amaliy yordam Bajaruvchi tomonidan taqdim etiladi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Koreyada yuzaga kelgan intizomiy, huquqiy yoki moliyaviy muammolar uchun Bajaruvchi javobgar emas.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Mijoz konsulting bilan shartnoma qilganidan so‘ng huddi shunday boshqa bir konsulting firma bilan shartnoma orqali hamkorlik qilmasik majburiyatini oladi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Universitet tomonidan Universitetga to‘langan kontrakt to‘lovini qaytarish rad etilgan taqdirda, Bajaruvchi ushbu mablag‘ni o‘z hisobidan qaytarib berishga majbur emas.</span></li>
  </ul>
</div>"""

        merged_p2_element = {
            "id": "text_p2_merged_rights",
            "type": "text",
            "x": 12.7,
            "y": 12.7,
            "width": 184.6,
            "height": 265.0,
            "zIndex": 1,
            "content": merged_p2_content,
            "style": {
                "fontFamily": "Times New Roman",
                "fontSize": 10.5,
                "fontWeight": "normal",
                "fontStyle": "normal",
                "textAlign": "justify",
                "color": "#000000",
                "lineHeight": 1.35,
                "backgroundColor": "transparent"
            }
        }

        merged_p4_content = """<div class="contract-section">
  <div style="direction: ltr; text-transform: uppercase; margin-bottom: 4px;">
    <p style="margin: 0 0 4px 0;"><b><span>Nizolarni hal qilish va shartnomani bekor qilish tartibi:</span></b></p>
  </div>
  <ul style="direction: ltr; text-transform: none; margin: 0 0 8px 0; padding-left: 1.6em;">
    <li style="list-style: disc; margin-bottom: 2px;"><span>Nizolar muzokaralar yo'li bilan xal qilinishi mumkin bo'lmasa, barcha nizolar O'zbekiston Respublikasi qonun hujjatlarida belgilangan tartibda hal etiladi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Firmaga qilingan 100% to'lov mijozga Elchixona tomonidan viza berilmagan taqdirdagina talabani arizasiga muvofiq qaytarib beriladi. Qaytarib berish muddati: Talaba tomonidan ariza yozilib, Viza berilmagani aniq bo'lgan sanadan boshlab 15 kun muddat ichida.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Ushbu Shartnoma shartida ko'rsatilmagan barcha masalalar, tomonlar O'zbekiston Respublikasining amaldagi qonun hujjatlari bilan tartibga solinadi.</span></li>
  </ul>
  <div style="direction: ltr; text-transform: uppercase; margin-top: 6px; margin-bottom: 4px;">
    <p style="margin: 0 0 4px 0;"><b><span>SHARTNOMANING FAOLIYAT MUDDATI</span></b></p>
  </div>
  <ul style="direction: ltr; text-transform: none; margin: 0 0 8px 0; padding-left: 1.6em;">
    <li style="list-style: disc; margin-bottom: 2px;"><span>Ushbu shartnoma tomonlar imzolagan kundan boshlab qonuniy kuchga kiradi va shartnomaning faoliyati muddati 270 kalendar kuni deb xisoblanadi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Shartnoma shartlariga zid kelishi mumkin bo'lgan xolatlarda, ushbu shartnomani imzolashdan oldin bajaruvchi bilan Mijoz o'rtasidagi barcha og'zaki muzokaralar olib boriladi, agar bunda ziddiyatlar ro'y bersa shartnoma imzolanmaydi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Shartnoma o'zbek tilida, 2 nusxada, har biri bir xil qonuniy kuchga ega, Bajaruvchi birinchi va Mijoz ikkinchi nusxasini olish huquqiga ega.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Shartnomaga qo'shimcha, o'zgartirish, to'lovlarga chegirma, kelishuvsiz o'zgartirishlar kiritilmaydi.</span></li>
  </ul>
  <div style="direction: ltr; text-transform: uppercase; margin-top: 6px; margin-bottom: 4px;">
    <p style="margin: 0 0 4px 0;"><b><span>FORS-MAJOR</span></b></p>
  </div>
  <ul style="direction: ltr; text-transform: none; margin: 0; padding-left: 1.6em;">
    <li style="list-style: disc; margin-bottom: 2px;"><span>Favqulotda holatlar yuzaga kelgan taqdirda, (Pandemiya aviareyslar, viza berilishi to'xtatilishi, harbiy harakatlar, elchixona qarorlari o'zgarishi) shu kabi boshqa holatlarda tomonlar o'z majburiyatlarini vaqtinchalik bajarishdan ozod etiladi va o'zaro kelishuv orqali hal qilinadi.</span></li>
    <li style="list-style: disc; margin-bottom: 2px;"><span>Yuqorida ko'rsatilgan xolatar yuzaga kelgan taqdirda, tomonlar bir birini og'zaki va yozma tarzda ogohlantiradi, ogohlantirish xolatni tasdiqlovchi hujjat taqdim etilishi lozim.</span></li>
  </ul>
</div>"""

        merged_p4_element = {
            "id": "text_p4_merged_legal",
            "type": "text",
            "x": 12.7,
            "y": 14.7,
            "width": 184.6,
            "height": 165.0,
            "zIndex": 1,
            "content": merged_p4_content,
            "style": {
                "fontFamily": "Times New Roman",
                "fontSize": 11.0,
                "fontWeight": "normal",
                "fontStyle": "normal",
                "textAlign": "justify",
                "color": "#000000",
                "lineHeight": 1.3,
                "backgroundColor": "transparent"
            }
        }

        def is_legacy_legal_element(content, y=None):
            c = (content or '').lower()
            is_keyword = any(k in c for k in [
                'nizolar', 'faoliyat', 'fors-major', 'favqulotda', 'bekor qilish', '<hr'
            ]) or c.strip() in ['<p><strong>3</strong></p>', '<p style="text-align: right;"><strong>3</strong></p>']
            if is_keyword:
                return True
            if y is not None and y < 175:
                is_requisite = any(r in c for r in ['bajaruvchi', 'mijoz', 'inn:', 'f.i.o', 'passport'])
                if not is_requisite:
                    return True
            return False

        def optimize_document_pages(doc):
            pages = doc.get('pages', [])
            if not pages:
                return False

            modified = False

            # --- OPTIMIZE PAGE 1 ---
            p1 = pages[0]
            p1_elements = p1.get('elements', [])
            has_merged_p1 = any(el.get('id') == 'text_p1_merged_body' for el in p1_elements)

            if not has_merged_p1 and len(p1_elements) >= 10:
                top_els = []
                body_els = []
                pg_els = []
                discount_el = None

                for el in p1_elements:
                    c_str = (el.get('content') or '')
                    y = el.get('y', 0)
                    el_type = el.get('type')

                    if '{{page_number}}' in c_str or y > 275:
                        pg_els.append(el)
                    elif '{{discount}}' in c_str and 80 <= y <= 125:
                        discount_el = el
                    elif y < 75 or el_type == 'checkbox':
                        top_els.append(el)
                    else:
                        body_els.append(el)

                if len(body_els) >= 2:
                    body_els.sort(key=lambda e: e.get('y', 0))

                    # Inline discount into pricing paragraph
                    for b in body_els:
                        content_str = b.get('content') or ''
                        if 'chegirma miqdori' in content_str.lower():
                            inline_discount = '<span style="font-weight: bold; text-decoration: underline;">&nbsp;{{discount}}&nbsp;so\'m</span>'
                            if re.search(r'_{2,}\s*so\'?m', content_str, re.IGNORECASE):
                                content_str = re.sub(r'_{2,}\s*so\'?m', inline_discount, content_str, flags=re.IGNORECASE)
                            elif re.search(r'_{2,}', content_str):
                                content_str = re.sub(r'_{2,}', inline_discount, content_str)
                            else:
                                content_str = re.sub(r'(chegirma miqdori:\s*)', r'\1' + inline_discount + ' ', content_str, flags=re.IGNORECASE)
                            b['content'] = content_str

                    # Merge body elements HTML
                    p1_parts = []
                    for b in body_els:
                        c = (b.get('content') or '').strip()
                        if c:
                            p1_parts.append(c)

                    merged_p1_content = '<div class="contract-section">' + ''.join(p1_parts) + '</div>'
                    first_y = body_els[0].get('y', 78.0)
                    total_h = sum(b.get('height', 10) for b in body_els)

                    merged_p1_element = {
                        "id": "text_p1_merged_body",
                        "type": "text",
                        "x": 12.7,
                        "y": first_y,
                        "width": 184.6,
                        "height": total_h,
                        "zIndex": 1,
                        "content": merged_p1_content,
                        "style": {
                            "fontFamily": "Times New Roman",
                            "fontSize": 11.0,
                            "fontWeight": "normal",
                            "fontStyle": "normal",
                            "textAlign": "justify",
                            "color": "#000000",
                            "lineHeight": 1.35,
                            "backgroundColor": "transparent"
                        }
                    }

                    p1['elements'] = top_els + [merged_p1_element] + pg_els
                    modified = True

            # --- OPTIMIZE PAGE 2 ---
            if len(pages) >= 2:
                p2 = pages[1]
                p2_elements = p2.get('elements', [])
                has_merged_p2 = any(el.get('id') == 'text_p2_merged_rights' for el in p2_elements)
                p2_rights_count = sum(1 for el in p2_elements if el.get('type') == 'text' and 'majburiyat' in el.get('content', '').lower())

                if not has_merged_p2 and p2_rights_count > 1:
                    pgnum_p2 = [el for el in p2_elements if 'page_number' in el.get('content', '')]
                    p2['elements'] = [merged_p2_element] + pgnum_p2
                    modified = True

            # --- OPTIMIZE PAGE 4 ---
            if len(pages) >= 4:
                p4 = pages[3]
                p4_elements = p4.get('elements', [])
                has_merged_p4 = any(el.get('id') == 'text_p4_merged_legal' for el in p4_elements)

                if has_merged_p4:
                    filtered_p4 = [
                        el for el in p4_elements
                        if el.get('id') == 'text_p4_merged_legal'
                        or not is_legacy_legal_element(el.get('content', ''), el.get('y'))
                    ]
                    if len(filtered_p4) != len(p4_elements):
                        p4['elements'] = filtered_p4
                        modified = True
                else:
                    legacy_legal_count = sum(1 for el in p4_elements if is_legacy_legal_element(el.get('content', ''), el.get('y')))
                    if legacy_legal_count >= 2:
                        rest_p4 = [
                            el for el in p4_elements
                            if not is_legacy_legal_element(el.get('content', ''), el.get('y'))
                        ]
                        p4['elements'] = [merged_p4_element] + rest_p4
                        modified = True

            return modified

        # 1. Update all TariffOption models
        for to in TariffOption.objects.all():
            if not to.contract_text or not to.contract_text.startswith('{'):
                continue
            try:
                doc = json.loads(to.contract_text)
                if optimize_document_pages(doc):
                    to.contract_text = json.dumps(doc, ensure_ascii=False)
                    to.save(update_fields=['contract_text'])
                    self.stdout.write(self.style.SUCCESS(f"Updated TariffOption: {to.name}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating TariffOption {to.name}: {e}"))

        # 2. Update all active Contracts with canvas_source
        contracts = Contract.objects.filter(canvas_source__isnull=False).exclude(canvas_source='')
        for c in contracts:
            try:
                doc = json.loads(c.canvas_source)
                if optimize_document_pages(doc):
                    c.canvas_source = json.dumps(doc, ensure_ascii=False)
                    # Sync plain content for non-canvas fallbacks
                    pages_html = []
                    for p in doc.get('pages', []):
                        p_html = [el['content'] for el in p.get('elements', []) if el.get('content')]
                        pages_html.append("\n".join(p_html))
                    c.content = '<hr data-page-break="true" />'.join(pages_html)
                    c.save(update_fields=['canvas_source', 'content'])
                    self.stdout.write(self.style.SUCCESS(f"Updated Contract: {c.contract_number} ({c.id})"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error updating Contract {c.id}: {e}"))
