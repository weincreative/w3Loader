#coding:utf-8
#https://github.com/ccxt/ccxt
#pip install -r requirements.txt 
#python -m pip install --upgrade pip
#pyinstaller --onefile -w whenLambo.py
import os
import random
import sqlite3
import config
import pandas as pd
import ccxt
import time
#import winsound
import requests
from bs4 import BeautifulSoup as bs
import logger
import argparse
import numpy as np
from datetime import datetime
import urllib3

def internetOn():
    try:
        url = "https://google.com/"
        soup = bs(requests.get(url).content, "html.parser")
        if soup != "":
            return True
    except Exception as Error:
        return False

#print(datetime.fromtimestamp(1644752404953/1000))

duration = 4000  # milliseconds
freq = 550  # Hz
proxies = []

def get_free_proxies():
    url = "https://free-proxy-list.net/"
    #http://free-proxy.cz/en/proxylist/country/all/https/ping/level3
    soup = bs(requests.get(url).content, "html.parser")
    for row in soup.find("table", attrs={"class": "table table-striped table-bordered"}).find_all("tr")[1:]:
        tds = row.find_all("td")
        try:
            ip = tds[0].text.strip()
            port = tds[1].text.strip()
            host = f"{ip}:{port}"
            proxies.append(host)
        except IndexError:
            continue
    return proxies

def get_session():
    session = requests.Session()
    proxy = random.choice(proxies)
    session.proxies = {"https": proxy} #{"http": proxy, "https": proxy}
    return session

parser = argparse.ArgumentParser(description='koinler')
parser.add_argument('-sx','--symblx',type=str,default='blz')
parser.add_argument('-lx','--leverx',type=float,default=20.0)
parser.add_argument('-bx','--basex',type=float,default=1.0)
parser.add_argument('-sbx','--safeBasex',type=float,default=2.0)
parser.add_argument('-stx','--maxSafeTradex',type=float,default=500.0)
args = parser.parse_args()

#py test5.py -sx band -lx 20 -bx 1 -sbx 2 -stx 3000
# SETTİNGS
symbolName = (args.symblx).upper()
leverage = float(args.leverx) # kaldıracı binanceden ayarlamalısın
baseOrderSize = float(args.basex)#float(input("Base Order Size: ")) # emir büyüklüğü
safetyOrderSize = float(args.safeBasex)#float(input("Safety Order Size: ")) # sonra ki emirlerin kaçar kaçar açılacağı
maxSafetyTradesCount = float(args.maxSafeTradex) # maximum kaç işleme giricek sınırı
priceDeviation = float(0.55)#float(input("Price Deviation %: ")) # yüzde kaç düştükçe yada yükseldikçe alım yapsın
safetyOrderStepScale = float(2)#float(input("Safety Order Step Scale: ")) # alım yaptıktan sonra ki alımları kaça katlayarak yüzdelerini alımlara devam edeceğini belirt
safetyOrderVolumeScale = float(2)#float(input("Safety Order Volume Scale: ")) # ilk alımlarını yaptıktan sonra margin büyüklüğünü hep katlaması gereken sayı
positionSide = float(3)#float(input("Position Side = Only Long(1) - Only Short(2) - Long and Short(3): ")) # pozisyon yönü
takeProfit = float(0.55)#float(input("Take Profit %: ")) # alımlarını satacağı yer yüzde
stopLoss = float(0)#float(input("Stop Loss %: ")) # kayıp önleme için kod
#os.system("title " + symbolName)

