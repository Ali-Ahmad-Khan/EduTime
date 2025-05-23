import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Email configuration
ADMIN_EMAIL = "aak.aliahmadk@gmail.com"
EMAIL_PASSWORD = "ckjqqjcpbuzzxjhk"  # In production, use environment variables
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_welcome_email(recipient_email, role):
    """Send a welcome email to the user"""
    try:
        msg = MIMEMultipart()
        msg['From'] = ADMIN_EMAIL
        msg['To'] = recipient_email
        msg['Subject'] = "Welcome to EduTime!"
        
        # Email body
        if role == 'STUDENT':
            body = f"""
            <html>
              <body>
                <h2>Welcome to EduTime!</h2>
                <p>Thank you for registering as a student. Your account has been created successfully.</p>
                <p>You can now log in to your account at <a href="http://localhost:5000/login">EduTime</a> with your email and password.</p>
                <p>If you did not register for an EduTime account, please ignore this email.</p>
              </body>
            </html>
            """
        else:  # INSTRUCTOR
            body = f"""
            <html>
              <body>
                <h2>Welcome to EduTime!</h2>
                <p>You have been registered as an instructor. You can now log in to EduTime using your email and set password.</p>
                <p>Access your account at: <a href="http://localhost:5000/login">EduTime</a></p>
                <p>If you were not expecting this email, please contact the administrator.</p>
              </body>
            </html>
            """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(ADMIN_EMAIL, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False 