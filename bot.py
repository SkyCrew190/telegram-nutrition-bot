import os
import logging
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен бота из переменных окружения
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
FATSECRET_API_KEY = os.getenv("FATSECRET_API_KEY")
FATSECRET_API_SECRET = os.getenv("FATSECRET_API_SECRET")


def start(update: Update, context: CallbackContext) -> None:
    """Обработчик команды /start"""
    keyboard = [[InlineKeyboardButton("📋 Список продуктов и блюд", callback_data='list'),
                 InlineKeyboardButton("📊 Полноценное меню", callback_data='menu')],
                [InlineKeyboardButton("🏋️ План тренировок", callback_data='workout')],
                [InlineKeyboardButton("📊 Прогресс и отчёты", callback_data='progress')],
                [InlineKeyboardButton("⏰ Напоминания", callback_data='reminders')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        "Привет! Я помогу составить план питания, тренировок и сравнить цены продуктов. Выбери, что тебя интересует:",
        reply_markup=reply_markup
    )


def button_handler(update: Update, context: CallbackContext) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    query.answer()
    
    if query.data == 'list':
        query.edit_message_text("Вы выбрали список продуктов и блюд! Введите свои предпочтения и ограничения.")
        context.user_data['waiting_for_preferences'] = True
    elif query.data == 'menu':
        query.edit_message_text("Вы выбрали полноценное меню! Давайте начнем с параметров вашего питания.")
    elif query.data == 'workout':
        query.edit_message_text(
            "Вы выбрали план тренировок! Введите свои физические параметры (возраст, вес, рост, уровень активности) и цель тренировок (набор массы, похудение, поддержание формы)."
        )
        context.user_data['waiting_for_workout'] = True
    elif query.data == 'progress':
        query.edit_message_text("Выберите, какие данные хотите посмотреть: прогресс веса, изменения в тренировках или рекомендации по питанию.")
    elif query.data == 'reminders':
        query.edit_message_text("Настроим напоминания! Хотите получать уведомления о приёмах пищи, тренировках или покупках?")


def handle_preferences(update: Update, context: CallbackContext) -> None:
    """Обрабатывает ввод предпочтений пользователя и получает информацию о продуктах из FatSecret API."""
    if context.user_data.get('waiting_for_preferences'):
        user_input = update.message.text
        context.user_data['preferences'] = user_input
        
        # Получаем продукты по предпочтениям
        food_list = search_food(user_input)
        
        if food_list:
            response_text = "Вот продукты, соответствующие вашим предпочтениям:\n" + "\n".join(food_list)
            # Рассчитаем калории и макронутриенты
            nutrition_info = get_nutrition_info(food_list)
            response_text += "\n\nПищевая ценность:\n" + nutrition_info
        else:
            response_text = "Не удалось найти подходящие продукты. Попробуйте уточнить запрос."
        
        update.message.reply_text(response_text)
        context.user_data['waiting_for_preferences'] = False


def handle_workout(update: Update, context: CallbackContext) -> None:
    """Обрабатывает ввод данных пользователя и генерирует план тренировок."""
    if context.user_data.get('waiting_for_workout'):
        user_input = update.message.text
        context.user_data['workout_params'] = user_input
        
        # Генерация тренировочного плана
        workout_plan = generate_workout_plan(user_input)
        
        update.message.reply_text("Ваш персональный план тренировок:\n" + workout_plan)
        context.user_data['waiting_for_workout'] = False


def generate_workout_plan(user_input):
    """Создаёт тренировочный план на основе данных пользователя."""
    # Простейшая логика генерации плана
    if "набор массы" in user_input.lower():
        return "- Силовые тренировки 4-5 раз в неделю\n- Упор на базовые упражнения (присед, жим, становая тяга)\n- Высококалорийное питание"
    elif "похудение" in user_input.lower():
        return "- Кардио 3-4 раза в неделю\n- Силовые тренировки 3 раза в неделю\n- Дефицит калорий и контроль макронутриентов"
    else:
        return "- Смешанный режим: 3-4 тренировки в неделю\n- Баланс силовых и кардио нагрузок\n- Поддержание формы без строгих ограничений"


# Создаём приложение бота
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_preferences))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_workout))

if __name__ == "__main__":
    print("Бот запущен...")
    app.run_polling()
