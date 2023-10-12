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
import pdb
import traceback

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
access_token = ""
# fyers = ""
session = accessToken.SessionModel(client_id=client_id, secret_key=secret_key,
                                   redirect_uri=redirect_uri, response_type="code", grant_type="authorization_code")
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


@app.route('/setAuthCode', methods=['GET'])
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
    print(response)
    fyers = fyersModel.FyersModel(
        token=response, is_async=False, client_id=client_id, log_path="")
    return jsonify("success")

# code to generate error logs


def createLog(msg, scriptName):
    try:
        file = open('errorLogs.txt', 'a')
        file.writelines(f"\n{datetime.now()}-{scriptName} - {msg}")
    except:
        with open('errorLogs.txt', 'w') as f:
            traceback.print_exc(file=f)

# code to generate transactions logs


def createTransctionLog(msg, scriptName):
    try:
        file = open('TransactionErrorlogs.txt', 'a')
        file.writelines(f"\n{datetime.now()}-{scriptName} - {msg}")
    except:
        with open('TransactionErrorlogs.txt', 'w') as f:
            traceback.print_exc(file=f)

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
    try:
        symbolDataLink = "final_Output.csv"
        symbolData = pd.read_csv(symbolDataLink)
        scriptCode = []

        for data in symbolData.iterrows():
            scriptCode.append(data[1][0])
        return scriptCode
    except Exception as e:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify("Error", e), 500

# function to call buy method


def buy_order(symbol, qty):
    return placeorder(symbol, 1, qty)

# function to call sell method


def sell_order(symbol, qty):
    return placeorder(symbol, -1, qty)


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
    try:
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
    except Exception as e:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"messge": str(e)})
# function for insert transaction


def insert_transactions(scriptId, orderType, qtySlab, buyTarget, sellTarget, qtyBalance, scriptFundBalance, Profit, buyRate, Bings, buyMargin, sellMargin, sm2sell):
    try:
        sql = '{CALL InsertTransaction(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}'
        values = (scriptId, orderType, qtySlab, buyTarget, sellTarget,
                  qtyBalance, scriptFundBalance, Profit, buyRate, Bings, buyMargin, sellMargin, sm2sell)
        cnxn.execute(sql, values)
        cnxn.commit()

    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
# function to get script by id


def getScriptById(Id):
    try:
        sql = '{CALL getScriptData(?)}'
        values = (Id)
        cursor.execute(sql, values)
        row = cursor.fetchone()
        return row
    except Exception as e:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
# Function to get the last buy record


def getLastBuy(scriptId):
    try:
        sql = '{CALL getLastBuyByScriptId(?)}'
        values = (scriptId)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
# function to get the id of last sell


def getLastBuyQtySlab(scriptId):
    try:
        sql = '{CALL getLastBuyQtySlab(?)}'
        values = (scriptId)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)


def getLastSellId(scriptId):
    try:
        sql = '{CALL getLastSellId(?)}'
        values = (scriptId)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)


# function to update sell id for last buy
def updateLastTransaction(sellId, buyId):
    try:
        sql = '{CALL updateSellIdForBuy(?, ?)}'
        values = (sellId, buyId)
        cursor.execute(sql, values)
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)

# get transaction by id


def GetTransactionByScriptId(Id):
    try:
        sql = '{CALL getAlltransactions(?)}'
        values = (Id)
        cursor.execute(sql, values)
        row = cursor.fetchone()
        return row
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
# get average by script id


def getAvgPriceByScriptId(id):
    try:
        sql = '{CALL getAvgPriceByScriptId(?)}'
        values = (id)
        cursor.execute(sql, values)
        return cursor.fetchone()[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
# get sm2 flag by id


def getsm2FlagById(id):
    try:
        sql = '{CALL getSm2FlagById(?)}'
        values = (id)
        cursor.execute(sql, values)
        return cursor.fetchone()[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)


def getTodaysProfit():
    try:
        sql = '{CALL getTodaysProfit()}'
        cursor.execute(sql)
        return cursor.fetchone()[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)


def getScriptProfit():
    try:
        sql = '{CALL getTotalProfitByScriptId()}'
        cursor.execute(sql)
        return cursor.fetchone()[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)


# function to  get  deal  by id


def getDealById(id):
    try:
        sql = '{CALL getDealByScriptId(?)}'
        values = (id)
        cursor.execute(sql, values)
        return cursor.fetchone()[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
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
            traceback.print_exc(file=f)
# delete scripts by id


def deleteScriptById(id, scriptName, qty):
    try:
        order_status = placeorder(scriptName, -1, qty)
        if order_status['s'] != 'error':
            sql = '{CALL DeleteScript(?)}'
            values = (id)
            cursor.execute(sql, values)
            cnxn.commit()
        else:
            createLog(order_status['message'], scriptName)

    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)

# function to get current price script by id


def updateScriptCurrentPriceById(id, current_price, deal):
    try:
        sql = '{CALL updateCurrentPriceByscriptId(?, ?, ?)}'
        values = (id, current_price, deal)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)


