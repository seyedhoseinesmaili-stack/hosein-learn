# سامانهٔ آموزش آنلاین

پروژهٔ Django برای نمایش دوره‌ها، ثبت‌نام کاربران و پیگیری پیشرفت و زمان تماشای ویدیوها.

## اجرای محلی

در ریشهٔ پروژه اجرا کنید:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

آدرس محلی: `http://127.0.0.1:8000/`

## اجرای تست‌ها

```powershell
python manage.py test
```

## تنظیمات production

این متغیرها را در تنظیمات محیط میزبان تعریف کنید؛ کلید واقعی را در Git قرار ندهید:

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY` یک کلید تصادفی و محرمانه
- `DJANGO_ALLOWED_HOSTS` دامنه‌ها با جداکنندهٔ کاما، مانند `example.com,www.example.com`
- `DJANGO_CSRF_TRUSTED_ORIGINS` مبدأهای HTTPS با جداکنندهٔ کاما، مانند `https://example.com`
- `DJANGO_SECURE_SSL_REDIRECT=True` برای سایتی که HTTPS دارد
- `DJANGO_SECURE_HSTS_SECONDS=31536000` فقط پس از اطمینان از HTTPS در تمام سایت
- `DJANGO_TRUST_X_FORWARDED_PROTO=True` فقط اگر reverse proxy مطمئن این سرآیند را تنظیم و سرآیندهای ورودی کاربر را پاک‌سازی می‌کند

برای اجرای production روی Linux از `gunicorn learn.wsgi:application` استفاده کنید. در Render، از پوشهٔ پروژه، Build Command را به شکل زیر تنظیم کنید تا جدول‌های دیتابیس قبل از شروع سرویس ساخته شوند:

```sh
pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput
```

در Render، **Start Command** را هم دقیقاً به این مقدار تغییر دهید. اجرای migration در زمان شروع سرویس لازم است چون فایل SQLite ساخته‌شده در مرحلهٔ Build الزاماً در محیط اجرای سرویس وجود ندارد:

```sh
python manage.py migrate --noinput && gunicorn learn.wsgi:application
```

تنظیمات `DJANGO_SECRET_KEY`، `DJANGO_ALLOWED_HOSTS` و `DJANGO_CSRF_TRUSTED_ORIGINS` را در Environment سرویس Render وارد کنید. این پروژه در حال حاضر از SQLite استفاده می‌کند؛ برای حفظ اطلاعات کاربران در استقرارهای مجدد Render، دیتابیس پایدار مانند PostgreSQL را پیکربندی کنید.

دیتابیس محلی و فایل‌های بارگذاری‌شده در `media/` عمداً در Git قرار نمی‌گیرند. برای production باید دیتابیس پایدار و فضای ذخیره‌سازی پایدار برای ویدیوها جداگانه تنظیم شود.
