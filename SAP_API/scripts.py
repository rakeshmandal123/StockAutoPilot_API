# from app import app, cursor, cnxn, token_required, placeorder, fyers
from app import *
import transactions
from flask import request, jsonify, Blueprint
import pandas as pd
import time
from datetime import datetime
import traceback

# function to get symbol list
script = Blueprint('script', __name__)


# def getAllCodes():
#     try:
#         symbolDataLink = "final_Output.csv"
#         symbolData = pd.read_csv(symbolDataLink)
#         scriptCode = []
#         for data in symbolData.iterrows():
#             scriptCode.append(data[1][0])
#         return scriptCode
#     except Exception as e:
#         with open('errorLogs.txt', 'a+') as f:
#             # Added Below line code in every except block to store the time of every error logs
#             ########################################################################
#             f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
#             ########################################################################
#             traceback.print_exc(file=f)
#             return jsonify("Error", e), 500

def getAllCodes():
    try:
        cnxn = pyodbc.connect(cnxn_str)
        cursor = cnxn.cursor()
        scriptCode = cursor.execute(
            f"select script_code from script_codes where isnifty50 = 1").fetchall()
        cnxn.close()
        scriptCode = [x[0] for x in scriptCode]
        # print(scriptCode)
        return scriptCode
    except Exception as e:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify("Error"), 500


def getDealById(id):
    try:
        sql = '{CALL getDealByScriptId(?)}'
        values = (id)
        cursor.execute(sql, values)
        return cursor.fetchone()[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)

# delete script by id


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
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)

# function to get current price script by id


def UpdateSellBuyMargin(id, sellMargin):
    try:
        sql = '{CALL UpdateSellBuyMargin(?,?)}'
        values = (id, sellMargin)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def updateScriptCurrentPriceById(id, current_price, deal):
    try:
        sql = '{CALL updateCurrentPriceByscriptId(?, ?, ?)}'
        values = (id, current_price, deal)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
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
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)

# def getScriptProfit():
#     try:
#         sql = '{CALL getTotalProfitByScriptId()}'
#         cursor.execute(sql)
#         return cursor.fetchone()[0]
#     except:
#         with open('errorLogs.txt', 'a+') as f:
#             f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
#             traceback.print_exc(file=f)


@script.route('/api/getScriptProfit', methods=['GET'])
@token_required
def getScriptProfit():
    try:
        sql = '{CALL getTotalProfitByScriptId()}'
        cursor.execute(sql)
        return jsonify(cursor.fetchone()[0])
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500

# Route for Insert script


@script.route('/api/InsertScript', methods=['POST'])
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
        if result == None or result[12] == 1:
            sql = '{CALL InsertScript(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?, ?)}'
            values = (json['selectedScript']['code'], 0, json['buyMargin'], json['sellMargin'],
                      0, json['resetCriteria'], json['investmentAmount'], json['activeflag'], json['investmentAmount'], 0, json['specificValue'], json['marginalValue'], 0, json['market_rate_stoploss'])
            cnxn.execute(sql, values)
            cnxn.commit()
            return jsonify("Success")
        else:
            return jsonify({"message": f"{json['selectedScript']['code']} is already added!"})
    except Exception as e:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"messge": str(e)})


# Route to Get all Scripts
@script.route('/api/GetAllScripts', methods=['GET'])
@token_required
def getAllScripts():
    try:
        columns = ['id', 'scriptName', 'scriptId', 'buyMargin', 'sellMargin', 'quantityBalance',
                   'startDate', 'resetCriteria',  'investmentBalance', 'activeFlag', 'investmentFund', 'lastTransaction', 'isdeleted', 'avgPrice', 'currentprice', 'deal', 'specificValue', 'marginalValue', 'sm2Flag',  'market_rate_stoploss']
        cnxn3 = pyodbc.connect(cnxn_str)
        cursor3 = cnxn3.cursor()
        cursor3.execute('select * from scripts')
        result = []
        for row in cursor3.fetchall():
            result.append(dict(zip(columns, row)))
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500

# get script by id


@script.route('/api/GetScriptById/<id>', methods=['GET'])
@token_required
def getScriptById(id):
    try:
        columns = ['id', 'scriptName', 'scriptId', 'buyMargin', 'sellMargin', 'quantityBalance',
                   'startDate', 'resetCriteria',  'investmentBalance', 'activeFlag', 'investmentFund', 'lastTransaction', 'isdeleted', 'avgPrice', 'currentprice', 'deal', 'specificValue', 'marginalValue', 'sm2Flag',  'market_rate_stoploss']
        cursor.execute(f"select * from scripts where id = {id}")
        result = cursor.fetchone()
        result[16] = float(result[16])
        result = (dict(zip(columns, result)))
        # print(result)
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


