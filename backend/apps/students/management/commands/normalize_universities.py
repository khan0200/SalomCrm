from django.core.management.base import BaseCommand
from django.db import transaction


# Research-verified rename map (see conversation history for sourcing):
# old UniversityOption.name -> new canonical name. Entries with no city/
# region suffix get one added; the last 4 entries are confirmed TRUE
# duplicates (same institution under a different name) that collapse into
# an already-existing canonical row.
NORMALIZE_MAP = {
    'Ansan University': 'ANSAN UNIVERSITY (SANGNOK-GU, ANSAN, GYEONGGI)',
    'Bucheon University': 'BUCHEON UNIVERSITY (WONMI-GU, BUCHEON, GYEONGGI)',
    'Busan Institute of Science and Technology': 'BUSAN INSTITUTE OF SCIENCE AND TECHNOLOGY (BUK-GU, BUSAN)',
    'CHA University': 'CHA UNIVERSITY (POCHEON, GYEONGGI)',
    'Changshin University': 'CHANGSHIN UNIVERSITY (MASANHOEWON-GU, CHANGWON, GYEONGNAM)',
    'Changwon National University': 'CHANGWON NATIONAL UNIVERSITY (CHANGWON, GYEONGNAM)',
    'Changwon National University Namhae Campus': 'CHANGWON NATIONAL UNIVERSITY NAMHAE CAMPUS (NAMHAE, GYEONGNAM)',
    'Cheju Halla University': 'CHEJU HALLA UNIVERSITY (JEJU-SI, JEJU)',
    'Daegu Catholic University': 'DAEGU CATHOLIC UNIVERSITY (HAYANG-EUP, GYEONGSAN, GYEONGBUK)',
    'Dankook University': 'DANKOOK UNIVERSITY (YONGIN/CHEONAN)',
    'Dongshin University': 'DONGSHIN UNIVERSITY (NAJU, JEONNAM)',
    'Eulji University': 'EULJI UNIVERSITY (SEONGNAM/DAEJEON)',
    'Gangseo University': 'GANGSEO UNIVERSITY (GANGSEO-GU, SEOUL)',
    'Geoje University': 'GEOJE UNIVERSITY (GEOJE, GYEONGNAM)',
    'Gumi University': 'GUMI UNIVERSITY (GUMI, GYEONGBUK)',
    'Gyeonggi Science and Technology University': 'GYEONGGI UNIVERSITY OF SCIENCE AND TECHNOLOGY (SIHEUNG, GYEONGGI)',
    'Gyeongkuk National University': 'ANDONG NATIONAL UNIVERSITY (ANDONG, GYEONGBUK)',
    'Gyeongnam Geochang University': 'GYEONGNAM GEOCHANG UNIVERSITY (GEOCHANG-EUP, GEOCHANG, GYEONGNAM)',
    'Gyeongsang National University': 'GYEONGSANG NATIONAL UNIVERSITY (JINJU, GYEONGNAM)',
    'Handong Global University': 'HANDONG GLOBAL UNIVERSITY (BUK-GU, POHANG, GYEONGBUK)',
    'Hansei University': 'HANSEI UNIVERSITY (GUNPO, GYEONGGI)',
    'Hanseo University': 'HANSEO UNIVERSITY (SEOSAN, CHUNGNAM)',
    "Hanyang Women's University": "HANYANG WOMEN'S UNIVERSITY (SEONGDONG-GU, SEOUL)",
    'Inje University': 'INJE UNIVERSITY (GIMHAE, GYEONGNAM)',
    'Jangan College': 'JANGAN UNIVERSITY (BONGDAM-EUP, HWASEONG, GYEONGGI)',
    'Jeju National University': 'JEJU NATIONAL UNIVERSITY (JEJU-SI, JEJU)',
    'Jeju Tourism University': 'JEJU TOURISM UNIVERSITY (AEWOL-EUP, JEJU-SI, JEJU)',
    'Jeonbuk Science College': 'JEONBUK SCIENCE COLLEGE (JEONGEUP, JEONBUK)',
    'Jeonju Vision College': 'JEONJU VISION COLLEGE (WANSAN-GU, JEONJU, JEONBUK)',
    'Jungwon University': 'JUNGWON UNIVERSITY (GOESAN-EUP, GOESAN, CHUNGBUK)',
    'Kangnam University': 'KANGNAM UNIVERSITY (GIHEUNG-GU, YONGIN, GYEONGGI)',
    'Keimyung College University': 'KEIMYUNG COLLEGE UNIVERSITY (DALSEO-GU, DAEGU)',
    'Kongju National University': 'KONGJU NATIONAL UNIVERSITY (GONGJU, CHUNGNAM)',
    'Konkuk University Glocal Campus': 'KONKUK UNIVERSITY GLOCAL CAMPUS (CHUNGJU, CHUNGBUK)',
    'Konyang University': 'KONYANG UNIVERSITY (NONSAN, CHUNGNAM)',
    'Korea Baptist University': 'KOREA BAPTIST UNIVERSITY (YUSEONG-GU, DAEJEON)',
    'Korea Maritime and Ocean University': 'KOREA MARITIME AND OCEAN UNIVERSITY (YEONGDO-GU, BUSAN)',
    'Korea Media Arts University': 'KOREA UNIVERSITY OF MEDIA ARTS (SEJONG)',
    'Korea National University of Education': 'KOREA NATIONAL UNIVERSITY OF EDUCATION (CHEONGJU, CHUNGBUK)',
    'Korea National University of Transportation': 'KOREA NATIONAL UNIVERSITY OF TRANSPORTATION (CHUNGJU, CHUNGBUK)',
    'Korea Nazarene University': 'KOREA NAZARENE UNIVERSITY (SEOBUK-GU, CHEONAN, CHUNGNAM)',
    'Korea University of Technology and Education': 'KOREA UNIVERSITY OF TECHNOLOGY AND EDUCATION (DONGNAM-GU, CHEONAN, CHUNGNAM)',
    'Kosin University': 'KOSIN UNIVERSITY (YEONGDO-GU, BUSAN)',
    'Kumoh National Institute of Technology': 'KUMOH NATIONAL INSTITUTE OF TECHNOLOGY (GUMI, GYEONGBUK)',
    'Kunsan National University': 'KUNSAN NATIONAL UNIVERSITY (GUNSAN, JEONBUK)',
    "Kwangju Women's University": "KWANGJU WOMEN'S UNIVERSITY (GWANGSAN-GU, GWANGJU)",
    'Kwangwoon University': 'KWANGWOON UNIVERSITY (NOWON-GU, SEOUL)',
    'Kyungdong University': 'KYUNGDONG UNIVERSITY (GOSEONG/WONJU, GANGWON)',
    'Kyungil University': 'KYUNGIL UNIVERSITY (HAYANG-EUP, GYEONGSAN, GYEONGBUK)',
    "Kyungin Women's University": "KYUNGIN WOMEN'S UNIVERSITY (GYEYANG-GU, INCHEON)",
    'Kyungnam College of Information & Technology': 'KYUNGNAM COLLEGE OF INFORMATION & TECHNOLOGY (SASANG-GU, BUSAN)',
    'Kyungnam University': 'KYUNGNAM UNIVERSITY (MASANHAPPO-GU, CHANGWON, GYEONGNAM)',
    'Kyungsung University': 'KYUNGSUNG UNIVERSITY (NAM-GU, BUSAN)',
    'Kyungwoon University': 'KYUNGWOON UNIVERSITY (SANDONG-EUP, GUMI, GYEONGBUK)',
    'Mokpo Science University': 'MOKPO SCIENCE UNIVERSITY (MOKPO, JEONNAM)',
    'Mokwon University': 'MOKWON UNIVERSITY (SEO-GU, DAEJEON)',
    'Myongji College': 'MYONGJI COLLEGE (SEODAEMUN-GU, SEOUL)',
    'Pai Chai University': 'PAI CHAI UNIVERSITY (SEO-GU, DAEJEON)',
    'Sangmyung University': 'SANGMYUNG UNIVERSITY (JONGNO-GU, SEOUL)',
    'Seokyeong University': 'SEOKYEONG UNIVERSITY (SEONGBUK-GU, SEOUL)',
    'Seoul Christian University': 'SEOUL CHRISTIAN UNIVERSITY (EUNPYEONG-GU, SEOUL)',
    'Seoul Institute of the Arts': 'SEOUL INSTITUTE OF THE ARTS (DANWON-GU, ANSAN, GYEONGGI)',
    'Seoul National University of Science and Technology': 'SEOUL NATIONAL UNIVERSITY OF SCIENCE AND TECHNOLOGY (NOWON-GU, SEOUL)',
    'Seoul Theological University': 'SEOUL THEOLOGICAL UNIVERSITY (SOSA-GU, BUCHEON, GYEONGGI)',
    "Seoul Women's University": "SEOUL WOMEN'S UNIVERSITY (NOWON-GU, SEOUL)",
    'Shinhan University': 'SHINHAN UNIVERSITY (UIJEONGBU, GYEONGGI)',
    'Silla University': 'SILLA UNIVERSITY (SASANG-GU, BUSAN)',
    "Sookmyung Women's University": "SOOKMYUNG WOMEN'S UNIVERSITY (YONGSAN-GU, SEOUL)",
    'Soonchunhyang University': 'SOONCHUNHYANG UNIVERSITY (ASAN, CHUNGNAM)',
    'Soongsil University': 'SOONGSIL UNIVERSITY (DONGJAK-GU, SEOUL)',
    'Sunchon National University': 'SUNCHON NATIONAL UNIVERSITY (SUNCHEON, JEONNAM)',
    'Sungkonghoe University': 'SUNGKONGHOE UNIVERSITY (GURO-GU, SEOUL)',
    'Sungkyul University': 'SUNGKYUL UNIVERSITY (MANAN-GU, ANYANG, GYEONGGI)',
    'Sunmoon University': 'SUNMOON UNIVERSITY (TANGJEONG-MYEON, ASAN, CHUNGNAM)',
    'The Catholic University of Korea': 'THE CATHOLIC UNIVERSITY OF KOREA (SEOUL/BUCHEON)',
    'Uiduk University': 'UIDUK UNIVERSITY (GANGDONG-MYEON, GYEONGJU, GYEONGBUK)',
    'Ulsan College': 'ULSAN COLLEGE (ULSAN)',
    'University of Seoul': 'UNIVERSITY OF SEOUL (DONGDAEMUN-GU, SEOUL)',
    'University of Ulsan': 'UNIVERSITY OF ULSAN (NAM-GU, ULSAN)',
    'Wonkwang Health Science University': 'WONKWANG HEALTH SCIENCE UNIVERSITY (IKSAN, JEONBUK)',
    'Yeungjin University': 'YEUNGJIN UNIVERSITY (BUK-GU, DAEGU)',
    'Yong-In University of Arts and Science': 'YONG-IN UNIVERSITY OF ARTS AND SCIENCE (CHEOIN-GU, YONGIN, GYEONGGI)',

    # Confirmed true duplicates: old name -> already-correct canonical name.
    # These rows get DELETED (not renamed) once any Student references are
    # repointed, since the canonical name already exists as a separate row.
    'Daelim University College': 'DAELIM UNIVERSITY (ANYANG, GYEONGGI)',
    'DONG EUI COLLEGE (BUSANJIN, BUSAN)': 'DONG-EUI UNIVERSITY (BUSANJIN, BUSAN)',
    'Incheon National University': 'INCHEON UNIVERSITY (YEONSU, INCHEON)',
    'Kunjang University': 'KUNJANG UNIVERSITY COLLEGE (GUNSAN, JEONBUK)',
}


