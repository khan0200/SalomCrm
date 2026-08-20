import urllib.request
import json
from decimal import Decimal
from django.core.management.base import BaseCommand
from apps.tenants.models import Tenant
from apps.students.models import (
    Student, Folder, TariffOption, EducationLevelOption,
    StudentGroupOption, LeadSourceOption, CoordinatorOption,
    UniversityOption, UniversityStatusOption
)
from apps.payments.models import (
    PaymentMethodTemplate, PaymentReceiverTemplate, PaymentNotePill
)

class Command(BaseCommand):
    help = 'Fetches and synchronizes all real students, folders, and settings from Supabase into CRM'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Connecting to Supabase to fetch real data..."))

        supabase_url = "https://ilzghipeqjfnunrznngn.supabase.co"
        anon_key = "sb_publishable_kU3BWKbGrbhZFVY7AbNpmg_ldE8JWDE"

        # 1. Authenticate with Head Manager account to get user JWT with full access
        auth_url = f"{supabase_url}/auth/v1/token?grant_type=password"
        auth_data = json.dumps({
            "email": "abdurazzakov_97@mail.ru",
            "password": "robocode2023@"
        }).encode('utf-8')

        req = urllib.request.Request(
            auth_url,
            data=auth_data,
            headers={
                "apikey": anon_key,
                "Content-Type": "application/json"
            }
        )

        try:
            with urllib.request.urlopen(req) as response:
                auth_res = json.loads(response.read().decode('utf-8'))
                access_token = auth_res['access_token']
                self.stdout.write(self.style.SUCCESS("Authenticated with Supabase!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Supabase Auth Failed: {e}"))
            return

        headers = {
            "apikey": anon_key,
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        def fetch_table(table_name):
            try:
                url = f"{supabase_url}/rest/v1/{table_name}?select=*"
                r = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(r) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except Exception as ex:
                self.stdout.write(self.style.WARNING(f"Could not fetch {table_name}: {ex}"))
                return []

        tenant_ub, _ = Tenant.objects.get_or_create(
            slug='unibridge',
            defaults={
                'id': 'unibridge',
                'name': 'Unibridge Educational Consulting',
                'is_active': True,
                'branding_color': '#007aff',
            }
        )

        # 2. Sync Settings Tables from Supabase
        # 2.1 Tariffs
        tariffs = fetch_table('tariff_options')
        for t in tariffs:
            if t.get('name'):
                TariffOption.objects.update_or_create(
                    tenant=tenant_ub,
                    name=t['name'].strip(),
                    defaults={'price': Decimal(str(t.get('price') or 0))}
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(tariffs)} tariff options"))

        # 2.2 Education Levels
        levels = fetch_table('education_levels')
        for l in levels:
            if l.get('name'):
                EducationLevelOption.objects.update_or_create(
                    tenant=tenant_ub,
                    name=l['name'].strip()
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(levels)} education levels"))

        # 2.3 Student Groups
        groups = fetch_table('student_groups')
        for g in groups:
            if g.get('name'):
                StudentGroupOption.objects.update_or_create(
                    tenant=tenant_ub,
                    name=g['name'].strip()
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(groups)} student groups"))

        # 2.4 Lead Sources
        leads = fetch_table('lead_sources')
        for l in leads:
            if l.get('name'):
                LeadSourceOption.objects.update_or_create(
                    tenant=tenant_ub,
                    name=l['name'].strip()
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(leads)} lead sources"))

        # 2.5 Universities
        unis = fetch_table('universities')
        for u in unis:
            if u.get('name'):
                UniversityOption.objects.update_or_create(
                    tenant=tenant_ub,
                    name=u['name'].strip()
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(unis)} universities"))

        # 2.6 Coordinators
        coords = fetch_table('coordinators')
        for c in coords:
            if c.get('name'):
                CoordinatorOption.objects.update_or_create(
                    tenant=tenant_ub,
                    name=c['name'].strip()
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(coords)} coordinators"))

        # 2.7 Payment Methods
        pms = fetch_table('payment_methods')
        for m in pms:
            if m.get('name'):
                PaymentMethodTemplate.objects.update_or_create(
                    tenant=tenant_ub,
                    name=m['name'].strip()
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(pms)} payment methods"))

        # 2.8 Payment Receivers
        prs = fetch_table('payment_receivers')
        for r in prs:
            if r.get('name'):
                PaymentReceiverTemplate.objects.update_or_create(
                    tenant=tenant_ub,
                    name=r['name'].strip()
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(prs)} payment receivers"))

        # 2.9 Payment Note Templates
        pnts = fetch_table('payment_note_templates')
        for n in pnts:
            if n.get('name'):
                PaymentNotePill.objects.update_or_create(
                    tenant=tenant_ub,
                    name=n['name'].strip()
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(pnts)} payment note pills"))

        # 2.10 University Statuses
        ustatuses = fetch_table('university_statuses')
        for s in ustatuses:
            if s.get('name'):
                UniversityStatusOption.objects.update_or_create(
                    tenant=tenant_ub,
                    name=s['name'].strip(),
                    defaults={'color_class': s.get('color_class') or 'text-blue-500'}
                )
        self.stdout.write(self.style.SUCCESS(f"Synced {len(ustatuses)} university statuses"))

        # 3. Fetch & Sync Folders
        supabase_folders = fetch_table('folders')
        folder_map = {}
        for f in supabase_folders:
            folder_obj, _ = Folder.objects.update_or_create(
                tenant=tenant_ub,
                name=f['name']
            )
            folder_map[f['id']] = folder_obj

        # 4. Fetch & Sync Students
        students_url = f"{supabase_url}/rest/v1/students?select=*&order=id.asc"
        req_students = urllib.request.Request(students_url, headers=headers)
        with urllib.request.urlopen(req_students) as response:
            supabase_students = json.loads(response.read().decode('utf-8'))

        self.stdout.write(self.style.NOTICE(f"Fetched {len(supabase_students)} students from Supabase. Upserting..."))

        synced_count = 0
        for s in supabase_students:
            student_id = s.get('id')
            if not student_id:
                continue

            balance_val = Decimal(str(s.get('balance') or 0))
            discount_val = Decimal(str(s.get('discount') or 0))

            student_obj, created = Student.objects.update_or_create(
                id=student_id,
                defaults={
                    'tenant': tenant_ub,
                    'full_name': s.get('full_name') or 'Unnamed Student',
                    'korean_name': s.get('korean_name'),
                    'passport': s.get('passport'),
                    'passport_issue_date': s.get('passport_issue_date'),
                    'passport_expire_date': s.get('passport_expire_date'),
                    'gender': s.get('gender') or s.get('sex'),
                    'birthday': s.get('birthday'),
                    'phone1': s.get('phone1'),
                    'phone2': s.get('phone2'),
                    'father_name': s.get('father_name'),
                    'father_phone': s.get('father_phone'),
                    'father_job': s.get('father_job'),
                    'mother_name': s.get('mother_name'),
                    'mother_phone': s.get('mother_phone'),
                    'mother_job': s.get('mother_job'),
                    'email': s.get('email'),
                    'address': s.get('address'),
                    'level': s.get('level'),
                    'level2': s.get('level2'),
                    'educational_background': s.get('educational_background'),
                    'major': s.get('major'),
                    'final_school_name': s.get('final_school_name'),
                    'gpa': str(s.get('gpa') or '') if s.get('gpa') is not None else None,
                    'gpa_system': str(s.get('gpa_system') or '') if s.get('gpa_system') is not None else None,
                    'degree_no': s.get('degree_no'),
                    'date_of_entry': s.get('date_of_entry'),
                    'date_of_graduation': s.get('date_of_graduation'),
                    'graduation_expected': bool(s.get('graduation_expected', False)),
                    'school_address': s.get('school_address'),
                    'school_website': s.get('school_website'),
                    'school_phone': s.get('school_phone'),
                    'school_email': s.get('school_email'),
                    'tariff': s.get('tariff'),
                    'language_certificate': s.get('language_certificate'),
                    'certificate_score': s.get('certificate_score'),
                    'certificate_test_date': s.get('certificate_test_date'),
                    'certificate_valid_date': s.get('certificate_valid_date'),
                    'language_certificate_2': s.get('language_certificate_2'),
                    'certificate_score_2': s.get('certificate_score_2'),
                    'certificate_2_test_date': s.get('certificate_2_test_date'),
                    'certificate_2_valid_date': s.get('certificate_2_valid_date'),
                    'language_certificate_3': s.get('language_certificate_3'),
                    'certificate_score_3': s.get('certificate_score_3'),
                    'certificate_3_test_date': s.get('certificate_3_test_date'),
                    'certificate_3_valid_date': s.get('certificate_3_valid_date'),
                    'university_1': s.get('university_1'),
                    'university_1_status': s.get('university_1_status') or 'Chosen',
                    'university_1_major': s.get('university_1_major'),
                    'university_2': s.get('university_2'),
                    'university_2_status': s.get('university_2_status'),
                    'university_2_major': s.get('university_2_major'),
                    'university_3': s.get('university_3'),
                    'university_3_status': s.get('university_3_status'),
                    'university_3_major': s.get('university_3_major'),
                    'university_4': s.get('university_4'),
                    'university_4_status': s.get('university_4_status'),
                    'university_4_major': s.get('university_4_major'),
                    'university_5': s.get('university_5'),
                    'university_5_status': s.get('university_5_status'),
                    'university_5_major': s.get('university_5_major'),
                    'balance': balance_val,
                    'discount': discount_val,
                    'pick_needed': s.get('pick_needed') or [],
                    'has_mc': bool(s.get('has_mc', False)),
                    'bc_hand_count': int(s.get('bc_hand_count') or 0),
                    'mc_hand_count': int(s.get('mc_hand_count') or 0),
                    'apos_hand_count': int(s.get('apos_hand_count') or 0),
                    'pic_hand_count': int(s.get('pic_hand_count') or 0),
                    'office': s.get('office') or 'TOSHKENT OFFIS',
                    'student_group': s.get('student_group'),
                    'lead_by': s.get('lead_by'),
                    'coordinator': s.get('coordinator'),
                    'notes': s.get('notes'),
                    'is_deleted': bool(s.get('is_deleted', False)),
                    'row_color': s.get('row_color'),
                    'status_row_color': s.get('status_row_color'),
                    'task_tags': s.get('task_tags') or [],
                    'invoice': s.get('invoice') or 'NOT TAKEN',
                    'invoice_university': s.get('invoice_university'),
                    'coa': s.get('coa') or 'NOT TAKEN',
                    'embassy': s.get('embassy') or 'Not Applied',
                    'embassy_documents': s.get('embassy_documents') or [],
                    'status_hidden': bool(s.get('status_hidden', False)),
                    'kdb_put_date': s.get('kdb_put_date'),
                    'kdb_take_date': s.get('kdb_take_date'),
                    'embassy_father_docs': s.get('embassy_father_docs') or [],
                    'embassy_mother_docs': s.get('embassy_mother_docs') or [],
                    'embassy_sponsor_notes': s.get('embassy_sponsor_notes') or '',
                    'google_drive_url': s.get('google_drive_url'),
                    'google_drive_folder_id': s.get('google_drive_folder_id'),
                }
            )

            # Assign folders
            student_folder_ids = s.get('folder_ids') or []
            if s.get('folder_id'):
                student_folder_ids.append(s.get('folder_id'))

            assigned_folders = [folder_map[fid] for fid in student_folder_ids if fid in folder_map]
            if assigned_folders:
                student_obj.folders.set(assigned_folders)

            synced_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully synced {synced_count} students, {len(supabase_folders)} folders, and all settings options from Supabase into Salom CRM!"))
