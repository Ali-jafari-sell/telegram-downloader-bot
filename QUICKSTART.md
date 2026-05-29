# 🚀 شروع سریع

## گزینه 1️⃣: اجرای مستقیم (بدون Docker)

```bash
# 1. نصب Python
apt install python3 python3-pip

# 2. نصب وابستگی‌ها
pip3 install -r requirements.txt

# 3. تنظیم توکن
nano telegram_downloader_bot.py
# خط 31 را ویرایش کنید

# 4. اجرا
python3 telegram_downloader_bot.py
```

---

## گزینه 2️⃣: اجرای با Docker (توصیه شده)

```bash
# 1. تنظیم متغیرها
cp .env.example .env
nano .env
# توکن خود را اضافه کنید

# 2. اجرا
docker-compose up -d

# 3. بررسی وضعیت
docker-compose logs -f
```

---

## گزینه 3️⃣: اجرای در Systemd

```bash
# 1. کپی فایل service
sudo cp telegram-bot.service /etc/systemd/system/

# 2. فعال‌سازی
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# 3. بررسی
sudo systemctl status telegram-bot
```

---

## 📱 استفاده

1. [@BotFather](https://t.me/BotFather) را باز کنید
2. `/newbot` را وارد کنید
3. توکن را کپی کنید
4. این توکن را در فایل `telegram_downloader_bot.py` جایگزین کنید
5. بات را شروع کنید

---

## ✅ تست کنید

```bash
# جستجوی بات خود در تلگرام
@your_bot_username

# دستورات:
/start  - شروع
/help   - راهنما
/stats  - آمار
/cancel - لغو
```

---

## 🛠️ ویژگی‌ها

✅ دانلود فایل‌های بزرگ تا 10GB
✅ پارتیشن‌بندی خودکار بر روی 1.9GB
✅ نمایش پیشرفت درخت‌زندگی
✅ فرستادن مستقیم به تلگرام
✅ ذخیره آمار استفاده
✅ سهل‌الاستعمال و سریع

---

## 🆘 مشکلات متداول

### خطای Module Not Found
```bash
pip3 install --upgrade pip
pip3 install -r requirements.txt
```

### خطای Permission Denied
```bash
chmod +x telegram_downloader_bot.py
```

### خطای Connection
- VPS را دوباره راه‌اندازی کنید
- فایروال را بررسی کنید
- توکن را دوباره تایید کنید

---

**آماده‌اید؟ شروع کنید! 🚀**
