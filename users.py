from flask import request
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


@users_namespace.route('/')
class UserList(Resource):
    @users_namespace.doc('list_users')
    def get(self):
        """List all users"""
        try:
            response = users_table.scan()
            return convert_decimals(response.get('Items', [])), 200
        except ClientError as e:
            return {'message': str(e)}, 500

    @users_namespace.doc('create_user')
    @users_namespace.expect(user_model)
    def post(self):
        """Create a new user"""
        data = request.json
        # Generate a unique user_id
        data['user_id'] = str(uuid.uuid4())  # Change this line to use UUID
        try:
            # Insert a new user into DynamoDB
            users_table.put_item(Item=data)
            return {'message': 'User created successfully'}, 201
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
            if not user:
                return {'message': 'User not found'}, 404
            return convert_decimals(user), 200
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
