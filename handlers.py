import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    add_student, get_student, get_schedule, 
    add_homework, get_homework, get_homework_by_date, mark_homework_done,
    is_admin, add_admin, add_lesson, get_all_groups, get_lessons_by_group, delete_lesson,
    get_lesson_by_id
)
from keyboards import get_main_keyboard, get_homework_inline_keyboard, get_groups_keyboard
from bot import get_izhevsk_now

router = Router()
logger = logging.getLogger(__name__)


# ==================== СОСТОЯНИЯ ДЛЯ FSM ====================

class AddHomeworkStates(StatesGroup):
    waiting_for_subject = State()
    waiting_for_task = State()
    waiting_for_date = State()


class AddLessonStates(StatesGroup):
    waiting_for_group = State()
    waiting_for_day = State()
    waiting_for_lesson_number = State()
    waiting_for_subject = State()
    waiting_for_room = State()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_today_name():
    """Возвращает название сегодняшнего дня на русском"""
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    return days[datetime.now().weekday()]


def get_tomorrow_name():
    """Возвращает название завтрашнего дня на русском"""
    days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    return days[(datetime.now().weekday() + 1) % 7]


# ==================== КОМАНДЫ ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ====================

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    student = get_student(user.id)
    
    if not student:
        add_student(user.id, user.first_name)
    
    await message.answer(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я бот-помощник студента.\n\n"
        "**Сначала выбери свою группу:**",
        reply_markup=get_groups_keyboard(),
        parse_mode="Markdown"
    )


@router.message(Command("schedule"))
@router.message(F.text == "📅 Расписание на сегодня")
async def cmd_schedule_today(message: Message):
    """Показать расписание на сегодня"""
    student = get_student(message.from_user.id)
    
    if not student or not student["group_name"]:
        await message.answer(
            "⚠️ Сначала выбери группу через /start"
        )
        return
    
    day_name = get_today_name()
    schedule = get_schedule(student["group_name"], day_name)
    
    if not schedule:
        await message.answer(f"📅 На {day_name} пар нет. Отдыхай! 🎉")
        return
    
    text = f"📅 Расписание на {day_name}:\n\n"
    for lesson in schedule:
        text += f"{lesson['lesson_number']} пара ({lesson['start_time']}-{lesson['end_time']})\n"
        text += f"📖 {lesson['subject']}\n"
        text += f"🏛️ ауд. {lesson['room']}\n\n"
    
    await message.answer(text)


@router.message(Command("tomorrow"))
@router.message(F.text == "📆 Расписание на завтра")
async def cmd_schedule_tomorrow(message: Message):
    """Показать расписание на завтра"""
    student = get_student(message.from_user.id)
    
    if not student or not student["group_name"]:
        await message.answer(
            "⚠️ Сначала выбери группу через /start"
        )
        return
    
    day_name = get_tomorrow_name()
    schedule = get_schedule(student["group_name"], day_name)
    
    if not schedule:
        await message.answer(f"📆 На {day_name} пар нет. Отдыхай! 🎉")
        return
    
    text = f"📆 Расписание на {day_name}:\n\n"
    for lesson in schedule:
        text += f"{lesson['lesson_number']} пара ({lesson['start_time']}-{lesson['end_time']})\n"
        text += f"📖 {lesson['subject']}\n"
        text += f"🏛️ ауд. {lesson['room']}\n\n"
    
    await message.answer(text)


@router.message(Command("homework"))
@router.message(F.text == "📚 Мои домашние задания")
async def cmd_homework(message: Message):
    """Показать домашние задания"""
    student = get_student(message.from_user.id)
    
    if not student:
        await message.answer("Сначала напиши /start для регистрации")
        return
    
    homework_list = get_homework(student["user_id"])
    
    if not homework_list:
        await message.answer("📚 У тебя пока нет домашних заданий.\n\nДобавь первое через /addhw!")
        return
    
    for hw in homework_list:
        status = "✅" if hw["is_done"] else "⏳"
        text = f"{status} **{hw['subject']}**\n"
        text += f"📝 {hw['task_text']}\n"
        text += f"📅 Срок: {hw['due_date']}\n"
        
        if not hw["is_done"]:
            await message.answer(
                text,
                reply_markup=get_homework_inline_keyboard(hw['id']),
                parse_mode="Markdown"
            )
        else:
            await message.answer(text, parse_mode="Markdown")


@router.message(Command("addhw"))
@router.message(F.text == "➕ Добавить домашнее задание")
async def cmd_add_hw_start(message: Message, state: FSMContext):
    """Начать добавление домашнего задания"""
    student = get_student(message.from_user.id)
    
    if not student:
        await message.answer("Сначала напиши /start для регистрации")
        return
    
    await message.answer(
        "➕ Давай добавим домашнее задание!\n\n"
        "Сначала напиши **название предмета** (например: Математика, Базы данных)",
        parse_mode="Markdown"
    )
    await state.set_state(AddHomeworkStates.waiting_for_subject)


