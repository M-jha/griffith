# Cloud Resource Management Automation

This repository contains Python classes for automating the management of AWS resources, including EC2 instances, RDS instances, and IAM policies.

## Table of Contents

- [Classes and Tasks](#classes-and-tasks)
  - [IAMPolicyAutomation](#1-iampolicyautomation)
  - [EC2Resource](#2-ec2management)
  - [RDSResource](#3-rdsmanagement)
- [Usage Examples](#usage-examples)
- [Setup Instructions](#setup-instructions)
- [Notes](#notes)

## Classes and Tasks

### 1. IAMPolicyAutomation

**Purpose**: Automate IAM-related tasks such as creating users, managing policies, and attaching policies to users.

**Key Functions**:

- `create_user(user_name)`: Create a new IAM user.
- `delete_user(user_name)`: Delete an existing IAM user.
- `attach_policy_to_user(policy_arn, user_name)`: Attach an IAM policy to a user.
- `detach_policy_from_user(policy_arn, user_name)`: Detach an IAM policy from a user.
- `create_policy_from_document(policy_name, policy_document)`: Create a new IAM policy from a policy document.
- `update_policy(policy_arn, new_policy_document)`: Update an existing IAM policy.
- `list_iam_roles()`: List all IAM roles in the AWS account.
- `list_iam_users()`: List all IAM users in the AWS account.
- `get_all_user_policies(user_name)`: Get all policies attached to a user (both managed and inline).

### 2. EC2Resource

**Purpose**: Automate EC2 instance management tasks.

**Key Functions**:

- `start_instances(instance_ids)`: Start an EC2 instance.
- `stop_instances(instance_ids)`: Stop an EC2 instance.
- `reboot_instance(instance_ids,status)`: Reboot an EC2 instance.
- `list_instances_ec2()`: List all EC2 instances.
- `get_instance_status(instance_id)`: Get status of instance.
- `create_instance(kwargs)`: Create a new EC2 instance with the provided parameters.


### 3. RDSResource

**Purpose**: Automate RDS instance management tasks.

**Key Functions**:

- `start_db_instance(db_instance_identifiers)`: Start an RDS instance.
- `stop_db_instance(db_instance_identifiers)`: Stop an RDS instance.
- `reboot_db_instance(db_instance_identifiers, status)`: Reboot an RDS instance.
- `list_instances()`: List all RDS instances.
- `create_instance(kwargs)`: Create a new RDS instance with the provided parameters.
- `get_instance_status(db_instance_identifier)`: Get the status of a specific RDS instance.
- `create_snapshot(db_instance_identifier, snapshot_identifier=None)`: Create a snapshot of the specified RDS instance.

## Usage Examples

**Creating a New IAM User and Attaching Policies**:

```python
from iam_policy_automation import IAMPolicyAutomation

iam = IAMPolicyAutomation()

# Create a new IAM user
user_name = 'new_data_engineer'
iam.create_user(user_name)

# Define policies to attach
policies = [
    'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess',
    'arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess'
]

# Attach policies to the user
for policy_arn in policies:
    iam.attach_policy_to_user(policy_arn, user_name)
