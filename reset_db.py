import sqlite3
import os

# Удаляем старую БД
if os.path.exists('student_bot.db'):
    os.remove('student_bot.db')
    print('✅ Старая БД удалена')

# Создаём новую БД с правильной структурой
conn = sqlite3.connect('student_bot.db')
cursor = conn.cursor()

# Таблица admins с group_name
cursor.execute('''
    CREATE TABLE admins (
        admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER UNIQUE,
        group_name TEXT
    )
''')

# Таблица lesson_times с 7 парами
cursor.execute('''
    CREATE TABLE lesson_times (
        lesson_number INTEGER PRIMARY KEY,
        start_time TEXT,
        end_time TEXT
    )
''')

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

conn.commit()
conn.close()

print('✅ База данных создана заново с правильной структурой!')
print('✅ Таблица admins содержит колонку group_name')
print('✅ Добавлено 7 пар')