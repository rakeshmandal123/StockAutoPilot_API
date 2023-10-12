from app import *
import transactions
import scripts
from flask import request, jsonify, Blueprint
import pandas as pd
import time
from datetime import datetime, date, timedelta

import traceback

logic2 = Blueprint('logic2', __name__)


# def updateLogic2ScriptForShortList(scriptId, transactionFlag, _52wh, _10wl):
#     try:
#         sql = '{CALL UpdateLogic2Scripts(?, ?, ?, ?)}'
#         values = (scriptId, transactionFlag, _52wh, _10wl)
#         cursor.execute(sql, values)
#     except:
#         with open('errorLogs.txt', 'a+') as f:
#             f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
#             traceback.print_exc(file=f)
def updateLogic2Scripts(scriptId, transactionFlag, _52WH, _10WL, qtyBalance, fundBalance, avgBuyPrice, active_flag):
    try:
        ################################################################################
        sql = '{CALL UpdateLogic2Scripts(?, ?, ?, ?,?,?,?,?)}'
################################################################################
        values = (scriptId, transactionFlag, _52WH, _10WL,
                  qtyBalance, fundBalance, avgBuyPrice, active_flag)
        cursor.execute(sql, values)
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def insertLogic2Transaction(scriptId, orderType, qtySlab, qtyBalance, profit, transactionPrice, scriptFundBalance, buy_target, sell_target, buy_margin, sell_margin):
    try:
        sql = '{CALL insertLogic2Transactions(?,?,?,?,?,?,?,?,?,?,? )}'
        values = (scriptId, orderType, qtySlab,
                  qtyBalance, profit, transactionPrice, scriptFundBalance, buy_target, sell_target, buy_margin, sell_margin)
        cursor.execute(sql, values)
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def get52WHprice(priceList):
    max = 0
    for x in priceList:
        if x[2] >= max:
            max = x[2]
    return max


def get10WLprice(priceList):
    min = 9999999999
    for x in priceList:
        if x[3] <= min:
            min = x[3]
    return min


def deleteLogic2ScriptById(id, scriptName, qty):
    try:
        # order_status = placeorder(scriptName, -1, qty)
        # if order_status['s'] != 'error':
        sql = '{CALL DeleteLogic2Script(?)}'
        values = (id)
        cursor.execute(sql, values)
        cnxn.commit()
        # else:
        #     createLog(order_status['message'], scriptName)

    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def updateLogic2ScriptCurrentPriceById(id, current_price, deal):
    try:
        sql = '{CALL updateCurrentPriceByLogic2ScriptId(?, ?, ?)}'
        values = (id, current_price, deal)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def Update52WHand10WL(id, _52WH, _10WL):
    try:
        sql = '{CALL Update52WHand10WL(?, ?, ?)}'
        values = (id, _52WH, _10WL)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def updateLogic2ScriptCurrentPriceById(id, current_price, deal):
    try:
        sql = '{CALL updateCurrentPriceByLogic2ScriptId(?, ?, ?)}'
        values = (id, current_price, deal)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
# edit logic 2 function


def UpdateLogic2ScriptById(id, buyMargin, sellMargin):
    try:
        sql = '{CALL editLogic2ScriptForm(?, ?, ?)}'
        values = (id, buyMargin,
                  sellMargin)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def getLastTransaction(id):
    try:

        # select top 1 transaction_price from logic2scripts where script_id = @id order by order_date desc
        sql = '{CALL getLastTransaction(?)}'
        values = (id)
        cnxn.execute(sql, values)
        cnxn.commit()
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


