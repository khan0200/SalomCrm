module.exports = {
  apps: [
    {
      name: 'salomcrm-backend',
      script: '/var/www/SalomCrm/venv/bin/gunicorn',
      args: 'config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --threads 2 --timeout 120',
      cwd: '/var/www/SalomCrm/backend',
      interpreter: 'none',
      env: {
        DJANGO_SETTINGS_MODULE: 'config.settings',
        PYTHONPATH: '/var/www/SalomCrm/backend',
      },
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
    },
  ],
}
