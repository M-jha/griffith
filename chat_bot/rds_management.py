import boto3

from Notifications import NotificatonV1

class RDSResource:
    """
    Class to manage RDS instances.
    """

    def __init__(self):
        """
        Initialize the RDS client using the provided session.

        Parameters:
            session (Session): A Boto3 session object.
        """
        self.client = boto3.client('rds')

    def list_instances(self):
        """
        List all RDS instances in the AWS account.

        Returns:
            list: A list of RDS instances.
        """
        response = self.client.describe_db_instances()
        instances = response['DBInstances']
        return instances

    def start_db_instance(self, db_instance_identifiers):
        """
        Start the specified RDS instances.

        Parameters:
            db_instance_identifiers (list): A list of RDS instance identifiers to start.
        """
        for db_instance_identifier in db_instance_identifiers:
            self.client.start_db_instance(DBInstanceIdentifier=db_instance_identifier)
            NotificatonV1.main(subject="Started RDS Instance",
                               body=f"The RDS instance with instance_id : {db_instance_identifier} is started")

    def stop_db_instance(self, db_instance_identifiers):
        """
        Stop the specified RDS instances.

        Parameters:
            db_instance_identifiers (list): A list of RDS instance identifiers to stop.
        """
        for db_instance_identifier in db_instance_identifiers:
            self.client.stop_db_instance(DBInstanceIdentifier=db_instance_identifier)
            NotificatonV1.main(subject="Stopped RDS Instance",
                               body=f"The RDS instance with instance_id : {db_instance_identifier} is stopped")

    def reboot_db_instance(self, db_instance_identifiers, status):
        """
        Restart RDS instances based on their current status.

        Parameters:
            db_instance_identifiers (list): A list of RDS instance identifiers to restart.
            status (str): The current status of the instances (for conditional restart).
        """

        restarted = False
        db_instance_identifier = None

        if status not in ('stopped', 'stopping'):
            self.stop_instances(db_instance_identifiers)
        if status == 'stopped':
            self.start_instances(db_instance_identifiers)
            restarted = True
            db_instance_identifier = db_instance_identifiers
        else:
            print("The instance is not stopped")

        if restarted and db_instance_identifier:
            NotificatonV1.main(subject="Restarted RDS Instance",
                               body=f"The RDS instance with instance_id : {db_instance_identifier} is restarted")

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

        NotificatonV1.main(subject="Created RDS Instance",
                           body=f"The RDS instance with instance_id : {response} is created")

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