# function to edit script by id
def UpdateScriptById(id, investmentBalance, buyMargin, sellMargin, resetCriteria, specificValue, marginalValue, sm2Flag,  market_rate_stoploss):
    try:
        sql = '{CALL editScriptForm(?, ?, ?, ?, ?, ?, ?, ?, ?)}'
        values = (id, investmentBalance, buyMargin,
                  sellMargin, resetCriteria, specificValue, marginalValue, sm2Flag,  market_rate_stoploss)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
# ------------------------------------------------------------------------------


def getLastTransactionByScriptId(id):
    try:
        sql = '{CALL getLastTradedPriceByScriptId(?)}'
        values = (id)
        cursor.execute(sql, values)
        print(cursor.fetchone())
        if cursor.fetchone() != None:
            return cursor.fetchone()[0]
        else:
            return 0
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
# ----------------------------------------------------------------------------------

# Route to Get all Scripts


@ app.route('/GetAllScripts', methods=['GET'])
@ token_required
def getAllScripts():
    try:
        columns = ['id', 'scriptName', 'scriptId', 'buyMargin', 'sellMargin', 'quantityBalance',
                   'startDate', 'resetCriteria',  'investmentBalance', 'activeFlag', 'investmentFund', 'lastTransaction', 'isdeleted', 'avgPrice', 'currentprice', 'deal', 'specificValue', 'marginalValue', 'sm2Flag',  'market_rate_stoploss']
        cursor.execute('select * from scripts')
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# Route to Get all Scripts by id


@ app.route('/GetScriptById/<id>', methods=['GET'])
@ token_required
def getScriptById(id):
    try:
        columns = ['id', 'scriptName', 'scriptId', 'buyMargin', 'sellMargin', 'quantityBalance',
                   'startDate', 'resetCriteria',  'investmentBalance', 'activeFlag', 'investmentFund', 'lastTransaction', 'isdeleted', 'avgPrice', 'currentprice', 'deal', 'specificValue', 'marginalValue', 'sm2Flag',  'market_rate_stoploss']
        cursor.execute(f"select * from scripts where id = {id}")
        result = cursor.fetchone()
        result[16] = float(result[16])
        result = (dict(zip(columns, result)))
        print(result)
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# Route to get update active status


@ app.route('/UpdateActiveStatus', methods=['POST'])
@ token_required
def updateActiveStatus():
    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):
        json = request.json
    try:
        cursor.execute(
            f"update scripts set active_flag = {json['activeStatus']} where id = {json['scriptId']}")
        cnxn.commit()
        # return jsonify("Success")
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# Route to get all script code


@ app.route('/GetAllScriptCode', methods=["GET"])
@ token_required
def getAllScriptsCode():
    try:
        scriptCodeList = []
        scriptCodes = getAllCodes()
        for script in scriptCodes:
            scriptCodeList.append({"name": script, "code": script})
        return scriptCodeList
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# Route to  get transaction by id


@ app.route('/getTransactionById/<id>', methods=['GET'])
@ token_required
def GetTransactionByScriptId(id):
    try:
        result = []
        columns = ['transactionId', 'scriptName', 'orderDate', 'orderType', 'qtySlab', 'buyTarget', 'sellTarget',
                   'qtyBalance', 'scriptFundBalance', 'profit', 'buyRate', 'buyMargin', 'sellMargin', 'sellId']
        sql = '{CALL GetTransactionByScriptId(?)}'
        values = (id)
        cursor.execute(sql, values)
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# Route to  get Current price by id


@ app.route("/updateScriptsCurrentPrice", methods=["GET"])
@ token_required
def update_script_current_price_by_id():
    try:
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
            time.sleep(0.5)

        return jsonify("Updated")
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# Route to Delete Script By id


