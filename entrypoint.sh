#!/bin/bash
set -e

# مایگریت دیتابیس
python manage.py migrate --noinput

# ساخت ادمین اگه وجود نداره
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser(
        username='$DJANGO_SUPERUSER_USERNAME',
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD',
    )
    print('✅ Superuser created.')
else:
    print('ℹ️  Superuser already exists, skipped.')
"
fi

# اجرای دستور پاس‌داده‌شده (مثل runserver یا gunicorn)
exec "$@"