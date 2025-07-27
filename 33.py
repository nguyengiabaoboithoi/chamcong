import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup  
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from datetime import datetime
import pandas as pd
import asyncio
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

BOIVN = os.getenv('boivn')

# Google Sheets Setup
SHEET_ID = '1jQ1mT3kSgJZU62g0BZgaObtXWV522f7bFU5LxmLCtNA'  # ID của Google Sheets bạn muốn lưu
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
CREDENTIALS_FILE = 'credentials.json'  # Đường dẫn đến tệp credentials.json

# Hàm để xác thực và kết nối với Google Sheets API
def authenticate_google_sheets():
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID)

# Hàm ghi dữ liệu vào Google Sheets
def write_attendance_to_google_sheets(user_id, username, action):
    # Kết nối đến Google Sheets
    sheet = authenticate_google_sheets().sheet1  # Mặc định là sheet1
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    date = datetime.now().strftime('%Y-%m-%d')
    
    # Dữ liệu cần ghi
    data = [date, username, action, now]
    
    # Thêm dữ liệu vào sheet
    sheet.append_row(data)

# Hàm gửi nhắc nhở sau một khoảng thời gian
async def send_reminder(context: ContextTypes.DEFAULT_TYPE, chat_id, message_id, action, user_id):
    await context.bot.send_message(
        chat_id=chat_id,
        text=f'⏰ Đã hết thời gian  | 时间已到    <b>{action}</b> !\n\n'
             f'❌ <b>@{user.username}</b> Vui lòng nhanh chóng trở lại vị trí làm việc của bạn.</b>❌',
        reply_to_message_id=message_id,
        parse_mode='HTML'
    )

# Hàm xử lý hành động theo thời gian
async def timed_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action):
    user = update.effective_user
    full_name = user.full_name if user.full_name else user.username  # Lấy tên đầy đủ hoặc username
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
    write_attendance_to_google_sheets(user.id, user.username, action)
    await update.message.reply_text(
        f"👤 @{user.username} <b>({full_name})</b>\n\n"
        f"🔔 XIN PHÉP: <b>{action}</b>\n"
        f"⏰ Thời gian bắt đầu | <b>开始时间: {now} .</b>\n"
        f"⏳ <i>Hãy trở lại vị trí làm việc trong vòng 10 phút nhé !</i> 💼",
        parse_mode='HTML'
    )

    # Đợi 120 giây (2 phút) rồi gửi nhắc nhở
    await asyncio.sleep(120)  # Đợi 2 phút (120 giây)
    await send_reminder(context, update.effective_chat.id, update.message.message_id, action, user.id)

# Các hàm hành động khác
async def hutthuoc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await timed_action(update, context, '🚬 đi hút thuốc | 去抽烟')

async def vesinh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await timed_action(update, context, '🚻 đi vệ sinh | 去卫生间')

async def viecrieng(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await timed_action(update, context, '🚀 đi việc riêng | 去个地方')

# Hàm chấm công vào
async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    full_name = user.full_name if user.full_name else user.username  
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') 
    write_attendance_to_google_sheets(user.id, user.username, 'chấm công vào | 打卡开始')
    await update.message.reply_text(
        f"👤 @{user.username} <b>({full_name})</b>\n\n"
        f"✅ Đã chấm công vào lúc ⏰ <b>{now}</b>.\n"
        f"👨🏻‍💻 Chúc bạn một ngày làm việc hiệu quả !\n"
        f"🎉 祝你工作愉快! 💪",
        parse_mode='HTML'
    )

# Hàm chấm công ra
async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    full_name = user.full_name if user.full_name else user.username  
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
    write_attendance_to_google_sheets(user.id, user.username, 'XUỐNG CA | 下班')
    await update.message.reply_text(
        f"👤 @{user.username} <b>({full_name})</b>\n\n"
        f"🏃 Đã nghỉ ngơi lúc ⏰ <b>{now}</b> .\n\n"
        f"👋 Hẹn gặp bạn vào ngày mai nhé !\n"
        f"明天见! 👋",
        parse_mode='HTML'
    )

# Hàm trở lại vị trí
async def tro_lai_vi_tri(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    full_name = user.full_name if user.full_name else user.username  
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  
    action = "🏃‍♂️ trở lại vị trí | 返回位置"
    write_attendance_to_google_sheets(user.id, user.username, action)
    await update.message.reply_text(
        f"🤖 @{user.username} <b>({full_name})</b> đã <b>{action}</b> lúc <b>{now}</b>.\n\n"
        f"Chúc bạn làm việc hiệu quả nhé ! 😉\n"
        f"祝你工作愉快!",
        parse_mode='HTML'
    )

# Hàm xử lý các nút bấm
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "LÊN CA | 打卡开始":
        await checkin(update, context)
    elif text == "XUỐNG CA | 下班":
        await checkout(update, context)
    elif text == "ĐI HÚT THUỐC | 去抽烟":
        await hutthuoc(update, context)
    elif text == "ĐI VỆ SINH | 去卫生间":
        await vesinh(update, context)
    elif text == "ĐI VIỆC RIÊNG | 去个地方":
        await viecrieng(update, context)
    elif text == "TRỞ LẠI VỊ TRÍ | 返回位置":
        await tro_lai_vi_tri(update, context)

# Định nghĩa hàm start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Khởi tạo các nút bấm cho người dùng
    keyboard = [
        ["LÊN CA | 打卡开始", "XUỐNG CA | 下班"],
        ["ĐI HÚT THUỐC | 去抽烟", "ĐI VỆ SINH | 去卫生间", "ĐI VIỆC RIÊNG | 去个地方"],
        ["TRỞ LẠI VỊ TRÍ | 返回位置"]
    ]
    # Cấu hình giao diện bàn phím cho người dùng
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    # Gửi thông báo chào mừng và hiển thị các nút bấm
    await update.message.reply_text(
        "🤖 :   <b>Chào bạn !</b>\n"
        "<b><i>Thời gian là vàng là bạc , đừng lãng phí khi mỗi phút đều quan trọng đối với sự thành công của bạn.</i></b>",
        reply_markup=reply_markup
    )

# Hàm khởi chạy bot
def main():
    app = ApplicationBuilder().token(BOIVN).concurrent_updates=True.build() 
    app.add_handler(CommandHandler("start", start))  
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_buttons))
    print("Bot _CHAMCONG_ đang chạy...")
    app.run_polling()

if __name__ == '__main__':
    main()
