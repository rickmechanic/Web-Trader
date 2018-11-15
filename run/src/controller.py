#!/usr/bin/env python3

from flask import Flask, session, url_for, render_template, request, redirect
import model

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
        if not user.set_from_credentials(username, password):
            print("account not found")
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
    return render_template('authorized/dashboard.html')

@app.route('/addfunds', methods=["GET","POST"])
def add_funds():
    user = session["Active User"]
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
            except ValueError:
                return render_template('authorized/addfunds.html', message="Invalid input, must be a positive number")
        user.increase_balance(amount)
    return redirect("/dashboard")

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
        return render_template('authorized/getprice.html', price="The current price of {} is $".format(ticker)+str(price))

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
        return redirect('/tradesuccess')        

@app.route('/sellstock', methods=["GET","POST"])
def sell_stock():
    if request.method == "GET":
        return render_template('authorized/sellstock.html')
    elif request.method == "POST":
        user = session["Active User"]
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
        return redirect('/tradesuccess')  

@app.route('/tradesuccess', methods=["GET"])
def trade_success():
    user = model.Account()
    user.set_from_pk(session["Active User"])
    trade = user.getlasttrade()
    ticker = trade.ticker
    position = user.getposition(ticker=ticker)
    return render_template('authorized/tradesuccess.html', ticker=ticker, price=trade.price*trade.volume, amount=position.amount, value=trade.price*position.amount, time=trade.time)

@app.route('/seetrades', methods=["GET","POST"])
def see_trades():
    user = model.Account()
    user.set_from_pk(session["Active User"])
    alltrades = user.gettrades()
    # trades = {}
    # trades["tickers"] = [i.ticker for i in alltrades]
    # trades["prices"] = [i.price for i in alltrades]
    # trades["volumes"] = [i.volume for i in alltrades]
    # trades["times"] = [i.time for i in alltrades]
    if request.method == "GET":
        if not alltrades:
            return render_template('authorized/seetrades.html', message="No trade history. Try buying some stock!")
        return render_template('authorized/seetrades.html', alltrades=alltrades)
    if request.method == "POST":
        ticker = request.form["ticker"]
        if not model.apiget(ticker):
            return render_template('authorized/seetrades.html', message="Stock doesn't exist")
        if not user.gettradesfor(ticker):
            return render_template('authorized/seetrades.html', message="No trades exist for that stock")
        alltrades = user.gettradesfor_html(ticker)
        trades = {}
        trades["tickers"] = [i.ticker for i in alltrades]
        trades["prices"] = [i.price for i in alltrades]
        trades["volumes"] = [i.volume for i in alltrades]
        trades["times"] = [i.time for i in alltrades]
        return render_template("authorized/seetrades.html", alltrades=alltrades)

@app.route('/viewportfolio', methods=["GET","POST"])
def view_portfolio():
    user = model.Account()
    user.set_from_pk(session["Active User"])
    allpositions = user.getpositions_html()
    positions = {}
    positions["tickers"] = [i.ticker for i in allpositions]
    positions["amounts"] = [i.amount for i in allpositions]
    positions["values"] = [round(i.amount*model.apiget(i.ticker),2) for i in allpositions]
    positions["total value"] = int(sum(positions["values"]))
    return render_template('authorized/viewportfolio.html', positions=positions)

    
@app.route('/logout', methods=["GET"])
def logout():
    session.pop("Active User")
    return redirect('/login')
        



        






if __name__ == "__main__":
    app.run(port=5002, debug=True)