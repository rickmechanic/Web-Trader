import sqlite3
from time import time
from hashlib import sha512

SALT = "!$m33gl3d33g"

def calculate_hash(string):
    hashobject = sha512()
    saltedstring = (string + SALT).encode()
    hashobject.update(saltedstring)
    return hashobject.hexdigest()

conn = sqlite3.connect("ttrader.db")
cur = conn.cursor()

SQL = """INSERT INTO accounts(username, pass_hash, balance, type)
VALUES(?, ?, ?, ?);"""
pw_hash = calculate_hash("password")
cur.execute(SQL, ("carter", pw_hash, 10000.0, 'USER'))

SQL = """INSERT INTO accounts(username, pass_hash, balance, type)
VALUES(?, ?, ?, ?);"""
pw_hash = calculate_hash("password")
cur.execute(SQL, ("rick", pw_hash, 10000.0, 'ADMN'))

SQL = """INSERT INTO trades(account_pk, ticker, volume, price, time) 
VALUES(?, ?, ?, ?, ?);"""
cur.execute(SQL, (1, "AAPL", 10, 100.0, int(time())))

SQL = """INSERT INTO positions(account_pk, ticker, amount) VALUES(?, ?, ?);"""
cur.execute(SQL, (1, "AAPL", 10))

SQL = """INSERT INTO trades(account_pk, ticker, volume, price, time) 
VALUES(?, ?, ?, ?, ?);"""
cur.execute(SQL, (1, "CMG", 40, 300.0, int(time())))

SQL = """INSERT INTO trades(account_pk, ticker, volume, price, time) 
VALUES(?, ?, ?, ?, ?);"""
cur.execute(SQL, (1, "F", 50, 300.0, int(time())))

SQL = """INSERT INTO trades(account_pk, ticker, volume, price, time) 
VALUES(?, ?, ?, ?, ?);"""
cur.execute(SQL, (1, "F", -50, 300.0, int(time())))

conn.commit()
cur.close()
conn.close()
