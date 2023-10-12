import signal
import smtplib
import ssl
import time
import pandas as pd
from datetime import date, datetime, timedelta
import pyodbc
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
from fyers_api import fyersModel
from fyers_api import accessToken
import os
import jwt
from functools import wraps
import traceback
import static.credentials as cred
app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

# connection string
cnxn_str = ("Driver={ODBC Driver 17 for SQL Server};"
            "Server=192.168.1.197;"
            "Integrated_Security=false;"
            "Trusted_Connection=No;"
            "MARS_Connection=Yes;"
            "Database=stockAutoPilot;"
            "UID=Admin;"
            "PWD=Admin123;"
            "autocommit=True;")
cnxn = pyodbc.connect(cnxn_str)
cursor = cnxn.cursor()
redirect_uri = cred.REDIRECT_URI
client_id = cred.CLIENT_ID
secret_key = cred.SECRET_KEY
grant_type = cred.GRANT_TYPE
response_type = cred.RESPONSE_TYPE
state = cred.STATE
initial_flag = 0
last_transaction = 0
quantity_balance = 0
# last_transaction = 0
last_buy_id = 0
last_transaction_date = date.today()
key = cred.KEY
access_token = ""
# fyers = ""


def getFyersToken():

    try:
        sql = '{CALL getFyToken()}'
        cursor.execute(sql)
        result = cursor.fetchone()
        # print(result[0])
        # print(len(result[0]))
        return result[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)


session = accessToken.SessionModel(client_id=client_id, secret_key=secret_key,
                                   redirect_uri=redirect_uri, response_type="code", grant_type="authorization_code")
if (getFyersToken() != None):
    global fyers
    auth_token = getFyersToken()
    fyers = fyersModel.FyersModel(
        token=auth_token, is_async=False, client_id=client_id, log_path="")

if not os.path.exists(f"apilog{date.today()}.txt"):
    f = open(f"apilog{date.today()}.txt", "w")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers["Authorization"][7:]
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            token = jwt.decode(token, key, algorithms=["HS256"])
        except:
            return jsonify({'status': 'Token is invalid'}), 401

        return f(*args, **kwargs)
    return decorated

# Login auth code


def getFyersFund():
    createAPILog("call of fyers fund")
    return fyers.funds()


def getFyersHoldings():
    createAPILog("call of fyers Holdings")
    return fyers.holdings()


def getFyersPositions():
    createAPILog("call of fyers Positions")
    return fyers.positions()

# code to generate error logs


def createLog(msg, scriptName):
    try:
        file = open('errorLogs.txt', 'a')
        file.writelines(f"\n{datetime.now()}-{scriptName} - {msg}")
    except:
        with open('errorLogs.txt', 'w') as f:
            traceback.print_exc(file=f)

# code to generate error logs


def createAPILog(message):
    try:
        file = open(f"apilog{date.today()}.txt", 'a')
        file.writelines(f"\n{datetime.now()}- {message}")
    except:
        with open(f"apilog{date.today()}.txt", 'w') as f:
            traceback.print_exc(file=f)

# code to generate transactions logs


def createTransctionLog(msg, scriptName):
    try:
        file = open('TransactionErrorlogs.txt', 'a')
        file.writelines(f"\n{datetime.now()}-{scriptName} - {msg}")
    except:
        with open('TransactionErrorlogs.txt', 'w') as f:
            traceback.print_exc(file=f)


def placeorder(symbol, side, qty):
    data = {
        "symbol": f"NSE:{symbol}-EQ",
        "qty": qty,
        # 2 indicates market order 1 => Limit Order 2 => Market Order 3 => Stop Order (SL-M) 4 => Stoplimit Order (SL-L)
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
    createAPILog(f"order placement {symbol}, type-{side}")
    return fyers.place_order(data)

# function to call buy method


def buy_order(symbol, qty):
    return placeorder(symbol, 1, qty)

# function to call sell method


def sell_order(symbol, qty):
    return placeorder(symbol, -1, qty)


def getLastBuy(scriptId):
    try:
        sql = '{CALL getLastBuyByScriptId(?)}'
        values = (scriptId)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def getLastBuyQtySlab(scriptId):
    try:
        sql = '{CALL getLastBuyQtySlab(?)}'
        values = (scriptId)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)

