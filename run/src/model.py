from time import time
from random import randint
import sqlite3
import requests
from hashlib import sha512
from datetime import datetime
import tzlocal

local_timezone = tzlocal.get_localzone()

SALT = "!$m33gl3d33g"

DBNAME = "ttrader.db"

def apiget(tick, url="https://api.iextrading.com/1.0/stock/{}/quote"):
    URL = url.format(tick)
    try:
        data = requests.get(URL).json()
        price = data.get("latestPrice")
    except:
        price = None
    return price

def ticker_cap(string):
    ticker = []
    for i in string:
        ticker.append(i.capitalize())
    ticker = "".join(ticker)
    return ticker

def zero_check(num):
    number = str(num)
    for i in number:
        if i != "0":
            return True
    return False

def calculate_hash(string):
    hashobject = sha512()
    saltedstring = (string + SALT).encode()
    hashobject.update(saltedstring)
    return hashobject.hexdigest()

def password_check(password):
    if len(password) < 8:
        return False
    for i in password:
        if i.isdigit():
            return True
    return False

def luhn_check(samplenumber):
    cardnumber = []
    for i in samplenumber:
        cardnumber.append(int(i))
    if cardnumber[0] not in [3,4,5,6]:
        return False
    if cardnumber[0] == 3 and len(cardnumber) != 15 and cardnumber[1] not in [4,7]:
        return False
    if cardnumber[0] in [4,5,6] and len(cardnumber) != 16:
        return False
    if cardnumber[0] == 5 and cardnumber[1] not in [1,2,3,4,5]:
        return False
    if cardnumber[0] == 6 and cardnumber[1] != 0 and cardnumber[2] != 1 and cardnumber[3] != 1:
        return False
    if len(cardnumber) == 16:
        for i in range(14,-1,-2):
            cardnumber[i] = cardnumber[i]*2
        for i in range(14,-1,-2):
            if cardnumber[i] > 9:
                cardnumber.append(cardnumber[i] % 10)
                cardnumber[i] = 1
        if sum(cardnumber) % 10 == 0:
            return True
        else:
            return False
    elif len(cardnumber) == 15:
        for i in range(13,-1,-2):
            cardnumber[i] = cardnumber[i]*2
        for i in range(13,-1,-2):
            if cardnumber[i] > 9:
                cardnumber.append(cardnumber[i] % 10)
                cardnumber[i] = 1
        if sum(cardnumber) % 10 == 0:
            return True
        else:
            return False

class OpenCursor:

    def __init__(self, db=DBNAME, *args, **kwargs):
        self.conn = sqlite3.connect(db, *args, **kwargs)
        self.conn.row_factory = sqlite3.Row  # access fetch results by col name
        self.cursor = self.conn.cursor()

    def __enter__(self):
        return self.cursor

    def __exit__(self, extype, exvalue, extraceback):
        if not extype:
            self.conn.commit()
        self.cursor.close()
        self.conn.close()

