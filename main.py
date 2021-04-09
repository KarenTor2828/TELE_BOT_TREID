# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

from tabulate import tabulate
from bs4 import BeautifulSoup
import telebot
from random import randint
import conf
import dbwoker
import pandas as pd
import requests
import os
import re
from selenium import webdriver as wb
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from time import sleep

# Запуск селениум на heroku
chrome_options = webdriver.ChromeOptions()
chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--no-sandbox")

bot = telebot.TeleBot(conf.token)


def init_driver(tag=0):
    #driver = wb.Chrome()
    driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    driver.get("https://bcs-express.ru")
    driver.implicitly_wait(5)
    return driver


driver_bot = init_driver()

#def close_driver(driver):
#    driver.close()


def get_list_variant(message, number):
    list_variant = list()
    for row in range(number):
        if dbwoker.get_current_property(str(message.chat.id) + str(row)) != False:
            list_variant.append(dbwoker.get_current_property(str(message.chat.id) + str(row)))
        else:
            break
    return list_variant


def del_list_variant(message, number):
    for row in range(number):
        dbwoker.del_state(str(message.chat.id) + str(row))


def search_firm(firm_input, driver):
    # ищем кнопку поиска в головном меню
    driver.get("https://bcs-express.ru")
    search_header = driver.find_element_by_class_name("icon-search")
    driver.implicitly_wait(3)
    search_header.click()
    # ищем окно ввода запроса
    input_form = driver.find_element_by_name('search')
    # добавил очищение 09042021
    input_form.clear()
    driver.implicitly_wait(1)
    # отправляем запрос
    input_form.send_keys(firm_input)
    driver.implicitly_wait(1)
    # закрываем окно поиска - так как не работает refresh от js на сайте
    close_header = driver.find_element_by_class_name("icon-close")
    close_header.click()
    # снова открываем поиск
    search_header.click()
    input_form.clear()
    input_form.send_keys(firm_input)
    page_search = driver.page_source
    soup = BeautifulSoup(page_search, 'lxml')
    list_variant = [{row.get('data-index'): row.get_text()} for row in
                    soup.find_all('div', {'class': 'autocomplete-suggestion'})]
    driver.refresh()
    return list_variant, soup.find_all('div', {'class': 'autocomplete-suggestion'})


def search_news(message, number_firm):
    firm_mask = re.findall(r'\b\w+\b', dbwoker.get_current_property(str(message.chat.id) + str(number_firm)))[1:]
    website = requests.get(f"https://bcs-express.ru/search?q={firm_mask[0]}" + '.').text
    soup = BeautifulSoup(website, 'lxml')
    try:
        news_titles = soup.find_all('a', {'class': 'search-result__item-title'})
        news_anons = soup.find_all('div', {'class': 'search-result__item-anons'})
        news_href = soup.find_all('a', {'class': 'search-result__item-title'})
        news_date = soup.find_all('div', {'class': 'search-result__item-date'})
        df_news = pd.DataFrame(list(zip([row.get_text() for row in news_date],
                                    [row.get_text() for row in news_titles],
                                    [row.get_text() for row in news_anons],
                                    ['https://bcs-express.ru' + row.get('href') for row in news_href])),
                               columns=['Date', 'Заголовок', 'Кратное описание', 'Ссылка'])
    except:
        df_news = list()
    return df_news


pict = [
    'https://forex02.ru/wp-content/uploads/2019/01/CHto-takoe-luchshaya-torgovaya-platforma-dlya-fondovogo-rynka.jpg',
    'https://avatars.mds.yandex.net/get-zen_doc/1576786/pub_5dce3499e161f40e7bb6f7ef_5dce36a51b50cd22ca7b16fc/scale_1200',
    'https://i1.wp.com/prof-trading.ru/wp-content/uploads/2020/05/ris-1-13.jpg',
    'https://custodian.ru/wp-content/uploads/2019/05/CRE_DataFeed-1.jpg',
    'https://i.pinimg.com/originals/bb/db/e0/bbdbe0769c01e7c81ed2957961e8e799.jpg',
    'https://finzona.com/upload/media/entries/2019-10/18/555-entry-0-1571384528.jpg'
]


