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

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": "*"}})

# connection string
cnxn_str = ("Driver={SQL Server Native Client 11.0};"
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
redirect_uri = "https://www.google.com/"
client_id = "1P2PP0NTZ1-100"
secret_key = "B7SFK0LMYT"
grant_type = "authorization_code"
response_type = "code"
state = "sample"
initial_flag = 0
last_transaction = 0
quantity_balance = 0
# last_transaction = 0
last_buy_id = 0
last_transaction_date = date.today()

key = "secret"
# -------------------------------Code to test-----------------------------------------


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
# -----------------------------------Code to test--------------------------------------

# Login auth code


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


# code to generate error logs
def createLog(msg, scriptName):
    file = open('Errorlogs.txt', 'a')
    file.writelines(f"\n{datetime.now()}-{scriptName} - {msg}")
    file.close()

# place order


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
    return fyers.place_order(data)

# function to get symbol list


def getAllCodes():
    symbolDataLink = "final_Output.csv"
    symbolData = pd.read_csv(symbolDataLink)
    scriptCode = []

    for data in symbolData.iterrows():
        scriptCode.append(data[1][0])
    return scriptCode

# function to call buy method


def buy_order(symbol, qty):
    return placeorder(symbol, 1, qty)

# function to call sell method


def sell_order(symbol, qty):
    return placeorder(symbol, -1, qty)

# function to call modify order


def modifyOrder(id, stopLoss, qty):
    print("Modify Order")
    data = {
        "id": id,
        "type": 1,
        "stopLoss": stopLoss,
        "qty": qty
    }
    print(fyers.modify_order(data))


# Route for Insert script
@app.route('/InsertScript', methods=['POST'])
@token_required
def insert_scripts():
    # for x in scripts:
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        # print(json)
    else:
        return 'Content-Type not supported!'

    cursor.execute(
        f"select *from scripts where script_name = '{json['selectedScript']['code']}'")
    result = cursor.fetchone()
    print(result)
    if result == None or result[12] == 1:
        sql = '{CALL InsertScript(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?)}'
        values = (json['selectedScript']['code'], 0, json['buyMargin'], json['sellMargin'],
                  0, json['resetCriteria'], json['investmentAmount'], -1, json['investmentAmount'], 0, json['specificValue'], json['marginalValue'], 0, json['market_rate_stoploss'])
        cnxn.execute(sql, values)
        cnxn.commit()
        return jsonify("Success")
    else:
        return jsonify({"message": f"{json['selectedScript']['code']} is already added!"})

# function for insert transaction


def insert_transactions(scriptId, orderType, qtySlab, buyTarget, sellTarget, qtyBalance, scriptFundBalance, Profit, buyRate, Bings, buyMargin, sellMargin):
    sql = '{CALL InsertTransaction(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}'
    values = (scriptId, orderType, qtySlab, buyTarget, sellTarget,
              qtyBalance, scriptFundBalance, Profit, buyRate, Bings, buyMargin, sellMargin)
    cnxn.execute(sql, values)
    cnxn.commit()

# function to get script by id


def getScriptById(Id):
    sql = '{CALL getScriptData(?)}'
    values = (Id)
    cursor.execute(sql, values)
    row = cursor.fetchone()
    return row

# Function to get the last buy record


def getLastBuy(scriptId):
    sql = '{CALL getLastBuyByScriptId(?)}'
    values = (scriptId)
    cursor.execute(sql, values)
    result = cursor.fetchone()
    return result

# function to get the id of last sell


def getLastSellId(scriptId):
    sql = '{CALL getLastSellId(?)}'
    values = (scriptId)
    cursor.execute(sql, values)
    result = cursor.fetchone()
    return result


# function to update sell id for last buy
def updateLastTransaction(sellId, buyId):
    sql = '{CALL updateSellIdForBuy(?, ?)}'
    values = (sellId, buyId)
    cursor.execute(sql, values)

# get transaction by id


def GetTransactionByScriptId(Id):
    sql = '{CALL getAlltransactions(?)}'
    values = (Id)
    cursor.execute(sql, values)
    row = cursor.fetchone()
    return row

# get average by script id


def getAvgPriceByScriptId(id):
    sql = '{CALL getAvgPriceByScriptId(?)}'
    values = (id)
    cursor.execute(sql, values)
    return cursor.fetchone()[0]

# get sm2 flag by id


def getsm2FlagById(id):
    sql = '{CALL getSm2FlagById(?)}'
    values = (id)
    cursor.execute(sql, values)
    return cursor.fetchone()[0]


def getTodaysProfit():

    sql = '{CALL getTodaysProfit()}'
    cursor.execute(sql)
    return cursor.fetchone()[0]


# function to  get  deal  by id


def getDealById(id):

    sql = '{CALL getDealByScriptId(?)}'
    values = (id)
    cursor.execute(sql, values)
    return cursor.fetchone()[0]


# update script by id


def updateScript(id, investmentBalance, qtyBalance, lastTransactions, averagePrice, sm2Flag):
    sql = '{CALL UpdateScriptForTransaction(?, ?, ?, ?, ?, ?)}'
    values = (id, investmentBalance, qtyBalance,
              lastTransactions, averagePrice, sm2Flag)
    cnxn.execute(sql, values)
    cnxn.commit()

# delete scripts by id


def deleteScriptById(id, scriptName, qty):
    sql = '{CALL DeleteScript(?)}'
    values = (id)
    placeorder(scriptName, -1, qty)
    cursor.execute(sql, id)
    cnxn.commit()

# function to get current price script by id


def updateScriptCurrentPriceById(id, current_price, deal):
    sql = '{CALL [updateCurrentPriceByscriptId](?, ?, ?)}'
    values = (id, current_price, deal)
    cnxn.execute(sql, values)
    cnxn.commit()


# function to edit script by id
def UpdateScriptById(id, investmentBalance, buyMargin, sellMargin, resetCriteria, specificValue, marginalValue, sm2Flag,  market_rate_stoploss):
    sql = '{CALL editScriptForm(?, ?, ?, ?, ?, ?, ?, ?, ?)}'
    values = (id, investmentBalance, buyMargin,
              sellMargin, resetCriteria, specificValue, marginalValue, sm2Flag,  market_rate_stoploss)
    cnxn.execute(sql, values)
    cnxn.commit()

# ------------------------------------------------------------------------------


def getLastTransactionByScriptId(id):
    sql = '{CALL getLastTradedPriceByScriptId(?)}'
    values = (id)
    cursor.execute(sql, values)
    print(cursor.fetchone())
    if cursor.fetchone() != None:
        return cursor.fetchone()[0]
    else:
        return 0
# ----------------------------------------------------------------------------------

# Route to Get all Scripts


@ app.route('/GetAllScripts', methods=['GET'])
@ token_required
def getAllScripts():
    columns = ['id', 'scriptName', 'scriptId', 'buyMargin', 'sellMargin', 'quantityBalance',
               'startDate', 'resetCriteria',  'investmentBalance', 'activeFlag', 'investmentFund', 'lastTransaction', 'isdeleted', 'avgPrice', 'currentprice', 'deal', 'specificValue', 'marginalValue', 'sm2Flag',  'market_rate_stoploss']
    cursor.execute('select * from scripts')
    result = []
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    return jsonify(result)

# Route to Get all Scripts by id


@ app.route('/GetScriptById/<id>', methods=['GET'])
@ token_required
def getScriptById(id):
    columns = ['id', 'scriptName', 'scriptId', 'buyMargin', 'sellMargin', 'quantityBalance',
               'startDate', 'resetCriteria',  'investmentBalance', 'activeFlag', 'investmentFund', 'lastTransaction', 'isdeleted', 'avgPrice', 'currentprice', 'deal', 'specificValue', 'marginalValue', 'sm2Flag',  'market_rate_stoploss']
    cursor.execute(f"select * from scripts where id = {id}")
    result = cursor.fetchone()
    result[16] = float(result[16])
    result = (dict(zip(columns, result)))
    print(result)
    return jsonify(result)
# Route to get update active status


@ app.route('/UpdateActiveStatus', methods=['POST'])
@ token_required
def updateActiveStatus():
    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):
        json = request.json
    cursor.execute(
        f"update scripts set active_flag = {json['activeStatus']} where id = {json['scriptId']}")
    cnxn.commit()
    return jsonify("Success")

