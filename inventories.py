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
    'inventory_id': fields.String(required=True, description='Inventory ID'),
    'item_id_dict': fields.String(required=True, description='Item ID Dictionary')
})

@inventory_namespace.route('/<string:inventory_id>')
@inventory_namespace.param('inventory_id', 'The inventory identifier')
class Inventory(Resource):
    @inventory_namespace.doc('get_inventory')
    def get(self, inventory_id):
        """Fetch an inventory by ID"""
        try:
            item_id_list = get_inventory_data(inventory_id)
                
            inventory_data = get_items_data(item_id_list)

            if not inventory_data:
                inventory_data = []
                
            html_content = render_template('inventory.html', inventory_id =inventory_id, inventory_items=inventory_data)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
        
        except ClientError as e:
            html_content = render_template('inventory.html')
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
    
@inventory_namespace.route('/add_item/<string:item_name>/<string:inventory_id>/<string:item_id>')
@inventory_namespace.doc('add_item')
class AddItem(Resource):
    def post(self, item_name, item_id, inventory_id):
        """Add an item to the inventory"""
        try:
            # Update the inventory table to add the item name to the item_id_list
            fill_inventory(inventory_id,item_id , item_name)
            item_id_list = get_inventory_data(inventory_id)
            inventory_data = get_items_data(item_id_list)
            
            html_content = render_template('inventory.html', inventory_id =inventory_id, inventory_items=inventory_data)
            response = make_response(html_content)
            response.headers['Content-Type'] = 'text/html'
            return response
            
        except ClientError as e:
            return {'message': str(e)}, 500


#Separate route for the search functionality
@inventory_namespace.route('/search/<string:inventory_id>')
class Search(Resource):
    def post(self, inventory_id):
        search_query = request.form.get('search_query')
        search_results = []
        
        if search_query:
            # Fetch the search results from DynamoDB
            search_results = search_items_in_dynamodb(search_query.lower())
        
        item_id_list = get_inventory_data(inventory_id)
        inventory_data = get_items_data(item_id_list)


        html_content = render_template('inventory.html',inventory_id = inventory_id, inventory_items=inventory_data, search_results=search_results)
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response
    
    
#Separate route for the search functionality
@inventory_namespace.route('/delete/<string:item_name>/<string:inventory_id>/<string:item_id>')
class Delete(Resource):
    def post(self, inventory_id, item_name, item_id):
        # Delete the item from the inventory
        delete_item(inventory_id, item_id, item_name)
        
        item_id_list = get_inventory_data(inventory_id)
        inventory_data = get_items_data(item_id_list)
        
        html_content = render_template('inventory.html',inventory_id = inventory_id, inventory_items=inventory_data)
        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html'
        return response
    
    
@inventory_namespace.route('/update/<string:item_name>/<string:item_id>/<string:inventory_id>')
class Update(Resource):
    def post(self, inventory_id, item_name, item_id):
        quantity = request.form.get('newItemQuantity')
        
        if quantity and int(quantity) > 0:
            update_item(inventory_id, item_id, item_name, int(quantity))
        
        item_id_list = get_inventory_data(inventory_id)
        inventory_data = get_items_data(item_id_list)
        
        html_content = render_template('inventory.html',inventory_id = inventory_id, inventory_items=inventory_data)
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

def fill_inventory(inventory_id, new_item_id, new_item_name):
    # Fetch the inventory data from DynamoDB
    response = inventory_table.get_item(Key={'inventory_id': inventory_id})
    inventory = response.get('Item')
    
    if not inventory:
        item_id_dict = {}
    else:
        item_id_dict = inventory.get('item_id_dict', {})
        
    # Add the new item to the inventory
    item_id_dict[(new_item_id + "," + new_item_name)] = 1
    
    # Update the inventory table with the new item
    inventory_table.update_item(
        Key={'inventory_id': inventory_id},
        UpdateExpression='SET item_id_dict = :item_id_dict',
        ExpressionAttributeValues={':item_id_dict': item_id_dict}
    )
    
def get_inventory_data(inventory_id):
    response = inventory_table.get_item(Key={'inventory_id': inventory_id})

    inventory = response.get('Item')

    if not inventory:
        item_id_dict = {}
    else:
        item_id_dict = inventory.get('item_id_dict', {})

    return item_id_dict

def get_items_data(item_id_dict):
    items_data = []
    
    if not item_id_dict:
        return items_data
    
    for item_data in item_id_dict.keys():
        item_name = item_data.split(",")[1]
        item_id = item_data.split(",")[0]
        response = item_table.get_item(Key={'item_id': item_id, 'item_name': item_name})
        item = response.get('Item')
        
        
        if item:
            item['item_quantity'] = item_id_dict[item_data]
            print("quantity -----------------")
            print(item['item_quantity'])
            items_data.append(item)
    
    return items_data

def delete_item(inventory_id, item_id, item_name):
    # Fetch the inventory data from DynamoDB
    response = inventory_table.get_item(Key={'inventory_id': inventory_id})
    inventory = response.get('Item')
    
    if not inventory:
        return False

    item_id_dict = inventory.get('item_id_dict', {})
    item_id_composed = item_id + "," + item_name
    
    # Remove the item from the inventory
    if item_id_composed in item_id_dict:
        del item_id_dict[item_id_composed]
        
        # Update the inventory table with the new item list
        inventory_table.update_item(
            Key={'inventory_id': inventory_id},
            UpdateExpression='SET item_id_dict = :item_id_dict',
            ExpressionAttributeValues={':item_id_dict': item_id_dict}
        )
        
        return True
    
    return False

def update_item(inventory_id, item_id, item_name, quantity):
    # Fetch the inventory data from DynamoDB
    response = inventory_table.get_item(Key={'inventory_id': inventory_id})
    inventory = response.get('Item')
    
    if not inventory:
        return False

    item_id_dict = inventory.get('item_id_dict', {})
    item_id_composed = item_id + "," + item_name
    
    # Update the quantity of the item in the inventory
    if item_id_composed in item_id_dict:
        item_id_dict[item_id_composed] = quantity
        
        # Update the inventory table with the new item list
        inventory_table.update_item(
            Key={'inventory_id': inventory_id},
            UpdateExpression='SET item_id_dict = :item_id_dict',
            ExpressionAttributeValues={':item_id_dict': item_id_dict}
        )
        
        return True
    
    return False