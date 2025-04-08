import logging
import os # Thêm thư viện os để đọc biến môi trường
from dotenv import load_dotenv # Thêm thư viện python-dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)

# Tải biến môi trường từ file .env (nếu có, hữu ích khi chạy local)
# Trên dịch vụ online như Render, biến môi trường sẽ được set qua giao diện web
load_dotenv()

# --- CẤU HÌNH ---
# Lấy token từ biến môi trường 'TELEGRAM_BOT_TOKEN'
# TUYỆT ĐỐI KHÔNG VIẾT TOKEN TRỰC TIẾP VÀO ĐÂY KHI ĐƯA LÊN GITHUB
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Kiểm tra xem token có tồn tại không
if TELEGRAM_BOT_TOKEN is None:
    # Ghi log lỗi và thoát nếu không tìm thấy token
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    logger.error("FATAL ERROR: TELEGRAM_BOT_TOKEN không được tìm thấy trong biến môi trường.")
    exit("Thoát chương trình do thiếu TELEGRAM_BOT_TOKEN.") # Dừng bot nếu không có token


# Bật logging để theo dõi hoạt động và lỗi (sau khi chắc chắn có token)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- DỮ LIỆU SẢN PHẨM (Ví dụ đơn giản) ---
# Trong ứng dụng thực tế, bạn có thể lấy dữ liệu này từ database hoặc file
# Hoặc thay bằng danh sách tài khoản Netflix, Spotify... như bạn muốn
PRODUCTS = {
    'SP001': {'name': 'Áo Thun Trơn', 'price': 150000, 'description': 'Áo thun cotton thoáng mát.'},
    'SP002': {'name': 'Quần Jeans Rách', 'price': 350000, 'description': 'Quần jeans phong cách.'},
    'SP003': {'name': 'Nón Lưỡi Trai', 'price': 100000, 'description': 'Nón che nắng tiện lợi.'},
    # Bạn có thể thay đổi danh sách này thành các tài khoản
    # 'NF_1M': {'name': 'Tài khoản Netflix Premium 1 tháng', 'price': 50000, 'description': 'Xem phim chất lượng cao, dùng 1 tháng.'},
    # 'SP_3M': {'name': 'Tài khoản Spotify Premium 3 tháng', 'price': 90000, 'description': 'Nghe nhạc không quảng cáo, 3 tháng.'},
}

# --- CÁC HÀM XỬ LÝ LỆNH ---

# Hàm xử lý lệnh /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gửi tin nhắn chào mừng khi người dùng gõ /start."""
    user = update.effective_user
    welcome_message = (
        f"Xin chào {user.mention_html()}!\n\n"
        "Tôi là bot bán hàng. Bạn có thể dùng các lệnh sau:\n"
        "/products - Xem danh sách sản phẩm/tài khoản\n"
        "/help - Xem lại trợ giúp này"
    )
    await update.message.reply_html(welcome_message)

# Hàm xử lý lệnh /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gửi lại tin nhắn trợ giúp."""
    help_text = (
        "Bạn có thể sử dụng các lệnh sau:\n"
        "/start - Bắt đầu lại cuộc trò chuyện\n"
        "/products - Xem danh sách sản phẩm/tài khoản\n"
        "/help - Xem lại trợ giúp này"
    )
    await update.message.reply_text(help_text)