# function to get the id of last sell


def getLastSellId(scriptId):
    try:
        sql = '{CALL getLastSellId(?)}'
        values = (scriptId)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)

# function to update sell id for last buy


def updateLastTransaction(sellId, buyId):
    try:
        sql = '{CALL updateSellIdForBuy(?, ?)}'
        values = (sellId, buyId)
        cursor.execute(sql, values)
        cursor.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


# get average by script id
def getAvgPriceByScriptId(id):
    try:
        sql = '{CALL getAvgPriceByScriptId(?)}'
        values = (id)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)

# get sm2 flag by id


def getsm2FlagById(id):
    try:
        sql = '{CALL getSm2FlagById(?)}'
        values = (id)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


# update script by id
def updateScript(id, investmentBalance, qtyBalance, lastTransactions, averagePrice, sm2Flag):
    try:
        sql = '{CALL UpdateScriptForTransaction(?, ?, ?, ?, ?, ?)}'
        values = (id, investmentBalance, qtyBalance,
                  lastTransactions, averagePrice, sm2Flag)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def getLastTransactionByScriptId(id):
    try:
        sql = '{CALL getLastTradedPriceByScriptId(?)}'
        values = (id)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        if result != None:
            return result[0]
        else:
            return 0
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def getLastNotified():
    try:
        sql = '{CALL getLastNotified()}'
        cursor.execute(sql)
        result = cursor.fetchone()
        return result[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def setLastNotified():
    try:
        sql = '{CALL setLastNotified()}'
        cursor.execute(sql)
        cursor.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def sendEmail():
    port = 465  # For SSL
    smtp_server = "smtp.gmail.com"
    sender_email = "rupal.tripund@gmail.com"  # Enter your address
    receiver_email = "rajeshrs81@gmail.com"  # Enter receiver address
    password = "lqcwljvatimrevva"
    message = """\
        Subject: CDSL Login not done.


       Please do cdsl login otherwise orders will not be placed."""

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)


def getTodayScriptQtyBalByScriptName(scriptName):
    sql = '{CALL getTodayScriptQtyBalByScriptName(?)}'
    values = (scriptName)
    cursor.execute(sql, values)
    result = cursor.fetchone()
    return result


def sortTradeBook(e):
    return e['orderDateTime']


def getTodaysTransaction():
    try:
        result = []
        sql = '{CALL getTodaysTransaction()}'
        cursor.execute(sql)
        transactions = cursor.fetchall()
        return transactions
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)

