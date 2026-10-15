# 🚀 FreeNET

> پروژه‌ای آموزشی و آزمایشی برای آشنایی با مدیریت انتقال‌های VLESS در Python

[🇬🇧 English](README.md)

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Railway](https://img.shields.io/badge/Railway-deploy-0B0D0E?logo=railway&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## هدف و محدوده پروژه

FreeNET یک پروژه آموزشی برای مطالعه و آزمایش نحوه‌ی پردازش هدرهای VLESS و انتقال داده‌ی TCP روی WebSocket و تبادل‌های HTTP به سبک XHTTP در Python است. هدف آن یادگیری و آزمایش محلی است و یک محصول کامل یا آماده‌ی استفاده‌ی عملیاتی محسوب نمی‌شود.

برنامه‌ی نمونه این حالت‌ها را دارد:

- VLESS روی WebSocket
- VLESS روی XHTTP با حالت `packet-up`
- VLESS روی XHTTP با حالت `stream-up`

پیاده‌سازی فقط مقصدهای TCP را پشتیبانی می‌کند و UDP در آن پیاده‌سازی نشده است. هنگام استقرار، TLS می‌تواند در پلتفرم میزبانی خاتمه یابد. مدیریت کاربر، دیتابیس و Trojan در این repository وجود ندارد.

## استقرار روی Railway

1. از این repository یک Fork بسازید و Fork را به‌عنوان سرویس Railway مستقر کنید. نام Fork یا repository را به دلخواه انتخاب کنید.
2. با حساب GitHub خود وارد Railway شوید و دسترسی Railway به Fork را تأیید کنید. از حسابی استفاده کنید که با شرایط جاری حساب و سرویس Railway سازگار باشد؛ این پروژه نمی‌تواند پذیرش یا عدم محدودیت حساب را تضمین کند.
3. یک Railway Domain عمومی بسازید و منتظر موفق شدن بررسی سلامت برنامه در مسیر `/health` بمانید.

Volume پایدار یا مسیر `/data` نیاز نیست. Railway مقدار `PORT` را فراهم می‌کند؛ برنامه روی `0.0.0.0` گوش می‌دهد و HTTPS/TLS عمومی را Railway مدیریت می‌کند.

### ثابت نگه‌داشتن شناسه‌ها

متغیرهای محیطی اختیاری:

| متغیر | پیش‌فرض | کاربرد |
| --- | --- | --- |
| `SEC` | مقدار تصادفی در شروع هر process | کلیدی که در مسیر Subscription قرار می‌گیرد. برای ثابت ماندن لینک پس از redeploy، آن را در Railway Variables تنظیم کنید. |
| `VLESS_UUID` | UUID تصادفی در شروع هر process | UUID سرور و لینک‌های کلاینت. برای ثابت ماندن کانفیگ‌ها پس از redeploy، آن را در Railway Variables تنظیم کنید. |
| `PORT` | `8000` | پورت HTTP؛ معمولاً Railway آن را تنظیم می‌کند. |

هنگام شروع برنامه، لینک کامل Subscription در لاگ‌های Deploy چاپ می‌شود. اگر `SEC` تنظیم نشده باشد، لینک Subscription با هر restart یا redeploy تغییر می‌کند. اگر `VLESS_UUID` تنظیم نشده باشد، کلاینت‌ها نیز پس از restart به UUID جدید نیاز دارند. هیچ‌کدام از این مقادیر به‌صورت پایدار روی دیسک ذخیره نمی‌شوند.

`SEC` و `VLESS_UUID` را محرمانه نگه دارید. هرکسی لینک Subscription را داشته باشد می‌تواند کانفیگ‌های نمونه را دریافت کند و هرکسی UUID را بداند می‌تواند endpointهای آزمایشی را فراخوانی کند.

## Subscription و انتقال‌ها

برای آزمایش، لینکی را که در لاگ چاپ شده باز کنید:

```text
https://<railway-domain>/sub/<SEC>
```

پاسخ به‌صورت Base64 است و شامل سه کانفیگ آزمایشی VLESS و یک مورد نمایشی وضعیت است:

| مورد | انتقال | مسیر سرور | توضیح |
| --- | --- | --- | --- |
| FreeNET-VLESS-WS | WebSocket | `/vless/<uuid>` | TLS روی دامنه عمومی؛ ALPN برابر `http/1.1`. |
| FreeNET-XHTTP-Packet-Up | XHTTP `packet-up` | `/xhttp/<uuid>` | متدهای HTTP `GET` و `POST`؛ TLS روی دامنه عمومی. |
| FreeNET-XHTTP-Stream-Up | XHTTP `stream-up` | `/xhttp/<uuid>` | متدهای HTTP `GET` و `POST`؛ TLS روی دامنه عمومی. |
| وضعیت FreeNET | فقط نمایشی | endpoint برنامه نیست | Uptime فرایند و ترافیک کلی را نمایش می‌دهد و کانفیگ اتصال نیست. |

هدرهای پاسخ Subscription نیز آمار کلی Upload و Download را دارند. شمارنده‌ها و Uptime فقط در حافظه هستند؛ با restart پاک می‌شوند و روی دیسک ذخیره نمی‌شوند.

## اجرای محلی با Python

Python نسخه 3.12 یا جدیدتر پیشنهاد می‌شود.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
SEC=change-this-secret VLESS_UUID=12345678-1234-5678-1234-567812345678 PORT=8000 python main.py
```

برای مشاهده‌ی کانفیگ‌های آزمایشی، `http://localhost:8000/sub/change-this-secret` را باز کنید. برای آزمایش از طریق دامنه‌ی عمومی، خاتمه‌ی TLS را تنظیم کنید و مقدار `RAILWAY_PUBLIC_DOMAIN` را برابر دامنه‌ی مورد استفاده برای URL شروع برنامه قرار دهید.

## Docker

کانتینر stateless است و به Volume نیاز ندارد:

```bash
docker build -t freenet .
docker run --rm -p 8000:8000 -e PORT=8000 -e SEC=change-this-secret freenet
```

## ساختار پروژه

```text
FreeNET/
├── main.py          # برنامه FastAPI، Subscription آزمایشی، بررسی UUID و مسیرها
├── core.py          # انتقال داده TCP، شمارنده‌های حافظه‌ای و uptime
├── health.py        # پردازش درخواست‌های VLESS WebSocket و XHTTP
├── Dockerfile
├── railway.json
├── requirements.txt
├── README.md
└── README-fa.md
```
