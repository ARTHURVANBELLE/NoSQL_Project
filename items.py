import boto3
from botocore.exceptions import ClientError
import dynamoConnect
from flask import request, render_template, jsonify, make_response
from flask_restx import Api, Resource, fields, Namespace

# Initialize DynamoDB and set up Namespace and Table
table_name = "items"
items_table = dynamoConnect.dynamodb_resource.Table(table_name)
items_namespace = Namespace('items', description='API for managing items')

# Define Item model for documentation and payload validation
item_model = items_namespace.model('Item', {
    'item_name': fields.String(required=True, description='Item name'),
    'item_id': fields.String(required=True, description='Item ID (eg: consumable001)'),
    'item_rarity': fields.String(required=True, description='Item rarity'),
    'item_properties': fields.String(required=True, description='Item properties')
})

# Endpoint for JSON response of all items at '/items_api'
@items_namespace.route('/')
class ItemList(Resource):
    @items_namespace.marshal_list_with(item_model)
    def get(self):
        """Get all items as JSON"""
        return get_all_items()

    @items_namespace.expect(item_model)
    @items_namespace.marshal_with(item_model, code=201)
    def post(self):
        """Create a new item"""
        data = items_namespace.payload
        print("Received payload:", data)  # Add this line
        create_item(data['item_name'], data['item_id'], data['item_rarity'], data['item_properties'])
        return data, 201


# Endpoint for the HTML page at '/items_api/items'
@items_namespace.route('/items')
class ItemPage(Resource):
    def get(self):
        """Render the items list as an HTML page"""
        items = get_all_items()
        return make_response(render_template('create_item.html', items=items))


# Helper functions for database operations
def create_item(item_name, item_id, item_rarity, item_properties):
    """Add a new item to the DynamoDB table."""
    try:
        item = {
            'item_name': item_name,
            'item_id': item_id,
            'item_rarity': item_rarity,
            'item_properties': item_properties
        }
        items_table.put_item(Item=item)
    except ClientError as e:
        print(f"Error adding item: {e}")

def get_all_items():
    """Retrieve all items from the DynamoDB table."""
    try:
        response = items_table.scan()
        return response['Items']
    except ClientError as e:
        print(f"Error retrieving items: {e}")
        return []
