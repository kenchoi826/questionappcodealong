from flask import Flask, render_template, g, url_for, request, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db
import sqlite3
import os

app = Flask(__name__)
#create random secret key with os.urandom
app.config['SECRET_KEY'] = os.urandom(24)

#db helper
@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'postgres_db_cur'):
        g.postgres_db_cur.close()
    
    if hasattr(g, 'postgres_db_conn'):
        g.postgres_db_conn.close()


#verify if user session is active
def get_current_user():
    user_result = None

    if 'user' in session:
        user = session['user']
        
        db = get_db()
        db.execute('SELECT id, name, expert, admin FROM users where name = %s',(user,))
        user_result = db.fetchone()
    return user_result

#routing

@app.route('/')
def index():
    user = get_current_user()
    db = get_db()
    db.execute("SELECT questions.id, questions.question_text, askers.name as asked_by, experts.name as answered_by FROM questions\
                JOIN users as askers ON askers.id = questions.asked_by_id JOIN users as experts ON experts.id = questions.expert_id\
                WHERE questions.answer_text is not null ORDER BY experts.name")

    all_answered_results = db.fetchall()

    return render_template('home.html', user=user, all_answered_results=all_answered_results)

@app.route('/answer/<question_id>', methods=['GET','POST'])
def answer(question_id):
    user = get_current_user()
    
    if not user:
        flash("you must login to access that page")
        return redirect(url_for('login'))

    if user['expert'] == 0:
        flash("you don't have right to access this page")
        return redirect(url_for('index'))

    db = get_db()
    db.execute('SELECT id, question_text FROM questions WHERE id = %s',(question_id,))
    question_result = db.fetchone()

    if request.method == "POST":
        answer = request.form['answer']
        db.execute('UPDATE questions SET answer_text = %s WHERE id = %s',(answer, question_id))
        return redirect(url_for('unanswered'))

    return render_template('answer.html', user=user, question_result=question_result)

@app.route('/ask', methods=['GET','POST'])
def ask():
    user = get_current_user()
    
    if not user:
        flash("you must login to access that page")
        return redirect(url_for('login'))

    db = get_db()
    if request.method=='POST':
        question = request.form['question']
        expert_id = request.form['expert']
        user_id = user['id']
        db.execute('INSERT INTO questions (question_text, asked_by_id, expert_id) VALUES (%s,%s,%s)',(question,user_id,expert_id))
        flash("question submitted")
        
    db.execute("SELECT id, name FROM users WHERE expert = '1'")
    expert_results = db.fetchall()

    
    return render_template('ask.html', user=user, expert_results = expert_results)

@app.route('/login', methods=['GET','POST'])
def login():
    user = get_current_user()
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        db.execute('SELECT name, password FROM users WHERE name = %s',(name,))
        user_result = db.fetchone()

        if user_result:

            if check_password_hash(user_result['password'],password):
                session['user'] = user_result['name']
                return redirect(url_for('index'))
            else:
                flash("That's an incorrect password")
                return redirect(url_for('login'))
        else:
            flash("Username doesn't exist")
            return redirect(url_for('login'))
            
    return render_template('login.html', user=user)

@app.route('/question/<question_id>')
def question(question_id):
    user = get_current_user()

    db = get_db()
    db.execute('SELECT questions.question_text, questions.answer_text, askers.name as asked_by, experts.name as answered_by FROM questions\
                        JOIN users as askers ON askers.id = questions.asked_by_id JOIN users as experts ON experts.id = questions.expert_id\
                        WHERE questions.id = %s',(question_id,))
    question_result = db.fetchone()
    return render_template('question.html', user=user, question_result=question_result)

@app.route('/register', methods=['GET','POST'])
def register():
    
    db = get_db()
    if request.method == 'POST':
        name = request.form['name']
        #check existing user
        db.execute("SELECT id FROM users WHERE name = %s",(name,))
        existing_result = db.fetchall()

        if existing_result:
            flash("username existed. Please try again")
            return redirect(url_for('register'))

        password = generate_password_hash(request.form['password'], method='sha256')
        db.execute('INSERT INTO users (name, password, expert, admin) VALUES (%s,%s,%s,%s)',(name,password,'0','0'))
        flash('You have successfully registered.')
        return redirect(url_for('register'))
        
    return render_template('register.html')

@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    
    if not user:
        flash("you must login to access that page")
        return redirect(url_for('login'))

    
    if user['expert'] == 0:
        flash("you don't have right to access this page")
        return redirect(url_for('index'))

    db = get_db()
    expert_id = user['id']
    db.execute("SELECT questions.id, question_text, users.name as name FROM questions JOIN users ON users.id = \
    questions.asked_by_id WHERE answer_text is null AND expert_id = %s",(expert_id,))
    question_results = db.fetchall()
    return render_template('unanswered.html', user=user, question_results=question_results)

@app.route('/users')
def users():
    user = get_current_user()

    if not user:
        flash("you must login to access that page")
        return redirect(url_for('login'))
    
    if user['admin'] == 0:
        flash("you don't have right to access this page")
        return redirect(url_for('index'))

    db = get_db()
    db.execute('SELECT id, name, expert, admin FROM users')
    users_result = db.fetchall()

    return render_template('users.html', user=user, users_result=users_result)

@app.route('/promote/<user_id>')
def promote(user_id):
    db = get_db()
    db.execute('UPDATE users SET expert = True WHERE id = %s',(user_id,))
    return redirect(url_for('users'))

@app.route('/demote/<user_id>')
def demote(user_id):
    db = get_db()
    db.execute('UPDATE users SET expert = False WHERE id = %s',(user_id,))
    return redirect(url_for('users'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