@logic2.route('/api/Updatelogic2ScriptById', methods=['PUT'])
@token_required
def Update_Logic2_Script_By_Id():

    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        # print(json)
    else:
        return 'Content-Type not supported!'
    try:
        buyMargin = json["buy_Margin"]
        sellMargin = json["sell_Margin"]
        # investmentAmount = json["investmentAmount"]
        id = json["id"]
        UpdateLogic2ScriptById(id, buyMargin, sellMargin)
    #    UpdateSellBuyMargin(id, sellMargin)
        return jsonify("Success")
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@logic2.route('/api/InsertLogic2Script', methods=['POST'])
@token_required
def insert_scripts():

    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
        # print(json)
    else:
        return 'Content-Type not supported!'
    try:
        cursor.execute(
            f"select *from logic2scripts where script_name = '{json['selectedScript']['code']}'")
        result = cursor.fetchone()
        # print(result)
        if result == None:
            data = {"symbols": f"NSE:{json['selectedScript']['code']}-EQ"}
            current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
            createAPILog("call to add script- current price ")
            eligibility_quantity = int(
                float(json['investmentAmount'])/current_price)
            qty_slab = int(eligibility_quantity/5)
            startDate = date.today() - timedelta(days=365)
            endDate = date.today() - timedelta(days=1)
            dataFor52WH = {
                "symbol": f"NSE:{json['selectedScript']['code']}-EQ",
                "resolution": "D",
                "date_format": "1",
                "range_from": startDate,
                "range_to": endDate,
                "cont_flag": "1"
            }
            _52wh = get52WHprice(fyers.history(data=dataFor52WH)['candles'])
            createAPILog("call to get 52 WH price")
            startDate = date.today() - timedelta(days=70)
            endDate = date.today() - timedelta(days=1)
            dataFor10WL = {
                "symbol": f"NSE:{json['selectedScript']['code']}-EQ",
                "resolution": "D",
                "date_format": "1",
                "range_from": startDate,
                "range_to": endDate,
                "cont_flag": "1"
            }
            _10wl = get10WLprice(fyers.history(data=dataFor10WL)['candles'])
            createAPILog("call to get 10 WL price")
            sql = '{CALL insertlogic2Scripts(?, ?, ?, ?, ?, ?, ?,?)}'
            values = (json['selectedScript']['code'],
                      json['investmentAmount'], json['buy_margin'],  json['sell_margin'], qty_slab, _52wh, _10wl, current_price)
            cursor.execute(sql, values)
            cursor.commit()

            return jsonify("Success")

        else:
            return jsonify({"message": f"{json['selectedScript']['code']} is already added!"})
    except Exception as e:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"messge": str(e)})


@logic2.route('/api/getAllLogic2Scripts', methods=['GET'])
@token_required
def getallscriptsforlogic2():
    try:
        columns = ['id', 'scriptName', 'transactionFlag', '_52wh', '_10wl',
                   'avgBuyPrice', 'qtyBalance', 'isdeleted', 'investedAmount', 'investmentBalance', 'qtySlab', 'ModifiedDate', 'buyMargin', 'sellMargin', 'currentPrice', 'deal', 'active_flag']
        cursor.execute('select * from logic2scripts')
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
        # print(result)
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@logic2.route('/api/GetLogic2ScriptById/<id>', methods=['GET'])
@token_required
def getLogic2ScriptById(id):
    try:
        columns = ['id', 'scriptName', 'transactionFlag', '_52wh', '_10wl',
                   'avgBuyPrice', 'qtyBalance', 'isdeleted', 'investedAmount', 'investmentBalance',     'qtySlab', 'ModifiedDate', 'buyMargin', 'sellMargin', 'currentPrice', 'deal', 'active_flag']
        cursor.execute(f"select * from logic2scripts where id = {id}")
        result = cursor.fetchone()
        # result[16] = float(result[16])
        result = (dict(zip(columns, result)))
        # print(result)
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@logic2.route('/api/getLogic2TransactionById/<id>', methods=['GET'])
@token_required
def GetLogic2TransactionByScriptId(id):
    try:
        result = []
        columns = ['transactionId', 'scriptName', 'orderDate', 'orderType', 'qtySlab',
                   'qtyBalance', 'scriptFundBalance', 'profit', 'transactionPrice']
        sql = '{CALL getLogic2TransactionsById(?)}'
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


@logic2.route('/api/DeleteLogic2ScriptById', methods=['DELETE'])
@token_required
def deleteLogic2ScriptById():
    try:
        args = request.args
        id = args.to_dict()["id"]
        scriptName = args.to_dict()["scriptName"]
        qty = args.to_dict()["qty"]
        print("id:", id, "qty:", qty, "scriptName:",
              scriptName)
        # data = {"symbols": f"NSE:{scriptName}-EQ"}
        # print(fyers.quotes(data))
        # if (fyers.quotes(data)):
        # current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
        if int(qty) == 0:
            print("Delete")
            sql = '{CALL DeleteLogic2Script(?)}'
            values = (id)
            cursor.execute(sql, values)
            cnxn.commit()
        # else:
        #     print("current price", current_price)
        #     # print("last transaction", app.last_transaction)
        #     print("qty", qty)
        #     avg_price = getAvgPriceByScriptId(id)
        #     transactions.insert_transactions(
        #         id, -1, qty, 0, 0, 0, 0, (float(current_price) - float(avg_price))*float(qty), 0, 0, 0, 0, 0)
        #     updateScript(id, 0, 0, current_price, 0, 0)
        #     deleteLogic2ScriptById(id, scriptName, qty)
        #     createTransctionLog(
        #         f"Sold {qty} of {scriptName} (Delete)", scriptName)

        return jsonify("Success")
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": "Internal Server Error"}), 500
# This route runs at a time interval everyday to check which condition is met (buy, loss sell, profit sell) No transactions are made here


