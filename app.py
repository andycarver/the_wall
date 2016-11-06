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
def wall():
	if "user_id" not in session:
		return redirect("/")

	query = "SELECT * FROM users WHERE id=:id;"
	data = {"id": session["user_id"]}
	user = mysql.query_db(query, data)[0]

	messagequery = "SELECT messages.id, messages.user_id, messages.message, messages.created_at, users.first_name, users.last_name FROM messages LEFT JOIN users ON users.id = messages.user_id ORDER BY messages.created_at DESC"
	messagedata = mysql.query_db(messagequery)

	commentquery = "SELECT comments.message_id, comments.comment, comments.created_at, users.first_name, users.last_name FROM comments LEFT JOIN messages ON comments.message_id = messages.id LEFT JOIN users ON comments.user_id = users.id ORDER BY comments.created_at DESC"
	commentdata = mysql.query_db(commentquery)

	return render_template("wall.html", messagedata=messagedata, commentdata=commentdata, user=user)

@app.route("/post", methods=["POST"])
def post():
	query = "INSERT INTO messages(user_id, created_at, message)VALUES(:user_id, NOW(), :message)"
    
	data = {
        "user_id" : session['user_id'],
        'message' : request.form['new_message']
    }
	mysql.query_db(query,data)

	return redirect('/wall')

@app.route('/comment/<message_id>',methods=["POST"])
def comment(message_id):
    query = 'INSERT INTO comments (comment, message_id, user_id) VALUES (:comment, :message_id, :user_id);'
    data = {
            'comment': request.form['new_comment'],
            'message_id': message_id,
            'user_id': session['user_id']
    }
    mysql.query_db(query,data)
    return redirect('/wall')

@app.route("/logoff")
def logoff():
	session.clear()
	return redirect("/")

app.run(debug=True)