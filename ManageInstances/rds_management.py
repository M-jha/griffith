import boto3
from datetime import datetime
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

    def create_instance(self, db_instance_identifier):
        """
        Create a new RDS instance with fixed parameters except for DBInstanceIdentifier.

        Parameters:
            db_instance_identifier (str): The unique identifier for the new RDS instance.

        Returns:
            dict: The response from AWS after creating the RDS instance.
        """

        db_instance_class = 'db.t3.micro'
        engine = 'mysql'
        allocated_storage = 20
        master_username = 'admin'
        master_user_password = 'adminpassword'
        backup_retention_period = 7
        port = 3306
        multi_az = False
        engine_version = '8.0'
        publicly_accessible = True

        # Create the RDS instance with the fixed parameters and the provided DBInstanceIdentifier
        response = self.client.create_db_instance(
            DBInstanceIdentifier=db_instance_identifier,
            DBInstanceClass=db_instance_class,
            Engine=engine,
            AllocatedStorage=allocated_storage,
            MasterUsername=master_username,
            MasterUserPassword=master_user_password,
            BackupRetentionPeriod=backup_retention_period,
            Port=port,
            MultiAZ=multi_az,
            EngineVersion=engine_version,
            PubliclyAccessible=publicly_accessible
        )

        # Notify about the instance creation
        NotificatonV1.main(subject="Created RDS Instance",
                           body=f"The RDS instance with instance_id: {response} is created")

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

        # Notify that the snapshot was created
        NotificatonV1.main(subject="RDS Snapshot Created",
                           body=f"The snapshot with ID: {snapshot_identifier} for instance {db_instance_identifier} has been created.")

        return response