from flask import request, render_template, jsonify, make_response
from flask_restx import Api, Resource, fields, Namespace
import boto3
from botocore.exceptions import ClientError

import dynamoConnect

import uuid
from decimal import Decimal

# Initialize the Namespace (not an Api)
monsters_namespace = Namespace('v1/monsters', description='Monster operations')

monsters_table = dynamoConnect.dynamodb_resource.Table("monsters")

# Define the monster model for the Swagger UI
monster_model = monsters_namespace.model('Monster', {
    'monster_id': fields.String(required=True, description='Unique Monster identifier'),
    'name': fields.String(required=True, description='Monster name'),
    'inventory_id': fields.Integer(required=True, description='Inventory ID'),
    'reward_money': fields.Integer(required=True, description='Monster reward money'),
    'reward_xp': fields.Integer(required=True, description='Monster reward experience points'),
    'level': fields.Integer(required=True, description='Monster level'),
})

def convert_decimals(obj):
    if isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj


@monsters_namespace.route('/monsters')
class MonsterList(Resource):
    @monsters_namespace.doc('list_monsters')
    def get(self):
        """List all monsters"""
        #Render the monster_List page
        try:
            html_content = render_template('monster_templates/monster_list.html')
            response = make_response(html_content)
            #response = monsters_table.scan()
            #return convert_decimals(response.get('Items', [])), 200
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            return {'message': str(e)}, 500


        
@monsters_namespace.route('/')
class Monsters(Resource):
    @monsters_namespace.doc('all_monsters')
    def get(self):
        """List all monsters as JSON with pagination"""
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)
        search = request.args.get('search', '', type=str)

        try:

            #Scan all tables
            response = monsters_table.scan()
            monsters = convert_decimals(response.get('Items', []))

            # Filter a monster if a search term is provided
            if search:
                monsters = [monster for monster in monsters if search.lower() in monster['name'].lower() or search.lower() in monster['monster_id'].lower()]
            total_monsters = len(monsters)

            #Apply pagination
            start = (page - 1) * limit
            end = start + limit
            paginated_monsters = monsters[start:end]

            return {
                'monsters' : paginated_monsters,
                'total_monsters' : total_monsters
            }, 200
        except ClientError as e:
            return {'message': str(e)}, 500
        
    @monsters_namespace.doc('create_monster')
    @monsters_namespace.expect(monster_model)
    def post(self):
        """Create a new monster"""
        data = request.json
        # Generate a unique monster_id
        data['monster_id'] = str(uuid.uuid4())  # Change this line to use UUID
        try:
            # Insert a new monster into DynamoDB
            monsters_table.put_item(Item=data)
            return {'message': 'Monster created successfully'}, 201
        except ClientError as e:
            return {'message': str(e)}, 500


@monsters_namespace.route('/<string:monster_id>')
@monsters_namespace.param('monster_id', 'The monster identifier')
class Monster(Resource):
    @monsters_namespace.doc('get_monster')
    def get(self, monster_id):
        """Fetch a monster by monster_id"""
        try:
            response = monsters_table.get_item(Key={'monster_id': monster_id})
            monster = response.get('Item')
            if not monster:
                return {'message': 'Monster not found'}, 404
            return convert_decimals(monster), 200
        except ClientError as e:
            return {'message': str(e)}, 500

    @monsters_namespace.doc('delete_monster')
    def delete(self, monster_id):
        """Delete a monster by monster_id"""
        try:
            monsters_table.delete_item(Key={'monster_id': monster_id})
            return {'message': 'Monster deleted successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500

    @monsters_namespace.doc('update_monster')
    @monsters_namespace.expect(monster_model)
    def put(self, monster_id):
        """Update a monster by monster_id"""
        data = request.json
        try:
            # Update monster information
            monsters_table.update_item(
                Key={'monster_id': monster_id},
                UpdateExpression="set #name=:new_name, inventory_id=:new_inventory_id, reward_money=:new_reward_money,  reward_xp=:new_reward_xp, level=new_level",
                ExpressionAttributeValues={
                    ':new_name': data['name'],
                    ':new_inventory_id': data['inventory_id'],
                    ':new_reward_money': data['reward_money'],
                    ':new_reward_xp': data['reward_xp'],
                    ':new_level': data['level']
                },
                ExpressionAttributeNames={
                    '#name': 'name',
                }
            )
            return {'message': 'Monster updated successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500
