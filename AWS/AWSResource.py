import boto3
import time
from datetime import datetime
from abc import ABC, abstractmethod


class AWSResource(ABC):
    """
    Abstract base class defining the structure for AWS resource management.
    """

    @abstractmethod
    def list_instances(self):
        """
        List all instances of the resource.
        """
        pass

    @abstractmethod
    def start_instances(self, instance_ids):
        """
        Start the specified instances.

        Parameters:
            instance_ids (list): A list of instance IDs to start.
        """
        pass

    @abstractmethod
    def stop_instances(self, instance_ids):
        """
        Stop the specified instances.

        Parameters:
            instance_ids (list): A list of instance IDs to stop.
        """
        pass

    @abstractmethod
    def restart_instances(self, instance_ids, status):
        """
        Restart instances by stopping and then starting them.

        Parameters:
            instance_ids (list): A list of instance IDs to restart.
            status (str): The current status of the instances (for conditional restart).
        """
        pass

    @abstractmethod
    def create_instance(self, **kwargs):
        """
        Create a new instance with the provided parameters.

        Parameters:
            **kwargs: Keyword arguments for instance creation parameters.
        """
        pass

    @abstractmethod
    def get_instance_status(self, db_instance_identifier):
        """
        Get the status of a specific instance.

        Parameters:
            db_instance_identifier (str): The identifier of the instance.
        """
        pass

    @abstractmethod
    def create_snapshot(self, db_instance_identifier):
        """
        Get the status of a specific instance.

        Parameters:
            db_instance_identifier (str): The identifier of the instance.
        """
        pass

    @abstractmethod
    def list_snapshots(self, db_instance_identifier):
        """
        Get the status of a specific instance.

        Parameters:
            db_instance_identifier (str): The identifier of the instance.
        """
        pass


class EC2Resource(AWSResource):
    """
    Class to manage EC2 instances.
    """

    def __init__(self, session):
        """
        Initialize the EC2 client using the provided session.

        Parameters:
            session (Session): A Boto3 session object.
        """
        self.client = session.client('ec2')

    def list_instances(self):
        """
        List all EC2 instances in the AWS account.

        Returns:
            list: A list of EC2 instances.
        """
        response = self.client.describe_instances()
        instances = [instance for reservation in response['Reservations'] for instance in reservation['Instances']]
        return instances

    def start_instances(self, instance_ids):
        """
        Start the specified EC2 instances.

        Parameters:
            instance_ids (list): A list of EC2 instance IDs to start.
        """
        self.client.start_instances(InstanceIds=instance_ids)

    def stop_instances(self, instance_ids):
        """
        Stop the specified EC2 instances.

        Parameters:
            instance_ids (list): A list of EC2 instance IDs to stop.
        """
        self.client.stop_instances(InstanceIds=instance_ids)

    def restart_instances(self, instance_ids, status):
        """
        Restart EC2 instances by stopping and then starting them.

        Parameters:
            instance_ids (list): A list of EC2 instance IDs to restart.
            status (str): The current status of the instances (for conditional restart).
        """
        self.stop_instances(instance_ids)
        self.start_instances(instance_ids)

    def create_instance(self, **kwargs):
        """
        Create a new EC2 instance with the provided parameters.

        Parameters:
            **kwargs: Keyword arguments for instance creation (e.g., ImageId, InstanceType).

        Returns:
            str: The ID of the newly created EC2 instance.
        """
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
        """
        Get the status of a specific EC2 instance.

        Parameters:
            instance_id (str): The ID of the EC2 instance.

        Returns:
            str: The current status of the instance.
        """
        response = self.client.describe_instance_status(InstanceIds=[instance_id])
        if response['InstanceStatuses']:
            return response['InstanceStatuses'][0]['InstanceState']['Name']
        else:
            return 'Instance status not available'

    def create_snapshot(self, db_instance_identifier, snapshot_identifier=None):
        pass

    def list_snapshots(self, db_instance_identifier=None):
        pass


