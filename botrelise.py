from bs4 import BeautifulSoup as bs
import matplotlib.pyplot as plt
import yfinance as yf
import requests
import telebot
import os

# Enabling the bot
bot = telebot.TeleBot(os.environ["TOKEN"])
headers = {}
headers[os.environ["USER_AGENT"]] = os.environ["USER_VALUE"]
headers[os.environ["ACCEPT"]] = os.environ["ACCEPT_VALUE"]

def make_ticker(message):
    ticker = str(message.text.upper())
    return ticker

def create_url(message):
    new_list_url = []  # Entering variables for data storage
    list_url = [os.environ["USA"], os.environ["RU"], os.environ["FI"], os.environ["XE"], os.environ["ES"],
                os.environ["UK"],  os.environ["FR"], os.environ["PT"], os.environ["DK"], os.environ["SE"],
                os.environ["NG"], os.environ["CN"],  os.environ["HK"], os.environ["JP"], os.environ["CA"]]
    ticker = make_ticker(message)
    url_with_ticker = [new_list_url.append(url + ticker + os.environ["END_URL"]) for url in list_url]
    return new_list_url

def create_dict_parse(message):
    dict_parse, soup = {}, ''
    new_list_url = create_url(message)
    session = requests.Session()
    for url in new_list_url:  # Check the content of the soup from the links
        request = session.get(url, headers=headers)
        soup = bs(request.content, 'html.parser')
        if str(soup).find('cr_financials_ratios module') > 0:
            dict_parse[url] = soup
    return dict_parse

def create_doc(message):
    ticker, dict_for_make_doc, dict_parse = create_chart(message)
    if dict_for_make_doc and dict_parse is not None:
        for name_comp, soup in dict_for_make_doc.items():
            # Parsing information about the company
            name_exc = soup.find('div', class_='cr_quotesHeader').find('span', class_='exchangeName').text  # Name Exchange
            curr_time = soup.find('div', class_='charts-datacol').find('h5').text                           # Current time
            curr_price = soup.find('div', class_='charts-datacol').find('span', class_='curr_price').text   # Current price
            open_pr = soup.find('div', class_='cr_compare_data').find('li').text                            # Opening price

            # Collecting General information about the company
            name_company = '*' * 19 + 'General information' + '*' * 19 + '\n' +'Company name:  ' + str(name_comp.strip()) + '\n'
            name_exchange = 'Ticker and exchange:  ' + ticker + ' ' + str(name_exc.strip()) + '\n'
            current_time = 'Time:  ' + str(curr_time.strip()) + '\n'
            current_price = 'Current price:  ' + str(curr_price.strip()) + '\n'
            open_price = str(open_pr.strip()) + '\n' * 2 + '*' * 17 + 'Financials information' + '*' * 18 + '\n' * 2

            # Parsing financial data
            in_come = soup.find('table', class_={'cr_financials_table'})
            net_come_title = in_come.find('td', class_={'data_lbl'}).text
            net_come_value = in_come.find('td', class_={'data_data'}).text
            title_multi = soup.find('div', class_={'cr_financials_ratios module'})
            title_mind = title_multi.find_all('div', class_={'cr_data'})
            net_income = str(net_come_title) + " (Quarterly):  " + str(net_come_value) + '\n' * 2

            bot.send_message(message.from_user.id, "Create Statement for " + str(name_comp) + " company...")
            general_info = name_company + name_exchange + current_time + current_price + open_price + net_income

            # Writing data to a file
            with open('Statement ' + name_comp + '.txt', 'w', encoding='utf-8') as doc:
                doc.write(general_info)
                numV = 0
                for v in title_mind:
                    numV = numV + 1
                    if numV != 1:
                        NameTab = v.find('h4')
                        v1 = str(NameTab.text.strip()) + ':\n'
                        doc.write(v1)
                        v2 = v.find_all('td')
                        for v3 in v2:
                            v4 = v3.find_all('span')
                            prov, stroka_tab, strok = '', '', ''
                            for v5 in v4:
                                v55 = v5.text.strip()
                                if prov != v55:
                                    stroka_tab = stroka_tab + v55 + ':  '
                                    strok = stroka_tab.strip(':  ')
                                    prov = v55
                            doc.write(strok + '\n')
                        doc.write('\n' + '*' * 57 + '\n' + '\n')

            # Sending a file with financial data
            with open('Statement ' + name_comp + '.txt', 'rb') as doc:
                bot.send_document(message.from_user.id, doc)
            # After sending the file, delete it
            os.remove('Statement ' + name_comp + '.txt')
        bot.send_message(message.from_user.id, "If you need anything else, you need only send '/start' again!")
    else:
        bot.send_message(message.from_user.id, "Ticker (" + ticker + ") is not correct, try command '/start' again!")

def create_chart(message):
    ticker = make_ticker(message)
    bot.send_message(message.from_user.id, "Search a ticker (" + ticker + ")")
    dict_parse = create_dict_parse(message)
    dict_for_make_doc = {}
    for url, soup in dict_parse.items():
        name_comp = soup.find('div', class_='cr_quotesHeader').find('span', class_='companyName').text
        dict_for_make_doc[name_comp] = soup
        if url == os.environ["RU"] + ticker + os.environ["END_URL"]:
            chart_ticker = ticker + ".ME"
        elif url != os.environ["RU"] + ticker + os.environ["END_URL"]:
            chart_ticker = ticker
        bot.send_message(message.from_user.id, "Create chart for " + str(name_comp) + " company...")
        plt.switch_backend('agg')
        data = yf.download(chart_ticker, period='3y')
        data['Adj Close'].plot()
        plt.title(str(name_comp), fontsize=15, color='blue')
        plt.savefig(str(name_comp) + '.png', bbox_inches='tight', dpi=282)
        plt.clf()
        # Sending a chart
        with open(str(name_comp) + '.png', 'rb') as stock_data:
            bot.send_photo(message.from_user.id, stock_data)
        # Deleting a chart
        os.remove(str(name_comp) + '.png')
    return ticker, dict_for_make_doc, dict_parse

@bot.message_handler(commands=['start']) # Greeting
def begin(message):
    bot.send_message(message.from_user.id, 'Enter ticker company')  # We ask the user to enter the Ticker after the start command
    bot.register_next_step_handler(message, create_url)

@bot.message_handler(commands=['info']) # Information about multipliers
def info(message):
    bot.send_message(message.from_user.id,  "P/E: p/e < 0 loss; 0 < p/e < 5 underestimate;" + '\n'
                                            "P/S: p/s < 1 underestimate;" + '\n'
                                            "EV/EBITDA: ev/ebitda < 5 underestimate;" + '\n'
                                            "P/BC: p/bv < 1 underestimate; p/bv > 1 overestimate;" + '\n'
                                            "P/CF: 3 < p/cf < 15 underestimate;" + '\n'
                                            "DEBT/EBITDA: debt/ebitda <= 5" + '\n'
                                            "ROE: The more the better" + '\n')


bot.polling(none_stop=True, interval=0, timeout=20)




