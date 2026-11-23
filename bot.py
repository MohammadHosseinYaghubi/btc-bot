import logging
import os
from dotenv import load_dotenv  
load_dotenv()  
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

# توکن رباتت رو اینجا بذار
# TOKEN = "YOUR_BOT_TOKEN_HERE"
# ========== تنظیمات ==========
TOKEN = os.environ.get("BOT_TOKEN")  # توکن را از متغیر محیطی می‌خوانیم
if not TOKEN:
    raise ValueError("متغیر محیطی BOT_TOKEN تنظیم نشده است.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("قیمت بیت‌کوین 🚀", callback_data="btc")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = (
        "سلام 👋\n\n"
        "به ربات قیمت بیت‌کوین خوش اومدی!\n\n"
        "دستورات موجود:\n"
        "• /start — شروع مجدد\n"
        "• /btc — قیمت لحظه‌ای بیت‌کوین\n\n"
        "برای دریافت قیمت سریع روی دکمه زیر کلیک کن:"
    )
    await update.message.reply_text(text, reply_markup=reply_markup)

async def btc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("در حال دریافت قیمت...")
    
    try:
        # از API عمومی بایننس استفاده می‌کنیم (سریع و بدون نیاز به کلید)
        url = "https://api.binance.com/api/v3/ticker/24hr?symbol=BTCUSDT"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        price = float(data["lastPrice"])
        change = float(data["priceChangePercent"])
        high = float(data["highPrice"])
        low = float(data["lowPrice"])
        
        emoji = "🟢" if change >= 0 else "🔴"
        
        text = (
            f"₿ **قیمت لحظه‌ای بیت‌کوین**\n\n"
            f"💵 قیمت: **${price:,.2f}**\n"
            f"{emoji} تغییر ۲۴ ساعت: **{change:+.2f}%**\n"
            f"📈 بالاترین ۲۴س: ${high:,.2f}\n"
            f"📉 پایین‌ترین ۲۴س: ${low:,.2f}\n\n"
            f"_منبع: Binance_"
        )
        
        await msg.edit_text(text, parse_mode="Markdown")
        
    except Exception as e:
        await msg.edit_text("❌ خطا در دریافت قیمت. لطفاً چند ثانیه بعد دوباره امتحان کنید.")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "btc":
        # شبیه‌سازی دستور /btc
        fake_update = Update(update.update_id, message=query.message)
        await btc(fake_update, context)

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("btc", btc))
    app.add_handler(CommandHandler("price", btc))  # دستور جایگزین
    from telegram.ext import CallbackQueryHandler
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("ربات در حال اجرا است...")
    app.run_polling()

if __name__ == "__main__":
    main()