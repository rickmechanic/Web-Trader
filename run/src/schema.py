import sqlite3

conn = sqlite3.connect('ttrader.db')
cur = conn.cursor()

SQL = "DROP TABLE IF EXISTS accounts;"
cur.execute(SQL)
SQL = "DROP TABLE IF EXISTS trades;"
cur.execute(SQL)
SQL = "DROP TABLE IF EXISTS positions;"
cur.execute(SQL)

SQL = """ 
CREATE TABLE accounts(
    pk INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR,
    pass_hash VARCHAR(128),
    balance FLOAT,
    type VARCHAR(4)
); """
cur.execute(SQL)

SQL = """
CREATE TABLE trades(
    pk INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker VARCHAR,
    volume INTEGER,
    price FLOAT,
    time INTEGER,
    account_pk INTEGER,
    FOREIGN KEY(account_pk) REFERENCES accounts(pk)
); """
cur.execute(SQL)

SQL = """
CREATE TABLE positions(
    pk INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker VARCHAR,
    amount INTEGER,
    account_pk INTEGER,
    FOREIGN KEY(account_pk) REFERENCES accounts(pk)
); """
cur.execute(SQL)

# use joins and views at the end of exercise 2
