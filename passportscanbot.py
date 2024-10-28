from telegram import ReplyKeyboardRemove, Update, InlineKeyboardMarkup, \
    InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, MessageHandler, \
    filters, ContextTypes, ConversationHandler, CallbackQueryHandler
import cv2
import numpy as np
import main
from config import TOKEN, admins
from db import Database
from conversationdata import ConversationData
from imageprocessing import ImageProcessing
from warnings import filterwarnings
from telegram.warnings import PTBUserWarning
from DocRequests import DocRequests

PHOTO, HANDLE_REPLY, FIX_DATA, ADMIN_COMMANDS, HANDLE_ADMIN, DATABASE_PAGES, \
DATABASE_SEARCH = range(7)


def format_response(response):
    return "\n".join("{}:\t{}".format(k, v) for k, v in response.items())


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Проверка, является ли пользователь админом
    conv_data.telegram_id = update.message.chat.id
    conv_data.telegram_nick = str(update.message.chat.username)
    print(conv_data.telegram_id, conv_data.telegram_nick)
    if conv_data.telegram_nick in admins:
        conv_data.chat_id = update.message.chat_id
        index = admins.index(conv_data.telegram_nick)
        admins[index] = int(conv_data.telegram_id)
        await update.message.reply_text(
            f'Здравствуйте! Выберите действие',
            reply_markup=conv_data.admin_keyboard
        )
        return HANDLE_ADMIN
    elif conv_data.telegram_id in admins:
        await update.message.reply_text(
            f'Здравствуйте! Выберите действие',
            reply_markup=conv_data.admin_keyboard
        )
        return HANDLE_ADMIN

    await update.message.reply_text(f'Здравствуйте!\nДля того, чтобы считать '
                                    f'данные, отправьте фото развернутого '
                                    f'паспорта. Убедитесь, что нижние '
                                    f'строчки хорошо видны',
                                    reply_markup=ReplyKeyboardRemove()
                                    )
    return PHOTO


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Данный бот предназначен для считывания '
                                    f'основных данных с фотографии паспорта. '
                                    f'После получения считанных данных Вы '
                                    f'можете их исправить в случае '
                                    f'нахождения ошибок. Напишите "/start", '
                                    f'чтобы начать')


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Получение ID пользователя и файла
    file_id = update.message.photo[-1].file_id
    file = await context.bot.get_file(file_id)

    byte_image = await file.download_as_bytearray()
    np_array_img = np.asarray(byte_image, np.uint8)
    img = cv2.imdecode(np_array_img, cv2.IMREAD_COLOR)

    print('Photo recieved')

    conv_data.image_to_save = byte_image
    conv_data.passport_data = main.main(img)

    response_text = format_response(conv_data.passport_data)
    print('Photo scanned')
    await update.message.reply_text(f'{response_text}\n\n'
                                    f'Если в каких-то данных ошибка, нажмите '
                                    f'на соответствующую кнопку. Если все '
                                    f'данные корректны, нажмите "Завершить"',
                                    reply_markup=conv_data.keyboard
                                    )
    return HANDLE_REPLY


async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.message.text
    if reply == f'Фамилия':
        await update.message.reply_text(f"Введите фамилию",
                                        reply_markup=ReplyKeyboardRemove())
        conv_data.key_to_fix = 'Фамилия'
        return FIX_DATA
    if reply == f'Имя':
        await update.message.reply_text(f"Введите имя",
                                        reply_markup=ReplyKeyboardRemove())
        conv_data.key_to_fix = 'Имя'
        return FIX_DATA
    if reply == f'Отчество':
        await update.message.reply_text(f"Введите отчество",
                                        reply_markup=ReplyKeyboardRemove())
        conv_data.key_to_fix = 'Отчество'
        return FIX_DATA
    if reply == f'Дата рождения':
        await update.message.reply_text(f"Введите дату рождения",
                                        reply_markup=ReplyKeyboardRemove())
        conv_data.key_to_fix = 'Дата рождения'
        return FIX_DATA
    if reply == f'Серия':
        await update.message.reply_text(f"Введите серию",
                                        reply_markup=ReplyKeyboardRemove())
        conv_data.key_to_fix = 'Серия'
        return FIX_DATA
    if reply == f'Номер':
        await update.message.reply_text(f"Введите номер",
                                        reply_markup=ReplyKeyboardRemove())
        conv_data.key_to_fix = 'Номер'
        return FIX_DATA
    if reply == f'Завершить':
        await update.message.reply_text(f"Спасибо!",
                                        reply_markup=ReplyKeyboardRemove())

        data = list(conv_data.passport_data.values())
        if conv_data.telegram_id != -1:
            Database.add_user_data(conv_data.telegram_id,
                                   conv_data.telegram_nick, *data)
        ImageProcessing.save_photo(conv_data.image_to_save,
                                   conv_data.passport_data['Дата рождения'],
                                   conv_data.telegram_id)

        session_id = DocRequests.get_session()
        try:
            template_ids = DocRequests.get_template_ids(session_id)
        except:
            session_id = DocRequests.get_session()
            template_ids = DocRequests.get_template_ids(session_id)

        # file_info = doc_requests.get_file_info(doc_requests.session_id,
        #                                        doc_requests.correct_id)
        # print(file_info.json())
        template_id = template_ids.json()["data"][0]["recordId"]
        try:
            DocRequests.fillDoc(template_id,
                                session_id,
                                conv_data.passport_data)
        except:
            session_id = DocRequests.get_session()
            DocRequests.fillDoc(template_id,
                                session_id,
                                conv_data.passport_data)

        filename = conv_data.passport_data["Фамилия"] + "_" + \
                   conv_data.passport_data["Имя"] + "_" + \
                   str(conv_data.telegram_id)
        try:
            DocRequests.download_file(template_id,
                                      session_id,
                                      filename,
                                      "docx",
                                      )
        except:
            session_id = DocRequests.get_session()
            DocRequests.download_file(template_id,
                                      session_id,
                                      filename,
                                      "docx",
                                      )

        return ConversationHandler.END


