import boto3
import json
from botocore.exceptions import ClientError


class IAMPolicyAutomation:
    """
    A class to automate IAM-related tasks such as creating users,
    managing policies, and attaching policies to users.
    """

    def __init__(self):
        """
        Initialize the IAM client using AWS credentials from environment variables
        or AWS configuration files.
        """
        self.iam_client = boto3.client('iam')

    def list_iam_roles(self):
        """
        List all IAM roles in the AWS account.

        Returns:
            list: A list of IAM roles.
        """
        try:
            response = self.iam_client.list_roles()
            roles = response['Roles']
            print("IAM Roles in the account:")
            for role in roles:
                print(f"Role Name: {role['RoleName']}")
            return roles
        except ClientError as e:
            print(f"Error listing IAM roles: {e}")
            return None

    def get_attached_policies_for_user(self, user_name):
        """
        Get the managed policies attached to a specific IAM user.

        Parameters:
            user_name (str): The name of the IAM user.

        Returns:
            list: A list of attached policies.
        """
        try:
            response = self.iam_client.list_attached_user_policies(UserName=user_name)
            policies = response['AttachedPolicies']
            print(f"Managed policies attached to user {user_name}:")
            for policy in policies:
                print(f"Policy Name: {policy['PolicyName']}, ARN: {policy['PolicyArn']}")
            return policies
        except ClientError as e:
            print(f"Error fetching managed policies for user {user_name}: {e}")
            return None

    def get_inline_policies_for_user(self, user_name):
        """
        Get the inline policies for a specific IAM user.

        Parameters:
            user_name (str): The name of the IAM user.

        Returns:
            list: A list of inline policy names.
        """
        try:
            response = self.iam_client.list_user_policies(UserName=user_name)
            inline_policies = response['PolicyNames']
            print(f"Inline policies attached to user {user_name}:")
            for policy_name in inline_policies:
                print(f"Inline Policy Name: {policy_name}")
            return inline_policies
        except ClientError as e:
            print(f"Error fetching inline policies for user {user_name}: {e}")
            return None

    def get_all_user_policies(self, user_name):
        """
        Fetch all policies attached to a user (both managed and inline).

        Parameters:
            user_name (str): The name of the IAM user.

        Returns:
            dict: A dictionary containing managed and inline policies.
        """
        managed_policies = self.get_attached_policies_for_user(user_name)
        inline_policies = self.get_inline_policies_for_user(user_name)

        return {
            "managed_policies": managed_policies,
            "inline_policies": inline_policies
        }

    def create_policy_from_document(self, policy_name, policy_document):
        """
        Create a new IAM policy from the provided policy document.

        Parameters:
            policy_name (str): The name for the policy being created.
            policy_document (str): The policy document in JSON string format.

        Returns:
            dict: The response from AWS if the policy is created successfully.
        """
        try:
            # Validate the policy document first
            if not self.validate_policy(policy_document):
                print("Invalid policy document format.")
                return None

            # Create the policy
            response = self.iam_client.create_policy(
                PolicyName=policy_name,
                PolicyDocument=policy_document
            )
            print(f"Policy '{policy_name}' created successfully.")
            return response
        except ClientError as e:
            print(f"Error creating policy: {e}")
            return None

    def validate_policy(self, policy_document):
        """
        Perform basic validation on the policy document.

        Parameters:
            policy_document (str): The policy document in JSON string format.

        Returns:
            bool: True if valid, False otherwise.
        """
        try:
            policy_dict = json.loads(policy_document)
            if "Version" not in policy_dict or not policy_dict.get("Statement"):
                return False
            return True
        except json.JSONDecodeError:
            return False

    def update_policy(self, policy_arn, new_policy_document):
        """
        Update an existing IAM policy.

        Parameters:
            policy_arn (str): The ARN of the policy to update.
            new_policy_document (str): The new policy document in JSON string format.

        Returns:
            dict: The response from AWS if the policy is updated successfully.
        """
        try:
            response = self.iam_client.create_policy_version(
                PolicyArn=policy_arn,
                PolicyDocument=new_policy_document,
                SetAsDefault=True
            )
            print(f"Policy '{policy_arn}' updated successfully.")
            return response
        except ClientError as e:
            print(f"Error updating policy: {e}")
            return None

    def create_user(self, user_name):
        """
        Create a new IAM user.

        Parameters:
            user_name (str): The name of the user to create.

        Returns:
            dict: The response from AWS if the user is created successfully.
        """
        try:
            response = self.iam_client.create_user(UserName=user_name)
            print(f"User '{user_name}' created successfully.")
            return response
        except ClientError as e:
            print(f"Error creating user '{user_name}': {e}")
            return None

    def attach_policy_to_user(self, policy_arn, user_name):
        """
        Attach an IAM policy to a user.

        Parameters:
            policy_arn (str): The ARN of the policy to attach.
            user_name (str): The name of the user.

        Returns:
            dict: The response from AWS if the policy is attached successfully.
        """
        try:
            response = self.iam_client.attach_user_policy(
                PolicyArn=policy_arn,
                UserName=user_name
            )
            print(f"Policy '{policy_arn}' attached to user '{user_name}'.")
            return response
        except ClientError as e:
            print(f"Error attaching policy to user: {e}")
            return None

    def user_exists(self, user_name):
        """
        Check if the specified IAM user exists.

        Parameters:
            user_name (str): The name of the user.

        Returns:
            bool: True if the user exists, False otherwise.
        """
        try:
            self.iam_client.get_user(UserName=user_name)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                return False
            else:
                print(f"Error checking user existence: {e}")
                return None

    def delete_user(self, user_name):
        """
        Delete the specified IAM user if they exist.

        Parameters:
            user_name (str): The name of the user to delete.
        """
        if self.user_exists(user_name):
            try:
                # Detach managed policies
                managed_policies = self.get_attached_policies_for_user(user_name)
                if managed_policies:
                    for policy in managed_policies:
                        self.iam_client.detach_user_policy(
                            UserName=user_name,
                            PolicyArn=policy['PolicyArn']
                        )

                # Delete inline policies
                inline_policies = self.get_inline_policies_for_user(user_name)
                if inline_policies:
                    for policy_name in inline_policies:
                        self.iam_client.delete_user_policy(
                            UserName=user_name,
                            PolicyName=policy_name
                        )

                # Delete the user
                self.iam_client.delete_user(UserName=user_name)
                print(f"User '{user_name}' deleted successfully.")
            except ClientError as e:
                print(f"Error deleting user '{user_name}': {e}")
        else:
            print(f"User '{user_name}' does not exist.")

    def delete_policy(self, policy_name):
        """
        Delete a managed IAM policy by its name.

        Parameters:
            policy_name (str): The name of the policy to delete.
        """
        try:
            # Fetch the policy ARN by name
            paginator = self.iam_client.get_paginator('list_policies')
            for response in paginator.paginate(Scope='All'):
                for policy in response['Policies']:
                    if policy['PolicyName'] == policy_name:
                        policy_arn = policy['Arn']
                        # Delete all non-default policy versions
                        versions = self.iam_client.list_policy_versions(PolicyArn=policy_arn)
                        for version in versions['Versions']:
                            if not version['IsDefaultVersion']:
                                self.iam_client.delete_policy_version(
                                    PolicyArn=policy_arn,
                                    VersionId=version['VersionId']
                                )
                        # Delete the policy
                        self.iam_client.delete_policy(PolicyArn=policy_arn)
                        print(f"Policy '{policy_name}' deleted successfully.")
                        return
            print(f"Policy '{policy_name}' does not exist.")
        except ClientError as e:
            print(f"Error deleting policy '{policy_name}': {e}")

