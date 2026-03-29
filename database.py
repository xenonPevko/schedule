import sqlite3
import logging

DB_NAME = "student_bot.db"

logger = logging.getLogger(__name__)

def get_db_connection():
    """Возвращает соединение с базой данных"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создаёт таблицы, если их нет"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Таблица студентов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                group_name TEXT,
                first_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица групп
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT UNIQUE
            )
        ''')
        
        # Таблица времени пар
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lesson_times (
                lesson_number INTEGER PRIMARY KEY,
                start_time TEXT,
                end_time TEXT
            )
        ''')
        
        # Таблица расписания
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_name TEXT,
                day_of_week TEXT,
                lesson_number INTEGER,
                subject TEXT,
                room TEXT,
                FOREIGN KEY (lesson_number) REFERENCES lesson_times(lesson_number)
            )
        ''')
        
        # Таблица домашних заданий
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS homework (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                task_text TEXT,
                due_date TEXT,
                is_done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES students(user_id)
            )
        ''')
        
        # Таблица администраторов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                group_name TEXT
            )
        ''')
        
        # Добавляем время пар по умолчанию 
        cursor.execute('''
            INSERT OR IGNORE INTO lesson_times (lesson_number, start_time, end_time)
            VALUES 
                (1, '08:20', '09:50'),
                (2, '10:00', '11:30'),
                (3, '12:10', '13:40'),
                (4, '13:50', '15:20'),
                (5, '15:30', '17:00'),
                (6, '17:20', '18:50'),
                (7, '19:00', '20:30')
        ''')
        
        conn.commit()
        logger.info("База данных инициализирована")

def add_student(telegram_id, first_name, group_name=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO students (telegram_id, first_name, group_name)
            VALUES (?, ?, ?)
        ''', (telegram_id, first_name, group_name))
        conn.commit()
        return cursor.lastrowid

def get_student(telegram_id):
    """Получает информацию о студенте"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM students WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone()

def get_schedule(group_name, day_of_week):
    """Получает расписание для группы на определённый день"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.lesson_number, lt.start_time, lt.end_time, s.subject, s.room
            FROM schedule s
            JOIN lesson_times lt ON s.lesson_number = lt.lesson_number
            WHERE s.group_name = ? AND s.day_of_week = ?
            ORDER BY s.lesson_number
        ''', (group_name, day_of_week))
        return cursor.fetchall()

def add_homework(user_id, subject, task_text, due_date):
    """Добавляет домашнее задание"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO homework (user_id, subject, task_text, due_date)
            VALUES (?, ?, ?, ?)
        ''', (user_id, subject, task_text, due_date))
        conn.commit()
        return cursor.lastrowid

def get_homework(user_id, due_date=None):
    """Получает домашние задания студента"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if due_date:
            cursor.execute('''
                SELECT * FROM homework 
                WHERE user_id = ? AND due_date = ?
                ORDER BY due_date
            ''', (user_id, due_date))
        else:
            cursor.execute('''
                SELECT * FROM homework 
                WHERE user_id = ? 
                ORDER BY due_date
            ''', (user_id,))
        return cursor.fetchall()

def mark_homework_done(hw_id):
    """Отмечает задание выполненным"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE homework SET is_done = 1 WHERE id = ?', (hw_id,))
        conn.commit()

def is_admin(telegram_id, group_name=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if group_name:
            cursor.execute('''
                SELECT * FROM admins 
                WHERE telegram_id = ? AND (group_name = ? OR group_name IS NULL)
            ''', (telegram_id, group_name))
        else:
            cursor.execute('SELECT * FROM admins WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone() is not None

def add_admin(telegram_id, group_name=None):
    """Добавляет администратора с привязкой к группе"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO admins (telegram_id, group_name) 
            VALUES (?, ?)
        ''', (telegram_id, group_name))
        conn.commit()

def add_lesson(group_name, day_of_week, lesson_number, subject, room):
    """Добавляет занятие в расписание"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO schedule (group_name, day_of_week, lesson_number, subject, room)
            VALUES (?, ?, ?, ?, ?)
        ''', (group_name, day_of_week, lesson_number, subject, room))
        conn.commit()
        return cursor.lastrowid

def get_all_groups():
    """Получает список всех групп, у которых есть расписание"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT group_name FROM schedule')
        return [row["group_name"] for row in cursor.fetchall()]

def delete_lesson(lesson_id):
    """Удаляет занятие по ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM schedule WHERE id = ?', (lesson_id,))
        conn.commit()
        return cursor.rowcount

def get_lessons_by_group(group_name):
    """Получает все занятия группы с ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.id, s.day_of_week, s.lesson_number, lt.start_time, lt.end_time, s.subject, s.room
            FROM schedule s
            JOIN lesson_times lt ON s.lesson_number = lt.lesson_number
            WHERE s.group_name = ?
            ORDER BY 
                CASE s.day_of_week
                    WHEN 'понедельник' THEN 1
                    WHEN 'вторник' THEN 2
                    WHEN 'среда' THEN 3
                    WHEN 'четверг' THEN 4
                    WHEN 'пятница' THEN 5
                    WHEN 'суббота' THEN 6
                    WHEN 'воскресенье' THEN 7
                END,
                s.lesson_number
        ''', (group_name,))
        return cursor.fetchall()
    
def get_lesson_by_id(lesson_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM schedule WHERE id = ?', (lesson_id,))
        return cursor.fetchone()

def get_homework_by_date(user_id, due_date):
    """Получает домашние задания на конкретную дату"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM homework 
            WHERE user_id = ? AND due_date = ?
            ORDER BY due_date
        ''', (user_id, due_date))
        return cursor.fetchall()