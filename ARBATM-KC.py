# pip install python-kucoin #-----Third Party -- Do NOT use
# PIP uninstall python-kucoin
# from kucoin.client import Client

# pip install kucoin-python         #Official
# pip install kucoin-futures-python #Official
# STOP Working -- Fix: python -m ensurepip
from kucoin.client import Market as Market_Spot
from kucoin.client import Trade as Trade_Spot
from kucoin_futures.client import Market as Market_Futures
from kucoin_futures.client import Trade as Trade_Futures
#from kucoin.asyncio import KucoinSocketManager
import sys
import csv
import keyboard #pip install keyboard
from datetime import datetime
import time as t
import winsound
import gsheet

########################################################################
import API_Keys # from API_Keys import KC_SPOT
use_sandbox = False
if use_sandbox:
    client_sm = Market_Spot(API_Keys.KC_SPOT_SANDBOX['key'],
                            API_Keys.KC_SPOT_SANDBOX['secret'],
                            API_Keys.KC_SPOT_SANDBOX['passphrase'],
                            API_Keys.KC_SPOT_SANDBOX['is_sandbox'])
    client_st = Trade_Spot(API_Keys.KC_SPOT_SANDBOX['key'],
                           API_Keys.KC_SPOT_SANDBOX['secret'],
                           API_Keys.KC_SPOT_SANDBOX['passphrase'],
                           API_Keys.KC_SPOT_SANDBOX['is_sandbox'])
    client_fm = Market_Futures(API_Keys.KC_FUTURES_SANDBOX['key'],
                               API_Keys.KC_FUTURES_SANDBOX['secret'],
                               API_Keys.KC_FUTURES_SANDBOX['passphrase'],
                               API_Keys.KC_FUTURES_SANDBOX['is_sandbox'])
    client_ft = Trade_Futures(API_Keys.KC_FUTURES_SANDBOX['key'],
                              API_Keys.KC_FUTURES_SANDBOX['secret'],
                              API_Keys.KC_FUTURES_SANDBOX['passphrase'],
                              API_Keys.KC_FUTURES_SANDBOX['is_sandbox'])
else:
    client_sm = Market_Spot(API_Keys.KC_SPOT['key'],
                            API_Keys.KC_SPOT['secret'],
                            API_Keys.KC_SPOT['passphrase'],
                            API_Keys.KC_SPOT['is_sandbox'])
    client_st = Trade_Spot(API_Keys.KC_SPOT['key'],
                           API_Keys.KC_SPOT['secret'],
                           API_Keys.KC_SPOT['passphrase'],
                           API_Keys.KC_SPOT['is_sandbox'])
    client_fm = Market_Futures(API_Keys.KC_FUTURES['key'],
                               API_Keys.KC_FUTURES['secret'],
                               API_Keys.KC_FUTURES['passphrase'],
                               API_Keys.KC_FUTURES['is_sandbox'])
    client_ft = Trade_Futures(API_Keys.KC_FUTURES['key'],
                              API_Keys.KC_FUTURES['secret'],
                              API_Keys.KC_FUTURES['passphrase'],
                              API_Keys.KC_FUTURES['is_sandbox'])

########################################################################

