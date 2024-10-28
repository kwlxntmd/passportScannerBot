import sqlean as sqlite3
from prettytable import PrettyTable


class Database:
    ROWS_PER_PAGE = 10

    @staticmethod
    def connect():
        connection = sqlite3.connect('passport_data.db')
        cursor = connection.cursor()
        cursor.execute('PRAGMA encoding = "UTF-8"')

        # create passport data table
        command1 = """CREATE TABLE IF NOT EXISTS
            passports(
                telegram_id INTEGER PRIMARY KEY,
                telegram_nick TEXT COLLATE NOCASE,
                surname TEXT COLLATE NOCASE,
                name TEXT COLLATE NOCASE,
                fathers_name TEXT COLLATE NOCASE,
                date_of_birth TEXT COLLATE NOCASE,
                series TEXT COLLATE NOCASE,
                number TEXT COLLATE NOCASE
                )"""

        cursor.execute(command1)

        connection.commit()
        connection.close()

    @staticmethod
    def add_user_data(tg_id, telegram_nick, sur, name, otch, date_of_birth,
                      series, number):
        connection = sqlite3.connect('passport_data.db')
        existing_data = Database.search_for_existing_data(tg_id)
        if existing_data:
            # Обновляем существующую запись
            Database.edit_existing_data(tg_id, telegram_nick, sur, name,
                                        otch, date_of_birth, series, number)
        else:
            # Добавляем новую запись
            Database.add_new_data(tg_id, telegram_nick, sur, name, otch,
                                  date_of_birth,
                                  series, number)

        connection.commit()
        print('added user to database')
        connection.close()

    @staticmethod
    def search_for_existing_data(tg_id):
        connection = sqlite3.connect('passport_data.db')
        cursor = connection.cursor()

        # Проверяем если данные о пользователе уже существуют
        cursor.execute('SELECT 1 FROM passports WHERE telegram_id=?',
                       (tg_id,))
        existing_data = cursor.fetchone()
        return existing_data

    @staticmethod
    def edit_existing_data(tg_id, telegram_nick, sur, name, otch,
                           date_of_birth, series, number):
        connection = sqlite3.connect('passport_data.db')
        cursor = connection.cursor()
        cursor.execute('''
                            UPDATE passports SET
                            telegram_nick=?,
                            surname=?,
                            name=?,
                            fathers_name=?,
                            date_of_birth=?,
                            series=?,
                            number=?
                            WHERE telegram_id=?
                        ''', (
            telegram_nick, name, sur, otch, date_of_birth, series, number,
            tg_id))

    @staticmethod
    def add_new_data(tg_id, telegram_nick, sur, name, otch, date_of_birth,
                     series, number):
        connection = sqlite3.connect('passport_data.db')
        cursor = connection.cursor()
        cursor.execute('''
                        INSERT INTO passports
                        (telegram_id, telegram_nick, surname, name,
                        fathers_name, date_of_birth, series, number)
                        VALUES (?,?,?,?,?,?,?,?)
                        ''', (
            tg_id, telegram_nick, sur, name, otch, date_of_birth, series,
            number))

    @staticmethod
    def get_total_pages():
        conn = sqlite3.connect('passport_data.db')
        cursor = conn.cursor()
        # Получение общего количества строк в таблице
        cursor.execute('SELECT COUNT(*) FROM passports')
        total_rows = cursor.fetchone()[0]

        # Вычисление общего количества страниц
        return (total_rows +
                Database.ROWS_PER_PAGE - 1) // Database.ROWS_PER_PAGE

    @staticmethod
    def search(params):
        sqlite3.extensions.enable_all()
        print(params)
        # Подключаемся к базе данных
        conn = sqlite3.connect('passport_data.db')
        cursor = conn.cursor()

        # Создаем SQL-запрос по введенным параметрам
        sql_query = "SELECT * FROM passports "
        conditions = []
        for param in params:
            param = param.upper()
            conditions.append(
                f"telegram_id LIKE '%{param}%'"
                f" OR upper(telegram_nick) LIKE '%{param}%'"
                f" OR upper(surname) LIKE '%{param}%'"
                f" OR upper(name) LIKE '%{param}%'"
                f" OR upper(fathers_name) LIKE '%{param}%'"
                f" OR date_of_birth LIKE '%{param}%'"
                f" OR series LIKE '%{param}%'"
                f" OR number LIKE '%{param}%'")
        sql_query += "WHERE ("
        sql_query += ") AND (".join(conditions)
        sql_query += ")"
        print(conditions)
        print(sql_query)
        print("Conditions created")

        cursor.execute(sql_query)
        results = cursor.fetchall()
        print(results)
        cursor.close()
        conn.close()
        print("conn closed")
        return results

    @staticmethod
    def format_table(rows, columns):
        conn = sqlite3.connect('passport_data.db')

        # Создание таблицы для вывода данных
        table = PrettyTable(columns)
        table.align = 'c'

        # Добавление данных в таблицу
        for row in rows:
            table.add_row(row)

        # Получение отформатированной таблицы
        formatted_table = table.get_string()
        conn.close()
        print(formatted_table)
        return formatted_table

    @staticmethod
    def get_data_for_page(page, rows_per_page):
        conn = sqlite3.connect('passport_data.db')
        cursor = conn.cursor()
        offset = (page - 1) * rows_per_page
        cursor.execute('SELECT * FROM passports LIMIT ? OFFSET ?',
                       (rows_per_page, offset))
        rows = cursor.fetchall()
        print(rows)
        return rows

    @staticmethod
    def get_names_for_page(page, rows_per_page):
        conn = sqlite3.connect('passport_data.db')
        cursor = conn.cursor()
        offset = (page - 1) * rows_per_page
        cursor.execute('SELECT name FROM passports LIMIT ? OFFSET ?',
                       (rows_per_page, offset))
        rows = cursor.fetchall()
        names = []
        for item in rows:
            names.append(item[0])
        cursor.execute('SELECT telegram_id FROM passports LIMIT ? OFFSET ?',
                       (rows_per_page, offset))
        rows = cursor.fetchall()
        ids = []
        for item in rows:
            ids.append(item[0])
        cursor.execute('SELECT surname FROM passports LIMIT ? OFFSET ?',
                       (rows_per_page, offset))
        rows = cursor.fetchall()
        surnames = []
        for item in rows:
            surnames.append(item[0])
        return ids, surnames, names

    @staticmethod
    def delete_data(key):
        conn = sqlite3.connect('passport_data.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM passports WHERE telegram_id = ?', (key,))
        conn.commit()
