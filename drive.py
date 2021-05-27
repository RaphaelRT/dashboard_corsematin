# https://developers.google.com/drive/api/v3/quickstart/python
from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import pandas as pd
import ssl
from dotenv import load_dotenv
import json
load_dotenv(verbose=True)

ssl._create_default_https_context = ssl._create_unverified_context

# https://developers.google.com/analytics/devguides/config/mgmt/v3/quickstart/service-py
from apiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
#print(os.environ)

champs_cred = [
  "type",
  "project_id",
  "private_key_id",
  "private_key",
  "client_email",
  "client_id",
  "auth_uri"
  "token_uri",
  "auth_provider_x509_cert_url",
  "client_x509_cert_url"
]
#champs_cred = {c : os.environ.get(c.upper())  for c in champs_cred}
#champs_cred["private_key"] = champs_cred["private_key"].replace("\n", "")
#with open('credentials.json', 'w') as fp:
    #json.dump(champs_cred, fp, indent=2, separators=(',', ': '))
json_str = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
json_data = json.loads(json_str)
json_data['private_key'] = json_data['private_key'].replace('\\n', '\n')

credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            json_data, scopes=SCOPES
            )

# https://developers.google.com/drive/api/v3/quickstart/python
service = build('drive', 'v3', credentials=credentials)

# Call the Drive v3 API
results = service.files().list(
    pageSize=10, fields="nextPageToken, files(id, name)").execute()
items = results.get('files', [])

if not items:
    print('No files found.')
else:
    print('Files:')
    #for item in items:
        #print(u'{0} ({1})'.format(item['name'], item['id']))
data_files = {item['name']: f"https://drive.google.com/uc?id={item['id']}" for item in items}
print(data_files)



