from flask import Flask, render_template, jsonify
from flask import Flask
from flask_restx import Api
import DB_tables  # This will execute the creation of the tables
import dynamoConnect

# Import the users_namespace from users.py
from users import users_namespace

from monsters import monsters_namespace

app = Flask(__name__)
api = Api(app, version='1.0', title='Game API', description='API for the game management')

# Register the User API namespace
api.add_namespace(users_namespace, path='/users_api')

users_table = dynamoConnect.dynamodb_resource.Table("users")
response = users_table.scan()
print(response)

with app.app_context():
    print("Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.methods} {rule.rule}")

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
