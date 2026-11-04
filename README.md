<div dir="rtl" align="right">

<h1>🛰️ Falix-Relay</h1>

<p>یک رلهٔ سبک VLESS + WebSocket بر پایهٔ Xray-core رسمی.</p>

<p>
  <a href="README-En.md">🇬🇧 English</a>
  ·
  <a href="https://github.com/MHDLabs/Falix-Relay">مخزن GitHub</a>
</p>

<p>Falix-Relay برای راه‌اندازی یک سرویس ساده طراحی شده است. تنظیمات اصلی را با چند متغیر محیطی انجام می‌دهی و سرویس بدون پنل یا دیتابیس اجرا می‌شود.</p>

<h2>✨ امکانات</h2>

<ul>
  <li>🔐 یک ورودی VLESS با یک UUID</li>
  <li>🌐 انتقال WebSocket با مسیر قابل تنظیم</li>
  <li>⚙️ تنظیم پورت و مسیر از طریق متغیرهای محیطی</li>
  <li>📦 ایمیج Docker برای معماری‌های AMD64 و ARM64</li>
  <li>🔒 اجرای Xray با کاربر غیر root</li>
  <li>🧪 بررسی تنظیمات با فرمان check</li>
</ul>

<h2>🧩 محدودهٔ پروژه</h2>

<ul>
  <li>هستهٔ پروژه، نسخهٔ رسمی Xray-core با نسخهٔ ثابت v26.10.21 است.</li>
  <li>در حال حاضر فقط VLESS + WebSocket فعال است.</li>
  <li>پروژه یک UUID و یک ورودی دارد.</li>
  <li>خروجی Xray از نوع direct است.</li>
  <li>پنل وب، ربات، دیتابیس، سیستم کاربری، سهمیه و آمار مصرف ندارد.</li>
  <li>اطلاعاتی داخل کانتینر به‌صورت پایدار ذخیره نمی‌شود.</li>
</ul>

<h2>☁️ اجرای پروژه روی Falix</h2>

<p>برای اجرای Falix-Relay به نوع سروری نیاز داری که امکان استفاده از Docker image سفارشی را ارائه کند. این گزینه در همهٔ سرورهای Falix وجود ندارد. قبل از شروع، بخش <a href="https://kb.falixnodes.net/falix/dashboard/setup/startup-configuration">Startup Configuration</a> را بررسی کن.</p>

<p>⚠️ طبق <a href="https://falixnodes.net/acceptable-use-policy">سیاست استفادهٔ قابل قبول Falix</a>، سرورهای Free برای اجرای نرم‌افزار VPN یا Proxy و انتقال ترافیک دیگران مجاز نیستند. این پروژه را روی سرور Free اجرا نکن. شرایط پلن مورد استفاده‌ات را هم پیش از استقرار بخوان.</p>

<h3>۱. انتخاب ایمیج</h3>

<p>در تنظیمات Startup سرور، ایمیج زیر را وارد یا انتخاب کن. اگر پنل سرورت چنین گزینه‌ای ندارد، آن نوع سرور برای اجرای مستقیم این ایمیج مناسب نیست.</p>

</div>

```text
ghcr.io/mhdlabs/falix-relay:latest
```

<div dir="rtl" align="right">

<h3>۲. تنظیم پورت</h3>

<p>از بخش Network → Ports پورت اختصاص‌یافته به سرورت را بردار. مقدار PORT باید دقیقاً با همان عدد برابر باشد.</p>

<p>نکته: Falix مقدار پورت را با متغیر SERVER_PORT در اختیار محیط اجرا می‌گذارد، اما نسخهٔ فعلی Falix-Relay فقط متغیر PORT را می‌خواند. بنابراین PORT را خودت با همان شماره تنظیم کن. برنامه هنوز SERVER_PORT را به‌صورت خودکار نمی‌خواند.</p>

<h3>۳. تنظیم متغیرهای محیطی</h3>

<ul>
  <li><code dir="ltr">XRAY_UUID</code>: یک UUID خصوصی و تصادفی</li>
  <li><code dir="ltr">PORT</code>: پورت اختصاص‌یافته در پنل Falix</li>
  <li><code dir="ltr">WS_PATH</code>: مسیر WebSocket. مقدار پیش‌فرض <code dir="ltr">/relay</code> است.</li>
</ul>

<p>برای ساخت UUID در Linux از دستور زیر استفاده کن:</p>

</div>

```sh
cat /proc/sys/kernel/random/uuid
```

<div dir="rtl" align="right">

<h3>۴. اجرای سرویس</h3>

<p>سرور را از پنل Falix اجرا کن و خروجی Console را ببین. پیام شروع سرویس باید پورت تنظیم‌شده و مسیر WebSocket را نشان بدهد.</p>

<h2>🔗 ساخت لینک اتصال</h2>

<p>Falix دو مسیر معمول برای اتصال در اختیار می‌گذارد. آدرس و پورت را از بخش Network پنل بردار.</p>

<h3>اتصال مستقیم با پورت عمومی</h3>

<p>این روش از WebSocket معمولی استفاده می‌کند و TLS ندارد. مقدارهای نمونه را با اطلاعات سرور خودت عوض کن.</p>

</div>

```text
vless://<XRAY_UUID>@<FALIX_ADDRESS>:<FALIX_PORT>?encryption=none&security=none&type=ws&host=<FALIX_ADDRESS>&path=%2Frelay#Falix-Relay
```

