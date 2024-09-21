import boto3
import time
from datetime import datetime, time as dt_time
# import holidays  # You can use the 'holidays' package to check for public holidays
from abc import ABC, abstractmethod

class AWSResource(ABC):

    @abstractmethod
    def list_instances(self):
        pass

    @abstractmethod
    def start_instances(self, instance_ids):
        pass

    @abstractmethod
    def stop_instances(self, instance_ids):
        pass

    @abstractmethod
    def restart_instances(self, instance_ids, status):
        pass

    @abstractmethod
    def create_instance(self, **kwargs):
        pass

    @abstractmethod
    def get_instance_status(self, db_instance_identifier):
        pass


class EC2Resource(AWSResource):

    def __init__(self, session):
        self.client = session.client('ec2')

    def list_instances(self):
        response = self.client.describe_instances()
        instances = [instance for reservation in response['Reservations'] for instance in reservation['Instances']]
        return instances

    def start_instances(self, instance_ids):
        self.client.start_instances(InstanceIds=instance_ids)

    def stop_instances(self, instance_ids):
        self.client.stop_instances(InstanceIds=instance_ids)

    def restart_instances(self, instance_ids, status):
        self.stop_instances(instance_ids)
        self.start_instances(instance_ids)

    def create_instance(self, **kwargs):
        response = self.client.run_instances(
            ImageId=kwargs.get('ImageId', 'ami-0c55b159cbfafe1f0'),
            InstanceType=kwargs.get('InstanceType', 't2.micro'),
            MinCount=1,
            MaxCount=1,
            KeyName=kwargs.get('KeyName'),
            SecurityGroupIds=kwargs.get('SecurityGroupIds'),
            SubnetId=kwargs.get('SubnetId'),
        )
        instance_id = response['Instances'][0]['InstanceId']
        print(f"EC2 instance created with ID: {instance_id}")
        return instance_id

    def get_instance_status(self, instance_id):
        response = self.client.describe_instance_status(InstanceIds=[instance_id])
        if response['InstanceStatuses']:
            return response['InstanceStatuses'][0]['InstanceState']['Name']
        else:
            return 'Instance status not available'


class AWSResourceFactory:

    @staticmethod
    def create_resource(resource_type, session):
        if resource_type == 'EC2':
            return EC2Resource(session)
        else:
            raise ValueError(f"Resource type '{resource_type}' is not supported.")


def is_weekend():
    today = datetime.now().weekday()
    return today >= 5  # 5 is Saturday, 6 is Sunday

def is_night_time():
    current_time = datetime.now().time()
    night_start = dt_time(22, 0)  # 10 PM
    morning_end = dt_time(8, 0)  # 8 AM
    return current_time >= night_start or current_time <= morning_end

# def is_public_holiday():
#     us_holidays = holidays.US()  # Use holidays package to get public holidays for a country (US in this case)
#     today = datetime.now().date()
#     return today in us_holidays

def is_custom_time_range(start_time, end_time):
    current_time = datetime.now().time()
    return start_time <= current_time <= end_time

def should_stop_instance():
    # Check if any condition is met to stop the instance
    return is_weekend() or is_night_time() or is_custom_time_range(dt_time(12, 0), dt_time(13, 0))

def main():
    session = boto3.Session()

    ec2_resource = AWSResourceFactory.create_resource('EC2', session)
    instances = ec2_resource.list_instances()

    instance_ids = [instance['InstanceId'] for instance in instances]

    if not instance_ids:
        print("No instances found.")
        return

    for instance in instances:
        instance_id = instance['InstanceId']
        instance_status = ec2_resource.get_instance_status(instance_id)

        # If any condition is met and instance is running, stop it
        if should_stop_instance():
            if instance_status == 'running':
                ec2_resource.stop_instances([instance_id])
                print(f"Stopped instance: {instance_id}")

        # If none of the conditions are met and instance is stopped, start it
        else:
            if instance_status == 'stopped':
                ec2_resource.start_instances([instance_id])
                print(f"Started instance: {instance_id}")

if __name__ == "__main__":
    main()