@ app.route('/DeleteScriptById', methods=['DELETE'])
@ token_required
def deletescriptbyid():
    try:
        args = request.args
        id = args.to_dict()["id"]

        scriptName = args.to_dict()["scriptName"]
        qty = args.to_dict()["qty"]
        status = int(args.to_dict()["status"])
        print("id:", id, "qty:", qty, "scriptName:",
              scriptName, "status:", status)
        data = {"symbols": f"NSE:{scriptName}-EQ"}
        # print(fyers.quotes(data))
        print(status == -1)
        if (fyers.quotes(data)):
            current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
        if status == -1:
            print("saved")
            sql = '{CALL DeleteScript(?)}'
            values = (id)
            cursor.execute(sql, values)
            cnxn.commit()
        else:
            print("current price", current_price)
            print("last transaction", last_transaction)
            print("qty", qty)
            avg_price = getAvgPriceByScriptId(id)
            insert_transactions(
                id, -1, qty, 0, 0, 0, 0, (float(current_price) - float(avg_price))*float(qty), 0, 0, 0, 0)
            updateScript(id, 0, 0, current_price, 0, 0)
            deleteScriptById(id, scriptName, qty)
            createTransctionLog(
                f"Sold {qty} of {scriptName} (Delete)", scriptName)

        return jsonify("Success")
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# Route for updating the script status by id (live, paused)


@ app.route('/UpdateScriptStatusById', methods=['GET'])
@ token_required
def update_script_status_by_id():
    try:
        args = request.args
        id = args.to_dict()["id"]
        status = args.to_dict()["status"]
        sql = '{CALL updateScriptActiveStatus(?, ?)}'
        values = (id, status)
        cnxn.execute(sql, values)
        cnxn.commit()

        return jsonify("Success")

    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500

# Route to get transaction for current date


@app.route('/getTodaysProfit', methods=['GET'])
@token_required
def getTodaysProfit():
    try:
        sql = '{CALL getTodaysProfit()}'
        cursor.execute(sql)
        return jsonify(cursor.fetchone()[0])
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@app.route('/getScriptProfit', methods=['GET'])
@token_required
def getScriptProfit():
    try:
        sql = '{CALL getTotalProfitByScriptId()}'
        cursor.execute(sql)
        return jsonify(cursor.fetchone()[0])
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@ app.route('/GetTransactionForCurrentDate', methods=['GET'])
@ token_required
def transactionForCurrentDate():
    try:
        result = []
        columns = ['scriptId', 'scriptName', 'orderDate', 'orderType', 'qtySlab', 'buyTarget', 'sellTarget',
                   'qtyBalance', 'scriptFundBalance', 'profit', 'buyRate', 'sm2sell']
        sql = '{CALL getAlltransactions()}'
        cursor.execute(sql)
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
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
    try:
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
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# CODE FOR  GET PROFIT BY SCRIPT ID


@ app.route('/getProfitByScriptId/<id>', methods=['GET'])
@ token_required
def getProfitByScriptId(id):
    try:
        sql = '{CALL getProfitByScriptId(?)}'
        values = (id)
        result = cnxn.execute(sql, values)
        profit = result.fetchone()[0]
        return {"profit": profit}
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# ROUTE FOR LOGIN USER

# ------------------------------Code to test--------------------------------------------------


@ app.route("/authenticate", methods=["POST"])
def authenticate():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        try:
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
                traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# -------------------------------Code to test-----------------------------------------------------

# ROUTE TO GET CURRENT PRICE FOR SELECTED SCRIPT IN ADD SCRIPT FORM


@ app.route("/currentPriceForSelectedScript", methods=["GET"])
@ token_required
def currentPriceForSelectedScript():
    try:
        args = request.args
        data = {"symbols": f"NSE:{args['code']}-EQ"}
        current_price = float(fyers.quotes(data)["d"][0]["v"]["lp"])
        return jsonify({"currentPrice": current_price})
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@ app.route('/addScriptFund', methods=['POST'])
@ token_required
def addScriptFund():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
    print(json)
    try:
        sql = '{CALL addScriptFund(?,?)}'
        values = (json["scriptId"], json["scriptFund"])
        cnxn.execute(sql, values)
        cnxn.commit()
        return jsonify("updated")
    except:
        with open('errorLogs.txt', 'a+') as f:
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


# Route for starting the program


