import gspread
from oauth2client.service_account import ServiceAccountCredentials
import names
import datetime

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

credentials = ServiceAccountCredentials.from_json_keyfile_name('./credentials.json', scope)
gc = gspread.authorize(credentials)

def get_sheet():
    sh = gc.create('A new spreadsheet')
    today = str(datetime.date.today())
    name = names.get_first_name(gender='female')
    sh = gc.create(f'{today} {name}')
    sh.share(None, perm_type='anyone', role='writer')
    sh_link = f"https://docs.google.com/spreadsheets/d/{sh.id}"
    return sh, sh_link
