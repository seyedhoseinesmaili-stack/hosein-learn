# آکادمی سید

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

برای اجرای production روی Linux از اسکریپت `start.sh` استفاده کنید. در Render، **Root Directory** باید پوشه‌ای باشد که `manage.py` و `requirements.txt` در آن قرار دارند (اگر ریشهٔ مخزن همین پوشه است، این گزینه را خالی بگذارید) و Build Command را این‌طور تنظیم کنید:

```sh
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command** را روی این مقدار بگذارید تا migration در محیط اجرای واقعی، پیش از Gunicorn اجرا شود:

```sh
bash start.sh
```

تنظیمات `DJANGO_SECRET_KEY`، `DJANGO_ALLOWED_HOSTS` و `DJANGO_CSRF_TRUSTED_ORIGINS` را در Environment سرویس Render وارد کنید. این پروژه در حال حاضر از SQLite استفاده می‌کند؛ برای حفظ اطلاعات کاربران در استقرارهای مجدد Render، دیتابیس پایدار مانند PostgreSQL را پیکربندی کنید.

دیتابیس محلی و فایل‌های بارگذاری‌شده در `media/` عمداً در Git قرار نمی‌گیرند. برای production باید دیتابیس پایدار و فضای ذخیره‌سازی پایدار برای ویدیوها جداگانه تنظیم شود.
