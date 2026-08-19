import json
import urllib.request
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.tenants.models import Tenant, Branch
from apps.students.models import (
    Student, Folder, TariffOption, EducationLevelOption,
    StudentGroupOption, LeadSourceOption, CoordinatorOption
)
from apps.payments.models import (
    Payment, PaymentMethodTemplate, PaymentReceiverTemplate, PaymentNotePill
)

User = get_user_model()

SUPABASE_URL = "https://ilzghipeqjfnunrznngn.supabase.co"
SUPABASE_ANON_KEY = "sb_publishable_kU3BWKbGrbhZFVY7AbNpmg_ldE8JWDE"

class Command(BaseCommand):
    help = 'Imports all real students, payments, folders, and options from Supabase into Salom CRM'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Connecting to Supabase and authenticating as Unibridge Head Manager..."))

        # 1. Supabase Auth
        auth_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        auth_payload = json.dumps({
            'email': 'abdurazzakov_97@mail.ru',
            'password': 'robocode2023@'
        }).encode('utf-8')

        auth_req = urllib.request.Request(
            auth_url,
            data=auth_payload,
            headers={
                'apikey': SUPABASE_ANON_KEY,
                'Content-Type': 'application/json'
            }
        )

        try:
            with urllib.request.urlopen(auth_req) as resp:
                token_data = json.loads(resp.read().decode('utf-8'))
                access_token = token_data['access_token']
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to authenticate with Supabase: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("Authenticated with Supabase successfully!"))

        # Helper to query Supabase REST API
        def fetch_supabase_table(table_name):
            req = urllib.request.Request(
                f"{SUPABASE_URL}/rest/v1/{table_name}?select=*&limit=1000",
                headers={
                    'apikey': SUPABASE_ANON_KEY,
                    'Authorization': f"Bearer {access_token}"
                }
            )
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode('utf-8'))

        # 2. Ensure Super Admin and Unibridge Head Manager exist in local Django DB
        super_admin, _ = User.objects.get_or_create(
            email='admin@uniapp.com',
            defaults={'full_name': 'Platform Super Administrator', 'role': 'SUPER_ADMIN', 'is_staff': True, 'is_superuser': True}
        )
        super_admin.set_password('admin123456')
        super_admin.save()

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

        branch_tsh, _ = Branch.objects.get_or_create(tenant=tenant_ub, name='TOSHKENT OFFIS', defaults={'code': 'TSH'})
        branch_and, _ = Branch.objects.get_or_create(tenant=tenant_ub, name='ANDIJON OFFIS', defaults={'code': 'AND'})

        head_manager, _ = User.objects.get_or_create(
            email='abdurazzakov_97@mail.ru',
            defaults={
                'full_name': 'Jasurbek Head Manager',
                'role': 'HEAD_MANAGER',
                'tenant': tenant_ub,
                'branch': branch_tsh,
                'is_staff': True,
            }
        )
        head_manager.set_password('robocode2023@')
        head_manager.tenant = tenant_ub
        head_manager.role = 'HEAD_MANAGER'
        head_manager.save()

        # Keep ONLY these 2 demo accounts
        User.objects.exclude(email__in=['admin@uniapp.com', 'abdurazzakov_97@mail.ru']).delete()

        # 3. Fetch and Import Folders
        self.stdout.write(self.style.NOTICE("Fetching Folders from Supabase..."))
        sb_folders = fetch_supabase_table('folders')
        folder_map = {}
        for f_data in sb_folders:
            folder_obj, _ = Folder.objects.get_or_create(
                tenant=tenant_ub,
                name=f_data['name'].strip()
            )
            folder_map[f_data['id']] = folder_obj
            # Also map by name
            folder_map[f_data['name'].strip().lower()] = folder_obj

        # Ensure standard KDB folder exists
        folder_kdb, _ = Folder.objects.get_or_create(tenant=tenant_ub, name='KDB')
        folder_map['kdb'] = folder_kdb
        self.stdout.write(self.style.SUCCESS(f"Imported {Folder.objects.filter(tenant=tenant_ub).count()} Folders."))

        # 4. Fetch and Import Students
        self.stdout.write(self.style.NOTICE("Fetching Students from Supabase..."))
        sb_students = fetch_supabase_table('students')
        self.stdout.write(self.style.NOTICE(f"Fetched {len(sb_students)} students from Supabase. Importing..."))

        tariffs_set = set()
        levels_set = set()
        groups_set = set()
        leads_set = set()
        coordinators_set = set()

        imported_students_count = 0
        for s in sb_students:
            s_id = str(s.get('id', '')).strip().upper()
            if not s_id:
                continue

            full_name = str(s.get('full_name') or s.get('korean_name') or s_id).strip().upper()
            tariff_val = (s.get('tariff') or '').strip()
            level_val = (s.get('level') or '').strip().upper()
            group_val = (s.get('student_group') or '').strip()
            lead_val = (s.get('lead_by') or '').strip()
            coord_val = (s.get('coordinator') or '').strip()

            if tariff_val: tariffs_set.add(tariff_val)
            if level_val: levels_set.add(level_val)
            if group_val: groups_set.add(group_val)
            if lead_val: leads_set.add(lead_val)
            if coord_val: coordinators_set.add(coord_val)

            # Map raw fields to Student model
            student_defaults = {
                'full_name': full_name,
                'korean_name': s.get('korean_name'),
                'passport': s.get('passport'),
                'passport_issue_date': s.get('passport_issue_date'),
                'passport_expire_date': s.get('passport_expire_date'),
                'gender': s.get('gender'),
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
                'level': level_val or None,
                'level2': s.get('level2'),
                'educational_background': s.get('educational_background'),
                'major': s.get('major'),
                'final_school_name': s.get('final_school_name'),
                'gpa': s.get('gpa'),
                'gpa_system': s.get('gpa_system'),
                'degree_no': s.get('degree_no'),
                'date_of_entry': s.get('date_of_entry'),
                'date_of_graduation': s.get('date_of_graduation'),
                'graduation_expected': s.get('graduation_expected', False),
                'school_address': s.get('school_address'),
                'school_website': s.get('school_website'),
                'school_phone': s.get('school_phone'),
                'school_email': s.get('school_email'),
                'tariff': tariff_val or None,
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
                'balance': Decimal(str(s.get('balance', 0) or 0)),
                'discount': Decimal(str(s.get('discount', 0) or 0)),
                'pick_needed': s.get('pick_needed') or [],
                'has_mc': s.get('has_mc', False),
                'bc_hand_count': s.get('bc_hand_count', 0),
                'mc_hand_count': s.get('mc_hand_count', 0),
                'apos_hand_count': s.get('apos_hand_count', 0),
                'pic_hand_count': s.get('pic_hand_count', 0),
                'invoice': s.get('invoice'),
                'invoice_university': s.get('invoice_university'),
                'coa': s.get('coa'),
                'embassy': s.get('embassy'),
                'embassy_documents': s.get('embassy_documents') or [],
                'status_hidden': s.get('status_hidden', False),
                'kdb_put_date': s.get('kdb_put_date'),
                'kdb_take_date': s.get('kdb_take_date'),
                'embassy_father_docs': s.get('embassy_father_docs') or [],
                'embassy_mother_docs': s.get('embassy_mother_docs') or [],
                'embassy_sponsor_notes': s.get('embassy_sponsor_notes'),
                'office': s.get('office'),
                'student_group': group_val or None,
                'lead_by': lead_val or None,
                'coordinator': coord_val or None,
                'notes': s.get('notes'),
                'is_deleted': s.get('is_deleted', False),
                'row_color': s.get('row_color'),
                'status_row_color': s.get('status_row_color'),
                'task_tags': s.get('task_tags') or [],
                'google_drive_url': s.get('google_drive_url'),
                'google_drive_folder_id': s.get('google_drive_folder_id'),
                'tenant': tenant_ub,
                'created_by': head_manager,
            }

            student_obj, _ = Student.objects.update_or_create(
                id=s_id,
                defaults=student_defaults
            )

            # Assign folders
            student_folders_raw = s.get('folders') or s.get('folder_ids') or []
            if isinstance(student_folders_raw, list) and student_folders_raw:
                assigned_folders = []
                for f_id in student_folders_raw:
                    if f_id in folder_map:
                        assigned_folders.append(folder_map[f_id])
                if assigned_folders:
                    student_obj.folders.set(assigned_folders)

            # If student has KDB dates, ensure added to KDB folder
            if student_obj.kdb_put_date or student_obj.kdb_take_date:
                student_obj.folders.add(folder_kdb)

            imported_students_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported_students_count} students!"))

        # 5. Seed Auto-discovering Options
        for t_name in tariffs_set:
            TariffOption.objects.get_or_create(tenant=tenant_ub, name=t_name)
        for l_name in levels_set:
            EducationLevelOption.objects.get_or_create(tenant=tenant_ub, name=l_name)
        for g_name in groups_set:
            StudentGroupOption.objects.get_or_create(tenant=tenant_ub, name=g_name)
        for lead_name in leads_set:
            LeadSourceOption.objects.get_or_create(tenant=tenant_ub, name=lead_name)
        for c_name in coordinators_set:
            CoordinatorOption.objects.get_or_create(tenant=tenant_ub, name=c_name)

        # 6. Fetch and Import Payments
        self.stdout.write(self.style.NOTICE("Fetching Payments from Supabase..."))
        sb_payments = fetch_supabase_table('payments')
        self.stdout.write(self.style.NOTICE(f"Fetched {len(sb_payments)} payments. Importing..."))

        payment_methods_set = set()
        receivers_set = set()
        imported_payments_count = 0

        for p in sb_payments:
            p_id = p.get('id')
            if not p_id:
                continue

            student_id = (p.get('student_id') or '').strip().upper()
            student_ref = None
            if student_id:
                student_ref = Student.objects.filter(id=student_id, tenant=tenant_ub).first()

            method = str(p.get('method') or 'Naqd').strip()
            received_by = str(p.get('received_by') or 'Admin').strip()
            notes = str(p.get('notes') or '').strip()

            payment_methods_set.add(method)
            receivers_set.add(received_by)

            Payment.objects.update_or_create(
                id=p_id,
                defaults={
                    'tenant': tenant_ub,
                    'student': student_ref,
                    'student_name': p.get('student_name') or (student_ref.full_name if student_ref else None),
                    'amount': Decimal(str(p.get('amount', 0) or 0)),
                    'method': method,
                    'received_by': received_by,
                    'notes': notes or None,
                    'is_discount': p.get('is_discount', False) or 'DISCOUNT' in notes.upper(),
                    'is_withdrawal': p.get('is_withdrawal', False) or 'WITHDRAW' in notes.upper(),
                    'created_by': head_manager,
                    'created_at': p.get('created_at')
                }
            )
            imported_payments_count += 1

        for m in payment_methods_set:
            PaymentMethodTemplate.objects.get_or_create(tenant=tenant_ub, name=m)
        for r in receivers_set:
            PaymentReceiverTemplate.objects.get_or_create(tenant=tenant_ub, name=r)

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported_payments_count} payments!"))
        self.stdout.write(self.style.SUCCESS("ALL SUPABASE DATA SUCCESSFULLY IMPORTED INTO SALOM CRM!"))
