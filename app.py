import re

from flask import Flask, render_template, request, redirect, session, flash
from flask_bcrypt import Bcrypt

from mysqlconnection import MySQLConnector

app = Flask(__name__)
app.secret_key = "secret_key"

mysql = MySQLConnector(app, "theWall")
bcrypt = Bcrypt(app)

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
	errors = []

	query = "SELECT * FROM users WHERE email=:email;"
	data = {"email": request.form["email"]}

	user = mysql.query_db(query, data)

	if not request.form["email"]:
		errors.append("Please enter an E-mail address")
	elif not EMAIL_REGEX.match(request.form["email"]):
		errors.append("Not a valid E-mail")
	elif user:
		errors.append("E-mail address in use")

	if not request.form["password"]:
		errors.append("Please enter a password")
	elif len(request.form["password"]) < 8:
		errors.append("Password must be 8 characters")
	elif request.form["password"] != request.form["confirm"]:
		errors.append("Password and confirm password must match")

	if errors:
		for error in errors:
			flash(error)
		return redirect("/")
	else:
		query = "INSERT INTO users (first_name, last_name, email, password, created_at, updated_at) VALUES (:first_name, :last_name, :email, :pw_hash, NOW(), NOW());"
		data = {
			"first_name": request.form["first_name"],
			"last_name": request.form["last_name"],
			"email": request.form["email"],
			"pw_hash": bcrypt.generate_password_hash(request.form["password"]),
		}

		session["user_id"] = mysql.query_db(query, data)

		return redirect("/wall")


@app.route("/login", methods=["POST"])
def login():
	query = "SELECT * FROM users WHERE email=:email;"
	data = {"email": request.form["email"]}

	user = mysql.query_db(query, data)

	if not user:
		flash("User name +not valid")
		return redirect("/")

	user = user[0]
	
	if bcrypt.check_password_hash(user["password"], request.form["password"]):
		session["user_id"] = user["id"]
		return redirect("/wall")
	else:
		flash("password not valid")
		return redirect("/")

@app.route("/wall")
def success():
	if "user_id" not in session:
		return redirect("/")

	query = "SELECT * FROM users WHERE id=:id;"
	data = {"id": session["user_id"]}
	user = mysql.query_db(query, data)[0]

	return render_template("wall.html", user=user)

@app.route("/post", methods=["POST"])
def post():
	if "user_id" in session:
		query = "INSERT INTO messages (message, created_at, updated_at, user_id) VALUES (:message, NOW(), NOW(), session['userid']);"
		data = {"message": request.form["message"]}

		session["user_id"] = mysql.query_db(query, data)

		return redirect("/wall")

@app.route("/logoff")
def logoff():
	session.clear()
	return redirect("/")

app.run(debug=True)