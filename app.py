from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = "secret123"

def add_message(user_id, message):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('INSERT INTO messages(user_id, content) VALUES (?,?)', (user_id,message))
    conn.commit()
    conn.close()

def get_messages():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT messages.content,
    messages.created_at,
    users.username
    FROM messages
    JOIN users ON messages.user_id = users.id
    ORDER BY messages.created_at DESC''')
    messages = cursor.fetchall()
    conn.close()

    return messages

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/messages_rules")
def messages_rules():
    return render_template("messages_rules.html")

@app.route("/error")
def error():
    error_message = request.args.get("error")
    return render_template("error_page.html", error=error_message)

@app.route("/main")
def main():
    if 'user' in session:
        username = session['user']
        return render_template("main.html", user=username)
    return render_template("main.html")

@app.route("/logout")
def logout():
    if 'user' not in session:
        return redirect("/main")
    session.clear()
    return redirect("/main")

@app.route("/delete", methods=["GET", "POST"])

def delete():
    if 'user' not in session:
        return redirect("/main")
    try:
        if request.method == "POST":
            password = request.form.get("password")
            password2 = request.form.get("password2")
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (session['user'],))
            user = cursor.fetchone()
            conn.close()
            if password == password2:
                if check_password_hash(user[2], password):
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    cursor.execute('DELETE FROM users WHERE username = ?', (session['user'],))
                    conn.commit()
                    conn.close()
                    session.clear()
                    return redirect("/main")
                else:
                    return redirect(url_for("error", error="wrong password"))
            else:
                return redirect(url_for("error", error="Passwords don't match."))
    except:
        return redirect(url_for("error", error="unable to delete account"))

    return render_template("delete_account.html")

@app.route("/location")
def location():
    return render_template("location.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password2 = request.form['password2']
        if password == password2:
            hashed_password = generate_password_hash(password)

            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            try:
                cursor.execute(
                    "INSERT INTO users (username, password) VALUES (?, ?)",
                    (username, hashed_password)
                )
                conn.commit()
            except:
                return redirect(url_for("error", error="account is already registered"))

            conn.close()
            return redirect("/login")
        else:
            return redirect(url_for("error", error="passwords don't match"))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session['user'] = username
            return redirect("/main")
        else:
            return redirect(url_for("error", error="wrong password or username"))
    return render_template('login.html')

@app.route("/board", methods=['GET', 'POST'])
def board():
    if 'user' not in session:
        return redirect("/main")
    user = session['user']
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ?", (user,))
    user_id = cursor.fetchone()[0]
    if request.method == 'POST':
        content = request.form['content']

        if content.strip():
            add_message(user_id, content)

        return redirect("/board")
    messages = get_messages()
    return render_template('board.html', messages=messages, user=session["user"], content=messages)

@app.route("/edit_profile", methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        return redirect("/main")

    current_user = session['user']
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        if new_password:
            hashed_password = generate_password_hash(new_password)
            cursor.execute(
                "UPDATE users SET username = ?, password = ? WHERE username = ?",
                (new_username, hashed_password, current_user)
            )
        else:
            cursor.execute(
                "UPDATE users SET username = ? WHERE username = ?",
                (new_username, current_user)
            )

        conn.commit()
        conn.close()

        session['user'] = new_username
        return redirect("/main")

    return render_template('edit_profile.html', user=current_user)

port = int(os.environ.get("PORT", 10000))
app.run(host='0.0.0.0', port=port)