# Route to get all script code


@ app.route('/GetAllScriptCode', methods=["GET"])
@ token_required
def getAllScriptsCode():
    scriptCodeList = []
    scriptCodes = getAllCodes()
    for script in scriptCodes:
        scriptCodeList.append({"name": script, "code": script})
    return scriptCodeList

# Route to  get transaction by id


@ app.route('/getTransactionById/<id>', methods=['GET'])
@ token_required
def GetTransactionByScriptId(id):
    result = []
    columns = ['scriptId', 'scriptName', 'orderDate', 'orderType', 'qtySlab', 'buyTarget', 'sellTarget',
               'qtyBalance', 'scriptFundBalance', 'profit', 'buyRate', 'buyMargin', 'sellMargin']
    sql = '{CALL GetTransactionByScriptId(?)}'
    values = (id)
    cursor.execute(sql, values)
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    return jsonify(result)

# Route to  get Current price by id


@ app.route("/updateScriptsCurrentPrice", methods=["GET"])
@ token_required
def update_script_current_price_by_id():
    columns = ['id', 'scriptName', 'scriptId', 'buyMargin', 'sellMargin', 'quantityBalance',
               'startDate', 'resetCriteria',  'investmentBalance', 'activeFlag', 'investmentFund', 'lastTransaction', 'isdeleted', 'avgPrice', 'currentprice']
    cursor.execute('select * from scripts where isdeleted = 0')
    result = []
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    for row in result:
        data = {"symbols": f"NSE:{row['scriptName']}-EQ"}
        current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
        avg_price = float(row["avgPrice"])
        qty = row["quantityBalance"]
        # print("avg", avg_price)
        # print("qty", qty)
        # print("cp", current_price)
        deal = (current_price - avg_price)*qty
        updateScriptCurrentPriceById(row["id"], current_price, deal)
        time.sleep(0.1)
    return jsonify("Updated")

