import os
import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

@app.route("/test")
def test():
    return "✅ Flask app is running!"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    user_id = session["user_id"]
    # it is a list of dict so [0] for the first one and for the["key"]
    balance = db.execute("SELECT * FROM users WHERE id = ?",user_id)[0]["cash"]
    #right method
    # it is a list of dict --> HTML rows.stock --> key & Value
    rows = db.execute("SELECT stock, nr, cost, date FROM stocks WHERE id = ?", user_id)

    return render_template("index.html", BALANCE=balance, rows=rows)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == "POST":
        if request.form.get("stock"):
            result = lookup(request.form.get("stock"))
            nr = int(request.form.get("nr"))
            if result and nr:
                # add the the data to database change the balance
                # return render_template("quoted.html", name=result["name"], price=result["price"], symbol=result["symbol"])
                cost = int(nr * float(result["price"]))
                user_id = session["user_id"]
                Balance = db.execute("SELECT * FROM users WHERE id = ?",user_id)[0]["cash"]
                datenow = datetime.datetime.now()
                #return db.execute(SELECT * FROM users WHERE id = ?,user_id)[0]["cash"]
                if Balance >= cost:
                    remain = float(Balance) - cost
                    db.execute("INSERT INTO stocks (id,stock,nr,date,cost) VALUES (?,?,?,?,?)", user_id, str(result["symbol"]), nr, datenow,cost)
                    db.execute("UPDATE users SET cash = ? WHERE id = ?", remain, user_id)
                else:
                    return apology("SORRY, NO BALANCE")
            else: return redirect("/buy")

    return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    return apology("TODO")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if request.form.get("symbol"):
            result = lookup(request.form.get("symbol"))
            if result:
                return render_template("quoted.html", name=result["name"], price=result["price"], symbol=result["symbol"])
            else:
                return apology("invalid quote")
    return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        name = request.form.get("username")
        passwordone = request.form.get("password1")
        passwordtwo = request.form.get("password2")
        names = db.execute("SELECT username FROM users")

        if db.execute("SELECT * FROM users WHERE username = ?", name):
            return apology("user name is already excisiting")
        if passwordone == passwordtwo:
            hashpassword = generate_password_hash(passwordone)
            if name and passwordone:
                db.execute("INSERT INTO users (username, hash) VALUES (?,?)", name, hashpassword)
                return "you are registered"
        else:
            return redirect("/register")

    return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    #Get Method
    user_id = session["user_id"]
    stocks = db.execute("SELECT * FROM stocks WHERE id = ? GROUP BY stock",user_id)

    #POST Method
    if request.method == "POST":
        if request.form.get("nr"):
            stock = request.form.get("list")
            #available = db.execute("SELECT SUM(nr) as total FROM stocks WHERE id = ? AND stock = ?", user_id, stock)[0]["total"]
            #available =  db.execute("SELECT COUNT(*) FROM stocks WHERE id = ? AND stock = ?",user_id , stock)[0]["COUNT(*)"]
            available =  db.execute("SELECT SUM(nr) FROM stocks WHERE id = ? AND stock = ?",user_id , stock)[0]["SUM(nr)"]
            nr = int(request.form.get("nr"))
            #return available
            sold = nr * -1
            if nr > available :
                return "error your available stocks are less than what u want to sell"
            else:
                result = lookup(stock)
                db.execute("INSERT INTO stocks (id, stock, nr, date, cost) VALUES (?,?,?,?,?)",user_id , stock, sold, datetime.datetime.now(), int(result["price"]))
                balance = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
                cash = float(balance) + float(result["price"])
                db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, user_id)
                return "sold"


        else: return "error enter a number"

    #GEt Method
    return render_template("sell.html", stocks=stocks)
