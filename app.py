from flask import Flask, render_template, jsonify
import DB_tables  #this execute the creation of the tables

# If u're looking for the code to create the tables ==> DB_tables.py

#visit these pages http://127.0.0.1:5000/user - http://127.0.0.1:5000/login - http://127.0.0.1:5000/clan

app = Flask(__name__)

# Route for the login page 
@app.route('/login')
def home():
    return render_template('login.html')

# Route for an user page 
@app.route('/user')
def about():
    return render_template('user.html')

# Route for an clan page 
@app.route('/clan')
def clan():
    return render_template('clan.html')


if __name__ == '__main__':
    app.run(debug=True)
