import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

def send_email(subject, body):

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_name = "Griffith Notifications"
    sender_email = "h8917991@gmail.com"
    # sender_password = "Hackathon@2024"
    sender_password = "ajjw lqsc gpsi dtxe"

    recipients = [
        ("Murli", "murli@cipio.ai"),
        ("Dipshi", "dipshi@cipio.ai"),
        ("Manthan", "mjha@cipio.ai"),
        ("Sushmit", "sushmitsatish@gmail.com")
    ]

    # Set up the SMTP server
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()  # Enable security
    server.login(sender_email, sender_password)

    # Loop over each recipient and send the email
    for recipient_name, recipient_email in recipients:
        # Create the email
        message = MIMEMultipart()
        message['From'] = formataddr((sender_name, sender_email))  # Name and email for the sender
        message['To'] = formataddr((recipient_name, recipient_email))  # Name and email for the recipient
        message['Subject'] = subject

        # Add body to the email
        message.attach(MIMEText(body, 'plain'))

        # Send the email
        server.sendmail(sender_email, recipient_email, message.as_string())

    # Close the SMTP server connection
    server.quit()


if __name__ == "__main__":
    # Email configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_name = "Griffith Notifications"
    sender_email = "h8917991@gmail.com"
    # sender_password = "Hackathon@2024"
    sender_password = "ajjw lqsc gpsi dtxe"

    # List of recipients
    # recipients = ["murli@cipio.ai", "mjha@cipio.ai", "dipshi@cipio.ai", "sushmitsatish@gmail.com"]

    recipients = [
        ("Murli", "murli@cipio.ai"),
        ("Dipshi", "dipshi@cipio.ai"),
        ("Manthan", "mjha@cipio.ai"),
        ("Sushmit", "sushmitsatish@gmail.com")
    ]

    # Custom subject and body
    subject = "Your Custom Subject"
    body = "This is the body of your custom email."

    # Send the email to the list of recipients
    send_email(subject, body)