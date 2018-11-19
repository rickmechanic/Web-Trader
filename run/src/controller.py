#!/usr/bin/env python3

from flask import Flask, session, url_for, render_template, request, redirect
import model
import locale
from datetime import datetime
import tzlocal

local_timezone = tzlocal.get_localzone()
locale.setlocale(locale.LC_ALL, 'en_US')

app = Flask(__name__)
app.secret_key = b'thesessionneedsthis'

@app.route('/', methods=["GET"])
def direct_from_initial_get():
    if "Active User" in session:
        return redirect('/dashboard')
    else:
        return redirect('/login')
    
@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template('unauthorized/login.html')
    elif request.method == "POST":
        user = model.Account()
        username = request.form["username"]
        password = model.calculate_hash(request.form["password"])
        if not user.set_from_credentials(username=username, password=password):
            return render_template('unauthorized/login.html', message="Incorrect username or password")
        user.set_from_credentials(username=username, password=password)
        session["Active User"] = user.pk
        return redirect(url_for('show_dashboard'))

@app.route('/createaccount', methods=["GET","POST"])
def createaccount():
    if request.method == "GET":
        return render_template('unauthorized/createaccount.html')
    elif request.method == "POST":
        user = model.Account()
        username = request.form["username"]
        if not user.username_exists_check(username):
            return render_template('unauthorized/createaccount.html', message="Username already exists")
        password = request.form["password"]
        if not model.password_check(password):
            return render_template('unauthorized/createaccount.html', message="Password must be 8 characters long and include 1 number")  
        password2 = request.form["password2"]
        if password2 != password:
            return render_template('/unauthorized/createaccount.html', message="Passwords don't match. Try again")
        user = model.Account(username=username, pass_hash=model.calculate_hash(password))
        user.save()
        return render_template('unauthorized/login.html', success_message="Account created!")

@app.route('/dashboard', methods=["GET"])
def show_dashboard():
    user = model.Account()
    user.set_from_pk(session["Active User"])
    balance = '${:,.2f}'.format(user.balance)
    allpositions = user.getpositions_html()
    positions = {}
    positions["tickers"] = [i.ticker for i in allpositions]
    positions["amounts"] = [i.amount for i in allpositions]
    positions["values"] = ['${:,.2f}'.format(i.amount*model.apiget(i.ticker)) for i in allpositions]
    positions["total value"] = sum([(i.amount*model.apiget(i.ticker)) for i in allpositions])
    total_value = '${:,.2f}'.format(positions["total value"])
    length = range(0,len(positions["tickers"]))

    return render_template('authorized/dashboard.html', balance=balance, length=length, positions=positions, total_value=total_value)

@app.route('/addfunds', methods=["GET","POST"])
def add_funds():
    user = model.Account()
    user.set_from_pk(session["Active User"])
    if request.method == "GET":
        return render_template('authorized/addfunds.html')
    elif request.method == "POST":
        cardnumber = request.form["cardnumber"]
        if not cardnumber.isdigit():
            return render_template('authorized/addfunds.html', message="Invalid credit card")
        if not model.luhn_check(cardnumber):
            return render_template('authorized/addfunds.html', message="Invalid credit card")
        amount = request.form["amount"]
        if amount[0] == "$":
            amount == amount[1:]
        try:
            amount = float(amount)
            if amount < 0.01:
                return render_template('authorized/addfunds.html', message="Invalid input, must be a positive number")
        except ValueError:
            return render_template('authorized/addfunds.html', message="Invalid input, must be a positive number")
        user.increase_balance(amount)
    return redirect(url_for('deposit_success'))

@app.route('/depositsuccess', methods=["GET"])
def deposit_success():
    user=model.Account()
    user.set_from_pk(session["Active User"])
    balance = '${:,.2f}'.format(user.balance)
    return render_template('authorized/depositsuccess.html', balance=balance)

@app.route('/getprice', methods=["GET","POST"])
def get_price():
    if request.method == "GET":
        return render_template('authorized/getprice.html')
    elif request.method == "POST":
        user = session["Active User"]
        ticker = request.form["ticker"]
        price = model.apiget(ticker)
        if not price:
            return render_template('authorized/getprice.html', message="Stock doesn't exist")
        return render_template('authorized/getprice.html', price='${:,.2f}'.format(price), ticker=model.ticker_cap(ticker))

@app.route('/buystock', methods=["GET","POST"])
def buy_stock():
    if request.method == "GET":
        return render_template('authorized/buystock.html')
    elif request.method == "POST":
        user = model.Account()
        user.set_from_pk(session["Active User"])
        ticker = model.ticker_cap(request.form["ticker"])
        price = model.apiget(ticker)
        if not price:
            return render_template('authorized/buystock.html', message="Stock doesn't exist")
        volume = request.form["volume"]
        try:
            volume=int(volume)
            if volume <= 0:
                return render_template('authorized/sellstock.html', message="Invalid input, must be positive integer")
        except ValueError:
            return render_template('authorized/buystock.html', message="Invalid input, must be positive integer")
        if not model.zero_check(volume):
            return render_template('authorized/buystock.html', message="Invalid input, must be positive integer")
        balance_check = user.sufficient_balance_check(float(price)*float(volume))
        if not balance_check:
            return render_template('authorized/buystock.html', message="Insufficient funds")
        user.buy(ticker, volume, price=price)
        return redirect(url_for('trade_success'))      

