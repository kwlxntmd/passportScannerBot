from telegram import ReplyKeyboardMarkup


class ConversationData:
    def __init__(self):
        self.passport_data = {
        }
        self.chat_id = None
        self.telegram_id = -1
        self.telegram_nick = ""
        self.key_to_fix = 'Номер'
        self.keyboard = ReplyKeyboardMarkup(
            keyboard=[[f"Фамилия", f"Имя", f"Отчество", f"Дата рождения",
                       f"Серия", f"Номер", f"Завершить"]],
            one_time_keyboard=True
        )
        self.admin_keyboard = ReplyKeyboardMarkup(
            keyboard=[[f"Вывести базу данных", f"Поиск по базе",
                       f"Завершить"]],
            one_time_keyboard=True
        )
        self.pages_keyboard = ReplyKeyboardMarkup(
            keyboard=[[f"Пред. стр.", f"След. стр.", f"Получить документ",
                       f"Удалить данные", f"Завершить"]],
            one_time_keyboard=False
        )
        self.confirm_keyboard = ReplyKeyboardMarkup(
            keyboard=[[f"Да", f"Нет"]]
        )
        self.image_to_save = None
        self.total_pages = None
        self.page = 1
        self.cur_table = None
        self.flag = True

    @staticmethod
    def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
        menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
        return menu
