from flask import Flask, render_template, request, redirect, url_for, session, abort, flash
from flask import request
from flask_mysqldb import MySQL
app = Flask(__name__)
print(app.config['TEMPLATES_AUTO_RELOAD'])

app.config['MYSQL_HOST'] = 'sensorsystemdb.mysql.database.azure.com'
app.config['MYSQL_USER'] = 'sensor'
app.config['MYSQL_PASSWORD'] = 'Enesa12345!'
app.config['MYSQL_DB'] = 'sensor_test'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_SSL_CA'] = '.\DigiCertGlobalRootCA.crt.pem'
    # cur = mysql.connection.cursor()
    # cur.execute('''SELECT * FROM sensor''')
    # rv = cur.fetchall()
    # return str(rv)
import mysql.connector as mysql
# MYSQL_USER = 'sensor'  # USER-NAME
# MYSQL_PASS = 'Enesa12345!'  # MYSQL_PASS
# MYSQL_DATABASE = 'sensor_test'  # DATABASE_NAME

# connection = mysql.connect(user=MYSQL_USER,
#                            passwd=MYSQL_PASS,
#                            database=MYSQL_DATABASE,
#                            host='sensorsystemdb.mysql.database.azure.com',

#                            port = 3306)


cnx= mysql.connect(user="sensor", password="Enesa12345!", host="sensorsystemdb.mysql.database.azure.com", port=3306, database="sensor_test")
sql= cnx.cursor(dictionary=True)



mysql = MySQL(app)

@app.route("/")
def hello():
    return render_template('home.html')

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Hämta användardata från formuläret
        username = request.form['username']
        password = request.form['password']

        # Skapa en cursor för att utföra MySQL-frågor


        # Kör en MySQL-fråga för att hämta användardata baserat på användarnamn och lösenord
        sql.execute("SELECT id, name, email, password FROM users WHERE name = %s AND password = %s", (username, password))
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

@app.route('/dashboard')
def dashboard():
    # Kontrollera om användaren är inloggad
    if 'user' not in session:
        return redirect(url_for('login'))

    # Hämta användardata från sessionsvariabeln
    user = session['user']

    # Hämta data från people-tabellen i databasen
    sql.execute("SELECT * FROM people")

    # Skapa en dictionary för att gruppera personer efter hemid
    homes = {}
    for person in sql:
        home = person['home']
        if home not in homes:
            homes[home] = [person]
        else:
            homes[home].append(person)

    # Returnera data till template
    return render_template("dashboard.html", user=user, homes=homes)


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

@app.route('/profile/<name>')
def profile(name):
    cursor = cnx.cursor()
    cursor.execute("SELECT * FROM people WHERE name = %s", (name,))
    result = cursor.fetchall()
    home = ""
    for row in result:
        home = row[7]
    return render_template('profile.html', name=name, home=home)


# Route för att hantera POST-requests från edit-formulären
@app.route('/edit', methods=['POST'])
def edit():
    # Hämta data från edit-formuläret
    id = request.form['id']
    name = request.form['name']
    email = request.form['email']

    # Uppdatera informationen i databasen
    sql.execute("UPDATE people SET name=%s, email=%s WHERE id=%s", (name, email, id))
    cnx.commit()

    # Omdirigera till dashboarden
    return redirect(url_for('dashboard'))

# Dashboardens HTML-kod med edit-knappar


# Sida med edit-formulär
@app.route('/edit/<id>')
def edit_form(id):
    # Hämta informationen från databasen baserat på ID:t
    sql.execute("SELECT * FROM people WHERE id=%s", (id,))
    person = sql.fetchone()

    # Visa formuläret med befintlig information
    return render_template('edit.html', person=person)

# Edit-formuläret



@app.route("/error")
def error():
    abort(500, "oh no some error!")


if __name__ == "__main__":
    app.secret_key = 'your_secret_key'
    app.run(debug=True, port=80, host="0.0.0.0")
