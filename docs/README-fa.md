# 🛰️ راهنمای راه‌اندازی Falix-Relay

[🇬🇧 English guide](README.md) · [README فارسی پروژه](../README-fa.md) · [مخزن GitHub](https://github.com/MHDLabs/Falix-Relay)


Falix-Relay باینری رسمی Xray-core را به‌صورت یک سرویس مینیمال VLESS + WebSocket اجرا می‌کند. این راهنما متغیرهای محیطی، تنظیم شبکه در Falix، قالب لینک کلاینت و اجرای عمومی Docker را توضیح می‌دهد.

> [!WARNING]
> **سرورهای رایگان Falix مجاز به اجرای نرم‌افزار VPN/Proxy یا انتقال ترافیک دیگران نیستند.** این محدودیت در [سیاست استفادهٔ قابل قبول Falix](https://falixnodes.net/acceptable-use-policy) آمده است. این پروژه را روی سرور Free اجرا نکن. پیش از استفاده از پلن‌های دیگر نیز قوانین همان پلن را بررسی کن.

## 🧭 فهرست

- [پیش‌نیازها](#-پیشنیازها)
- [راه‌اندازی روی Falix](#-راهاندازی-روی-falix)
- [لینک‌های اتصال](#-لینکهای-اتصال)
- [متغیرهای محیطی](#-متغیرهای-محیطی)
- [اجرا با Docker Compose](#-اجرا-با-docker-compose)
- [عیب‌یابی](#-عیبیابی)
- [به‌روزرسانی و حذف](#-بهروزرسانی-و-حذف)

## 📦 پیش‌نیازها

- پلن و نوع سروری در Falix که قوانین و محیط اجرایی آن اجازهٔ این کاربرد را بدهد
- محیط اجرایی سازگار با ایمیج منتشرشدهٔ پروژه: `ghcr.io/mhdlabs/falix-relay:latest`
- یک پورت عمومی اختصاص‌یافته
- یک UUID خصوصی
- برای WSS، یک Reverse Proxy در Falix که به پورت داخلی سرویس اشاره کند

**نکتهٔ مهم دربارهٔ محیط اجرا:** گزینهٔ انتخاب Docker Image سفارشی در Falix فقط برای بعضی انواع سرور که چنین گزینه‌ای دارند در دسترس است. انتشار ایمیج در GHCR به این معنی نیست که همهٔ انواع سرور Falix می‌توانند مستقیماً آن را اجرا کنند. راهنمای [تنظیمات Startup در Falix](https://kb.falixnodes.net/falix/dashboard/setup/startup-configuration) را ببین.

## ☁️ راه‌اندازی روی Falix

### ۱. بررسی محیط اجرا

از نوع سروری استفاده کن که امکان اجرای ایمیج کانتینری Falix-Relay را داشته باشد. اگر نوع سرورت گزینهٔ اجرای Docker Image سازگار را ارائه نمی‌کند، نمی‌توانی این ایمیج را مستقیماً در همان سرور انتخاب کنی.

### ۲. اختصاص پورت عمومی

در پنل Falix وارد بخش **Network → Ports** شو و پورت عمومی اختصاص‌یافته به سرور را یادداشت کن. Falix شمارهٔ پورت را تعیین می‌کند؛ فرض نکن مقدار آن حتماً `8080` است.

برنامه روی `0.0.0.0` گوش می‌دهد؛ این آدرس برای دسترسی عمومی از طریق شبکهٔ Falix ضروری است. جزئیات بیشتر در [راهنمای شبکهٔ Falix](https://client.falixnodes.net/guides/panel/network-page-deep) آمده است.

### ۳. تنظیم متغیرهای محیطی

در بخش Environment سرور، این مقادیر را تنظیم کن:

| متغیر | مقدار |
|---|---|
| `XRAY_UUID` | یک UUID خصوصی و جدید |
| `PORT` | دقیقاً همان شمارهٔ پورت نمایش‌داده‌شده در **Network → Ports** |
| `WS_PATH` | `/relay` |

Falix پورت اختصاص‌یافته را از طریق متغیر `SERVER_PORT` در اختیار سرور قرار می‌دهد؛ اما نقطهٔ ورود فعلی Falix-Relay متغیر `PORT` را می‌خواند. بنابراین مقدار عددی پورت Falix را در `PORT` هم وارد کن. ایمیج فعلی به‌صورت خودکار `SERVER_PORT` را به `PORT` تبدیل نمی‌کند.

برای ساخت UUID در Linux:


```sh
cat /proc/sys/kernel/random/uuid
```


UUID را محرمانه نگه دار و آن را در Issue عمومی، تصویر صفحه یا مخزن عمومی قرار نده.

### ۴. اجرای سرویس

از پنل Falix سرور را Start یا Restart کن و خروجی بخش Console را بررسی کن. پیام شروع سرویس باید شبیه نمونهٔ زیر باشد:


```text
Falix-Relay: starting official Xray-core on TCP port 12345 (WebSocket path /relay)
```


عدد پورت در این مثال صرفاً نمونه است؛ از پورتی استفاده کن که برای سرور خودت اختصاص داده شده است.

### ۵. انتخاب مسیر اتصال

Falix چند روش برای دسترسی به سرور ارائه می‌کند:

- **Ports:** آدرس و پورت عمومی مستقیم؛ بدون TLS.
- **Falix subdomain:** نام دامنه‌ای که به سرور اشاره می‌کند، اما همچنان به پورت اختصاص‌یافته نیاز دارد و به‌تنهایی TLS ندارد.
- **Reverse Proxy:** دامنه با TLS خودکار؛ برای WebSocket امن (WSS) از این روش استفاده کن.

راهنماهای رسمی [Domains and HTTPS](https://client.falixnodes.net/guides/web-apps/domains-and-https) و [WebSockets](https://client.falixnodes.net/guides/web-apps/websockets) جزئیات بیشتری دارند.

## 🔗 لینک‌های اتصال

ورودی Xray از WebSocket بدون TLS استفاده می‌کند. قالب لینک را مطابق روش انتشار سرویس انتخاب کن.

### اتصال مستقیم با آدرس و پورت Falix — WebSocket معمولی

از آدرس و پورت بخش **Network → Ports** استفاده کن:


```text
vless://<XRAY_UUID>@<FALIX_ADDRESS>:<FALIX_PORT>?encryption=none&security=none&type=ws&host=<FALIX_ADDRESS>&path=%2Frelay#Falix-Relay
```


این روش TLS ندارد. کلاینت باید VLESS روی WebSocket معمولی را پشتیبانی کند.

### اتصال از طریق Falix Reverse Proxy — WebSocket امن

اگر Reverse Proxy را ساخته‌ای و وضعیت TLS آن فعال است، از دامنهٔ پروکسی و پورت HTTPS استفاده کن:


```text
vless://<XRAY_UUID>@<FALIX_DOMAIN>:443?encryption=none&security=tls&sni=<FALIX_DOMAIN>&type=ws&host=<FALIX_DOMAIN>&path=%2Frelay#Falix-Relay
```


تمام جای‌نگهدارها را با مقادیر واقعی خودت جایگزین کن. Reverse Proxy باید درخواست‌های WebSocket را به همان پورت داخلی تنظیم‌شده در `PORT` منتقل کند و مسیر `/relay` را تغییر ندهد.

> [!NOTE]
> ساب‌دامین بخش DNS/Subdomains با دامنهٔ Reverse Proxy یکی نیست. ساب‌دامین DNS به‌تنهایی TLS ندارد. برای پورت خام از `security=none` استفاده کن؛ برای `security=tls` ابتدا Reverse Proxy را با TLS فعال تنظیم کن.

## ⚙️ متغیرهای محیطی

| متغیر | ضروری | پیش‌فرض | توضیح |
|---|---:|---|---|
| `XRAY_UUID` | برای `run` و `check` بله | — | UUID خصوصی تنها کلاینت VLESS |
| `PORT` | خیر | `8080` | پورت TCP؛ بازهٔ معتبر `1024` تا `65535` |
| `WS_PATH` | خیر | `/relay` | مسیر درخواست WebSocket |

پیکربندی فعلی یک ورودی VLESS و یک خروجی مستقیم دارد. پنل وب، مدیریت حساب، دیتابیس، سهمیه، شمارندهٔ ترافیک، سرویس QR یا ذخیره‌سازی پایدار داخل کانتینر در پروژه وجود ندارد.

## 🐳 اجرا با Docker Compose

این بخش برای یک میزبان Docker است که کنترل کامل آن را داری و می‌توانی روی همان میزبان یک TLS Reverse Proxy اجرا کنی. این روش جایگزین مراحل تنظیم پنل و محیط اجرایی Falix نیست.

۱. مخزن را دریافت و فایل محیطی را بساز:


```sh
git clone https://github.com/MHDLabs/Falix-Relay.git
cd Falix-Relay
cp .env.example .env
```


۲. یک UUID بساز و مقدار نمونهٔ `XRAY_UUID` را در فایل `.env` جایگزین کن. با UUID نمونه سرویس واقعی را اجرا نکن.

۳. ایمیج را بساز و تنظیمات را بررسی کن:


```sh
docker compose build
docker compose run --rm falix-relay check
```


۴. سرویس را اجرا و لاگ‌ها را مشاهده کن:


```sh
docker compose up -d
docker compose logs -f falix-relay
```


فایل Compose ارائه‌شده پورت را فقط روی `127.0.0.1` منتشر می‌کند. روی همان میزبان یک Reverse Proxy دارای TLS تنظیم کن تا ترافیک WebSocket را به همین پورت محلی بفرستد. نگاشت پورت را بدون آگاهی از پیامدهای انتشار WebSocket بدون TLS روی رابط عمومی تغییر نده.

برای دریافت مستقیم ایمیج آماده:


```sh
docker pull ghcr.io/mhdlabs/falix-relay:latest
```


ایمیج برای Linux با معماری‌های `amd64` و `arm64` ساخته می‌شود. دریافت بدون ورود به GHCR مستلزم Public بودن Package است.

## 🧰 عیب‌یابی

| نشانه | بررسی |
|---|---|
| کانتینر بلافاصله خارج می‌شود | مقدار و فرمت `XRAY_UUID` را بررسی کن؛ Console در Falix یا `docker logs` را ببین. |
| اتصال رد می‌شود | مطمئن شو سرویس اجراست و `PORT` با پورت اختصاص‌یافته در Falix یکسان است. |
| اتصال Timeout می‌شود | تخصیص پورت در Falix و قوانین Firewall را بررسی کن. |
| اتصال مستقیم برقرار نمی‌شود | آدرس و پورت دقیق Falix را وارد کن و TLS را در کلاینت غیرفعال کن. |
| اتصال WSS برقرار نمی‌شود | فعال بودن Reverse Proxy و TLS، درستی پورت مقصد و عبور WebSocket Upgrade را بررسی کن. |
| کلاینت به سرویس می‌رسد اما احراز هویت نمی‌شود | UUID و مسیر `/relay` را تطبیق بده. |
| Docker Compose اجرا نمی‌شود | فرمان‌های `docker compose logs falix-relay` و `docker compose run --rm falix-relay check` را اجرا کن. |

فرمان `check` تنظیمات را با ابزار خود Xray اعتبارسنجی می‌کند؛ اما DNS عمومی، پورت Falix، وضعیت TLS، Firewall یا اتصال کامل کلاینت را آزمایش نمی‌کند.

## 🔄 به‌روزرسانی و حذف

برای استقرار مبتنی بر GHCR، ایمیج جدید را دریافت و سرور را با همان متغیرهای محیطی Restart کن:


```sh
docker pull ghcr.io/mhdlabs/falix-relay:latest
```


برای Docker Compose:


```sh
docker compose pull
docker compose up -d
```


برای توقف و حذف کانتینر Compose:


```sh
docker compose down
```


Falix-Relay دادهٔ پایدار داخل کانتینر نگهداری نمی‌کند. پیش از جایگزینی یا حذف سرویس، نسخهٔ خصوصی UUID را در محل امن نگه دار.

---

**مستندات بیشتر:** [README پروژه](../README.md) · [راهنمای فارسی](README-fa.md) · [کد منبع](https://github.com/MHDLabs/Falix-Relay)
