#Do NOT name this file <<gspread.py>> --> Will get error
import gspread
import time as t

api_retry_max = 5
empty_ws_name = "current"

def set_current_ws(ws_name):
    ws = sh.worksheet(ws_name)

def clean():
    #ws = sh.worksheet(ws_name)
    ws.clear()

def rename_worksheet(new_ws_name):
    ws.update_title(title=new_ws_name)

def freeze(top_x_row):
    ws.freeze(rows=top_x_row)

def write_cell(row, col, content):
    ws.update_cell(row, col, content)

def write_tuple(row, tup1):
    api_retry_count = 0
    while api_retry_count <= api_retry_max:
        try:
            for i, val in enumerate(tup1):
                ws.update_cell(row, i+1, val)
                #gsheet.write(num_order_placed+1, i+1, val)
            break
        except:
            api_retry_count += 1
            print("ERROR (G-1)!!! when <main:gspreadr>  " + " Attempt: " + str(api_retry_count))
            t.sleep(60)    # 'code': 429, 'message': "Quota exceeded for quota metric 'Write requests'
            pass


print ("GoogleSpread Ver:" + gspread.__version__)
gc = gspread.service_account(filename='gsheet_credential.json')
sh = gc.open_by_key("1xTl1k5pTeo13lj1MZf74fU3dBvNTtN6B7N-Ly-R8y9I") #ARBATM_DATA

# Create empty WS named "current"
try:
    ws = sh.worksheet(empty_ws_name)
except:
    ws = sh.add_worksheet(title=empty_ws_name, rows="0", cols="0")
    pass

