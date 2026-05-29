FROM python:3.11-slim

# تنظیم دایرکتوری کاری
WORKDIR /app

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# کپی فایل‌ها
COPY requirements.txt .
COPY telegram_downloader_bot.py .

# نصب وابستگی‌های پایتون
RUN pip install --no-cache-dir -r requirements.txt

# ایجاد دایرکتوری‌های مورد نیاز
RUN mkdir -p downloads temp logs

# اجرا
CMD ["python", "telegram_downloader_bot.py"]