########################################################################
class bcolors:
    Red = '\033[91m'
    Blue = '\033[94m'
    Cyan = '\033[96m'
    Green = '\033[92m'
    Magenta = '\033[95m'
    Grey = '\033[90m'
    Yellow = '\033[93m'
    Orange = '\033[48;2;255;165;0m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    NORMAL = '\033[39m'

class actions:
    DoNothing = 0
    OpenHedge = 1       # Open Hedge Position (Buy S, Sell F)
    AddPosition = 2     # Add Position (Buy S, Sell F)
    CloseAll = 3        # Close All (Sell S, Buy F)

formatter_2d = "{0:.2f}"
formatter_5d = "{0:.5f}"
formatter_5d_pn = "{:+.5f}" # with +ve/-ve sign
formatter_3d_pn = "{:+.3f}" # with +ve/-ve sign
formatter_idx = "{:0>6d}"

########################################################################
api_retry_max = 5
exchange_name = "KuCoin"
########################################################################
#https://api-futures.kucoin.com/api/v1/ticker?symbol=XBTUSDM
#https://api-futures.kucoin.com/api/v1/level2/depth100?symbol=XBTUSDM
#https://api.kucoin.com/api/v1/symbols
#https://api-futures.kucoin.com/api/v1/contracts/active

#global ob_buy

def proximity_in_orderbook(sym, sym_f,
                           buy_client, tgt_buy_price, buy_variance_allowed_pct,
                           sell_client, tgt_sell_price, sell_variance_allowed_pct,
                           size, mode):
    ####################################################################################
    # Mode 1: Buy S, Sell F --> Hedge, Add
    # Mode 2: Sell S, Buy F --> Close All
    # Double check that OrderBook support desired execute price within allowed variance
    # Allow +/- variance  (-ve Good, +ve NOT Good)
    ####################################################################################
    asks_size_accum, asks_price_accum, diff_buy_pct, asks_index = 0, 0, 0, 0
    bids_size_accum, bids_price_accum, diff_sell_pct, bids_index = 0, 0, 0, 0
    ask_buy_ok, bid_sell_ok = False, False
    proximity_short_txt, proximity_in_orderbook_txt = "", ""

    api_retry_count = 0
    while api_retry_count < api_retry_max:
        try:
            if mode == 1:
                #Mode 1: Buy S, Sell F --> Hedge, Add
                ob_buy = buy_client.get_aggregated_orderv3(symbol=sym)      # Buy S
                ob_sell = sell_client.l2_order_book(symbol=sym_f)           # Sell F
            else:
                #Mode 2: Sell S, Buy F --> Close All
                ob_buy = buy_client.l2_order_book(symbol=sym_f)             # Buy F
                ob_sell = sell_client.get_aggregated_orderv3(symbol=sym)    # Sell S
            break
        except:
            t.sleep(2)
            api_retry_count += 1
            print("ERROR (2)!!! when <proximity_in_orderbook:get_order_book>  " + " Attempt: " + str(api_retry_count))
            pass

    while True:
        asks_size_accum = asks_size_accum + float(ob_buy['asks'][asks_index][1])
        asks_price_accum = asks_price_accum + (float(ob_buy['asks'][asks_index][0]) * float(ob_buy['asks'][asks_index][1])) # [0]=Price, [1]=Size
        if asks_size_accum > size:
            diff_buy_pct = ((asks_price_accum / asks_size_accum) - tgt_buy_price) / tgt_buy_price * 100
            # -ve Good, +ve NOT Good
            # -ve: avg. asks on OrderBook cheaper than target buy price
            # +ve: avg. asks on OrderBook more expensive than target buy price
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks, " + "DesiredBuyPrice: " + str(tgt_buy_price) + "\r\n"
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Takes " + str(asks_index + 1) + " entries to reach " + str(size) + " " + sym + "\r\n"
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + str(asks_index + 1) + "-th <ask> price = " + str(ob_buy['asks'][asks_index][0]) + ", diff = " + formatter_5d_pn.format(diff_buy_pct) + "%" + "\r\n" + "\r\n"
            break
        asks_index += 1

    while True:
        bids_size_accum = bids_size_accum + float(ob_sell['bids'][bids_index][1])
        bids_price_accum = bids_price_accum + (float(ob_sell['bids'][bids_index][0]) * float(ob_sell['bids'][bids_index][1])) # [0]=Price, [1]=Size
        if bids_size_accum > size:
            diff_sell_pct = (tgt_sell_price - (bids_price_accum / bids_size_accum)) / tgt_sell_price * 100
            # -ve Good, +ve NOT Good
            # -ve: avg. bids on OrderBook higher than target sell price
            # +ve: avg. bids on OrderBook lower than target sell price
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Sell / Bids, " + "DesiredSellPrice: " + str(tgt_sell_price) + "\r\n"
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Takes " + str(bids_index + 1) + " entries to reach " + str(size) + " " + sym + "\r\n"
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + str(bids_index + 1) + "-th <bid> price = " + str(ob_sell['bids'][bids_index][0]) + ", diff = " + formatter_5d_pn.format(diff_sell_pct) + "%" + "\r\n" + "\r\n"
            break
        bids_index += 1

    ask_buy_ok = False
    if diff_buy_pct <= buy_variance_allowed_pct:
        ask_buy_ok = True
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks: " + formatter_5d_pn.format(diff_buy_pct) + "% within " + str(buy_variance_allowed_pct) + " limit " + "\r\n"
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks: " + formatter_5d_pn.format(diff_buy_pct) + "% exceeded " + str(buy_variance_allowed_pct) + " limit " + "\r\n"

    bid_sell_ok = False
    if diff_sell_pct <= sell_variance_allowed_pct:
        bid_sell_ok = True
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Sell / Bids: " + formatter_5d_pn.format(diff_sell_pct) + "% within " + str(sell_variance_allowed_pct) + " limit " + "\r\n"
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Sell / Bids: " + formatter_5d_pn.format(diff_sell_pct) + "% exceeded " + str(sell_variance_allowed_pct) + " limit " + "\r\n"

    if ask_buy_ok and bid_sell_ok:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Within Limit -- Proceed to order>>"
        proximity_short_txt = str(formatter_5d_pn.format(diff_buy_pct))  + "% within " + str(buy_variance_allowed_pct)  + "% Limit " + "(" + str(asks_index) + ")" + ", " + \
                              str(formatter_5d_pn.format(diff_sell_pct)) + "% within " + str(sell_variance_allowed_pct) + "% Limit " + "(" + str(bids_index) + ")" + " -- OK to Proceed"
        #return True, proximity_in_orderbook_txt, proximity_short_txt  #OK to Prceed
    elif ask_buy_ok:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Limit Exceeded -- Do Not Proceed>>"
        proximity_short_txt = str(formatter_5d_pn.format(diff_buy_pct))  + "% within " + str(buy_variance_allowed_pct)  + "% Limit " + "(" + str(asks_index) + ")" + ", " + \
                              str(formatter_5d_pn.format(diff_sell_pct)) + "% exceed " + str(sell_variance_allowed_pct) + "% Limit " + "(" + str(bids_index) + ")" + " -- NOT OK"
        #return False, proximity_in_orderbook_txt, proximity_short_txt #Not OK to Proceed
    elif bid_sell_ok:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Limit Exceeded -- Do Not Proceed>>"
        proximity_short_txt = str(formatter_5d_pn.format(diff_buy_pct))  + "% exceed " + str(buy_variance_allowed_pct)  + "% Limit " + "(" + str(asks_index) + ")" + ", " + \
                              str(formatter_5d_pn.format(diff_sell_pct)) + "% within " + str(sell_variance_allowed_pct) + "% Limit " + "(" + str(bids_index) + ")" + " -- NOT OK"
        #return False, proximity_in_orderbook_txt, proximity_short_txt #Not OK to Proceed
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Limit Exceeded -- Do Not Proceed>>"
        proximity_short_txt = str(formatter_5d_pn.format(diff_buy_pct))  + "% exceed " + str(buy_variance_allowed_pct)  + "% Limit " + "(" + str(asks_index) + ")" + ", " + \
                              str(formatter_5d_pn.format(diff_sell_pct)) + "% exceed " + str(sell_variance_allowed_pct) + "% Limit " + "(" + str(bids_index) + ")" + " -- NOT OK"
        #return False, proximity_in_orderbook_txt, proximity_short_txt  # Not OK to Proceed

    return ask_buy_ok and bid_sell_ok, proximity_in_orderbook_txt, proximity_short_txt

def place_market_order (sym, sym_f,
                        buy_client, buy_price,
                        sell_client, sell_price,
                        lotsize):
    ####################################################################################
    # Buy S, Sell F --> Hedge, Add
    # Place Market and RollBack if necessary
    ####################################################################################
    id_buy = "0"
    id_sell = "0"
    id_close = "0"
    print("Buy S: " + str(lotsize) + " " + sym)
    print("Sell F: " + str(lotsize) + " " + sym)
    place_market_order_txt = ""

    api_retry_count = 0
    while api_retry_count <= api_retry_max:
        try:
            # Buy S
            id_buy = buy_client.create_market_order (sym, Client.SIDE_BUY, size=lotsize) # This Actually work
            #order_id = client.create_market_order('BTC-USDT', 'buy', size='1')
            print (bcolors.WARNING + bcolors.BOLD + "Buy S Order ID:  " + sym + " id:" + str(id_buy['orderId']) + "!!!!!" + bcolors.NORMAL)
            break
        except:
            print("ERROR (3a)!!! when <place_market_order:create_market_order>  " + " Attempt: " + str(api_retry_count))
            api_retry_count += 1
            pass

    api_retry_count = 0
    if id_buy['orderId'] != "0": #Bought S Successful, Sell F
        while api_retry_count <= api_retry_max:
            try:
                # Sell F
                id_sell = sell_client.create_market_order(sym, Client.SIDE_SELL, size=lotsize) # --> ERROR!!!!!!!!!!!!!!!!!!!!
                print(bcolors.WARNING + bcolors.BOLD + "Sell F Order ID:  " + sym_f + " " + str(id_sell) + bcolors.NORMAL)
                break
            except:
                print("place_market_order (Sell F) ERROR")
                api_retry_count += 1
                pass

    api_retry_count = 0
    if id_sell == "0": #Bought S Successful, Sell F Failed, Sell S (close IMMEDIATELY!!)
        while api_retry_count <= api_retry_max:
            try:
                # Sell (Close) S
                id_close = buy_client.create_market_order(sym, Client.SIDE_SELL, size=lotsize)
            except:
                api_retry_count += 1
                pass

    return id_buy, id_sell, id_close, "Buy Order ID:  " + sym + " " + str(id_buy)


symbol = "ETH"
sym, sym_f = symbol+"-USDT", symbol+"USDTM" #"SUSHI-USDT", "SUSHIUSDTM"
lotsize = 100 #10000
max_pos = 5
spot_fee_pct = 0.1      #0.1%
futures_fee_pct = 0.03  #vary from 0.03% to 0%


probe_idx = 2
delta, delta_pct = 0, 0
max_delta_pct, min_delta_pct, zero_delta_pct = 0, 0, 1000
num_pos, num_order_placed, num_cycle = 0, 0, 0
start_dt = datetime.fromtimestamp(int(t.time()))
tgt_pl = 0

hedge_bottom, hedge_top = -0.04, 0.04 #-0.01, 0.01   # in %
range_bottom, range_top = -0.25, 0.25   #-0.25, 0.25   # in %
ob_var_allow_pct  = 0.3          #0.01 # in %
ts_var_allow_sec = 2.5           # in seconds

file_ws_name = exchange_name + "_" + symbol + "_" +  str(start_dt)
condition, condition_rmk = "", ""
action, action_rmk = "", ""
ob_text = ""
f = open(file_ws_name.replace(":","-") + ".csv", "a", newline="")
f.truncate(0)
writer = csv.writer(f)
tup1 = ("Index", "Local-Time",
        "OrderPlaced", "Target_PL",
        "F_TimeStamp", "F_Price$",
        "S_TimeStamp", "S_Price$",
        "F-S_TimeStamp", "F-S_$", "(F-S)/S_%",
        "Condition", "Condition Txt", "Action", "Action Txt",
        "Num_Cycle", "Num_Order_Placed", "Num_Pos", "OrderBook")
writer.writerow(tup1)

#def add_empty_sheet():
#    sh.add_worksheet(title=empty_ws_name)
file_ws_name = exchange_name + "_" + symbol + "_" +  str(start_dt)
gsheet.rename_worksheet(file_ws_name)
gsheet.set_current_ws(file_ws_name)
gsheet.clean()
gsheet.freeze(2)
gsheet.write_cell(1, 1,
                  "Started On: " + str(start_dt) + "\r\n" + "\r\n" +
                  "Exchange: " + exchange_name + "\r\n" +
                  "Sandbox: " + str(use_sandbox) + "\r\n" +
                  "Spot: " + sym + "\r\n" +
                  "Futures: " + sym_f + "\r\n" +
                  "Lot Size: " + str(lotsize) + "\r\n\r\n" +
                  "Parameters:" + "\r\n" +
                  "F/S Time Diff Allow: " + str(ts_var_allow_sec) + " seconds" + "\r\n" +
                  "Hedge (F=S): " + str(hedge_bottom) + " to " + str(hedge_top) + "%" + "\r\n" +
                  "Add (F>=S): " + str(range_top) + "%" + "\r\n" +
                  "Close All (F<=S):" + str(range_bottom) + "%")
gsheet.write_tuple(num_order_placed + 2, tup1)

#sys.exit()


while True:
    t.sleep(0)
    local_dt = datetime.fromtimestamp(int(t.time()))

    #bcsa = client.get_aggregated_order(symbol=sym) #get_aggregated_order(symbol=sym) RETIRED ??


    api_retry_count = 0
    while api_retry_count <= api_retry_max:
        try:
            spot = client_sm.get_ticker(sym) #float(client.get_ticker(sym)['price'])
            spot_price = float(spot['price'])
            spot_dt = datetime.fromtimestamp(int(spot['time']) / 1000)     # using the local timezone
            future = client_fm.get_ticker(sym_f)
            future_price = float(future['price'])
            future_dt = datetime.fromtimestamp(int(future['ts']) / 1000000000)
            break
        except:
            api_retry_count += 1
            print ("ERROR (1)!!! when <main:get_ticker>  " + " Attempt: " + str(api_retry_count))
            pass

    delta = future_price - spot_price
    delta_pct = (future_price - spot_price) / spot_price * 100
    if delta_pct < min_delta_pct:
        min_delta_pct = delta_pct
    elif delta_pct > max_delta_pct:
        max_delta_pct = delta_pct
    if abs(delta_pct) < abs(zero_delta_pct):
        zero_delta_pct = delta_pct
    if delta_pct > 0:
        # F>S
        condition = "Contango (F>S)"
    elif delta_pct < 0:
        # F<S
        condition = 'Backwardation (F<S)'
    else:
        #F=S
        condition = 'Neutural (F=S)'

    ts_diff = (future_dt - spot_dt).total_seconds()
    if abs(ts_diff) <= ts_var_allow_sec:
        ts_within_allowance = True
        ts_diff_txt = str(formatter_5d_pn.format(ts_diff)) + "sec within +/-" + str(ts_var_allow_sec) + "sec limit"
    else:
        ts_within_allowance = False
        ts_diff_txt = str(formatter_5d_pn.format(ts_diff)) + "sec exceeded +/-" + str(ts_var_allow_sec) + "sec limit"


    action_rmk, condition_rmk = "", ""
    proximity_text = ""
    order_text = ""
    action = "--"
    order_placed = "--"
    happenings = 0
    if num_pos == 0:
        if delta_pct >= hedge_bottom and delta_pct <= hedge_top and ts_within_allowance: #Very Difficult to be 0
            ########################
            # Open Hedge Position
            ########################
            condition_rmk = "NumPos = " + str(num_pos) + " and Delta_Pct:" + str(formatter_5d_pn.format(delta_pct)) + "% is between " + str(formatter_3d_pn.format(hedge_bottom)) + "% and " + str(formatter_3d_pn.format(hedge_top)) + "%"
            action = "Open Hedge" + "(" + str(formatter_5d_pn.format(delta_pct)) + "% is between " + str(hedge_bottom) + "% and " + str(hedge_top) + "%)"
            proceed = proximity_in_orderbook(sym, sym_f,
                                             client_sm, spot_price, ob_var_allow_pct,
                                             client_fm, future_price, ob_var_allow_pct,
                                             lotsize, mode=1)
            ob_text = proceed[1]
            proximity_text = proceed[2]
            if(proceed[0] == True):
                # Open Hedge Position
                action_rmk = "Open Hedge Position (Buy S, Sell F), OrderBook within Limit, proceed to order "
                #order = place_market_order(sym, client, spot_price, client_f, future_price, lotsize)
                #order_text = order[1]
                num_pos += 1
                order_placed = "Hedged"
                tgt_pl = (future_price - spot_price) * lotsize
                print (tgt_pl)
                num_order_placed += 1
                winsound.Beep(440, 500)
            else:
                action_rmk = "Open Hedge Position (Buy S, Sell F) <Halted>, OrderBook exceeded Limit "
        else:
            condition_rmk = "NumPos = " + str(num_pos) + " and Delta_Pct:" + str(formatter_5d_pn.format(delta_pct)) + "% is NOT between " + str(formatter_3d_pn.format(hedge_bottom)) + "% and " + str(formatter_3d_pn.format(hedge_top)) + "%"

    else:
        if delta_pct >= range_top and ts_within_allowance:
            ########################
            # Add Position
            ########################
            condition_rmk = "NumPos = " + str(num_pos) + " and Delta_Pct:" + str(formatter_3d_pn.format(delta_pct)) + "% >= " + str(formatter_3d_pn.format(range_top)) + "%"
            action = "Add Position" + "(" + str(formatter_5d_pn.format(delta_pct)) + "% >= " + str(range_top) + "%)"
            if num_pos < max_pos:
                proceed = proximity_in_orderbook(sym, sym_f,
                                                 client_sm, spot_price, ob_var_allow_pct,
                                                 client_fm, future_price, ob_var_allow_pct,
                                                 lotsize, mode=1)
                #proceed = proximity_in_orderbook(sym, sym_f, client_sm, spot_price, 0.01, client_fm, future_price, 0.01, lotsize)
                ob_text = proceed[1]
                proximity_text = proceed[2]
                if (proceed[0] == True):
                    # Add Position
                    action_rmk = "Add Position (Buy S, Sell F), OrderBook within Limit, proceed to order "
                    num_pos += 1
                    order_placed = "Added"
                    tgt_pl = (future_price - spot_price) * lotsize
                    num_order_placed += 1
                    winsound.Beep(440, 500)
                else:
                    action_rmk = "Add Position (Buy S, Sell F) <Halted>, OrderBook exceeded Limit "
            else:
                action_rmk = "Should Add Position (Buy S, Sell F), but already hit max "
        elif delta_pct <= range_bottom and ts_within_allowance:
            ########################
            # Close All Positions
            ########################
            condition_rmk = "NumPos = " + str(num_pos) + " and Delta_Pct:" + str(formatter_5d_pn.format(delta_pct)) + "% <= " + str(formatter_3d_pn.format(range_bottom)) + "%"
            action = "Close All " + "(" + str(formatter_5d_pn.format(delta_pct)) + "% <= " + str(range_bottom) + "%)"
            proceed = proximity_in_orderbook(sym, sym_f,
                                             client_fm, future_price, ob_var_allow_pct,
                                             client_sm, spot_price, ob_var_allow_pct,
                                             lotsize*num_pos, mode=2)
            ob_text = proceed[1]
            proximity_text = proceed[2]
            if (proceed[0] == True):
                #Close All Positions
                action_rmk = "Close All (Sell S, Buy F)  " + str(num_pos) + " Positions"
                num_pos = 0
                num_cycle += 1
                order_placed = "Closed"
                tgt_pl = (spot_price - future_price) * lotsize
                num_order_placed += 1
                winsound.Beep(440, 500)
            else:
                action_rmk = "Close All (Sell S, Buy F) <Halted>, OrderBook exceeded Limit "
        else:
            ##########################
            # Do Nothing, Loop Again #
            ##########################
            condition_rmk = "NumPos = " + str(num_pos) + " and Delta_Pct:" + str(formatter_5d_pn.format(delta_pct)) + "% is Neither <= " + str(formatter_3d_pn.format(range_bottom)) + "% or >= " + str(formatter_3d_pn.format(range_top)) + "%"

    disp = ("=" * 156) + "\n" + \
            "Local Time: " + str(local_dt) + " (Started: " + str(start_dt) + ", " + str(local_dt-start_dt) + " ago)" + " "*59 + \
            "NumCycle:" + str(num_cycle).zfill(2) + "  NumPos:" + str(num_pos).zfill(2) + "\n" + \
            "Iteration: " + str(formatter_idx.format(probe_idx)) + " "*3 + "Spot: " + sym + ", Futures: " + sym_f + " "*75 + "NumOrderPlaced:" + str(happenings).zfill(2) + " " + bcolors.Red + order_placed + bcolors.NORMAL + "\n" + \
            "<Future>: (" + future_dt.strftime("%Y-%m-%d %H:%M:%S.%f") + ") " + str(formatter_5d.format(future_price)) + \
            " <Spot>: (" + spot_dt.strftime("%Y-%m-%d %H:%M:%S.%f") + ") " + str(formatter_5d.format(spot_price)) + "\n" + \
            bcolors.Blue + "<Delta>: " + str(formatter_5d_pn.format(delta)) + bcolors.NORMAL + \
            bcolors.Cyan + " <Delta_Pct>: " + str(formatter_5d_pn.format(delta_pct)) + "% " + \
            bcolors.Green + " (Min_Delta_Pct:" + str(formatter_5d_pn.format(min_delta_pct)) + "% Max_Delta_Pct:" + str(formatter_5d_pn.format(max_delta_pct)) + "% Zero_Delta_Pct:" + str(formatter_5d_pn.format(zero_delta_pct)) + "%)" + bcolors.NORMAL + "\n" + \
            bcolors.Yellow + "<Time Delta (F-S)>: " + ts_diff_txt + bcolors.NORMAL + "\n" + \
            bcolors.Yellow + "{:<20}".format("<Condition>:") + bcolors.Red + "{:<20}".format(condition) + bcolors.Yellow + condition_rmk + bcolors.NORMAL + "\n" + \
            bcolors.Yellow + "{:<20}".format("<Action>:") + bcolors.Red + "{:<20}".format(action) + bcolors.Yellow + "{:<121}".format(action_rmk) + bcolors.NORMAL + "\n" + \
            bcolors.Yellow + "<Proximity Check>:  " + str(proximity_text) + bcolors.NORMAL + "\n" + \
            bcolors.Yellow + "<Order Action>: " + str(order_text) + bcolors.NORMAL
    tup1 = (str(probe_idx), str(local_dt),
            order_placed, str(tgt_pl),
            spot_dt.strftime("%Y-%m-%d %H:%M:%S.%f"), str(spot_price),
            future_dt.strftime("%Y-%m-%d %H:%M:%S.%f"), str(future_price),
            (future_dt - spot_dt).total_seconds(), str("{:.5f}".format(delta)), str("{:.5f}".format(delta_pct)),
            condition, condition_rmk, action, action_rmk,
            num_cycle, num_order_placed, num_pos, ob_text)

    writer.writerow(tup1)
    print(disp)
    if order_placed != "--":
        gsheet.write_tuple(num_order_placed + 2, tup1)

    ob_text = ""
    probe_idx += 1
    if keyboard.is_pressed("q"):
        print ("q pressed, end loop")
        break
f.close()
