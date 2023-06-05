from flask import Flask, render_template, request, redirect, url_for, session, abort, flash, jsonify, render_template_string
from flask import request
from flask_mysqldb import MySQL
from builtins import sorted
import matplotlib.pyplot as plt
import mpld3
import numpy as np
import pandas as pd
import base64
import io
import plotly.express as px
import plotly.graph_objects as go
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


app = Flask(__name__)
app.secret_key = 'axis'
print(app.config['TEMPLATES_AUTO_RELOAD'])

app.config['MYSQL_HOST'] = 'sensorsystemdb.mysql.database.azure.com'
app.config['MYSQL_USER'] = 'sensor'
app.config['MYSQL_PASSWORD'] = 'Enesa12345!'
app.config['MYSQL_DB'] = 'sensor_test'
app.config['MYSQL_PORT'] = 3306
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_SSL_CA'] = '.\DigiCertGlobalRootCA.crt.pem'
app.config['MYSQL_CONNECT_TIMEOUT'] = 600000

import mysql.connector as mysql

cnx= mysql.connect(user="sensor", password="Enesa12345!", host="sensorsystemdb.mysql.database.azure.com", port=3306, database="sensor_test")
sql= cnx.cursor(dictionary=True)

mysql = MySQL(app)
@app.route('/search')
def search():
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

@app.route('/dashboard')
def dashboard():
    query = request.args.get('query', '')
    # Hämta data från databasen
    sql.execute("SELECT pers_nr, hub_id, name, age, email, phone, address, warning FROM senior WHERE name LIKE %s OR address LIKE %s OR pers_nr LIKE %s", ('%'+query+'%', '%'+query+'%', '%'+query+'%'))
    seniorer = sql.fetchall()
    cnx.commit()

    # Gruppera seniorerna efter hub_id och sortera efter hub_id
    seniorer_grouped = {}
    for senior in seniorer:
        hub_id = senior['hub_id']
        if hub_id not in seniorer_grouped:
            seniorer_grouped[hub_id] = []
        seniorer_grouped[hub_id].append(senior)
    seniorer_sorted = sorted(seniorer_grouped.items(), key=lambda x: x[0])

    # Skicka data till mallen
    return render_template('dashboard.html', seniorer_grouped=seniorer_grouped, seniorer_sorted=seniorer_sorted, query=query)

@app.route('/profile/<name>')
def profile(name):
    sql.execute("SELECT * FROM senior WHERE name = %s", (name,))
    result = sql.fetchall()
    cnx.commit()
    home = ""
    for row in result:
        home = row['hub_id']
    plot1 = visualization(home)  # Call visualization function and get plot
    plot2 = visualization2(home)  # Call visualization2 function and get plot2
    return render_template('profile.html', name=name, home=home, plot1=plot1, plot2=plot2)

def visualization(hub_id):
    query = f"""SELECT m.device_id, m.last_active, l.room, s.room_id, m.status
                FROM Motion m
                JOIN location l ON m.device_id = l.device_id
                JOIN station s ON l.room_id = s.room_id
                WHERE m.last_active >= '2023-04-27 00:00:00'
                AND s.station_id = %s;""" % hub_id
    cursor = mysql.connection.cursor()
    cursor.execute(query)

    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['device_id', 'last_active', 'room', 'status'])

    # Data preprocessing
    df['last_active'] = pd.to_datetime(df['last_active'])
    df['room'] = df['room'].str.lower()  # Convert room names to lowercase
    room_order = ['vardagsrum', 'kök', 'badrum']

    df = df[df['status'] == '1'].copy()

    # Create plot
    fig = go.Figure()

    for device_id, device_group in df.groupby('device_id'):
        for room, room_group in device_group.groupby('room'):
            x_values = []
            y_values = []
            for idx, row in room_group.iterrows():
                x_values.extend([row['last_active'], row['last_active'] + pd.Timedelta(minutes=30), None])
                y_values.extend([row['room'], row['room'], None])
            
            fig.add_trace(go.Scatter(x=x_values,
                                     y=y_values,
                                     mode='lines',
                                     name=device_id,
                                     showlegend=True))

    # Customize plot
    earliest_day = df['last_active'].min().floor('D')  # Get the earliest day
    start_time = earliest_day + pd.Timedelta(hours=9)  # Set start time to 09:00 of the earliest day
    fig.update_xaxes(title_text='Time', range=[start_time, df['last_active'].max()])
    fig.update_yaxes(title_text='Room', tickvals=room_order, ticktext=room_order, categoryorder='array', categoryarray=room_order)
    fig.update_layout(title='Motion Data by Room and Time', showlegend=True)

    plot1 = fig.to_html(full_html=False, include_plotlyjs='cdn')

    return plot1  # Return the plot
