# پرتال خبری — Portale Khabar

وب‌سایت خبری فارسی، راست‌چین و دارک‌مود، ساخته‌شده با Django.
A Persian (RTL) news portal built with Django, featuring a dark glassmorphism
UI, an automatic RSS aggregator with smart categorisation, comments and likes,
and a modern admin panel.

---

## ✨ امکانات (Features)

- **راست‌چین و فارسی** با فونت Vazirmatn و فونت تیتر.
- **ظاهر مدرن دارک مود** با کارت‌های شیشه‌ای (glassmorphism) و حالت برآمده.
- **اخبار دستی + اخبار RSS**: مقالات توسط مدیر اضافه می‌شوند و بقیه به‌صورت
  خودکار از فیدهای خبرگزاری‌ها دریافت می‌شوند. نام منبع به‌صورت کوچک نمایش
  داده می‌شود و برچسب «RSS» روی کارت می‌نشیند.
- **دریافت خودکار RSS در پس‌زمینه** با `django-apscheduler` (بدون Celery).
- **دسته‌بندی هوشمند هیبرید**: تطبیق کلمات کلیدی فارسی روی عنوان/خلاصه و در
  صورت نبود تطابق، استفاده از دسته‌ی فید.
- **فیلتر اخبار تکراری** با نرمال‌سازی عنوان و هش.
- **جستجوی سریع** و **فیلتر بر اساس دسته و تاریخ انتشار**.
- **نظرات** (با تأیید مدیر) و **لایک/دیسلایک** ناشناس (بدون ثبت‌نام).
- **پنل ادمین فارسی/RTL/دارک** با `django-jazzmin`.
- **دیتابیس SQLite**.

---

## 📁 ساختار پروژه (Project structure)

```
portale-khabar/
├── manage.py
├── requirements.txt
├── apps/
│   ├── config/            # پروژه‌ی جنگو (settings/urls/wsgi/asgi)
│   ├── news/              # اپ اصلی: Category, Article, RSSFeed + سرویس‌ها
│   │   ├── services/      # rss_fetcher, categorizer, dedup
│   │   ├── management/    # دستور fetch_rss
│   │   ├── templatetags/
│   │   └── scheduler.py   # استارت apscheduler
│   ├── interactions/      # نظرات و لایک/دیسلایک
│   └── pages/             # درباره ما / ارتباط با ما
├── templates/
│   ├── base.html
│   ├── components/        # navbar, sidebar, article_card, ...
│   ├── partials/          # news_list, pagination, ...
│   └── pages/             # home, news_list, news_detail, rss_news, about, contact
└── static/
    ├── src/input.css      # سورس Tailwind
    ├── css/tailwind.css   # خروجی کامپایل‌شده
    ├── fonts/
    └── js/main.js         # AJAX برای لایک/نظر
```

---

## 🚀 نصب و اجرا (Setup & run)

### ۱) نصب وابستگی‌های پایتون
```bash
pip install -r requirements.txt
```

### ۲) مهاجرت‌های دیتابیس
```bash
python manage.py migrate
```

### ۳) ساخت ادمین (superuser)
```bash
python manage.py createsuperuser
```

### ۴) کامپایل Tailwind (در صورت تغییر `static/src/input.css`)
```bash
# روش پیشنهادی با standalone CLI یا npm:
npx tailwindcss -i ./static/src/input.css -o ./static/css/tailwind.css --minify --watch
```
> پروژه همراه با یک خروجی پیش‌کامپایل‌شده عرضه می‌شود تا بدون Node هم اجرا شود؛
> فقط در صورت تغییر استایل، این دستور را اجرا کنید.

### ۵) اجرای سرور توسعه
```bash
python manage.py runserver
```

سپس:
- سایت: http://127.0.0.1:8000/
- پنل ادمین: http://127.0.0.1:8000/admin/

---

## 🔁 دریافت خودکار RSS

اسکدولر با شروع سرور توسعه (با فیلتر `RUN_MAIN`) اجرا می‌شود. برای محیط
production (gunicorn/uwsgi) متغیر محیطی زیر را ست کنید:

```bash
export ENABLE_SCHEDULER=1
```

دریافت دستی برای تست:
```bash
python manage.py fetch_rss            # همه‌ی فیدهای فعال
python manage.py fetch_rss --feed-id 1 # فقط یک فید خاص
```

---

## 🧱 مدل‌های کلیدی

- **Category**: دسته موضوعی + کلمات کلیدی برای دسته‌بندی هوشمند.
- **Article**: خبر دستی یا RSS، با `dedup_hash` برای حذف تکرار، تصویر محلی/URL،
  برچسب منبع و حالت ویژه (featured).
- **RSSFeed**: منبع قابل مدیریت از ادمین با بازه‌ی دریافت مجزا.
- **Comment** / **Like**: تعاملات کاربران (بدون ثبت‌نام).

---

## 📝 نکات توسعه

- تمام فایل‌های پایتون با کامنت انگلیسی خوانا نوشته شده‌اند.
- مقادیر قابل تنظیم در پایین فایل `apps/config/settings.py` جمع شده‌اند.
