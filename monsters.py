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
    'monster_type': fields.String(required=True, description='Monster type'),
    'monster_name': fields.String(required=True, description='Monster name'),
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
                monsters = [monster for monster in monsters if search.lower() in monster['monster_name'].lower() or search.lower() in monster['monster_type'].lower()]
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
        print(data)

        try:
            
           # Check if all required fields for the table schema are present
            required_keys = ["monster_type", "monster_name"]
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Missing required field: {key}")            


            # Convert fields to required types (DynamoDB type restrictions)
            data['inventory_id'] = int(data['inventory_id'])
            data['reward_money'] = int(data['reward_money'])
            data['reward_xp'] = int(data['reward_xp'])
            data['level'] = int(data['level'])

            

            # Debugging: Print the final data before insertion
            print("Final data to insert:", data)
            # Insert a new monster into DynamoDB
            monsters_table.put_item(Item=data)
            print("done")




            return {'message': 'Monster created successfully'}, 201
        except ClientError as e:
            print("DynamoDB ClientError:", str(e))
            return {'message': str(e)}, 500
        except ValueError as ve:
            print("Validation Error:", str(ve))
            return {'message': str(ve)}, 400        


@monsters_namespace.route('/<string:monster_type>/<string:monster_name>')
@monsters_namespace.param('monster_type', 'The monster type')
@monsters_namespace.param('monster_name', 'The monster name')

class Monster(Resource):
    @monsters_namespace.doc('get_monster')
    def get(self, monster_name, monster_type):
        """Fetch a monster by monster_name and monster_type"""
        try:
            print(f"Fetching monster with type: {monster_type}, name: {monster_name}")
            response = monsters_table.get_item(Key={'monster_name': monster_name, 'monster_type':monster_type})
            print(response)
            if 'Item' not in response:
                return {'message': 'Monster not found'}, 404
            print(monster_name)
            print(monster_type)
            monster = response.get('Item')
            monster_data = {
                "monster_name": monster_name,
                "monster_type": monster_type,
                "reward_money": monster.get('reward_money'),
                "reward_xp": monster.get('reward_xp'),
                
                "level": monster.get('level'),
                "inventory_id": monster.get('inventory_id')
            }
            if not monster_data:
                return {'message': 'Monster not found'}, 404

            html_content = render_template('monster_templates/monster_detail.html', monster=monster_data)
            response = make_response(html_content)

            #html_content = render_template('create_monster.html')
            #response = monsters_table.get_item(Key={'monster_type': monster_type, 'monster_name': monster_name})
            #monster = response.get('Item')
            #if not monster:
            #    return {'message': 'Monster not found'}, 404
            #return convert_decimals(monster), 200
            
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            return {'message': str(e)}, 500

    @monsters_namespace.doc('delete_monster')
    def delete(self, monster_name, monster_type):
        """Delete a monster by monster_type and monster_name"""
        try:
            monsters_table.delete_item(Key={'monster_name': monster_name, 'monster_type':monster_type})
            return {'message': 'Monster deleted successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500
    
    @monsters_namespace.doc('update_monster')
    @monsters_namespace.expect(monster_model)
    def put(self, monster_name, monster_type):
        """Update a monster by monster_type and monster_name"""
        data = request.json
        print("hello")
        print(data)
        try:
            # Update monster information
            monsters_table.update_item(
            Key={'monster_name': monster_name, 'monster_type': monster_type},
            UpdateExpression="SET inventory_id = :new_inventory_id, "
                             "reward_money = :new_reward_money, reward_xp = :new_reward_xp, #level = :new_level",
            ExpressionAttributeValues={
                ':new_inventory_id': data['inventory_id'],
                ':new_reward_money': data['reward_money'],
                ':new_reward_xp': data['reward_xp'],
                ':new_level': data['level']
            },
            ExpressionAttributeNames={
                '#level': 'level'  # Alias for the reserved keyword 'level'
            }
        )

            return {'message': 'Monster updated successfully'}, 200
        except ClientError as e:
            print("DynamoDB ClientError:", e.response['Error']['Message'])
            return {'message': str(e)}, 500
        
@monsters_namespace.route('/<string:monster_type>/<string:monster_name>/edit')
@monsters_namespace.param('monster_type', 'The monster type')
@monsters_namespace.param('monster_name', 'The monster name')
class EditMonster(Resource):
    @monsters_namespace.doc('edit_monster_page')
    def get(self, monster_type, monster_name):
        """Fetch monster data for editing."""
        try:
            # Retrieve monster data using the composite key of monster_type and monster_name
            response = monsters_table.get_item(Key={
                'monster_type': monster_type,
                'monster_name': monster_name
            })
            monster = response.get('Item')
            if not monster:
                return {'message': 'Monster not found'}, 404


            # Define available monster types
            monster_types = [
                {"monster_type": "Dragon"},
                {"monster_type": "Goblin"},
                {"monster_type": "Troll"},
                {"monster_type": "Golem"},
                {"monster_type": "Vampire"}
            ]

            # Prepare monster data
            monster_data = {
                "monster_type": monster['monster_type'],
                "monster_name": monster['monster_name'],
                "reward_money": monster.get('reward_money', 0),
                "inventory_id": monster.get('inventory_id', 0),
                "reward_xp": monster.get('reward_xp', 0),
                "level": monster.get('level', "Unknown")
            }

            # Render the template with monster data; monster types are embedded in the HTML
            html_content = render_template(
                'monster_templates/monster_edit.html', 
                monster=monster_data,
                monster_types=monster_types
            )
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response

        except ClientError as e:
            return {'message': str(e)}, 500