@router.message(AddHomeworkStates.waiting_for_subject)
async def add_hw_subject(message: Message, state: FSMContext):
    """Сохраняем предмет и просим задание"""
    await state.update_data(subject=message.text)
    await message.answer(
        "📝 Теперь напиши **описание задания**\n"
        "(что нужно сделать, номер задачи, страницы и т.д.)",
        parse_mode="Markdown"
    )
    await state.set_state(AddHomeworkStates.waiting_for_task)


@router.message(AddHomeworkStates.waiting_for_task)
async def add_hw_task(message: Message, state: FSMContext):
    """Сохраняем задание и просим дату"""
    await state.update_data(task=message.text)
    await message.answer(
        "📅 Теперь напиши **дату сдачи** в формате: ДД.ММ.ГГГГ\n\n"
        "Например: 25.05.2026",
        parse_mode="Markdown"
    )
    await state.set_state(AddHomeworkStates.waiting_for_date)


@router.message(AddHomeworkStates.waiting_for_date)
async def add_hw_date(message: Message, state: FSMContext):
    """Сохраняем дату и создаём задание"""
    due_date = message.text
    
    # Проверка формата даты и запрет на прошедшую дату
    try:
        due_date_obj = datetime.strptime(due_date, "%d.%m.%Y")
        today = get_izhevsk_now().date()
        
        if due_date_obj < today:
            await message.answer("❌ Нельзя добавить домашнее задание на прошедшую дату!")
            return
    except ValueError:
        await message.answer(
            "❌ Неправильный формат даты!\n"
            "Напиши в формате: ДД.ММ.ГГГГ (например, 25.05.2026)"
        )
        return
    
    data = await state.get_data()
    student = get_student(message.from_user.id)
    
    add_homework(
        user_id=student["user_id"],
        subject=data["subject"],
        task_text=data["task"],
        due_date=due_date
    )
    
    await message.answer(
        f"✅ Домашнее задание добавлено!\n\n"
        f"📖 {data['subject']}\n"
        f"📝 {data['task']}\n"
        f"📅 Срок: {due_date}\n\n"
        "Я напомню о нём за день до срока!"
    )
    
    await state.clear()


@router.message(Command("setgroup"))
async def cmd_set_group(message: Message):
    """Установить группу (альтернативный способ)"""
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "⚠️ Напиши: /setgroup НАЗВАНИЕ_ГРУППЫ\n\n"
            "Например: /setgroup ПИ-д\n\n"
            "Доступные группы: ПИ-д, ПИ-э, ПИ-ю, ИВТ, ИС, ИТ"
        )
        return
    
    group_name = parts[1]
    valid_groups = ["ПИ-д", "ПИ-э", "ПИ-ю", "ИВТ", "ИС", "ИТ"]
    
    if group_name not in valid_groups:
        await message.answer(f"❌ Группа {group_name} не найдена. Доступные группы: {', '.join(valid_groups)}")
        return
    
    student = get_student(message.from_user.id)
    
    if student:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE students SET group_name = ? WHERE user_id = ?',
                (group_name, student["user_id"])
            )
            conn.commit()
    
    await message.answer(f"✅ Группа {group_name} сохранена!", reply_markup=get_main_keyboard())


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Помощь"""
    help_text = """
📖 Справка по командам:

/start — начать работу (выбрать группу)
/schedule — расписание на сегодня
/tomorrow — расписание на завтра
/homework — мои домашние задания
/addhw — добавить домашнее задание
/checkreminders — проверить задания на завтра
/setgroup — установить группу

📌 Для старост:
/becomeadmin КОД — стать администратором 
/addlesson — добавить занятие в расписание
/viewschedule — посмотреть расписание группы
/isadmin — проверить статус администратора

