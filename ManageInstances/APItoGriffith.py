from flask import Flask, request, jsonify
import csv
import os
import boto3
from datetime import datetime
from abc import ABC, abstractmethod

app = Flask(__name__)

# CSV file path
CSV_FILE_PATH = '/home/murli/hackathon-2024/ManageInstances/ec2_conditions.csv'

# Ensure the CSV file exists with headers if it's not present
if not os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['InstanceID', 'Weekend', 'NightTime', 'PublicHoliday', 'CustomStartTime', 'CustomEndTime'])


# AWS Resource Management (EC2 and RDS)
class AWSResource(ABC):

    @abstractmethod
    def list_instances(self):
        pass

    @abstractmethod
    def start_instance(self, instance_id):
        pass

    @abstractmethod
    def stop_instance(self, instance_id):
        pass


class EC2Resource(AWSResource):

    def __init__(self, session):
        self.client = session.client('ec2')

    def list_instances(self):
        response = self.client.describe_instances()
        instances = [instance for reservation in response['Reservations'] for instance in reservation['Instances']]
        return instances

    def start_instance(self, instance_id):
        self.client.start_instances(InstanceIds=[instance_id])
        return f"EC2 instance {instance_id} is starting."

    def stop_instance(self, instance_id):
        self.client.stop_instances(InstanceIds=[instance_id])
        return f"EC2 instance {instance_id} is stopping."


class RDSResource(AWSResource):

    def __init__(self, session):
        self.client = session.client('rds')

    def list_instances(self):
        response = self.client.describe_db_instances()
        instances = response['DBInstances']
        return instances

    def start_instance(self, instance_id):
        self.client.start_db_instance(DBInstanceIdentifier=instance_id)
        return f"RDS instance {instance_id} is starting."

    def stop_instance(self, instance_id):
        self.client.stop_db_instance(DBInstanceIdentifier=instance_id)
        return f"RDS instance {instance_id} is stopping."


class AWSResourceFactory:

    @staticmethod
    def create_resource(resource_type, session):
        if resource_type == 'EC2':
            return EC2Resource(session)
        elif resource_type == 'RDS':
            return RDSResource(session)
        else:
            raise ValueError(f"Resource type '{resource_type}' is not supported.")


# AWS Session Setup (You can modify to use environment variables or other security practices)
def get_aws_session():
    return boto3.Session(
        aws_access_key_id='AKIAVVPPFW4MGPYYQYPU',
        aws_secret_access_key='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',
        region_name='us-west-2'
    )


# API to add data to CSV
@app.route('/add_instance_condition', methods=['POST'])
def add_instance_condition():
    data = request.json

    # Required fields in the JSON payload
    required_fields = ['InstanceID', 'Weekend', 'NightTime', 'PublicHoliday', 'CustomStartTime', 'CustomEndTime']

    # Check if all required fields are present
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing fields in the request'}), 400

    # Append the data to the CSV
    with open(CSV_FILE_PATH, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            data['InstanceID'],
            data['Weekend'],
            data['NightTime'],
            data['PublicHoliday'],
            data['CustomStartTime'],
            data['CustomEndTime']
        ])

    return jsonify({'message': 'Instance condition added successfully!'}), 201


# API to list EC2 instances
@app.route('/list_ec2_instances', methods=['GET'])
def list_ec2_instances():
    session = get_aws_session()
    ec2_resource = AWSResourceFactory.create_resource('EC2', session)
    instances = ec2_resource.list_instances()

    # Format the instances' information
    instance_list = []
    for instance in instances:
        instance_data = {
            'InstanceID': instance.get('InstanceId'),
            'State': instance['State']['Name'],
            'InstanceType': instance.get('InstanceType'),
            'LaunchTime': instance.get('LaunchTime').strftime('%Y-%m-%d %H:%M:%S')
        }
        instance_list.append(instance_data)

    return jsonify({'ec2_instances': instance_list})


# API to list RDS instances
@app.route('/list_rds_instances', methods=['GET'])
def list_rds_instances():
    session = get_aws_session()
    rds_resource = AWSResourceFactory.create_resource('RDS', session)
    instances = rds_resource.list_instances()

    # Format the instances' information
    instance_list = []
    for instance in instances:
        instance_data = {
            'DBInstanceIdentifier': instance.get('DBInstanceIdentifier'),
            'DBInstanceStatus': instance.get('DBInstanceStatus'),
            'DBInstanceClass': instance.get('DBInstanceClass'),
            'Engine': instance.get('Engine'),
            'Endpoint': instance.get('Endpoint', {}).get('Address')
        }
        instance_list.append(instance_data)

    return jsonify({'rds_instances': instance_list})


# API to stop/start EC2 instance
@app.route('/ec2_instance/<action>', methods=['POST'])
def manage_ec2_instance(action):
    session = get_aws_session()
    ec2_resource = AWSResourceFactory.create_resource('EC2', session)

    data = request.json
    instance_id = data.get('InstanceID')

    if not instance_id:
        return jsonify({'error': 'InstanceID is required'}), 400

    if action == 'start':
        message = ec2_resource.start_instance(instance_id)
    elif action == 'stop':
        message = ec2_resource.stop_instance(instance_id)
    else:
        return jsonify({'error': 'Invalid action'}), 400

    return jsonify({'message': message})


# API to stop/start RDS instance
@app.route('/rds_instance/<action>', methods=['POST'])
def manage_rds_instance(action):
    session = get_aws_session()
    rds_resource = AWSResourceFactory.create_resource('RDS', session)

    data = request.json
    db_instance_id = data.get('DBInstanceIdentifier')

    if not db_instance_id:
        return jsonify({'error': 'DBInstanceIdentifier is required'}), 400

    if action == 'start':
        message = rds_resource.start_instance(db_instance_id)
    elif action == 'stop':
        message = rds_resource.stop_instance(db_instance_id)
    else:
        return jsonify({'error': 'Invalid action'}), 400

    return jsonify({'message': message})


# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
