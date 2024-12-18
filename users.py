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
clans_table = dynamoConnect.dynamodb_resource.Table("clans")
inventory_table = dynamoConnect.dynamodb_resource.Table("inventories")

user_classes = dynamoConnect.dynamodb_resource.Table("user_classes")

# Define the user model for the Swagger UI
user_model = users_namespace.model('User', {
    'user_id': fields.String(required=True, description='Unique user identifier'),
    'name': fields.String(required=True, description='User name'),
    'clan_id': fields.String(required=False, description='Clan ID'),
    'money': fields.Integer(required=True, description='User money'),
    'inventory_id': fields.String(required=True, description='Inventory ID'),
    'xp': fields.Integer(required=True, description='User experience points'),
    'elo': fields.Integer(required=True, description='User ranking/elo'),
    'user_class': fields.String(required=True, description='User class')
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
class Clans(Resource):
    @users_namespace.doc('all_users')
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
        inventory_data = {
            'inventory_id': '',
            'item_id_dict': {}
        }

        try:
            # Check if clan_id is provided and valid
            clan_id = data.get('clan_id')
            if clan_id:
                clan_response = clans_table.get_item(Key={'clan_id': clan_id})
                clan = clan_response.get('Item')
                if not clan:
                    return {'message': 'Clan ID points to a non-existent clan'}, 400
            else:
                clan_id = None  # Explicitly set to None if not provided

            # Generate a unique user_id
            new_user_id = str(uuid.uuid4())
            data['user_id'] = new_user_id
            data['inventory_id'] = new_user_id
            inventory_data['inventory_id'] = new_user_id

            # Update clan's user_id_list if a valid clan_id is provided
            if clan_id:
                user_id_list = clan.get('user_id_list', '')
                new_user_id_list = f"{user_id_list};{new_user_id}" if user_id_list else new_user_id
                clans_table.update_item(
                    Key={'clan_id': clan_id},
                    UpdateExpression="set user_id_list=:new_user_id_list",
                    ExpressionAttributeValues={
                        ':new_user_id_list': new_user_id_list
                    }
                )

            # Verify and insert user into the user_classes table
            user_class_response = user_classes.get_item(Key={'user_class': data['user_class']})
            if not user_class_response.get('Item'):
                return {'message': 'User class does not exist'}, 400

            # Insert the new user into DynamoDB
            users_table.put_item(Item=data)
            inventory_table.put_item(Item=inventory_data)
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
                "user_class": user.get('user_class', "Unknown")
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
            user = users_table.get_item(Key={'user_id': user_id}).get('Item')
            if not user:
                return {'message': 'User not found'}, 404
        
            clan_id = user['clan_id']

            if clan_id:
                response = clans_table.get_item(Key={'clan_id': clan_id})
                clan = response.get('Item')
                if not clan:
                    return {'message': 'Clan not found'}, 404

                # Retrieve and update user_id_list
                user_id_list = clan.get('user_id_list', '').split(';')

                # Filter out the user_id to be removed
                updated_user_id_list = ';'.join(uid for uid in user_id_list if uid and uid != user_id)

                # Update the clan with the modified user_id_list
                clans_table.update_item(
                    Key={'clan_id': clan_id},
                    UpdateExpression='SET user_id_list = :updatedList',
                    ExpressionAttributeValues={':updatedList': updated_user_id_list}
                )

            users_table.delete_item(Key={'user_id': user_id})
            inventory_table.delete_item(Key={'inventory_id': user_id})
            
            return {'message': 'User deleted successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500

    @users_namespace.doc('update_user')
    @users_namespace.expect(user_model)
    def put(self, user_id):
        """Update a user by user_id"""
        data = request.json
        try:
            user = users_table.get_item(Key={'user_id': user_id}).get('Item')

            clan_id = user['clan_id']
            new_clan_id = data['clan_id']

            if clan_id != new_clan_id:
                if clan_id:
                    response = clans_table.get_item(Key={'clan_id': clan_id})
                    clan = response.get('Item')
                    if not clan:
                        return {'message': 'Clan not found'}, 404

                    user_id_list = clan.get('user_id_list', '')

                    # Remove the specified user_id from the list
                    updated_user_id_list = ';'.join(
                        uid for uid in user_id_list.split(';') if uid and uid != user_id
                    )

                    clans_table.update_item(
                        Key={'clan_id': clan_id},
                        UpdateExpression='SET user_id_list = :updatedList',
                        ExpressionAttributeValues={':updatedList': updated_user_id_list}
                    )
                
                if new_clan_id:
                    new_response = clans_table.get_item(Key={'clan_id': new_clan_id})
                    new_clan = new_response.get('Item')
                    if not new_clan:
                        return {'message': 'New Clan not found'}, 404

                    new_user_id_list = new_clan.get('user_id_list', '')

                    # Add the specified user_id in the list
                    new_updated_user_id_list = new_user_id_list+";"+user_id

                    clans_table.update_item(
                        Key={'clan_id': new_clan_id},
                        UpdateExpression='SET user_id_list = :updatedList',
                        ExpressionAttributeValues={':updatedList': new_updated_user_id_list}
                    )

            user_class_response = user_classes.get_item(Key={'user_class': data['user_class']})

            if user_class_response:

                # Update user information
                users_table.update_item(
                    Key={'user_id': user_id},
                    UpdateExpression="set #name=:new_name, clan_id=:new_clan_id, money=:new_money, xp=:new_xp, elo=:new_elo, user_class=:new_user_class",
                    ExpressionAttributeValues={
                        ':new_name': data['name'],
                        ':new_clan_id': data['clan_id'],
                        ':new_money': data['money'],
                        ':new_xp': data['xp'],
                        ':new_elo': data['elo'],
                        ':new_user_class': data['user_class']
                    },
                    ExpressionAttributeNames={
                        '#name': 'name'
                    }
                )
                return {'message': 'User updated successfully'}, 200
            else:
                return {'message': 'New User class does not exist'}, 400
        except ClientError as e:
            return {'message': str(e)}, 500

@users_namespace.route('/<string:user_id>/edit')
@users_namespace.param('user_id', 'The user identifier')
class EditUser(Resource):
    @users_namespace.doc('edit_user_page')
    def get(self, user_id):
        """Fetch user data for editing and user classes for dropdown."""
        try:
            # Retrieve user data
            response = users_table.get_item(Key={'user_id': user_id})
            user = response.get('Item')
            if not user:
                return {'message': 'User not found'}, 404

            # Retrieve available user classes
            user_classes_response = user_classes.scan()
            user_classes_list = user_classes_response.get('Items', [])

            user_data = {
                "user_id": user['user_id'],
                "name": user.get('name', "Unknown"),
                "clan_id": user.get('clan_id', 0),
                "money": user.get('money', 0),
                "inventory_id": user.get('inventory_id', 0),
                "xp": user.get('xp', 0),
                "elo": user.get('elo', 0),
                "user_class": user.get('user_class', "Unknown")
            }
            
            # Pass both user data and user classes to the template
            html_content = render_template('user_templates/user_edit.html', user=user_data, user_classes=user_classes_list)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            return {'message': str(e)}, 500
        
@users_namespace.route('/user_classes')
class UserClasses(Resource):
    def get(self):
        """Fetch and return all available user classes."""
        try:
            # Retrieve user classes from the user_classes table
            response = user_classes.scan()
            user_classes_list = response.get('Items', [])

            return {
                'user_classes': user_classes_list
            }, 200
        except ClientError as e:
            return {'message': str(e)}, 500
