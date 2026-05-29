# 🤖 راهنمای نصب ربات دانلودر تلگرامی بر روی VPS

## 📋 پیش‌نیازها
- VPS با Linux (Ubuntu یا Debian)
- Python 3.8+
- توکن بات تلگرام

## 🚀 مراحل نصب

### 1️⃣ اتصال به VPS
```bash
ssh root@YOUR_SERVER_IP
```

### 2️⃣ بروزرسانی سیستم
```bash
apt update && apt upgrade -y
apt install python3 python3-pip git -y
```

### 3️⃣ کلون کردن پروژه (یا بارگذاری فایل‌ها)
```bash
cd /home
mkdir telegram-bot && cd telegram-bot

# اگر روی گیت‌هاب است:
# git clone <YOUR_REPO_URL> .

# یا کپی فایل‌ها مستقیم
# (از طریق SCP یا FTP)
```

### 4️⃣ نصب وابستگی‌ها
```bash
pip3 install -r requirements.txt
```

### 5️⃣ تنظیم توکن
```bash
nano telegram_downloader_bot.py
```

**خط 31** را پیدا کنید و توکن خود را جایگزین کنید:
```python
TOKEN = "YOUR_BOT_TOKEN"  # توکن خود را اینجا قرار دهید
```

### 6️⃣ ایجاد Systemd Service (برای اجرای خودکار)

```bash
cat > /etc/systemd/system/telegram-bot.service << 'EOF'
[Unit]
Description=Telegram Downloader Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/telegram-bot
ExecStart=/usr/bin/python3 /home/telegram-bot/telegram_downloader_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### 7️⃣ فعال‌سازی و شروع سرویس
```bash
systemctl daemon-reload
systemctl enable telegram-bot
systemctl start telegram-bot
```

### 8️⃣ بررسی وضعیت
```bash
systemctl status telegram-bot
journalctl -u telegram-bot -f  # برای دیدن لاگ‌ها
```

---

## 📝 دستورات مفید

### شروع مجدد بات
```bash
systemctl restart telegram-bot
```

### متوقف کردن بات
```bash
systemctl stop telegram-bot
```

### حذف سرویس
```bash
systemctl disable telegram-bot
systemctl stop telegram-bot
rm /etc/systemd/system/telegram-bot.service
systemctl daemon-reload
```

### دیدن لاگ‌های زنده
```bash
journalctl -u telegram-bot -f
```

---

## 🔧 مشکل‌ یابی

### مشکل: "ModuleNotFoundError"
```bash
pip3 install -r requirements.txt
```

### مشکل: دسترسی رد شده
```bash
chmod +x telegram_downloader_bot.py
```

### مشکل: خطای توکن
- توکن را از [@BotFather](https://t.me/BotFather) دوباره دریافت کنید
- مطمئن شوید که سرویس دوباره شروع شود

---

## 📊 نکات مهم

✅ فایل‌های دانلود شده در پوشه `downloads` ذخیره می‌شوند
✅ فایل‌های موقت در پوشه `temp` ذخیره می‌شوند
✅ حداکثر اندازه فایل: 10GB
✅ حد آستانه پارتیشن‌بندی: 1.9GB

---

## 🛡️ توصیه‌های امنیتی

```bash
# اجرای بات با کاربر غیر root
useradd -m telegrambot
usermod -aG telegrambot /home/telegram-bot
chown -R telegrambot:telegrambot /home/telegram-bot

# تغییر سرویس برای استفاده از این کاربر
# در فایل service تغییر: User=telegrambot
```

---

## 📞 نیاز به کمک؟

برای مشکلات بیشتر:
```bash
cat /var/log/syslog | grep telegram-bot
```

اگر فایل `downloads` یا `temp` وجود ندارد:
```bash
mkdir -p downloads temp
chmod 755 downloads temp
```
