import json
import csv
import os
import boto3
import requests

from flask import Flask, request, jsonify
from abc import ABC, abstractmethod
from flask_cors import CORS
from chat_bot.magnificent_bot import GPTFunctionExecutor
from Notifications import NotificatonV1
from datetime import datetime


app = Flask(__name__)
CORS(app)

# CSV file path
CSV_FILE_PATH = 'ec2_conditions.csv'

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

    def create_snapshot(self, db_instance_identifier, snapshot_identifier=None):
        pass

    def list_snapshots(self, db_instance_identifier=None):
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
        NotificatonV1.main(subject="Started EC2 Instance",
                           body=f"The EC2 instance with instance_id : {instance_id} is Started")
        return f"EC2 instance {instance_id} is starting."

    def stop_instance(self, instance_id):
        self.client.stop_instances(InstanceIds=[instance_id])
        NotificatonV1.main(subject="Stopped EC2 Instance",
                           body=f"The EC2 instance with instance_id : {instance_id} is Stopped")
        return f"EC2 instance {instance_id} is stopping."

    def create_snapshot(self, db_instance_identifier, snapshot_identifier=None):
        pass

    def list_snapshots(self, db_instance_identifier=None):
        pass


class RDSResource(AWSResource):

    def __init__(self, session):
        self.client = session.client('rds')

    def list_instances(self):
        response = self.client.describe_db_instances()
        instances = response['DBInstances']
        return instances

    def start_instance(self, instance_id):
        self.client.start_db_instance(DBInstanceIdentifier=instance_id)
        NotificatonV1.main(subject="Started RDS Instance",
                           body=f"The RDS instance with instance_id : {instance_id} is Started")
        return f"RDS instance {instance_id} is starting."

    def stop_instance(self, instance_id):
        self.client.stop_db_instance(DBInstanceIdentifier=instance_id)
        NotificatonV1.main(subject="Stopped RDS Instance",
                           body=f"The RDS instance with instance_id : {instance_id} is Stopped")
        return f"RDS instance {instance_id} is stopping."

    def create_snapshot(self, db_instance_identifier, snapshot_identifier=None):
        """
        Create a snapshot of the specified RDS instance.

        Parameters:
            db_instance_identifier (str): The identifier of the RDS instance.
            snapshot_identifier (str): Optional. The identifier for the snapshot. If not provided, a default one will be generated.

        Returns:
            dict: The response from AWS after creating the snapshot.
        """
        if not snapshot_identifier:
            # Generate a snapshot name using the instance ID and current timestamp
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            snapshot_identifier = f"{db_instance_identifier}-snapshot-{timestamp}"

        # Create the snapshot
        response = self.client.create_db_snapshot(
            DBInstanceIdentifier=db_instance_identifier,
            DBSnapshotIdentifier=snapshot_identifier
        )
        return response

    def list_snapshots(self, db_instance_identifier=None):
        """
        List all snapshots of the specified RDS instance, or all snapshots if no instance is specified.

        Parameters:
            db_instance_identifier (str): Optional. The identifier of the RDS instance to list snapshots for.

        Returns:
            list: A list of RDS snapshots.
        """
        if db_instance_identifier:
            response = self.client.describe_db_snapshots(DBInstanceIdentifier=db_instance_identifier)
        else:
            response = self.client.describe_db_snapshots()

        snapshots = response['DBSnapshots']
        return snapshots


class AWSResourceFactory:

    @staticmethod
    def create_resource(resource_type, session):
        if resource_type == 'EC2':
            return EC2Resource(session)
        elif resource_type == 'RDS':
            return RDSResource(session)
        else:
            raise ValueError(f"Resource type '{resource_type}' is not supported.")


# API to add or update data in CSV
@app.route('/add_instance_condition', methods=['POST'])
def add_instance_condition():
    data = request.json

    # Required fields in the JSON payload (include Category)
    required_fields = ['InstanceID', 'Category']

    # Check for required fields and set defaults
    instance_id = data.get('InstanceID')
    category = data.get('Category')
    weekend = data.get('Weekend', 'no')  # Default to 'no'
    nighttime = data.get('NightTime', 'no')  # Default to 'no'
    public_holiday = data.get('PublicHoliday', 'no')  # Default to 'no'
    custom_start_time = data.get('CustomStartTime', '00:00')  # Default to '00:00'
    custom_end_time = data.get('CustomEndTime', '23:59')  # Default to '23:59'

    # Validate required fields
    if not instance_id or not category:
        return jsonify({'error': 'Missing InstanceID or Category in the request'}), 400

    updated = False
    rows = []

    # Read the existing CSV file
    with open(CSV_FILE_PATH, mode='r', newline='') as file:
        reader = csv.reader(file)
        header = next(reader)  # Skip the header row
        rows = list(reader)

    # Check if the combination of InstanceID and Category exists and update it
    for i, row in enumerate(rows):
        if row[0] == instance_id and row[1] == category:  # Check if InstanceID and Category match
            rows[i] = [
                instance_id,
                category,
                weekend,
                nighttime,
                public_holiday,
                custom_start_time,
                custom_end_time
            ]
            updated = True
            break

    # If not updated, append a new row
    if not updated:
        rows.append([
            instance_id,
            category,
            weekend,
            nighttime,
            public_holiday,
            custom_start_time,
            custom_end_time
        ])

    # Write the updated data back to the CSV file
    with open(CSV_FILE_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['InstanceID', 'Category', 'Weekend', 'NightTime', 'PublicHoliday', 'CustomStartTime', 'CustomEndTime'])
        writer.writerows(rows)

    if updated:
        return jsonify({'message': 'Instance condition updated successfully!'}), 200
    else:
        return jsonify({'message': 'Instance condition added successfully!'}), 201


