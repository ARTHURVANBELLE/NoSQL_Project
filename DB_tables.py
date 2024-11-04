import boto3
from botocore.exceptions import ClientError

import dynamoConnect

dynamodb_client = dynamoConnect.dynamodb_client

dynamodb_resource = dynamoConnect.dynamodb_resource

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

def create_table(table_name, keySchema, attributeDefinitions, constant_elements = None):
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

            if constant_elements:

                table = dynamoConnect.dynamodb_resource.Table(table_name)

                for element in constant_elements:
                    if table_name == "user_classes":
                        new_user_class = {
                            "user_class": element
                        }

                        table.put_item(Item=new_user_class)

        except ClientError as e:
            print(f"Error creating table: {e}")
    # else:
    #     print(f"Table '{table_name}' already exists. No need to create.")

universalThroughPut = {'ReadCapacityUnits': 10,'WriteCapacityUnits': 10}

table_Users = "users"
user_keySchema = [
        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
    ]
user_attributeDefinitions = [
        {'AttributeName': 'user_id', 'AttributeType': 'S'}
    ]

# table_Users = "users"
# user_keySchema = [
#         {'AttributeName': 'user_id', 'KeyType': 'HASH'}
#     ]
# user_attributeDefinitions = [
#         {'AttributeName': 'user_id', 'AttributeType': 'N'}
#     ]

table_Clans = "clans"
clan_keySchema = [
        {'AttributeName': 'clan_id', 'KeyType': 'HASH'}
    ]
clan_attributeDefinitions = [
        {'AttributeName': 'clan_id', 'AttributeType': 'S'}
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
        {'AttributeName': 'inventory_id', 'AttributeType': 'S'}
    ]

# Items are composed of an ID reprensting the type (Eg weapon, armor, potion, etc) (hash key)
# & of a name (range key) that can not be the same as another item of the same type

table_Items = "items"
item_keySchema = [
        {'AttributeName': 'item_id', 'KeyType': 'HASH'},
        {'AttributeName': 'item_name', 'KeyType': 'RANGE'},
        
    ]
item_attributeDefinitions = [
        {'AttributeName': 'item_id', 'AttributeType': 'S'},
        {'AttributeName': 'item_name', 'AttributeType': 'S'}
    ]

table_Logs = "logs"
logs_keySchema = [
        {'AttributeName': 'user_id', 'KeyType': 'HASH'},
        {'AttributeName': 'date_time', 'KeyType': 'RANGE'},
        
    ]
logs_attributeDefinitions = [
        {'AttributeName': 'user_id', 'AttributeType': 'S'},
        {'AttributeName': 'date_time', 'AttributeType': 'S'}
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
create_table(table_Logs, logs_keySchema, logs_attributeDefinitions)

# create_table(table_Weapons, weapon_keySchema, weapon_attributeDefinitions)
# create_table(table_Armors, armor_keySchema, armor_attributeDefinitions)

table_User_Classes = "user_classes"
user_classes_keySchema = [
        {'AttributeName': 'user_class', 'KeyType': 'HASH'}
    ]
user_classes_attributeDefinitions = [
        {'AttributeName': 'user_class', 'AttributeType': 'S'}
    ]

user_classes = [
    "warrior", "mage", "priest", "ranger", "paladin"
]

create_table(table_User_Classes, user_classes_keySchema, user_classes_attributeDefinitions, user_classes)