#DATABASE
def createBotDB():
    services.execute("CREATE TABLE IF NOT EXISTS coinRunner (tid INTEGER PRIMARY KEY AUTOINCREMENT, xsymbol VARCHAR, xleverage VARCHAR, maxMargin VARCHAR, startTime DATETIME, finishTime DATETIME, xstatus VARCHAR)")
    services.execute("CREATE TABLE IF NOT EXISTS activeOrder (tid INTEGER PRIMARY KEY AUTOINCREMENT, orderSymbol VARCHAR, orderStartPrice VARCHAR, orderEndPrice VARCHAR, positionSide VARCHAR, origQty VARCHAR, orderFillTime DATETIME, active VARCHAR)")
    services.execute("CREATE TABLE IF NOT EXISTS orderHistory (tid INTEGER PRIMARY KEY AUTOINCREMENT, orderSymbol VARCHAR, orderStartPrice VARCHAR, orderEndPrice VARCHAR, positionSide VARCHAR, orderTradeCount VARCHAR, origQty VARCHAR, takeProfit VARCHAR, orderFillTime DATETIME)")
    services.execute("CREATE TABLE IF NOT EXISTS consoleLog (tid INTEGER PRIMARY KEY AUTOINCREMENT, executeCode VARCHAR, dateTimeCode DATETIME)")
    services.execute("CREATE TABLE IF NOT EXISTS toplamValletUSDT (tid INTEGER PRIMARY KEY AUTOINCREMENT, valueMaxMargin VARCHAR)")
    connection.commit()

def SelectLongTakeProfit(symbly,side):
    services.execute(f"SELECT tid, orderEndPrice, origQty, active, orderStartPrice FROM activeOrder WHERE positionSide = '{side}' and orderSymbol = '{symbly}' and active = '1' ")
    rows=services.fetchall()
    for row in rows:
        if(side=="LONG"):
            LongCoins.append(f"{row[0]}:{row[1]}:{row[2]}:{row[3]}:{row[4]}")

def SelectShortTakeProfit(symbly,side):
    services.execute(f"SELECT tid, orderEndPrice, origQty, active, orderStartPrice FROM activeOrder WHERE positionSide = '{side}' and orderSymbol = '{symbly}' and active = '1' ")
    rows=services.fetchall()
    for row in rows:
        if(side=="SHORT"):
            ShortCoins.append(f"{row[0]}:{row[1]}:{row[2]}:{row[3]}:{row[4]}") 
        
def SelectMaxMargin():
    services.execute(f"SELECT ROUND(SUM(CAST(valueMaxMargin as DOUBLE)),2) FROM toplamValletUSDT")
    rows=services.fetchall()
    for row in rows:
        TOPUSDT.append(f"{row[0]}")

def endBuy(symbly): 
    services.execute(f"SELECT COALESCE(max(tid),'0'),COALESCE(orderStartPrice,'0.0') FROM activeOrder WHERE active = 1 and orderSymbol = '{symbly}' ")
    services.execute(f"SELECT COALESCE(max(t1.tid),'0')AS MAXTID,COALESCE(t1.orderStartPrice,'0.0')as STARTPRICE, (SELECT count(tid) FROM activeOrder WHERE active = 1 AND positionSide = 'LONG' AND orderSymbol = t1.orderSymbol)AS LONG, (SELECT count(tid) FROM activeOrder WHERE active = 1 AND positionSide = 'SHORT' AND orderSymbol = t1.orderSymbol)AS SHORT FROM activeOrder t1 WHERE t1.active = 1 and t1.orderSymbol = '{symbly}' ")
    rows=services.fetchall()
    for row in rows:
        if row[0] != "0":
            endBuyMAX.append(f"{row[1]}:{row[2]}:{row[3]}")
        else:
            endBuyMAX.append(f"0")      
            
def sorEntryPrice(symbl,side):
    balance = exchange.fetch_balance()
    free_balance = exchange.fetch_free_balance()
    positions = balance['info']['positions']
    current_positions = [position for position in positions if float(position['positionAmt']) != 0 and position['symbol'] == symbl and position['positionSide'] == side]
    position_info = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
    #aldimEntryPrice.append(float(position_info["entryPrice"][len(position_info.index) - 1]))
                           
#ATTRIBUTES
first = True
LongCoins = []
ShortCoins = []
TOPUSDT = []
endBuyMAX = []
aldimEntryPrice = []
tradeLongCount = 1
tradeShortCount = 1
symbol = symbolName+"/USDT"
commision = 0.0360

#DATABASE
connection=sqlite3.connect(f'venBot-ADMIN.db')
services=connection.cursor()
createBotDB()

