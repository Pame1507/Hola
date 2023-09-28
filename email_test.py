#!/usr/bin/python3

# import libraries
import imaplib
import email
import re
import base64
import os


# mail config
email_address = "test_support_email@avery-design.com"
imap_server = "mail.avery-design.com" 
password = "xXwdamiInMn?"

# Connect to the IMAP server
imap = imaplib.IMAP4_SSL(imap_server)

# Login to the email account
imap.login(email_address, password)

# Select the inbox
imap.select("Inbox")

# Initialize a set to store processed email UIDs
emails_by_subject = {}

def save_to_txt(message, txt_filename):
    with open(txt_filename, 'w', encoding= 'utf-8') as txt_file:
        txt_file.write(f"From: {message.get('From')}\n")
        txt_file.write("Content:\n")

        for part in message.walk():
            if part.get_content_type() == "text/plain":
                txt_file.write(part.as_string())

# Search for emails based on criteria (e.g., CC address)
_, msgnums = imap.search(None, 'OR (TO "support_pci@avery-design.com") (CC "support_pci@avery-design.com") NOT (FROM "bugzilla-daemon@bugzilla.avery-design.com.tw")')  #Tambien puede ir en el to, pero si el from es de bugzilla omitir.


#_, msgnums = imap.search(None, 'OR (TO "support_pci@avery-design.com") (CC "support_pci@avery-design.com") NOT (FROM "bugzilla-daemon@bugzilla.avery-design.com.tw" OR FROM "*@siemens.com")')  #Tambien puede ir en el to, pero si el from es de bugzilla omitir.


for msgnum in msgnums[0].split():
    _, data = imap.fetch(msgnum, "(RFC822)")
    message = email.message_from_bytes(data[0][1])
    subject = message.get("Subject")
    
    # Remove "Re:" or "RE:" prefixes and any leading/trailing spaces
    cleaned_subject = re.sub(r'^\s*(?:Re:\s*|RE:\s*)', '', subject, flags=re.IGNORECASE).strip()

    # Get the UID of the email
    uid_response = imap.uid("FETCH", msgnum, "(UID)")
    uid = re.search(r'UID (\d+)', uid_response[1][0].decode()).group(1)
    
     # Store emails by cleaned subject
    if cleaned_subject in emails_by_subject:
        emails_by_subject[cleaned_subject] = (uid, message)
    else:
        emails_by_subject[cleaned_subject] = (uid, message)

    # Check if this email has already been processed
    for cleaned_subject, (uid, message) in emails_by_subject.items():   
        subject_filename = re.sub(r'\s', '_', cleaned_subject)
        bug_number_match = re.search(r'\[Bug (\d+)\]', cleaned_subject, re.IGNORECASE)

        if bug_number_match:
            bug_number = bug_number_match.group(1)
            txt_filename = f"BUG_{bug_number}.txt"
        else:
            subject_filename = re.sub(r'\s', '_', cleaned_subject)
            subject_filename = re.sub(r'[\\/:*?"<>|]', '', subject_filename)
            txt_filename = f"{subject_filename}.txt"

        save_to_txt(message, txt_filename)

# Define a function to check if a file's content has base64 encoding
def has_base64_encoding(file_path):
    with open(file_path, 'r', encoding='utf-8') as txt_file:
        content = txt_file.read()
        return 'Content-Transfer-Encoding: base64' in content

# Define a function to extract and decode base64 content from a file
def extract_base64_content(file_path):
    with open(file_path, 'r', encoding='utf-8') as txt_file:
        lines = txt_file.readlines()

        # Extract the first five lines
        first_five_lines = ''.join(lines[:5])

        # Skip the first five lines and join the rest of the lines
        content = ''.join(lines[5:])

        # Decode the base64 content
        decoded_content = base64.b64decode(content.encode()).decode('utf-8', errors='ignore')

        return decoded_content, first_five_lines

# Directory where your .txt files are stored
txt_files_directory = "/home/pamgui02/Downloads"

# Initialize the poni variable
poni = None
first_five_lines = None

# Loop through all the .txt files in the directory
for filename in os.listdir(txt_files_directory):
    if filename.endswith(".txt"):
        file_path = os.path.join(txt_files_directory, filename)
        if has_base64_encoding(file_path):
            extracted_content, first_five_lines = extract_base64_content(file_path)
            # Store the content in the poni variable
            poni = extracted_content
            print(f"File '{filename}' has Content-Transfer-Encoding: base64")

            # Replace the file's content with poni
            with open(file_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(first_five_lines)
                txt_file.write(poni)

# Close connection to server
imap.close()
imap.logout()
