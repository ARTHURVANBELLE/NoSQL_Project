import boto3
from botocore.exceptions import ClientError


dynamodb_client = boto3.client('dynamodb', 
                        endpoint_url='http://localhost:8000', 
                        region_name='eu-west-1',
                        aws_access_key_id='fakeMyKeyId',
                        aws_secret_access_key='fakeSecretAccessKey')

dynamodb_resource = boto3.resource('dynamodb', 
                        endpoint_url='http://localhost:8000', 
                        region_name='eu-west-1',
                        aws_access_key_id='fakeMyKeyId',
                        aws_secret_access_key='fakeSecretAccessKey')

def table_exists(table_name):
    """Check if a DynamoDB table exists."""
    try:
        dynamodb_client.describe_table(TableName=table_name)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print(f"Table '{table_name}' does not exist.")
            return False
        else:
            # For any other exceptions
            print(f"Error occurred: {e}")
            return False

def create_table(table_name, keySchema, attributeDefinitions):
    """Create a DynamoDB table if it doesn't exist."""
    if not table_exists(table_name):
        try:
            # Define the table schema
            table = dynamodb_client.create_table(
                TableName = table_name,
                KeySchema = keySchema,
                AttributeDefinitions = attributeDefinitions,
                ProvisionedThroughput = universalThroughPut
            )

            # Wait until the table is created
            dynamodb_client.get_waiter('table_exists').wait(TableName=table_name)
            print(f"Table '{table_name}' created successfully.")
        except ClientError as e:
            print(f"Error creating table: {e}")
    else:
        print(f"Table '{table_name}' already exists. No need to create.")

universalThroughPut = {'ReadCapacityUnits': 10,'WriteCapacityUnits': 10}

table_Users = "users"
user_keySchema = [
        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
    ]
user_attributeDefinitions = [
        {'AttributeName': 'user_id', 'AttributeType': 'N'}
    ]

table_Clans = "clans"
clan_keySchema = [
        {'AttributeName': 'clan_id', 'KeyType': 'HASH'}
    ]
clan_attributeDefinitions = [
        {'AttributeName': 'clan_id', 'AttributeType': 'N'}
    ]

table_Monsters = "monsters"
monster_keySchema = [
        {'AttributeName': 'monster_type', 'KeyType': 'HASH'},
        {'AttributeName': 'monster_name', 'KeyType': 'RANGE'}
    ]
monster_attributeDefinitions = [
        {'AttributeName': 'monster_type', 'AttributeType': 'S'},
        {'AttributeName': 'monster_name', 'AttributeType': 'S'}
    ]

table_Inventories = "inventories"
inventory_keySchema = [
        {'AttributeName': 'inventory_id', 'KeyType': 'HASH'}
    ]
inventory_attributeDefinitions = [
        {'AttributeName': 'inventory_id', 'AttributeType': 'N'}
    ]

# Items are composed of an ID (partition key) representing the type and the nbr of the item (for ex : "W1" for the 1st weapon)
# & of a name (range key) that can be the same for mutliple items

table_Items = "items"
item_keySchema = [
        {'AttributeName': 'item_id', 'KeyType': 'HASH'},
        {'AttributeName': 'item_name', 'KeyType': 'RANGE'},
        
    ]
item_attributeDefinitions = [
        {'AttributeName': 'item_id', 'AttributeType': 'S'},
        {'AttributeName': 'item_name', 'AttributeType': 'S'}
    ]

# table_Weapons = "weapons"
# weapon_keySchema = [
#         {'AttributeName': 'weapon_subtype', 'KeyType': 'HASH'},
#         {'AttributeName': 'weapon_id', 'KeyType': 'RANGE'}
#     ]
# weapon_attributeDefinitions = [
#         {'AttributeName': 'weapon_subtype', 'AttributeType': 'S'},
#         {'AttributeName': 'weapon_id', 'AttributeType': 'N'}
#     ]

# table_Armors = "armors"
# armor_keySchema = [
#         {'AttributeName': 'armor_subtype', 'KeyType': 'HASH'},
#         {'AttributeName': 'armor_id', 'KeyType': 'RANGE'}
#     ]
# armor_attributeDefinitions = [
#         {'AttributeName': 'armor_subtype', 'AttributeType': 'S'},
#         {'AttributeName': 'armor_id', 'AttributeType': 'N'}
#     ]

create_table(table_Users, user_keySchema, user_attributeDefinitions)
create_table(table_Clans, clan_keySchema, clan_attributeDefinitions)
create_table(table_Monsters, monster_keySchema, monster_attributeDefinitions)
create_table(table_Inventories, inventory_keySchema, inventory_attributeDefinitions)
create_table(table_Items, item_keySchema, item_attributeDefinitions)
# create_table(table_Weapons, weapon_keySchema, weapon_attributeDefinitions)
# create_table(table_Armors, armor_keySchema, armor_attributeDefinitions)

def list_dynamodb_tables():
    try:
        # Get the list of tables
        response = dynamodb_client.list_tables()
        
        table_names = response.get('TableNames', [])
        
        if table_names:
            print("Existing DynamoDB tables:")
            for table in table_names:
                print(table)
        else:
            print("No tables found.")
    
    except Exception as e:
        print(f"Error listing tables: {e}")

# Call the function to print the tables
list_dynamodb_tables()

try:
    items = dynamodb_resource.Table('items')
    # items.put_item(
    #     Item =
    #     {
    #         'item_id': 'W1',
    #         'item_name': 'Claymore'
    #     }
    # )
    response = items.get_item(
        Key={
            'item_id': 'W1',
            'item_name': 'Claymore'
        }
    )

    item = response["Item"]
    print(item)
except ClientError as e:
    print('Error Code: {}'.format(e.response['Error']['Code']))