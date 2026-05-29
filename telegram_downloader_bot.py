#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Downloader Bot
دانلود فایل‌ها از طریق URL و ارسال به تلگرام با پشتیبانی پارتیشن‌بندی
"""

import os
import sys
import logging
import zipfile
import shutil
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.error import BadRequest

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ثوابت
TOKEN = "YOUR_BOT_TOKEN"  # توکن بات تلگرام خود را قرار دهید
MAX_FILE_SIZE = 1.9 * 1024 * 1024 * 1024  # 1.9 GB
DOWNLOAD_DIR = Path("downloads")
TEMP_DIR = Path("temp")

# حالات کنوازشی (Conversation States)
WAITING_FOR_URL = 0
WAITING_FOR_FILE_TYPE = 1

# ایجاد دایرکتوری‌ها
DOWNLOAD_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)


class FileDownloader:
    """کلاس برای دانلود و مدیریت فایل‌ها"""

    @staticmethod
    def _get_session() -> requests.Session:
        """ایجاد session با retry strategy"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    @staticmethod
    def get_file_size(url: str) -> Optional[int]:
        """دریافت اندازه فایل بدون دانلود کامل"""
        session = FileDownloader._get_session()
        try:
            response = session.head(url, allow_redirects=True, timeout=30)
            size = response.headers.get('content-length')
            return int(size) if size else None
        except Exception as e:
            logger.error(f"خطا در دریافت اندازه فایل: {e}")
            return None
        finally:
            session.close()

    @staticmethod
    def download_file(url: str, filepath: Path, callback=None) -> bool:
        """دانلود فایل با نمایش پیشرفت"""
        session = FileDownloader._get_session()
        try:
            response = session.get(url, stream=True, timeout=120)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if callback and total_size > 0:
                            progress_pct = int((downloaded / total_size) * 100)
                            callback(progress_pct, downloaded, total_size)

            return True
        except Exception as e:
            logger.error(f"خطا در دانلود: {e}")
            return False
        finally:
            session.close()
    
    @staticmethod
    def split_file_to_zip(filepath: Path, max_size: int = MAX_FILE_SIZE) -> list:
        """تقسیم فایل بزرگ به چندین ZIP حداکثر 1.9GB"""
        file_size = filepath.stat().st_size

        if file_size <= max_size:
            return [filepath]

        parts = []
        part_num = 1
        current_size = 0
        buffer = []
        buffer_size = 0

        try:
            work_dir = TEMP_DIR / filepath.stem
            if work_dir.exists():
                shutil.rmtree(work_dir)
            work_dir.mkdir(parents=True)

            chunk_size = 262144  # 256KB chunks

            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        # نوشتن buffer نهایی
                        if buffer:
                            part_zip = DOWNLOAD_DIR / f"{filepath.stem}_part{part_num}.zip"
                            with zipfile.ZipFile(part_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                                temp_data = b''.join(buffer)
                                zf.writestr(f"{filepath.stem}_part{part_num}.bin", temp_data)
                            parts.append(part_zip)
                        break

                    buffer.append(chunk)
                    buffer_size += len(chunk)

                    if buffer_size >= max_size:
                        # ایجاد ZIP از buffer
                        part_zip = DOWNLOAD_DIR / f"{filepath.stem}_part{part_num}.zip"
                        with zipfile.ZipFile(part_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                            temp_data = b''.join(buffer)
                            zf.writestr(f"{filepath.stem}_part{part_num}.bin", temp_data)
                        parts.append(part_zip)

                        part_num += 1
                        buffer = []
                        buffer_size = 0

            return parts

        except Exception as e:
            logger.error(f"خطا در پارتیشن‌بندی: {e}")
            return []
        finally:
            if work_dir.exists():
                shutil.rmtree(work_dir)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دستور شروع"""
    welcome_text = """
🤖 **خوش‌آمدید به ربات دانلودر تلگرامی**

من می‌تونم فایل‌ها رو از URL دانلود کرده و برای شما بفرستم.

**ویژگی‌ها:**
• دانلود فایل‌های تا 1.9GB بدون پارتیشن
• تقسیم خودکار برای فایل‌های بزرگتر
• نمایش پیشرفت دانلود
• ارسال مستقیم به تلگرام

**چطور استفاده کنم:**
لطفاً URL فایل را ارسال کنید.

مثال:
`https://example.com/file.zip`
    """
    
    await update.message.reply_text(
        welcome_text,
        parse_mode='Markdown'
    )
    return WAITING_FOR_URL


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """پردازش URL دریافتی"""
    url = update.message.text.strip()
    
    # بررسی معتبری URL
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            await update.message.reply_text(
                "❌ URL معتبر نیست. لطفاً یک URL صحیح ارسال کنید."
            )
            return WAITING_FOR_URL
    except Exception:
        await update.message.reply_text(
            "❌ خطا در پردازش URL."
        )
        return WAITING_FOR_URL
    
    # دریافت نام فایل
    try:
        filename = url.split('/')[-1].split('?')[0]
        if not filename:
            filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    except:
        filename = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # دریافت اندازه فایل
    status_msg = await update.message.reply_text(
        f"📊 درحال بررسی فایل...\n"
        f"🔗 {filename}"
    )
    
    file_size = FileDownloader.get_file_size(url)
    
    if file_size is None:
        await status_msg.edit_text(
            "❌ نتوانستم اندازه فایل را دریافت کنم.\n"
            "URL را دوباره بررسی کنید."
        )
        return WAITING_FOR_URL
    
    size_mb = file_size / (1024 * 1024)
    size_gb = file_size / (1024 * 1024 * 1024)
    
    if size_gb > 10:
        await status_msg.edit_text(
            f"❌ فایل خیلی بزرگ است ({size_gb:.2f}GB)\n"
            "حداکثر 10GB قابل دانلود است."
        )
        return WAITING_FOR_URL
    
    # شروع دانلود
    await status_msg.edit_text(
        f"📥 درحال دانلود...\n"
        f"📦 فایل: {filename}\n"
        f"💾 اندازه: {size_gb:.2f}GB ({size_mb:.0f}MB)\n\n"
        f"⏳ لطفاً صبر کنید..."
    )
    
    filepath = DOWNLOAD_DIR / filename

    last_update = 0

    async def progress_callback(progress_pct, downloaded, total):
        """نمایش پیشرفت"""
        nonlocal last_update
        try:
            if progress_pct >= last_update + 10:  # هر 10 درصد یک بار به‌روز کنید
                last_update = progress_pct
                downloaded_mb = downloaded / (1024 * 1024)
                total_mb = total / (1024 * 1024)
                bar_length = int(progress_pct / 5)
                await status_msg.edit_text(
                    f"📥 درحال دانلود...\n"
                    f"📦 {filename}\n"
                    f"💾 {downloaded_mb:.0f}MB / {total_mb:.0f}MB\n"
                    f"📊 {progress_pct}%\n\n"
                    f"{'█' * bar_length}{'░' * (20 - bar_length)}"
                )
        except Exception as e:
            logger.debug(f"خطا در به‌روز progress: {e}")
    
    # دانلود فایل
    success = FileDownloader.download_file(url, filepath, progress_callback)
    
    if not success:
        await status_msg.edit_text(
            "❌ دانلود ناموفق بود.\n"
            "لطفاً دوباره سعی کنید."
        )
        return WAITING_FOR_URL
    
    # بررسی اندازه و تقسیم
    actual_size = filepath.stat().st_size
    
    if actual_size > MAX_FILE_SIZE:
        await status_msg.edit_text(
            f"🔄 درحال تقسیم فایل...\n"
            f"📦 {filename}\n"
            f"💾 {actual_size/(1024*1024*1024):.2f}GB"
        )
        
        parts = FileDownloader.split_file_to_zip(filepath)
        
        if not parts:
            await status_msg.edit_text(
                "❌ خطا در تقسیم فایل."
            )
            return WAITING_FOR_URL
        
        # ارسال پارت‌ها
        await status_msg.edit_text(
            f"📤 درحال ارسال {len(parts)} فایل...\n\n"
        )
        
        for i, part in enumerate(parts, 1):
            try:
                with open(part, 'rb') as f:
                    await update.message.reply_document(
                        document=f,
                        caption=f"📦 قسمت {i} از {len(parts)}\n"
                                f"💾 {part.stat().st_size/(1024*1024):.0f}MB"
                    )
            except BadRequest as e:
                await update.message.reply_text(
                    f"❌ خطا در ارسال قسمت {i}: {str(e)}"
                )
    
    else:
        # ارسال بدون تقسیم
        try:
            with open(filepath, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    caption=f"✅ {filename}\n"
                            f"💾 {actual_size/(1024*1024):.0f}MB"
                )
        except BadRequest as e:
            await update.message.reply_text(
                f"❌ خطا در ارسال: {str(e)}"
            )
    
    # پاک‌سازی
    try:
        if filepath.exists():
            filepath.unlink()
        # پاک‌سازی دایرکتوری موقت
        temp_work_dir = TEMP_DIR / filename
        if temp_work_dir.exists():
            shutil.rmtree(temp_work_dir)
    except Exception as e:
        logger.warning(f"خطا در پاک‌سازی فایل‌ها: {e}")
    
    await status_msg.edit_text(
        "✅ کار تمام شد!\n\n"
        "برای دانلود فایل دیگری، URL جدید را ارسال کنید."
    )
    
    return WAITING_FOR_URL


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو عملیات"""
    await update.message.reply_text("❌ لغو شد.")
    return ConversationHandler.END


def main():
    """تابع اصلی"""
    
    # ایجاد Application
    app = Application.builder().token(TOKEN).build()
    
    # ایجاد conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    app.add_handler(conv_handler)
    
    # دستورات اضافی
    app.add_handler(CommandHandler('help', start))
    
    logger.info("🤖 ربات شروع شد...")
    
    # شروع
    app.run_polling()


if __name__ == '__main__':
    main()