import scripts
import logic2
import transactions
@app.route('/api/historicalAnalysis', methods=["POST"])
def calculateOutput():
    jsonRequest = request.json
    # print(jsonRequest)
    script_name = jsonRequest["scriptName"]
    investment_amount = float(jsonRequest["investmentAmount"])
    initial_investment_fund = investment_amount
    filePath = jsonRequest["filePath"]
    buy_margin = float(jsonRequest["buyMargin"])
    sell_margin = float(jsonRequest["sellMargin"])
    data = pd.read_csv(filePath)
    df = pd.DataFrame(data)
    last_buy = df["Close"][0]
    eligible_qty = investment_amount/last_buy
    qty_slab = int(eligible_qty/10)
    print(qty_slab)

    buy_array = []
    sell_array = []
    inter_buy_array = []
    buy_counter = 1
    sell_counter = 0

    buy_array.append(last_buy)
    inter_buy_array.append(f"B{buy_counter}")
    df.loc[0, "action"] = f"B{buy_counter}"
    investment_amount -= qty_slab*df["Close"][0]
    df.loc[0, "buy_price"] = qty_slab*df["Close"][0]
    df.loc[0, "invest_bal"] = investment_amount
    for price in range(0, len(df)):
        slab_amount = qty_slab*df["Close"][price]
        if len(buy_array) == 0:
            buy_array.append(df["Close"][price])
            investment_amount -= slab_amount
            last_buy = buy_array[-1]
            buy_counter += 1
            inter_buy_array.append(f"B{buy_counter}")
            df.loc[price, "action"] = f"B{buy_counter}"
            df.loc[price, "buy_price"] = slab_amount
            df.loc[price, "invest_bal"] = investment_amount
        elif len(buy_array) != 0:
            last_buy = buy_array[-1]
        if df["Close"][price] <= last_buy - (buy_margin/100)*last_buy and investment_amount > slab_amount:
            buy_array.append(df["Close"][price])
            investment_amount -= slab_amount
            buy_counter += 1
            inter_buy_array.append(f"B{buy_counter}")
            df.loc[price, "action"] = f"B{buy_counter}"
            df.loc[price, "buy_price"] = slab_amount
            df.loc[price, "invest_bal"] = investment_amount
        if df["Close"][price] >= last_buy + (sell_margin/100)*last_buy and len(buy_array) != 0 and len(inter_buy_array) != 0:
            sell_counter += 1
            investment_amount += slab_amount
            df.loc[price, "action"] = f"{inter_buy_array[-1]}S{sell_counter}"
            df.loc[price, "profit"] = (df["Close"][price] - last_buy)*qty_slab
            df.loc[price, "sell_price"] = slab_amount
            df.loc[price, "invest_bal"] = investment_amount
            inter_buy_array.pop()
            buy_array.pop()
    df.loc[0, "script_name"] = script_name
    df.loc[0, "script_fund"] = initial_investment_fund
    df.to_csv(f"{filePath[:-4]}{date.today()}.csv")
    return jsonify("success")


@app.route('/api/getFundSummary', methods=['GET'])
@token_required
def getFundSummary():
    try:
        fyersFund = getFyersFund()['fund_limit'][0]['equityAmount']
        fyersHoldings = getFyersHoldings()["overall"]
        fyersPositions = getFyersPositions()["overall"]
        investedValue = fyersHoldings["total_investment"]
        pnl = fyersHoldings["total_pl"]
        # print("pnl", fyersHoldings["total_pl"])
        marketValue = fyersHoldings["total_current_value"]
        # print("fyers position", getFyersPositions())

        # pnl_realized = fyersPositions["realized_profit"]
        # print(marketValue)
        return jsonify({'fyersFund': fyersFund, 'invValue': investedValue, 'pnl': pnl, 'marketCurrentValue': marketValue})

    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@app.route('/api/getRemainingApiCalls', methods=['GET'])
@token_required
def getRemainingAPIcalls():
    count = 0
    with open(f"apilog{date.today()}.txt") as fp:
        for line in fp:
            if line.strip():
                count += 1
    count = 10000 - count
    return jsonify(count)


@app.route('/api/setAuthCode', methods=['GET'])
def login():
    global fyers
    global session
    args = request.args
    # if not os.path.exists("access_token.txt"):

    response = session.generate_authcode()
    # print("Login Url :", response)
    auth_code = args.to_dict()["token"]
    session.set_token(auth_code)
    response = session.generate_token()['access_token']
    # print(response)
    sql = '{CALL fyToken(?)}'
    values = (response)
    cursor.execute(sql, values)
    cursor.commit()
    fyers = fyersModel.FyersModel(
        token=response, is_async=False, client_id=client_id, log_path="")
    return jsonify("success")


