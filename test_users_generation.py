import boto3
import uuid
import random
import string
from decimal import Decimal
import dynamoConnect

users_table = dynamoConnect.dynamodb_resource.Table("users")
clans_table = dynamoConnect.dynamodb_resource.Table("clans")
inventory_table = dynamoConnect.dynamodb_resource.Table("inventories")

# List of sample user classes
user_classes_list = ['Warrior', 'Mage', 'Rogue', 'Cleric', 'Archer']

def random_string(length):
    """Generate a random string of uppercase letters and digits."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def generate_random_user():
    """Generate a random user with attributes."""
    user_id = str(uuid.uuid4())
    name = random_string(10)
    clan_id = None
    money = random.randint(0, 100000)
    xp = random.randint(0, 10000)
    elo = random.randint(0, 3000)
    user_class = random.choice(user_classes_list)

    user_data = {
        'user_id': user_id,
        'name': name,
        'clan_id': clan_id,
        'money': Decimal(money),
        'inventory_id': user_id,  # Using the same user_id as inventory_id
        'xp': Decimal(xp),
        'elo': Decimal(elo),
        'user_class': user_class
    }

    inventory_data = {
        'inventory_id': user_id,
        'item_id_dict': {}
    }

    return user_data, inventory_data

def insert_users(batch_size=25, total_users=50000):
    """Insert random users into the DynamoDB table in batches."""
    for i in range(0, total_users, batch_size):
        with users_table.batch_writer() as user_batch, inventory_table.batch_writer() as inventory_batch:
            for _ in range(batch_size):
                user_data, inventory_data = generate_random_user()
                user_batch.put_item(Item=user_data)
                inventory_batch.put_item(Item=inventory_data)
        print(f"Inserted {i + batch_size} users")

# Run the user insertion
if __name__ == "__main__":
    insert_users()