@logic2.route("/api/updateLogic2ScriptsCurrentPrice", methods=["GET"])
@token_required
def update_script_current_price_by_id():
    try:
        columns = ['id', 'quantityBalance', 'avgPrice', 'deal', 'scriptName']
        cursor.execute(
            'select id,avg_price,quantity_balance,deal,script_name from logic2Scripts where isdeleted = 0')
        result = []
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
        for row in result:
            data = {"symbols": f"NSE:{row['scriptName']}-EQ"}
            current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
            createAPILog("call to  update logic 2 scripts current price")
            # print(fyers.quotes(data))
            avg_price = float(row["avgPrice"])
            qty = float(row["quantityBalance"])
            deal = (current_price - avg_price)*qty
            updateLogic2ScriptCurrentPriceById(row["id"], current_price, deal)
            time.sleep(1)

        return jsonify("Updated")
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            # f.writelines(str(fyers.quotes(data)))
            traceback.print_exc(file=f)
            return jsonify({"message": "Internal Server Error"}), 500


@ logic2.route('/api/Logic2Transaction', methods=['GET'])
@ token_required
def start_program():
    transactionList = []
    # get all the active scripts for Logic2
    cnxn2 = pyodbc.connect(cnxn_str)
    cursor2 = cnxn2.cursor()
    activeScripts = cursor2.execute(
        f"select * from logic2Scripts where isdeleted = 0").fetchall()
    if (datetime.now() < datetime.now().replace(hour=15, minute=30, second=0, microsecond=0) and activeScripts != None):
        for rowdata in activeScripts:
            # need to change the index values [] after database is build
            id = rowdata[0]
            scriptName = rowdata[1]
            transactionFlag = rowdata[2]
            # _52wh = rowdata[4]
            # _10wl = rowdata[5]
            avgBuyPrice = float(rowdata[6])
            quantityBalance = rowdata[7]
            fundBalance = float(rowdata[8])
            investmentAmount = rowdata[9]
            qtySlab = rowdata[10]
#########################################################################
            buyMargin = rowdata[12]  # Need to change this as per column in
            # Table also update in sp and route For both Insert and get route
            sellMargin = rowdata[13]
            lastTransaction = getLastTransaction(id)  # -> Get Last Buy Price
            # stopLoss = float(rowdata[13])
            avg_price = float(getlogic2AvgPriceByScriptId(id))
