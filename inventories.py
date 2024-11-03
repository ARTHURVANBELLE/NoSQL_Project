from flask import request, render_template, jsonify, make_response
from flask_restx import Api, Resource, fields, Namespace
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Attr, Key


import dynamoConnect

import uuid
from decimal import Decimal

inventory_namespace = Namespace('v1/inventory', description='Inventory Operation')

inventory_table = dynamoConnect.dynamodb_resource.Table("inventories")
item_table = dynamoConnect.dynamodb_resource.Table("items")

# Define the user model for the Swagger UI
inventory_model = inventory_namespace.model('Inventory', {
    'inventory_id': fields.String(required=True, description='Unique user identifier'),
    'item_id_list': fields.String(required=True, description='User name')
})

inventory_items = [
    {
        'id': 1,
        'name': 'Potion',
        'quantity': 10,
        'rarity': 'Consumable',
        'properties': 'Heals 50 HP'
    },
    {
        'id': 2,
        'name': 'Sword',
        'quantity': 1,
        'rarity': 'Weapon',
        'properties': 'A sharp blade for battle'
    }
    # Add more items as needed
]

# Sample items table data - replace with your database
items_table = [
    {'id': 1, 'name': 'Potion', 'category': 'Consumable', 'description': 'Heals 50 HP'},
    {'id': 2, 'name': 'Sword', 'category': 'Weapon', 'description': 'A sharp blade for battle'},
    {'id': 3, 'name': 'Shield', 'category': 'Armor', 'description': 'Protects from attacks'}
]

@inventory_namespace.route('/<string:inventory_id>')
@inventory_namespace.param('inventory_id', 'The inventory identifier')

class Inventory(Resource):
    @inventory_namespace.doc('get_inventory')
    def get(self, inventory_id):
        """Fetch an inventory by ID"""
        try:
            response = inventory_table.get_item(Key={'inventory_id': inventory_id})
            inventory = response.get('Item')
            
            if not inventory:
                item_id_list = []
            else:
                item_id_list = inventory.get('item_id_list', [])
                
            inventory_data = {
                "invntory_id": inventory_id,
                "item_id_list": item_id_list,
            }
            if not inventory_data:
                return {'message': 'Inventory not found'}, 404
            
            html_content = render_template('inventory.html', inventory_items=inventory_data)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        
        except ClientError as e:
            #return {'message': str(e)}, 500
            html_content = render_template('inventory.html')
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response

#Separate route for the search functionality
@inventory_namespace.route('/search')
class Search(Resource):
    def post(self):
        search_query = request.form.get('search_query')
        search_results = []
        
        if search_query:
            # Fetch the search results from DynamoDB
            search_results = search_items_in_dynamodb(search_query.lower())


        html_content = render_template('inventory.html', inventory_items=[], search_results=search_results)
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response


def search_items_in_dynamodb(search_query):
    # scan table for all items
    response = item_table.scan()
    items = response.get('Items', [])
    
    # Perform additional filtering in Python if necessary for case insensitivity
    search_results = [
        item for item in items if search_query.lower() in item['item_name'].lower()
    ]

    return search_results