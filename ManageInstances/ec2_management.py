import boto3
from Notifications import NotificatonV1

class EC2Resource:
    """
    Class to manage EC2 instances.
    """

    def __init__(self):
        """
        Initialize the EC2 client using the provided session.

        Parameters:
            session (Session): A Boto3 session object.
        """
        self.client = boto3.client('ec2')

    def list_instances_ec2(self):
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
        NotificatonV1.main(subject="Start EC2 Instance",
                           body=f"The EC2 instance with instance_id : {instance_ids} is start")

    def stop_instances(self, instance_ids):
        """
        Stop the specified EC2 instances.

        Parameters:
            instance_ids (list): A list of EC2 instance IDs to stop.
        """
        self.client.stop_instances(InstanceIds=instance_ids)
        NotificatonV1.main(subject="Stop EC2 Instance",
                           body=f"The EC2 instance with instance_id : {instance_ids} is stop")

    def reboot_instance(self, instance_ids, status):
        """
        Restart EC2 instances by stopping and then starting them.

        Parameters:
            instance_ids (list): A list of EC2 instance IDs to restart.
            status (str): The current status of the instances (for conditional restart).
        """
        self.stop_instances(instance_ids)
        self.start_instances(instance_ids)
        NotificatonV1.main(subject="Restarted EC2 Instance",
                           body=f"The EC2 instance with instance_id : {instance_ids} is restarted")

    def create_instance(self, key_name):
        """
        Create a new EC2 instance with fixed parameters except for the key pair name.

        Parameters:
            key_name (str): The name of the key pair to use.

        Returns:
            str: The ID of the newly created EC2 instance.
        """

        image_id = 'ami-076e3756930a93fbb'
        instance_type = 't2.micro'
        security_group_ids = ['sg-7288db58']
        subnet_id = 'subnet-caa77ab2'

        # Create the EC2 instance with the fixed parameters and the provided key_name
        response = self.client.run_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            KeyName=key_name,
            SecurityGroupIds=security_group_ids,
            SubnetId=subnet_id,
        )

        # Get the instance ID of the newly created instance
        instance_id = response['Instances'][0]['InstanceId']
        print(f"EC2 instance created with ID: {instance_id}")

        # Notification for instance creation
        NotificatonV1.main(subject="Created EC2 Instance",
                           body=f"The EC2 instance with instance_id: {instance_id} is created")

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