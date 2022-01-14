#Do NOT name this file <<gspread.py>> --> Will get error
import gspread

print (gspread.__version__)
gc = gspread.service_account(filename='gsheet_credential.json')
sh = gc.open_by_key("1xTl1k5pTeo13lj1MZf74fU3dBvNTtN6B7N-Ly-R8y9I")
ws = sh.worksheet("current")

def clean:
    ws.clear()


