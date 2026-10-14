"""
Stage 2 canary: server-side canonical PDF generation for a finalized online
contract, via headless Chromium (Playwright) driven by a Node.js helper
script (backend/pdf_renderer/) that reuses the frontend's own
contractCanvasConverter.ts/contractVariables.ts - see that directory's
render.ts for why those files are vendored instead of reimplemented in
Python.

This module owns:
  - Mapping a Contract row to the Node script's expected stdin JSON.
  - Idempotent generation: select_for_update() + final_pdf_status guards
    against two concurrent requests racing into two different renders for
    the same contract.
  - Subprocess lifecycle: timeout, temp-file cleanup, error capture.
  - Persisting the result onto Contract.final_pdf (private FileSystemStorage
    - never served via MEDIA_URL; see contract_pdf_views.py for the
    permission-checked download path).

Deliberately NOT handled here (out of scope for the Stage 2 canary):
  - Legacy plain-HTML (non-canvas) tariffs - render.ts raises for these.
  - Re-generation after a contract is amended - see Contract.final_pdf's
    own "immutable once set" docstring; that's the existing re-sign/
    versioning flow's job, not this service's.
"""
import json
import logging
import os
import subprocess
import tempfile
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from .models import Contract, ContractAuditEvent

logger = logging.getLogger(__name__)

PDF_RENDERER_DIR = Path(settings.BASE_DIR) / 'pdf_renderer'
RENDER_SCRIPT = PDF_RENDERER_DIR / 'dist' / 'render.js'

# aaPanel's Node install isn't on the default process PATH - same discovery
# problem deploy.py documents for pm2/npm. Overridable via env for local dev
# (a plain `node` on PATH) vs. production (the explicit aaPanel path).
NODE_BIN = os.environ.get('PDF_RENDERER_NODE_BIN', 'node')

# Single render timeout. Deliberately conservative for the Stage 2 canary -
# the infrastructure audit's concurrency ceiling (report §06) hasn't been
# measured against this specific template yet, so this errs toward failing
# fast and visibly rather than letting a stuck Chromium page hang a gunicorn
# worker indefinitely.
RENDER_TIMEOUT_SECONDS = 20


class PdfGenerationError(Exception):
    """Raised for any failure that should leave final_pdf_status='failed'."""


def _resolve_tenant_requisites_fallback():
    """
    contractVariables.ts's resolveTenantRequisites() reads localStorage
    (active_tenant_id / user_profile) - meaningless on a server with no
    browser session. The Node side still calls it (unchanged, to stay
    byte-identical with the frontend), but localStorage is simply absent
    under Node, so it silently falls through to UNIBRIDGE_REQUISITES's
    hardcoded default every time. This matches the "default tenant" a
    staff member would see on a machine with no prior localStorage state -
    acceptable for the canary since all current contracts use the
    canvas-contract format's own embedded requisites text, not this
    fallback. Flagged here (not fixed) as a known Stage 2 limitation - see
    the Stage 2 report's "Remaining risks" section.
    """


def _build_student_payload(contract: Contract) -> dict:
    """
    Maps authoritative Contract fields to the shape buildVariableValues()
    (vendored contractVariables.ts) expects as its `student` argument -
    mirrors the keys ContractSignLinkPage.vue's buildVariableValues() call
    reads from `contractInfo`/`studentSignature`, but sourced here from the
    DB row instead of session-only frontend state. This is the fix for the
    signature bug noted in the Stage 1 code trace: signature_data comes
    from the persisted Contract field, not a frontend ref that's empty on
    a returning visit.
    """
    return {
        'full_name': contract.full_name,
        'passport_number': contract.passport_number,
        'date_of_birth': contract.date_of_birth,
        'phone1': contract.phone1,
        'phone2': contract.phone2,
        'tariff_price': str(contract.tariff_price or 0),
        'discount': str(contract.discount or 0),
        'education_level': contract.education_level,
        'office': contract.office,
        'signature_data': contract.signature_data,
        'verification_code': contract.verification_code,
        'verified_at': contract.verified_at.isoformat() if contract.verified_at else None,
        'signed_at': contract.signed_at.isoformat() if contract.signed_at else None,
        'created_at': contract.created_at.isoformat() if contract.created_at else None,
        'guardian_full_name': contract.guardian_full_name,
        'guardian_passport_number': contract.guardian_passport_number,
        'guardian_relation': contract.guardian_relation,
        'guardian_phone': contract.guardian_phone,
        'guardian_address': contract.guardian_address,
        'guardian_signature_data': contract.guardian_signature_data,
    }


def _build_contract_meta_payload(contract: Contract, sign_url: str) -> dict:
    return {
        'contractNumber': contract.contract_number,
        'templateName': contract.tariff_name,
        'price': str(contract.tariff_price or 0),
        'discount': str(contract.discount or 0),
        'verificationCode': contract.verification_code,
        'signUrl': sign_url,
        'office': contract.office,
        'educationLevel': contract.education_level,
    }


