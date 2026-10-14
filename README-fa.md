# 🚀 FreeNET

> سرور مینیمال VLESS با انتقال‌های WebSocket و XHTTP

[🇬🇧 English](README.md)

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-deploy-0B0D0E?logo=railway&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## معرفی

FreeNET یک سرور کوچک VLESS است که برای اجرا پشت reverse proxy مبتنی بر HTTP/HTTPS، مانند Railway، در نظر گرفته شده است. انتقال‌های پشتیبانی‌شده:

- VLESS روی WebSocket
- VLESS روی XHTTP با حالت `packet-up`
- VLESS روی XHTTP با حالت `stream-up`

پنل وب، سرویس Subscription، دیتابیس کاربران و Trojan وجود ندارد. تنظیمات کلاینت را دستی و با دامنه سرویس و UUID موجود در `/data/identity.json` بسازید.

اتصال به مقصدهای پروکسی از TCP استفاده می‌کند. خاتمه TLS و دسترسی عمومی HTTPS باید توسط پلتفرم میزبانی یا reverse proxy انجام شود.

## استقرار روی Railway

1. این repository را به‌عنوان سرویس Railway مستقر کنید.
2. یک Volume پایدار با مسیر mount برابر `/data` اضافه کنید.
3. دامنه عمومی اختصاص دهید و HTTPS را فعال کنید.

Railway پورت اجرا را از طریق `PORT` می‌دهد و برنامه روی `0.0.0.0` گوش می‌دهد. مسیر Health check برابر `/health` است.

فایل‌های داده:

- `/data/identity.json` — UUID سرویس VLESS
- `/data/stats.json` — شمارنده کلی Upload و Download

برای ثابت ماندن UUID و آمار پس از راه‌اندازی مجدد، Volume را حفظ کنید. در مهاجرت از نسخه‌های قدیمی، UUID قبلی خوانده می‌شود و فیلدهای قدیمی Trojan و Subscription از فایل identity حذف می‌شوند.

## مسیرهای اتصال کلاینت

### VLESS WebSocket

- مسیر WebSocket: `/vless/<uuid>`
- انتقال: WebSocket
- TLS: روی reverse proxy عمومی فعال باشد؛ در صورت نیاز دامنه عمومی را برای SNI/Host قرار دهید.
- Encryption: `none`

### VLESS XHTTP

- مسیر HTTP: `/xhttp/<uuid>` (زیرمسیرهای بیشتر نیز پذیرفته می‌شوند)
- متدها: `GET` و `POST`
- حالت‌ها: `packet-up` و `stream-up`
- Encryption: `none`

انتقال و حالت XHTTP را در تنظیمات کلاینت انتخاب کنید. سرور لینک یا کانفیگ خودکار منتشر نمی‌کند.

## تنظیمات و ذخیره‌سازی

| متغیر | پیش‌فرض | کاربرد |
| --- | --- | --- |
| `PORT` | `8000` | پورت HTTP؛ معمولاً Railway آن را تنظیم می‌کند |
| `FREENET_DATA_DIR` | `/data` | مسیر ذخیره identity و آمار |

برای اجرای محلی:

```bash
mkdir -p data
FREENET_DATA_DIR=./data PORT=8000 python main.py
```

UUID در اولین اجرا ساخته و در `data/identity.json` ذخیره می‌شود؛ همان UUID را در کلاینت وارد کنید. برای اتصال واقعی کلاینت از دامنه عمومی دارای TLS استفاده کنید.

آمار Upload و Download به‌صورت کلی برای کل سرویس است و با حفظ Volume باقی می‌ماند. Uptime مربوط به اجرای فعلی برنامه است و بعد از restart از نو محاسبه می‌شود.

## Docker

```bash
docker build -t freenet .
docker volume create freenet-data
docker run --rm -p 8000:8000 -e PORT=8000 -v freenet-data:/data freenet
```

## ساختار پروژه

```text
FreeNET/
├── main.py          # برنامه FastAPI، ذخیره UUID و مسیرهای HTTP
├── core.py          # TCP relay و آمار کلی
├── protocols.py     # انتقال‌های VLESS WebSocket و XHTTP
├── Dockerfile
├── railway.json
├── requirements.txt
├── README.md
└── README-fa.md
```
