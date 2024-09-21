import boto3
import time

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
        # EC2 create instance logic would go here (omitted for now)
        pass

    def get_instance_status(self, instance_id):
        # EC2 status check logic would go here (omitted for now)
        pass


class RDSResource(AWSResource):

    def __init__(self, session):
        self.client = session.client('rds')

    def list_instances(self):
        response = self.client.describe_db_instances()
        instances = response['DBInstances']
        return instances

    def start_instances(self, db_instance_identifiers):
        for db_instance_identifier in db_instance_identifiers:
            self.client.start_db_instance(DBInstanceIdentifier=db_instance_identifier)

    def stop_instances(self, db_instance_identifiers):
        for db_instance_identifier in db_instance_identifiers:
            self.client.stop_db_instance(DBInstanceIdentifier=db_instance_identifier)

    def restart_instances(self, db_instance_identifiers, status):
        if status not in ('stopped', 'stopping'):
            self.stop_instances(db_instance_identifiers)
        if status in ('stopped'):
            self.start_instances(db_instance_identifiers)
        else:
            print("The Instance is not stopped")

    def create_instance(self, **kwargs):
        # Ensure necessary parameters are provided
        required_params = ['DBInstanceIdentifier', 'DBInstanceClass', 'Engine']
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter: {param}")

        response = self.client.create_db_instance(
            DBInstanceIdentifier=kwargs['DBInstanceIdentifier'],
            DBInstanceClass=kwargs['DBInstanceClass'],
            Engine=kwargs['Engine'],
            AllocatedStorage=kwargs.get('AllocatedStorage', 20),  # default 20 GB
            MasterUsername=kwargs.get('MasterUsername', 'admin'),
            MasterUserPassword=kwargs.get('MasterUserPassword', 'password123'),
            BackupRetentionPeriod=kwargs.get('BackupRetentionPeriod', 7),  # default 7 days
            Port=kwargs.get('Port', 3306),  # default port for MySQL
            MultiAZ=kwargs.get('MultiAZ', False),  # default single AZ
            EngineVersion=kwargs.get('EngineVersion', '8.0'),  # default MySQL version
            PubliclyAccessible=kwargs.get('PubliclyAccessible', True)
        )
        return response

    def get_instance_status(self, db_instance_identifier):
        response = self.client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        status = response['DBInstances'][0]['DBInstanceStatus']
        return status


class AWSResourceFactory:

    @staticmethod
    def create_resource(resource_type, session):
        if resource_type == 'EC2':
            return EC2Resource(session)
        elif resource_type == 'RDS':
            return RDSResource(session)
        else:
            raise ValueError(f"Resource type '{resource_type}' is not supported.")


def main():
    session = boto3.Session()

    # Example usage
    rds_resource = AWSResourceFactory.create_resource('RDS', session)
    # # Create RDS instance
    # rds_response = rds_resource.create_instance(
    #     DBInstanceIdentifier='mydbinstance',
    #     DBInstanceClass='db.t3.micro',
    #     Engine='mysql',
    #     AllocatedStorage=20,
    #     MasterUsername='admin',
    #     MasterUserPassword='adminpassword'
    # )
    # print(f"RDS Instance Creation Response: {rds_response}")

    # List RDS instances
    rds_instances = rds_resource.list_instances()
    print("\nRDS Instances:")
    for instance in rds_instances:
        print(f"DB Instance Identifier: {instance['DBInstanceIdentifier']}")

    # Get the status of a specific RDS instance
    rds_status = rds_resource.get_instance_status('mydbinstance')
    print(f"\nStatus of RDS instance 'mydbinstance': {rds_status}")

    # Stop the RDS instance if not already stopping or stopped
    if rds_status not in ('stopped', 'stopping'):
        print("\nStopping RDS instance 'mydbinstance'...")
        rds_resource.stop_instances(['mydbinstance'])
    else:
        print(f"\nRDS instance 'mydbinstance' is already stopped/stopping (current status: {rds_status}).")

    # Wait for the instance to reach the 'stopped' state
    rds_status = rds_resource.get_instance_status('mydbinstance')
    while rds_status == 'stopping':
        print(f"Waiting for instance 'mydbinstance' to stop (current status: {rds_status})...")
        time.sleep(10)  # Sleep for 10 seconds before checking the status again
        rds_status = rds_resource.get_instance_status('mydbinstance')

    print(f"Status after stopping: {rds_status}")

    # Validation before restarting
    if rds_status == 'stopped':
        print("\nRDS instance 'mydbinstance' is stopped. Attempting to restart...")
        rds_resource.restart_instances(['mydbinstance'], rds_status)

        # Check the status after restarting
        rds_status = rds_resource.get_instance_status('mydbinstance')
        print(f"Status after restarting: {rds_status}")

        while rds_status == 'starting':
            print(f"Waiting for instance 'mydbinstance' to stop (current status: {rds_status})...")
            time.sleep(10)  # Sleep for 10 seconds before checking the status again
            rds_status = rds_resource.get_instance_status('mydbinstance')
            print(f"Status after restarting: {rds_status}")

    else:
        print(f"\nRDS instance 'mydbinstance' is not stopped (current status: {rds_status}). Cannot restart.")


if __name__ == "__main__":
    main()