# API CONNECT
exchange = ccxt.binance({
"apiKey": config.apiKey,
"secret": config.secretKey,
'options': {
'defaultType': 'future'
},
'enableRateLimit': True
})
while True:
    try:
        #NOW TIME
        nowt = time.localtime()
        current_time = time.strftime("%d-%m-%Y %H:%M:%S", nowt)   #'%Y-%m-%d %H:%M:%S
        time.sleep(1)
        while internetOn() == False: 
            print("[HATA] : Internet baglantiniz gitmistir, lutfen baglantinizi kontrol ediniz")
            services.execute(f"INSERT INTO consoleLog VALUES (null,'{Error}','{current_time}')")
            connection.commit()
            time.sleep(30)
            if internetOn() == True:
                break
        
        #        get_free_proxies()
        #        e = get_session()        
        #        exchange = ccxt.binance({
        #        "apiKey": config.apiKey,
        #        "secret": config.secretKey,
        #        'options': {
        #        'defaultType': 'future'
        #        },
        #        'proxies': e.proxies,
        #        'enableRateLimit': True
        #        })
        #        
        #        for i in range(len(proxies)):
        #            s = get_session(proxies)
        #            try:
        #                print("Request page with IP:", s.get("http://icanhazip.com", timeout=1.5).text.strip())
        #            except Exception as e:
        #                continue
        
        #LOOP ATTRIBUTES
        #https://github.com/ccxt/ccxt/wiki/Manual#querying-orders
        newSymbol = f"{symbolName}USDT"
        balance = exchange.fetch_balance()
        free_balance = exchange.fetch_free_balance()
        orders = np.array(exchange.fetchClosedOrders(symbol))
        #leverageControl = exchange.fapiPrivate_post_leverage({"symbol": newSymbol,"leverage": int(leverage),})
        #marginSideControl = exchange.fapiPrivatePostMarginType ({"symbol": newSymbol,"marginType": 'CROSSED',})
        positions = balance['info']['positions']
        current_positions = [position for position in positions if float(position['positionAmt']) != 0 and position['symbol'] == symbol ]
        time.sleep(1)
        position_info = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
        
        #LOAD BARS
        try:
            bars = exchange.fetch_ohlcv(newSymbol, timeframe="1m", since = None, limit = 1)
        except Exception as Error:
            print (f"[HATA] : Message:{Error}")
            time.sleep(3)
            continue
        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
        
        LongCoins = []
        ShortCoins = []
        TOPUSDT=[]
        SelectLongTakeProfit(newSymbol,"LONG")
        SelectShortTakeProfit(newSymbol,"SHORT")
        SelectMaxMargin()
        endBuy(newSymbol)
        
        # Starting price
        if first:
            if endBuyMAX[0] != "0":
                exCo=endBuyMAX[0].split(":")
                firstPrice = float(exCo[0])
                tradeLongCount = int(exCo[1])
                tradeShortCount = int(exCo[2])
            else:
                firstPrice = float(df["close"][len(df.index) - 1])
            #print("(*) FirstPrice: ",firstPrice," Free Usdt: ", round(float(free_balance["USDT"]),2), " Total Money: ", round(float(balance['total']["USDT"]),2))
            first = False
        endBuyMAX = []
        currentPrice = float(df["close"][len(df.index) - 1])

        # LONG ENTER
        def longEnter(amountx):
            order = exchange.create_order(symbol=symbol, amount=amountx, side='BUY', type='MARKET', params={'positionSide': 'LONG'})
            #winsound.Beep(freq, duration)
            
        # LONG EXIT
        def longExit(amountx):
            order = exchange.create_order(symbol=symbol, amount=amountx, side='SELL', type='MARKET', params={'positionSide': 'LONG'})

        # SHORT ENTER
        def shortEnter(amountx):
            order = exchange.create_order(symbol=symbol, amount=amountx, side='SELL', type='MARKET', params={'positionSide': 'SHORT'})
            #winsound.Beep(freq, duration)
            
        # SHORT EXIT
        def shortExit(amountx):
            order = exchange.create_order(symbol=symbol, amount=amountx, side='BUY', type='MARKET', params={'positionSide': 'SHORT'})

        # LONG ENTER
        #float(free_balance["USDT"]) >= baseOrderSize
        if firstPrice - (firstPrice/100) * priceDeviation >= currentPrice and maxSafetyTradesCount>tradeLongCount and (positionSide == 1 or positionSide == 3):
            posSideTxt="LONG"
            if (tradeLongCount % 3 == 0):
                alinacak_miktar = ((baseOrderSize * safetyOrderSize)* float(leverage)) / float(df["close"][len(df.index) - 1])         
                #longEnter(alinacak_miktar)
                #sorEntryPrice(newSymbol,posSideTxt)
                #if len(aldimEntryPrice[0]) > 0:
                #    print(aldimEntryPrice[0])
                print(f"{newSymbol}: LONG ENTER : BuyPrice:{currentPrice}, tradeCount:{tradeLongCount}")
                services.execute(f"INSERT INTO activeOrder VALUES (null, '{newSymbol}', '{currentPrice}', '{((currentPrice / 100) * priceDeviation) + currentPrice}', '{posSideTxt}', '{alinacak_miktar}', '{current_time}','1')")
                connection.commit()
                first = True
                #logger.sendMsg(('::BUY::\n'+str(current_time)+'\nCoinSembol: '+str(newSymbol)+'_'+str(leverage)+'X'+'\nLONG ENTER'+'\nMiktar: '+str(alinacak_miktar)+'\nTradeCount: '+str(tradeCount)+'\nPriceDeviation: '+str(priceDeviation)),'0')
                tradeLongCount += 1
                alinacak_miktar = 0
            else:
                alinacak_miktar = (baseOrderSize * float(leverage)) / float(df["close"][len(df.index) - 1])
                #longEnter(alinacak_miktar)
                #sorEntryPrice(newSymbol,posSideTxt)
                #if len(aldimEntryPrice[0]) > 0:
                #    print(aldimEntryPrice[0])
                print(f"{newSymbol}: LONG ENTER : BuyPrice:{currentPrice}, tradeCount:{tradeLongCount}")
                services.execute(f"INSERT INTO activeOrder VALUES (null, '{newSymbol}', '{currentPrice}', '{((currentPrice / 100) * priceDeviation) + currentPrice}', '{posSideTxt}', '{alinacak_miktar}', '{current_time}','1')")
                connection.commit()
                first = True
                #logger.sendMsg(('::BUY::\n'+str(current_time)+'\nCoinSembol: '+str(newSymbol)+'_'+str(leverage)+'X'+'\nLONG ENTER'+'\nMiktar: '+str(alinacak_miktar)+'\nTradeCount: '+str(tradeCount)+'\nPriceDeviation: '+str(priceDeviation)),'0')
                tradeLongCount += 1
                alinacak_miktar = 0
            time.sleep(1)

        # SHORT ENTER
        #float(free_balance["USDT"]) >= baseOrderSize
        if ((firstPrice / 100) * priceDeviation) + firstPrice <= currentPrice and maxSafetyTradesCount>tradeShortCount and (positionSide == 2 or positionSide == 3): 
            posSideTxt="SHORT"
            if (tradeShortCount % 3 == 0):
                safetyOrderSize = safetyOrderSize*safetyOrderVolumeScale
                alinacak_miktar = (safetyOrderSize * float(leverage)) / float(df["close"][len(df.index) - 1])
                #shortEnter(alinacak_miktar)
                #sorEntryPrice(newSymbol,posSideTxt)
                #if len(aldimEntryPrice[0]) > 0:
                #    print(aldimEntryPrice[0])
                safetyOrderSize = float(config._safetyOrderSize)
                print(f"{newSymbol}: SHORT ENTER : BuyPrice:{currentPrice}, tradeCount:{tradeShortCount}")
                services.execute(f"INSERT INTO activeOrder VALUES (null, '{newSymbol}', '{currentPrice}', '{currentPrice - ((currentPrice / 100) * priceDeviation)}', '{posSideTxt}', '{alinacak_miktar}', '{current_time}','1')")
                connection.commit()
                first = True
                #logger.sendMsg(('::BUY::\n'+str(current_time)+'\nCoinSembol: '+str(newSymbol)+'_'+str(leverage)+'X'+'\nSHORT ENTER'+'\nMiktar: '+str(alinacak_miktar)+'\nTradeCount: '+str(tradeCount)+'\nPriceDeviation: '+str(priceDeviation)),'0')
                tradeShortCount += 1
                alinacak_miktar = 0
            else:
                alinacak_miktar = (baseOrderSize * float(leverage)) / float(df["close"][len(df.index) - 1])
                #shortEnter(alinacak_miktar)
                #sorEntryPrice(newSymbol,posSideTxt)
                #if len(aldimEntryPrice[0]) > 0:
                #    print(aldimEntryPrice[0])
                print(f"{newSymbol}: SHORT ENTER : BuyPrice:{currentPrice}, tradeCount:{tradeShortCount}")
                services.execute(f"INSERT INTO activeOrder VALUES (null, '{newSymbol}', '{currentPrice}', '{currentPrice - ((currentPrice / 100) * priceDeviation)}', '{posSideTxt}', '{alinacak_miktar}', '{current_time}','1')")
                connection.commit()
                first = True
                #logger.sendMsg(('::BUY::\n'+str(current_time)+'\nCoinSembol: '+str(newSymbol)+'_'+str(leverage)+'X'+'\nSHORT ENTER'+'\nMiktar: '+str(alinacak_miktar)+'\nTradeCount: '+str(tradeCount)+'\nPriceDeviation: '+str(priceDeviation)),'0')
                tradeShortCount += 1
                alinacak_miktar = 0
            time.sleep(1)

        for x in LongCoins:
            exractCoin=[]
            setYeniMaxMargin=0
            exractCoin=x.split(":")
            if float(exractCoin[1]) < currentPrice:
                #longExit(float(exractCoin[2]))
                if tradeLongCount > 1:
                    tradeLongCount -= 1
                print(f"{newSymbol}: LONG TAKE PROFIT : {exractCoin[0]} : Start:{exractCoin[4]}, End:{exractCoin[1]} > current: {currentPrice}")
                logger.sendMsg(f"{current_time}:{newSymbol}: LONG SATTIM 0.50$ KAR","0")
                services.execute(f"UPDATE activeOrder SET active = '0' WHERE tid = '{exractCoin[0]}'")
                setYeniMaxMargin= float(TOPUSDT[0]) + 0.50
                services.execute(f"UPDATE toplamValletUSDT SET valueMaxMargin = '{setYeniMaxMargin}' WHERE tid = '1'")
                connection.commit()
                time.sleep(1)

        for y in ShortCoins:
            exractCoin=[]
            setYeniMaxMargin=0
            exractCoin=y.split(":")
            if float(exractCoin[1]) > currentPrice:
                #shortExit(float(exractCoin[2]))
                if tradeShortCount > 1:
                    tradeShortCount -= 1
                print(f"{newSymbol}: SHORT TAKE PROFIT : {exractCoin[0]} : Start:{exractCoin[4]}, End:{exractCoin[1]} > current: {currentPrice}")
                logger.sendMsg(f"{current_time}:{newSymbol}: SHORT SATTIM 0.50$ KAR","0")
                services.execute(f"UPDATE activeOrder SET active = '0' WHERE tid = '{exractCoin[0]}'")
                setYeniMaxMargin= float(TOPUSDT[0]) + 0.50
                services.execute(f"UPDATE toplamValletUSDT SET valueMaxMargin = '{setYeniMaxMargin}' WHERE tid = '1'")
                connection.commit()
                time.sleep(1)
                
        #if inPosition:
        #    print("Trade Count: ", tradeCount, " Avarege Price: ", float(position_info["entryPrice"][len(position_info.index) - 1]), " Free Usdt: ", round(float(free_balance["USDT"]),2), " Total Money: ", round(float(balance['total']["USDT"]),2))
        #if inPosition == False: 
        #    print(f"Starting Price: {firstPrice}, Current Price: {currentPrice}, Total Money: {round(float(balance['total']['USDT']),2)}")
        #print("***********************************")
        
        time.sleep(2)

        #ERRORS
    except ccxt.BaseError as Error:
        nowt = time.localtime()
        current_time = time.strftime("%d-%m-%Y %H:%M:%S", nowt)
        print (f"[HATA] : {Error}")
        services.execute(f"INSERT INTO consoleLog VALUES (null,'{Error}','{current_time}')")
        connection.commit()
        time.sleep(20)
        continue