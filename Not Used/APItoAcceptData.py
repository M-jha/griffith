from flask import Flask, request, jsonify
import csv
import os

app = Flask(__name__)

# CSV file path
CSV_FILE_PATH = '/home/murli/hackathon-2024/ManageInstances/ec2_conditions.csv'

# Ensure the CSV file exists with headers if it's not present
if not os.path.exists(CSV_FILE_PATH):
    with open(CSV_FILE_PATH, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['InstanceID', 'Weekend', 'NightTime', 'PublicHoliday', 'CustomStartTime', 'CustomEndTime'])


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


# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
