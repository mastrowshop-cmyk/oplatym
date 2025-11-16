import logging
import asyncio
from telegram import Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from datetime import datetime, timedelta
import json
import os

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (получите у @BotFather)
BOT_TOKEN = "8420895702:AAE54hLFxjNyWyP7MkW1StwCoHEqXJEFOZY"

# Главный администратор
MAIN_ADMIN_ID = 7668402802

# Белый список аккаунтов (не блокировать)
WHITELIST_IDS = {
    5314493557, 7279244310, 7754541004, 8444260034, 
    7840997504, 8185132005, 6962444738, 7431538558
}

# Белый список чатов
ALLOWED_CHATS = {2136717768, 4974965215}

# Администраторы бота
ADMIN_IDS = {MAIN_ADMIN_ID}

# Игнор-лист пользователей
IGNORED_USERS = set()

# Чат для логов
LOG_CHAT_ID = 4974965215

# Файлы для хранения данных
DATA_FILE = "bot_data.json"
EXAMPLE_DATA_FILE = "bot_data.example.json"

# Создание файла данных если не существует
def create_data_file_if_not_exists():
    if not os.path.exists(DATA_FILE):
        initial_data = {
            'whitelist_ids': list(WHITELIST_IDS),
            'allowed_chats': list(ALLOWED_CHATS),
            'admin_ids': list(ADMIN_IDS),
            'ignored_users': list(IGNORED_USERS)
        }
        save_data(initial_data, DATA_FILE)
        logger.info("✅ Создан новый файл данных bot_data.json")

# Создание примера файла данных
def create_example_data_file():
    example_data = {
        'whitelist_ids': [5314493557, 7279244310, 7754541004, 8444260034, 7840997504, 8185132005, 6962444738, 7431538558],
        'allowed_chats': [2136717768, 4974965215],
        'admin_ids': [7668402802],
        'ignored_users': []
    }
    save_data(example_data, EXAMPLE_DATA_FILE)
    logger.info("✅ Создан файл примера bot_data.example.json")

# Загрузка данных
def load_data():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
    return {}

# Сохранение данных
def save_data(data, filename=DATA_FILE):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения данных: {e}")

# Инициализация данных
def init_data():
    data = load_data()
    global WHITELIST_IDS, ALLOWED_CHATS, ADMIN_IDS, IGNORED_USERS
    
    WHITELIST_IDS = set(data.get('whitelist_ids', WHITELIST_IDS))
    ALLOWED_CHATS = set(data.get('allowed_chats', ALLOWED_CHATS))
    ADMIN_IDS = set(data.get('admin_ids', ADMIN_IDS))
    IGNORED_USERS = set(data.get('ignored_users', IGNORED_USERS))

# Сохранение всех данных
def save_all_data():
    data = {
        'whitelist_ids': list(WHITELIST_IDS),
        'allowed_chats': list(ALLOWED_CHATS),
        'admin_ids': list(ADMIN_IDS),
        'ignored_users': list(IGNORED_USERS)
    }
    save_data(data)

# Проверка разрешенного чата
async def is_allowed_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat_id = update.effective_chat.id
    if chat_id not in ALLOWED_CHATS and chat_id not in ADMIN_IDS:
        if update.message and update.message.chat.type != 'private':
            response = await update.message.reply_text("🚫 Бот работает только в чатах компании Oplatym.ru")
            await asyncio.sleep(10)
            try:
                await response.delete()
                await update.message.delete()
            except:
                pass
        return False
    return True

# Проверка прав администратора бота
def is_bot_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# Функция для отправки логов
async def send_log(context: ContextTypes.DEFAULT_TYPE, message: str):
    try:
        await context.bot.send_message(
            chat_id=LOG_CHAT_ID,
            text=f"📊 {message}"
        )
    except Exception as e:
        logger.error(f"Ошибка отправки лога: {e}")

# Функция для отправки сообщения с автоудалением
async def send_message_with_auto_delete(context: ContextTypes.DEFAULT_TYPE, chat_id: int, text: str, parse_mode=None, reply_markup=None):
    try:
        message = await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
        
        # Планируем удаление через 10 минут только в группах
        if chat_id not in ADMIN_IDS:
            context.job_queue.run_once(
                delete_system_message, 
                600,
                data={'chat_id': chat_id, 'message_id': message.message_id},
                name=f"delete_system_{message.message_id}"
            )
        
        return message
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        return None