# API to list EC2 instances
@app.route('/list_ec2_instances', methods=['GET'])
def list_ec2_instances():
    session = boto3.Session()  # Pass your session to the factory or create it externally
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
    session = boto3.Session()  # Pass your session to the factory or create it externally
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
    session = boto3.Session()  # Pass your session to the factory or create it externally
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
    session = boto3.Session()  # Pass your session to the factory or create it externally
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


# @app.route('/bot_interaction', methods=['POST'])
# def bot_interaction():
#     data = request.json
#     user_input = data.get('user_input')
#
#     if not user_input:
#         return jsonify({'error': 'Missing user input in the request'}), 400
#
#     try:
#         # Initialize GPTFunctionExecutor with your GitHub repo details
#         repo_owner = 'M-jha'  # Replace with your GitHub username
#         repo_name = 'griffith'  # Replace with your repository name
#         executor = GPTFunctionExecutor(repo_owner, repo_name, branch='hackathon_2024')
#         executor.run()
#
#         # Run the bot to interpret user input
#         assistant_reply = executor.interpret_user_prompt(user_input)
#
#         # Try to extract function details from the bot's response
#         function_details_json = executor.extract_function_details_from_reply(assistant_reply)
#
#         if function_details_json:
#             # Parse the function details JSON
#             function_details_list = json.loads(function_details_json)
#
#             # Dynamically execute functions based on the parsed details
#             results = executor.execute_functions(function_details_list)
#             return jsonify({'bot_reply': assistant_reply, 'execution_results': results})
#
#         return jsonify({'bot_reply': assistant_reply, 'message': 'No function details found in the bot response'})
#
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500

@app.route('/bot_interaction', methods=['POST'])
def bot_interaction():
    data = request.json
    user_input = data.get('user_input')
    previous_function_details = data.get('function_details', None)  # Get previous function details if provided

    if not user_input:
        return jsonify({'error': 'Missing user input in the request'}), 400

    try:
        # Initialize GPTFunctionExecutor with your GitHub repo details
        repo_owner = 'M-jha'
        repo_name = 'griffith'
        executor = GPTFunctionExecutor(repo_owner, repo_name, branch='main')

        # Initialize the executor to set up the knowledge base
        executor.initialize()

        # If we have previous function details and the user input is 'good to go' or 'yes'
        if previous_function_details and user_input.lower().strip() in ["yes", "good to go"]:
            # Proceed with executing the function
            results = executor.execute_functions(previous_function_details)
            return jsonify({
                'message': 'Execution completed',
                'execution_results': results
            })

        # If previous function details are provided and the user is filling missing parameters
        if previous_function_details:
            # Handle missing parameters filled by the user
            for function_detail in previous_function_details:
                for param in function_detail['parameters']:
                    if function_detail['parameters'][param] == "":
                        function_detail['parameters'][param] = user_input.strip()

            # Ask the user if they are ready to proceed
            return jsonify({
                'message': "Do you want to proceed with executing these actions? Confirm with 'yes' or 'good to go'.",
                'function_details': previous_function_details
            })

        # No previous function details, start a new interaction
        response = executor.run(user_input)

        # Return the response which now includes assistant interaction, missing parameter handling, or confirmation request
        return jsonify(response)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# GitHub API URL and PAT
org_name = "GriffithGithubOrg"
github_pat = os.getenv("GIT_SECRET")
print(github_pat)

# Route to get organization members
@app.route('/org-members', methods=['GET'])
def get_org_members():
    url = f"https://api.github.com/orgs/{org_name}/members"
    headers = {
        "Authorization": f"token {github_pat}"
    }

    # Make the request to GitHub API
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        members = response.json()
        member_list = [{"username": member['login']} for member in members]
        return jsonify({"data": member_list}), 200  # Send members under "data"
    else:
        return jsonify({"error": f"Failed to retrieve members: {response.status_code} - {response.text}"}), response.status_code


@app.route('/create_rds_snapshot', methods=['POST'])
def create_rds_snapshot():
    session = boto3.Session()  # Create a new session
    rds_resource = AWSResourceFactory.create_resource('RDS', session)

    data = request.json
    db_instance_id = data.get('DBInstanceIdentifier')
    snapshot_identifier = data.get('SnapshotIdentifier')

    if not db_instance_id:
        return jsonify({'error': 'DBInstanceIdentifier is required'}), 400

    try:
        response = rds_resource.create_snapshot(db_instance_identifier=db_instance_id, snapshot_identifier=snapshot_identifier)
        return jsonify({'message': 'Snapshot created successfully!', 'snapshot': response}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/list_rds_snapshots', methods=['GET'])
def list_rds_snapshots():
    session = boto3.Session()  # Create a new session
    rds_resource = AWSResourceFactory.create_resource('RDS', session)

    db_instance_id = request.args.get('DBInstanceIdentifier')

    try:
        snapshots = rds_resource.list_snapshots(db_instance_identifier=db_instance_id)
        return jsonify({'snapshots': snapshots}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/list_iam_users', methods=['GET'])
def list_iam_users():
    # Create an IAM client
    iam_client = boto3.client('iam')

    # Initialize a paginator to handle large result sets
    paginator = iam_client.get_paginator('list_users')

    # Iterate through each page of users
    users = []
    for page in paginator.paginate():
        for user in page['Users']:
            users.append({
                'UserName': user['UserName'],
                'UserId': user['UserId'],
                'Arn': user['Arn'],
                'CreateDate': user['CreateDate'].strftime('%Y-%m-%d %H:%M:%S')
            })

    # Return the user information as JSON
    return jsonify(users), 200

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
