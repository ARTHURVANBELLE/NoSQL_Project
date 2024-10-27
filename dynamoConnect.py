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