# Route to Delete Script By id


@ app.route('/DeleteScriptById', methods=['DELETE'])
@ token_required
def deletescriptbyid():
    args = request.args
    id = args.to_dict()["id"]

    scriptName = args.to_dict()["scriptName"]
    qty = args.to_dict()["qty"]
    status = int(args.to_dict()["status"])
    print("id:", id, "qty:", qty, "scriptName:",
          scriptName, "status:", status)
    data = {"symbols": f"NSE:{scriptName}-EQ"}
    if (fyers.quotes(data)):
        current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
    if status == -1:
        deleteScriptById(id, scriptName, qty)
    else:
        print("current price", current_price)
        print("las transaction", last_transaction)
        print("qty", qty)
        avg_price = getAvgPriceByScriptId(id)
        insert_transactions(
            id, -1, qty, 0, 0, 0, 0, (float(current_price) - float(avg_price))*float(qty), 0, 0, 0, 0)
        updateScript(id, 0, 0, current_price, 0, 0)
        deleteScriptById(id, scriptName, qty)

    return jsonify("Success")

# Route for updating the script status by id (live, paused)


@ app.route('/UpdateScriptStatusById', methods=['GET'])
@ token_required
def update_script_status_by_id():
    args = request.args
    id = args.to_dict()["id"]
    status = args.to_dict()["status"]
    sql = '{CALL updateScriptActiveStatus(?, ?)}'
    values = (id, status)
    cnxn.execute(sql, values)
    cnxn.commit()

    return jsonify("Success")

# Route to get transaction for current date


@app.route('/getTodaysProfit', methods=['GET'])
@token_required
def getTodaysProfit():

    sql = '{CALL getTodaysProfit()}'
    cursor.execute(sql)
    return jsonify(cursor.fetchone()[0])


@ app.route('/GetTransactionForCurrentDate', methods=['GET'])
@ token_required
def transactionForCurrentDate():
    result = []
    columns = ['scriptId', 'scriptName', 'orderDate', 'orderType', 'qtySlab', 'buyTarget', 'sellTarget',
               'qtyBalance', 'scriptFundBalance', 'profit', 'buyRate']
    sql = '{CALL getAlltransactions()}'
    cursor.execute(sql)
    for row in cursor.fetchall():
        result.append(dict(zip(columns, row)))
    return jsonify(result)

# code for update script details by id