# Route to get update active status
@script.route('/api//UpdateActiveStatus', methods=['POST'])
@token_required
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
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500

# Route to get all script code


@script.route('/api//GetAllScriptCode', methods=["GET"])
@token_required
def getAllScriptsCode():
    try:
        scriptCodeList = []
        scriptCodes = getAllCodes()
        for script in scriptCodes:
            scriptCodeList.append({"name": script, "code": script})
        return scriptCodeList
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


# Route to  get Current price by id
@script.route("/api//updateScriptsCurrentPrice", methods=["GET"])
@token_required
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
            # print(fyers.quotes(data))
            avg_price = float(row["avgPrice"])
            qty = row["quantityBalance"]
            deal = (current_price - avg_price)*qty
            updateScriptCurrentPriceById(row["id"], current_price, deal)
            time.sleep(1)

        return jsonify("Updated")
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500

# Route to Delete Script By id


# Route to Delete Script By id


@script.route('/api//DeleteScriptById', methods=['DELETE'])
@token_required
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
        if (fyers.quotes(data)):
            current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
        if status == -1 or int(qty) == 0:
            print("saved")
            sql = '{CALL DeleteScript(?)}'
            values = (id)
            cursor.execute(sql, values)
            cnxn.commit()
        else:
            print("current price", current_price)
            # print("last transaction", app.last_transaction)
            print("qty", qty)
            avg_price = getAvgPriceByScriptId(id)
            transactions.insert_transactions(
                id, -1, qty, 0, 0, 0, 0, (float(current_price) - float(avg_price))*float(qty), 0, 0, 0, 0, 0)
            updateScript(id, 0, 0, current_price, 0, 0)
            deleteScriptById(id, scriptName, qty)
            createTransctionLog(
                f"Sold {qty} of {scriptName} (Delete)", scriptName)

        return jsonify("Success")
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str(fyers.quotes(data))}), 500


# Route for updating the script status by id (live, paused)
@script.route('/api/UpdateScriptStatusById', methods=['GET'])
@token_required
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
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500

# code for update script details by id


@script.route('/api/UpdateScriptById', methods=['PUT'])
@token_required
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
        UpdateSellBuyMargin(id, sellMargin)
        return jsonify("Success")
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


# CODE FOR  GET PROFIT BY SCRIPT ID
@script.route('/api/getProfitByScriptId/<id>', methods=['GET'])
@token_required
def getProfitByScriptId(id):
    try:
        sql = '{CALL getProfitByScriptId(?)}'
        values = (id)
        result = cnxn.execute(sql, values)
        profit = result.fetchone()[0]
        return {"profit": profit}
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@script.route('/api/getInvestedValueByScriptId/<id>', methods=['GET'])
@token_required
def getInvestedValueByScriptId(id):
    try:
        sql = '{CALL getInvestedValueByScriptId(?)}'
        values = (id)
        result = cnxn.execute(sql, values)
        InvestedValue = result.fetchone()[0]
        return {"InvestedValue": InvestedValue}
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
# ROUTE TO GET CURRENT PRICE FOR SELECTED SCRIPT IN ADD SCRIPT FORM


@script.route("/api/currentPriceForSelectedScript", methods=["GET"])
@token_required
def currentPriceForSelectedScript():
    try:
        args = request.args
        data = {"symbols": f"NSE:{args['code']}-EQ"}
        current_price = float(fyers.quotes(data)["d"][0]["v"]["lp"])
        return jsonify({"currentPrice": current_price})
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@script.route('/api/addScriptFund', methods=['POST'])
@token_required
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
        # to get the updated fund balance from scripts table so that we can insert it into transactions
        fundBalance = float(cnxn.execute(
            f"select investment_balance from scripts where id = {json['scriptId']}").fetchone()[0])
        print(fundBalance)
        transactions.insert_transactions(
            json["scriptId"], 2, 0, 0, 0, 0, fundBalance, 0, json["scriptFund"], 0, 0, 0, 0)
        return jsonify("updated")
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@script.route('/api/getFundHistoryById/<id>', methods=['GET'])
@token_required
def getFundHistoryById(id):
    # content_type = request.headers.get('Content-Type')
    # if (content_type == 'application/json'):
    #     json = request.json
    try:
        result = []
        columns = ['order_date', 'script_fund_balance', 'qty_slab',
                   'order_type', 'buy_rate', ]
        sql = '{CALL FundHistoryByScriptId(?)}'
        values = (id)
        cursor.execute(sql, values)
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
