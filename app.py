from flask import Flask, render_template, jsonify
import DB_tables  #this execute the creation of the tables

# If u're looking for the code to create the tables ==> DB_tables.py

#visit these pages http://127.0.0.1:5000/user - http://127.0.0.1:5000/login - http://127.0.0.1:5000/clan - ...

app = Flask(__name__)

# Route for the login page 
@app.route('/login')
def home():
    return render_template('login.html')

# Route for an user page 
@app.route('/user')
def user_profile():
    user = {
        "clan": "Warriors of Light",
        "money": 1500,
        "inventory": ["Sword", "Shield", "Potion"],
        "xp": 2450,
        "elo": 1200,
        "classe": "Warrior"
    }
    return render_template('user.html', user=user)

# Route for an clan page 
@app.route('/clan')
def clan_overview():
    clan_members = [
        {"username": "warrior123", "name": "John Smith", "money": 2000, "level": 35},
        {"username": "mageQueen", "name": "Emily Stone", "money": 3500, "level": 42}
    ]
    return render_template('clan.html', clan_members=clan_members)

# Route for the create_item page
@app.route('/create_item')
def create_item():
    return render_template('create_item.html')

# Route for the create_monster page
@app.route('/create_monster')
def create_monster():
    return render_template('create_monster.html')


if __name__ == '__main__':
    app.run(debug=True)
