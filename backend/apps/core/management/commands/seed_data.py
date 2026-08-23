from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, Branch
from apps.students.models import (
    Student, Folder, TariffOption, EducationLevelOption,
    StudentGroupOption, LeadSourceOption, CoordinatorOption
)
from apps.payments.models import (
    PaymentMethodTemplate, PaymentReceiverTemplate, PaymentNotePill
)
from apps.payments.services import record_payment

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds CRM database with Super Admin and Unibridge Head Manager (abdurazzakov_97@mail.ru)'

    def handle(self, *args, **options):
        self.stdout.write("Starting Uniapp v3 Database Seeding...")

        # 1. Platform Super Admin
        super_admin, created = User.objects.get_or_create(
            email='admin@uniapp.com',
            defaults={
                'full_name': 'Platform Super Administrator',
                'role': 'SUPER_ADMIN',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        super_admin.set_password('admin123456')
        super_admin.save()
        self.stdout.write(self.style.SUCCESS("Super Admin ready: admin@uniapp.com (Password: admin123456)"))

        # 2. Tenant: Unibridge
        tenant_ub, _ = Tenant.objects.get_or_create(
            slug='unibridge',
            defaults={
                'id': 'unibridge',
                'name': 'Unibridge Educational Consulting',
                'is_active': True,
                'branding_color': '#007aff',
                'description': 'Main Unibridge Consulting Agency'
            }
        )

        # Branches
        branch_andijon, _ = Branch.objects.get_or_create(tenant=tenant_ub, name='ANDIJON OFFIS', defaults={'code': 'AND'})
        branch_tashkent, _ = Branch.objects.get_or_create(tenant=tenant_ub, name='TOSHKENT OFFIS', defaults={'code': 'TSH'})

        # Folders
        folder_kdb, _ = Folder.objects.get_or_create(tenant=tenant_ub, name='KDB')
        folder_jeonju, _ = Folder.objects.get_or_create(tenant=tenant_ub, name='Jeonju')
        folder_woosuk, _ = Folder.objects.get_or_create(tenant=tenant_ub, name='WOOSUK')
        folder_next, _ = Folder.objects.get_or_create(tenant=tenant_ub, name='NEXT SEMESTER')
        folder_vip, _ = Folder.objects.get_or_create(tenant=tenant_ub, name='VIP 2026')
        folder_march, _ = Folder.objects.get_or_create(tenant=tenant_ub, name='March Intake')

        # 3. Unibridge Head Manager (abdurazzakov_97@mail.ru)
        head_manager, created = User.objects.get_or_create(
            email='abdurazzakov_97@mail.ru',
            defaults={
                'full_name': 'UNIBRIDGE HEAD MANAGER',
                'role': 'HEAD_MANAGER',
                'tenant': tenant_ub,
                'branch': branch_tashkent,
                'is_staff': True,
            }
        )
        head_manager.set_password('robocode2023@')
        head_manager.tenant = tenant_ub
        head_manager.role = 'HEAD_MANAGER'
        head_manager.save()
        self.stdout.write(self.style.SUCCESS("Unibridge Head Manager ready: abdurazzakov_97@mail.ru (Password: robocode2023@)"))

        # Remove any other demo users to keep ONLY these two accounts
        User.objects.exclude(email__in=['admin@uniapp.com', 'abdurazzakov_97@mail.ru']).delete()

        # 4. Seed Standard Options for Unibridge
        tariffs = [
            ('STANDART', Decimal('13000000')),
            ('PREMIUM', Decimal('32500000')),
            ('VISA PLUS', Decimal('65000000')),
            ('E-VISA (TIL SERTIFIKATISIZ)', Decimal('24000000')),
            ('E-VISA (TIL SERTIFIKATLI)', Decimal('16000000')),
            ('REGIONAL VISA', Decimal('24000000')),
            ('ZERO RISK', Decimal('18500000')),
            ('E-VISA', Decimal('2000000')),
        ]
        for name, price in tariffs:
            TariffOption.objects.get_or_create(tenant=tenant_ub, name=name, defaults={'price': price})

        levels = ['COLLEGE', 'BACHELOR', 'MASTERS', 'MASTER NO CERTIFICATE', 'LANGUAGE COURSE']
        for l in levels:
            EducationLevelOption.objects.get_or_create(tenant=tenant_ub, name=l)

        groups = ['2026 Spring', '2026 Fall', 'Fast Track', 'Group A', 'Group B']
        for g in groups:
            StudentGroupOption.objects.get_or_create(tenant=tenant_ub, name=g)

        leads = ['Instagram', 'Telegram', 'Tavsiya (Friend)', 'Banner', 'Office Walk-in']
        for lead in leads:
            LeadSourceOption.objects.get_or_create(tenant=tenant_ub, name=lead)

        coordinators = ['BAXTIYOR', 'MUHAMMADALI', 'MUSLIHIDDIN', 'ABDULAZIZ']
        for c in coordinators:
            CoordinatorOption.objects.get_or_create(tenant=tenant_ub, name=c)

        methods = ['Karta J.A', 'Karta Abdulaziz', 'Naqd', 'Karta M.A', 'Bank', 'Discount']
        for m in methods:
            PaymentMethodTemplate.objects.get_or_create(tenant=tenant_ub, name=m)

        receivers = ['ABDULAZIZ', 'MUSLIHIDDIN', 'BAXTIYOR', 'MUHAMMADALI', 'JASUR', 'ADMIN']
        for r in receivers:
            PaymentReceiverTemplate.objects.get_or_create(tenant=tenant_ub, name=r)

        pills = ['Shartnoma uchun', 'Qarz', 'Elchixona uchun', 'Appfee', 'DISCOUNT']
        for p in pills:
            PaymentNotePill.objects.get_or_create(tenant=tenant_ub, name=p)

        unis = [
            'JEONJU UNIVERSITY (WANSAN, JEONJU)',
            'WOOSUK UNIVERSITY (WANJU, JEOLLABUK-DO)',
            'HANYANG UNIVERSITY (SEONGDONG, SEOUL)',
            'INHA UNIVERSITY (MICHUHOL, INCHEON)',
            'SEJONG UNIVERSITY (GWANGJIN, SEOUL)',
            'KOOKMIN UNIVERSITY (SEONGBUK, SEOUL)',
            'YEUNGNAM UNIVERSITY (GYEONGSAN, GYEONGSANGBUK-DO)',
            'BUSAN UNIVERSITY OF FOREIGN STUDIES (GEUMJEONG, BUSAN)',
            'KYUNGPOOK NATIONAL UNIVERSITY (BUK-GU, DAEGU)',
        ]
        from apps.students.models import UniversityOption, UniversityStatusOption, TagOption
        for u in unis:
            UniversityOption.objects.get_or_create(tenant=tenant_ub, name=u)

        statuses = [
            ('Chosen', 'text-blue-500'),
            ('Applying', 'text-amber-500'),
            ('Applied', 'text-purple-500'),
            ('Waiting', 'text-orange-500'),
            ('Accepted', 'text-emerald-500'),
            ('Rejected', 'text-red-500'),
            ('Passed', 'text-teal-500'),
        ]
        for s_name, s_color in statuses:
            UniversityStatusOption.objects.get_or_create(tenant=tenant_ub, name=s_name, defaults={'color_class': s_color})

        tags_data = [
            ('HAL', '✅'),
            ('JEONJU REG', '📋'),
            ('KDB', '💳'),
            ('Natija kutilmoqda', '⏳'),
            ('Topik 2', '🏷️'),
            ('til kursi', '🏷️'),
            ('BUFS TIL KURSI', '🚩'),
            ('BUFS APPFEE', '🎫'),
            ('AeroSpace', '✈️'),
            ('GIMCHEON OK', '🏷️'),
            ('WOOSUK APPFEE', '💳'),
            ('Documents Pending', '📄'),
            ('Visa Processing', '🎫'),
            ('Visa Approved', '🛂'),
            ('Departure', '✈️'),
            ('Arrived', '📍'),
            ('Scholarship Awarded', '💎'),
            ('Call', '📞'),
            ('Apply', '🎓'),
            ('Documents', '📄'),
            ('Payment', '💰'),
        ]
        for t_name, t_icon in tags_data:
            TagOption.objects.update_or_create(tenant=tenant_ub, name=t_name, defaults={'icon': t_icon})

        # 5. Seed Sample Students for Unibridge
        sample_students = [
            {
                'id': 'CF2',
                'full_name': 'MAKHAMADAMINOV ABDULLOKH SANJARBEK UGLI',
                'passport': 'FA8877665',
                'phone1': '94-187-76-82',
                'phone2': '58-888-94-74',
                'level': 'COLLEGE',
                'tariff': None,
                'language_certificate': 'TOPIK',
                'certificate_score': '2',
                'office': 'TOSHKENT OFFIS',
                'student_group': '2026 Spring',
                'lead_by': 'Instagram',
                'coordinator': 'BAXTIYOR',
                'invoice': 'NOT TAKEN',
                'coa': 'NOT TAKEN',
                'folders': [folder_jeonju],
            },
            {
                'id': 'D1',
                'full_name': 'ISAKJONOV MUKHAMMADIYOR NAVRUZBEK UGLI',
                'passport': 'FB1122334',
                'phone1': '88-146-47-87',
                'phone2': '88-083-56-83',
                'level': 'COLLEGE',
                'level2': 'LANGUAGE COURSE',
                'tariff': 'VISA PLUS',
                'language_certificate': 'TOPIK',
                'certificate_score': '2',
                'office': 'ANDIJON OFFIS',
                'student_group': '2026 Spring',
                'lead_by': 'Telegram',
                'coordinator': 'ABDULAZIZ',
                'invoice': 'NOT TAKEN',
                'coa': 'NOT TAKEN',
                'folders': [folder_woosuk],
            },
            {
                'id': 'F4',
                'full_name': 'SUYUNOV ABDUSHUKUR ABDIMUMIN UGLI',
                'passport': 'FC9988112',
                'phone1': '91-188-08-68',
                'phone2': '91-134-06-01',
                'level': 'MASTERS',
                'tariff': 'E-VISA (TIL SERTIFIKATLI)',
                'language_certificate': 'TOPIK',
                'certificate_score': 'EXPECTED',
                'office': 'TOSHKENT OFFIS',
                'student_group': '2026 Fall',
                'lead_by': 'Instagram',
                'coordinator': 'MUHAMMADALI',
                'invoice': 'NOT TAKEN',
                'coa': 'NOT TAKEN',
                'folders': [folder_next],
            },
            {
                'id': 'F5',
                'full_name': 'SAIDBOEV SOKHIDULLO MIRZAKHMAD UGLI',
                'passport': 'FD4455667',
                'phone1': '94-252-15-10',
                'phone2': '50-886-60-38',
                'level': 'MASTER NO CERTIFICATE',
                'tariff': 'E-VISA (TIL SERTIFIKATSIZ)',
                'language_certificate': 'NO CERTIFICATE',
                'university_1': 'JEONJU UNIVERSITY (WANSAN, JEONJU)',
                'university_1_status': 'Accepted',
                'office': 'TOSHKENT OFFIS',
                'student_group': '2026 Spring',
                'lead_by': 'Tavsiya (Friend)',
                'coordinator': 'MUSLIHIDDIN',
                'invoice': 'PAID',
                'coa': 'TAKEN',
                'row_color': 'EMERALD',
                'folders': [folder_jeonju],
            },
            {
                'id': 'UB101',
                'full_name': 'RUSTAMOV AZIZBEK ANVAR OGLI',
                'korean_name': '루스타모프 아지즈벡',
                'passport': 'FA1234567',
                'phone1': '90-123-45-67',
                'level': 'BACHELOR',
                'tariff': 'PREMIUM',
                'language_certificate': 'TOPIK',
                'certificate_score': 'LEVEL 3',
                'university_1': 'SEJONG UNIVERSITY',
                'university_1_status': 'Accepted',
                'university_1_major': 'Business Administration',
                'university_2': 'KOOKMIN UNIVERSITY',
                'university_2_status': 'Applied',
                'office': 'TOSHKENT OFFIS',
                'student_group': '2026 Spring',
                'lead_by': 'Instagram',
                'coordinator': 'BAXTIYOR',
                'invoice': 'PAID',
                'coa': 'TAKEN',
                'kdb_put_date': '2026-08-10',
                'kdb_take_date': '2026-08-25',
                'embassy': 'PENDING',
                'embassy_father_docs': ['RASMIY ISH HAQQI', 'KADASTR'],
                'embassy_mother_docs': ['TEX.PASSPORT', 'BANKSHOT'],
                'embassy_sponsor_notes': 'Ota rasmiy firma egasi, oylik 15mln',
                'row_color': 'BLUE',
                'task_tags': ['Documents', 'Apply'],
                'folders': [folder_kdb, folder_vip],
            },
            {
                'id': 'UB102',
                'full_name': 'KARIMOV SHOHRUH BAXTIYOR OGLI',
                'korean_name': '카리모프 쇼흐루흐',
                'passport': 'FB9876543',
                'phone1': '99-876-54-32',
                'level': 'MASTERS',
                'tariff': 'STANDART',
                'language_certificate': 'IELTS',
                'certificate_score': '6.5',
                'university_1': 'HANYANG UNIVERSITY',
                'university_1_status': 'Chosen',
                'university_1_major': 'Computer Science',
                'office': 'ANDIJON OFFIS',
                'student_group': '2026 Spring',
                'lead_by': 'Tavsiya (Friend)',
                'coordinator': 'ABDULAZIZ',
                'invoice': 'TAKEN',
                'coa': 'NOT TAKEN',
                'kdb_put_date': '2026-08-15',
                'kdb_take_date': '2026-08-21',
                'embassy': 'APPROVED',
                'embassy_father_docs': ['KADASTR X2', 'DO\'KON'],
                'row_color': 'EMERALD',
                'folders': [folder_kdb],
            },
            {
                'id': 'UB103',
                'full_name': 'TOSHEVA NODIRA KOMILJON QIZI',
                'korean_name': '토셰바 노디라',
                'passport': 'FC5544332',
                'phone1': '93-456-78-90',
                'level': 'LANGUAGE COURSE',
                'tariff': 'E-VISA',
                'language_certificate': 'NO CERTIFICATE',
                'certificate_score': None,
                'university_1': 'YEUNGNAM UNIVERSITY',
                'university_1_status': 'Applying',
                'office': 'TOSHKENT OFFIS',
                'student_group': 'Fast Track',
                'lead_by': 'Telegram',
                'coordinator': 'MUSLIHIDDIN',
                'invoice': 'NOT TAKEN',
                'coa': 'NOT TAKEN',
                'row_color': 'YELLOW',
                'folders': [folder_march],
            },
            {
                'id': 'UB104',
                'full_name': 'ISMOILOV JAVOHIR SARDOR OGLI',
                'korean_name': '이스모일로프 자보히르',
                'passport': 'FD1122334',
                'phone1': '94-998-87-76',
                'level': 'COLLEGE',
                'tariff': 'VISA PLUS',
                'language_certificate': 'TOPIK',
                'certificate_score': 'LEVEL 2',
                'university_1': 'INHA UNIVERSITY',
                'university_1_status': 'Accepted',
                'office': 'TOSHKENT OFFIS',
                'student_group': '2026 Spring',
                'lead_by': 'Instagram',
                'coordinator': 'MUHAMMADALI',
                'invoice': 'PAID',
                'coa': 'TAKEN',
                'kdb_put_date': '2026-08-01',
                'kdb_take_date': '2026-08-18',
                'embassy': 'PENDING',
                'row_color': 'RED',
                'folders': [folder_kdb],
            },
            {
                'id': 'UB105',
                'full_name': 'ABDULLAYEV BEHZOD OLIM OGLI',
                'korean_name': '압둘라예프 베흐조드',
                'passport': 'FE9988776',
                'phone1': '91-333-22-11',
                'level': 'BACHELOR',
                'tariff': 'STANDART',
                'language_certificate': 'IELTS',
                'certificate_score': '5.5',
                'university_1': 'DONGGUK UNIVERSITY',
                'university_1_status': 'Chosen',
                'office': 'ANDIJON OFFIS',
                'student_group': 'Group A',
                'lead_by': 'Banner',
                'coordinator': 'BAXTIYOR',
                'invoice': 'NOT PAID',
                'coa': 'NOT TAKEN',
                'status_hidden': True,
                'folders': [],
            }
        ]

        for s_data in sample_students:
            folders_list = s_data.pop('folders', [])
            student_id = s_data['id']
            s_obj, created = Student.objects.get_or_create(
                id=student_id,
                defaults={
                    **s_data,
                    'tenant': tenant_ub,
                    'created_by': head_manager
                }
            )
            if folders_list:
                s_obj.folders.set(folders_list)

        # 6. Record Payments for UB101 & UB102
        s101 = Student.objects.get(id='UB101')
        record_payment(
            tenant=tenant_ub,
            student=s101,
            amount=Decimal('20000000'),
            method='Karta Abdulaziz',
            received_by='ABDULAZIZ',
            notes='Shartnoma uchun birinchi to\'lov (Contract 1st payment)',
            is_discount=False,
            user=head_manager
        )
        record_payment(
            tenant=tenant_ub,
            student=s101,
            amount=Decimal('2500000'),
            method='Discount',
            received_by='ADMIN',
            notes='DISCOUNT: Yangi yil aksiyasi (Holiday discount)',
            is_discount=True,
            user=head_manager
        )

        s102 = Student.objects.get(id='UB102')
        record_payment(
            tenant=tenant_ub,
            student=s102,
            amount=Decimal('13000000'),
            method='Bank',
            received_by='MUSLIHIDDIN',
            notes='To\'liq to\'lov qilindi (Full payment)',
            is_discount=False,
            user=head_manager
        )

        self.stdout.write(self.style.SUCCESS("Database seeded with exactly the requested accounts!"))
        self.stdout.write(self.style.SUCCESS("  1. Platform Super Admin: admin@uniapp.com / admin123456"))
        self.stdout.write(self.style.SUCCESS("  2. Unibridge Head Manager: abdurazzakov_97@mail.ru / robocode2023@"))