@ app.route('/StartProgram', methods=['GET'])
@ token_required
def start_program():
    # print("Average Price", getAvgPriceByScriptId(id))
    last_traded_value = 0
    transactionList = []
    # get all the active scrupts
    activeScripts = cursor.execute(
        f"select * from scripts where active_flag = 1 and isdeleted = 0").fetchall()
    print(activeScripts)
    # loop through all the active scripts
    if (datetime.now() < datetime.now().replace(hour=15, minute=30, second=0, microsecond=0) and activeScripts != None):
        for rowdata in activeScripts:
            data = {"symbols": f"NSE:{rowdata[1]}-EQ"}
            current_price = float(fyers.quotes(data)["d"][0]["v"]["lp"])
            id = rowdata[0]
            scriptName = rowdata[1]
            investment_balance = float(rowdata[8])
            buy_margin = rowdata[3]
            sell_margin = rowdata[4]
            last_transaction = rowdata[11]
            last_transaction_date = date.today()
            reset_criteria = rowdata[7]
            sm2_flag = rowdata[18]
            print("sm2 flag", sm2_flag)

            deal = rowdata[15]
            average_price = rowdata[13]
            market_rate_stoploss = rowdata[19]
            startFlag = 1
            specific_value = rowdata[16]
            marginal_value = rowdata[17]
            if getLastTransactionByScriptId(id):
                last_traded_value = getLastTransactionByScriptId(rowdata[0])
            # get last transaction for the script if only exists
            print(getLastBuy(id))
            if getLastBuy(id) != None:
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
            # query = cnxn.execute(
            #     f"select active_flag from scripts where id = {id}")
            if investment_balance <= current_price * qty_slab:
                transactionList.append(
                    {"scriptName": scriptName, "message": "Balance is low- Trade can not be placed"})

            if stock_quantity == 0 and last_transaction == 0 and investment_balance >= current_price * qty_slab:
                # code for placing a buy order and store the response in order_status
                order_status = buy_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    print(f"Initial Buy for - {current_price} {qty_slab} qty")
                    message = f"Initial Buy for - {current_price} {qty_slab} qty"
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
                        sell_margin,
                        0
                    )
                    updateScript(script_id, investment_balance,
                                 stock_quantity, current_price, average_price, 1)
                    createTransctionLog(
                        f" Intial Buy {qty_slab} of {scriptName}", scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": message})
                else:
                    createTransctionLog(order_status['message'], scriptName)

            if stock_quantity == 0 and reset_criteria == 0 and last_transaction != 0 and investment_balance >= current_price * qty_slab:
                order_status = buy_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    print(f"spot buy- {current_price} {qty_slab} qty")
                    message = f"spot buy- {current_price} {qty_slab} qty"
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
                        sell_margin,
                        0
                    )
                    updateScript(script_id, investment_balance,
                                 stock_quantity, current_price, average_price, 1)
                    createTransctionLog(
                        f"spot buy- {current_price} {qty_slab} qty", scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": message})
                else:
                    createLog(order_status['message'], scriptName)
            elif stock_quantity == 0 and current_price <= last_traded_value - (marginal_value / 100) * last_traded_value and reset_criteria == 1 and last_traded_value != 0 and investment_balance >= current_price * qty_slab:
                order_status = buy_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    print(f"marginal buy - {current_price} {qty_slab} qty")
                    message = f"marginal buy - {current_price} {qty_slab} qty"
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
                        sell_margin,
                        0
                    )
                    updateScript(script_id, investment_balance,
                                 stock_quantity, current_price, average_price, 1)
                    createTransctionLog(message, scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": message})
                else:
                    createLog(order_status['message'], scriptName)

            elif stock_quantity == 0 and reset_criteria == 2 and current_price <= specific_value and investment_balance >= current_price * qty_slab:
                order_status = buy_order(scriptName, qty_slab)
                if order_status['s'] != 'error':
                    print(f"specific value - {current_price} {qty_slab} qty")
                    message = f"specific value - {current_price} {qty_slab} qty"
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
                        sell_margin,
                        0
                    )
                    updateScript(script_id, investment_balance,
                                 stock_quantity, current_price, average_price, 1)
                    createTransctionLog(message, scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": message})
                else:
                    createLog(order_status['message'], scriptName)
            elif stock_quantity == 0 and reset_criteria == 2 and current_price > specific_value and investment_balance >= current_price * qty_slab:
                createTransctionLog(
                    f"Did not hit specific value because CP({current_price}) > SpecificValue({specific_value})", scriptName)
                transactionList.append(
                    {"scriptName": scriptName, "message": f"Did not hit specific value because CP({current_price}) > SpecificValue({specific_value})"})
            print(
                "============================================================================================")
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
                    lastBuyQtySlab = getLastBuyQtySlab(script_id)
                    order_status = sell_order(scriptName, lastBuyQtySlab)
                    if order_status['s'] != 'error':
                        stock_quantity -= lastBuyQtySlab
# +++++++++++++++++++++++++++++++++Changes for correcting investment balance++++++++++++++++++++++++++++++++
                        investment_balance += lastBuyQtySlab*last_transaction

# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                        last_traded_value = current_price
                        print(
                            f"Sold at - {current_price} {lastBuyQtySlab} qty")
                        print(
                            "============================================================================================")
                        message = f"Sold at - {current_price} {lastBuyQtySlab} qty at sm2 rate"
                        if stock_quantity == 0:
                            average_price = 0
                        else:
                            average_price = (investment_fund -
                                             investment_balance)/stock_quantity
                        insert_transactions(
                            script_id,
                            -1,
                            lastBuyQtySlab,
                            current_price - (buy_margin / 100) * current_price,
                            current_price + (sm2 / 100) * current_price,
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
                        updateLastTransaction(last_sell_id, last_buy_id)
                        createTransctionLog(message, scriptName)
                        transactionList.append(
                            {"scriptName": scriptName, "message": message})
                    else:
                        createLog(order_status['message'], scriptName)

            # condition for selling at sell margin or condition if sm2 is not met on same day then sell at a value greater than sm1 the next day
                elif (stock_quantity > qty_slab and current_price >= last_transaction + (sell_margin / 100) * last_transaction) or (last_transaction_date < date.today() and stock_quantity == qty_slab and current_price >= last_transaction + (sell_margin / 100) * last_transaction):
                    print("In Regular sell condition block")
                    lastBuyQtySlab = getLastBuyQtySlab(script_id)
                    order_status = sell_order(scriptName, lastBuyQtySlab)
                    order_status = sell_order(scriptName, lastBuyQtySlab)
                    if order_status['s'] != 'error':
                        stock_quantity -= lastBuyQtySlab
# +++++++++++++++++++++++++++++++++Changes for correcting investment balance++++++++++++++++++++++++++++++++
                        investment_balance += lastBuyQtySlab*last_transaction
# +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                        last_traded_value = current_price
                        print(
                            f"Sold at - {current_price} {lastBuyQtySlab} qty")
                        print(
                            "============================================================================================")
                        message = f"Sold at - {current_price} {lastBuyQtySlab} qty"
                        if stock_quantity == 0:
                            average_price = 0
                        else:
                            average_price = (investment_fund -
                                             investment_balance)/stock_quantity
                        insert_transactions(
                            script_id,
                            -1,
                            lastBuyQtySlab,
                            current_price - (buy_margin / 100) * current_price,
                            current_price +
                            (sell_margin / 100) * current_price,
                            stock_quantity,
                            investment_balance,
                            (current_price - last_transaction)*lastBuyQtySlab,
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
                        updateLastTransaction(last_sell_id, last_buy_id)
                        createTransctionLog(message, scriptName)
                        transactionList.append(
                            {"scriptName": scriptName, "message": message})
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
                        message = f"Bought for - {current_price} {qty_slab} qty"
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
                    else:
                        createLog(order_status['message'], scriptName)
                elif (current_price <= market_rate_stoploss):
                    print("Market Rate Stop Loss Condition")

                    order_status = sell_order(scriptName, stock_quantity)
                    order_id = order_status['id']
                    if order_status['s'] != 'error':

                        print(
                            f"Sold at - {current_price} {stock_quantity} qty at Stopp Loss Condition")
                        print(
                            "============================================================================================")
                        message = f"Sold at - {current_price} {stock_quantity} qty at Stopp Loss Condition"
                        average_price = investment_fund-investment_balance/stock_quantity
                        insert_transactions(
                            script_id,
                            -1,
                            stock_quantity,
                            current_price - (buy_margin / 100) * current_price,
                            current_price +
                            (sell_margin / 100) * current_price,
                            0,
                            investment_balance,
                            (current_price - last_transaction)*qty_slab,
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
            # query = cnxn.execute(
            #     f"select active_flag from scripts where id = {id}")
            # status = int(query.fetchone()[0])
            time.sleep(1)
        return jsonify(transactionList)
    else:
        print("Market Closed")
        # sql = '{CALL updateScriptActiveStatus(?, ?)}'
        # values = (id, 0)
        cnxn.execute(
            f"update scripts set active_flag = 0 where active_flag = 1 and isdeleted = 0")
        cnxn.commit()
        return jsonify({"message": "Market Closed"})


if __name__ == '__main__':
    # app.debug = True
    # app.run()
    app.run(debug=True, port=8001)
