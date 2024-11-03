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
    'item_properties': fields.List(fields.String, required=True, description='Item properties') 
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
        print("Received payload:", data)  # For debugging
        create_item(data['item_name'], data['item_id'], data['item_rarity'], data['item_properties'])
        return data, 201




# Endpoint for the HTML page at '/items_api/items'
@items_namespace.route('/items')
class ItemPage(Resource):
    def get(self):
        """Render the items list as an HTML page"""
        items = get_all_items()
        return make_response(render_template('create_item.html', items=items))
    
# Update the Item resource class in your Flask app
@items_namespace.route('/<string:item_id>/<string:item_name>')
class Item(Resource):
    def get(self, item_id, item_name):
        """Get a specific item by ID and Name"""
        try:
            response = items_table.get_item(
                Key={
                    'item_id': item_id,
                    'item_name': item_name
                }
            )
            if 'Item' in response:
                return response['Item']
            return {'message': 'Item not found'}, 404
        except ClientError as e:
            return {'message': str(e)}, 500

    @items_namespace.expect(item_model)
    @items_namespace.marshal_with(item_model)
    def put(self, item_id, item_name):
        """Update an existing item"""
        try:
            data = request.json
            new_item_id = data.get('new_item_id', item_id)
            new_item_name = data.get('item_name', item_name)

            # Delete the old item first
            delete_item(item_id, item_name)

            # Create new item with updated data
            create_item(
                new_item_name,
                new_item_id,
                data['item_rarity'],
                data['item_properties']
            )
            return data, 200
        except Exception as e:
            return {'message': str(e)}, 500

    def delete(self, item_id, item_name):
        """Delete an item"""
        try:
            delete_item(item_id, item_name)
            return {'message': 'Item deleted successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500




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
def update_item(item_id, item_name, item_rarity, item_properties):
    """Update non-key fields of an existing item in the DynamoDB table."""
    try:
        items_table.update_item(
            Key={'item_id': item_id},
            UpdateExpression="SET item_name = :name, item_rarity = :rarity, item_properties = :properties",
            ExpressionAttributeValues={
                ':name': item_name,
                ':rarity': item_rarity,
                ':properties': item_properties
            }
        )
    except ClientError as e:
        print(f"Error updating item: {e}")

def delete_item(item_id, item_name):
    """Delete an item from the DynamoDB table by item_id and item_name."""
    try:
        response = items_table.delete_item(
            Key={
                'item_id': item_id,    # Partition key
                'item_name': item_name  # Sort key
            },
            ReturnValues='ALL_OLD'  # Optional: return deleted item attributes
        )
        if 'Attributes' not in response:
            raise Exception('Item not found')
    except ClientError as e:
        print(f"Error deleting item: {e}")
        raise e



