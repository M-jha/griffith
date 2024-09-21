from setuptools import setup, find_packages

setup(
    name='cloud-resource-management',
    version='1.0.0',
    description='Automation tools for managing AWS resources like EC2, RDS, and IAM policies.',
    author='griffith',
    author_email='mjha@cipio.ai',
    packages=find_packages(),
    install_requires=[
        'boto3>=1.28.57',
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
)