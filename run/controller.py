#!/usr/bin/env python3

from flask import Flask, session, render_template, request, redirect
import model

app = Flask(__name__)
app.secret_key = 'the session needs this'

@app.route('/', methods=["GET"])
def direct_from_initial_get():
    if user in session:
        return redirect('/dashboard')
    else:
        return redirect('/login')
    
@app.route('/login', methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template('unauthorized/login.html')
    elif request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = model.Account()
        while not user.set_from_credentials(username, password):
            return render_template('unauthorized/login.html', message="Incorrect username or password")
        user = model.Account(username=username, pass_hash=model.calculate_hash(password))
        session["Active User"] = user
        return redirect('/dashboard')

@app.route('/createaccount', methods=["GET","POST"])
def createaccount():
    user = model.Account()
    if request.method == "GET":
        return render_template('unauthorized/createaccount.html')
    elif request.method == "POST":
        username = request.form["username"]
        if not user.username_exists_check(username):
            return render_template('unauthorized/createaccount.html', message="Username already exists")
            
        password = request.form["password"]
        if not model.password_check(password):
            return render_template('unauthorized/createaccount.html', message="Password does not meet criteria")
            
        password2 = request.form["password2"]
        if password2 != password:
            return render_template('/unauthorizde/createaccount.html', message="Passwords don't match")
            
        user = model.Account(username=username, pass_hash=model.calculate_hash(password))
        user.save()
        return redirect('/login')

@app.route('/dashboard', methods=["GET"])
def show_dashboard():
    if not session["Active User"]:
        return redirect('/login')
    return render_template('authorized/dashboard.html')

@app.route('/addfunds', methods=["GET","POST"])
def add_funds():
    user = session["Active User"]
    if request.method == "GET":
        if not session["Active User"]:
            return redirect('/login')
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
            except ValueError:
                return render_template('authorized/addfunds.html', message="Invalid input, must be a positive number")
        user.increase_balance(amount)

@app.route('/getprice', methods=["GET","POST"])
def get_price():
    if request.method == "GET":
        if not session["Active User"]:
            return redirect('/login')
        return render_template('authorized/getprice.html')
    elif request.method == "POST":
        ticker = request.form["ticker"]
        price = model.apiget(ticker)
        if not price:
            return render_template('authorized/getprice.html', message="Stock does not exist")
        return render_template('authorized/getprice.html', price=price)

@app.route('/buystock', methods=["GET","POST"])
def buy_stock():
    user = session["Active User"]
    if request.method == "GET":
        return render_template('authorized/buystock.html')
    elif request.method == "POST":
        ticker = model.ticker_cap(request.form["ticker"])
        price = model.apiget(ticker)
        if not price:
            return render_template('authorized/buystock.html', message="Stock does not exist")
        volume = request.form["volume"]
        try:
            volume=int(volume)
        except ValueError:
            return render_template('authorized/buystock.html', message="Invalid input, must be positive integer")
        if not model.zero_check(volume):
            return render_template('authorized/buystock.html', message="Invalid input, must be positive integer")
        balance_check = user.sufficient_balance_check(float(price)*float(volume))
        if not balance_check:
            return render_template('authorized/buystock.html', message="Insufficient balance")
        user.buy(ticker, volume, price=price)
        return redirect('/tradesuccess')        

@app.route('/sellstock', methods=["GET","POST"])
def sell_stock():
    user = session["Active User"]
    if request.method == "GET":
        return render_template('authorized/sellstock.html')
    elif request.method == "POST":
        ticker = model.ticker_cap(request.form["ticker"])
        price = model.apiget(ticker)
        if not price:
            return render_template('authorized/sellstock.html', message="Stock does not exist")
        if not user.stock_ownership_check(ticker):
            return render_template('authorized/sellstock.html', message="Stock not owned")
        volume = request.form["volume"]
        try:
            volume=int(volume)
        except ValueError:
            return render_template('authorized/sellstock.html', message="Invalid input, must be positive integer")
        if not model.zero_check(volume):
            return render_template('authorized/sellstock.html', message="Invalid input, must be positive integer")
        if not user.sufficient_amount_check(ticker, volume):
            return render_template('authorized/sellstock.html', message="Insufficient amount owned")
        user.sell(ticker, volume, price=price)
        return redirect('/tradesuccess')  

@app.route('/tradesuccess', method=["GET"])
def trade_success():
    user = session["Active User"]
    trade = user.getlasttrade()
    ticker = trade.ticker
    price = trade.price
    volume = trade.volume
    time = trade.time
    position = user.getposition(ticker=ticker)
    amount = position.amount
    return render_template('authorized/tradesuccess.html', ticker=ticker, price=price*volume, amount=amount, value=price*amount, time=time)

@app.route('/seetrades', methods=["GET","POST"])
def see_trades():
    user = session["Active User"]
    alltrades = user.gettrades()
    trades = {}
    trades["tickers"] = [i.ticker for i in alltrades]
    trades["prices"] = [i.price for i in alltrades]
    trades["volumes"] = [i.volume for i in alltrades]
    return render_template('authorized/seetrades.html')


@app.route('/viewportfolio', methods=["GET","POST"])
def view_portfolio():
    if request.method == "GET":
    elif request.method == "POST":
    
@app.route('/logout'. methods=["GET"])
def logout():
    del session[user]
    return redirect('/login')
        



        






if __name__ == "__main__":
    app.run()