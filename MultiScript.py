import pyodbc
from flask import Flask, request, jsonify
import time
from fyers_api import fyersModel
from fyers_api import accessToken
from fyers_api.Websocket import ws


cnxn_str = ("Driver={SQL Server Native Client 11.0};"
            "Server=192.168.1.197;"
            "Integrated_Security=false;"
            "Trusted_Connection=No;"
            "MARS_Connection=Yes;"
            "Database=stockAutoPilot;"
            "UID=Tripund;"
            "PWD=Shiv@123;"
            "autocommit=True;")
cnxn = pyodbc.connect(cnxn_str)
cursor = cnxn.cursor()


def getMultiScriptDetails():
    sql = '{CALL GetAllScripts()}'
    cursor.execute(sql)
    for row in cursor.fetchall():
        scriptName = row[1]
        buyMargin = row[3]
        sellMargin = row[4]
        quantityBalance = row[4]
        investmentBalance = row[4]
        lastTransaction = row[4]
        currentPrice = 10000
        qtySlab = 1
        print('Script name = ', scriptName, 'Buy Margin=', buyMargin, 'Sell Margin=', sellMargin,
              'Quantity Balance=', quantityBalance, 'Investment Balance=', investmentBalance, 'Last Transaction=', lastTransaction)

    if currentPrice >= lastTransaction + (sellMargin / 100) * lastTransaction and quantityBalance > 0:
        lastTransaction = currentPrice
        quantityBalance -= 1
        investmentBalance += qtySlab*currentPrice + \
            (currentPrice - lastTransaction)*qtySlab

    elif currentPrice <= lastTransaction - (buyMargin / 100) * lastTransaction:
        lastTransaction = currentPrice
        quantityBalance += 1
        investmentBalance -= qtySlab*currentPrice

    time.sleep(300)


if __name__ == '__main__':
    result = getMultiScriptDetails()
    print('result=', result)