async def fix_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    correct_data = update.message.text
    conv_data.passport_data[conv_data.key_to_fix] = correct_data.capitalize()
    response_text = format_response(conv_data.passport_data)
    await update.message.reply_text(f'{response_text}\n\n'
                                    f'Если в каких-то данных ошибка, нажмите '
                                    f'на соответствующую кнопку. Если все '
                                    f'данные корректны, нажмите "Завершить"',
                                    reply_markup=conv_data.keyboard
                                    )
    return HANDLE_REPLY


# Admin commands
async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f'Выберите действие',
        reply_markup=conv_data.admin_keyboard
    )
    return HANDLE_ADMIN


async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply = update.message.text
    if reply == f'Вывести базу данных':
        keyboard = [[InlineKeyboardButton("Просмотреть базу данных",
                                          callback_data='view')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Нажмите на кнопку",
                                        reply_markup=reply_markup)
        conv_data.total_pages = Database.get_total_pages()
        return DATABASE_PAGES
    if reply == f'Поиск по базе':
        await update.message.reply_text(f"Введите данные, по которым хотите "
                                        f"провести поиск. Пожалуйста, "
                                        f"вводите их через пробел",
                                        reply_markup=ReplyKeyboardRemove())
        return DATABASE_SEARCH
    if reply == f'Завершить':
        await update.message.reply_text(f"Спасибо!",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


async def db_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_result = Database.search(update.message.text.upper().split())
    print("search results acquired")
    if len(search_result) > 0:
        db_table = Database.format_table(search_result,
                                         ['id',
                                          '@',
                                          'Фамилия',
                                          'Имя',
                                          'Отчество',
                                          'Дата Рождения',
                                          'Серия',
                                          'Номер'])
        await update.message.reply_text(f'<pre>{db_table}</pre>' +
                                        f"\n\n\n Выберите следующее действие",
                                        reply_markup=conv_data.admin_keyboard,
                                        parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"Ничего не найдено. Выберите "
                                        f"следующее действие",
                                        reply_markup=conv_data.admin_keyboard)
    return HANDLE_ADMIN


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Спасибо!",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


async def pages_query(update, context):
    query = update.callback_query

    # Получение текущей страницы базы данных сохраненной в контексте
    page = conv_data.page
    rows_per_page = 10

    if query.data.startswith('confirm:'):
        conv_data.flag = True
        print(query.data.split(':')[1])
        Database.delete_data(int(query.data.split(':')[1]))
    if query.data == 'del_cancel':
        conv_data.flag = True

    if query.data == 'prev':
        # Предыдущая страница
        conv_data.flag = True
        page -= 1
        if page < 1:
            page = 1
    elif query.data == 'next':
        conv_data.flag = True
        # Следующая страница
        page += 1
        if page > conv_data.total_pages:
            page -= 1
    elif query.data == "doc_data":
        conv_data.flag = False
        buttons = []
        ids, surnames, names = Database.get_names_for_page(page, rows_per_page)
        for i in range(len(ids)):
            button = InlineKeyboardButton(surnames[i] + " " + names[i],
                                          callback_data='doc:'
                                                        + surnames[i]
                                                        + ':' + names[i]
                                                        + ':' + str(ids[i]))

            buttons.append(button)
        nick_buttons = InlineKeyboardMarkup(
            [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
            + [[InlineKeyboardButton('Завершить', callback_data='del_cancel')]]

        )
        await query.edit_message_text(text=f'<pre>{conv_data.cur_table}</pre>'
                                           + f'\n\n\nВыберите,'
                                             f' чей документ получить:',
                                      reply_markup=nick_buttons,
                                      parse_mode=ParseMode.HTML)
    elif query.data.startswith("doc:"):
        data_to_send = "user_documents/" + \
                       query.data.split(':')[1] + "_" + \
                       query.data.split(':')[2] + "_" + \
                       query.data.split(':')[3] + \
                       ".docx"
        document = open(data_to_send, 'rb')
        await context.bot.send_document(conv_data.chat_id, document)
        conv_data.flag = True

    elif query.data == 'del_data':
        conv_data.flag = False
        buttons = []
        ids, surnames, names = Database.get_names_for_page(page, rows_per_page)
        for i in range(len(ids)):
            button = InlineKeyboardButton(surnames[i] + " " + names[i],
                                          callback_data='delete:'
                                                        + surnames[i]
                                                        + ':' + names[i]
                                                        + ':' + str(ids[i]))

            buttons.append(button)
        nick_buttons = InlineKeyboardMarkup(
            [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
            + [[InlineKeyboardButton('Завершить', callback_data='del_cancel')]]

        )
        await query.edit_message_text(text=f'<pre>{conv_data.cur_table}</pre>'
                                           + f'\n\n\nВыберите,'
                                             f' чьи данные удалить:',
                                      reply_markup=nick_buttons,
                                      parse_mode=ParseMode.HTML)
    elif query.data.startswith('delete:'):
        conv_data.flag = False
        data_to_delete = query.data.split(':')[3]
        data_to_show = query.data.split(':')[1] + ' ' + \
                       query.data.split(':')[2]
        await query.edit_message_text(text=f'<pre>{conv_data.cur_table}</pre>'
                                           + f'\n\n\nВы уверены, что хотите'
                                             f' удалить пользователя'
                                             f' <b>{data_to_show}</b> из'
                                             f' базы данных?',
                                      reply_markup=InlineKeyboardMarkup(
                                          [
                                              [
                                                  InlineKeyboardButton(
                                                      'Да',
                                                      callback_data=
                                                      'confirm:' +
                                                      data_to_delete),
                                                  InlineKeyboardButton(
                                                      'Нет',
                                                      callback_data=
                                                      'del_data')
                                              ]]),
                                      parse_mode=ParseMode.HTML)

    elif query.data == 'finish':
        conv_data.flag = True
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text='Выберите действие',
                                       reply_markup=conv_data.admin_keyboard)

        # Завершение показа базы данных
        return HANDLE_ADMIN

    # Создание таблицы для текущей страницы базы данных
    if conv_data.flag:
        table_data = Database.get_data_for_page(page, rows_per_page)
        formatted_table = Database.format_table(table_data,
                                                ['id', '@', 'Фамилия', 'Имя',
                                                 'Отчество', 'Дата Рождения',
                                                 'Серия', 'Номер']
                                                )
        conv_data.cur_table = formatted_table

        # Изменение сообщения с таблицей
        await query.edit_message_text(text=f'<pre>{conv_data.cur_table}</pre>',
                                      reply_markup=InlineKeyboardMarkup(
                                          [
                                              [
                                                  InlineKeyboardButton(
                                                      'Пред. стр',
                                                      callback_data=
                                                      'prev'),
                                                  InlineKeyboardButton(
                                                      'След. стр',
                                                      callback_data=
                                                      'next')
                                              ],
                                              [InlineKeyboardButton(
                                                  'Получить документ',
                                                  callback_data=
                                                  'doc_data')],
                                              [InlineKeyboardButton(
                                                  'Удалить данные',
                                                  callback_data=
                                                  'del_data')],
                                              [InlineKeyboardButton(
                                                  'Завершить',
                                                  callback_data=
                                                  'finish')]
                                          ]
                                      ),
                                      parse_mode=ParseMode.HTML)

    # Сохранение текущей страницы в контексте
    conv_data.page = page


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')
    await update.message.reply_text(f'Произошла ошибка. Пожалуйста, '
                                    f'перезапустите разговор с ботом')
    return ConversationHandler.END


if __name__ == '__main__':
    print('Starting bot...')
    Database.connect()
    app = Application.builder().token(TOKEN).build()

    conv_data = ConversationData()

    filterwarnings(action="ignore", message=r".*CallbackQueryHandler",
                   category=PTBUserWarning)

    # Commands
    app.add_handler(CommandHandler('help', help_command))

    # Conversation Handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, photo)],
            HANDLE_REPLY: [MessageHandler(filters.TEXT, handle_reply)],
            FIX_DATA: [MessageHandler(filters.TEXT, fix_data)],
            ADMIN_COMMANDS: [MessageHandler(filters.TEXT, admin_commands)],
            HANDLE_ADMIN: [MessageHandler(filters.TEXT, handle_admin)],
            DATABASE_PAGES: [CallbackQueryHandler(pages_query)],
            DATABASE_SEARCH: [MessageHandler(filters.TEXT, db_search)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    # Errors
    app.add_error_handler(error)

    # Polls the bot
    print('Polling...')
    app.run_polling(allowed_updates=Update.ALL_TYPES)