def visualization2(hub_id):
    # Query to fetch the data
    query = f"""SELECT motion_count
                FROM statistics
                WHERE hub_id = %s;""" % hub_id
    cursor = mysql.connection.cursor()
    cursor.execute(query)

    # Fetching and processing data
    data = cursor.fetchall()
    motion_counts = [row['motion_count'] for row in data]

    # Create histogram
    fig = go.Figure(data=[go.Histogram(x=motion_counts)])

    # Customize plot
    fig.update_layout(
        title='Motion Count Distribution',
        xaxis_title='Motion Count',
        yaxis_title='Frequency'
    )

    # Convert plot to HTML
    plot2 = fig.to_html(full_html=False, include_plotlyjs='cdn')

    return plot2  # Return the ploto

  # Pass plots to the template

    #return render_template_string('<html><body>{{ plot|safe }}</body></html>', plot=plot)

@app.route("/")
def hello():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        # User is already logged in, redirect to dashboard
        return render_template('user_profil.html')

    if request.method == 'POST':
        # Retrieve the user inputs from the form
        email = request.form['email']
        password = request.form['password']

        # Check if the user exists in the database
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT * FROM user WHERE email = %s AND password= %s",(email,password))
            user = cursor.fetchone()
            if not user:
                # User does not exist, display an error message
                error = 'Invalid email or password.'
                return render_template('login.html', error=error)

            # Verify the password
            if password != user['password']:
                # Password is incorrect, display an error message
                error = 'Invalid email or password.'
                return render_template('login.html', error=error)

            # Password is correct, set the session variable and redirect to dashboard
            session['user_id'] = user['user_id']
            session['user_name'] = user['name']
            session['user_email'] = user['email']
            flash('You have logged in')
            return redirect(url_for('dashboard'))

    # Render the login page template
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    # Remove user data from the session
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    # Flash a message to the user
    flash('You have been logged out.')
    # Redirect to the login page
    return redirect(url_for('login'))

@app.route('/about')
def about():
    return render_template('about.html')

# Route för att hantera POST-requests från edit-formulären
@app.route('/edit', methods=['POST'])
def edit():
    # Hämta data från edit-formuläret
    id = request.form['id']
    name = request.form['name']
    email = request.form['email']

    # Uppdatera informationen i databasen
    sql.execute("UPDATE senior SET name=%s, email=%s WHERE id=%s", (name, email, id))
    cnx.commit()

    # Omdirigera till dashboarden
    return redirect(url_for('dashboard'))

# Dashboardens HTML-kod med edit-knappar

# Sida med edit-formulär
@app.route('/edit/<id>')
def edit_form(pers_nr):
    # Hämta informationen från databasen baserat på ID:t
    sql.execute("SELECT * FROM senior WHERE pers_nr=%s", (pers_nr,))
    person = sql.fetchone()

    # Visa formuläret med befintlig information
    return render_template('edit.html', person=person)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # Data validation could go here

        # Check that passwords match
        try:
            with mysql.connection.cursor() as cursor:
                # Check if the email is already in use
                cursor.execute("SELECT * FROM user WHERE email = %s", (email,))
                user = cursor.fetchone()
                if user:
                    flash('Email address already in use. Please use a different email.')
                    return redirect(url_for('signup'))

                # Insert the new user into the database
                insert_query = "INSERT INTO user (name, email, password) VALUES (%s, %s, %s)"
                cursor.execute(insert_query, (name, email, password))
            
            mysql.connection.commit()
        except Exception as e:
            flash('An error occurred while creating your account. Please try again.')
            return redirect(url_for('signup'))

        # Flash a success message
        flash('Sign up successful! You can now login.')
        
        # Redirect to the login page
        return redirect('/login')

    # If the request method is GET, simply render the signup.html template
    return render_template('signup.html')
@app.route('/user_profil')
def user_profil():
    # Render the user profile template with the user's data
    return render_template('user_profil.html')

#@app.route('/visualization')


@app.route("/error")
def error():
    abort(500, "oh no some error!")

if __name__ == "__main__":
    app.secret_key = 'your_secret_key'
    app.run(debug=True, port=8000, host="0.0.0.0")