@ app.route('/UpdateScriptById', methods=['PUT'])
@ token_required
def update_script_by_id():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        print(json)
    else:
        return 'Content-Type not supported!'
    market_rate_stoploss = json["market_rate_stoploss"]
    print("market_rate_stop", market_rate_stoploss)
    # stop_loss = json["stop_loss"]
    # stop_loss_percentage = json["stop_loss_percentage"]
    # stop_loss_value = json["stop_loss_value"]
    marginalValue = json["marginalValue"]
    specificValue = json["specificValue"]
    resetCriteria = json["resetCriteria"]
    buyMargin = json["buyMargin"]
    sellMargin = json["sellMargin"]
    investmentAmount = json["investmentAmount"]
    id = json["id"]
    sm2Flag = json["sm2Flag"]

    UpdateScriptById(id, investmentAmount, buyMargin,
                     sellMargin, resetCriteria, specificValue, marginalValue, sm2Flag,  market_rate_stoploss)
    return jsonify("Success")

# CODE FOR  GET PROFIT BY SCRIPT ID


@ app.route('/getProfitByScriptId/<id>', methods=['GET'])
@ token_required
def getProfitByScriptId(id):
    sql = '{CALL getProfitByScriptId(?)}'
    values = (id)
    result = cnxn.execute(sql, values)
    profit = result.fetchone()[0]
    return {"profit": profit}


# ROUTE FOR LOGIN USER

# ------------------------------Code to test--------------------------------------------------


@ app.route("/authenticate", methods=["POST"])
def authenticate():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json

        cursor.execute(
            f"select * from users where username='{json['username']}' and password='{json['password']}'")
        if (cursor.fetchone()):
            token = jwt.encode({'user': json["username"], 'exp': datetime.utcnow(
            ) + timedelta(days=1)}, "secret", "HS256")
        else:
            return jsonify({"message": "Invalid Credentials"}), 404

        return jsonify({"token": token})
# -------------------------------Code to test-----------------------------------------------------

# ROUTE TO GET CURRENT PRICE FOR SELECTED SCRIPT IN ADD SCRIPT FORM


@ app.route("/currentPriceForSelectedScript", methods=["GET"])
@ token_required
def currentPriceForSelectedScript():
    args = request.args
    data = {"symbols": f"NSE:{args['code']}-EQ"}
    current_price = float(fyers.quotes(data)["d"][0]["v"]["lp"])
    return jsonify({"currentPrice": current_price})

# Route for starting the program


@ app.route('/StartProgram/<id>', methods=['GET'])
@ token_required
def start_program(id):
    # print("Average Price", getAvgPriceByScriptId(id))
    last_traded_value = 0
    cursor.execute(f"select * from scripts where id = {id}")
    rowdata = cursor.fetchone()
    data = {"symbols": f"NSE:{rowdata[1]}-EQ"}
    current_price = float(fyers.quotes(data)["d"][0]["v"]["lp"])
    scriptName = rowdata[1]
    investment_balance = float(rowdata[8])
    buy_margin = rowdata[3]
    sell_margin = rowdata[4]
    last_transaction = rowdata[11]
    last_transaction_date = date.today()
    reset_criteria = rowdata[7]
    sm2_flag = getsm2FlagById(id)
    print("sm2 flag", sm2_flag)

    deal = rowdata[15]
    average_price = rowdata[13]
    market_rate_stoploss = rowdata[19]
    startFlag = 1
# -------------------------------------------------------------------
    specific_value = rowdata[16]
    marginal_value = rowdata[17]
    if getLastTransactionByScriptId(id):
        last_traded_value = getLastTransactionByScriptId(rowdata[0])
