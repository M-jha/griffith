import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr


class EmailAutomation:
    """
    A class to automate sending emails to multiple recipients with default configuration.
    """

    def __init__(self,
                 smtp_server="smtp.gmail.com",
                 smtp_port=587,
                 sender_name="Griffith Notifications",
                 sender_email="h8917991@gmail.com",
                 sender_password="ajjw lqsc gpsi dtxe"):
        """
        Initialize the SMTP server details and sender information with default parameters.
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_name = sender_name
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.server = None
        self.receivers = [("Murli", "murli@cipio.ai"),
                        ("Dipshi", "dipshi@cipio.ai"),
                        ("Manthan", "mjha@cipio.ai"),
                        ("Sushmit", "sushmitsatish@gmail.com")]

    def connect_smtp_server(self):
        """
        Connect to the SMTP server and log in with sender credentials.
        """
        try:
            self.server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.server.starttls()
            self.server.login(self.sender_email, self.sender_password)
            print("Connected to SMTP server successfully.")
        except smtplib.SMTPException as e:
            print(f"Error connecting to SMTP server: {e}")

    def create_email(self, subject, body, recipient_name, recipient_email):
        """
        Create an email message object with the specified subject and body.

        Parameters:
            subject (str): The email subject.
            body (str): The email body content.
            recipient_name (str): The recipient's name.
            recipient_email (str): The recipient's email address.

        Returns:
            MIMEMultipart: The constructed email message object.
        """
        message = MIMEMultipart()
        message['From'] = formataddr((self.sender_name, self.sender_email))
        message['To'] = formataddr((recipient_name, recipient_email))
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        return message

    def send_email(self, subject, body):
        """
        Send the email to multiple recipients.

        Parameters:
            recipients (list): A list of tuples with recipient names and emails.
            subject (str): The email subject.
            body (str): The email body content.
        """
        if self.server is None:
            print("SMTP server not connected.")
            return

        for recipient_name, recipient_email in self.receivers:
            message = self.create_email(subject, body, recipient_name, recipient_email)
            try:
                self.server.sendmail(self.sender_email, recipient_email, message.as_string())
                print(f"Email sent to {recipient_name} ({recipient_email})")
            except smtplib.SMTPException as e:
                print(f"Failed to send email to {recipient_name}: {e}")

    def close_smtp_server(self):
        """
        Close the connection to the SMTP server.
        """
        if self.server:
            self.server.quit()
            print("SMTP server connection closed.")


def main(subject="Your Custom Subject", body="This is the body of your custom email."):
    """
    Main function to configure email settings and send an email.

    Default subject and body can be overridden.
    """
    # Default recipients list

    # Initialize the EmailAutomation class with default parameters
    email_automation = EmailAutomation()

    # Connect to the SMTP server
    email_automation.connect_smtp_server()

    # Send emails to the list of recipients
    email_automation.send_email(subject, body)

    # Close the SMTP server connection
    email_automation.close_smtp_server()


if __name__ == "__main__":
    main()
