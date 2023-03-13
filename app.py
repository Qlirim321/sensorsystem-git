from flask import Flask, render_template, request, redirect, url_for, session, abort
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
mysql = MySQL(app)

@app.route("/")
def hello():
    return render_template('home.html')
@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/about')
def about():
    return render_template('about.html')

@app.route("/error")
def error():
    abort(500, "oh no some error!")


if __name__ == "__main__":
    app.run(debug=True, port=80, host="0.0.0.0")
