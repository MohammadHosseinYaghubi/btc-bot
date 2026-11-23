import os
import logging
import httpx
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ========== بارگذاری متغیرهای محیطی ==========
load_dotenv()

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError(
        "متغیر محیطی BOT_TOKEN تنظیم نشده است. "
        "فایل .env را بررسی کنید یا متغیر محیطی سرور را ست کنید."
    )

# ========== لاگ ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ========== تنظیمات API ==========
BINANCE_URL = "https://api.binance.com/api/v3/ticker/24hr"
REQUEST_TIMEOUT = 10.0


# ========== تابع مشترک دریافت و قالب‌بندی قیمت ==========
async def fetch_btc_price() -> str:
    """قیمت لحظه‌ای بیت‌کوین را از بایننس می‌گیرد و متن آماده برمی‌گرداند."""
    params = {"symbol": "BTCUSDT"}

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.get(BINANCE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    price = float(data["lastPrice"])
    change = float(data["priceChangePercent"])
    high = float(data["highPrice"])
    low = float(data["lowPrice"])
    volume = float(data["quoteVolume"])  # حجم ۲۴ ساعته به USDT

    arrow = "📈" if change >= 0 else "📉"
    sign = "+" if change >= 0 else ""
    trend_emoji = "🟢" if change >= 0 else "🔴"

    text = (
        "┌──────────────────────────────┐\n"
        "│   ₿  **BTC / USDT — Live**       │\n"
        "└──────────────────────────────┘\n\n"
        f"💵 **قیمت لحظه‌ای:**  `${price:,.2f}`\n\n"
        f"{trend_emoji} **تغییر ۲۴ ساعته:**  `{sign}{change:.2f}%`\n\n"
        "─────────── ۲۴ ساعت گذشته ───────────\n"
        f"📈 **بالاترین:**  `${high:,.2f}`\n"
        f"📉 **پایین‌ترین:**  `${low:,.2f}`\n"
        f"📊 **حجم معاملات:**  `${volume:,.0f}`\n\n"
        "─────────── منبع داده ───────────\n"
        "🔗 **Binance Spot API**\n"
        "⏱ به‌روزرسانی: لحظه‌ای"
    )
    return text


# ========== دستور /start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    first_name = user.first_name if user.first_name else "دوست عزیز"

    keyboard = [
        [InlineKeyboardButton("💰 دریافت قیمت بیت‌کوین", callback_data="btc_price")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"سلام **{first_name}** 👋\n\n"
        "به **BTC Live** خوش آمدی — همراه لحظه‌ای بازار بیت‌کوین.\n\n"
        "**دستورات موجود:**\n"
        "• `/start` — نمایش این راهنما\n"
        "• `/btc` — قیمت لحظه‌ای بیت‌کوین\n"
        "• `/price` — همان دستور `/btc`\n\n"
        "برای شروع، روی دکمه زیر بزن یا دستور `/btc` را ارسال کن:"
    )
    await update.message.reply_text(
        text, reply_markup=reply_markup, parse_mode="Markdown"
    )


# ========== دستور /btc و /price ==========
async def btc_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("⏳ در حال دریافت قیمت لحظه‌ای...")

    try:
        text = await fetch_btc_price()
        await msg.edit_text(text, parse_mode="Markdown")
    except httpx.HTTPStatusError as e:
        logger.error(f"Binance HTTP error: {e.response.status_code} - {e.response.text}")
        await msg.edit_text(
            "⚠️ سرویس قیمت موقتاً پاسخ نمی‌دهد. لطفاً چند لحظه بعد دوباره تلاش کن."
        )
    except httpx.RequestError as e:
        logger.error(f"Binance request error: {e}")
        await msg.edit_text(
            "🌐 مشکل در اتصال به اینترنت سرور. لطفاً بعداً دوباره تلاش کن."
        )
    except (KeyError, ValueError) as e:
        logger.error(f"Binance response parse error: {e}")
        await msg.edit_text(
            "❌ داده‌ی دریافتی نامعتبر بود. لطفاً دوباره تلاش کن."
        )
    except Exception:
        logger.exception("Unexpected error in btc_command")
        await msg.edit_text("❌ خطای غیرمنتظره رخ داد. لطفاً بعداً تلاش کن.")


# ========== مدیریت دکمه‌های شیشه‌ای ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()  # جلوگیری از لودینگ دکمه

    if query.data == "btc_price":
        # به‌جای ساخت Update جعلی، منطق را از همان‌جا اجرا می‌کنیم
        await query.message.edit_text("⏳ در حال دریافت قیمت لحظه‌ای...")
        try:
            text = await fetch_btc_price()
            await query.message.edit_text(text, parse_mode="Markdown")
        except Exception:
            logger.exception("Error in button_handler")
            await query.message.edit_text(
                "❌ خطا در دریافت قیمت. لطفاً دوباره تلاش کن."
            )


# ========== راه‌اندازی ==========
def main() -> None:
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc_command))
    app.add_handler(CommandHandler("price", btc_command))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("BTC Live bot is starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()