# SalomCRM — Deploy Guide

## Deploy qilish (production serverga)

Kod GitHub'ga push qilingandan keyin, serverga chiqarish uchun loyiha ildizidagi `deploy.py` skripti ishlatiladi.

```powershell
$env:DEPLOY_PASSWORD="SalomKorea2026!"; python deploy.py
```

Bu skript avtomatik ravishda: serverda `git fetch && git reset --hard origin/main` qiladi, backend
dependencies/migratsiyalarni yangilaydi, frontend'ni build qiladi, va `pm2 restart salomcrm-backend`
orqali qayta ishga tushiradi. To'liq bosqichlar pastda.

**Foydali buyruqlar:**
```powershell
# Faqat server holatini tekshirish (deploy qilmasdan)
$env:DEPLOY_PASSWORD="SalomKorea2026!"; python deploy.py --status

# Backend loglarini ko'rish
$env:DEPLOY_PASSWORD="SalomKorea2026!"; python deploy.py --logs
```

⚠️ Bu production serverga ta'sir qiladigan amal — kod push qilingandan keyin, va odatda foydalanuvchi
aniq so'raganda yoki tasdiqlagandan keyin ishga tushirilishi kerak.

---

## To'liq jarayon (commit → push → deploy)

### Texnologiyalar

| Qism | Texnologiyalar | Vazifasi |
| :--- | :--- | :--- |
| Versiya boshqaruvi | Git, GitHub (`khan0200/SalomCrm`) | Kod o'zgarishlarini saqlash va serverga yetkazish |
| Deploy vositasi | Python (`deploy.py`), `paramiko` | SSH orqali serverga ulanish va buyruqlarni bajarish |
| Server muhiti | Ubuntu / aaPanel (`178.238.231.210`) | Production serveri |
| Backend & WSGI | Python 3, Django, Gunicorn | API va biznes mantiq |
| Process Manager | PM2 (`salomcrm-backend`) | Gunicorn jarayonini boshqarish, avtomatik restart |
| Frontend | Vue 3, TypeScript, Vite, TailwindCSS | SPA'ni static fayllarga build qilish (`dist/`) |
| Web Server | Nginx | Reverse Proxy (80/443 → frontend `dist/` va backend `:8000`) |
| Ma'lumotlar bazasi | PostgreSQL | Migratsiyalar va sequence sinxronizatsiyasi |

### 1-bosqich: Git commit va push

1. `git status` / `git diff` orqali o'zgargan fayllarni tekshirish.
2. Lokal tekshiruv: frontend uchun `npm run build` (yoki kamida `vue-tsc --noEmit`), backend uchun
   `python -m py_compile ...` yoki syntax check.
3. Conventional Commits formatida commit (masalan `feat(students): ...`, `fix(contracts): ...`).
4. `git push origin main`.

### 2-bosqich: `deploy.py` serverda nima qiladi

1. **SSH ulanish** — `paramiko.SSHClient` orqali `root@178.238.231.210`, loyiha yo'li
   `/var/www/SalomCrm`.
2. **Kodni yangilash** — `git fetch origin && git reset --hard origin/main`. Agar tarmoq xatosi
   bo'lsa, lokal `git bundle`ni SFTP orqali yuklab fallback qiladi.
3. **Backend** — `venv/bin/pip install -r requirements.txt gunicorn`, `manage.py migrate --noinput`,
   `manage.py fix_sequences`, `manage.py collectstatic --noinput`.
4. **Frontend** — aaPanel Node.js muhiti orqali `npm ci --no-audit && npm run build`. Agar serverda
   RAM yetmay Vite build xato bersa, lokal build qilib `dist.tar.gz` SFTP orqali yuklanadi.
5. **Systemd vs PM2 mojarosi** — eski `systemd` servisi (`salomcrm-backend.service`) to'xtatiladi/
   disable qilinadi, `:8000` porti faqat PM2 nazoratida ekanligi tekshiriladi (`ss -tlnpH`).
6. **PM2 restart** — `pm2 restart salomcrm-backend --update-env && pm2 save`, so'ng
   `nginx -s reload`.
7. **Health check** — `curl .../api/docs/` va `curl http://127.0.0.1/` 200 qaytarishi, `pm2 list`da
   status `online` ekanligi tekshiriladi.
