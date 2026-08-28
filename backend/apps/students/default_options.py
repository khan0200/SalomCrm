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
