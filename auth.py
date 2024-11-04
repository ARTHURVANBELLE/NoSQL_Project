from flask import Blueprint, request, render_template, redirect, url_for, jsonify, make_response
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import dynamoConnect

# Initialize DynamoDB
dynamodb = dynamoConnect.dynamodb_resource
users_table = dynamodb.Table("users")
logs_table = dynamodb.Table("logs")

# Define Blueprint for authentication
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('uname')
        if not username:
            return jsonify({'error': 'Username is required'}), 400

        # Check if user exists
        try:
            response = users_table.scan(
                FilterExpression=boto3.dynamodb.conditions.Attr('name').eq(username)
            )
            if 'Items' not in response or not response['Items']:
                return jsonify({'error': 'User not found'}), 404
            
            user = response['Items'][0]  # Assume username is unique
            user_id = user['user_id']
            
            # Log the login with user_id and current timestamp
            current_time = datetime.utcnow().isoformat() + 'Z'
            log_login(user_id, current_time)
            
            # Redirect to actions input page with user_id
            return redirect(url_for('auth.actions', user_id=user_id))
        except ClientError as e:
            return jsonify({'error': str(e)}), 500

    # Render the login page on GET request
    return render_template('login.html')

def log_login(user_id, date_time):
    """Log a user login action."""
    try:
        log = {
            'user_id': user_id,
            'date_time': date_time,
            'actions': 'LOGIN'
        }
        logs_table.put_item(Item=log)
    except ClientError as e:
        print(f"Error logging action: {e}")

@auth.route('/actions/<string:user_id>', methods=['GET', 'POST'])
def actions(user_id):
    if request.method == 'POST':
        action = request.form.get('action')
        if action:
            current_time = datetime.utcnow().isoformat() + 'Z'
            log_action(user_id, current_time, action)
            return jsonify({'message': 'Action logged successfully'}), 201
        else:
            return jsonify({'error': 'Action is required'}), 400

    return render_template('actions_input.html', user_id=user_id)

def log_action(user_id, date_time, action):
    """Log a specific user action."""
    try:
        log = {
            'user_id': user_id,
            'date_time': date_time,
            'actions': action
        }
        logs_table.put_item(Item=log)
    except ClientError as e:
        print(f"Error logging action: {e}")
