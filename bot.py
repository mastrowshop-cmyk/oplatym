import logging
from telegram import Update, ChatPermissions
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (получите у @BotFather)
BOT_TOKEN = "8417645903:AAHTr9rpoY_mjwPU9IKJ54r_KLK5RnujAJ0"

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Я бот-модератор Oplatym.ru! Доступные команды:\n\n"
        "🛠 **Команды модерации:**\n"
        "/warn - предупредить пользователя\n"
        "/mute - ограничить пользователя\n"
        "/unmute - снять ограничения\n"
        "/ban - забанить пользователя\n"
        "/unban - разбанить пользователя\n"
        "/kick - кикнуть пользователя\n"
        "/id - получить ID пользователя\n\n"
        "ℹ️ **Информационные:**\n"
        "/help - помощь по командам\n"
        "/rules - показать правила чата\n"
        "/check - проверить права бота\n\n"
        "💡 **Использование:** Ответьте на сообщение пользователя командой модерации"
    )

# Команда /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📋 **Помощь по командам:**

👮‍♂️ **Модерация (только для админов):**
• Ответьте на сообщение и используйте:
  /warn - предупредить пользователя
  /mute - ограничить на 1 час
  /unmute - снять ограничения  
  /ban - забанить пользователя
  /kick - кикнуть пользователя

• /unban ID - разбанить по ID
• /id - получить ID пользователя

🔧 **Как разбанить:**
1. Ответьте на сообщение пользователя командой /id
2. Скопируйте его ID
3. Используйте /unban ID_пользователя

ℹ️ **Информационные команды:**
/check - проверить права бота
/rules - показать правила чата

⚠️ *Только администраторы могут использовать команды модерации!*
    """
    await update.message.reply_text(help_text)

# Команда /rules
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules_text = """
📜 **Правила чата Oplatym.ru:**

1. 🚫 Запрещён спам и флуд
2. 🚫 Запрещены оскорбления и нецензурная лексика
3. 🚫 Запрещена реклама без согласования
4. 🚫 Запрещено мошенничество и обман
5. ✅ Уважайте других участников
6. ✅ Соблюдайте тематику чата
7. ✅ Ведите себя культурно

‼️ **ВНИМАНИЕ МОШЕННИКИ!**
• Мы первые не пишем!
• Будьте бдительны при общении
• Переходите только через официальные аккаунты

