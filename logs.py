import boto3
from botocore.exceptions import ClientError
import dynamoConnect
from flask import request, render_template, jsonify, make_response
from flask_restx import Api, Resource, fields, Namespace

# Initialize DynamoDB and set up Namespace and Table
table_name = "logs"
logs_table = dynamoConnect.dynamodb_resource.Table(table_name)
logs_namespace = Namespace('v1/logs', description='API for managing logs of players')

# Define Item model for documentation and payload validation
logs_model = logs_namespace.model('Logs', {
    'user_id': fields.String(required=True, description='Id of the user'),
    'date_time': fields.String(required=True, description='Date and time of connection'),
    'actions': fields.String(required=False, description='List of actions made by the user'),
})

# Endpoint for JSON response of all logs at '/logs_api'
@logs_namespace.route('/')
class ItemList(Resource):
    @logs_namespace.marshal_list_with(logs_model)
    def get(self):
        """Get all logs as JSON"""
        return get_all_logs()

    @logs_namespace.expect(logs_model)
    @logs_namespace.marshal_with(logs_model, code=201)
    def post(self):
        """Create a new log entry"""
        data = logs_namespace.payload
        create_log(data['user_id'], data['date_time'], data.get('actions', ""))
        return data, 201
    

# Endpoint for the HTML page at '/logs_api/logs'
@logs_namespace.route('/logs')
class ItemPage(Resource):
    def get(self):
        """Render the logs list as an HTML page"""
        logs = get_all_logs()
        return make_response(render_template('create_logs.html', logs=logs))
    
# Endpoint for specific log entry operations
@logs_namespace.route('/<string:user_id>/<string:date_time>')
class Item(Resource):
    def get(self, user_id, date_time):
        """Get a specific log by user_id and date_time"""
        try:
            response = logs_table.get_item(
                Key={
                    'user_id': user_id,
                    'date_time': date_time
                }
            )
            if 'Item' in response:
                return response['Item']
            return {'message': 'Log not found'}, 404
        except ClientError as e:
            return {'message': str(e)}, 500

    def delete(self, user_id, date_time):
        """Delete a log entry"""
        try:
            delete_log(user_id, date_time)
            return {'message': 'Log deleted successfully'}, 200
        except ClientError as e:
            return {'message': str(e)}, 500
        

# Helper functions for database operations
def create_log(user_id, date_time, actions):
    """Add a new item to the DynamoDB table."""
    try:
        log = {
            'user_id': user_id,
            'date_time': date_time,
            'actions': actions,
        }
        logs_table.put_item(Item=log)
    except ClientError as e:
        print(f"Error adding item: {e}")

def get_all_logs():
    """Retrieve all logs from the DynamoDB table."""
    try:
        response = logs_table.scan()
        return response.get('Items', [])
    except ClientError as e:
        print(f"Error retrieving logs: {e}")
        return []

def update_log(user_id, date_time, actions):
    """Update non-key fields of an existing item in the DynamoDB table."""
    try:
        logs_table.update_item(
            Key={'user_id': user_id, 'date_time': date_time},
            UpdateExpression="SET actions = :actions",
            ExpressionAttributeValues={':actions': actions},
        )
    except ClientError as e:
        print(f"Error updating log: {e}")

def delete_log(user_id, date_time):
    """Delete an item from the DynamoDB table by user_id and date_time."""
    try:
        response = logs_table.delete_item(
            Key={
                'user_id': user_id,
                'date_time': date_time
            },
        )
        if 'Attributes' not in response:
            print('Log not found')
    except ClientError as e:
        print(f"Error deleting log: {e}")
