from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'martdevelopers_ContactTracingApp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)



# Index
@app.route('/')
def index():
    return render_template('home.html')

 
# About
@app.route('/about')
def about():
    return render_template('about.html')


# Questions
@app.route('/questions')
def questions():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get Questions
    result = cur.execute("SELECT * FROM questions")

    questions = cur.fetchall()

    if result > 0:
        return render_template('questions.html', questions=questions)
    else:
        msg = 'No Asked Questions Found'
        return render_template('questions.html', msg=msg)
    # Close connection
    cur.close()

#Answers
@app.route('/answers')
def answers():
    #Create Cursor
    cur = mysql.connection.cursor()
    #Get answers
    result = cur.execute("SELECT * FROM answers")
    answers = cur.fetchall()
    #condition if ya gat no answers to the questions.

    if result>0:
       return render_template('answers.html', answers=answers)
    else:
        msg='No Answered Questions Found'
        return render_template('answers.html',msg=msg)

#KILL Conncetion
    cur.close()


#Single Question
@app.route('/question/<string:id>/')
def question(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get Question
    result = cur.execute("SELECT * FROM questions WHERE id = %s", [id])

    question = cur.fetchone()

    return render_template('question.html', question=question)

#single answer
@app.route('/answer/<string:id>/')
def answer(id):
    #Create Cursor
    cur = mysql.connection.cursor()
    #Get Answer
    result = cur.execute("SELECT * FROM answers WHERE id = %s", [id])
    answer = cur.fetchone()
    return render_template('answer.html', answer=answer)


# Register Form Class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


# User Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        username = request.form['username']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password']

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # Passed
                session['logged_in'] = True
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid login'
                return render_template('login.html', error=error)
            # Close connection
            cur.close()
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get questions
    #result = cur.execute("SELECT * FROM articles")
    # Show questions only from the user logged in 
    result = cur.execute("SELECT * FROM questions WHERE author = %s", [session['username']])

    questions = cur.fetchall()

    result = cur.execute("SELECT * FROM answers WHERE author = %s", [session['username']])

    answers = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', questions=questions)      
        return render_template('dashboard.html',  answers=answers)
    else:
        msg = 'No Contact Tracing Responses Found'
        return render_template('dashboard.html', msg=msg)
    # Close connection
    cur.close()

# Questionaire form
class ArticleForm(Form):
    name= StringField('Full Name', [validators.Length(min=1, max=200)])
    age = StringField('Age', [validators.length(min=1, max=200)])
    phone = StringField('Phone Number',[validators.length(min=1,max=15)])
    symptoms=TextAreaField('Symptoms',[validators.length(min=30)])
    symptops_started = TextAreaField('When Did You Start Having These Symptoms', [validators.Length(min=20, max=200)])
    closeness = StringField('Have You Been Close To Someonw With Symptoms',[validators.length(min=20, max=200)])
    other_medical_issues = StringField('Do You Have Any Medical Chronic Medical Condition - Name Them', [validators.length(min=20, max=200)])

# Add question
@app.route('/take_survey', methods=['GET', 'POST'])
@is_logged_in
def add_question():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        age = form.age.data
        phone = form.phone.data
        symptoms = form.symptoms.data
        symptops_started = form.symptops_started.data
        closeness = form.closeness.data
        other_medical_issues = form.other_medical_issues.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO questions(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Question Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('take_survey.html', form=form)


# Add Answer
@app.route('/add_answer', methods=['GET', 'POST'])
@is_logged_in
def add_answer():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO answers(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Answer  Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_answer.html', form=form)


# Edit Article
@app.route('/edit_question/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_question(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM questions WHERE id = %s", [id])

    question = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = question['title']
    form.body.data = question['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE questions SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Question Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_question.html', form=form)

#Edit Answer
@app.route('/edit_answer/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_answer(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Get question by id
    result = cur.execute("SELECT * FROM answers WHERE id = %s", [id])

    question= cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = question['title']
    form.body.data = question['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE answers SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('Answer Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_answer.html', form=form)

# Delete Question
@app.route('/delete_question/<string:id>', methods=['POST'])
@is_logged_in
def delete_question(id):
    # Create cursor
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM questions WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Question Deleted', 'success')

    return redirect(url_for('dashboard'))

  
if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True)