class Account:

    def __init__(self, username=None, pass_hash=None, balance=None, acct_type=None, pk=None):
        self.pk = pk
        self.username = username
        self.pass_hash = pass_hash
        self.balance = balance
        self.acct_type = acct_type
    
    def __bool__(self):
        return bool(self.pk)
        
    def save(self):
        with OpenCursor() as cur:
            if not self.pk:
                SQL = """
                INSERT INTO accounts(username, pass_hash, balance, type)
                VALUES(?, ?, ?, ?);
                """
                cur.execute(SQL, (self.username, self.pass_hash, self.balance, self.acct_type))
                self.pk = cur.lastrowid

            else:
                SQL = """
                UPDATE accounts SET username=?, pass_hash=?, balance=?, type=? WHERE
                pk=?;
                """
                cur.execute(SQL, (self.username, self.pass_hash, self.balance, self.acct_type,
                                  self.pk))

    def username_exists_check(self, username):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM accounts WHERE username=?;"""
            cur.execute(SQL, (username,))
            row = cur.fetchone()
            if row:
                return False
        return True

    def set_pass_hash(self, password):
        self.pass_hash = calculate_hash(password)
        return self

    def set_from_credentials(self, username, password):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM accounts WHERE username=? AND pass_hash=?"""
            cur.execute(SQL, (username, password))
            row = cur.fetchone()
            if not row:
                return self
            self.set_from_row(row)
            return self

    def set_from_row(self, row):
        self.pk = row["pk"]
        self.username = row["username"]
        self.pass_hash = row["pass_hash"]
        self.balance = row["balance"]
        self.acct_type = row["type"]
        return self

    def set_from_pk(self, pk):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM accounts WHERE accounts.pk=?"""
            cur.execute(SQL, (pk,))
            row = cur.fetchone()
        return self.set_from_row(row)
    
    def getaccounts(self):
        results = []
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM accounts """
            cur.execute(SQL)
            rows = cur.fetchall()
            for row in rows:
                user = Account()
                user.set_from_row(row)
                user_final = "User: {}, Balance: ${}".format(user.username, user.balance)
                results.append(user_final)
                SQL = """ SELECT * FROM positions WHERE account_pk=? """
                cur.execute(SQL, (user.pk,))
                poss = cur.fetchall()
                for pos in poss:
                    position = Position()
                    position.set_from_row(pos)
                    position_final = "    {} - {} shares".format(position.ticker, position.amount)
                    results.append(position_final)
        return results

    def getbalance(self):
        balance = str(round(self.balance,2))
        if balance[-1] == "0":
            balance = balance+"0"
        return balance

    def increase_balance(self, deposit):
        self.balance = self.balance + deposit
        self.save()

    def getpositions_html(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM positions WHERE account_pk=?;"""
            cur.execute(SQL, (self.pk,))
            rows = cur.fetchall()
            results = []
            values = []
            for row in rows:
                if row[2] == 0:
                    SQL = """
                    DELETE FROM positions WHERE account_pk=?;"""
                    cur.execute(SQL, (self.pk,))
                elif row[2] != 0:
                    pos = Position()
                    pos.set_from_row(row)
                    results.append(pos)
                    values.append(pos.amount*(apiget(pos.ticker)))
            value = round(sum(values),2)
        return results

    def getpositions(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM positions WHERE account_pk=?;"""
            cur.execute(SQL, (self.pk,))
            rows = cur.fetchall()
            results = []
            values = []
            for row in rows:
                if row[2] == 0:
                    SQL = """
                    DELETE FROM positions WHERE account_pk=?;"""
                    cur.execute(SQL, (self.pk,))
                elif row[2] != 0:
                    pos = Position()
                    pos.set_from_row(row)
                    pos_final = "Stock: {}, Shares: {}, Position value: ${}".format(pos.ticker, pos.amount, round((pos.amount*apiget(pos.ticker)),2))
                    results.append(pos_final)
                    values.append(pos.amount*(apiget(pos.ticker)))
            results.append("Total Portfolio Value: ${}".format(round(sum(values),2)))
        return results
    
    def getposition(self, ticker):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM positions WHERE account_pk=? AND ticker=?;"""
            cur.execute(SQL, (self.pk,ticker))
            row = cur.fetchone()
            if not row:
                return None
            if row[2] == 0:
                SQL = """
                DELETE FROM positions WHERE account_pk=? AND ticker=?;"""
                cur.execute(SQL, (self.pk,ticker))
                return None
            pos = Position()
        return pos.set_from_row(row)

    def getposition_display(self, row, price):
        if not row:
            return False
        return "Stock: {}, Shares: {}, Position Value: ${}".format(row.ticker, row.amount, round(row.amount*price,2))

    def increase_position(self, ticker, amount):
        pos = self.getposition(ticker)
        if not pos:
            pos = Position(account_pk=self.pk, ticker=ticker, amount=0)
        pos.amount += amount
        pos.save()
    
    def decrease_position(self, ticker, amount):
        pos = self.getposition(ticker)
        if not pos or pos.amount < amount:
            raise ValueError("Position doesn't exist or insufficient amount")
        pos.amount -= amount
        pos.save()
    
    def gettrades(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM trades WHERE account_pk=? ORDER BY time DESC;"""
            cur.execute(SQL, (self.pk,))
            rows = cur.fetchall()
            results = []
            for row in rows:
                trade = Trade()
                trade.set_from_row(row)
                results.append(trade)
        return results
    
    def getlasttrade(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM trades WHERE account_pk=? ORDER BY time DESC;"""
            cur.execute(SQL, (self.pk,))
            row = cur.fetchone()
            trade = Trade()
            trade = trade.set_from_row(row)
        return trade
    
    def gettrades_display(self):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM trades WHERE account_pk=? ORDER BY time DESC;"""
            cur.execute(SQL, (self.pk,))
            rows = cur.fetchall()
            results = []
            for row in rows:
                trade = Trade()
                trade.set_from_row(row)
                if trade.volume < 0:
                    trade_type = "Sale"
                    trade_final = "Type: {}, Time: {}, Stock: {}, Price: ${}, Volume: {}, Total Value: +${}".format(trade_type, str(datetime.fromtimestamp(trade.time, local_timezone))[0:-6], trade.ticker, trade.price, trade.volume, round((abs(trade.volume)*trade.price),2))
                elif trade.volume > 0:
                    trade_type = "Buy"
                    trade_final = "Type: {}, Time: {}, Stock: {}, Price: ${}, Volume: {}, Total Value: -${}".format(trade_type, str(datetime.fromtimestamp(trade.time, local_timezone))[0:-6], trade.ticker, trade.price, trade.volume, round((trade.volume*trade.price),2))
                results.append(trade_final)
        return results
    
    def gettradesfor(self, ticker):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM trades WHERE account_pk=? AND ticker=? ORDER BY time DESC;"""
            cur.execute(SQL, (self.pk, ticker))
            rows = cur.fetchall()
            results = []
            for row in rows:
                trade = Trade()
                trade.set_from_row(row)
                if trade.volume < 0:
                    trade_type = "Sale"
                    trade_final = "Type: {}, Time: {}, Stock: {}, Price: ${}, Volume: {}, Total Value: +${}".format(trade_type, str(datetime.fromtimestamp(trade.time, local_timezone))[0:-6], trade.ticker, trade.price, trade.volume, round((abs(trade.volume)*trade.price),2))
                elif trade.volume > 0:
                    trade_type = "Buy"
                    trade_final = "Type: {}, Time: {}, Stock: {}, Price: ${}, Volume: {}, Total Value: -${}".format(trade_type, str(datetime.fromtimestamp(trade.time, local_timezone))[0:-6], trade.ticker, trade.price, trade.volume, round((trade.volume*trade.price),2))
                results.append(trade_final)
        return results
    
    def gettradesfor_html(self, ticker):
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM trades WHERE account_pk=? AND ticker=? ORDER BY time DESC;"""
            cur.execute(SQL, (self.pk, ticker))
            rows = cur.fetchall()
            results = []
            for row in rows:
                trade = Trade()
                trade.set_from_row(row)
                results.append(trade)
        return results

    def buy(self, ticker, volume, price=None):
        self.increase_position(ticker, amount=volume)
        trade=Trade(account_pk=self.pk, ticker=ticker, volume=volume, price=price)
        self.balance -= volume*price
        trade.save()
        self.save()

    def sell(self, ticker, volume, price=None):
        self.decrease_position(ticker, amount=volume)
        trade=Trade(account_pk=self.pk, ticker=ticker, volume=volume*-1, price=price)
        self.balance += volume*price
        trade.save()
        self.save()
    
    def sufficient_balance_check(self, value):
        if value > self.balance:
            return False
        return True
    
    def stock_ownership_check(self, ticker):
        results = []
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM positions WHERE account_pk=?;"""
            cur.execute(SQL, (self.pk,))
            rows = cur.fetchall()
            for row in rows:
                results.append(row[1])
        if ticker in results:
            return True
        return False
    
    def sufficient_amount_check(self, ticker, volume):
        result = 0
        with OpenCursor() as cur:
            SQL = """
            SELECT * FROM positions WHERE ticker=? AND account_pk=?;"""
            cur.execute(SQL, (ticker, self.pk))
            row = cur.fetchone()
            result += row[2]
        if result < volume:
            return False
        return True

class Trade:

    def __init__(self, pk=None, account_pk=None, ticker=None,
                 volume=None, price=None, time=None):
        self.pk = pk
        self.account_pk = account_pk
        self.ticker = ticker
        self.volume = volume
        self.price = price
        self.time = time

    def save(self):
        if self.time is None:
            self.time = int(time())
        with OpenCursor() as cur:
            if not self.pk:
                SQL = """
                INSERT INTO trades (account_pk, ticker, volume, price, time)
                VALUES(?, ?, ?, ?, ?);
                """
                cur.execute(SQL, (self.account_pk, self.ticker, self.volume, self.price, self.time))
                self.pk = cur.lastrowid

            else:
                SQL = """
                UPDATE trades SET account_pk=?, ticker=?, volume=?, price=?, time=? WHERE
                pk=?;
                """
                cur.execute(SQL, (self.account_pk, self.ticker, self.volume, self.price, self.time,
                                  self.pk))

    def set_from_row(self, row):
        self.pk = row["pk"]
        self.account_pk = row["account_pk"]
        self.ticker = row["ticker"]
        self.volume = row["volume"]
        self.price = row["price"]
        self.time = row["time"]
        return self

    def __repr__(self):
        display = "Trade PK = {}: Time = {}, Stock = {}, Price = {}, Volume = {}, Account PK = {}".format(self.pk, self.time, self.ticker, self.price, self.volume, self.account_pk)
        return display

class Position:

    def __init__(self, account_pk=None, ticker=None, amount=None, pk=None):
        self.account_pk = account_pk
        self.ticker = ticker
        self.amount = amount
        self.pk = pk

    def save(self):
        with OpenCursor() as cur:
            if not self.pk:
                SQL = """
                INSERT INTO positions(account_pk, ticker, amount)
                VALUES(?, ?, ?);
                """
                cur.execute(SQL, (self.account_pk, self.ticker, self.amount))
                self.pk = cur.lastrowid

            else:
                SQL = """
                UPDATE positions SET account_pk=?, ticker=?, amount=? WHERE
                pk=?;
                """
                cur.execute(SQL, (self.account_pk, self.ticker, self.amount,
                                  self.pk))

    def set_from_row(self, row):
        self.pk = row["pk"]
        self.account_pk = row["account_pk"]
        self.ticker = row["ticker"]
        self.amount = row["amount"]
        return self

    def getvalue(self):
        return self.amount * apiget(self.ticker)

    def __repr__(self):
        display = "Position PK = {}: Stock = {}, Amount = {}, Account PK = {}".format(self.pk, self.ticker, self.amount, self.account_pk)
        return display
            


