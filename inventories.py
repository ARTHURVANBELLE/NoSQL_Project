from flask import request, render_template, jsonify, make_response
from flask_restx import Api, Resource, fields, Namespace
import boto3
from botocore.exceptions import ClientError

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