class RDSResource(AWSResource):
    """
    Class to manage RDS instances.
    """

    def __init__(self, session):
        """
        Initialize the RDS client using the provided session.

        Parameters:
            session (Session): A Boto3 session object.
        """
        self.client = session.client('rds')

    def list_instances(self):
        """
        List all RDS instances in the AWS account.

        Returns:
            list: A list of RDS instances.
        """
        response = self.client.describe_db_instances()
        instances = response['DBInstances']
        return instances

    def start_instances(self, db_instance_identifiers):
        """
        Start the specified RDS instances.

        Parameters:
            db_instance_identifiers (list): A list of RDS instance identifiers to start.
        """
        for db_instance_identifier in db_instance_identifiers:
            self.client.start_db_instance(DBInstanceIdentifier=db_instance_identifier)

    def stop_instances(self, db_instance_identifiers):
        """
        Stop the specified RDS instances.

        Parameters:
            db_instance_identifiers (list): A list of RDS instance identifiers to stop.
        """
        for db_instance_identifier in db_instance_identifiers:
            self.client.stop_db_instance(DBInstanceIdentifier=db_instance_identifier)

    def restart_instances(self, db_instance_identifiers, status):
        """
        Restart RDS instances based on their current status.

        Parameters:
            db_instance_identifiers (list): A list of RDS instance identifiers to restart.
            status (str): The current status of the instances (for conditional restart).
        """
        if status not in ('stopped', 'stopping'):
            self.stop_instances(db_instance_identifiers)
        if status == 'stopped':
            self.start_instances(db_instance_identifiers)
        else:
            print("The instance is not stopped")

    def create_instance(self, **kwargs):
        """
        Create a new RDS instance with the provided parameters.

        Parameters:
            **kwargs: Keyword arguments for instance creation (e.g., DBInstanceIdentifier, DBInstanceClass, Engine).

        Returns:
            dict: The response from AWS after creating the RDS instance.
        """
        required_params = ['DBInstanceIdentifier', 'DBInstanceClass', 'Engine']
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"Missing required parameter: {param}")

        response = self.client.create_db_instance(
            DBInstanceIdentifier=kwargs['DBInstanceIdentifier'],
            DBInstanceClass=kwargs['DBInstanceClass'],
            Engine=kwargs['Engine'],
            AllocatedStorage=kwargs.get('AllocatedStorage', 20),
            MasterUsername=kwargs.get('MasterUsername', 'admin'),
            MasterUserPassword=kwargs.get('MasterUserPassword', 'password123'),
            BackupRetentionPeriod=kwargs.get('BackupRetentionPeriod', 7),
            Port=kwargs.get('Port', 3306),
            MultiAZ=kwargs.get('MultiAZ', False),
            EngineVersion=kwargs.get('EngineVersion', '8.0'),
            PubliclyAccessible=kwargs.get('PubliclyAccessible', True)
        )
        return response

    def get_instance_status(self, db_instance_identifier):
        """
        Get the status of a specific RDS instance.

        Parameters:
            db_instance_identifier (str): The identifier of the RDS instance.

        Returns:
            str: The current status of the RDS instance.
        """
        response = self.client.describe_db_instances(DBInstanceIdentifier=db_instance_identifier)
        status = response['DBInstances'][0]['DBInstanceStatus']
        return status

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
    """
    Factory class for creating AWS resource objects (EC2, RDS).
    """

    @staticmethod
    def create_resource(resource_type, session):
        """
        Create an AWS resource object based on the resource type.

        Parameters:
            resource_type (str): The type of AWS resource ('EC2' or 'RDS').
            session (Session): A Boto3 session object.

        Returns:
            AWSResource: An instance of EC2Resource or RDSResource, depending on the resource type.

        Raises:
            ValueError: If the resource type is not supported.
        """
        if resource_type == 'EC2':
            return EC2Resource(session)
        elif resource_type == 'RDS':
            return RDSResource(session)
        else:
            raise ValueError(f"Resource type '{resource_type}' is not supported.")


def main():
    """
    Main function to demonstrate the use of EC2Resource and RDSResource.
    """
    session = boto3.Session()

    # Example usage for RDS
    rds_resource = AWSResourceFactory.create_resource('RDS', session)
    ec2_resource = AWSResourceFactory.create_resource('EC2', session)

    rds_instances = rds_resource.list_instances()

    # start_rds_instances = rds_resource.start_instances(['mydbinstance'])

    snapshot = rds_resource.create_snapshot('mydbinstance')

    list_snapshot = rds_resource.list_snapshots()

    rds_instances = rds_resource.list_instances()



    # # Create RDS instance
    # rds_response = rds_resource.create_instance(
    #     DBInstanceIdentifier='mydbinstance2',
    #     DBInstanceClass='db.t3.micro',
    #     Engine='mysql',
    #     AllocatedStorage=20,
    #     MasterUsername='admin',
    #     MasterUserPassword='adminpassword'
    # )
    # print(f"RDS Instance Creation Response: {rds_response}")
    #
    # # List RDS instances
    # rds_instances = rds_resource.list_instances()
    # print("\nRDS Instances:")
    # for instance in rds_instances:
    #     print(f"DB Instance Identifier: {instance['DBInstanceIdentifier']}")
    #
    # # Get the status of a specific RDS instance
    # instance_status = rds_resource.get_instance_status('mydbinstance')
    # print(f"\nRDS Instance Status: {instance_status}")




if __name__ == "__main__":
    main()