# Hàm xử lý lệnh /products
async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Hiển thị danh sách sản phẩm với các nút bấm."""
    # Sử dụng PRODUCTS hay ACCOUNTS_FOR_SALE tùy vào bạn định nghĩa ở trên
    items_to_show = PRODUCTS 
    if not items_to_show:
        await update.message.reply_text("Xin lỗi, hiện tại cửa hàng chưa có mặt hàng nào.")
        return

    keyboard = []
    for item_id, item_info in items_to_show.items():
        # Tạo một nút bấm cho mỗi mặt hàng
        button = InlineKeyboardButton(
            f"{item_info['name']} - {item_info['price']:,} VND", # Định dạng giá tiền
            callback_data=f"product_{item_id}" # Dữ liệu gửi đi khi nút được bấm
        )
        keyboard.append([button]) # Mỗi nút nằm trên một hàng

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Dưới đây là danh sách của chúng tôi:', reply_markup=reply_markup)

# Hàm xử lý khi người dùng bấm vào nút sản phẩm (Inline Keyboard Button)
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Xử lý dữ liệu từ các nút bấm inline."""
    query = update.callback_query
    await query.answer() # Bắt buộc phải gọi answer()

    callback_data = query.data
    logger.info(f"Nhận được callback data: {callback_data}")
    
    # Sử dụng PRODUCTS hay ACCOUNTS_FOR_SALE tùy vào bạn định nghĩa ở trên
    items_to_show = PRODUCTS 

    # Kiểm tra xem callback data có phải là xem chi tiết sản phẩm không
    if callback_data.startswith("product_"):
        item_id = callback_data.split("_")[1] # Lấy mã mặt hàng
        item = items_to_show.get(item_id)

        if item:
            # Hiển thị chi tiết mặt hàng
            detail_text = (
                f"*{item['name']}*\n\n"
                f"{item['description']}\n\n"
                f"Giá: *{item['price']:,} VND*"
            )
            # Logic nút bấm tiếp theo (ví dụ: Mua ngay, Thêm vào giỏ)
            # Nếu bán tài khoản, nút có thể là "Mua ngay"
            keyboard = [[InlineKeyboardButton("Mua ngay (Coming soon)", callback_data=f"buy_{item_id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            try:
                # Thử chỉnh sửa tin nhắn gốc
                await query.edit_message_text(text=detail_text, reply_markup=reply_markup, parse_mode='Markdown')
            except Exception as e:
                # Nếu không edit được (ví dụ tin nhắn quá cũ), gửi tin mới
                logger.warning(f"Không thể edit tin nhắn: {e}. Gửi tin nhắn mới.")
                await query.message.reply_markdown(detail_text, reply_markup=reply_markup)

        else:
            await query.edit_message_text(text="Xin lỗi, không tìm thấy mặt hàng này.")

    elif callback_data.startswith("buy_"):
        item_id = callback_data.split("_")[1]
        # Logic xử lý mua hàng (lấy thông tin, thanh toán, gửi tài khoản...)
        # Sẽ được thêm ở đây trong tương lai
        await query.message.reply_text(f"Chức năng mua {item_id} đang được phát triển!")


# Hàm xử lý các tin nhắn văn bản thông thường (không phải lệnh)
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Phản hồi lại tin nhắn của người dùng (ví dụ)."""
    # Bạn có thể thêm logic xử lý hội thoại tự nhiên ở đây nếu muốn
    await update.message.reply_text("Cảm ơn bạn đã nhắn tin! Dùng lệnh /products để xem mặt hàng hoặc /help.")


# --- Hàm Main để chạy Bot ---
def main() -> None:
    """Khởi động bot và lắng nghe các cập nhật."""
    logger.info("Đang khởi tạo Application...")
    # Tạo Application với token đã đọc từ biến môi trường
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Đăng ký các handler cho các lệnh
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("products", show_products))

    # Đăng ký handler cho các callback query từ nút bấm inline
    application.add_handler(CallbackQueryHandler(button_callback))

    # Đăng ký handler cho các tin nhắn văn bản thông thường (để ở cuối cùng)
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo)) # Tạm thời tắt echo để tránh spam

    # Bắt đầu chạy bot (sử dụng polling)
    logger.info("Bot chuẩn bị chạy polling...")
    application.run_polling()
    logger.info("Bot đã dừng.") # Dòng này thường chỉ xuất hiện khi bot dừng hẳn


if __name__ == '__main__':
    main()
