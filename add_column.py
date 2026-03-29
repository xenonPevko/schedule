import sqlite3

conn = sqlite3.connect('student_bot.db')
try:
    conn.execute('ALTER TABLE admins ADD COLUMN group_name TEXT')
    print('✅ Колонка group_name добавлена')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('✅ Колонка group_name уже существует')
    else:
        print(f'Ошибка: {e}')
conn.commit()
conn.close()