Также можно пользоваться кнопками внизу 👇
"""
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("checkreminders"))
async def cmd_check_reminders(message: Message):
    """Проверяет домашние задания на завтра (имитация напоминания)"""
    user_id = message.from_user.id
    tomorrow = (get_izhevsk_now() + timedelta(days=1)).date()
    
    homework_list = get_homework_by_date(user_id, tomorrow.strftime("%d.%m.%Y"))
    
    if not homework_list:
        await message.answer("📭 На завтра нет домашних заданий")
        return
    
    text = "📢 **Напоминание на завтра:**\n\n"
    for hw in homework_list:
        text += f"📖 {hw['subject']}\n📝 {hw['task_text']}\n\n"
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("isadmin"))
async def cmd_is_admin(message: Message):
    """Проверяет, является ли пользователь администратором"""
    if is_admin(message.from_user.id):
        await message.answer("✅ Ты администратор")
    else:
        await message.answer("❌ Ты не администратор")


# ==================== ОБРАБОТЧИК ВЫБОРА ГРУППЫ ====================




# ==================== ОБРАБОТЧИК ИНЛАЙН-КНОПОК ====================

@router.callback_query(F.data.startswith("done_"))
async def callback_mark_done(callback: CallbackQuery):
    """Отмечает задание выполненным"""
    print(f"Получен callback: {callback.data}")  # Отладка
    hw_id = int(callback.data.split("_")[1])
    mark_homework_done(hw_id)
    
    await callback.answer("✅ Задание отмечено как выполненное!")
    await callback.message.edit_text(
        callback.message.text + "\n\n✅ Выполнено!"
    )


# ==================== КОМАНДЫ ДЛЯ АДМИНИСТРАТОРОВ ====================

@router.message(Command("becomeadmin"))
async def cmd_become_admin(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("❌ Введи код: /becomeadmin КОД")
        return
    
    code = parts[1]
    ADMIN_SECRET_CODE = "STAROSTA2026"
    
    if code == ADMIN_SECRET_CODE:
        student = get_student(message.from_user.id)
        group_name = student["group_name"] if student else None
        
        add_admin(message.from_user.id, group_name)
        if group_name:
            await message.answer(f"✅ Ты теперь староста группы {group_name}!")
        else:
            await message.answer("✅ Ты теперь староста! (группа не указана)")
    else:
        await message.answer("❌ Неверный код")


@router.message(Command("addlesson"))
async def cmd_add_lesson_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда доступна только старосте группы.")
        return
    
    # Получаем группу старосты
    student = get_student(message.from_user.id)
    if not student or not student["group_name"]:
        await message.answer("⚠️ Сначала выбери свою группу через /start")
        return
    
    group_name = student["group_name"]
    await state.update_data(group_name=group_name)
    
    # Сразу переходим к выбору дня недели
    from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
    
    days_kb = [
        [KeyboardButton(text="понедельник"), KeyboardButton(text="вторник"), KeyboardButton(text="среда")],
        [KeyboardButton(text="четверг"), KeyboardButton(text="пятница"), KeyboardButton(text="суббота")],
        [KeyboardButton(text="воскресенье"), KeyboardButton(text="◀️ Отмена")]
    ]
    kb = ReplyKeyboardMarkup(keyboard=days_kb, resize_keyboard=True)
    
    await message.answer(
        f"📚 **Добавление занятия для группы {group_name}**\n\n"
        "Выбери **день недели**:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(AddLessonStates.waiting_for_day)


@router.message(AddLessonStates.waiting_for_group)
async def add_lesson_group(message: Message, state: FSMContext):
    """Сохраняем группу, спрашиваем день"""
    group_name = message.text.upper()
    await state.update_data(group_name=group_name)
    
    days_kb = [
    [KeyboardButton(text="понедельник"), KeyboardButton(text="вторник"), KeyboardButton(text="среда")],
    [KeyboardButton(text="четверг"), KeyboardButton(text="пятница"), KeyboardButton(text="суббота")],
    [KeyboardButton(text="воскресенье")]
]
    kb = ReplyKeyboardMarkup(keyboard=days_kb, resize_keyboard=True)
    
    await message.answer(
        f"Группа: {group_name}\n\n"
        "Теперь выбери **день недели**:",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(AddLessonStates.waiting_for_day)


@router.message(AddLessonStates.waiting_for_day)
async def add_lesson_day(message: Message, state: FSMContext):
    """Сохраняем день, спрашиваем номер пары"""
    day = message.text.lower()
    valid_days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"]
    
    if day not in valid_days:
        await message.answer("❌ Выбери день из списка кнопками")
        return
    
    await state.update_data(day=day)
    
    numbers_kb = [[KeyboardButton(text=str(i))] for i in range(1, 8)]  
    numbers_kb.append([KeyboardButton(text="◀️ Отмена")])
    kb = ReplyKeyboardMarkup(keyboard=numbers_kb, resize_keyboard=True)
    
    await message.answer(
        f"День: {day}\n\n"
        "Введи **номер пары** (1-6):",
        reply_markup=kb,
        parse_mode="Markdown"
    )
    await state.set_state(AddLessonStates.waiting_for_lesson_number)


@router.message(AddLessonStates.waiting_for_lesson_number)
async def add_lesson_number(message: Message, state: FSMContext):
    """Сохраняем номер пары, спрашиваем предмет"""
    if message.text == "◀️ Отмена":
        await state.clear()
        await message.answer("❌ Добавление отменено", reply_markup=get_main_keyboard())
        return
    
    try:
        lesson_number = int(message.text)
        if lesson_number < 1 or lesson_number > 6:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введи число от 1 до 6")
        return
    
    await state.update_data(lesson_number=lesson_number)
    await message.answer(
        f"Номер пары: {lesson_number}\n\n"
        "Теперь введи **название предмета**:",
        parse_mode="Markdown"
    )
    await state.set_state(AddLessonStates.waiting_for_subject)


@router.message(AddLessonStates.waiting_for_subject)
async def add_lesson_subject(message: Message, state: FSMContext):
    """Сохраняем предмет, спрашиваем аудиторию"""
    await state.update_data(subject=message.text)
    await message.answer(
        f"Предмет: {message.text}\n\n"
        "Теперь введи **номер аудитории**:",
        parse_mode="Markdown"
    )
    await state.set_state(AddLessonStates.waiting_for_room)


@router.message(AddLessonStates.waiting_for_room)
async def add_lesson_room(message: Message, state: FSMContext):
    """Сохраняем аудиторию и создаём занятие"""
    room = message.text
    data = await state.get_data()
    
    add_lesson(
        group_name=data["group_name"],
        day_of_week=data["day"],
        lesson_number=data["lesson_number"],
        subject=data["subject"],
        room=room
    )
    
    await message.answer(
        f"✅ **Занятие добавлено!**\n\n"
        f"Группа: {data['group_name']}\n"
        f"День: {data['day']}\n"
        f"Пара: {data['lesson_number']}\n"
        f"Предмет: {data['subject']}\n"
        f"Аудитория: {room}",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )
    await state.clear()


@router.message(Command("viewschedule"))
async def cmd_view_schedule(message: Message):
    """Просмотр расписания группы (только для админов)"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда доступна только старосте группы.")
        return
    
    groups = get_all_groups()
    if not groups:
        await message.answer("📭 В базе пока нет расписания ни для одной группы.")
        return
    
    group = groups[0]
    lessons = get_lessons_by_group(group)
    
    if not lessons:
        await message.answer(f"📭 Для группы {group} расписание пустое.")
        return
    
    text = f"📚 **Расписание группы {group}**\n\n"
    current_day = ""
    for lesson in lessons:
        if lesson["day_of_week"] != current_day:
            current_day = lesson["day_of_week"]
            text += f"\n*{current_day.capitalize()}:*\n"
        text += f"{lesson['lesson_number']} пара ({lesson['start_time']}-{lesson['end_time']}) — {lesson['subject']} (ауд. {lesson['room']}) — /del_{lesson['id']}\n"
    
    text += "\n_Для удаления нажми на команду /del_ID_"
    await message.answer(text, parse_mode="Markdown")