class Command(BaseCommand):
    help = (
        "Normalizes UniversityOption names to uppercase with a consistent "
        "'(CITY/DISTRICT, REGION)' suffix, and merges 4 confirmed true "
        "duplicates (same institution under a different name) into their "
        "already-existing canonical row. Any Student university_1..5 field "
        "referencing a renamed/merged name is updated to match. Runs as a "
        "dry-run report unless --apply is passed."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually write changes. Without this flag, only reports what would change.',
        )
        parser.add_argument(
            '--tenant',
            default='unibridge',
            help="Tenant id to normalize (default: unibridge).",
        )

    def handle(self, *args, **options):
        from apps.students.models import UniversityOption, Student

        apply_changes = options['apply']
        tenant_id = options['tenant']

        qs = UniversityOption.objects.filter(tenant_id=tenant_id)
        by_name = {u.name: u for u in qs}

        renames = []       # (old_name, new_name, option_id) - simple uppercase/city-suffix rename
        merges = []        # (old_name, canonical_name, old_option_id, canonical_option_id)
        uppercase_only = []  # (old_name, new_name, option_id) - already had a suffix, just needs case fix

        for uni in qs:
            if uni.name in NORMALIZE_MAP:
                target_name = NORMALIZE_MAP[uni.name]
                if target_name in by_name and by_name[target_name].id != uni.id:
                    merges.append((uni.name, target_name, uni.id, by_name[target_name].id))
                else:
                    renames.append((uni.name, target_name, uni.id))
            else:
                target_name = uni.name.strip().upper()
                target_name = ' '.join(target_name.split())
                if target_name != uni.name:
                    uppercase_only.append((uni.name, target_name, uni.id))

        self.stdout.write(self.style.NOTICE(f"Tenant: {tenant_id}"))
        self.stdout.write(f"\n=== Simple renames (add city suffix): {len(renames)} ===")
        for old, new, _id in renames:
            self.stdout.write(f"  id={_id}  {old!r} -> {new!r}")

        self.stdout.write(f"\n=== Uppercase-only fixes: {len(uppercase_only)} ===")
        for old, new, _id in uppercase_only:
            self.stdout.write(f"  id={_id}  {old!r} -> {new!r}")

        self.stdout.write(f"\n=== Merges into existing canonical row: {len(merges)} ===")
        student_updates_needed = []
        for old, canonical, old_id, canonical_id in merges:
            affected = []
            for i in range(1, 6):
                field = f'university_{i}'
                n = Student.objects.filter(tenant_id=tenant_id, **{field: old}).count()
                if n:
                    affected.append((field, n))
            self.stdout.write(
                f"  id={old_id} {old!r} -> id={canonical_id} {canonical!r} "
                f"(deletes id={old_id}; {sum(n for _, n in affected)} student field(s) to repoint)"
            )
            if affected:
                student_updates_needed.append((old, canonical, affected))

        total_changes = len(renames) + len(uppercase_only) + len(merges)
        self.stdout.write(self.style.WARNING(f"\nTotal UniversityOption rows affected: {total_changes}"))

        if not apply_changes:
            self.stdout.write(self.style.NOTICE(
                "Dry run only — no changes made. Re-run with --apply to write changes."
            ))
            return

        with transaction.atomic():
            # 1. Repoint any Student rows referencing a name that's about to be merged away.
            for old, canonical, _affected in student_updates_needed:
                for i in range(1, 6):
                    field = f'university_{i}'
                    for student in Student.objects.filter(tenant_id=tenant_id, **{field: old}):
                        setattr(student, field, canonical)
                        student.save(update_fields=[field, 'updated_at'])

            # 2. Delete the now-unreferenced duplicate UniversityOption rows.
            merge_ids = [old_id for _, _, old_id, _ in merges]
            if merge_ids:
                UniversityOption.objects.filter(id__in=merge_ids).delete()

            # 3. Apply simple renames and uppercase-only fixes.
            for old, new, _id in renames + uppercase_only:
                UniversityOption.objects.filter(id=_id).update(name=new)

        self.stdout.write(self.style.SUCCESS(
            f"Applied: {len(renames)} renames, {len(uppercase_only)} uppercase fixes, "
            f"{len(merges)} merges ({len(merge_ids)} rows deleted)."
        ))
