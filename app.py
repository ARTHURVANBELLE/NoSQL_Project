from flask import Flask, render_template, jsonify, redirect
from flask_restx import Api
import DB_tables  # This will execute the creation of the tables
import dynamoConnect
from flask import redirect, url_for
from flask import Blueprint



# Import the users_namespace from users.py
from users import users_namespace
from items import items_namespace
from clans import clans_namespace
from logs import logs_namespace
from auth import auth

from inventories import inventory_namespace
from monsters import monsters_namespace

app = Flask(__name__)
api = Api(app, version='1.0', title='Game API', description='API for the game management')

# Register the User API namespace
api.add_namespace(users_namespace, path='/users_api')
api.add_namespace(items_namespace, path='/items_api')
api.add_namespace(clans_namespace, path='/clans_api')
api.add_namespace(monsters_namespace, path='/monsters_api')
api.add_namespace(monsters_namespace, path='/monsters_api')
api.add_namespace(inventory_namespace, path='/inventory_api')
api.add_namespace(logs_namespace, path='/logs_api')

app.register_blueprint(auth)

# Route for the home page
@app.route('/home')
def home():
    return render_template('home.html')

# Route for the users page
@app.route('/users')
def users():
    return render_template('user_templates/user_list.html')

# Route for the items page
@app.route('/items')
def items():
    return redirect(url_for('v1/items_item_page'))  

# Route for the monsters page
@app.route('/monsters')
def monsters():
    return render_template('monster_templates/monster_list.html')

# Route for the clans page
@app.route('/clans')
def clans():
    return render_template('clan_templates/clan_list.html')

# Route for the inventories page
@app.route('/inventories')
def inventories():
    return render_template('inventory.html')

# Route for the login page
@app.route('/login')
def login():
    return render_template('login.html')

# Route for the logs page
@app.route('/logs')
def logs():
    return redirect(url_for('v1/logs_item_page'))

# Route for the admin page
@app.route('/admin')
def admin():
    return redirect("http://localhost:8001")

# Route for the api page
@app.route('/api')
def api_redirect():
    return redirect("http://localhost:5000")

# with app.app_context():
#     print("Registered routes:")
#     for rule in app.url_map.iter_rules():
#         print(f"{rule.methods} {rule.rule}") 

if __name__ == '__main__':
    app.run(debug=True)

# # Route for the login page 
# @app.route('/login')
# def home():
#     return render_template('login.html')

# # Route for an user page 
# @app.route('/user/<int:user_id>')
# def user_profile(user_id):
#     from users import get_user_data  # Assuming you have a utility function to get user data
#     user = get_user_data(user_id)
    
#     if user:
#         # Adapt the user data to fit the HTML template structure
#         user_data = {
#             "clan": user.get('clan_id', "Unknown"),
#             "money": user.get('money', 0),
#             "inventory": ["Sword", "Shield", "Potion"],  # You might want to fetch inventory data separately
#             "xp": user.get('xp', 0),
#             "elo": user.get('elo', 0),
#             "classe": user.get('class', "Unknown")
#         }
#         return render_template('user.html', user=user_data)
#     else:
#         return "User not found", 404
# # Route for an clan page 
# @app.route('/clan')
# def clan_overview():
#     clan_members = [
#         {"username": "warrior123", "name": "John Smith", "money": 2000, "level": 35},
#         {"username": "mageQueen", "name": "Emily Stone", "money": 3500, "level": 42}
#     ]
#     return render_template('clan.html', clan_members=clan_members)

# # Route for the create_item page
# @app.route('/create_item')
# def create_item():
#     return render_template('create_item.html')

# # Route for the create_monster page
# @app.route('/create_monster')
# def create_monster():
#     return render_template('create_monster.html')
