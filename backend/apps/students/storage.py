"""
Private file storage for Contract.final_pdf (Stage 2 canary).

Deliberately a separate FileSystemStorage pointed at settings.PRIVATE_MEDIA_ROOT
rather than the default storage (settings.MEDIA_ROOT) - production's nginx
serves MEDIA_ROOT as a fully public, unauthenticated static alias (verified
in the live vhost config), so any file saved there is reachable by anyone
who learns its filename regardless of what permission checks Django's own
views apply. Files under PRIVATE_MEDIA_ROOT have no nginx location block at
all - the only way to read one is through ContractViewSet.download_pdf_canary,
which re-runs the same tenant-scoped get_object() every other action on
that ViewSet uses.
"""
from django.conf import settings
from django.core.files.storage import FileSystemStorage

class PrivateFileSystemStorage(FileSystemStorage):
    """
    FileSystemStorage.url() falls back to settings.MEDIA_URL whenever
    base_url is None/unset - passing base_url=None does NOT disable .url(),
    it just makes it silently build a /media/... link, which would be
    actively wrong here (nothing serves this location at that path) and
    dangerously misleading (it LOOKS like a working link). Overriding
    .url() to always raise is the only way to make "this file has no
    public URL" an actual guarantee instead of an intention.
    """
    def url(self, name):
        raise NotImplementedError(
            'private_pdf_storage has no public URL by design - use ContractViewSet.download_pdf_canary '
            '(authenticated, tenant-scoped) to read a final_pdf file, never storage.url().'
        )


def private_pdf_storage():
    """
    Factory, not an instance - Django's migration framework deconstructs a
    FileField's `storage=` kwarg by calling it, and for a bare instance that
    bakes the CURRENT MACHINE's resolved absolute path
    (settings.PRIVATE_MEDIA_ROOT, under BASE_DIR) directly into the
    generated migration file. That migration then "drifts" on every other
    machine whose BASE_DIR differs (exactly what happened: the local dev
    checkout and the production server disagree, so every deploy re-flagged
    a spurious AlterField). A callable instead gets stored as an import
    path and re-invoked wherever the migration runs, so the location is
    always resolved fresh against that machine's own settings.
    """
    return PrivateFileSystemStorage(
        location=str(settings.PRIVATE_MEDIA_ROOT / 'contracts_final_pdf'),
    )
