import json
import time
import requests
from app.Utils.Pinecone import train_txt
from bs4 import BeautifulSoup
from fastapi import Request
# Configure this.
FROM_EMAIL_ADDR = 'ihorkurylo5@zohomail.com'
TO_EMAIL_ADDR = 'andriilohvin@gmail.com'
REDIRECT_URL = 'http://localhost:5000/callback/'
CLIENT_ID = '1000.PNFU8HRNLRN9MPQ2RSFI3PYFVJ75LC'
CLIENT_SECRET = '413be26aa64ff2111cf96afb02c9acd19ab5b583d0'
BASE_OAUTH_API_URL = 'https://accounts.zoho.com/'
BASE_API_URL = 'https://mail.zoho.com/api/'


ZOHO_DATA = {
    "access_token": "",
    "refresh_token": "",
    "api_domain": "https://www.zohoapis.com",
    "token_type": "Bearer",
    "expires_in": 7200,
    "account_id": "",
    "folder_id": "",
}


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
    print(data)
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
    url = (
        "%saccounts/%s/folders/%s/messages/%s/content?"
        "includeBlockContent=%s"
    ) % (BASE_API_URL, ZOHO_DATA['account_id'], folder_id, message_id, "true")
    
    headers = {
        'Authorization': 'Zoho-oauthtoken ' + ZOHO_DATA['access_token']
    }
    
    # print(url)
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    if 'content' in data['data']:
        emails = data['data']['content']
        soup = BeautifulSoup(emails, 'html.parser')
        train_txt(soup.get_text())
        # print(soup.get_text(), "\n---------------")
    # filename = f"./data/message-{from_address}-{thread_id}.txt"
    # with open("filename.txt", 'a') as f:
    #     f.write(filename + '\n')
    # with open(filename, 'a') as f:
    #     f.write(emails + '\n')

# def get_mail_folders():
#     url = BASE_API_URL + 'accounts/%s/folders'
#     url = url % ZOHO_DATA['account_id']
#     headers = {
#         'Authorization': 'Zoho-oauthtoken ' + ZOHO_DATA['access_token']
#     }
#     r = requests.get(url, headers=headers)
#     data = json.loads(r.text)
#     print(data['data'][0]['folderId'], data['data'][0]['folderName'])
#     ZOHO_DATA['folder_id'] = data['data'][0]['folderId']  # 7666736000000008014

def get_mail_list(start):

    url = BASE_API_URL + 'accounts/%s/messages/view'
    url = url % ZOHO_DATA['account_id']
    url = (
        "%s?"
        "folderId=%s&"
        "start=%s&"
        "limit=%s&"
        "threadedMails=true"
    ) % (url, ZOHO_DATA['folder_id'], start, 200)
    
    headers = {
        'Authorization': 'Zoho-oauthtoken ' + ZOHO_DATA['access_token']
    }
    
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    # print(data)
    if len(data['data']) == 0:
        return False
    for message in data['data']:
        message_id = message['messageId']
        folder_id = message['folderId']
        from_address = message['fromAddress']
        thread_id = ""
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


def start():
    req_zoho()