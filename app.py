from flask import Flask, render_template, request, redirect, url_for, session, abort, flash, jsonify
from flask import request
from flask_mysqldb import MySQL
from builtins import sorted

app = Flask(__name__)
print(app.config['TEMPLATES_AUTO_RELOAD'])

app.config['MYSQL_HOST'] = 'sensorsystemdb.mysql.database.azure.com'
app.config['MYSQL_USER'] = 'sensor'
app.config['MYSQL_PASSWORD'] = 'Enesa12345!'
app.config['MYSQL_DB'] = 'sensor_test'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_SSL_CA'] = '.\DigiCertGlobalRootCA.crt.pem'

import mysql.connector as mysql


cnx= mysql.connect(user="sensor", password="Enesa12345!", host="sensorsystemdb.mysql.database.azure.com", port=3306, database="sensor_test")
sql= cnx.cursor(dictionary=True)

mysql = MySQL(app)

import mysql.connector


def updt_warning():
    '''Function to update the warning levels of senior citizens based on their motion counts'''
    query = """
        UPDATE senior s
        INNER JOIN (
          SELECT hub_id,
            CASE
              WHEN (room_name = "Kök" AND motion_count BETWEEN 0 AND 5) OR (room_name = "Vardagsrum" AND motion_count BETWEEN 0 AND 5) OR (room_name = "Badrum" AND motion_count BETWEEN 0 AND 5) THEN 1
              WHEN (room_name = "Kök" AND motion_count BETWEEN 5 AND 10) OR (room_name = "Vardagsrum" AND motion_count BETWEEN 5 AND 10) OR (room_name = "Badrum" AND motion_count BETWEEN 5 AND 10) THEN 2
              ELSE 3
            END AS warning
          FROM statistics
          WHERE motion_hour IS NOT NULL
        ) stats ON s.hub_id = stats.hub_id
        SET s.warning = stats.warning;
    """
    sql.execute(query)
    cnx.commit()

@app.route('/search')
def search():
    ''' Enables searching for seniors'''
    query = request.args.get('query', '')
    sql.execute("SELECT name, address, pers_nr FROM senior WHERE name LIKE %s OR address LIKE %s OR pers_nr LIKE %s", ('%'+query+'%', '%'+query+'%', '%'+query+'%'))
    results = sql.fetchall()
    cnx.commit()
    return jsonify(results)

@app.route('/search_results')
def search_results():
    query = request.args.get('query', '')
    sql.execute("SELECT name, address, pers_nr FROM senior WHERE name LIKE %s OR address LIKE %s OR pers_nr LIKE %s", ('%'+query+'%', '%'+query+'%', '%'+query+'%'))
    results = sql.fetchall()
    cnx.commit()
    return render_template('search_results.html', results=results)

@app.route('/search_results_page', methods=['POST'])
def search_results_page():
    query = request.form.get('query')
    if query is None:
        flash('Missing query parameter')
        return redirect(url_for('search_results'))

    # Retrieve data from the database
    sql.execute("SELECT name, address, pers_nr FROM senior WHERE name LIKE %s OR address LIKE %s OR pers_nr LIKE %s", ('%'+query+'%', '%'+query+'%', '%'+query+'%'))
    results = sql.fetchall()
    cnx.commit()

    return render_template('search_results.html', results=results)


@app.route('/dashboard')
def dashboard():
    ''' Overview of all seniors in the database, sorted by alert level and grouped by hub_id'''
    query = request.args.get('query', '')
    # Retrieve data from the databse
    sql.execute("SELECT pers_nr, hub_id, name, age, email, phone, address, warning FROM senior WHERE name LIKE %s OR address LIKE %s OR pers_nr LIKE %s", ('%'+query+'%', '%'+query+'%', '%'+query+'%'))
    seniorer = sql.fetchall()
    cnx.commit()

    # Sort seniors based on warning
    seniorer_sorted = sorted(seniorer, key=lambda x: x['warning'], reverse=True)

    # Group seniors based on hub_id
    seniorer_grouped = {}
    for senior in seniorer_sorted:
        hub_id = senior['hub_id']
        if hub_id not in seniorer_grouped:
            seniorer_grouped[hub_id] = []
        seniorer_grouped[hub_id].append(senior)

    return render_template('dashboard.html', seniorer_grouped=seniorer_grouped, query=query)

@app.route('/profile/<name>')
def profile(name):
    '''Hub id and name of senior are sent to profile.html'''
    sql.execute("SELECT * FROM senior WHERE name = %s", (name,))
    result = sql.fetchall()
    cnx.commit()
    home = ""
    for row in result:
        home = row['hub_id']
    return render_template('profile.html', name=name, home=home)

@app.route("/")
def hello():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Hämta användardata från formuläret
        email = request.form['email']
        password = request.form['password']

        # Skapa en cursor för att utföra MySQL-frågor

        # Kör en MySQL-fråga för att hämta användardata baserat på e-post och lösenord
        sql.execute("SELECT user_id, name, email, password FROM user WHERE email = %s AND password = %s", (email, password))
        user = sql.fetchone()

        if user:
            # Spara användardata i en sessionsvariabel
            session['user'] = user
            return redirect(url_for('dashboard'))
        else:
            # Visa ett felmeddelande om inloggningen misslyckades
            flash('Invalid login credentials')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    # Ta bort användardata från sessionsvariabeln
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/about')
def about():
    return render_template('about.html')


# Edit-formuläret
@app.route('/signup', methods=['POST'])
def signup_post():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm-password']

    # validera användardata och skapa en användare i databasen
    if password == confirm_password:
        # skapa en ny kursor för att köra SQL-satser
        cursor = cnx.cursor()

        # använd SQL-satsen INSERT INTO för att lägga till användaren
        insert_query = "INSERT INTO user (name, email, password) VALUES (%s, %s, %s)"
        cursor.execute(insert_query, (username, email, password))

        # spara ändringar till databasen och stäng anslutningen och kursorer
        cnx.commit()
        cursor.close()
        cnx.close()

        return redirect(url_for('login'))

    # om lösenorden inte matchar, visa en felmeddelande
    flash('Passwords do not match. Please try again.')
    return redirect(url_for('signup'))


@app.route("/error")
def error():
    abort(500, "oh no some error!")

if __name__ == "__main__":
    app.secret_key = 'your_secret_key'
    app.run(debug=True, port=80, host="0.0.0.0")