<div dir="rtl" align="right">

<h3>اتصال از طریق Reverse Proxy</h3>

<p>برای اتصال امن، در پنل Falix یک Reverse Proxy با TLS فعال بساز و پورت داخلی سرویس را به‌عنوان Backend انتخاب کن. پس از فعال شدن TLS، از دامنهٔ همان Proxy استفاده کن.</p>

</div>

```text
vless://<XRAY_UUID>@<FALIX_DOMAIN>:443?encryption=none&security=tls&sni=<FALIX_DOMAIN>&type=ws&host=<FALIX_DOMAIN>&path=%2Frelay#Falix-Relay
```

<div dir="rtl" align="right">

<p>ساب‌دامین DNS به‌تنهایی TLS ایجاد نمی‌کند. برای استفاده از security=tls باید دامنه از طریق Reverse Proxy دارای TLS ارائه شود و مسیر WebSocket یعنی <code dir="ltr">/relay</code> بدون تغییر به سرویس برسد.</p>

<h2>⚙️ متغیرهای محیطی</h2>

<ul>
  <li><code dir="ltr">XRAY_UUID</code>، ضروری برای اجرا و بررسی تنظیمات. UUID تنها کلاینت VLESS است.</li>
  <li><code dir="ltr">PORT</code>، پیش‌فرض 8080. پورت TCP داخلی سرویس است و باید بین 1024 تا 65535 باشد.</li>
  <li><code dir="ltr">WS_PATH</code>، پیش‌فرض /relay. مسیر ورودی WebSocket است.</li>
</ul>

<h2>🐳 اجرای محلی با Docker Compose</h2>

<p>برای اجرای پروژه روی یک میزبان Docker، مخزن را دریافت کن و فایل تنظیمات نمونه را کپی کن:</p>

</div>

```sh
git clone https://github.com/MHDLabs/Falix-Relay.git
cd Falix-Relay
cp .env.example .env
```

<div dir="rtl" align="right">

<p>مقدار نمونهٔ XRAY_UUID را در فایل .env با UUID خصوصی خودت جایگزین کن. سپس ایمیج را بساز و تنظیمات Xray را بررسی کن:</p>

</div>

```sh
docker compose build
docker compose run --rm falix-relay check
```

<div dir="rtl" align="right">

<p>برای اجرای سرویس و مشاهدهٔ لاگ‌ها:</p>

</div>

```sh
docker compose up -d
docker compose logs -f falix-relay
```

<div dir="rtl" align="right">

<p>فایل Compose پورت را فقط روی 127.0.0.1 منتشر می‌کند. برای دسترسی عمومی، یک Reverse Proxy دارای TLS روی همان میزبان تنظیم کن و WebSocket را به پورت محلی سرویس بفرست.</p>

<h2>📦 دریافت ایمیج آماده</h2>

<p>GitHub Actions با انتشار تغییرات روی main و تگ‌های v*، ایمیج چندمعماری را در GitHub Container Registry می‌سازد.</p>

</div>

```sh
docker pull ghcr.io/mhdlabs/falix-relay:latest
```

<div dir="rtl" align="right">

<p>برای دریافت بدون ورود، دسترسی Package در GitHub باید روی Public باشد.</p>

<h2>🛠️ عیب‌یابی</h2>

<ul>
  <li>سرویس اجرا نمی‌شود: مقدار و قالب XRAY_UUID و بازهٔ PORT را بررسی کن.</li>
  <li>اتصال رد می‌شود: مطمئن شو PORT با پورت اختصاص‌یافته در Falix برابر است.</li>
  <li>اتصال مستقیم برقرار نمی‌شود: آدرس، پورت، UUID و مسیر /relay را بررسی کن. برای اتصال مستقیم TLS را خاموش نگه دار.</li>
  <li>اتصال امن برقرار نمی‌شود: وضعیت TLS در Reverse Proxy و پورت Backend را بررسی کن.</li>
  <li>خطای تنظیمات داری: فرمان check را اجرا کن و لاگ Xray را ببین.</li>
</ul>

<p>فرمان check فقط ساختار تنظیمات Xray را بررسی می‌کند. این فرمان وضعیت DNS، پورت عمومی، TLS، فایروال یا اتصال نهایی کلاینت را آزمایش نمی‌کند.</p>

<h2>🔐 امنیت</h2>

<ul>
  <li>UUID را خصوصی نگه دار و آن را در مخزن یا تصویر عمومی منتشر نکن.</li>
  <li>اتصال مستقیم WebSocket رمزنگاری TLS ندارد.</li>
  <li>برای WSS از Reverse Proxy دارای TLS استفاده کن.</li>
  <li>پورت خام سرویس را بدون لایهٔ محافظ در معرض اینترنت قرار نده.</li>
  <li>پیش از حذف یا جایگزینی کانتینر، UUID خودت را در محل امن نگه دار.</li>
</ul>

<h2>📄 مجوز</h2>

<p>فایل‌های Falix-Relay تحت مجوز MIT منتشر شده‌اند. Xray-core پروژه‌ای مستقل است و مجوز خودش را دارد.</p>

<hr>

<p>❤️ ساخته‌شده با عشق در MHDLabs</p>
<p>Keep it simple :)</p>

</div>