@bot.message_handler(commands=["info"])
def cmd_info(message):
    bot.send_message(message.chat.id, "Для начала введи название компании. \n"
                                      "Название компании необходимо вводить по правилу:\n"
                                      "1.Если компания российская, то пиши на русском языке\n"
                                      "2.Если компания иностранная, то пиши на английском языке\n"
                                      "3.Исключение для российских компаний,у которых "
                                      "название на английском языке\n"
                                      "3.Если я не знаю компанию, я дам тебе знать.\n"
                                      "Далее я предложу тебе варианты компаний, которые похожи на твой запрос.\n"
                                      "Тебе нужно выбрать вариант из моего списка предложений.\n"
                                      "Если тебе необходимо вернутся в начало - введи /reset \n")


@bot.message_handler(commands=["commands"])
def cmd_commands(message):
    bot.send_message(message.chat.id,
                     "/start - вернет в начало диалога.\n"
                     "/info -  расскажет, что я умею делать.\n"
                     "/list_variant - список всех вариантов поиска по запросу.\n"
                     "/request_news -  запрос новостей по последней выбранной компании.\n"
                     "/reset - вернет тебя в начало поиска по компаниям.\n"
                     "/commands - опишет все доступные команды.\n")


@bot.message_handler(commands=["reset"])
def cmd_reset(message):
    # Удаляем список всех вариантов фирм
    del_list_variant(message, 5)
    # Удаляем выбранный id фирмы
    dbwoker.del_state(str(message.chat.id) + 'firm_id')
    bot.send_message(message.chat.id, "Давай начнем сначала =).\n"
                                      "Введи название компании, которая тебя интересует.\n"
                                      "Используй /info или /commands для дополнительной информации и моих команд.")
    dbwoker.set_state(message.chat.id, conf.States.S_ENTER_FIRM.value)


@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(message.chat.id, "Привет, трейдер! Я новостной телеграмм бот! :) \n"
                                      "Я могу найти последние актуальные новости фондового рынка любой компании!\n"
                                      "Выбери /info и ты получишь подробную информацию.\n"
                                      "Выбери /commands и ты получишь список всех команд.\n"
                                      "Выбери /reset и ты вернешься в начало поиска по компаниям.")
    bot.send_photo(message.chat.id, pict[randint(0, 5)])
    dbwoker.set_state(message.chat.id, conf.States.S_ENTER_FIRM.value)


@bot.message_handler(commands=["list_variant"])
def cmd_commands(message):
    print(get_list_variant(message, 5))
    if get_list_variant(message, 5) != list():
        bot.send_message(message.chat.id,
                     ', '.join([e + '\n' for i, e in enumerate(get_list_variant(message, 5))]).replace('\n,', ',\n'))
        bot.send_message(message.chat.id,  "Вот весь список вариантов по компании. \n"
                                           "Пожалуйста,выбирите числовой номер варианта для предоставления"
                                           "информации.\n "
                                           "Выбрать вариант для вывода новостей? - /request_news \n"
                                           "Выбери /reset и ты вернешься в начало поиска по компаниям.\n")
        # меняем шаг пользователя
        dbwoker.set_state(message.chat.id, conf.States.S_CHOOSE_FIRM.value)
    else:
        bot.send_message(message.chat.id,  "Вы не запрашиали ранее информацию по компании.\n"
                                           "Выбери /reset и ты вернешься в начало поиска по компаниям.\n")


@bot.message_handler(func=lambda message: (dbwoker.get_current_state(message.chat.id) == conf.States.S_ENTER_FIRM.value)
                                          and message.text.strip().lower() not in
                                          ('/reset', '/info', '/start', '/commands', '/request_news'))