@ app.route("/api/authenticate", methods=["POST"])
def authenticate():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        try:
            # cursor.execute(
            #     f"select * from users where username='{json['username']}' and password='{json['password']}'")
            cursor.execute(
                f"select * from users where username='{json['username']}' and password='{json['password']}'")
            if (cursor.fetchone()):
                token = jwt.encode({'user': json["username"], 'exp': datetime.utcnow(
                ) + timedelta(days=1)}, "secret", "HS256")
            else:
                return jsonify({"message": "Invalid Credentials"}), 404

            return jsonify({"token": token})
        except:
            with open('errorLogs.txt', 'a+') as f:
                f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
                traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@app.route("/api/checkFyersToken", methods=["GET"])
@token_required
def checkFyersToken():
    createAPILog("call for get fyers profile")
    return jsonify(fyers.get_profile())


@ app.route('/api/StartProgram', methods=['GET'])
@ token_required
def start_program():
    # print("Average Price", getAvgPriceByScriptId(id))
    last_traded_value = 0
    transactionList = []
    # get all the active scrupts
    activeScripts = cursor.execute(
        f"select * from scripts where active_flag = 1 and isdeleted = 0").fetchall()
    # print(activeScripts)
    # loop through all the active scripts
    if (datetime.now() < datetime.now().replace(hour=15, minute=30, second=0, microsecond=0) and activeScripts != None):
        for rowdata in activeScripts:
            data = {"symbols": f"NSE:{rowdata[1]}-EQ"}
            # print(fyers.quotes(data))
            current_price = float(fyers.quotes(data)["d"][0]["v"]["lp"])
            id = rowdata[0]
            scriptName = rowdata[1]
            investment_balance = float(rowdata[8])
            createTransctionLog(
                f"investment balance while getting from db={investment_balance}", scriptName)
            buy_margin = rowdata[3]
            sell_margin = rowdata[4]
            last_transaction = rowdata[11]
            last_transaction_date = date.today()
            reset_criteria = rowdata[7]
            sm2_flag = rowdata[18]
            # print("sm2 flag", sm2_flag)
            deal = rowdata[15]
            avg_price = float(getAvgPriceByScriptId(id))
            average_price = rowdata[13]
            market_rate_stoploss = rowdata[19]
            startFlag = 1
            specific_value = rowdata[16]
            marginal_value = rowdata[17]
            if getLastTransactionByScriptId(id):
                last_traded_value = getLastTransactionByScriptId(rowdata[0])
            # get last transaction for the script if only exists
            # print(getLastBuy(id))
            if getLastBuy(id) != None:
                last_transaction = getLastBuy(id)[10]
                last_buy_id = getLastBuy(id)[0]
                last_transaction_date = str(getLastBuy(id)[1])
                last_buy_qty_slab = getLastBuy(id)[4]
                last_transaction_date = datetime.strptime(
                    last_transaction_date[0:10], '%Y-%m-%d').date()
            stock_quantity = rowdata[5]
            investment_fund = rowdata[10]
            script_id = rowdata[0]
            eligibility_quantity = int(investment_fund/current_price)
            qty_slab = int(eligibility_quantity/5)
            sm2 = 2*sell_margin

            if investment_balance <= current_price * qty_slab:
                transactionList.append(
                    {"scriptName": scriptName, "message": "Balance is low- Trade can not be placed"})

            if stock_quantity == 0 and last_transaction == 0 and investment_balance >= current_price * qty_slab:
                # code for placing a buy order and store the response in order_status
                order_status = buy_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    try:
                        tradebook = fyers.tradebook()['tradeBook']
                        tradebook.sort(key=sortTradeBook)
                        current_price = tradebook[-1]["tradePrice"]
                        print(
                            f"Initial Buy for - {current_price} {qty_slab} qty")
                        message = f"Initial Buy for - {current_price} {qty_slab} qty"
                        stock_quantity += qty_slab  # stock_quantity= stock_quantity + qty_slab
                        investment_balance -= qty_slab*current_price
                        last_transaction = current_price
                        if getLastBuy(id):
                            last_buy_id = getLastBuy(id)[0]
                        average_price = current_price
                        # print(average_price)
                        transactions.insert_transactions(
                            script_id,
                            1,
                            qty_slab,
                            current_price - (buy_margin / 100) * current_price,
                            current_price +
                            (sell_margin / 100) * current_price,
                            stock_quantity,
                            investment_balance,
                            0,
                            current_price,
                            0,
                            buy_margin,
                            sell_margin,
                            0
                        )
                        updateScript(script_id, investment_balance,
                                     stock_quantity, current_price, average_price, 1)
                        createTransctionLog(
                            f" Intial Buy {qty_slab} of {scriptName}", scriptName)
                        transactionList.append(
                            {"scriptName": scriptName, "message": message})
                    except:
                        os.kill(os.getpid(), signal.SIGINT)
                else:
                    createTransctionLog(order_status['message'], scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": order_status['message']})

            if stock_quantity == 0 and reset_criteria == 0 and last_transaction != 0 and investment_balance >= current_price * qty_slab:
                order_status = buy_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    try:
                        tradebook = fyers.tradebook()['tradeBook']
                        tradebook.sort(key=sortTradeBook)
                        current_price = tradebook[-1]["tradePrice"]
                        print(f"spot buy- {current_price} {qty_slab} qty")
                        message = f"spot buy- {current_price} {qty_slab} qty"
                        stock_quantity += qty_slab
                        investment_balance -= qty_slab*current_price
                        last_transaction = current_price
                        if getLastBuy(id) != None:
                            last_buy_id = getLastBuy(id)[0]
                        average_price = current_price
                        transactions.insert_transactions(
                            script_id,
                            1,
                            qty_slab,
                            current_price - (buy_margin / 100) * current_price,
                            current_price +
                            (sell_margin / 100) * current_price,
                            stock_quantity,
                            investment_balance,
                            0,
                            current_price,
                            0,
                            buy_margin,
                            sell_margin,
                            0
                        )
                        updateScript(script_id, investment_balance,
                                     stock_quantity, current_price, average_price, 1)
                        createTransctionLog(
                            f"spot buy- {current_price} {qty_slab} qty", scriptName)
                        transactionList.append(
                            {"scriptName": scriptName, "message": message})
                    except:
                        os.kill(os.getpid(), signal.SIGINT)
                else:
                    createLog(order_status['message'], scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": order_status['message']})

            elif stock_quantity == 0 and reset_criteria == 2 and current_price <= specific_value and investment_balance >= current_price * qty_slab:
                order_status = buy_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    try:
                        tradebook = fyers.tradebook()['tradeBook']
                        tradebook.sort(key=sortTradeBook)
                        current_price = tradebook[-1]["tradePrice"]
                        message = f"specific value - {current_price} {qty_slab} qty"
                        stock_quantity += qty_slab
                        investment_balance -= qty_slab*current_price
                        last_transaction = current_price
                        last_buy_id = getLastBuy(id)[0]
                        average_price = current_price
                        transactions.insert_transactions(
                            script_id,
                            1,
                            qty_slab,
                            current_price - (buy_margin / 100) * current_price,
                            current_price +
                            (sell_margin / 100) * current_price,
                            stock_quantity,
                            investment_balance,
                            0,
                            current_price,
                            0,
                            buy_margin,
                            sell_margin,
                            0
                        )
                        updateScript(script_id, investment_balance,
                                     stock_quantity, current_price, average_price, 1)
                        createTransctionLog(message, scriptName)
                        transactionList.append(
                            {"scriptName": scriptName, "message": message})
                    except:
                        os.kill(os.getpid(), signal.SIGINT)
                else:
                    createLog(order_status['message'], scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": order_status['message']})
            elif stock_quantity == 0 and reset_criteria == 2 and current_price > specific_value and investment_balance >= current_price * qty_slab:
                createTransctionLog(
                    f"Did not hit specific value because CP({current_price}) > SpecificValue({specific_value})", scriptName)
                transactionList.append(
                    {"scriptName": scriptName, "message": f"Did not hit specific value because CP({current_price}) > SpecificValue({specific_value})"})
            createAPILog(f"For getting curent price")
            data = fyers.quotes(data)
            if (data):
                current_price = data["d"][0]["v"]["lp"]
                # Condition for selling at sm2 rate
                if stock_quantity != 0 and stock_quantity == qty_slab and current_price >= last_transaction + (sm2 / 100) * last_transaction and last_transaction != 0 and sm2_flag == 1:
                    print("In Sell Order block with sm2")
                    lastBuyQtySlab = getLastBuyQtySlab(script_id)
                    order_status = sell_order(scriptName, lastBuyQtySlab)
                    if order_status['s'] != 'error':
                        try:
                            tradebook = fyers.tradebook()['tradeBook']
                            tradebook.sort(key=sortTradeBook)
                            current_price = tradebook[-1]["tradePrice"]
                            stock_quantity -= lastBuyQtySlab
                            investment_balance += lastBuyQtySlab*last_transaction
                            last_traded_value = current_price
                            message = f"Sold at - {current_price} {lastBuyQtySlab} qty at sm2 rate"
                            if stock_quantity == 0:
                                average_price = 0
                            else:
                                average_price = (investment_fund -
                                                 investment_balance)/stock_quantity
                            transactions.insert_transactions(
                                script_id,
                                -1,
                                lastBuyQtySlab,
                                0,
                                0,
                                stock_quantity,
                                investment_balance,
                                (current_price - last_transaction)*lastBuyQtySlab,
                                current_price,
                                1,
                                buy_margin,
                                sm2,
                                1
                            )
                            updateScript(script_id, investment_balance,
                                         stock_quantity, last_transaction, average_price, 0)
                            # it stores the last buy price of the script
                            last_transaction = getLastBuy(id)[10]
                            last_buy_id = getLastBuy(id)[0]
                            last_sell_id = getLastSellId(id)[0]
                            # print("Last buy id", last_buy_id)
                            # print("Last sell id", last_sell_id)
                            updateLastTransaction(last_sell_id, last_buy_id)
                            createTransctionLog(message, scriptName)
                            transactionList.append(
                                {"scriptName": scriptName, "message": message})
                        except:
                            os.kill(os.getpid(), signal.SIGINT)
                    elif order_status['code'] == -99:
                        last_notified = getLastNotified()
                        if last_notified == date.today().strftime("%Y-%m-%d"):
                            pass
                        else:
                            sendEmail()
                            setLastNotified()
                        return jsonify({"message": -99})
                    else:
                        # createLog(order_status['message'], scriptName)
                        createLog(order_status, scriptName)
                        transactionList.append(
                            {"scriptName": scriptName, "message": order_status['message']})

            # condition for selling at sell margin or condition if sm2 is not met on same day then sell at a value greater than sm1 the next day
                elif (stock_quantity > last_buy_qty_slab and current_price >= last_transaction + (sell_margin / 100) * last_transaction) or (last_transaction_date < date.today() and stock_quantity == last_buy_qty_slab and current_price >= last_transaction + (sell_margin / 100) * last_transaction):
                    # print("In Regular sell condition block")
                    order_status = sell_order(scriptName, last_buy_qty_slab)
                    if order_status['s'] != 'error':
                        try:
                            tradebook = fyers.tradebook()['tradeBook']
                            tradebook.sort(key=sortTradeBook)
                            current_price = tradebook[-1]["tradePrice"]
                            stock_quantity -= last_buy_qty_slab
                            createTransctionLog(
                                f"investment balance={investment_balance}, qtySlab{qty_slab}, currentPrice={current_price}", scriptName)
                            investment_balance += last_buy_qty_slab*last_transaction
                            createTransctionLog(
                                f"investment balance={investment_balance}", scriptName)
                            last_traded_value = current_price
                            # print(
                            #     f"Sold at - {current_price} {last_buy_qty_slab} qty")
                            # print(
                            #     "============================================================================================")
                            message = f"Sold at - {current_price} {last_buy_qty_slab} qty"
                            if stock_quantity == 0:
                                average_price = 0
                            else:
                                average_price = (investment_fund -
                                                 investment_balance)/stock_quantity
                            transactions.insert_transactions(
                                script_id,
                                -1,
                                last_buy_qty_slab,
                                0,
                                0,
                                stock_quantity,
                                investment_balance,
                                (current_price - last_transaction) *
                                last_buy_qty_slab,
                                current_price,
                                1,
                                buy_margin,
                                sell_margin,
                                0
                            )
                            updateScript(script_id, investment_balance,
                                         stock_quantity, last_transaction, average_price, 0)
                            last_transaction = getLastBuy(id)[10]
                            last_buy_id = getLastBuy(id)[0]
                            last_sell_id = getLastSellId(id)[0]
                            # print("Last buy id", last_buy_id)
                            # print("Last sell id", last_sell_id)
                            updateLastTransaction(last_sell_id, last_buy_id)
                            createTransctionLog(message, scriptName)
                            transactionList.append(
                                {"scriptName": scriptName, "message": message})
                        except:
                            os.kill(os.getpid(), signal.SIGINT)
                    elif order_status['code'] == -99:
                        last_notified = getLastNotified()
                        if last_notified == date.today().strftime("%Y-%m-%d"):
                            pass
                        else:
                            sendEmail()
                            setLastNotified()
                        return jsonify({"message": -99})
                    else:
                        # createLog(order_status['message'], scriptName)
                        createLog(order_status['message'], scriptName)
                        transactionList.append(
                            {"scriptName": scriptName, "message": order_status['message']})

            # condition for buying at buy margin
                elif stock_quantity != 0 and current_price <= last_transaction - (buy_margin / 100) * last_transaction and investment_balance >= current_price * qty_slab and stock_quantity <= eligibility_quantity:
                    # print("In regular buy condition")
                    order_status = buy_order(scriptName, qty_slab)
                    if order_status['s'] != 'error':
                        try:
                            tradebook = fyers.tradebook()['tradeBook']
                            tradebook.sort(key=sortTradeBook)
                            current_price = tradebook[-1]["tradePrice"]
                            last_transaction = current_price
                            last_buy_id = getLastBuy(id)[0]
                            stock_quantity += qty_slab
                            createTransctionLog(
                                f"investment balance={investment_balance}, qtySlab{qty_slab}, currentPrice={current_price}", scriptName)
                            investment_balance -= qty_slab*current_price
                            createTransctionLog(
                                f"investment balance={investment_balance}", scriptName)
                            message = f"Bought for - {current_price} {qty_slab} qty"
                            if stock_quantity == 0:
                                average_price = 0
                            else:
                                average_price = (investment_fund -
                                                 investment_balance)/stock_quantity
                            transactions.insert_transactions(
                                script_id,
                                1,
                                qty_slab,
                                current_price -
                                (buy_margin / 100) * current_price,
                                current_price +
                                (sell_margin / 100) * current_price,
                                stock_quantity,
                                investment_balance,
                                0,
                                current_price,
                                0,
                                buy_margin,
                                sell_margin,
                                0
                            )
                            updateScript(script_id, investment_balance,
                                         stock_quantity, last_transaction, average_price, 0)
                            createTransctionLog(message, scriptName)
                            transactionList.append(
                                {"scriptName": scriptName, "message": message})
                        except:
                            os.kill(os.getpid(), signal.SIGINT)
                    else:
                        createLog(order_status['message'], scriptName)
                        transactionList.append(
                            {"scriptName": scriptName, "message": order_status['message']})
                elif (current_price <= market_rate_stoploss):
                    # print("Market Rate Stop Loss Condition")
                    order_status = sell_order(scriptName, stock_quantity)
                    order_id = order_status['id']
                    if order_status['s'] != 'error':
                        try:
                            message = f"Sold at - {current_price} {stock_quantity} qty at Stopp Loss Condition"
                            average_price = investment_fund-investment_balance/stock_quantity
                            transactions.insert_transactions(
                                script_id,
                                -1,
                                stock_quantity,
                                current_price -
                                (buy_margin / 100) * current_price,
                                current_price +
                                (sell_margin / 100) * current_price,
                                0,
                                investment_balance,
                                (current_price - avg_price)*qty_slab,
                                current_price,
                                1,
                                buy_margin,
                                sell_margin,
                                0
                            )
                            updateScript(script_id, investment_balance,
                                         0, last_transaction, average_price, 0)
                            createTransctionLog(message, scriptName)
                            transactionList.append(
                                {"scriptName": scriptName, "message": message})
                        except:
                            os.kill(os.getpid(), signal.SIGINT)
                    else:
                        createLog(order_status['message'], scriptName)
                        transactionList.append(
                            {"scriptName": scriptName, "message": order_status['message']})
                    last_transaction = getLastBuy(id)[10]
                    last_buy_id = getLastBuy(id)[0]
                    last_sell_id = getLastSellId(id)[0]
                    # print("Last buy id", last_buy_id)
                    # print("Last sell id", last_sell_id)
                    updateLastTransaction(last_sell_id, last_buy_id)
                    sql = '{CALL updateScriptActiveStatus(?, ?)}'
                    values = (id, 2)
                    cnxn.execute(sql, values)
                    cnxn.commit()
                else:
                    print("No transaction were made")
            time.sleep(1)
        return jsonify(transactionList)
    else:
        print("Market Closed")
        cnxn.execute(
            f"update scripts set active_flag = 0 where active_flag = 1 and isdeleted = 0")
        cnxn.commit()
        isExist = os.path.exists(f'fyersTradebook_{date.today()}.csv')
        if not isExist:
            createAPILog(f"Fyers tradebook")
            df = pd.DataFrame(fyers.tradebook()['tradeBook'])
            df.to_csv(f'fyersTradebook_{date.today()}.csv')
        # code for conciliation
        positions = fyers.positions()
        isExist = os.path.exists(f'ConciliationReport_{date.today()}.csv')
        if not isExist:
            fyersTradebook = fyers.tradebook()['tradeBook']
            todaysTransaction = transactions.getTodaysTransaction()
            fyersTradebook.sort(key=sortTradeBook)
            concilitionReport = []
            for transaction in reversed(range(len(fyersTradebook))):
                # print(todaysTransaction[transaction]["order_date"])
                concilitionReport.append({
                    "fy_orderDate": fyersTradebook[transaction]["orderDateTime"],
                    "SAP_orderDate": todaysTransaction[transaction]["order_date"].strftime('%Y-%m-%d %H:%M:%S'),
                    "fy_qtySlab": fyersTradebook[transaction]["tradedQty"],
                    "SAP_qtySlab": todaysTransaction[transaction]["qty_slab"],
                    "fy_tradedPrice": fyersTradebook[transaction]["tradePrice"],
                    "SAP_tradedPrice": todaysTransaction[transaction]["buy_rate"],
                    "fy_tradeValue": fyersTradebook[transaction]["tradeValue"],
                    "SAP_tradeValue": todaysTransaction[transaction]["buy_rate"]*todaysTransaction[transaction]["qty_slab"],
                    "symbol": fyersTradebook[transaction]["symbol"]
                })
            df = pd.DataFrame(concilitionReport)
            df.to_csv(f'conciliation_report{date.today()}.csv')
        return jsonify({"message": "Market Closed"})


if __name__ == '__main__':
    app.register_blueprint(scripts.script)
    app.register_blueprint(transactions.transaction)
    app.register_blueprint(logic2.logic2)
    app.run(debug=True, port=8001)