# Функция для удаления системных сообщений
async def delete_system_message(context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_id = context.job.data['chat_id']
        message_id = context.job.data['message_id']
        
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"Системное сообщение {message_id} удалено из чата {chat_id}")
        
    except Exception as e:
        logger.error(f"Ошибка при удалении системного сообщения: {e}")

# АДМИН ПАНЕЛЬ - Главное меню
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_bot_admin(update.effective_user.id):
        await update.message.reply_text("❌ У вас нет прав доступа к админ панели")
        return
    
    keyboard = [
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("👥 Управление пользователями", callback_data="admin_users")],
        [InlineKeyboardButton("💬 Управление чатами", callback_data="admin_chats")],
        [InlineKeyboardButton("🛡️ Управление администраторами", callback_data="admin_admins")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🛠️ **Панель администратора Oplatym.ru**\n\n"
        "Выберите раздел для управления:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Обработчик callback запросов админ панели
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_bot_admin(user_id):
        await query.edit_message_text("❌ У вас нет прав доступа")
        return
    
    data = query.data
    
    if data == "admin_broadcast":
        await show_broadcast_menu(query, context)
    elif data == "admin_users":
        await show_users_menu(query, context)
    elif data == "admin_chats":
        await show_chats_menu(query, context)
    elif data == "admin_admins":
        await show_admins_menu(query, context)
    elif data == "admin_stats":
        await show_stats(query, context)
    elif data == "admin_back":
        await admin_panel_back(query, context)
    elif data.startswith("broadcast_"):
        await handle_broadcast(query, context, data)
    elif data.startswith("user_"):
        await handle_user_management(query, context, data)
    elif data.startswith("chat_"):
        await handle_chat_management(query, context, data)
    elif data.startswith("admin_"):
        await handle_admin_management(query, context, data)

# Меню рассылки
async def show_broadcast_menu(query, context):
    keyboard = [
        [InlineKeyboardButton("📢 Рассылка во все чаты", callback_data="broadcast_all")],
        [InlineKeyboardButton("📱 Рассылка в ЛС", callback_data="broadcast_pm")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📢 **Управление рассылкой**\n\n"
        "Выберите тип рассылки:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Меню пользователей
async def show_users_menu(query, context):
    ignored_count = len(IGNORED_USERS)
    whitelist_count = len(WHITELIST_IDS)
    
    keyboard = [
        [InlineKeyboardButton("🚫 Игнор-лист", callback_data="user_ignore")],
        [InlineKeyboardButton("✅ Белый список", callback_data="user_whitelist")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"👥 **Управление пользователями**\n\n"
        f"🚫 В игнор-листе: {ignored_count} пользователей\n"
        f"✅ В белом списке: {whitelist_count} пользователей\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Меню чатов
async def show_chats_menu(query, context):
    chats_count = len(ALLOWED_CHATS)
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить чат", callback_data="chat_add")],
        [InlineKeyboardButton("🗑️ Удалить чат", callback_data="chat_remove")],
        [InlineKeyboardButton("📋 Список чатов", callback_data="chat_list")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"💬 **Управление чатами**\n\n"
        f"📊 Разрешенных чатов: {chats_count}\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Меню администраторов
async def show_admins_menu(query, context):
    admins_count = len(ADMIN_IDS)
    
    keyboard = [
        [InlineKeyboardButton("➕ Добавить админа", callback_data="admin_add")],
        [InlineKeyboardButton("🗑️ Удалить админа", callback_data="admin_remove")],
        [InlineKeyboardButton("📋 Список админов", callback_data="admin_list")],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="admin_back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🛡️ **Управление администраторами**\n\n"
        f"👑 Администраторов: {admins_count}\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Статистика
async def show_stats(query, context):
    stats_text = (
        f"📊 **Статистика бота**\n\n"
        f"💬 Разрешенных чатов: {len(ALLOWED_CHATS)}\n"
        f"👥 Пользователей в белом списке: {len(WHITELIST_IDS)}\n"
        f"🚫 Пользователей в игнор-листе: {len(IGNORED_USERS)}\n"
        f"👑 Администраторов: {len(ADMIN_IDS)}\n\n"
        f"🕒 Бот запущен: {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    
    keyboard = [[InlineKeyboardButton("🔄 Обновить", callback_data="admin_stats")],
                [InlineKeyboardButton("🏠 Главное меню", callback_data="admin_back")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(stats_text, reply_markup=reply_markup, parse_mode='Markdown')

# Назад в главное меню
async def admin_panel_back(query, context):
    await admin_panel(update=Update(update_id=query.update_id, message=query.message), context=context)

# Обработка рассылки
async def handle_broadcast(query, context, data):
    if data == "broadcast_all":
        context.user_data['awaiting_broadcast'] = 'all'
        await query.edit_message_text(
            "📢 **Рассылка во все чаты**\n\n"
            "Отправьте сообщение для рассылки во все разрешенные чаты:",
            parse_mode='Markdown'
        )
    elif data == "broadcast_pm":
        context.user_data['awaiting_broadcast'] = 'pm'
        await query.edit_message_text(
            "📱 **Рассылка в личные сообщения**\n\n"
            "Отправьте сообщение для рассылки всем пользователям из белого списка:",
            parse_mode='Markdown'
        )

# Обработка управления пользователями
async def handle_user_management(query, context, data):
    if data == "user_ignore":
        await show_ignore_management(query, context)
    elif data == "user_whitelist":
        await show_whitelist_management(query, context)

# Показать управление игнор-листом
async def show_ignore_management(query, context):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить в игнор", callback_data="user_ignore_add")],
        [InlineKeyboardButton("🗑️ Удалить из игнора", callback_data="user_ignore_remove")],
        [InlineKeyboardButton("📋 Список игнора", callback_data="user_ignore_list")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"🚫 **Управление игнор-листом**\n\n"
        f"Пользователей в игноре: {len(IGNORED_USERS)}\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Показать управление белым списком
async def show_whitelist_management(query, context):
    keyboard = [
        [InlineKeyboardButton("➕ Добавить в белый список", callback_data="user_whitelist_add")],
        [InlineKeyboardButton("🗑️ Удалить из белого списка", callback_data="user_whitelist_remove")],
        [InlineKeyboardButton("📋 Белый список", callback_data="user_whitelist_list")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_users")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        f"✅ **Управление белым списком**\n\n"
        f"Пользователей в белом списке: {len(WHITELIST_IDS)}\n\n"
        f"Выберите действие:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Обработка управления чатами
async def handle_chat_management(query, context, data):
    if data == "chat_add":
        context.user_data['awaiting_chat_add'] = True
        await query.edit_message_text(
            "➕ **Добавление чата**\n\n"
            "Перешлите любое сообщение из чата который хотите добавить, "
            "или отправьте ID чата (число, можно получить через /id в нужном чате):",
            parse_mode='Markdown'
        )
    elif data == "chat_remove":
        await show_chat_remove_menu(query, context)
    elif data == "chat_list":
        await show_chat_list(query, context)

# Обработка управления администраторами
async def handle_admin_management(query, context, data):
    if data == "admin_add":
        context.user_data['awaiting_admin_add'] = True
        await query.edit_message_text(
            "➕ **Добавление администратора**\n\n"
            "Перешлите сообщение пользователя или отправьте его ID:",
            parse_mode='Markdown'
        )
    elif data == "admin_remove":
        await show_admin_remove_menu(query, context)
    elif data == "admin_list":
        await show_admin_list(query, context)

# Показать список чатов для удаления
async def show_chat_remove_menu(query, context):
    if not ALLOWED_CHATS:
        await query.edit_message_text("❌ Нет добавленных чатов")
        return
    
    keyboard = []
    for chat_id in ALLOWED_CHATS:
        try:
            chat = await context.bot.get_chat(chat_id)
            chat_name = chat.title or "Личные сообщения"
            keyboard.append([InlineKeyboardButton(f"🗑️ {chat_name}", callback_data=f"chat_remove_{chat_id}")])
        except:
            keyboard.append([InlineKeyboardButton(f"🗑️ Чат {chat_id}", callback_data=f"chat_remove_{chat_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_chats")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🗑️ **Удаление чата**\n\n"
        "Выберите чат для удаления:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Показать список администраторов для удаления
async def show_admin_remove_menu(query, context):
    if len(ADMIN_IDS) <= 1:
        await query.edit_message_text("❌ Нельзя удалить единственного администратора")
        return
    
    keyboard = []
    for admin_id in ADMIN_IDS:
        if admin_id == MAIN_ADMIN_ID:
            continue
        try:
            user = await context.bot.get_chat(admin_id)
            user_name = user.first_name or "Пользователь"
            keyboard.append([InlineKeyboardButton(f"🗑️ {user_name}", callback_data=f"admin_remove_{admin_id}")])
        except:
            keyboard.append([InlineKeyboardButton(f"🗑️ ID {admin_id}", callback_data=f"admin_remove_{admin_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="admin_admins")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🗑️ **Удаление администратора**\n\n"
        "Выберите администратора для удаления:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Показать список чатов
async def show_chat_list(query, context):
    if not ALLOWED_CHATS:
        await query.edit_message_text("❌ Нет добавленных чатов")
        return
    
    chats_text = "📋 **Список разрешенных чатов:**\n\n"
    for i, chat_id in enumerate(ALLOWED_CHATS, 1):
        try:
            chat = await context.bot.get_chat(chat_id)
            chat_name = chat.title or "Личные сообщения"
            chats_text += f"{i}. {chat_name} (ID: `{chat_id}`)\n"
        except:
            chats_text += f"{i}. Чат {chat_id}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_chats")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(chats_text, reply_markup=reply_markup, parse_mode='Markdown')

# Показать список администраторов
async def show_admin_list(query, context):
    admins_text = "👑 **Список администраторов:**\n\n"
    for i, admin_id in enumerate(ADMIN_IDS, 1):
        try:
            user = await context.bot.get_chat(admin_id)
            user_name = user.first_name or "Пользователь"
            status = "👑 Главный" if admin_id == MAIN_ADMIN_ID else "🛡️ Админ"
            admins_text += f"{i}. {user_name} {status} (ID: `{admin_id}`)\n"
        except:
            admins_text += f"{i}. Пользователь {admin_id}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="admin_admins")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(admins_text, reply_markup=reply_markup, parse_mode='Markdown')

# Обработка текстовых сообщений для админ панели
async def handle_admin_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_bot_admin(update.effective_user.id):
        return
    
    user_data = context.user_data
    
    # Обработка рассылки
    if 'awaiting_broadcast' in user_data:
        broadcast_type = user_data['awaiting_broadcast']
        del user_data['awaiting_broadcast']
        
        message_text = update.message.text
        success_count = 0
        total_count = 0
        
        if broadcast_type == 'all':
            targets = ALLOWED_CHATS
            target_name = "чаты"
        else:  # broadcast_type == 'pm'
            targets = WHITELIST_IDS
            target_name = "пользователи"
        
        total_count = len(targets)
        
        await update.message.reply_text(f"🔄 Начинаю рассылку для {total_count} {target_name}...")
        
        for target_id in targets:
            try:
                await context.bot.send_message(chat_id=target_id, text=message_text)
                success_count += 1
                await asyncio.sleep(0.1)  # Задержка чтобы не превысить лимиты
            except Exception as e:
                logger.error(f"Ошибка рассылки для {target_id}: {e}")
        
        await update.message.reply_text(
            f"✅ Рассылка завершена!\n"
            f"📤 Успешно: {success_count}/{total_count}"
        )
        return
    
    # Обработка добавления чата
    if 'awaiting_chat_add' in user_data:
        del user_data['awaiting_chat_add']
        
        if update.message.forward_from_chat:
            chat_id = update.message.forward_from_chat.id
        else:
            try:
                chat_id = int(update.message.text)
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID чата")
                return
        
        try:
            chat = await context.bot.get_chat(chat_id)
            ALLOWED_CHATS.add(chat_id)
            save_all_data()
            
            await update.message.reply_text(
                f"✅ Чат \"{chat.title}\" (ID: {chat_id}) добавлен в белый список"
            )
            await send_log(context, f"Админ {update.message.from_user.first_name} добавил чат {chat.title} ({chat_id})")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка добавления чата: {e}")
        return
    
    # Обработка добавления администратора
    if 'awaiting_admin_add' in user_data:
        del user_data['awaiting_admin_add']
        
        if update.message.forward_from:
            user_id = update.message.forward_from.id
        else:
            try:
                user_id = int(update.message.text)
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID пользователя")
                return
        
        try:
            user = await context.bot.get_chat(user_id)
            ADMIN_IDS.add(user_id)
            save_all_data()
            
            await update.message.reply_text(
                f"✅ Пользователь {user.first_name} (ID: {user_id}) добавлен как администратор"
            )
            await send_log(context, f"Админ {update.message.from_user.first_name} добавил администратора {user.first_name} ({user_id})")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка добавления администратора: {e}")
        return

# Обработка callback для удаления чатов и администраторов
async def handle_remove_callback(query, context, data):
    if data.startswith("chat_remove_"):
        chat_id = int(data.split('_')[2])
        
        try:
            chat = await context.bot.get_chat(chat_id)
            chat_name = chat.title
        except:
            chat_name = f"чат {chat_id}"
        
        ALLOWED_CHATS.discard(chat_id)
        save_all_data()
        
        await query.edit_message_text(f"✅ Чат \"{chat_name}\" удален из белого списка")
        await send_log(context, f"Админ {query.from_user.first_name} удалил чат {chat_name} ({chat_id})")
        
    elif data.startswith("admin_remove_"):
        admin_id = int(data.split('_')[2])
        
        if admin_id == MAIN_ADMIN_ID:
            await query.answer("❌ Нельзя удалить главного администратора", show_alert=True)
            return
        
        try:
            user = await context.bot.get_chat(admin_id)
            user_name = user.first_name
        except:
            user_name = f"пользователь {admin_id}"
        
        ADMIN_IDS.discard(admin_id)
        save_all_data()
        
        await query.edit_message_text(f"✅ Администратор {user_name} удален")
        await send_log(context, f"Админ {query.from_user.first_name} удалил администратора {user_name} ({admin_id})")

# Обработка callback для пользователей
async def handle_user_callback(query, context, data):
    if data == "user_ignore_add":
        context.user_data['awaiting_ignore_add'] = True
        await query.edit_message_text(
            "🚫 **Добавление в игнор-лист**\n\n"
            "Перешлите сообщение пользователя или отправьте его ID:",
            parse_mode='Markdown'
        )
    elif data == "user_ignore_remove":
        await show_ignore_remove_menu(query, context)
    elif data == "user_ignore_list":
        await show_ignore_list(query, context)
    elif data == "user_whitelist_add":
        context.user_data['awaiting_whitelist_add'] = True
        await query.edit_message_text(
            "✅ **Добавление в белый список**\n\n"
            "Перешлите сообщение пользователя или отправьте его ID:",
            parse_mode='Markdown'
        )
    elif data == "user_whitelist_remove":
        await show_whitelist_remove_menu(query, context)
    elif data == "user_whitelist_list":
        await show_whitelist_list(query, context)
    elif data.startswith("ignore_remove_"):
        await handle_ignore_remove(query, context, data)
    elif data.startswith("whitelist_remove_"):
        await handle_whitelist_remove(query, context, data)

# Показать меню удаления из игнора
async def show_ignore_remove_menu(query, context):
    if not IGNORED_USERS:
        await query.edit_message_text("❌ Игнор-лист пуст")
        return
    
    keyboard = []
    for user_id in IGNORED_USERS:
        try:
            user = await context.bot.get_chat(user_id)
            user_name = user.first_name or "Пользователь"
            keyboard.append([InlineKeyboardButton(f"✅ {user_name}", callback_data=f"ignore_remove_{user_id}")])
        except:
            keyboard.append([InlineKeyboardButton(f"✅ ID {user_id}", callback_data=f"ignore_remove_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="user_ignore")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "✅ **Удаление из игнор-листа**\n\n"
        "Выберите пользователя для удаления:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Показать меню удаления из белого списка
async def show_whitelist_remove_menu(query, context):
    if not WHITELIST_IDS:
        await query.edit_message_text("❌ Белый список пуст")
        return
    
    keyboard = []
    for user_id in WHITELIST_IDS:
        try:
            user = await context.bot.get_chat(user_id)
            user_name = user.first_name or "Пользователь"
            keyboard.append([InlineKeyboardButton(f"🗑️ {user_name}", callback_data=f"whitelist_remove_{user_id}")])
        except:
            keyboard.append([InlineKeyboardButton(f"🗑️ ID {user_id}", callback_data=f"whitelist_remove_{user_id}")])
    
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="user_whitelist")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🗑️ **Удаление из белого списка**\n\n"
        "Выберите пользователя для удаления:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# Показать список игнора
async def show_ignore_list(query, context):
    if not IGNORED_USERS:
        await query.edit_message_text("❌ Игнор-лист пуст")
        return
    
    ignore_text = "🚫 **Список игнор-листа:**\n\n"
    for i, user_id in enumerate(IGNORED_USERS, 1):
        try:
            user = await context.bot.get_chat(user_id)
            user_name = user.first_name or "Пользователь"
            ignore_text += f"{i}. {user_name} (ID: `{user_id}`)\n"
        except:
            ignore_text += f"{i}. Пользователь {user_id}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="user_ignore")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(ignore_text, reply_markup=reply_markup, parse_mode='Markdown')

# Показать белый список
async def show_whitelist_list(query, context):
    if not WHITELIST_IDS:
        await query.edit_message_text("❌ Белый список пуст")
        return
    
    whitelist_text = "✅ **Белый список пользователей:**\n\n"
    for i, user_id in enumerate(WHITELIST_IDS, 1):
        try:
            user = await context.bot.get_chat(user_id)
            user_name = user.first_name or "Пользователь"
            whitelist_text += f"{i}. {user_name} (ID: `{user_id}`)\n"
        except:
            whitelist_text += f"{i}. Пользователь {user_id}\n"
    
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="user_whitelist")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(whitelist_text, reply_markup=reply_markup, parse_mode='Markdown')

# Удалить из игнора
async def handle_ignore_remove(query, context, data):
    user_id = int(data.split('_')[2])
    
    try:
        user = await context.bot.get_chat(user_id)
        user_name = user.first_name
    except:
        user_name = f"пользователь {user_id}"
    
    IGNORED_USERS.discard(user_id)
    save_all_data()
    
    await query.edit_message_text(f"✅ Пользователь {user_name} удален из игнор-листа")
    await send_log(context, f"Админ {query.from_user.first_name} удалил из игнора {user_name} ({user_id})")

# Удалить из белого списка
async def handle_whitelist_remove(query, context, data):
    user_id = int(data.split('_')[2])
    
    try:
        user = await context.bot.get_chat(user_id)
        user_name = user.first_name
    except:
        user_name = f"пользователь {user_id}"
    
    WHITELIST_IDS.discard(user_id)
    save_all_data()
    
    await query.edit_message_text(f"✅ Пользователь {user_name} удален из белого списка")
    await send_log(context, f"Админ {query.from_user.first_name} удалил из белого списка {user_name} ({user_id})")

# Обработка текстовых сообщений для управления пользователями
async def handle_user_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_bot_admin(update.effective_user.id):
        return
    
    user_data = context.user_data
    
    # Добавление в игнор
    if 'awaiting_ignore_add' in user_data:
        del user_data['awaiting_ignore_add']
        
        if update.message.forward_from:
            user_id = update.message.forward_from.id
        else:
            try:
                user_id = int(update.message.text)
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID пользователя")
                return
        
        try:
            user = await context.bot.get_chat(user_id)
            IGNORED_USERS.add(user_id)
            save_all_data()
            
            await update.message.reply_text(
                f"🚫 Пользователь {user.first_name} (ID: {user_id}) добавлен в игнор-лист"
            )
            await send_log(context, f"Админ {update.message.from_user.first_name} добавил в игнор {user.first_name} ({user_id})")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка добавления в игнор: {e}")
        return
    
    # Добавление в белый список
    if 'awaiting_whitelist_add' in user_data:
        del user_data['awaiting_whitelist_add']
        
        if update.message.forward_from:
            user_id = update.message.forward_from.id
        else:
            try:
                user_id = int(update.message.text)
            except ValueError:
                await update.message.reply_text("❌ Неверный формат ID пользователя")
                return
        
        try:
            user = await context.bot.get_chat(user_id)
            WHITELIST_IDS.add(user_id)
            save_all_data()
            
            await update.message.reply_text(
                f"✅ Пользователь {user.first_name} (ID: {user_id}) добавлен в белый список"
            )
            await send_log(context, f"Админ {update.message.from_user.first_name} добавил в белый список {user.first_name} ({user_id})")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка добавления в белый список: {e}")
        return

# Обновленный обработчик callback
async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if not is_bot_admin(user_id):
        await query.edit_message_text("❌ У вас нет прав доступа")
        return
    
    data = query.data
    
    if data == "admin_broadcast":
        await show_broadcast_menu(query, context)
    elif data == "admin_users":
        await show_users_menu(query, context)
    elif data == "admin_chats":
        await show_chats_menu(query, context)
    elif data == "admin_admins":
        await show_admins_menu(query, context)
    elif data == "admin_stats":
        await show_stats(query, context)
    elif data == "admin_back":
        await admin_panel_back(query, context)
    elif data.startswith("broadcast_"):
        await handle_broadcast(query, context, data)
    elif data.startswith("user_"):
        await handle_user_callback(query, context, data)
    elif data.startswith("chat_"):
        await handle_chat_management(query, context, data)
    elif data.startswith("admin_"):
        if data.startswith("admin_remove_"):
            await handle_remove_callback(query, context, data)
        else:
            await handle_admin_management(query, context, data)
    elif data.startswith("ignore_") or data.startswith("whitelist_"):
        await handle_user_callback(query, context, data)

# Команда для админ панели
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat.type != 'private':
        await update.message.reply_text("🛠️ Админ панель доступна только в личных сообщениях с ботом")
        return
    
    await admin_panel(update, context)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_allowed_chat(update, context):
        return
    
    await send_log(context, f"Команда /start от {update.message.from_user.first_name} в чате {update.message.chat_id}")
    
    if is_bot_admin(update.effective_user.id):
        # Для администраторов показываем расширенное меню
        keyboard = [
            [InlineKeyboardButton("🛠️ Админ панель", callback_data="admin_panel")],
            [InlineKeyboardButton("📋 Команды бота", callback_data="bot_commands")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 Я бот-модератор Oplatym.ru!\n\n"
            "Выберите действие:",
            reply_markup=reply_markup
        )
    else:
        await send_message_with_auto_delete(
            context,
            update.message.chat_id,
            "🤖 Я бот-модератор Oplatym.ru!\n\n"
            "🛠 **Основные команды:**\n"
            "/help - помощь по командам\n"
            "/rules - правила чата\n\n"
            "💡 Бот автоматически модерирует чат и помогает с безопасностью.",
            parse_mode='HTML'
        )

# Основная функция
def main():
    # Создание файлов данных при первом запуске
    create_data_file_if_not_exists()
    create_example_data_file()
    
    # Инициализация данных
    init_data()
    
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчики админ панели
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^broadcast_"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^user_"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^chat_"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^ignore_"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^whitelist_"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_panel"))
    application.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^bot_commands"))
    
    # Обработчики текстовых сообщений для админ панели
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, 
        handle_admin_text
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & ~filters.COMMAND, 
        handle_user_text
    ))

    # [ЗДЕСЬ ДОЛЖНЫ БЫТЬ ВСЕ ОСТАЛЬНЫЕ ОБРАБОТЧИКИ ИЗ ПРЕДЫДУЩЕГО КОДА]

    # Запуск бота
    print("🟢 Бот Oplatym.ru запущен с админ панелью!")
    print("👑 Главный администратор:", MAIN_ADMIN_ID)
    print("💬 Разрешенные чаты:", ALLOWED_CHATS)
    print("📁 Созданы файлы: bot_data.json и bot_data.example.json")
    application.run_polling()

if __name__ == "__main__":
    main()