def cmd_search_firm(message):
    bot.send_message(message.chat.id, "Запрашиваю информацию у сервера....\n")
    list_firm, soup_file = search_firm(message.text.lower().strip(), driver_bot)
    if list_firm == list():
        bot.send_message(message.chat.id, "Извини, я не знаю такую фирму.Попробуй еще раз.\n"
                                          "Попробуй ввести название компании с заглавной буквы - иногда помогает :) \n"
                                          "Если вы хотите выбрать другую компанию нажмите /reset.\n")
    elif list_firm != list():
        list_firms = [str(index) + str(': ') + str(element.get(str(index))) for index, element in
                      enumerate(list_firm[:5])]
        for row in range(len(list_firms)):
            bot.send_message(message.chat.id, list_firms[row])
            # записываю все варианты в базу
            dbwoker.set_property(str(message.chat.id) + str(row), list_firms[row])
        bot.send_message(message.chat.id, "Пожалуйста,выбирите числовой номер варианта для предоставления информации.\n"
                                          "Если вы хотите выбрать другую компанию нажмите /reset.\n")
        # записывает то, что мы вводим
        dbwoker.set_property(str(message.chat.id) + 'firm_input', message.text.strip())
        # записывает то, что лист всех индексов фирм
        index_firm = [str(index).strip() for index, element in enumerate(list_firm[:5])]
        dbwoker.set_property(str(message.chat.id) + 'firm_list', ', '.join(index_firm))
        # меняем шаг пользователя
        dbwoker.set_state(message.chat.id, conf.States.S_CHOOSE_FIRM.value)
    else:
        bot.send_message(message.chat.id, "Что-то пошло не так...\n"
                                          "Попробуй еще раз отправить запрос. \n"
                                          "Описание моих возможностей на /info.\n"
                                          "Выбери /reset и ты вернешься в начало поиска по компаниям.\n")
    #close_driver(driver_ch)


@bot.message_handler(
    func=lambda message: (dbwoker.get_current_state(message.chat.id) == conf.States.S_CHOOSE_FIRM.value)
                         and message.text.strip().lower() not in
                         ('/reset', '/info', '/start', '/commands', '/request_news', '/list_variant'))
def cmd_choose_firm(message):
    try:
        int(message.text.strip())
        if message.text.strip() in dbwoker.get_current_property(str(message.chat.id) + 'firm_list').split(', '):
            # записывает то, что мы вводим
            dbwoker.set_property(str(message.chat.id) + 'firm_id', message.text.strip())
            bot.send_message(message.chat.id, "Вы выбрали вариант:")
            bot.send_message(message.chat.id, dbwoker.get_current_property(str(message.chat.id) + message.text.strip()))
            bot.send_message(message.chat.id, "Выбрать вариант для вывода новостей? - /request_news \n"
                                              "Если вы хотите выбрать другой вариант - введите число заново. \n"
                                              "Увидеть список всех доступных вариантов - /list_variant \n"
                                              "Если вы хотите выбрать другую компанию нажмите /reset.\n")
        else:
            bot.send_message(message.chat.id, "Вариант вне диапозона.\n"
                                              "Увидеть список всех доступных вариантов - /list_variant \n"
                                              "Если вы хотите выбрать другую компанию нажмите /reset.\n")
    except:
        bot.send_message(message.chat.id, "Похоже Вы ввели буквы. Повторите ввод.\n"
                                          "Если вы хотите выбрать другой вариант,то повторите ввод. \n"
                                          "Увидеть список всех доступных вариантов - /list_variant \n"
                                          "Если вы хотите выбрать другую компанию нажмите /reset.\n")


