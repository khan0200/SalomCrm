"""
Default option lists given to every tenant.

These are per-tenant defaults, not shared rows: a new tenant starts from the
same list, and whatever it adds, renames or deletes afterwards affects only
that tenant.
"""

DEFAULT_UNIVERSITY_STATUSES = [
    ('Chosen', 'text-blue-500'),
    ('Applying', 'text-amber-500'),
    ('Applied', 'text-indigo-500'),
    ('Accepted', 'text-emerald-500'),
    ('Failed', 'text-rose-500'),
]


# Snapshot of the university catalogue as of 2026-08-28 (176 names, deduped
# across all tenants at that time). Fixed on purpose: a tenant's own later
# additions/renames must never leak into other tenants' defaults, so this
# list is not regenerated from live data. To refresh it, run
# `manage.py snapshot_default_universities` and replace the list below.
DEFAULT_UNIVERSITIES = [
    'AJOU UNIVERSITY (SUWON, GYEONGGI)',
    'ANYANG UNIVERSITY (ANYANG, GYEONGGI)',
    'Ansan University',
    'BAEKSEOK UNIVERSITY (CHEONAN, CHUNGNAM)',
    'BUSAN UNIVERSITY OF FOREIGN STUDIES (GEUMJEONG, BUSAN)',
    'Bucheon University',
    'Busan Institute of Science and Technology',
    'CHA University',
    'CHEONGAM UNIVERSITY (SUNCHEON, JEONNAM)',
    'CHEONGJU UNIVERSITY (CHEONGJU, CHUNGBUK)',
    'CHONNAM NATIONAL UNIVERSITY (BUK-GU, GWANGJU)',
    'CHOSUN UNIVERSITY (DONG-GU, GWANGJU)',
    'CHUNG-ANG UNIVERSITY (DONGJAK, SEOUL)',
    'CHUNGBUK HEALTH & SCIENCE UNIVERSITY (CHEONJU, CHUNGBUK)',
    'CHUNGBUK NATIONAL UNIVERSITY (CHEONGJU, CHUNGBUK)',
    'CHUNGCHEONG COLLEGE (CHEONGJU, CHUNCHEONG-BUK DO)',
    'CHUNGNAM NATIONAL UNIVERSITY (YUSEONG, DAEJEON)',
    'Changshin University',
    'Changwon National University',
    'Changwon National University Namhae Campus',
    'Cheju Halla University',
    'DAEGU HAANY UNIVERSITY (GYEONGSAN, GYEONGBUK)',
    'DAEGU UNIVERSITY (GYEONGSAN, GYEONGBUK)',
    'DAEJIN UNIVERSITY (POCHEON, GYEONGGI)',
    'DAELIM UNIVERSITY (ANYANG, GYEONGGI)',
    'DAESHIN UNIVERSITY (GYEONGSAN, GYEONGBUK)',
    'DAEWON UNIVERSITY COLLEGE (JECHEON, CHUNGBUK)',
    'DONG EUI COLLEGE (BUSANJIN, BUSAN)',
    'DONG-A UNIVERSITY (SAHA, BUSAN)',
    'DONG-EUI INSTITUTE OF TECHNOLOGY (BUSANJIN, BUSAN)',
    'DONG-EUI UNIVERSITY (BUSANJIN, BUSAN)',
    "DONGDUK WOMEN'S UNIVERSITY (SEONGBUK, SEOUL)",
    'DONGSEO UNIVERSITY (SASANG, BUSAN)',
    'DONGWON INSTITUTE OF SCIENCE AND TECHNOLOGY (YANGSAN, GYEONGNAM)',
    "DUKSUNG WOMEN'S UNIVERSITY (DOBONG, SEOUL)",
    'Daegu Catholic University',
    'Daelim University College',
    'Dankook University',
    'Dongguk University (WISE Campus)',
    'Dongshin University',
    'EWHA WOMANS UNIVERSITY (SEODAEMUN, SEOUL)',
    'Eulji University',
    'FAR EAST UNIVERSITY (EUMSEONG, CHUNGBUK)',
    'GACHON UNIVERSITY (SEONGNAM, GYEONGGI)',
    'GIMCHEON UNIVERSITY (GIMCHEON, GYEONGBUK)',
    'GIST (Gwangju Institute of Science and Technology)',
    'GWANGJU UNIVERSITY (NAM-GU, GWANGJU)',
    'Gangseo University',
    'Geoje University',
    'Gumi University',
    'Gyeonggi Science and Technology University',
    'Gyeongkuk National University',
    'Gyeongnam Geochang University',
    'Gyeongsang National University',
    'HALLYM UNIVERSITY (CHUNCHEON, GANGWON)',
    'HANBAT NATIONAL UNIVERSITY (YUSEONG, DAEJEON)',
    'HANKUK UNIVERSITY OF FOREIGN STUDIES (DONGDAEMUN, SEOUL)',
    'HANNAM UNIVERSITY (DAEDEOK, DAEJEON)',
    'HANSUNG UNIVERSITY (SEONGBUK, SEOUL)',
    'HANYANG UNIVERSITY (SEONGDONG, SEOUL)',
    'HONGIK UNIVERSITY (MAPO, SEOUL)',
    'HOSEO UNIVERSITY (ASAN, CHUNGNAM)',
    'Handong Global University',
    'Hansei University',
    'Hanseo University',
    "Hanyang Women's University",
    'INCHEON UNIVERSITY (YEONSU, INCHEON)',
    'INDUK UNIVERSITY (NOWON, SEOUL)',
    'INHA TECHNICAL COLLEGE (1%)',
    'INHA UNIVERSITY (MICHUHOL, INCHEON)',
    'Incheon National University',
    'Inje University',
    'JEONBUK NATIONAL UNIVERSITY (DEOKJIN, JEONJU)',
    'JEONJU UNIVERSITY (WANSAN, JEONJU)',
    'JOONGBU UNIVERSITY (GEUMSAN, CHUNGNAM)',
    'Jangan College',
    'Jeju National University',
    'Jeju Tourism University',
    'Jeonbuk Science College',
    'Jeonju Vision College',
    'Jungwon University',
    'KAIST (YUSEONG, DAEJEON)',
    'KANGWON NATIONAL UNIVERSITY (CHUNCHEON, GANGWON)',
    'KEIMYUNG UNIVERSITY (DALSEO, DAEGU)',
    'KONKUK UNIVERSITY (GWANGJIN, SEOUL)',
    'KOOKMIN UNIVERSITY (SEONGBUK, SEOUL)',
    'KOREA UNIVERSITY (SEONGBUK, SEOUL)',
    'KOREAN AEROSPACE UNIVERSITY (GOYANG, GYEONGGI)',
    'KUNJANG UNIVERSITY COLLEGE (GUNSAN, JEONBUK)',
    'KYONGGI UNIVERSITY (SUWON, GYEONGGI)',
    'KYUNG HEE UNIVERSITY (DONGDAEMUN, SEOUL)',
    'KYUNGBOK UNIVERSITY (NAMYANGJU, GYEONGGI)',
    'KYUNGPOOK NATIONAL UNIVERSITY (BUK-GU, DAEGU)',
    'Kangnam University',
    'Keimyung College University',
    'Kongju National University',
    'Konkuk University Glocal Campus',
    'Konyang University',
    'Korea Baptist University',
    'Korea Maritime and Ocean University',
    'Korea Media Arts University',
    'Korea National University of Education',
    'Korea National University of Transportation',
    'Korea Nazarene University',
    'Korea University of Technology and Education',
    'Kosin University',
    'Kumoh National Institute of Technology',
    'Kunjang University',
    'Kunsan National University',
    "Kwangju Women's University",
    'Kwangwoon University',
    'Kyungdong University',
    'Kyungil University',
    "Kyungin Women's University",
    'Kyungnam College of Information & Technology',
    'Kyungnam University',
    'Kyungsung University',
    'Kyungwoon University',
    'MOKPO NATIONAL UNIVERSITY (MOKPO, JEONNAM)',
    'Mokpo Science University',
    'Mokwon University',
    'Myongji College',
    'Myongji University (Seoul Campus)',
    'NAMSEOUL UNIVERSITY (CHEONAN, CHUNGNAM)',
    'OSAN UNIVERSITY (OSAN, GYEONGGI)',
    'PUKYONG NATIONAL UNIVERSITY (NAM-GU, BUSAN)',
    'PUSAN NATIONAL UNIVERSITY (GEUMJEONG, BUSAN)',
    'PYEONGTAEK UNIVERSITY (PYEONGTAEK, GYEONGGI)',
    'Pai Chai University',
    'Pohang University of Science and Technology (POSTECH)',
    'SAHMYOOK UNIVERSITY (NOWON, SEOUL)',
    'SEJONG UNIVERSITY (GWANGJIN, SEOUL)',
    'SEMYUNG UNIVERSITY (JECHEON, CHUNGBUK)',
    'SEOJEONG UNIVERSITY (YANGJU, GYEONGGI)',
    'SEOUL MEDIA INSTITUTE OF TECHNOLOGY (SMIT) (GANGSEO, SEOUL)',
    'SEOUL NATIONAL UNIVERSITY (GWANAK, SEOUL)',
    'SEOYEONG UNIVERSITY (PAJU, GYEONGGI)',
    'SOGANG UNIVERSITY (MAPO, SEOUL)',
    'SUNCHEON JEIL COLLEGE (SUNCHEON, JEONNAM)',
    'SUNGKYUNKWAN UNIVERSITY (JONGNO, SEOUL)',
    'SUNGSHIN WOMENS UNIVERSITY (SEONGBUK, SEOUL)',
    'Sangmyung University',
    'Seokyeong University',
    'Seoul Christian University',
    'Seoul Institute of the Arts',
    'Seoul National University of Science and Technology',
    'Seoul Theological University',
    "Seoul Women's University",
    'Shinhan University',
    'Silla University',
    "Sookmyung Women's University",
    'Soonchunhyang University',
    'Soongsil University',
    'Sunchon National University',
    'Sungkonghoe University',
    'Sungkyul University',
    'Sunmoon University',
    'TONGMYONG UNIVERSITY (NAM-GU, BUSAN)',
    'TONGWON UNIVERSITY (GWANGJU, GYEONGGI)',
    'The Catholic University of Korea',
    'Uiduk University',
    'Ulsan College',
    'Ulsan National Institute of Science and Technology (UNIST)',
    'University of Seoul',
    'University of Ulsan',
    'WONKWANG UNIVERSITY (IKSAN, JEONBUK)',
    'WOOSONG UNIVERSITY (DONG-GU, DAEJEON)',
    'WOOSUK UNIVERSITY (WANJU, JEONBUK)',
    'Wonkwang Health Science University',
    'YEUNGNAM UNIVERSITY (GYEONGSAN, GYEONGBUK)',
    'YEUNGNAM UNIVERSITY COLLEGE (NAM-GU, DAEGU)',
    'YONSEI UNIVERSITY (SEODAEMUN, SEOUL)',
    'YONSEI UNIVERSITY MIRAE CAMPUS (WONJU, GANGWON)',
    'YOUNG-SAN UNIVERSITY (YANGSAN, GYEONGNAM)',
    'Yeungjin University',
    'Yong-In University of Arts and Science',
]


