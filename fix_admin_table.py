import sqlite3

conn = sqlite3.connect('student_bot.db')
conn.execute('DROP TABLE IF EXISTS admins')
conn.commit()
conn.close()
print('✅ Таблица admins удалена. Перезапусти бота, и она создастся заново с правильной структурой.')