@app.route('/sellstock', methods=["GET","POST"])
def sell_stock():
    if request.method == "GET":
        return render_template('authorized/sellstock.html')
    elif request.method == "POST":
        user = model.Account()
        user.set_from_pk(session["Active User"])
        ticker = model.ticker_cap(request.form["ticker"])
        price = model.apiget(ticker)
        if not price:
            return render_template('authorized/sellstock.html', message="Stock doesn't exist")
        if not user.stock_ownership_check(ticker):
            return render_template('authorized/sellstock.html', message="Stock not owned")
        volume = request.form["volume"]
        try:
            volume=int(volume)
            if volume <= 0:
                return render_template('authorized/sellstock.html', message="Invalid input, must be positive integer")
        except ValueError:
            return render_template('authorized/sellstock.html', message="Invalid input, must be positive integer")
        if not model.zero_check(volume):
            return render_template('authorized/sellstock.html', message="Invalid input, must be positive integer")
        if not user.sufficient_amount_check(ticker, volume):
            return render_template('authorized/sellstock.html', message="Insufficient amount owned")
        user.sell(ticker, volume, price=price)
        return redirect(url_for('trade_success')) 

@app.route('/tradesuccess', methods=["GET"])
def trade_success():
    user = model.Account()
    user.set_from_pk(session["Active User"])
    trade = user.getlasttrade()
    ticker = trade.ticker
    position = user.getposition(ticker=ticker)
    if not position:
        return render_template('authorized/tradesuccess.html', message="Position closed out")
    return render_template('authorized/tradesuccess.html', ticker=ticker, price='${:,.2f}'.format(abs(trade.price*trade.volume)), amount=position.amount, value='${:,.2f}'.format(trade.price*position.amount), time=str(datetime.fromtimestamp(trade.time, local_timezone))[0:-6])

@app.route('/seetrades', methods=["GET","POST"])
def see_trades():
    user = model.Account()
    user.set_from_pk(session["Active User"])
    alltrades = user.gettrades()
    trades = {}
    trades["tickers"] = [i.ticker for i in alltrades]
    trades["prices"] = ['${:,.2f}'.format(i.price) for i in alltrades]
    trades["volumes"] = [i.volume for i in alltrades]
    trades["values"] = ['${:,.2f}'.format((i.price*i.volume)) for i in alltrades]
    trades["times"] = [str(datetime.fromtimestamp(i.time, local_timezone))[0:-6] for i in alltrades]
    length = range(0,len(trades["tickers"]))
    if request.method == "GET":
        if not alltrades:
            return render_template('authorized/seetrades.html', message="No trade history. Try buying some stock!")
        return render_template('authorized/seetrades.html', trades=trades, length=length)
    if request.method == "POST":
        ticker = request.form["ticker"]
        if not model.apiget(ticker):
            return render_template('authorized/seetrades.html', trades=trades, length=length, message="Stock doesn't exist")
        if not user.gettradesfor(ticker):
            return render_template('authorized/seetrades.html', trades=trades, length=length, message="No trades exist for that stock")
        alltrades = user.gettradesfor_html(ticker)
        trades = {}
        trades["tickers"] = [i.ticker for i in alltrades]
        trades["prices"] = ['${:,.2f}'.format(i.price) for i in alltrades]
        trades["volumes"] = [i.volume for i in alltrades]
        trades["values"] = [ '${:,.2f}'.format((i.price*i.volume)) for i in alltrades]
        trades["times"] = [str(datetime.fromtimestamp(i.time, local_timezone))[0:-6] for i in alltrades]
        length = range(0,len(trades["tickers"]))
        return render_template("authorized/seetrades.html", trades=trades, length=length)

@app.route('/viewportfolio', methods=["GET","POST"])
def view_portfolio():
    user = model.Account()
    user.set_from_pk(session["Active User"])
    allpositions = user.getpositions_html()
    positions = {}
    positions["tickers"] = [i.ticker for i in allpositions]
    positions["amounts"] = [i.amount for i in allpositions]
    positions["values"] = ['${:,.2f}'.format(i.amount*model.apiget(i.ticker)) for i in allpositions]
    positions["total value"] = sum([(i.amount*model.apiget(i.ticker)) for i in allpositions])
    total_value = '${:,.2f}'.format(positions["total value"])
    length = range(0,len(positions["tickers"]))
    return render_template('authorized/viewportfolio.html', positions=positions, length=length, total_value=total_value)

@app.route('/logout', methods=["GET"])
def logout():
    session.pop("Active User")
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("unauthorized/404.html")   



        






if __name__ == "__main__":
    app.run(port=5002, debug=True)