def seed_default_options(tenant):
    """
    Give `tenant` the default universities and university statuses.

    Idempotent: existing names are left alone, so this is safe to re-run and
    will not clobber a tenant's own edits.
    """
    from .models import UniversityOption, UniversityStatusOption

    # ── University statuses ───────────────────────────────────────────
    existing_statuses = {
        (n or '').strip().lower()
        for n in UniversityStatusOption.objects.filter(tenant=tenant).values_list('name', flat=True)
    }
    for name, color in DEFAULT_UNIVERSITY_STATUSES:
        if name.lower() not in existing_statuses:
            UniversityStatusOption.objects.create(
                name=name, color_class=color, tenant=tenant
            )

    # ── Universities ──────────────────────────────────────────────────
    # Seeded from the fixed DEFAULT_UNIVERSITIES snapshot above, not from
    # another tenant's live data — a tenant's later additions/renames must
    # never leak into other tenants' defaults.
    existing_unis = {
        (n or '').strip().lower()
        for n in UniversityOption.objects.filter(tenant=tenant).values_list('name', flat=True)
    }

    seen = set()
    to_create = []
    for raw in DEFAULT_UNIVERSITIES:
        name = (raw or '').strip()
        key = name.lower()
        if not name or key in seen or key in existing_unis:
            continue
        seen.add(key)
        to_create.append(UniversityOption(name=name, tenant=tenant))

    if to_create:
        UniversityOption.objects.bulk_create(to_create)

    # ── Branches / Offices ────────────────────────────────────────────
    from apps.tenants.models import Branch
    if not Branch.objects.filter(tenant=tenant).exists():
        Branch.objects.create(name='TOSHKENT OFFIS', tenant=tenant)

    # ── Payment Methods ───────────────────────────────────────────────
    from apps.payments.models import PaymentMethodTemplate, PaymentNotePill
    DEFAULT_PAYMENT_METHODS = ['CARD', 'CASH', 'BANK']
    existing_methods = {
        (n or '').strip().lower()
        for n in PaymentMethodTemplate.objects.filter(tenant=tenant).values_list('name', flat=True)
    }
    for m in DEFAULT_PAYMENT_METHODS:
        if m.lower() not in existing_methods:
            PaymentMethodTemplate.objects.create(name=m, tenant=tenant)

    # ── Quick Note Templates ──────────────────────────────────────────
    DEFAULT_NOTE_PILLS = ['DISCOUNT', 'SHARTNOMA UCHUN', 'QARZ', 'ELCHIXONA UCHUN']
    existing_notes = {
        (n or '').strip().lower()
        for n in PaymentNotePill.objects.filter(tenant=tenant).values_list('name', flat=True)
    }
    for n in DEFAULT_NOTE_PILLS:
        if n.lower() not in existing_notes:
            PaymentNotePill.objects.create(name=n, tenant=tenant)

    # ── Default Folders ───────────────────────────────────────────────
    from apps.students.models import Folder
    if not Folder.objects.filter(tenant=tenant, name__iexact='KDB').exists():
        Folder.objects.create(name='KDB', tenant=tenant)

    # ── Guardian (kafillik) consent appendix ────────────────────────────
    # Inactive and free (see TariffOption.is_active docstring): editable from
    # the Contracts menu, never selectable by a student, never used as a
    # standalone contract - only ever attached as an appendix for minors.
    from apps.students.models import TariffOption
    if not TariffOption.objects.filter(tenant=tenant, name=GUARDIAN_TARIFF_NAME).exists():
        TariffOption.objects.create(
            tenant=tenant,
            name=GUARDIAN_TARIFF_NAME,
            price=0,
            contract_text=DEFAULT_GUARDIAN_CONTRACT_TEXT,
            is_active=False,
        )


