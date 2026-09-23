"""
Management command: insert_executor_stamp
===========================================
Embeds the company stamp+signature image (base64 data in
_executor_stamp_data.py) into the "BAJARUVCHI" (executor/company) block of
every contract template belonging to a tenant, as a new canvas element
layered on top of the existing text.

The stamp's ring is exactly 4cm in diameter on the page - this was measured
directly from the source PNG (ring spans y:15-387 out of a 402px-tall trim,
i.e. a 372px ring against a 40mm target -> 0.107527 mm/px), so the whole
image is placed at ~62.8mm x 43.2mm. Position is anchored relative to each
template's own BAJARUVCHI box (found by content, not a fixed page number,
since box coordinates differ slightly per tariff), at roughly 48% across
and 42% down that box - matching where a real stamp overlaps the address
lines in this company's contracts.

Usage:
    python manage.py insert_executor_stamp --tenant unibridge --dry-run
    python manage.py insert_executor_stamp --tenant unibridge

Flags:
    --tenant   Tenant slug to scope the change to (e.g. unibridge)
    --dry-run  Preview affected tariffs without saving anything
"""
import json

from django.core.management.base import BaseCommand, CommandError

from ._executor_stamp_data import STAMP_PNG_BASE64

STAMP_WIDTH_MM = 62.8
STAMP_HEIGHT_MM = 43.2
# Ring center within the trimmed PNG, in mm at the display scale above.
RING_CENTER_X_MM = 21.24
RING_CENTER_Y_MM = 21.61

# Fraction across/down the BAJARUVCHI box where the ring's center should land.
TARGET_FX = 0.48
TARGET_FY = 0.42

ELEMENT_ID_PREFIX = 'executor_stamp_'
HEADER_MARKER = '>BAJARUVCHI<'


class Command(BaseCommand):
    help = "Inserts the company stamp+signature image into the BAJARUVCHI block of every contract template for a tenant."

    def add_arguments(self, parser):
        parser.add_argument('--tenant', required=True, help='Tenant slug to scope the change to (e.g. unibridge)')
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving')

    def handle(self, *args, **options):
        from apps.students.models import TariffOption
        from apps.tenants.models import Tenant

        slug = options['tenant'].strip()
        dry_run = options['dry_run']

        try:
            tenant = Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            raise CommandError(f"Tenant with slug '{slug}' not found.")

        stamp_data_uri = 'data:image/png;base64,' + STAMP_PNG_BASE64

        stamp_html = (
            f'<img src="{stamp_data_uri}" '
            f'style="width:100%;height:100%;display:block;object-fit:contain;pointer-events:none;" '
            f'alt="Muhr va imzo" />'
        )

        options_qs = TariffOption.objects.filter(tenant=tenant).exclude(contract_text__isnull=True).exclude(contract_text='')

        self.stdout.write(f"\n{'[DRY RUN] ' if dry_run else ''}Insert executor stamp for tenant: {tenant.name} ({slug})")

        touched = 0
        skipped_existing = 0
        skipped_not_found = 0

        for opt in options_qs:
            try:
                data = json.loads(opt.contract_text)
            except (ValueError, TypeError):
                self.stdout.write(self.style.WARNING(f"  - {opt.name}: contract_text is not valid JSON, skipped"))
                continue

            pages = data.get('pages', [])

            # Idempotency: don't double-insert on a rerun.
            already = any(
                el.get('id', '').startswith(ELEMENT_ID_PREFIX)
                for page in pages for el in page.get('elements', [])
            )
            if already:
                self.stdout.write(f"  - {opt.name}: stamp already present, skipped")
                skipped_existing += 1
                continue

            target = None
            for page_index, page in enumerate(pages):
                for el in page.get('elements', []):
                    if HEADER_MARKER in (el.get('content') or ''):
                        target = (page_index, el)
                        break
                if target:
                    break

            if not target:
                self.stdout.write(self.style.WARNING(f"  - {opt.name}: BAJARUVCHI block not found, skipped"))
                skipped_not_found += 1
                continue

            page_index, box = target
            elements = pages[page_index]['elements']
            max_z = max((e.get('zIndex', 0) for e in elements), default=0)

            center_x = box['x'] + box['width'] * TARGET_FX
            center_y = box['y'] + box['height'] * TARGET_FY

            stamp_element = {
                'id': f'{ELEMENT_ID_PREFIX}{opt.id}',
                'type': 'text',
                'x': round(center_x - RING_CENTER_X_MM, 2),
                'y': round(center_y - RING_CENTER_Y_MM, 2),
                'width': STAMP_WIDTH_MM,
                'height': STAMP_HEIGHT_MM,
                'zIndex': max_z + 1,
                'content': stamp_html,
                'style': {
                    'fontFamily': 'Times New Roman',
                    'fontSize': 12,
                    'textAlign': 'left',
                },
            }

            self.stdout.write(
                f"  - {opt.name}: page {page_index}, box=({box['x']},{box['y']},{box['width']},{box['height']}) "
                f"-> stamp=({stamp_element['x']},{stamp_element['y']},{STAMP_WIDTH_MM},{STAMP_HEIGHT_MM}) z={stamp_element['zIndex']}"
            )

            if not dry_run:
                elements.append(stamp_element)
                opt.contract_text = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
                opt.save(update_fields=['contract_text'])

            touched += 1

        self.stdout.write(
            f"\n{'Would update' if dry_run else 'Updated'}: {touched}  |  "
            f"already had stamp: {skipped_existing}  |  block not found: {skipped_not_found}"
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No changes were saved."))
        else:
            self.stdout.write(self.style.SUCCESS("Done."))
