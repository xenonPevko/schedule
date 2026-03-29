import sqlite3
import os

# Удаляем старую БД
if os.path.exists('student_bot.db'):
    os.remove('student_bot.db')
    print('✅ Старая БД удалена')

# Создаём новую БД
conn = sqlite3.connect('student_bot.db')
cursor = conn.cursor()

# 1. Таблица студентов
cursor.execute('''
    CREATE TABLE students (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        group_name TEXT,
        first_name TEXT,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# 2. Таблица групп
cursor.execute('''
    CREATE TABLE groups (
        group_id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT UNIQUE
    )
''')

# 3. Таблица времени пар (7 пар)
cursor.execute('''
    CREATE TABLE lesson_times (
        lesson_number INTEGER PRIMARY KEY,
        start_time TEXT,
        end_time TEXT
    )
''')

# Добавляем 7 пар
lessons = [
    (1, '08:20', '09:50'),
    (2, '10:00', '11:30'),
    (3, '12:10', '13:40'),
    (4, '13:50', '15:20'),
    (5, '15:30', '17:00'),
    (6, '17:20', '18:50'),
    (7, '19:00', '20:30')
]
cursor.executemany('INSERT INTO lesson_times (lesson_number, start_time, end_time) VALUES (?, ?, ?)', lessons)

# 4. Таблица расписания
cursor.execute('''
    CREATE TABLE schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_name TEXT,
        day_of_week TEXT,
        lesson_number INTEGER,
        subject TEXT,
        room TEXT,
        FOREIGN KEY (lesson_number) REFERENCES lesson_times(lesson_number)
    )
''')

# 5. Таблица домашних заданий
cursor.execute('''
    CREATE TABLE homework (
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

# 6. Таблица администраторов (С КОЛОНКОЙ group_name)
cursor.execute('''
    CREATE TABLE admins (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        group_name TEXT
    )
''')

conn.commit()
conn.close()

print('✅ База данных создана заново!')
print('✅ Таблица admins имеет колонку group_name')
print('✅ Добавлено 7 пар')
print('✅ ВСЕ таблицы созданы с нуля')