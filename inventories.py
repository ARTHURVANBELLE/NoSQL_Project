from flask import request, render_template, jsonify, make_response
from flask_restx import Api, Resource, fields, Namespace
import boto3
from botocore.exceptions import ClientError

import dynamoConnect

import uuid
from decimal import Decimal

# Initialize the Namespace (not an Api)
inventory_namespace = Namespace('v1/inventory', description='Inventory Operation')
inventory_table = dynamoConnect.dynamodb_resource.Table("inventories")

# Define the user model for the Swagger UI
inventory_model = inventory_namespace.model('Inventory', {
    'inventory_id': fields.String(required=True, description='Unique user identifier'),
    'item_id_list': fields.String(required=True, description='User name')
})

@inventory_namespace.route('/<string:inventory_id>')
@inventory_namespace.param('inventory_id', 'The inventory identifier')

class Inventory(Resource):
    @inventory_namespace.doc('get_inventory')
    def get(self, inventory_id):
        """Fetch an inventory by ID"""
        try:
            response = inventory_table.get_item(Key={'inventory_id': inventory_id})
            inventory = response.get('Item')
            inventory_data = {
                "invntory_id": inventory_id,
                #"item_id_list": inventory.get('item_id_list', "Unknown"),
            }
            if not inventory_data:
                return {'message': 'Inventory not found'}, 404
            
            html_content = render_template('inventory.html', inventory=inventory_data)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        except ClientError as e:
            #return {'message': str(e)}, 500
            html_content = render_template('inventory.html')
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response