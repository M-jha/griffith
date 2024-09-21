import boto3
import pandas as pd
from datetime import datetime, time as dt_time

# Skip is_public_holiday function and remove it from logic

def is_weekend():
    return datetime.now().weekday() >= 5  # 5 is Saturday, 6 is Sunday

def is_night_time():
    current_time = datetime.now().time()
    night_start = dt_time(22, 0)  # 10 PM
    morning_end = dt_time(8, 0)  # 8 AM
    return current_time >= night_start or current_time <= morning_end

def is_custom_time_range(start_time, end_time):
    current_time = datetime.now().time()
    return start_time <= current_time <= end_time

def should_stop_instance(row):
    if row['Weekend'] and is_weekend():
        return True
    if row['NightTime'] and is_night_time():
        return True
    if row['CustomStartTime'] and row['CustomEndTime']:
        custom_start = datetime.strptime(row['CustomStartTime'], '%H:%M').time()
        custom_end = datetime.strptime(row['CustomEndTime'], '%H:%M').time()
        if is_custom_time_range(custom_start, custom_end):
            return True
    return False

def manage_ec2_instances():
    # Read from CSV
    df = pd.read_csv('/home/murli/hackathon-2024/ManageInstances/ec2_conditions.csv')

    session = boto3.Session(
        aws_access_key_id='AKIAVVPPFW4MGPYYQYPU',
        aws_secret_access_key='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',
        region_name='us-west-2'
    )

    print(f"Running Job at {datetime.now().time()}")

    # ec2_client = session.client('ec2')
    #
    # for _, row in df.iterrows():
    #     instance_id = row['InstanceID']
    #     instance_id = instance_id.replace("'", "")
    #     instance_status = ec2_client.describe_instance_status(InstanceIds=[instance_id])
    #
    #     if instance_status['InstanceStatuses']:
    #         current_status = instance_status['InstanceStatuses'][0]['InstanceState']['Name']
    #
    #         if should_stop_instance(row):
    #             if current_status == 'running':
    #                 ec2_client.stop_instances(InstanceIds=[instance_id])
    #                 print(f"Stopped instance: {instance_id}")
    #         else:
    #             if current_status == 'stopped':
    #                 ec2_client.start_instances(InstanceIds=[instance_id])
    #                 print(f"Started instance: {instance_id}")

if __name__ == "__main__":
    manage_ec2_instances()
