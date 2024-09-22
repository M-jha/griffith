import boto3
from flask import Flask, request, jsonify
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from collections import defaultdict


class AnalyseResource:
    """
    Automate the process to analyse resources.
    """

    # Function to get CPU usage for a specific EC2 instance and calculate daily averages
    def get_cpu_utilization(self, instance_id, start_time, end_time):
        # Initialize CloudWatch client
        cloudwatch_client = boto3.client('cloudwatch', region_name='us-west-1')
        metric = 'CPUUtilization'
        statistics = ['Average']
        period = 300  # 5 minutes
        # Fetch CPU utilization data from CloudWatch
        response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric,
            Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=statistics
        )
        # Dictionary to store CPU utilization grouped by day
        daily_data = defaultdict(list)
        # Group data by day
        for datapoint in response['Datapoints']:
            date_str = datapoint['Timestamp'].strftime('%Y-%m-%d')  # Extract the date (YYYY-MM-DD)
            daily_data[date_str].append(datapoint['Average'])
        # Calculate the average CPU utilization for each day
        averaged_cpu_data = []
        for date_str, cpu_values in daily_data.items():
            daily_average = sum(cpu_values) / len(cpu_values)  # Calculate daily average
            averaged_cpu_data.append({
                'date': date_str,
                'cpu_average': round(daily_average, 2)  # Round to two decimal places
            })
        return averaged_cpu_data

    def get_cpu_data(self, instance_id):
        """
        Analyse CPU utilization of the provided instance

        Parameters:
            instance_id (str): Id of RDS instance identifiers to analyse.
        """

        # Validate input parameters
        if not instance_id:
            return jsonify({'error': 'Missing required parameter: instance_id'}), 400

        # Set static start_time and end_time to the last 3 days
        end_time = datetime.utcnow()  # current time (UTC)
        start_time = end_time - timedelta(days=3)  # 3 days ago

        # Fetch the CPU utilization data
        cpu_data = self.get_cpu_utilization(instance_id, start_time, end_time)

        # Handle if no data is returned
        if not cpu_data:
            return jsonify({'error': 'No data available for the specified instance and time range'}), 404

        # Return the data as JSON
        return cpu_data

def main():
    """
    Main function to demonstrate the use of EC2Resource and RDSResource.
    """
    data = AnalyseResource().get_cpu_data('i-06c01fb386d7da475')

    print(data)

if __name__ == "__main__":
    main()