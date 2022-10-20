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
import io
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

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
           data['department'], 'member', data['chatId']]
    sheet.append_row(row)
    return


def get_member(sid):
    sheet = client.open("Records").worksheet('Members')
    members = sheet.get_all_records()
    member = next((m for m in members if m['ChatId'] == int(sid)), None)
    return member

def get_member_by_studentid(sid):
    sheet = client.open("Records").worksheet('Members')
    members = sheet.get_all_records()
    member = next((m for m in members if m['StudentId'] == int(sid)), None)
    return member

def get_reports_by_department(department):
    sheet = client.open("Records").worksheet('Journal')
    reports = sheet.get_all_records()
    return list(filter(lambda x: x['Department'] == department, reports))

def get_all_reports():
    sheet = client.open("Records").worksheet('Journal')
    return sheet.get_all_records()

def insert_record(data):
    member = get_member(data['chatId'])
    sheet = client.open("Records").worksheet('Journal')
    row = [member['StudentId'], member['Name'], member['Surname'], member['Department'], data['journal'], data['link'], data['fileId'], str(
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

    return link, file_id

def download_file(file_id):
    try:
        items = gdservice.files().list(fields="nextPageToken, files(id, name,mimeType)").execute()
        results = items.get('files', [])
        fileInfo = list(filter(lambda x: x['id']==file_id, results))
        if any(fileInfo):
            mime = fileInfo[0]['mimeType']
            name = fileInfo[0]['name']
        else:
            raise Exception

        request = gdservice.files().get_media(fileId = file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(F'Download {int(status.progress() * 100)}.')
        
        with open(name, "wb") as f:
            f.write(file.getbuffer())

    except Exception as error:
        print(F'An error occurred: {error}')
        name = None

    return name


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
    print(get_reports_by_department('Management'))
