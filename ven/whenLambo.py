#coding:utf-8
import os
import sys
import random
import sqlite3
import pandas as pd
import ccxt
import time
import requests
from bs4 import BeautifulSoup as bs
import argparse
import numpy as np
import pytz
from pytz import timezone
from datetime import datetime

def internetOn():
    try:
        url = "https://google.com/"
        soup = bs(requests.get(url).content, "html.parser")
        if soup != "":
            return True
    except Exception as Error:
        return False

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
        
parser = argparse.ArgumentParser(description='koinler')
parser.add_argument('-sx','--symblx',type=str)
parser.add_argument('-lx','--leverx',type=float)
parser.add_argument('-bx','--basex',type=float)
parser.add_argument('-sbx','--safeBasex',type=float)
parser.add_argument('-stx','--maxSafeTradex',type=float)
'''parser.add_argument('-sx','--symblx',type=str,default='BLZ')
parser.add_argument('-lx','--leverx',type=float,default=0.0)
parser.add_argument('-bx','--basex',type=float,default=0.0)
parser.add_argument('-sbx','--safeBasex',type=float,default=0.0)
parser.add_argument('-stx','--maxSafeTradex',type=float,default=0.0)'''
args = parser.parse_args()

# SETTİNGS
symbolName = (args.symblx).upper()
print(f"[RUNNING COIN]:{symbolName}/USDT")
leverage = float(args.leverx)
baseOrderSize = float(args.basex)
safetyOrderSize = float(args.safeBasex)
maxSafetyTradesCount = float(args.maxSafeTradex)
priceDeviation = float(0.55)
safetyOrderStepScale = float(2)
safetyOrderVolumeScale = float(2)
takeProfit = float(0.55)
stopLoss = float(0)

def optionsSelect():
    services.execute(f"SELECT * FROM optiOns")
    rows=services.fetchall()
    for row in rows:
        baseOPTIONS.append(f"{row[4]}:{row[6]}:{row[7]}:{row[8]}:{row[9]}:{row[10]}:{row[11]}:{row[12]}:{row[15]}")    
    for base in baseOPTIONS[0].split(":"):
        underOptions.append(base)

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
baseOPTIONS = []
underOptions = []
_APPID = "ADMIN"

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
apiKey = ""
secretKey = ""
    
#DATABASE
connection=sqlite3.connect(f'venBot-{_APPID}.db')
services=connection.cursor()
optionsSelect()
if(underOptions[6] != "" and underOptions[7] != ""):
    apiKey = underOptions[6]
    secretKey = underOptions[7]
            
