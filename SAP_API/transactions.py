from app import app, cursor, cnxn, token_required
from flask import request, jsonify, Blueprint
import pandas as pd
import traceback
from datetime import datetime
import signal
import os

# function for insert transaction
transaction = Blueprint('transaction', __name__)


def insert_transactions(scriptId, orderType, qtySlab, buyTarget, sellTarget, qtyBalance, scriptFundBalance, Profit, buyRate, Bings, buyMargin, sellMargin, sm2sell):
    try:
        sql = '{CALL InsertTransaction(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)}'
        values = (scriptId, orderType, qtySlab, buyTarget, sellTarget,
                  qtyBalance, scriptFundBalance, Profit, buyRate, Bings, buyMargin, sellMargin, sm2sell)
        cnxn.execute(sql, values)
        cnxn.commit()

    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
        os.kill(os.getpid(), signal.SIGINT)

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
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


def getTodaysProfit():
    try:
        sql = '{CALL getTodaysProfit()}'
        cursor.execute(sql)
        return cursor.fetchone()[0]
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)

# Route to  get transaction by id


def getTodaysTransaction():
    try:
        result = []
        sql = '{CALL getTodaysTransaction()}'
        cursor.execute(sql)
        columns = ["order_date", "qty_slab", "buy_rate"]
        transactions = cursor.fetchall()
        for transaction in transactions:
            result.append(dict(zip(columns, transaction)))
        return result
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)


@transaction.route('/api/getTransactionById/<id>', methods=['GET'])
@token_required
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
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@transaction.route('/api/getTodaysProfit', methods=['GET'])
@token_required
def getTodaysProfit():
    try:
        sql = '{CALL getTodaysProfit()}'
        cursor.execute(sql)
        return jsonify(cursor.fetchone()[0])
    except:
        with open('errorLogs.txt', 'a+') as f:
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500


@transaction.route('/api/GetTransactionForCurrentDate', methods=['GET'])
@token_required
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
            f.writelines(f"{'='*10}{datetime.now()}{'='*10}")
            traceback.print_exc(file=f)
            return jsonify({"message": str("500: Internal Server Error")}), 500
