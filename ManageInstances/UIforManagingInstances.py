import tkinter as tk
from tkinter import messagebox
import boto3
import pandas as pd
from datetime import datetime
import os

class EC2ManagerUI:
    def __init__(self, master):
        self.master = master
        self.master.title("EC2 Instance Stop Conditions")
        self.master.geometry("500x500")  # Set window size

        # AWS Session setup
        self.session = boto3.Session(
            aws_access_key_id='AKIAVVPPFW4MGPYYQYPU',
            aws_secret_access_key='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',
            region_name='us-west-2'
        )
        self.ec2_client = self.session.client('ec2')

        # Headings
        heading_label = tk.Label(master, text="EC2 Instance Manager", font=("Helvetica", 16, "bold"))
        heading_label.grid(row=0, column=0, columnspan=2, pady=10)

        instance_list_heading = tk.Label(master, text="List of Instances", font=("Helvetica", 12, "bold"))
        instance_list_heading.grid(row=1, column=0, columnspan=2, pady=(10, 5))

        # Frame for the list of instances
        self.frame = tk.Frame(master)
        self.frame.grid(row=2, column=0, columnspan=2, padx=20)

        # Load EC2 Instances
        self.load_ec2_instances()

        # Condition section heading
        condition_heading = tk.Label(master, text="Available Conditions to Stop Instances", font=("Helvetica", 12, "bold"))
        condition_heading.grid(row=3, column=0, columnspan=2, pady=(15, 5))

        # Checkboxes for stop conditions
        self.weekend_var = tk.IntVar()
        tk.Checkbutton(master, text="Stop on Weekend (Saturday/Sunday)", variable=self.weekend_var).grid(row=4, column=0, sticky=tk.W, padx=20)

        self.night_var = tk.IntVar()
        tk.Checkbutton(master, text="Stop During Night Time (10 PM to 8 AM)", variable=self.night_var).grid(row=5, column=0, sticky=tk.W, padx=20)

        # Custom time range
        tk.Label(master, text="Custom Start Time (HH:MM):").grid(row=6, column=0, sticky=tk.W, padx=20)
        self.custom_start_time_entry = tk.Entry(master)
        self.custom_start_time_entry.grid(row=6, column=1, padx=20, pady=5)

        tk.Label(master, text="Custom End Time (HH:MM):").grid(row=7, column=0, sticky=tk.W, padx=20)
        self.custom_end_time_entry = tk.Entry(master)
        self.custom_end_time_entry.grid(row=7, column=1, padx=20, pady=5)

        # Save button
        save_button = tk.Button(master, text="Save Conditions", command=self.save_to_csv, bg="#4CAF50", fg="white", font=("Helvetica", 10, "bold"))
        save_button.grid(row=8, column=0, columnspan=2, pady=20)

    def load_ec2_instances(self):
        """Fetch the list of EC2 instances and display checkboxes for each."""
        self.instances = []
        response = self.ec2_client.describe_instances()
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                state = instance['State']['Name']
                instance_info = f"Instance ID: {instance_id} | Status: {state}"

                # Store instance details
                var = tk.IntVar()
                chk = tk.Checkbutton(self.frame, text=instance_info, variable=var, anchor="w", padx=10)
                chk.pack(anchor=tk.W, pady=2)  # Vertical padding for better readability

                # Save reference to checkbox variable for later use
                instance_data = {
                    'instance_id': instance_id,
                    'var': var
                }
                self.instances.append(instance_data)

    def save_to_csv(self):
        selected_instances = [i['instance_id'] for i in self.instances if i['var'].get() == 1]
        if not selected_instances:
            messagebox.showerror("Error", "No instances selected!")
            return

        weekend = self.weekend_var.get()
        night_time = self.night_var.get()
        custom_start = self.custom_start_time_entry.get()
        custom_end = self.custom_end_time_entry.get()

        # Create or append to CSV
        file_exists = os.path.isfile('ec2_conditions.csv')
        df = pd.DataFrame([{
            'InstanceID': instance_id,
            'Weekend': weekend,
            'NightTime': night_time,
            'CustomStartTime': custom_start,
            'CustomEndTime': custom_end
        } for instance_id in selected_instances])

        if not file_exists:
            df.to_csv('ec2_conditions.csv', index=False)
        else:
            df.to_csv('ec2_conditions.csv', mode='a', header=False, index=False)

        messagebox.showinfo("Success", "Details saved to CSV!")
        self.clear_fields()

    def clear_fields(self):
        # Clear the form inputs
        self.weekend_var.set(0)
        self.night_var.set(0)
        self.custom_start_time_entry.delete(0, tk.END)
        self.custom_end_time_entry.delete(0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = EC2ManagerUI(root)
    root.mainloop()