#########################################################################
            isNifty100Data = verifyNiftyNotNull()
            data = {"symbols": f"NSE:{rowdata[1]}-EQ"}
            currentPrice = float(fyers.quotes(data)["d"][0]["v"]["lp"])
            createAPILog("call to get current price in start program")
            startDate = date.today() - timedelta(days=365)
            endDate = date.today() - timedelta(days=1)
            dataFor52WH = {
                "symbol": f"NSE:SBIN-EQ",
                "resolution": "D",
                "date_format": "1",
                "range_from": startDate,
                "range_to": endDate,
                "cont_flag": "1"
            }
            _52wh = get52WHprice(fyers.history(data=dataFor52WH)['candles'])
            createAPILog("call to update 52wh price")
            startDate = date.today() - timedelta(days=70)
            endDate = date.today() - timedelta(days=1)
            dataFor10WL = {
                "symbol": f"NSE:SBIN-EQ",
                "resolution": "D",
                "date_format": "1",
                "range_from": startDate,
                "range_to": endDate,
                "cont_flag": "1"
            }
            _10wl = get10WLprice(fyers.history(data=dataFor10WL)['candles'])
            createAPILog("call to update 10wl price")
            current_day = datetime.now().weekday()
            _300pm = datetime.now().replace(
                hour=15, minute=0, second=0, microsecond=0)
            _315pm = datetime.now().replace(
                hour=15, minute=15, second=0, microsecond=0)
            _320pm = datetime.now().replace(
                hour=15, minute=20, second=0, microsecond=0)
            _330pm = datetime.now().replace(
                hour=15, minute=30, second=0, microsecond=0)
            curent_time = datetime.now().strftime('%H:%M:%S')
            if currentPrice > _52wh and quantityBalance == 0:
                updateLogic2Scripts(id, 1, _52wh, _10wl,
                                    quantityBalance, fundBalance, avgBuyPrice, 0)
            print("isNifty100 data", isNifty100Data)
            if (current_day == 5 and curent_time > _300pm and curent_time < _315pm) or isNifty100Data:
                updateScriptCodes()
            # inital buy stocks on friday between 3:20 and 3:30 pm
            if quantityBalance == 0 and transactionFlag == 1 and current_day == 5 and curent_time > _320pm and curent_time < _330pm:
                order_status = buy_order(scriptName, qtySlab)
                if order_status['s'] != 'error':
                    quantityBalance += qtySlab
                    fundBalance -= currentPrice*qtySlab
                    avgBuyPrice = (investmentAmount -
                                   fundBalance)/quantityBalance
                    print(" Initial Buy")
                    insertLogic2Transaction(
                        id,
                        1,
                        qtySlab,
                        quantityBalance,
                        0,
                        currentPrice,
                        fundBalance,
                        currentPrice - (buyMargin / 100) * currentPrice,
                        currentPrice + (sellMargin / 100) * currentPrice,
                        buyMargin,
                        sellMargin
                    )
                    updateLogic2Scripts(
                        id, 0, _52wh, _10wl, quantityBalance, fundBalance, avgBuyPrice, 1)
                else:
                    createLog(order_status['message'], scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": order_status['message']})
            # buy stocks if cp is buyMargin% down of last transaction
            if quantityBalance > 0 and currentPrice < lastTransaction - (buyMargin/100)*lastTransaction and fundBalance >= qtySlab*currentPrice:
                order_status = buy_order(scriptName, qtySlab)
                if order_status['s'] != 'error':
                    quantityBalance += qtySlab
                    fundBalance -= currentPrice*qtySlab
                    avgBuyPrice = (investmentAmount -
                                   fundBalance)/quantityBalance
                    print("print buy margin")
                    insertLogic2Transaction(
                        id,
                        1,
                        qtySlab,
                        quantityBalance,
                        0,
                        currentPrice,
                        fundBalance,
                        currentPrice - (buyMargin / 100) * currentPrice,
                        currentPrice + (sellMargin / 100) * currentPrice,
                        buyMargin,
                        sellMargin
                    )
                    updateLogic2Scripts(
                        id, 0, _52wh, _10wl, quantityBalance, fundBalance, avgBuyPrice, 1)
                else:
                    createLog(order_status['message'], scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": order_status['message']})
            # sell all stocks at loss
            if currentPrice < _10wl or (currentPrice < avgBuyPrice - 30/100*avgBuyPrice and avgBuyPrice != 0):
                order_status = sell_order(scriptName, quantityBalance)
                if order_status['s'] != 'error':
                    qtySlab = quantityBalance
                    quantityBalance = 0
                    fundBalance += avgBuyPrice*qtySlab
                    print("sell all stocks at loss")

                    insertLogic2Transaction(
                        id,
                        -1,
                        qtySlab,
                        quantityBalance,
                        (currentPrice - avg_price)*quantityBalance,
                        currentPrice,
                        fundBalance,  # script fund balance
                        0,  # buytarget
                        0,  # selltarget
                        0,  # buymargin
                        0  # sell margin
                    )
                    updateLogic2Scripts(id, 0, _52wh, _10wl,
                                        quantityBalance, fundBalance, 0, 4)
                else:
                    createLog(order_status['message'], scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": order_status['message']})
            # sell all stocks at profit
            if currentPrice > avgBuyPrice + sellMargin/100*avgBuyPrice and avgBuyPrice != 0:
                order_status = sell_order(scriptName, qtySlab)
                if order_status['s'] != 'error':
                    qtySlab = quantityBalance
                    quantityBalance = 0
                    fundBalance += avgBuyPrice*qtySlab

                    insertLogic2Transaction(
                        id,  # script id
                        -1,  # order type
                        qtySlab,  # qtyslab
                        quantityBalance,  # qtybalance
                        (currentPrice - avg_price)*quantityBalance,  # profit
                        currentPrice,  # transaction _price
                        fundBalance,  # script fund balance
                        0,  # buytarget
                        0,  # selltarget
                        0,  # buymargin
                        0  # sell margin
                    )
                    updateLogic2Scripts(id, 0, _52wh, _10wl,
                                        quantityBalance, fundBalance, 0, 2)
                else:
                    createLog(order_status['message'], scriptName)
                    transactionList.append(
                        {"scriptName": scriptName, "message": order_status['message']})
    return jsonify("success")


# @ logic2.route('/test52wh', methods=['GET'])
# def test():
#     startDate = datetime.date.today() - datetime.timedelta(days=365)
#     endDate = datetime.date.today() - datetime.timedelta(days=1)
#     dataFor52WH = {
#         "symbol": f"NSE:SBIN-EQ",
#         "resolution": "D",
#         "date_format": "1",
#         "range_from": startDate,
#         "range_to": endDate,
#         "cont_flag": "1"
#     }
#     _52wh = get52WHprice(fyers.history(data=dataFor52WH)['candles'])
#     return jsonify(_52wh)

#
# @ logic2.route('/test10wl', methods=['GET'])
# def test10wl():
#     startDate = datetime.date.today() - datetime.timedelta(days=70)
#     endDate = datetime.date.today() - datetime.timedelta(days=1)
#     dataFor10WL = {
#         "symbol": f"NSE:SBIN-EQ",
#         "resolution": "D",
#         "date_format": "1",
#         "range_from": startDate,
#         "range_to": endDate,
#         "cont_flag": "1"
#     }
#     _10wl = get10WLprice(fyers.history(data=dataFor10WL)['candles'])
#     return jsonify(_10wl)


def getAllCodes():
    try:
        cnxn = pyodbc.connect(cnxn_str)
        cursor = cnxn.cursor()
        scriptCode = cursor.execute(
            f"select script_code from script_codes ").fetchall()
        cnxn.close()
        scriptCode = [x[0] for x in scriptCode]
        return scriptCode
    except Exception as e:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify("Error"), 500


@ logic2.route('/api/GetAllScriptCodeForNifty100', methods=["GET"])
@token_required
def getAllScriptsCode():
    try:
        scriptCodeList = []
        cnxn = pyodbc.connect(cnxn_str)
        cursor = cnxn.cursor()
        scripts = cursor.execute(
            f"select script_code, current_price, _52wh from script_codes").fetchall()
        cnxn.close()
        for script in scripts:
            if script[1] > script[2]:
                scriptCodeList.append({"name": script[0], "code": script[0]})
        return jsonify(scriptCodeList)
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@logic2.route('/api/logic2addScriptFund', methods=['POST'])
@token_required
def logic2addScriptFund():
    content_type = request.headers.get('Content-Type')
    if (content_type == 'application/json'):
        json = request.json
    print(json)
    try:
        sql = '{CALL addfundlogic2scripts(?,?)}'
        values = (json["scriptId"], json["scriptFund"])
        cnxn.execute(sql, values)
        cnxn.commit()
        return jsonify("updated")
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


def getlogic2AvgPriceByScriptId(id):
    try:
        sql = '{CALL getlogic2AvgPriceByScriptId(?)}'
        values = (id)
        cursor.execute(sql, values)
        result = cursor.fetchone()
        return result[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


@logic2.route('/api/Getlogic2TransactionForCurrentDate', methods=['GET'])
@token_required
def transactionForCurrentDate():
    try:
        result = []
        columns = ['scriptId', 'scriptName', 'orderDate', 'orderType', 'qtySlab',  'qtyBalance', 'profit', 'buyRate', 'scriptFundBalance', 'buyTarget',  'sellTarget'
                   ]
        sql = '{CALL getAllLogic2transactions()}'
        cursor.execute(sql)
        for row in cursor.fetchall():
            result.append(dict(zip(columns, row)))
        return jsonify(result)
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


def verifyNiftyNotNull():
    cnxn = pyodbc.connect(cnxn_str)
    cursor = cnxn.cursor()
    isNotNull = cursor.execute(
        f"select top 1 current_price from script_codes").fetchone()
    cnxn.close()
    # print("isNot Null", isNotNull[0] == None)
    if isNotNull[0] == None:
        return True
    else:
        return False


def updateScriptCodes():
    scriptCodes = getAllCodes()
    for script in scriptCodes:
        data = {"symbols": f"NSE:{script}-EQ"}
        current_price = fyers.quotes(data)["d"][0]["v"]["lp"]
        startDate = date.today() - timedelta(days=365)
        endDate = date.today() - timedelta(days=1)
        dataFor52WH = {
            "symbol": f"NSE:{script}-EQ",
            "resolution": "D",
            "date_format": "1",
            "range_from": startDate,
            "range_to": endDate,
            "cont_flag": "1"
        }
        _52wh = get52WHprice(fyers.history(data=dataFor52WH)['candles'])
        cnxn = pyodbc.connect(cnxn_str)
        cursor = cnxn.cursor()
        sql = '{CALL updateScriptCodes(?,?,?)}'
        values = (script, current_price, _52wh)
        cursor.execute(sql, values)
        cursor.commit()