def _run_node_renderer(payload: dict, output_path: Path) -> None:
    if not RENDER_SCRIPT.exists():
        raise PdfGenerationError(
            f"Render script not built: {RENDER_SCRIPT} - run `npm run build` in {PDF_RENDERER_DIR} first."
        )

    stdin_data = json.dumps({**payload, 'outputPath': str(output_path), 'timeoutMs': RENDER_TIMEOUT_SECONDS * 1000})

    try:
        proc = subprocess.run(
            [NODE_BIN, str(RENDER_SCRIPT)],
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=RENDER_TIMEOUT_SECONDS + 5,  # grace period beyond the in-script Chromium timeout
            cwd=str(PDF_RENDERER_DIR),
        )
    except subprocess.TimeoutExpired as exc:
        # Node's own `page.pdf({timeout})` should fire first and exit cleanly;
        # this outer timeout is the backstop for a genuinely hung Chromium
        # process (crash during shutdown, zombie render) - see the
        # infrastructure audit's concern about a render that "hangs instead
        # of completing" with zero swap configured.
        raise PdfGenerationError(f"Render process exceeded {RENDER_TIMEOUT_SECONDS + 5}s hard timeout") from exc

    # Never log stdin_data (contains signature_data/passport/etc.) - only
    # the script's own stdout/stderr, which by contract never echoes input.
    last_stdout_line = (proc.stdout or '').strip().splitlines()[-1] if proc.stdout else ''
    try:
        result = json.loads(last_stdout_line) if last_stdout_line else {}
    except json.JSONDecodeError:
        result = {}

    if proc.returncode != 0 or not result.get('ok'):
        error_detail = result.get('error') or (proc.stderr or '')[-2000:]
        logger.error('contract_pdf_service: render failed (exit=%s): %s', proc.returncode, error_detail)
        raise PdfGenerationError(f"Chromium render failed: {error_detail}")

    if not output_path.exists() or output_path.stat().st_size == 0:
        raise PdfGenerationError("Render reported success but produced no output file")


def generate_final_pdf(contract_id, sign_url: str = '', force: bool = False) -> Contract:
    """
    Idempotent entry point. Safe to call from multiple concurrent requests
    for the same contract_id - select_for_update() serializes them, and the
    second caller through the lock sees final_pdf_status already 'ready'
    (or 'pending', held by the first) and returns/raises accordingly
    instead of rendering twice.

    Raises PdfGenerationError on any failure; never marks a contract
    'ready' on partial/failed output, and never touches signing-status
    fields (status/signature_data/etc.) - this is purely additive to the
    existing signed record.
    """
    with transaction.atomic():
        contract = Contract.objects.select_for_update().get(id=contract_id)

        if contract.final_pdf_status == 'ready' and contract.final_pdf and not force:
            return contract  # Already generated - same bytes returned on every call, per spec.

        if contract.final_pdf_status == 'pending':
            raise PdfGenerationError(
                "A render for this contract is already in progress (concurrent request) - retry shortly."
            )

        if not contract.signature_data:
            raise PdfGenerationError(
                "Cannot generate final PDF: contract has no persisted signature (not yet signed)."
            )

        contract.final_pdf_status = 'pending'
        contract.save(update_fields=['final_pdf_status'])

    # Deliberately outside the transaction/lock: the actual render (subprocess,
    # up to RENDER_TIMEOUT_SECONDS) must not hold a DB row lock for its
    # duration - 'pending' status above is the concurrency guard instead.
    tmp_dir = Path(tempfile.mkdtemp(prefix='contract_pdf_'))
    output_path = tmp_dir / f'{uuid.uuid4().hex}.pdf'
    try:
        payload = {
            'canvasSource': contract.canvas_source or '',
            'content': contract.content or '',
            'guardianContent': '',  # Stage 2 canary scope: guardian appendix rendering deferred, see report.
            'student': _build_student_payload(contract),
            'contractMeta': _build_contract_meta_payload(contract, sign_url),
        }
        _run_node_renderer(payload, output_path)

        with open(output_path, 'rb') as f:
            pdf_bytes = f.read()

        with transaction.atomic():
            contract = Contract.objects.select_for_update().get(id=contract_id)
            filename = f'{contract.contract_number or contract.id}.pdf'
            contract.final_pdf.save(filename, ContentFile(pdf_bytes), save=False)
            contract.final_pdf_status = 'ready'
            contract.final_pdf_generated_at = timezone.now()
            contract.save(update_fields=['final_pdf', 'final_pdf_status', 'final_pdf_generated_at'])

            ContractAuditEvent.objects.create(
                contract=contract,
                tenant=contract.tenant,
                action='CONTRACT_PDF_GENERATED',
                actor_type='SYSTEM',
                description=f"Server-side canonical PDF generated ({len(pdf_bytes)} bytes).",
                metadata={'bytes': len(pdf_bytes), 'canary': True},
            )

        return contract

    except PdfGenerationError:
        _mark_failed(contract_id)
        raise
    except Exception as exc:
        logger.exception('contract_pdf_service: unexpected failure for contract=%s', contract_id)
        _mark_failed(contract_id)
        raise PdfGenerationError(f"Unexpected error during PDF generation: {exc}") from exc
    finally:
        # Never leave rendered PDF bytes sitting in /tmp beyond this request -
        # the only persisted copy must be the one on Contract.final_pdf,
        # written through Django's storage layer above.
        try:
            if output_path.exists():
                output_path.unlink()
            tmp_dir.rmdir()
        except OSError:
            pass


def _mark_failed(contract_id):
    try:
        with transaction.atomic():
            contract = Contract.objects.select_for_update().get(id=contract_id)
            # A failed render must never get silently stuck in 'pending' -
            # that state is this function's own concurrency guard (see
            # generate_final_pdf's early-return check), so leaving it set
            # after a failure would permanently block every future retry.
            contract.final_pdf_status = 'failed'
            contract.save(update_fields=['final_pdf_status'])
    except Exception:
        logger.exception('contract_pdf_service: failed to mark contract=%s as failed', contract_id)
