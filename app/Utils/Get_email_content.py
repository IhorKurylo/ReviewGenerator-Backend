import json
import re
import time
import requests
from app.Utils.Pinecone import train_txt
from bs4 import BeautifulSoup
from fastapi import Request
# Configure this.
FROM_EMAIL_ADDR = 'ihorkurylo5@zohomail.com'
TO_EMAIL_ADDR = 'andriilohvin@gmail.com'
REDIRECT_URL = 'http://95.164.44.248:5000/callback/'
CLIENT_ID = '1000.BWV591EOQJX8AUJS22NUGIJGIMXULO'
CLIENT_SECRET = '00bc90f92fe8ec91904acb23b285f0b7602a9893f8'
BASE_OAUTH_API_URL = 'https://accounts.zoho.com/'
BASE_API_URL = 'https://mail.zoho.com/api/'


previous_thread_Id = ""
emails_in_same_thread = []
metadata = ""

ZOHO_DATA = {
    "access_token": "",
    "refresh_token": "",
    "api_domain": "https://www.zohoapis.com",
    "token_type": "Bearer",
    "expires_in": 7200,
    "account_id": "",
    "folder_id": "",
}


def clean(txt: str):
    keep_characters = set(
        'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-@ ,\'"().!?\n\r%$#&^*+-~<>{}[]/|:;')
    new_text = ''.join(ch for ch in txt if ch in keep_characters)
    return new_text


def req_zoho():
    url = (
        "%soauth/v2/auth?"
        "scope=ZohoMail.accounts.READ,ZohoMail.messages.ALL,ZohoMail.folders.READ&"
        "client_id=%s&"
        "response_type=code&"
        "access_type=offline&"
        "redirect_uri=%s"
    ) % (BASE_OAUTH_API_URL, CLIENT_ID, REDIRECT_URL)
    print('CLICK THE LINK:')
    print(url)
    print('This only has to be done once.')
    return url


def get_access_token(request: Request, code):
    state = request.query_params.get('state')
    url = '%soauth/v2/token' % BASE_OAUTH_API_URL
    data = {
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URL,
        'scope': 'ZohoMail.accounts.READ,ZohoMail.messages.ALL,ZohoMail.folders.READ',
        'grant_type': 'authorization_code',
        'state': state
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    r = requests.post(url, data=data, headers=headers)
    data = json.loads(r.text)
    # print(data)
    ZOHO_DATA['access_token'] = data['access_token']


def get_account_id():
    url = BASE_API_URL + 'accounts'
    headers = {
        'Authorization': 'Zoho-oauthtoken ' + ZOHO_DATA['access_token']
    }
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    ZOHO_DATA['account_id'] = data['data'][0]['accountId']


# def send_mail(body, email_address):
#     url = BASE_API_URL + 'accounts/%s/messages'
#     url = url % ZOHO_DATA['account_id']
#     data = {
#         "fromAddress": FROM_EMAIL_ADDR,
#         "toAddress": email_address,
#         "ccAddress": "",
#         "bccAddress": "",
#         "subject": "Test E-Mail",
#         "content": body,
#         "askReceipt": "no"
#     }
#     headers = {
#         'Authorization': 'Zoho-oauthtoken ' + ZOHO_DATA['access_token']
#     }
#     r = requests.post(url, headers=headers, json=data)
#     print(r.text)

def get_mail_context(folder_id, message_id, from_address, thread_id):
    global previous_thread_Id, emails_in_same_thread, metadata
    url = (
        "%saccounts/%s/folders/%s/messages/%s/content?"
        "includeBlockContent=%s"
    ) % (BASE_API_URL, ZOHO_DATA['account_id'], folder_id, message_id, "false")

    headers = {
        'Authorization': 'Zoho-oauthtoken ' + ZOHO_DATA['access_token']
    }

    # print(url)
    # print(from_address, "    ", thread_id)
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)

    if thread_id == "-1" or thread_id != previous_thread_Id:
        # for email in emails_in_same_thread:
        #     train_txt(email, metadata)
        train_txt(metadata, metadata)
        # print(metadata, '\n--------------------\n')
        emails_in_same_thread = []
        metadata = ""
        previous_thread_Id = thread_id
    if 'content' in data['data']:
        emails = data['data']['content']
        soup = BeautifulSoup(emails, 'html.parser')
        soup_text = soup.get_text()
        soup_text = re.sub(r'\n{2,}', ' ', soup_text)
        soup_text = clean(soup_text)
        metadata += '\n' + soup_text
        # print(soup_text)
        # metadata += '\n' + soup.find('div').text()
        # emails_in_same_thread.append(soup.get_text())


def get_mail_folders():
    url = BASE_API_URL + 'accounts/%s/folders'
    url = url % ZOHO_DATA['account_id']
    headers = {
        'Authorization': 'Zoho-oauthtoken ' + ZOHO_DATA['access_token']
    }
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    ZOHO_DATA['folder_id'] = data['data'][0]['folderId']

count = 0

def get_mail_list(start, unit):
    global count
    url = BASE_API_URL + 'accounts/%s/messages/view'
    url = url % ZOHO_DATA['account_id']
    url = (
        "%s?"
        "folderId=%s&"
        "start=%s&"
        "limit=%s"
    ) % (url, ZOHO_DATA['folder_id'], start, unit)
    headers = {
        'Authorization': 'Zoho-oauthtoken ' + ZOHO_DATA['access_token']
    }

    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    # print(data)
    if len(data['data']) == 0:
        return False
    for message in data['data']:
        # print("count: ", count)
        # count += 1
        message_id = message['messageId']
        folder_id = message['folderId']
        from_address = message['fromAddress']
        thread_id = "-1"
        if 'threadId' in message:
            thread_id = message['threadId']
        get_mail_context(folder_id, message_id, from_address, thread_id)
    return True

# def refresh_auth():
#     # Update the access token every 50 minutes using the refresh token.
#     # The access token is valid for exactly 1 hour.
#     time.sleep(10)
#     while True:
#         url = (
#             '%soauth/v2/token?'
#             'refresh_token=%s&'
#             'client_id=%s&'
#             'client_secret=%s&'
#             'grant_type=refresh_token'
#         ) % (BASE_OAUTH_API_URL, ZOHO_DATA['refresh_token'], CLIENT_ID, CLIENT_SECRET)
#         r = requests.post(url)
#         data = json.loads(r.text)
#         if 'access_token' in data:
#             ZOHO_DATA['access_token'] = data['access_token']
#             print('refreshed', ZOHO_DATA)
#             time.sleep(3000)  # 50 minutes
#         else:
#             # Retry after 1 minute
#             time.sleep(60)


def start(clientId: str, clientSecret: str):
    global CLIENT_ID, CLIENT_SECRET
    if clientId != "":
        CLIENT_ID = clientId
    if clientSecret != "":
        CLIENT_SECRET = clientSecret
    print(CLIENT_ID)
    return req_zoho()