GUARDIAN_TARIFF_NAME = "Kafillik shartnomasi (18 yoshga to'lmaganlar uchun)"

# Snapshot as of 2026-09-18, taken from Unibridge's own edited version once it
# had the company-requisites block swapped from a baked-in tenant snapshot
# back to contractor_* tokens (so it renders correctly for whichever tenant
# it's seeded into). Fixed on purpose, same as DEFAULT_UNIVERSITIES above: a
# tenant's own later edits to this template must never leak into another
# tenant's default. Raw string on purpose - this is JSON text whose own
# backslash escapes must survive untouched.
DEFAULT_GUARDIAN_CONTRACT_TEXT = r'''{"version": 2, "type": "canvas-contract", "pageSize": {"width": 210, "height": 297, "unit": "mm"}, "margins": {"top": 20, "right": 15, "bottom": 20, "left": 25}, "defaultFontFamily": "Times New Roman", "defaultFontSize": 12, "pages": [{"id": "page_1_5iou1mv", "pageNumber": 1, "elements": [{"id": "heading_8t6xsal", "type": "heading", "headingLevel": 2, "x": 25, "y": 20, "width": 170, "height": 7.7, "zIndex": 1, "content": "<h2 style=\"margin: 0 0 6px 0; font-size: 15pt; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px;\">\n      Kafillik to'g'risida shartnoma\n    </h2>", "style": {"fontFamily": "Times New Roman", "fontSize": 14, "fontWeight": "bold", "color": "#111827", "textAlign": "center", "lineHeight": 1.3}}, {"id": "text_ss93eea", "type": "text", "x": 25, "y": 29, "width": 170, "height": 6.5, "zIndex": 2, "content": "<div style=\"font-size: 10.5pt; font-weight: 600; color: #334155; margin-bottom: 4px;\">\n      (18 yoshga to'lmagan talaba nomidan ota-ona / vasiy tomonidan tuziladigan ilova hujjat)\n    </div>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "text_92oveoz", "type": "text", "x": 25, "y": 39, "width": 170, "height": 6.3, "zIndex": 3, "content": "<div style=\"font-size: 10pt; color: #64748b;\">\n      Asosiy shartnoma № <strong>{{studentId}}</strong> ilovasi &nbsp;|&nbsp; {{branch}}, «{{date}}»\n    </div>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#0f172a", "textAlign": "justify", "lineHeight": 1.55, "fontWeight": "bold"}}, {"id": "text_k1icfhg", "type": "text", "x": 25, "y": 48, "width": 170, "height": 7.4, "zIndex": 4, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 10px 0;\">\n    Quyida imzo chekuvchi ota-ona / qonuniy vakil / vasiy (bundan buyon — <strong>«Kafil»</strong>):\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "table_55akknl", "type": "table", "x": 25, "y": 61.25, "width": 170, "height": 30, "zIndex": 5, "rows": 3, "cols": 2, "colWidths": [85, 85], "rowHeights": [10, 10, 10], "cells": [[{"id": "cell_xhvrbjy", "content": "F.I.O: ____________________________________", "textAlign": "left", "verticalAlign": "top", "borders": {"bottom": "1px solid rgb(148, 163, 184)"}}, {"id": "cell_rttl00y", "content": "Talabaga qarindoshligi: ______________________", "textAlign": "left", "verticalAlign": "top", "borders": {"bottom": "1px solid rgb(148, 163, 184)"}}], [{"id": "cell_3jyvanz", "content": "Pasport: ____________________________________", "textAlign": "left", "verticalAlign": "top", "borders": {"bottom": "1px solid rgb(148, 163, 184)"}}, {"id": "cell_11r7fb4", "content": "Telefon: ______________________________________", "textAlign": "left", "verticalAlign": "top", "borders": {"bottom": "1px solid rgb(148, 163, 184)"}}], [{"id": "cell_nznrnad", "content": "Yashash manzili: ____________________________________________________________", "textAlign": "left", "verticalAlign": "top", "colSpan": 2, "borders": {"bottom": "1px solid rgb(148, 163, 184)"}}, {"id": "cell_tth962k", "content": "", "coveredBy": {"r": 2, "c": 0}}]], "borderWidth": "1px", "borderColor": "#94a3b8", "borderStyle": "solid", "density": "normal"}, {"id": "text_x3zths2", "type": "text", "x": 25, "y": 117, "width": 170, "height": 20.5, "zIndex": 6, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 10px 0;\">\n    va ikkinchi tomondan «Korxona» o'rtasida, quyidagi voyaga yetmagan talaba nomidan tuzilgan\n    № <strong>{{studentId}}</strong> raqamli, «{{date}}» sanadagi ta'lim konsalting xizmati ko'rsatish\n    shartnomasi (bundan buyon — <strong>«Asosiy shartnoma»</strong>) bilan bog'liq holda tuzildi:\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "table_h03ip4p", "type": "table", "x": 25, "y": 143, "width": 170, "height": 20, "zIndex": 7, "rows": 2, "cols": 2, "colWidths": [85, 85], "rowHeights": [10, 10], "cells": [[{"id": "cell_5hl9fdb", "content": "Passport number: {{passportnumber}}", "textAlign": "left", "verticalAlign": "top", "borders": {"bottom": "1px solid rgb(148, 163, 184)"}}, {"id": "cell_2n4l1mh", "content": "Tug'ilgan sana: <strong>{{dateofbirth}}</strong>", "textAlign": "left", "verticalAlign": "top", "borders": {"bottom": "1px solid rgb(148, 163, 184)"}}], [{"id": "cell_xpxsig3", "content": "<p><!--StartFragment--><span style=\"font-variant-ligatures: normal; font-variant-caps: normal; orphans: 2; text-transform: none; widows: 2; word-spacing: 0px; -webkit-text-stroke-width: 0px;\">Talaba (voyaga yetmagan): </span>{{fullname}}</p>", "textAlign": "left", "verticalAlign": "top", "colSpan": 2, "borders": {"bottom": "1px solid rgb(148, 163, 184)"}}, {"id": "cell_qr9pqaf", "content": "", "coveredBy": {"r": 1, "c": 0}}]], "borderWidth": "1px", "borderColor": "#94a3b8", "borderStyle": "solid", "density": "normal"}, {"id": "heading_b8ofeym", "type": "heading", "headingLevel": 3, "x": 25, "y": 167, "width": 170, "height": 6.3, "zIndex": 8, "content": "<h3 style=\"font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;\">1. Shartnoma predmeti</h3>", "style": {"fontFamily": "Times New Roman", "fontSize": 13, "fontWeight": "bold", "color": "#111827", "textAlign": "center", "lineHeight": 1.3}}, {"id": "text_gbmpehh", "type": "text", "x": 25, "y": 179, "width": 170, "height": 27, "zIndex": 9, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 8px 0;\">\n    1.1. Kafil, O'zbekiston Respublikasi Fuqarolik kodeksining 27-moddasiga muvofiq, voyaga yetmagan Talaba tomonidan\n    Asosiy shartnomaning tuzilishiga o'zining yozma roziligini beradi va Talabaning Asosiy shartnoma bo'yicha barcha\n    majburiyatlarini, jumladan to'lov majburiyatlarini, o'z zimmasiga to'liq javobgarlik sifatida oladi.\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "text_21g9910", "type": "text", "x": 25, "y": 209.5, "width": 170, "height": 13.9, "zIndex": 10, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 8px 0;\">\n    1.2. Kafilning roziligisiz Asosiy shartnoma haqiqiy hisoblanmaydi va Fuqarolik kodeksining 27-moddasiga ko'ra\n    bekor qilinishi mumkin bo'lgan bitim sifatida e'tirof etiladi.\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "heading_dgdsnye", "type": "heading", "headingLevel": 3, "x": 25, "y": 229, "width": 170, "height": 6.3, "zIndex": 11, "content": "<h3 style=\"font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;\">2. Kafilning huquq va majburiyatlari</h3>", "style": {"fontFamily": "Times New Roman", "fontSize": 13, "fontWeight": "bold", "color": "#111827", "textAlign": "center", "lineHeight": 1.3}}, {"id": "text_w95ezzx", "type": "text", "x": 25, "y": 239, "width": 170, "height": 13.9, "zIndex": 12, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 8px 0;\">\n    2.1. Kafil Asosiy shartnoma bo'yicha barcha to'lovlarning o'z vaqtida va to'liq amalga oshirilishini ta'minlaydi\n    hamda Talabaning shartnoma shartlariga rioya etishini nazorat qiladi.\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "text_1789712140653_tatd", "type": "text", "x": 25, "y": 258.3, "width": 170, "height": 13.9, "zIndex": 13, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 8px 0;\">\n    2.2. Kafil Korxona bilan Talabaga oid barcha xabarlar va bildirishnomalarni olish huquqiga ega.\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "var_1789713693339", "type": "text", "x": 34.63, "y": 61.25, "width": 72.9, "height": 7.1, "zIndex": 14, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{guardianfullname}}</p>", "variableKey": "guardianfullname", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}, {"id": "var_1789713728361", "type": "text", "x": 37.79, "y": 70.7, "width": 60, "height": 7.1, "zIndex": 15, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{guardianpassportnumber}}</p>", "variableKey": "guardianpassportnumber", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}, {"id": "var_1789713758380", "type": "text", "x": 142.17, "y": 61.25, "width": 60, "height": 7.1, "zIndex": 16, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{guardianrelation}}</p>", "variableKey": "guardianrelation", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}, {"id": "var_1789713805928", "type": "text", "x": 50, "y": 81.1, "width": 60, "height": 7.1, "zIndex": 17, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{guardianaddress}}</p>", "variableKey": "guardianaddress", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}, {"id": "var_1789713825010", "type": "text", "x": 123.58, "y": 71, "width": 60, "height": 7.1, "zIndex": 18, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{guardianphone}}</p>", "variableKey": "guardianphone", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}]}, {"id": "page_2_tgi8zqa", "pageNumber": 2, "elements": [{"id": "heading_fo4rybn", "type": "heading", "headingLevel": 3, "x": 25, "y": 20, "width": 170, "height": 6.3, "zIndex": 2, "content": "<h3 style=\"font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;\">3. Kafilning javobgarligi</h3>", "style": {"fontFamily": "Times New Roman", "fontSize": 13, "fontWeight": "bold", "color": "#111827", "textAlign": "center", "lineHeight": 1.3}}, {"id": "text_2zzblk8", "type": "text", "x": 25, "y": 30, "width": 170, "height": 20.5, "zIndex": 3, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 8px 0;\">\n    3.1. Talaba Asosiy shartnoma bo'yicha o'z majburiyatini (jumladan, to'lovni) bajarmagan yoki lozim darajada\n    bajarmagan taqdirda, Kafil Korxona oldida Talaba bilan birgalikda (solidar) javobgar bo'ladi.\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "text_vncpkrh", "type": "text", "x": 25, "y": 50.5, "width": 170, "height": 13.9, "zIndex": 4, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 8px 0;\">\n    3.2. Kafil Asosiy shartnomaning barcha bandlari, shu jumladan bekor qilish va qaytarish shartlari bilan\n    tanishganini va ularga to'liq roziligini o'z imzosi bilan tasdiqlaydi.\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "heading_hvvzbyj", "type": "heading", "headingLevel": 3, "x": 25, "y": 70, "width": 170, "height": 6.3, "zIndex": 5, "content": "<h3 style=\"font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;\">4. Elektron shaklda tuzilishi</h3>", "style": {"fontFamily": "Times New Roman", "fontSize": 13, "fontWeight": "bold", "color": "#111827", "textAlign": "center", "lineHeight": 1.3}}, {"id": "text_vgb5u4n", "type": "text", "x": 25, "y": 81, "width": 170, "height": 33.6, "zIndex": 6, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 8px 0;\">\n    4.1. Tomonlar ushbu Kafillik shartnomasi Korxonaning axborot tizimi orqali elektron shaklda tuzilishi va\n    Kafilning grafik (qo'lda chizilgan) imzosi, elektron pochta orqali tasdiqlash kodi hamda tizim tomonidan\n    qayd etilgan sana, IP-manzil va qurilma ma'lumotlari birgalikda qo'lyozma imzoga tenglashtirilishini tan\n    oladilar. Elektron nusxa qog'oz nusxa bilan bir xil yuridik kuchga ega («Elektron tijorat to'g'risida»gi\n    O'RQ-792-son Qonun, 14–15-moddalar).\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "heading_nzvfv37", "type": "heading", "headingLevel": 3, "x": 25, "y": 120.5, "width": 170, "height": 6.3, "zIndex": 7, "content": "<h3 style=\"font-size: 12pt; font-weight: bold; margin: 16px 0 8px 0; text-align: center;\">5. Amal qilish muddati</h3>", "style": {"fontFamily": "Times New Roman", "fontSize": 13, "fontWeight": "bold", "color": "#111827", "textAlign": "center", "lineHeight": 1.3}}, {"id": "text_9ln1lg1", "type": "text", "x": 25, "y": 131.5, "width": 170, "height": 20.5, "zIndex": 8, "content": "<p style=\"text-align: justify; text-indent: 1.25cm; margin: 8px 0;\">\n    5.1. Ushbu Kafillik shartnomasi Asosiy shartnoma amal qilish muddati davomida yoki Talaba 18 (o'n sakkiz)\n    yoshga to'lgunga qadar, qaysi biri keyin kelsa, o'sha vaqtgacha amalda bo'ladi.\n  </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "text_zh6raxs", "type": "text", "x": 25, "y": 272, "width": 170, "height": 6.5, "zIndex": 10, "content": "<p style=\"margin-top: 14px; font-size: 10.5pt; color: #475569;\">\n      Talaba bilan tanishtirildi: <strong>{{fullname}}</strong> &nbsp; Imzo/tasdiq: ______________________\n    </p>", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#111827", "textAlign": "justify", "lineHeight": 1.55}}, {"id": "req_1789713858386_l9eo", "type": "text", "x": 25, "y": 156.7, "width": 83, "height": 77.6, "zIndex": 11, "content": "<p style=\"text-align: center; margin: 0.3em 0 0.8em; font-weight: bold; letter-spacing: 0.5px;\">BAJARUVCHI</p>\n<p style=\"margin: 0.28em 0;\">{{contractor_company}} INN: {{contractor_inn}}</p>\n<p style=\"margin: 0.28em 0;\">GUVOHNOMA RAQAMI: {{contractor_certificate}}</p>\n<p style=\"margin: 0.28em 0;\">{{contractor_address}}</p>\n<p style=\"margin: 0.28em 0;\">TELEFON: {{contractor_phone}}</p>\n<p style=\"margin: 0.28em 0;\">OKED: {{contractor_oked}} | MFO: {{contractor_mfo}}</p>\n<p style=\"margin: 0.28em 0;\">H/R: {{contractor_account}}</p>\n<p style=\"margin: 0.28em 0;\">BANK: {{contractor_bank}}</p>\n<p style=\"display: flex; justify-content: space-between; align-items: baseline; margin: 0.28em 0; overflow: hidden;\">\n  <span>&nbsp;</span>\n  <span style=\"font-weight: normal; font-size: 0.85em; float: right;\">(M.O')</span>\n</p>\n<p style=\"margin: 0.28em 0;\">DIREKTOR: {{contractor_director}}</p>", "style": {"fontFamily": "Times New Roman", "fontSize": 11, "fontWeight": "bold", "fontStyle": "normal", "textAlign": "left", "color": "#000000", "lineHeight": 1.35}}, {"id": "var_1789713872131", "type": "text", "x": 89.08, "y": 217.1, "width": 60, "height": 7.1, "zIndex": 12, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{qr_code}}</p>", "variableKey": "qr_code", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}, {"id": "var_1789713905063", "type": "text", "x": 110, "y": 270.9, "width": 60, "height": 7.1, "zIndex": 13, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{signature}}</p>", "variableKey": "signature", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}, {"id": "text_1789713943466_b4ds", "type": "text", "x": 123.31, "y": 172.58, "width": 72.9, "height": 7.1, "zIndex": 12, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{guardianfullname}}</p>", "variableKey": "guardianfullname", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}, {"id": "text_1789713943466_uwhl", "type": "text", "x": 124.15, "y": 190.3, "width": 60, "height": 7.1, "zIndex": 13, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{guardianpassportnumber}}</p>", "variableKey": "guardianpassportnumber", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}, {"id": "text_1789713943466_qiv6", "type": "text", "x": 125.69, "y": 207.9, "width": 60, "height": 7.1, "zIndex": 14, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{guardianphone}}</p>", "variableKey": "guardianphone", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}, {"id": "text_1789713955835_qtar", "type": "text", "x": 139, "y": 156.29, "width": 33.38, "height": 6, "zIndex": 15, "content": "<p>KAFIL</p>", "style": {"fontFamily": "Times New Roman", "fontSize": 11, "fontWeight": "bold", "fontStyle": "normal", "textAlign": "left", "color": "#000000", "lineHeight": 1.35}}, {"id": "text_1789714014553_7cba", "type": "text", "x": 123.31, "y": 166.58, "width": 66.26, "height": 6, "zIndex": 16, "content": "<p>KAFILNING TO'LIQ F.I.SH:</p>", "style": {"fontFamily": "Times New Roman", "fontSize": 11, "fontWeight": "bold", "fontStyle": "normal", "textAlign": "left", "color": "#000000", "lineHeight": 1.35}}, {"id": "text_1789714058954_xn7j", "type": "text", "x": 123.31, "y": 182.9, "width": 66.26, "height": 6, "zIndex": 17, "content": "<p>KAFILNING PASSPORT RAQAMI:</p>", "style": {"fontFamily": "Times New Roman", "fontSize": 11, "fontWeight": "bold", "fontStyle": "normal", "textAlign": "left", "color": "#000000", "lineHeight": 1.35}}, {"id": "text_1789714099917_jg00", "type": "text", "x": 123.31, "y": 200, "width": 66.26, "height": 6, "zIndex": 18, "content": "<p>KAFILNING TELEFON RAQAMI:</p>", "style": {"fontFamily": "Times New Roman", "fontSize": 11, "fontWeight": "bold", "fontStyle": "normal", "textAlign": "left", "color": "#000000", "lineHeight": 1.35}}, {"id": "text_1789714120243_y4sv", "type": "text", "x": 124.15, "y": 219.1, "width": 66.26, "height": 6, "zIndex": 19, "content": "<p>KAFILNING IMZOSI: _____________</p>", "style": {"fontFamily": "Times New Roman", "fontSize": 11, "fontWeight": "bold", "fontStyle": "normal", "textAlign": "left", "color": "#000000", "lineHeight": 1.35}}, {"id": "var_1789714146070", "type": "text", "x": 163.69, "y": 218.1, "width": 40, "height": 7.1, "zIndex": 20, "content": "<p style=\"color: #2563eb; font-weight: bold;\">{{guardiansignature}}</p>", "variableKey": "guardiansignature", "style": {"fontFamily": "Times New Roman", "fontSize": 12, "color": "#2563eb"}}]}]}'''