Нарушение правил ведёт к предупреждениям, муту или бану!
    """
    await update.message.reply_text(rules_text)

# Команда для проверки прав бота
async def check_rights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        chat_member = await context.bot.get_chat_member(update.message.chat_id, context.bot.id)
        rights_info = (
            f"🤖 **Статус бота:** {chat_member.status}\n"
            f"👑 **Права администратора:** {chat_member.status in ['administrator', 'creator']}\n"
            f"📊 **ID чата:** {update.message.chat_id}\n"
            f"💬 **Бот видит сообщения:** Да\n"
            f"✉️ **Бот может отправлять сообщения:** Да"
        )
        
        await update.message.reply_text(rights_info)
        
        # Дополнительная проверка для приветствий
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text(
                "⚠️ **ВНИМАНИЕ:** Бот не администратор!\n"
                "Приветствия и модерация могут не работать.\n"
                "Назначьте бота администратором с правами:\n"
                "• Удаление сообщений\n"
                "• Блокировка пользователей\n"
                "• Ограничение пользователей"
            )
        else:
            await update.message.reply_text("✅ Бот имеет права администратора! Все функции активны.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка проверки прав: {e}")

# Команда для получения ID пользователя
async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        user = update.message.reply_to_message.from_user
        await update.message.reply_text(
            f"👤 **Информация о пользователе:**\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"📛 **Имя:** {user.first_name}\n"
            f"🔗 **Username:** @{user.username if user.username else 'нет'}\n"
            f"👥 **Полное имя:** {user.full_name}\n\n"
            f"💡 **Для разбана используйте:** `/unban {user.id}`",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Ответьте на сообщение пользователя чтобы получить его ID!\n\n"
            "**Пример использования:**\n"
            "1. Найдите сообщение пользователя\n"
            "2. Ответьте на него командой /id\n"
            "3. Бот покажет ID пользователя"
        )

# Проверка прав администратора
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        user = await context.bot.get_chat_member(update.message.chat_id, update.message.from_user.id)
        return user.status in ['administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки прав: {e}")
        return False

# Получить пользователя из сообщения
async def get_mentioned_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.message.reply_to_message:
            return update.message.reply_to_message.from_user
        
        if context.args:
            # Пытаемся получить user_id из аргумента
            if context.args[0].isdigit():
                return int(context.args[0])
            else:
                await update.message.reply_text("❌ Для этой команды лучше ответьте на сообщение пользователя!")
                return None
        
        await update.message.reply_text("❌ Укажите пользователя или ответьте на его сообщение!")
        return None
    except Exception as e:
        logger.error(f"Ошибка получения пользователя: {e}")
        return None

# Команда /warn
async def warn_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    target_user = await get_mentioned_user(update, context)
    if not target_user:
        return
    
    if isinstance(target_user, int):
        await update.message.reply_text(f"⚠️ Пользователю ID {target_user} выдано предупреждение!")
    else:
        await update.message.reply_text(
            f"⚠️ Пользователю {target_user.mention_html()} выдано предупреждение!\n"
            f"📜 Пожалуйста, ознакомьтесь с правилами: /rules",
            parse_mode='HTML'
        )

# Команда /mute
async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    target_user = await get_mentioned_user(update, context)
    if not target_user:
        return
    
    if isinstance(target_user, int):
        await update.message.reply_text("❌ Мут можно выдать только ответом на сообщение!")
        return
    
    try:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat_id,
            user_id=target_user.id,
            permissions=permissions,
            until_date=3600  # 1 час
        )
        
        await update.message.reply_text(
            f"🔇 Пользователь {target_user.mention_html()} ограничен на 1 час!\n"
            f"⏰ Ограничение будет снято автоматически через 1 час.",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при муте: {e}")
        await update.message.reply_text("❌ Не удалось ограничить пользователя! Проверьте права бота.")

# Команда /unmute
async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    target_user = await get_mentioned_user(update, context)
    if not target_user:
        return
    
    if isinstance(target_user, int):
        await update.message.reply_text("❌ Размут можно выдать только ответом на сообщение!")
        return
    
    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat_id,
            user_id=target_user.id,
            permissions=permissions
        )
        
        await update.message.reply_text(
            f"🔊 С пользователя {target_user.mention_html()} сняты ограничения!",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при размуте: {e}")
        await update.message.reply_text("❌ Не удалось снять ограничения!")

# Команда /ban
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    target_user = await get_mentioned_user(update, context)
    if not target_user:
        return
    
    if isinstance(target_user, int):
        await update.message.reply_text("❌ Бан можно выдать только ответом на сообщение!")
        return
    
    try:
        await context.bot.ban_chat_member(
            chat_id=update.message.chat_id,
            user_id=target_user.id
        )
        
        await update.message.reply_text(
            f"🚫 Пользователь {target_user.mention_html()} забанен!",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при бане: {e}")
        await update.message.reply_text("❌ Не удалось забанить пользователя! Проверьте права бота.")

# Команда /unban - ИСПРАВЛЕННАЯ
async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите ID пользователя для разбана!\n\n"
            "📝 **Как использовать:**\n"
            "`/unban 123456789` - разбанить по ID\n\n"
            "💡 **Как получить ID?**\n"
            "Ответьте на сообщение пользователя командой `/id`"
        )
        return
    
    try:
        user_id = int(context.args[0])
        
        await context.bot.unban_chat_member(
            chat_id=update.message.chat_id,
            user_id=user_id
        )
        
        await update.message.reply_text(f"✅ Пользователь ID `{user_id}` разбанен!", parse_mode='Markdown')
        
    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат ID! Укажите числовой ID пользователя.\n"
            "Пример: `/unban 123456789`",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Ошибка при разбане: {e}")
        error_msg = str(e)
        if "user not found" in error_msg.lower():
            await update.message.reply_text("❌ Пользователь не найден или не забанен!")
        elif "not enough rights" in error_msg.lower():
            await update.message.reply_text("❌ У бота недостаточно прав для разбана!")
        else:
            await update.message.reply_text(f"❌ Не удалось разбанить пользователя! Ошибка: {error_msg}")

# Команда /kick
async def kick_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Эта команда только для администраторов!")
        return
    
    target_user = await get_mentioned_user(update, context)
    if not target_user:
        return
    
    if isinstance(target_user, int):
        await update.message.reply_text("❌ Кик можно выдать только ответом на сообщение!")
        return
    
    try:
        await context.bot.ban_chat_member(
            chat_id=update.message.chat_id,
            user_id=target_user.id
        )
        
        await context.bot.unban_chat_member(
            chat_id=update.message.chat_id,
            user_id=target_user.id
        )
        
        await update.message.reply_text(
            f"👢 Пользователь {target_user.mention_html()} кикнут из чата!",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка при кике: {e}")
        await update.message.reply_text("❌ Не удалось кикнуть пользователя!")

# Обновленное приветствие новых участников
async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        print(f"🔔 Новые участники обнаружены: {len(update.message.new_chat_members)}")
        
        for member in update.message.new_chat_members:
            print(f"👤 Обрабатываем: {member.first_name} (ID: {member.id})")
            
            if member.id == context.bot.id:
                # Бот добавлен в чат
                await update.message.reply_text(
                    "🤖 Привет! Я бот-модератор Oplatym.ru. "
                    "Дайте мне права администратора для полноценной работы. "
                    "Используйте /help для списка команд."
                )
                print("✅ Бот добавлен в чат")
            else:
                # Новый пользователь - ОБНОВЛЕННОЕ ПРИВЕТСТВИЕ
                welcome_message = (
                    f"👋 Добро пожаловать в Oplatym.ru!\n\n"
                    f"Мы рады видеть вас в нашем чате, пожалуйста ознакомьтесь с предупреждением ниже!\n\n"
                    f"‼️ ВАЖНО: ОСТЕРЕГАЙТЕСЬ МОШЕННИКОВ ‼️\n\n"
                    f"В последнее время участились случаи мошенничества.\n"
                    f"Обращаем ваше внимание: мы никогда не пишем первыми.\n"
                    f"Переходите в наши аккаунты только через ссылки, указанные в этом сообщении:\n\n"
                    f"🔐 <b>Официальные аккаунты Oplatym.ru</b>\n\n"
                    f"<b>Оплата сервисов:</b>\n"
                    f"- @OplatymRU\n"
                    f"- @ByOplatymRu\n"
                    f"- @oplatymManager3\n"
                    f"- @OplatymRu4\n\n"
                    f"<b>Денежные переводы:</b>\n"
                    f"- @oplatym_exchange07\n"
                    f"- @Oplatym_exchange20\n\n"
                    f"<b>Alipay:</b>\n"
                    f"- @CNYExchangeOplatym\n"
                    f"- @CNYExchangeOplatym2\n\n"
                    f"<i>Рады приветствовать вас, {member.mention_html()}! 🎉</i>"
                )
                sent_message = await update.message.reply_html(welcome_message)
                print(f"✅ Приветствие отправлено для {member.first_name}, ID сообщения: {sent_message.message_id}")
                
    except Exception as e:
        error_msg = f"❌ Ошибка в приветствии: {e}"
        print(error_msg)
        logger.error(error_msg)

# Автоответы на ключевые слова
async def auto_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message_text = update.message.text.lower()
        
        # Ключевые слова для оплаты, пополнения и перевода
        payment_keywords = [
            'как пополнить', 'как оплатить', 'как купить', 'как перевести',
            'хочу оплатить', 'хочу купить', 'хочу пополнить', 'хочу перевести',
            'произвести оплату', 'сделать перевод'
        ]
        
        # Проверяем содержит ли сообщение ключевые слова
        if any(keyword in message_text for keyword in payment_keywords):
            reply_message = (
                f"👋 Уважаемый клиент,\n\n"
                f"Обратитесь в один из наших аккаунтов:\n\n"
                f"<b>Оплата сервисов:</b>\n"
                f"- @OplatymRU\n"
                f"- @ByOplatymRu\n"
                f"- @oplatymManager3\n"
                f"- @OplatymRu4\n\n"
                f"<b>Денежные переводы:</b>\n"
                f"- @oplatym_exchange07\n"
                f"- @Oplatym_exchange20\n\n"
                f"<b>Alipay:</b>\n"
                f"- @CNYExchangeOplatym\n"
                f"- @CNYExchangeOplatym2\n\n"
                f"_________________________________________\n\n"
                f"<i>К вашему сведению, мы первыми не пишем! Пожалуйста остерегайтесь мошенников.</i>"
            )
            
            await update.message.reply_html(reply_message)
            print(f"✅ Автоответ отправлен пользователю {update.message.from_user.first_name}")
            
    except Exception as e:
        logger.error(f"Ошибка в автоответе: {e}")

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")

# Основная функция
def main():
    # Создаём приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rules", rules))
    application.add_handler(CommandHandler("check", check_rights))
    application.add_handler(CommandHandler("id", get_id))
    application.add_handler(CommandHandler("warn", warn_user))
    application.add_handler(CommandHandler("mute", mute_user))
    application.add_handler(CommandHandler("unmute", unmute_user))
    application.add_handler(CommandHandler("ban", ban_user))
    application.add_handler(CommandHandler("unban", unban_user))
    application.add_handler(CommandHandler("kick", kick_user))

    # Обработчик новых участников
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    
    # Обработчик автоответов на ключевые слова
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, 
        auto_reply
    ))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    print("🟢 Бот Oplatym.ru запущен и ожидает события...")
    print("📝 Доступные команды: /start, /help, /check, /id, /warn, /mute, /unmute, /ban, /unban, /kick")
    print("🔍 Автоответы активны для ключевых слов:")
    print("   - 'как пополнить', 'как оплатить', 'как купить', 'как перевести'")
    print("   - 'хочу оплатить', 'хочу купить', 'хочу пополнить', 'хочу перевести'")
    print("   - 'произвести оплату', 'сделать перевод'")
    application.run_polling()

if __name__ == "__main__":
    main()