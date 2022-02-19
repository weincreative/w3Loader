#coding:utf-8
import os
import sys
import random
import pandas as pd
import ccxt
import time
import sqlite3
import requests
from bs4 import BeautifulSoup as bs
import pytz
from pytz import timezone
from datetime import datetime
import subprocess

#https://github.com/ccxt/ccxt
#pip install -r requirements.txt 
#python -m pip install --upgrade pip
#pyinstaller --onefile -w whenLambo.py

#Attributes
USERCONTROL = ""
_APPID = "ADMIN"
_APPMAIL = ""
_APPTC = ""
_APPENDDAY = ""
_APPCOINCOUNT = ""
_APPUSERFIRSTDAY = ""
_APPTELEGRAMMAINTOKENBASE = ""
_APPTELEGRAMMAINTOKEN = ""
_APPTELEGRAMMAINID = ""
_APPTELEGRAMUSERID = ""
_APPAPIKEY = ""
_APPSECRETKEY = ""
_APPCOINS = ""
_APPTOPUSDT = ""
_APPSERVERNAME = ""
_APPLEVERAGE = ""
_APPBASEORDER = ""
_APPSAFEORDER = ""
_APPMAXORDERSIZE = ""

tenMinLoginFT = False
telegramSendingUser = False
telegramSendingAdmin = False

