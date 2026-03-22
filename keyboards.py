from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard():
    """Главная клавиатура с кнопками"""
    kb = [
        [KeyboardButton(text="📅 Расписание на сегодня")],
        [KeyboardButton(text="📆 Расписание на завтра")],
        [KeyboardButton(text="📚 Мои домашние задания")],
        [KeyboardButton(text="➕ Добавить домашнее задание")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_days_keyboard():
    """Клавиатура с днями недели для выбора"""
    days = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
    kb = [[KeyboardButton(text=day)] for day in days]
    kb.append([KeyboardButton(text="◀️ Назад")])
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_homework_inline_keyboard(hw_id):
    """Инлайн-клавиатура для отметки выполнения"""
    kb = [
        [InlineKeyboardButton(text="✅ Отметить как выполненное", callback_data=f"done_{hw_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)