# --------------------------------------------------------------------
    # get last transaction for the script if only exists
    if getLastBuy(id):
        last_transaction = getLastBuy(id)[10]
        last_buy_id = getLastBuy(id)[0]
        last_transaction_date = str(getLastBuy(id)[1])
        last_transaction_date = datetime.strptime(
            last_transaction_date[0:10], '%Y-%m-%d').date()
    stock_quantity = rowdata[5]
    investment_fund = rowdata[10]
    script_id = rowdata[0]
    eligibility_quantity = int(investment_fund/current_price)
    qty_slab = int(eligibility_quantity/5)
    sm2 = 2*sell_margin
    query = cnxn.execute(
        f"select active_flag from scripts where id = {id}")

    status = int(query.fetchone()[0])

    if stock_quantity == 0 and last_transaction == 0:
        # code for placing a buy order and store the response in order_status
        order_status = buy_order(scriptName, qty_slab)
        if order_status['s'] != 'error':
            print(f"Initial Buy for - {current_price} {qty_slab} qty")
            stock_quantity += qty_slab  # stock_quantity= stock_quantity + qty_slab
            investment_balance -= qty_slab*current_price
            last_transaction = current_price
            # last_buy_id = getLastBuy(id)[0]
            average_price = current_price
            print(average_price)
            insert_transactions(
                script_id,
                1,
                qty_slab,
                current_price - (buy_margin / 100) * current_price,
                current_price + (sell_margin / 100) * current_price,
                stock_quantity,
                investment_balance,
                0,
                current_price,
                0,
                buy_margin,
                sell_margin
            )
            updateScript(script_id, investment_balance,
                         stock_quantity, current_price, average_price, 1)
        else:
            createLog(order_status['message'], scriptName)
    # run the below code while market is not closed
    print("status", status)
    print("time", datetime.now() < datetime.now().replace(
        hour=15, minute=30, second=0, microsecond=0))
    while ((status == 1 or startFlag == 1) and datetime.now() < datetime.now().replace(
            hour=15, minute=30, second=0, microsecond=0)):
        startFlag = 0

        # invested_value = average_price * stock_quantity
        # market_value = current_price * stock_quantity
        # loss_percent = (invested_value - market_value)/invested_value * 100
        # loss_value = market_value - invested_value
        # print(loss_value)
        # print("Value", abs(loss_value) >= abs(stop_loss_value))
        # print("Criteria", stop_loss)
        # print("Quantity", stock_quantity >= eligibility_quantity)
        # Code for initial buy or if stock quantity is 0
        # added to get the updated sm2Flag column value in each loop
        sm2_flag = getsm2FlagById(id)
        if stock_quantity == 0 and reset_criteria == 1 and last_transaction != 0 and investment_balance >= current_price * qty_slab:
            order_status = buy_order(scriptName, qty_slab)
            if order_status['s'] != 'error':
                print(f"spot buy- {current_price} {qty_slab} qty")
                stock_quantity += qty_slab
                investment_balance -= qty_slab*current_price
                last_transaction = current_price

                # last_buy_id = getLastBuy(id)[0]
                average_price = current_price
                # average_price = (getAvgPriceByScriptId(id) + current_price)/2
                insert_transactions(
                    script_id,
                    1,
                    qty_slab,
                    current_price - (buy_margin / 100) * current_price,
                    current_price + (sell_margin / 100) * current_price,
                    stock_quantity,
                    investment_balance,
                    0,
                    current_price,
                    0,
                    buy_margin,
                    sell_margin
                )
                updateScript(script_id, investment_balance,
                             stock_quantity, current_price, average_price, 1)
            else:
                createLog(order_status['message'], scriptName)
        elif stock_quantity == 0 and current_price <= last_traded_value - (marginal_value / 100) * last_traded_value and reset_criteria == 2 and last_traded_value != 0 and investment_balance >= current_price * qty_slab:
            order_status = buy_order(scriptName, qty_slab)
            if order_status['s'] != 'error':
                print(f"marginal buy - {current_price} {qty_slab} qty")
                stock_quantity += qty_slab
                investment_balance -= qty_slab*current_price
                last_transaction = current_price
                last_traded_value = current_price
                # last_buy_id = getLastBuy(id)[0]
                average_price = current_price
                insert_transactions(
                    script_id,
                    1,
                    qty_slab,
                    current_price - (buy_margin / 100) * current_price,
                    current_price + (sell_margin / 100) * current_price,
                    stock_quantity,
                    investment_balance,
                    0,
                    current_price,
                    0,
                    buy_margin,
                    sell_margin
                )
                updateScript(script_id, investment_balance,
                             stock_quantity, current_price, average_price, 1)
            else:
                createLog(order_status['message'], scriptName)

        elif stock_quantity == 0 and reset_criteria == 3 and current_price <= specific_value and investment_balance >= current_price * qty_slab:
            order_status = buy_order(scriptName, qty_slab)
            if order_status['s'] != 'error':
                print(f"specific value - {current_price} {qty_slab} qty")
                stock_quantity += qty_slab
                investment_balance -= qty_slab*current_price
                last_transaction = current_price
                last_buy_id = getLastBuy(id)[0]
                average_price = current_price
                insert_transactions(
                    script_id,
                    1,
                    qty_slab,
                    current_price - (buy_margin / 100) * current_price,
                    current_price + (sell_margin / 100) * current_price,
                    stock_quantity,
                    investment_balance,
                    0,
                    current_price,
                    0,
                    buy_margin,
                    sell_margin
                )
                updateScript(script_id, investment_balance,
                             stock_quantity, current_price, average_price, 1)
            else:
                createLog(order_status['message'], scriptName)
        print("============================================================================================")
        print(f"Script Name : {scriptName}  ")
        print(f"Stock Quantity:{stock_quantity}")
        print(f"Last transaction: {last_transaction}")
        print(fyers.quotes(data))
        if (fyers.quotes(data)):
            current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
            print("current price =", current_price)

            # Condition for selling at sm2 rate
            print(last_transaction)
            if stock_quantity != 0 and stock_quantity == qty_slab and current_price >= last_transaction + (sm2 / 100) * last_transaction and last_transaction != 0 and sm2_flag == 1:
                print("In Sell Order block with sm2")
                order_status = sell_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    stock_quantity -= qty_slab
                    investment_balance += qty_slab*current_price + \
                        (current_price - last_transaction)*qty_slab
                    last_traded_value = current_price
                    print(
                        f"Sold at - {current_price} {qty_slab} qty")
                    print(
                        "============================================================================================")
                    if stock_quantity == 0:
                        average_price = 0
                    else:
                        average_price = (investment_fund -
                                         investment_balance)/stock_quantity
                    insert_transactions(
                        script_id,
                        -1,
                        qty_slab,
                        current_price - (buy_margin / 100) * current_price,
                        current_price + (sm2 / 100) * current_price,
                        stock_quantity,
                        investment_balance,
                        (current_price - last_transaction)*qty_slab,
                        current_price,
                        1,
                        buy_margin,
                        sm2
                    )
                    updateScript(script_id, investment_balance,
                                 stock_quantity, last_transaction, average_price, 0)
                    # it stores the last buy price of the script
                    last_transaction = getLastBuy(id)[10]
                    last_buy_id = getLastBuy(id)[0]
                    last_sell_id = getLastSellId(id)[0]
                    updateLastTransaction(last_sell_id, last_buy_id)
                else:
                    createLog(order_status['message'], scriptName)

            # condition for selling at sell margin or condition if sm2 is not met on same day then sell at a value greater than sm1 the next day
            elif (stock_quantity > qty_slab and current_price >= last_transaction + (sell_margin / 100) * last_transaction) or (last_transaction_date < date.today() and stock_quantity == qty_slab and current_price >= last_transaction + (sell_margin / 100) * last_transaction):
                print("In Regular sell condition block")
                order_status = sell_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    stock_quantity -= qty_slab
                    investment_balance += qty_slab*current_price + \
                        (current_price - last_transaction)*qty_slab
                    last_traded_value = current_price
                    print(
                        f"Sold at - {current_price} {qty_slab} qty")
                    print(
                        "============================================================================================")
                    if stock_quantity == 0:
                        average_price = 0
                    else:
                        average_price = (investment_fund -
                                         investment_balance)/stock_quantity
                    insert_transactions(
                        script_id,
                        -1,
                        qty_slab,
                        current_price - (buy_margin / 100) * current_price,
                        current_price + (sell_margin / 100) * current_price,
                        stock_quantity,
                        investment_balance,
                        (current_price - last_transaction)*qty_slab,
                        current_price,
                        1,
                        buy_margin,
                        sell_margin
                    )
                    updateScript(script_id, investment_balance,
                                 stock_quantity, last_transaction, average_price, 0)
                    last_transaction = getLastBuy(id)[10]
                    last_buy_id = getLastBuy(id)[0]
                    last_sell_id = getLastSellId(id)[0]
                    updateLastTransaction(last_sell_id, last_buy_id)
                else:
                    createLog(order_status['message'], scriptName)

            # condition for buying at buy margin
            elif stock_quantity != 0 and current_price <= last_transaction - (buy_margin / 100) * last_transaction and investment_balance >= current_price * qty_slab and stock_quantity <= eligibility_quantity:
                print("In regular buy condition")
                order_status = buy_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    last_transaction = current_price
                    last_buy_id = getLastBuy(id)[0]
                    stock_quantity += qty_slab
                    investment_balance -= qty_slab*current_price
                    print(
                        f"Bought for - {current_price} {qty_slab} qty")
                    print(
                        "============================================================================================")
                    if stock_quantity == 0:
                        average_price = 0
                    else:
                        average_price = (investment_fund -
                                         investment_balance)/stock_quantity
                    insert_transactions(
                        script_id,
                        1,
                        qty_slab,
                        current_price - (buy_margin / 100) * current_price,
                        current_price + (sell_margin / 100) * current_price,
                        stock_quantity,
                        investment_balance,
                        0,
                        current_price,
                        0,
                        buy_margin,
                        sell_margin

                    )
                    updateScript(script_id, investment_balance,
                                 stock_quantity, last_transaction, average_price, 0)
                else:
                    createLog(order_status['message'], scriptName)
            # elif ((loss_value <= -stop_loss_value and stop_loss == 2 and stop_loss_value != 0) or (loss_percent >= stop_loss_percentage and stop_loss == 1 and stop_loss_percentage != 0)) and stock_quantity >= eligibility_quantity:
            #     print("Stop Loss Condition")

            #     order_status = sell_order(scriptName, stock_quantity)
            #     order_id = order_status['id']
            #     if order_status['s'] != 'error':
            #         investment_balance = 0
            #         print(
            #             f"Sold at - {current_price} {stock_quantity} qty")
            #         print(
            #             "============================================================================================")
            #         average_price = investment_fund-investment_balance/stock_quantity
            #         insert_transactions(
            #             script_id,
            #             -1,
            #             stock_quantity,
            #             current_price - (buy_margin / 100) * current_price,
            #             current_price + (sell_margin / 100) * current_price,
            #             0,
            #             investment_balance,
            #             (current_price - last_transaction)*qty_slab,
            #             current_price,
            #             1,
            #             buy_margin,
            #             sell_margin
            #         )
            #         updateScript(script_id, investment_balance,
            #                      0, last_transaction, average_price, 0)
            #     else:
            #         createLog(order_status['message'], scriptName)
            #     last_transaction = getLastBuy(id)[10]
            #     last_buy_id = getLastBuy(id)[0]
            #     last_sell_id = getLastSellId(id)[0]
            #     updateLastTransaction(last_sell_id, last_buy_id)
            #     sql = '{CALL updateScriptActiveStatus(?, ?)}'
            #     values = (id, 2)
            #     cnxn.execute(sql, values)
            #     cnxn.commit()
            elif (current_price <= market_rate_stoploss):
                print("Market Rate Stop Loss Condition")

                order_status = sell_order(scriptName, stock_quantity)
                order_id = order_status['id']
                if order_status['s'] != 'error':
                    investment_balance = stock_quantity * current_price
                    print(
                        f"Sold at - {current_price} {stock_quantity} qty")
                    print(
                        "============================================================================================")
                    average_price = investment_fund-investment_balance/stock_quantity
                    insert_transactions(
                        script_id,
                        -1,
                        stock_quantity,
                        current_price - (buy_margin / 100) * current_price,
                        current_price + (sell_margin / 100) * current_price,
                        0,
                        investment_balance,
                        (current_price - last_transaction)*qty_slab,
                        current_price,
                        1,
                        buy_margin,
                        sell_margin
                    )
                    updateScript(script_id, investment_balance,
                                 0, last_transaction, average_price, 0)
                else:
                    createLog(order_status['message'], scriptName)
                last_transaction = getLastBuy(id)[10]
                last_buy_id = getLastBuy(id)[0]
                last_sell_id = getLastSellId(id)[0]
                updateLastTransaction(last_sell_id, last_buy_id)
                sql = '{CALL updateScriptActiveStatus(?, ?)}'
                values = (id, 2)
                cnxn.execute(sql, values)
                cnxn.commit()
            else:

                print("No transaction were made")
                print(
                    "=======================================================================================")
        query = cnxn.execute(
            f"select active_flag from scripts where id = {id}")
        status = int(query.fetchone()[0])
        time.sleep(300)
    else:
        print("Market Closed")
        sql = '{CALL updateScriptActiveStatus(?, ?)}'
        values = (id, 0)
        cnxn.execute(sql, values)
        cnxn.commit()
        return jsonify({"message": "Market Closed"})


if __name__ == '__main__':
    # app.debug = True
    # app.run()
    app.run(debug=True, port=8001)
