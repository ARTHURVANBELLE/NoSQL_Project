from flask import request, render_template, jsonify, make_response
from flask_restx import Api, Resource, fields, Namespace
import boto3
from botocore.exceptions import ClientError

import dynamoConnect

import uuid
from decimal import Decimal

# Initialize the Namespace (not an Api)
users_namespace = Namespace('v1/users', description='User operations')

users_table = dynamoConnect.dynamodb_resource.Table("users")

# Define the user model for the Swagger UI
user_model = users_namespace.model('User', {
    'user_id': fields.String(required=True, description='Unique user identifier'),
    'name': fields.String(required=True, description='User name'),
    'clan_id': fields.Integer(required=True, description='Clan ID'),
    'money': fields.Integer(required=True, description='User money'),
    'inventory_id': fields.Integer(required=True, description='Inventory ID'),
    'xp': fields.Integer(required=True, description='User experience points'),
    'elo': fields.Integer(required=True, description='User ranking/elo'),
    'class': fields.String(required=True, description='User class')
})

def convert_decimals(obj):
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


@users_namespace.route('/users/')
class UserList(Resource):
    @users_namespace.doc('user_list')
    def get(self):
        """Render the user list page."""
        try :
            html_content = render_template('user_templates/user_list.html')
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            return {'message': str(e)}, 500

@users_namespace.route('/')
class UserList(Resource):
    @users_namespace.doc('list_users')
    def get(self):
        """List all users as JSON with pagination."""
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search = request.args.get('search', '', type=str)

        try:
            # Scan all users
            response = users_table.scan()
            users = convert_decimals(response.get('Items', []))

            # Filter users if a search term is provided
            if search:
                users = [user for user in users if search.lower() in user['name'].lower() or search.lower() in user['user_id'].lower()]

            total_users = len(users)
            # Apply pagination
            start = (page - 1) * limit
            end = start + limit
            paginated_users = users[start:end]

            return {
                'users': paginated_users,
                'total_users': total_users
            }, 200

        except ClientError as e:
            return {'message': str(e)}, 500

    @users_namespace.doc('create_user')
    @users_namespace.expect(user_model)
    def post(self):
        """Create a new user"""
        data = request.json
        # Generate a unique user_id
        data['user_id'] = str(uuid.uuid4())
        try:
            # Insert a new user into DynamoDB
            users_table.put_item(Item=data)
            # Return a success message along with the new user's ID
            return {'message': 'User created successfully', 'user_id': data['user_id']}, 201
        except ClientError as e:
            return {'message': str(e)}, 500

@users_namespace.route('/<string:user_id>')
@users_namespace.param('user_id', 'The user identifier')
class User(Resource):
    @users_namespace.doc('get_user')
    def get(self, user_id):
        """Fetch a user by user_id"""
        try:
            response = users_table.get_item(Key={'user_id': user_id})
            user = response.get('Item')
            user_data = {
                "user_id": user_id,
                "name": user.get('name', "Unknown"),
                "clan": user.get('clan_id', "Unknown"),
                "money": user.get('money', 0),
                "inventory_id": user.get('inventory_id', 0),
                "xp": user.get('xp', 0),
                "elo": user.get('elo', 0),
                "class": user.get('class', "Unknown")
            }
            if not user_data:
                return {'message': 'User not found'}, 404
            
            html_content = render_template('user_templates/user.html', user=user_data)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            return {'message': str(e)}, 500

    @users_namespace.doc('delete_user')
    def delete(self, user_id):
        """Delete a user by user_id"""
        try:
            users_table.delete_item(Key={'user_id': user_id})
            return {'message': 'User deleted successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500

    @users_namespace.doc('update_user')
    @users_namespace.expect(user_model)
    def put(self, user_id):
        """Update a user by user_id"""
        data = request.json
        try:
            # Update user information
            users_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression="set #name=:new_name, clan_id=:new_clan_id, money=:new_money, inventory_id=:new_inventory_id, xp=:new_xp, elo=:new_elo, #class=:new_class",
                ExpressionAttributeValues={
                    ':new_name': data['name'],
                    ':new_clan_id': data['clan_id'],
                    ':new_money': data['money'],
                    ':new_inventory_id': data['inventory_id'],
                    ':new_xp': data['xp'],
                    ':new_elo': data['elo'],
                    ':new_class': data['class']
                },
                ExpressionAttributeNames={
                    '#name': 'name',
                    '#class': 'class'
                }
            )
            return {'message': 'User updated successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500

@users_namespace.route('/<string:user_id>/edit')
@users_namespace.param('user_id', 'The user identifier')
class EditUser(Resource):
    @users_namespace.doc('edit_user_page')
    def get(self, user_id):
        """Fetch user data for editing"""
        try:
            response = users_table.get_item(Key={'user_id': user_id})
            user = response.get('Item')
            if not user:
                return {'message': 'User not found'}, 404
            
            user_data = {
                "user_id": user['user_id'],
                "name": user.get('name', "Unknown"),
                "clan_id": user.get('clan_id', 0),
                "money": user.get('money', 0),
                "inventory_id": user.get('inventory_id', 0),
                "xp": user.get('xp', 0),
                "elo": user.get('elo', 0),
                "class": user.get('class', "Unknown")
            }
            html_content = render_template('user_templates/user_edit.html', user=user_data)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            return {'message': str(e)}, 500