#Colors
class color:
    HEADER = '\033[95m'
    IMPORTANT = '\33[35m'
    NOTICE = '\033[33m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    LOGGING = '\33[34m'
    END = '\033[0m'

#Random Color
color_random=[color.HEADER,color.IMPORTANT,
              color.NOTICE,color.OKBLUE,
              color.OKGREEN,color.WARNING,
              color.RED,color.LOGGING]
random.shuffle(color_random)

#Bot Logo
venBot_Logo = color_random[0] +'''

        ██╗   ██╗███████╗███╗   ██╗██████╗  ██████╗ ████████╗
        ██║   ██║██╔════╝████╗  ██║██╔══██╗██╔═══██╗╚══██╔══╝
        ██║   ██║█████╗  ██╔██╗ ██║██████╔╝██║   ██║   ██║   
        ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║██╔══██╗██║   ██║   ██║   
         ╚████╔╝ ███████╗██║ ╚████║██████╔╝╚██████╔╝   ██║   
          ╚═══╝  ╚══════╝╚═╝  ╚═══╝╚═════╝  ╚═════╝    ╚═╝   

'''

#Telegram Message ADMIN
def sendMainTELEMsg(text,_token1,_token2,_receiver,time):
    try:
        _teleToken=f"{_token1}:{_token2}"
        url_req=f"https://api.telegram.org/bot{_teleToken}/sendMessage?chat_id={_receiver}&text={text}"
        #result=requests.get(url_req)    
    except Exception as Error:
        services.execute(f"INSERT INTO consoleLog VALUES (null, {Error}, {time})")
        connection.commit()
        time.sleep(1)
        
#Telegram Message User
def sendUserTELEMsg(text,_token1,_token2,_receiver,time):
    try:
        _teleToken=f"{_token1}:{_token2}"
        url_req=f"https://api.telegram.org/bot{_teleToken}/sendMessage?chat_id={_receiver}&text={text}"
        #result=requests.get(url_req)    
    except Exception as Error:
        services.execute(f"INSERT INTO consoleLog VALUES (null, {Error}, {time})")
        connection.commit()
        time.sleep(1)
        
#Create DataBase       
def createBotDB():
    services.execute("CREATE TABLE IF NOT EXISTS optiOns (tid INTEGER PRIMARY KEY AUTOINCREMENT, APPID VARCHAR, APPMAIL VARCHAR, APPTC VARCHAR, APPENDDAY VARCHAR, APPCOINCOUNT VARCHAR, APPUSERFIRSTDAY VARCHAR, APPTELEGRAMMAINTOKENBASE VARCHAR, APPTELEGRAMMAINTOKEN VARCHAR, APPTELEGRAMMAINID VARCHAR, APPTELEGRAMUSERID VARCHAR, APPAPIKEY VARCHAR, APPSECRETKEY VARCHAR, APPCOINS VARCHAR, APPTOPUSDT VARCHAR, APPSERVERNAME VARCHAR, APPLEVERAGE VARCHAR, APPBASEORDER VARCHAR, APPSAFEORDER VARCHAR, APPMAXORDERSIZE VARCHAR)")
    services.execute("CREATE TABLE IF NOT EXISTS coinRunner (tid INTEGER PRIMARY KEY AUTOINCREMENT, symBil VARCHAR, leverAge VARCHAR, maxMargin VARCHAR, startTime DATETIME, finishTime DATETIME, coinStatus VARCHAR)")
    services.execute("CREATE TABLE IF NOT EXISTS activeOrder (tid INTEGER PRIMARY KEY AUTOINCREMENT, orderSymbol VARCHAR, orderStartPrice VARCHAR, orderEndPrice VARCHAR, positionSide VARCHAR, origQty VARCHAR, orderFillTime DATETIME, active VARCHAR)")
    services.execute("CREATE TABLE IF NOT EXISTS orderHistory (tid INTEGER PRIMARY KEY AUTOINCREMENT, orderSymbol VARCHAR, orderStartPrice VARCHAR, orderEndPrice VARCHAR, positionSide VARCHAR, origQty VARCHAR, takeProfit VARCHAR, orderFillTime DATETIME, active VARCHAR)")
    services.execute("CREATE TABLE IF NOT EXISTS consoleLog (tid INTEGER PRIMARY KEY AUTOINCREMENT, executeCode VARCHAR, dateTimeCode DATETIME)")
    services.execute("CREATE TABLE IF NOT EXISTS toplamValletUSDT (tid INTEGER PRIMARY KEY AUTOINCREMENT, valueMaxMargin VARCHAR)")
    connection.commit()

#Day Win Score Coin List    
def SelectKazancProfit(KTime):
    firstKTime=f"{KTime} 00:00:01"
    secondKTime=f"{KTime} 23:59:59"
    services.execute(f"SELECT orderSymbol, ROUND(CAST((count(tid)*0.50) as DOUBLE),2) AS VERI FROM activeOrder WHERE active = '0' and orderFillTime >= '{firstKTime}' and orderFillTime <= '{secondKTime}' GROUP BY orderSymbol ORDER BY VERI DESC")
    rows=services.fetchall()
    for row in rows:
        Kazanc.append(f"{row[0]}:{row[1]}") 

#Day Win Score USDT
def SelectDayWin(KTime):
    firstKTime=f"{KTime} 00:00:01"
    secondKTime=f"{KTime} 23:59:59"
    services.execute(f"SELECT ROUND(CAST((count(tid)*0.50) as DOUBLE),2) FROM activeOrder WHERE active = '0' AND orderFillTime >= '{firstKTime}' AND orderFillTime <= '{secondKTime}' ")
    rows=services.fetchall()
    for row in rows:
        DAYWINUSDT.append(f"{row[0]}")
        
#Full Wallet TOP USDT        
def SelectMaxMargin():
    services.execute(f"SELECT ROUND(SUM(CAST(valueMaxMargin as DOUBLE)),2) FROM toplamValletUSDT")
    rows=services.fetchall()
    for row in rows:
        TOPUSDT.append(f"{row[0]}")


print(venBot_Logo)
while True:
    try:
        #https://github.com/weincreative/w3Loader/blob/main/Authorization
        #Loop Attributes
        Kazanc = []
        TOPUSDT = []
        DAYWINUSDT = []
        USERCONTROL = ""
        
        #TR CurrenTime And ZRaporTime
        utc_now = datetime.utcnow()
        utc = pytz.timezone('UTC')
        aware_date = utc.localize(utc_now)
        turkey = timezone('Europe/Istanbul')
        current_time = aware_date.astimezone(turkey).strftime('%d-%m-%Y %H:%M:%S')
        current_day = aware_date.astimezone(turkey).strftime('%d-%m-%Y')
        daylyZ = aware_date.astimezone(turkey).strftime('%H:%M')
        hourlyZ = aware_date.astimezone(turkey).strftime('%M')
        tenMinLogin = aware_date.astimezone(turkey).strftime('%M')
        
        #Create and Login DataBase
        connection=sqlite3.connect(f"venBot-{_APPID}.db")
        services=connection.cursor()
        createBotDB()
        
        #GitHub Authorization
        url=f"https://github.com/weincreative/w3Loader/blob/main/Authorization"
        soup=bs(requests.get(url).content, "html.parser")    
        for row in soup.find("table").find_all("tr"):
            tds=row.find_all("td")
            exracter = tds[1].text.strip().split(":")
            USERCONTROL = exracter[0].strip()
            if USERCONTROL == _APPID:
                if int(tenMinLogin) % 10 == 0:
                    tenMinLoginFT = False
                if tenMinLoginFT == False:
                    _APPMAIL = exracter[1].strip()
                    _APPTC = exracter[2].strip()
                    _APPENDDAY = exracter[3].strip()
                    _APPCOINCOUNT = exracter[4].strip()
                    _APPUSERFIRSTDAY = exracter[5].strip()
                    _APPTELEGRAMMAINTOKENBASE = exracter[6].strip()
                    _APPTELEGRAMMAINTOKEN = exracter[7].strip()
                    _APPTELEGRAMMAINID = exracter[8].strip()
                    _APPTELEGRAMUSERID = exracter[9].strip()
                    _APPAPIKEY = exracter[10].strip()
                    _APPSECRETKEY = exracter[11].strip()
                    _APPCOINS = exracter[12].strip()
                    _APPTOPUSDT = exracter[13].strip()
                    _APPSERVERNAME = exracter[14].strip()
                    _APPLEVERAGE = exracter[15].strip()
                    _APPBASEORDER = exracter[16].strip()
                    _APPSAFEORDER = exracter[17].strip()
                    _APPMAXORDERSIZE = exracter[18].strip()
                    services.execute(f"INSERT INTO optiOns VALUES (null, '{_APPID}', '{_APPMAIL}', '{_APPTC}', '{_APPENDDAY}', '{_APPCOINCOUNT}', '{_APPUSERFIRSTDAY}', '{_APPTELEGRAMMAINTOKENBASE}', '{_APPTELEGRAMMAINTOKEN}', '{_APPTELEGRAMMAINID}', '{_APPTELEGRAMUSERID}', '{_APPAPIKEY}', '{_APPSECRETKEY}', '{_APPCOINS}', '{_APPTOPUSDT}', '{_APPSERVERNAME}', '{_APPLEVERAGE}', '{_APPBASEORDER}', '{_APPSAFEORDER}', '{_APPMAXORDERSIZE}')")
                    connection.commit()
                    print(f"User: {_APPID} Started..")
                    
                    #Runner.sh Writer
                    with open('runner.sh','w') as file_object:
                        controller = int(_APPCOINCOUNT)-1
                        file_object.write("#!/bin/bash"+"\n")
                        exracterCoin = _APPCOINS.split(",")
                        for exCoinSymbol in exracterCoin:
                            if controller != 1 and controller != 0:
                                file_object.write(f"python3 whenLambo.py -sx {exCoinSymbol} -lx {_APPLEVERAGE} -bx {_APPBASEORDER} -sbx {_APPSAFEORDER} -stx {_APPMAXORDERSIZE} &"+"\n")
                                services.execute(f"INSERT INTO coinRunner VALUES (null, '{exCoinSymbol}', '{_APPLEVERAGE}', '{_APPMAXORDERSIZE}', '{current_time}', null, 'READY')")
                                connection.commit()
                                controller -= 1
                            else:
                                file_object.write(f"python3 whenLambo.py -sx {exCoinSymbol} -lx {_APPLEVERAGE} -bx {_APPBASEORDER} -sbx {_APPSAFEORDER} -stx {_APPMAXORDERSIZE}")
                                services.execute(f"INSERT INTO coinRunner VALUES (null, '{exCoinSymbol}', '{_APPLEVERAGE}', '{_APPMAXORDERSIZE}', '{current_time}', null, 'READY')")
                                connection.commit()
                                controller -= 1
                                if controller == 0:
                                    tenMinLoginFT = True
                                    break
        
        #https://stackoverflow.com/questions/3777301/how-to-call-a-shell-script-from-python-code
        #if tenMinLoginFT == True:
            #os.system('sh runner.sh')
            #subprocess.run(["start", "cmd", "/K", "runner.sh"], shell=True)
            #subprocess.run('runner.sh',shell=True)
            #subprocess.call(['sh', './runner.sh'])
            #import shlex
            #subprocess.call(shlex.split('./test.sh param1 param2'))
            #subprocess.call(shlex.split(f"./test.sh param1 {your_python_var} param3"))
            #subprocess.Popen(['runner.sh'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        #ZRapor DB SELECT
        SelectKazancProfit(current_day)
        SelectDayWin(current_day)
        SelectMaxMargin()
        
        #User Hourly ZRapor
        for x in Kazanc:
            time.sleep(1)
            if(x != "" and str(hourlyZ) == '59' and telegramSendingUser == False):
                print(f"{current_time}\n::::::::: SAATLIK Z RAPORU ::::::::: \n _______________________________ \nTOPLAM CÜZDAN USDT MİKTARI = {TOPUSDT[0]}$ \nBUGÜN KAZANILAN TOPLAM USDT : {DAYWINUSDT[0]}$ \n _______________________________ \n:: BUGÜN KAZANILAN COIN BAZINDA DÖKÜMÜ :: \n{Kazanc}")
                sendUserTELEMsg(f"::::::::: SAATLIK Z RAPORU ::::::::: \n _______________________________ \nTOPLAM CÜZDAN USDT MİKTARI = {TOPUSDT[0]}$ \nBUGÜN KAZANILAN TOPLAM USDT : {DAYWINUSDT[0]}$ \n _______________________________ \n:: BUGÜN KAZANILAN COIN BAZINDA DÖKÜMÜ :: \n{Kazanc}",_APPTELEGRAMMAINTOKENBASE,_APPTELEGRAMMAINTOKEN,_APPTELEGRAMUSERID,current_time)
                telegramSendingUser = True
                Kazanc.clear()
            if(x != "" and str(hourlyZ) == '00' and telegramSendingUser == True):
                telegramSendingUser = False
            
        #ADMIN Daily ZRapor
        for y in Kazanc:
            time.sleep(1)
            if(y != "" and str(daylyZ) == '23:57' and telegramSendingAdmin == False):
                print(f"{current_time}\n::::::::: SAATLIK Z RAPORU ::::::::: \n _______________________________ \nTOPLAM CÜZDAN USDT MİKTARI = {TOPUSDT[0]}$ \nBUGÜN KAZANILAN TOPLAM USDT : {DAYWINUSDT[0]}$ \n _______________________________ \n:: BUGÜN KAZANILAN COIN BAZINDA DÖKÜMÜ :: \n{Kazanc}")
                sendMainTELEMsg(f"::::::::: SAATLIK Z RAPORU ::::::::: \n _______________________________ \nTOPLAM CÜZDAN USDT MİKTARI = {TOPUSDT[0]}$ \nBUGÜN KAZANILAN TOPLAM USDT : {DAYWINUSDT[0]}$ \n _______________________________ \n:: BUGÜN KAZANILAN COIN BAZINDA DÖKÜMÜ :: \n{Kazanc}",_APPTELEGRAMMAINTOKENBASE,_APPTELEGRAMMAINTOKEN,_APPTELEGRAMMAINID,current_time)
                telegramSendingAdmin = True
                Kazanc.clear()
            if(y != "" and str(daylyZ) == '23:58' and telegramSendingAdmin == True):
                telegramSendingAdmin = False   
                    
    except Exception as Error:
        print(f"[ERROR] : {Error}")
        services.execute(f"INSERT INTO consoleLog VALUES (null,'{Error}','{current_time}')")
        connection.commit()
        time.sleep(20)
        continue 
