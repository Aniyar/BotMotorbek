import gspread
import requests
import json
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint as pp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from datetime import datetime

gauth = GoogleAuth()
drive = GoogleDrive(gauth)

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
gdservice = build('drive', 'v3', credentials=creds)


def get_users():
    sheet = client.open("Records").sheet1
    data = sheet.get_all_records()
    pp(data)
    print(data[0])
    return


def insert_member(data):
    sheet = client.open("Records").worksheet('Members')
    row = [data['id'], data['name'], data['surname'],
           data['department'], 'member']
    sheet.append_row(row)
    return


def get_member(sid):
    sheet = client.open("Records").worksheet('Members')
    members = sheet.get_all_records()
    member = next((m for m in members if m['StudentId'] == sid), None)
    return member


def insert_record(data):
    sheet = client.open("Records").worksheet('Journal')
    row = [data['id'], data['department'], data['journal'], data['link'], str(
        datetime.today().date()), datetime.now().time().strftime("%H:%M")]
    sheet.append_row(row)
    return


def upload_file(fname):
    gfile = drive.CreateFile(
        {'parents': [{'id': '1wQEZP4215KfF8Zha3CPivZvwIh8fIjuG'}]})
    gfile.SetContentFile(fname)
    gfile.Upload()

    access_token = gauth.credentials.access_token
    file_id = gfile['id']
    url = 'https://www.googleapis.com/drive/v3/files/' + \
        file_id + '/permissions?supportsAllDrives=true'
    headers = {'Authorization': 'Bearer ' +
               access_token, 'Content-Type': 'application/json'}
    payload = {'type': 'anyone', 'value': 'anyone', 'role': 'reader'}
    res = requests.post(url, data=json.dumps(payload), headers=headers)

    # SHARABLE LINK
    link = gfile['alternateLink']
    return link


def listfiles():
    results = gdservice.files().list(
        fields="nextPageToken, files(id, name,mimeType)").execute()
    items = results.get('files', [])
    if not items:
        print('No files found.')
    else:
        print('Files:')
        print('Filename (File ID)')
        for item in items:
            print('{0} ({1})'.format(item['name'].encode('utf-8'), item['id']))
        print('Total=', len(items))


if __name__ == '__main__':
    # upload_file('file_37.jpg')
    print(get_member(202175390))
