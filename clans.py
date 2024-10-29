from flask import request, render_template, jsonify, make_response
from flask_restx import Api, Resource, fields, Namespace
import boto3
from botocore.exceptions import ClientError

import dynamoConnect

import uuid
from decimal import Decimal

# Initialize the Namespace (not an Api)
clans_namespace = Namespace('v1/clans', description='Clan operations')

clans_table = dynamoConnect.dynamodb_resource.Table("clans")

# Define the clan model for the Swagger UI
clan_model = clans_namespace.model('Clan', {
    'clan_id': fields.String(required=True, description='Unique clan identifier'),
    'name': fields.String(required=True, description='Clan Name'),
    'user_id_list': fields.String(required=True, description='String representing all the user ids separated by a ;'),
    'money': fields.Integer(required=True, description='Money accumulated by the clan'),
    'level': fields.Integer(required=True, descritpion='Level of the clan')
})

def convert_decimals(obj):
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

@clans_namespace.route('/clans/')
class ClanList(Resource):
    @clans_namespace.doc('clans_list')
    def get(self):
        """Render the clan list page."""
        try :
            html_content = render_template('clan_templates/clan_list.html')
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            return {'message': str(e)}, 500
        
@clans_namespace.route('/')
class Clans(Resource):
    @clans_namespace.doc('all_clans')
    def get(self):
        """List all clans as JSON with pagination."""
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search = request.args.get('search', '', type=str)

        try:
            # Scan all clans
            response = clans_table.scan()
            clans = convert_decimals(response.get('Items', []))

            # Filter clans if a search term is provided
            if search:
                clans = [clan for clan in clans if search.lower() in clan['name'].lower() or search.lower() in clan['clan_id'].lower()]

            total_clans = len(clans)
            # Apply pagination
            start = (page - 1) * limit
            end = start + limit
            paginated_clans = clans[start:end]

            return {
                'clans': paginated_clans,
                'total_clans': total_clans
            }, 200

        except ClientError as e:
            return {'message': str(e)}, 500

    @clans_namespace.doc('create_clan')
    @clans_namespace.expect(clan_model)
    def post(self):
        """Create a new clan"""
        data = request.json
        # Generate a unique clan_id
        data['clan_id'] = str(uuid.uuid4())
        try:
            # Insert a new clan into DynamoDB
            clans_table.put_item(Item=data)
            # Return a success message along with the new clan's ID
            return {'message': 'Clan created successfully', 'clan_id': data['clan_id']}, 201
        except ClientError as e:
            return {'message': str(e)}, 500

@clans_namespace.route('/<string:clan_id>')
@clans_namespace.param('clan_id', 'The clan identifier')
class Clan(Resource):
    @clans_namespace.doc('get_clan')
    def get(self, clan_id):
        """Fetch a clan by clan_id"""
        try:
            response = clans_table.get_item(Key={'clan_id': clan_id})
            clan = response.get('Item')
            clan_data = {
                "clan_id": clan_id,
                "name": clan.get('name', "Unknown"),
                "user_id_list": clan.get('user_id_list', "Unknown"),
                "money": clan.get('money', 0),
                "level": clan.get('level', 0)
            }
            if not clan_data:
                return {'message': 'Clan not found'}, 404
            
            html_content = render_template('clan_templates/clan.html', clan=clan_data)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            return {'message': str(e)}, 500

    @clans_namespace.doc('delete_clan')
    def delete(self, clan_id):
        """Delete a clan by clan_id"""
        try:
            clans_table.delete_item(Key={'clan_id': clan_id})
            return {'message': 'Clan deleted successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500

    @clans_namespace.doc('update_clan')
    @clans_namespace.expect(clan_model)
    def put(self, clan_id):
        """Update a clan by clan_id"""
        data = request.json
        try:
            # Update clan information
            clans_table.update_item(
                Key={'clan_id': clan_id},
                UpdateExpression="set #name=:new_name, user_id_list=:new_user_id_list, money=:new_money, level=:new_level",
                ExpressionAttributeValues={
                    ":new_name": data['name'],
                    ":new_user_id_list": data['user_id_list'],
                    ":new_money": data['money'],
                    ":new_level": data['level']
                },
                ExpressionAttributeNames={
                    '#name': 'name'
                }
            )
            return {'message': 'Clan updated successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500

@clans_namespace.route('/<string:clan_id>/edit')
@clans_namespace.param('clan_id', 'The clan identifier')
class EditUser(Resource):
    @clans_namespace.doc('edit_clan_page')
    def get(self, clan_id):
        """Fetch clan data for editing"""
        try:
            response = clans_table.get_item(Key={'clan_id': clan_id})
            clan = response.get('Item')
            if not clan:
                return {'message': 'Clan not found'}, 404
            
            clan_data = {
                "clan_id": clan['clan_id'],
                "name": clan.get('name', "Unknown"),
                "user_id_list": clan.get('user_id_list', "Unknown"),
                "money": clan.get('money', 0),
                "level": clan.get('level', 0)
            }
            html_content = render_template('clan_templates/clan_edit.html', clan=clan_data)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            return {'message': str(e)}, 500