# API CONNECT
exchange = ccxt.binance({
"apiKey": apiKey,
"secret": secretKey,
'options': {
'defaultType': 'future'
},
'enableRateLimit': True
})
while True:
    try:
        optionsSelect()
        time.sleep(1)
        while internetOn() == False: 
            print("[ERROR] : Your internet connection is gone, please check your connection")
            services.execute(f"INSERT INTO consoleLog VALUES (null,'Internet baglantiniz gitmistir, lutfen baglantinizi kontrol ediniz','{current_time}')")
            connection.commit()
            time.sleep(30)
            if internetOn() == True:
                break
            
        services.execute(f"UPDATE coinRunner SET coinStatus = 'RUNNING' WHERE coinStatus = 'READY' AND symBil = '{symbolName}' ")
        connection.commit()
        
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

        #LOOP ATTRIBUTES
        newSymbol = f"{symbolName}USDT"
        balance = exchange.fetch_balance()
        time.sleep(1)
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
            print (f"[ERROR] : Message:{Error}")
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
            print(f"{newSymbol}: (*)FirstPrice: {firstPrice} Free Usdt: ", round(float(free_balance["USDT"]),2),f" Total Money: ", round(float(balance['total']["USDT"]),2) )
            first = False
        endBuyMAX = []
        currentPrice = float(df["close"][len(df.index) - 1])

        # LONG ENTER
        def longEnter(amountx):
            order = exchange.create_order(symbol=symbol, amount=amountx, side='BUY', type='MARKET', params={'positionSide': 'LONG'})
            
        # LONG EXIT
        def longExit(amountx):
            order = exchange.create_order(symbol=symbol, amount=amountx, side='SELL', type='MARKET', params={'positionSide': 'LONG'})

        # SHORT ENTER
        def shortEnter(amountx):
            order = exchange.create_order(symbol=symbol, amount=amountx, side='SELL', type='MARKET', params={'positionSide': 'SHORT'})
            
        # SHORT EXIT
        def shortExit(amountx):
            order = exchange.create_order(symbol=symbol, amount=amountx, side='BUY', type='MARKET', params={'positionSide': 'SHORT'})

        #Long Enter CONTROL
        #float(free_balance["USDT"]) >= baseOrderSize
        if firstPrice - (firstPrice/100) * priceDeviation >= currentPrice and maxSafetyTradesCount>tradeLongCount:
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
                #sendUserTELEMsg(f"::BUY::\n{current_time}\nCoinSembol:{newSymbol} {int(leverage)}X\nLONG ENTER\nAmount: {alinacak_miktar}\nTradeCount: {tradeLongCount}\nPriceDeviation: {priceDeviation}", underOptions[2], underOptions[3], underOptions[5], current_time)
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
                #sendUserTELEMsg(f"::BUY::\n{current_time}\nCoinSembol:{newSymbol} {int(leverage)}X\nLONG ENTER\nAmount: {alinacak_miktar}\nTradeCount: {tradeLongCount}\nPriceDeviation: {priceDeviation}", underOptions[2], underOptions[3], underOptions[5], current_time)
                tradeLongCount += 1
                alinacak_miktar = 0
            time.sleep(1)
            
        #Short Enter CONTROL
        #float(free_balance["USDT"]) >= baseOrderSize
        if ((firstPrice / 100) * priceDeviation) + firstPrice <= currentPrice and maxSafetyTradesCount>tradeShortCount: 
            posSideTxt="SHORT"
            if (tradeShortCount % 3 == 0):
                alinacak_miktar = ((baseOrderSize * safetyOrderSize)* float(leverage)) / float(df["close"][len(df.index) - 1]) 
                #shortEnter(alinacak_miktar)
                #sorEntryPrice(newSymbol,posSideTxt)
                #if len(aldimEntryPrice[0]) > 0:
                #    print(aldimEntryPrice[0])
                print(f"{newSymbol}: SHORT ENTER : BuyPrice:{currentPrice}, tradeCount:{tradeShortCount}")
                services.execute(f"INSERT INTO activeOrder VALUES (null, '{newSymbol}', '{currentPrice}', '{currentPrice - ((currentPrice / 100) * priceDeviation)}', '{posSideTxt}', '{alinacak_miktar}', '{current_time}','1')")
                connection.commit()
                first = True
                #sendUserTELEMsg(f"::BUY::\n{current_time}\nCoinSembol:{newSymbol} {int(leverage)}X\nSHORT ENTER\nAmount: {alinacak_miktar}\nTradeCount: {tradeShortCount}\nPriceDeviation: {priceDeviation}", underOptions[2], underOptions[3], underOptions[5], current_time)
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
                #sendUserTELEMsg(f"::BUY::\n{current_time}\nCoinSembol:{newSymbol} {int(leverage)}X\nSHORT ENTER\nAmount: {alinacak_miktar}\nTradeCount: {tradeShortCount}\nPriceDeviation: {priceDeviation}", underOptions[2], underOptions[3], underOptions[5], current_time)
                tradeShortCount += 1
                alinacak_miktar = 0
            time.sleep(1)
            
        #Long TakeProfit     
        for x in LongCoins:
            exractCoin=[]
            setYeniMaxMargin=0
            exractCoin=x.split(":")
            if float(exractCoin[1]) < currentPrice:
                #longExit(float(exractCoin[2]))
                if tradeLongCount > 1:
                    tradeLongCount -= 1
                print(f"{newSymbol}: LONG TAKE PROFIT : {exractCoin[0]} : Start:{exractCoin[4]}, End:{exractCoin[1]} > current: {currentPrice}")
                #sendUserTELEMsg(f"{current_time}:{newSymbol}: LONG SATTIM 0.50$ KAR", underOptions[2], underOptions[3], underOptions[5], current_time)
                services.execute(f"INSERT INTO orderHistory VALUES (null, '{newSymbol}', '{currentPrice}', '{((currentPrice / 100) * priceDeviation) + currentPrice}', '{posSideTxt}', '{alinacak_miktar}', '0.5', '{current_time}','1')")
                services.execute(f"UPDATE activeOrder SET active = '0' WHERE tid = '{exractCoin[0]}'")
                setYeniMaxMargin= float(TOPUSDT[0]) + 0.50
                services.execute(f"UPDATE toplamValletUSDT SET valueMaxMargin = '{setYeniMaxMargin}' WHERE tid = '1'")
                connection.commit()
                time.sleep(1)
                
        #Short TakeProfit        
        for y in ShortCoins:
            exractCoin=[]
            setYeniMaxMargin=0
            exractCoin=y.split(":")
            if float(exractCoin[1]) > currentPrice:
                #shortExit(float(exractCoin[2]))
                if tradeShortCount > 1:
                    tradeShortCount -= 1
                print(f"{newSymbol}: SHORT TAKE PROFIT : {exractCoin[0]} : Start:{exractCoin[4]}, End:{exractCoin[1]} > current: {currentPrice}")
                #sendUserTELEMsg(f"{current_time}:{newSymbol}: SHORT SATTIM 0.50$ KAR", underOptions[2], underOptions[3], underOptions[5], current_time)
                services.execute(f"INSERT INTO orderHistory VALUES (null, '{newSymbol}', '{currentPrice}', '{currentPrice - ((currentPrice / 100) * priceDeviation)}', '{posSideTxt}', '{alinacak_miktar}', '0.5', '{current_time}','1')")
                services.execute(f"UPDATE activeOrder SET active = '0' WHERE tid = '{exractCoin[0]}'")
                setYeniMaxMargin= float(TOPUSDT[0]) + 0.50
                services.execute(f"UPDATE toplamValletUSDT SET valueMaxMargin = '{setYeniMaxMargin}' WHERE tid = '1'")
                connection.commit()
                time.sleep(1)
        time.sleep(2)
        
    #ERRORS
    except ccxt.BaseError as Error:
        print(f"[ERROR] : {Error}")
        services.execute(f"INSERT INTO consoleLog VALUES (null, '{Error}', '{current_time}')")
        connection.commit()
        time.sleep(20)
        continue