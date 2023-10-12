import time
import pandas as pd
from datetime import date, datetime
import sys
import concurrent.futures
import pyodbc
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from fyers_api import fyersModel
from fyers_api import accessToken
import webbrowser
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from fyers_api.Websocket import ws
import os

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
redirect_uri = "https://www.google.com/"
client_id = "1P2PP0NTZ1-100"
secret_key = "B7SFK0LMYT"
grant_type = "authorization_code"
response_type = "code"
state = "sample"
initial_flag = 0
last_transaction = 0
quantity_balance = 0


def login():
    access_token = ""
    if not os.path.exists("access_token.txt"):
        session = accessToken.SessionModel(client_id=client_id, secret_key=secret_key,
                                           redirect_uri=redirect_uri, response_type="code", grant_type="authorization_code")
        response = session.generate_authcode()
        print("Login Url :", response)
        auth_code = input("Enter Auth Code:")
        session.set_token(auth_code)
        response = session.generate_token()['access_token']
        with open("access_token.txt", "w") as f:
            f.write(response)
    else:
        with open("access_token.txt", "r") as f:
            access_token = f.read()
    return access_token


access_token = login()
fyers = fyersModel.FyersModel(
    token=access_token, is_async=False, client_id=client_id, log_path="")


def placeorder(side):
    data = {
        "symbol": "NSE:TATASTEEL-EQ",
        "qty": 1,
        # 2 indicates market order1 => Limit Order 2 => Market Order 3 => Stop Order (SL-M) 4 => Stoplimit Order (SL-L)
        "type": 2,
        "side": side,  # 1 for buy and -1 for sell
        "productType": "CNC",
        "limitPrice": 0,
        "stopPrice": 0,
        "validity": "DAY",
        "disclosedQty": 0,
        "offlineOrder": "False",
        # "stopLoss": 0,
        # "takeProfit": 0
    }
    print(fyers.place_order(data))


def buy_order():
    placeorder(1)
    # insert_transactions()


def sell_order():
    placeorder(-1)
    # insert_transactions()


def insert_scripts(scripts):
    # for x in scripts:
    sql = '{CALL InsertScript(?, ?, ?, ?, ?, ?, ?, ?, ?)}'
    values = (scripts['selectedScript']['code'], 0, scripts['buyMargin'], scripts['sellMargin'],
              0, 1, scripts['investmentAmount'], 1, scripts['investmentAmount'])
    cnxn.execute(sql, values)
    cnxn.commit()


def insert_transactions(scriptId, orderType, qtySlab, buyTarget, sellTarget, qtyBalance, scriptFundBalance, Profit, buyRate, Bings):
    sql = '{CALL InsertTransaction(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}'
    values = (scriptId, orderType, qtySlab, buyTarget, sellTarget,
              qtyBalance, scriptFundBalance, Profit, buyRate, Bings)
    cnxn.execute(sql, values)
    cnxn.commit()


def insert_scripts(scripts):
    # for x in scripts:
    sql = '{CALL InsertScript(?, ?, ?, ?, ?, ?, ?, ?, ?)}'
    values = (scripts['selectedScript']['code'], 0, scripts['buyMargin'], scripts['sellMargin'],
              0, 1, scripts['investmentAmount'], 1, scripts['investmentAmount'])
    cnxn.execute(sql, values)
    cnxn.commit()


def insert_transactions(scriptId, orderType, qtySlab, buyTarget, sellTarget, qtyBalance, scriptFundBalance, Profit, buyRate, Bings):
    sql = '{CALL InsertTransaction(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}'
    values = (scriptId, orderType, qtySlab, buyTarget, sellTarget,
              qtyBalance, scriptFundBalance, Profit, buyRate, Bings)
    cnxn.execute(sql, values)
    cnxn.commit()


def start_program():
    # scripts = []
    # content_type = request.headers.get('Content-Type')
    # if (content_type == 'application/json'):
    #     json = request.json
    #     print(json)
    #     for script in json:
    #         scripts.append(script)
    # else:
    #     return 'Content-Type not supported!'
    investment_balance = 100000
    buy_margin = 0.5
    sell_margin = 1
    stock_quantity = 5
    qty_slab = 1
    data = {"symbols": "NSE:TATASTEEL-EQ"}
    last_transaction = fyers.quotes(data)["d"][0]["v"]["lp"] - 1.4

    while (True):
        print(f"last transaction: {last_transaction}")
        if (fyers.quotes(data)):
            current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
            print("current price =", current_price)
            if current_price >= last_transaction + (sell_margin / 100) * last_transaction and stock_quantity > 0:
                sell_order()
                last_transaction = current_price
                stock_quantity -= 1
                investment_balance += qty_slab*current_price + \
                    (current_price - last_transaction)*qty_slab
                insert_transactions(
                    0,
                    -1,
                    1,
                    current_price - (1 / 100) * current_price,
                    current_price + (1 / 100) * current_price,
                    stock_quantity,
                    investment_balance,
                    (current_price - last_transaction)*qty_slab,
                    last_transaction,
                    1
                )

            elif current_price <= last_transaction - (buy_margin / 100) * last_transaction:
                buy_order()
                last_transaction = current_price
                stock_quantity += 1
                investment_balance -= qty_slab*current_price
                insert_transactions(
                    0,
                    1,
                    1,
                    current_price - (1 / 100) * current_price,
                    current_price + (1 / 100) * current_price,
                    stock_quantity,
                    investment_balance,
                    0,
                    0

                )
        time.sleep(300)


if __name__ == '__main__':
    start_program()