@router.message(lambda msg: msg.text and msg.text.startswith("/del_"))
async def cmd_delete_lesson(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда доступна только старосте группы.")
        return
    
    try:
        lesson_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат. Используй команду из списка.")
        return
    
    # Получаем группу старосты
    student = get_student(message.from_user.id)
    if not student or not student["group_name"]:
        await message.answer("⚠️ Сначала выбери свою группу.")
        return
    
    # Проверяем, что занятие принадлежит группе старосты
    lesson = get_lesson_by_id(lesson_id)
    if not lesson or lesson["group_name"] != student["group_name"]:
        await message.answer("❌ Занятие не найдено или принадлежит другой группе.")
        return
    
    deleted = delete_lesson(lesson_id)
    
    if deleted:
        await message.answer(f"✅ Занятие с ID {lesson_id} удалено.")
    else:
        await message.answer(f"❌ Занятие с ID {lesson_id} не найдено.")

@router.message(Command("del"))
async def cmd_delete_lesson_list(message: Message):
    """Показывает список занятий для удаления"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Эта команда доступна только старосте группы.")
        return
    
    student = get_student(message.from_user.id)
    if not student or not student["group_name"]:
        await message.answer("⚠️ Сначала выбери свою группу.")
        return
    
    group_name = student["group_name"]
    lessons = get_lessons_by_group(group_name)
    
    if not lessons:
        await message.answer(f"📭 Для группы {group_name} расписание пустое.")
        return
    
    text = f"📚 **Расписание группы {group_name}**\n\n"
    current_day = ""
    for lesson in lessons:
        if lesson["day_of_week"] != current_day:
            current_day = lesson["day_of_week"]
            text += f"\n*{current_day.capitalize()}:*\n"
        text += f"{lesson['lesson_number']} пара ({lesson['start_time']}-{lesson['end_time']}) — {lesson['subject']} (ауд. {lesson['room']})\n"
        text += f"➡️ Для удаления: `/del_{lesson['id']}`\n"
    
    await message.answer(text, parse_mode="Markdown")