# Main test function to validate user and policy creation
if __name__ == "__main__":
    # Initialize the IAMPolicyAutomation class
    iam_automation = IAMPolicyAutomation()

    # Example usage
    # Step 1: Create a new user
    user_name = "test_de"
    iam_automation.create_user(user_name)

    # Step 2: Define a policy document for the data engineer
    policy_document = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:DescribeInstances",
                    "ec2:StartInstances",
                    "ec2:StopInstances",
                    "s3:ListBucket",
                    "s3:GetObject",
                    "s3:PutObject"
                ],
                "Resource": [
                    "*"  # Note: Using wildcard for demonstration purposes
                ]
            }
        ]
    })

    # Step 3: Validate the policy document
    is_valid = iam_automation.validate_policy(policy_document)
    if is_valid:
        print("Policy document is valid.")
        # Step 4: Create the policy using the defined document
        policy_name = "DataEngineerPolicy"
        policy_response = iam_automation.create_policy_from_document(policy_name, policy_document)

        # Step 5: Attach the policy to the newly created user
        if policy_response:
            policy_arn = policy_response['Policy']['Arn']
            iam_automation.attach_policy_to_user(policy_arn, user_name)

        # Step 6: Verify the policies attached to the user
        all_user_policies = iam_automation.get_all_user_policies(user_name)
        print("User policies:", all_user_policies)

        # Step 7: Update policy (for testing purposes, we'll change the actions)
        new_policy_document = json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "ec2:DescribeInstances",
                        "s3:ListBucket"
                    ],
                    "Resource": [
                        "*"
                    ]
                }
            ]
        })

        update_response = iam_automation.update_policy(policy_arn, new_policy_document)

        # Step 8: Verify the updated policy
        updated_user_policies = iam_automation.get_all_user_policies(user_name)
        print("Updated user policies:", updated_user_policies)
    else:
        print("Policy document is invalid.")

    # Uncomment the following lines to test deletion functions
    # # Step 9: Delete the user
    # iam_automation.delete_user(user_name)

    # # Step 10: Delete the policy
    # iam_automation.delete_policy(policy_name)