@bot.message_handler(commands=["request_news"])
def cmd_request_news(message):
    if  dbwoker.get_current_property(str(message.chat.id) + 'firm_id') != False:
        bot.send_message(message.chat.id, "Запрашиваю информацию у сервера....\n")
        get_df = search_news(message, dbwoker.get_current_property(str(message.chat.id) + 'firm_id'))
        if len(get_df) > 0:
            dbwoker.set_state(message.chat.id, conf.States.S_ENTER_NUM_NEWS.value)
            bot.send_message(message.chat.id, "Ура! Я сформировал новости по компании: "
                             + dbwoker.get_current_property(str(message.chat.id) + dbwoker.get_current_property(str(message.chat.id) + 'firm_id'))[3:]
                             + "\n"
                             + "Осталоь совсем немного!\n"
                             + "Введите количество новостей, которое вы хотите вывести на экран. \n"
                             + "Общее количество новостей: " + str(len(get_df)) + "\n")
        else:
            bot.send_message(message.chat.id, "У меня нет новостей по компании: \n"
                             + dbwoker.get_current_property(str(message.chat.id) + dbwoker.get_current_property(str(message.chat.id) + 'firm_id'))[3:]
                             + "\n"
                             + "Для перехода на лист вариантов команий нажмите /list_variant \n"
                             + "Если вы хотите выбрать другую компанию нажмите /reset.\n")
    else:
        bot.send_message(message.chat.id, "Похоже Вы не выбирали вариант для поиска.\n"
                                          "Если вы хотите начать поиск нажмите на /reset.\n")


@bot.message_handler(
    func=lambda message: (dbwoker.get_current_state(message.chat.id) == conf.States.S_ENTER_NUM_NEWS.value)
                         and message.text.strip().lower() not in
                         ('/reset', '/info', '/start', '/commands', '/request_news'))
def cmd_get_news(message):
    try:
        int(message.text.lower().strip())
        get_df = search_news(message, dbwoker.get_current_property(str(message.chat.id) + 'firm_id'))
        if int(message.text.lower().strip()) <= len(get_df):
            if int(message.text.lower().strip()) != 0:
                bot.send_message(message.chat.id, "Формирую новости..... \n")
                get_news = get_df.head(int(message.text.lower().strip()))
                for row in range(len(get_news)):
                    bot.send_message(message.chat.id, "Дата публикации: \n" + str(get_df.iloc[row][0]) + "\n"
                                                      "Заголовок новости: \n" + str(get_df.iloc[row][1]) + "\n"
                                                      "Кратное описание: \n" + str(get_df.iloc[row][2]) + "\n"
                                                      "Ссылка на новость: \n" + str(get_df.iloc[row][3]) + "\n")
                dbwoker.set_state(message.chat.id, conf.States.S_ENTER_END_NEWS.value)
            else:
                bot.send_message(message.chat.id, "Вы ввели 0, а так нельзя... \n"
                                                  "Максимальное количество новостей для вывода - " + str(len(get_df))
                                                  + "\n"
                                                  "Для перехода на лист вариантов команий нажмите /list_variant \n"
                                                  "Если вы хотите выбрать другую компанию нажмите /reset.\n")
        else:
            bot.send_message(message.chat.id, "Вы ввели недопустимое число для вывода новостей \n"
                                              "Максимальное количество новостей для вывода - " + str(len(get_df))
                                              + "\n"
                                              "Для перехода на лист вариантов команий нажмите /list_variant \n"
                                              "Если вы хотите выбрать другую компанию нажмите /reset.\n")
    except:
        bot.send_message(message.chat.id, "Это не похоже на число."
                                          "Для перехода на лист вариантов команий нажмите /list_variant \n"
                                          "Если вы хотите выбрать другую компанию нажмите /reset.\n")


@bot.message_handler(
    func=lambda message: (dbwoker.get_current_state(message.chat.id) == conf.States.S_ENTER_END_NEWS.value)
                         and message.text.strip().lower() not in
                         ('/reset', '/info', '/start', '/commands', '/request_news'))
def cmd_get_news(message):
    bot.send_message(message.chat.id, "Последний Ваш запрос был по компании: \n"
                                      + dbwoker.get_current_property(str(message.chat.id) + dbwoker.get_current_property(str(message.chat.id) + 'firm_id'))[3:]
                                      + "\n"
                                      + "Увидеть список всех доступных вариантов - /list_variant \n"
                                      + "Начать поиск новостей по текущей выбранной компании /request_news.\n"
                                      + "Если вы хотите выбрать другую компанию нажмите /reset.\n")
    bot.send_message(message.chat.id, "Для перехода на лист вариантов команий нажмите /list_variant \n"
                                       "Если вы хотите выбрать другую компанию нажмите /reset.\n")


if __name__ == '__main__':
    bot.infinity_polling()
