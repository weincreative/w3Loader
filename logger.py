from urllib import response
import config,requests

token = config._telegramTokenMain

#TELEGRAM CHANNEL MESSAGE
def sendMsg(text,mes):
    if mes == '0':
        chatId = config._telegramBotMainReceiver_id
        url_req = "https://api.telegram.org/bot"+ str(token) +"/sendMessage" + "?chat_id=" + str(chatId) + "&text=" + str(text)
        result = requests.get(url_req)
    if mes == '1':
        chatId = config._telegramBotMainReceiver_id
        url_req = "https://api.telegram.org/bot"+ str(token) +"/sendMessage" + "?chat_id=" + str(chatId) + "&text=" + str(text)
        result = requests.get(url_req)
    if mes == '3':
        chatId = config._telegramBotMainReceiver_id
        url_req = "https://api.telegram.org/bot"+ str(token) +"/sendMessage" + "?chat_id=1771772162&text=" + str(text)
        result = requests.get(url_req)    