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
#import gsheet

########################################################################
import API_Keys # from API_Keys import KC_SPOT
client_sm = Market_Spot(API_Keys.KC_SPOT['key'], API_Keys.KC_SPOT['secret'], API_Keys.KC_SPOT['passphrase'], API_Keys.KC_SPOT['is_sandbox'])
client_st = Trade_Spot(API_Keys.KC_SPOT['key'], API_Keys.KC_SPOT['secret'], API_Keys.KC_SPOT['passphrase'], API_Keys.KC_SPOT['is_sandbox'])
client_fm = Market_Futures(API_Keys.KC_FUTURES['key'], API_Keys.KC_FUTURES['secret'], API_Keys.KC_FUTURES['passphrase'], API_Keys.KC_FUTURES['is_sandbox'])
client_ft = Trade_Futures(API_Keys.KC_FUTURES['key'], API_Keys.KC_FUTURES['secret'], API_Keys.KC_FUTURES['passphrase'], API_Keys.KC_FUTURES['is_sandbox'])
"""
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
"""
########################################################################

########################################################################
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
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
formatter_idx = "{:0>6d}"

api_retry_max = 5
#trade_action = 0
########################################################################
#HTTP:
#https://api-futures.kucoin.com/api/v1/ticker?symbol=XBTUSDM
#https://api-futures.kucoin.com/api/v1/level2/depth100?symbol=XBTUSDM
#https://api.kucoin.com/api/v1/symbols
#https://api-futures.kucoin.com/api/v1/contracts/active

#global ob_buy

def proximity_in_orderbook(sym, sym_f,
                           buy_client, tgt_buy_price, max_diff_buy,
                           sell_client, tgt_sell_price, max_diff_sell,
                           size, mode):
    # Mode 1: Buy S, Sell F --> Hedge, Add
    # Mode 2: Sell S, Buy F --> Close All
    asks_size_accum, asks_price_accum, diff_buy_pct, asks_index = 0, 0, 0, 0
    bids_size_accum, bids_price_accum, diff_sell_pct, bids_index = 0, 0, 0, 0
    ask_buy_ok, bid_sell_ok = False, False
    proximity_in_orderbook_txt = ""
    proximity_short_txt = ""

    api_retry_count = 0
    while api_retry_count < api_retry_max:
        try:
            if mode == 1:
                #Mode 1: Buy S, Sell F --> Hedge, Add
                ob_buy = buy_client.get_aggregated_orderv3(symbol=sym)  # Buy S
                ob_sell = sell_client.l2_order_book(symbol=sym_f)       # Sell F
            else:
                #Mode 2: Sell S, Buy F --> Close All
                ob_buy = buy_client.l2_order_book(symbol=sym_f)               # Buy F
                ob_sell = sell_client.get_aggregated_orderv3(symbol=sym)  # Sell S
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
            diff_buy_pct = ((asks_price_accum / asks_size_accum) - tgt_buy_price) / tgt_buy_price * 100 #-ve Good, +ve NOT Good
            #print ("diff_buy:" + str(diff_buy))
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks, " + "DesiredBuyPrice: " + str(tgt_buy_price) + "\r\n"
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Takes " + str(asks_index + 1) + " entries to reach " + str(size) + " " + sym + "\r\n"
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + str(asks_index + 1) + "-th <ask> price = " + str(ob_buy['asks'][asks_index][0]) + ", diff = " + formatter_5d_pn.format(diff_buy_pct) + "%" + "\r\n" + "\r\n"
            break
        asks_index += 1

    while True:
        bids_size_accum = bids_size_accum + float(ob_sell['bids'][bids_index][1])
        bids_price_accum = bids_price_accum + (float(ob_sell['bids'][bids_index][0]) * float(ob_sell['bids'][bids_index][1])) # [0]=Price, [1]=Size
        if bids_size_accum > size:
            diff_sell_pct = (tgt_sell_price - (bids_price_accum / bids_size_accum)) / tgt_sell_price * 100 #-ve Good, +ve NOT Good
            #print("diff_sell:" + str(diff_sell))
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Sell / Bids, " + "DesiredSellPrice: " + str(tgt_sell_price) + "\r\n"
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Takes " + str(bids_index + 1) + " entries to reach " + str(size) + " " + sym + "\r\n"
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + str(bids_index + 1) + "-th <bid> price = " + str(ob_sell['bids'][bids_index][0]) + ", diff = " + formatter_5d_pn.format(diff_sell_pct) + "%" + "\r\n" + "\r\n"
            break
        bids_index += 1

    ask_buy_ok = False
    if diff_buy_pct <= max_diff_buy:
        ask_buy_ok = True
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks: " + formatter_5d_pn.format(diff_buy_pct) + "% within " + str(max_diff_buy) + " limit " + "\r\n"
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks: " + formatter_5d_pn.format(diff_buy_pct) + "% exceeded " + str(max_diff_buy) + " limit " + "\r\n"

    bid_sell_ok = False
    if diff_sell_pct <= max_diff_sell:
        bid_sell_ok = True
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Sell / Bids: " + formatter_5d_pn.format(diff_sell_pct) + "% within " + str(max_diff_sell) + " limit " + "\r\n"
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Sell / Bids: " + formatter_5d_pn.format(diff_sell_pct) + "% exceeded " + str(max_diff_sell) + " limit " + "\r\n"

    #if diff_buy_pct <= max_diff_buy and diff_sell_pct <= max_diff_sell:
    if ask_buy_ok and bid_sell_ok:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Within Limit -- Proceed to order>>"
        proximity_short_txt = "Within Limit: OK To Proceed"
        return True, proximity_in_orderbook_txt, proximity_short_txt  #OK to Prceed
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Limit Exceeded -- Do Not Proceed>>"
        proximity_short_txt = "Limit Exceeded: Do NOT Proceed"
        return False, proximity_in_orderbook_txt, proximity_short_txt #Not OK to Proceed


def place_market_order (sym, buy_client, buy_price, sell_client, sell_price, lotsize):
    #Buy S, Sell F -> Add Position
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
            print (bcolors.WARNING + bcolors.BOLD + "Buy S Order ID:  " + sym + " id:" + str(id_buy['orderId']) + bcolors.NORMAL)
            break
        except:
            api_retry_count += 1
            pass

    api_retry_count = 0
    if id_buy['orderId'] != "0": #Bought S Successful, Sell F
        while api_retry_count <= api_retry_max:
            try:
                # Sell F
                id_sell = sell_client.create_market_order(sym, Client.SIDE_SELL, size=lotsize) # --> ERROR!!!!!!!!!!!!!!!!!!!!
                print(bcolors.WARNING + bcolors.BOLD + "Sell F Order ID:  " + sym + " " + str(id_sell) + bcolors.NORMAL)
                break
            except:
                print("place_market_order (Sell F) ERROR")
                api_retry_count += 1
                pass

    api_retry_count = 0
    if id_sell == "0": #Bought S Successful, Sell F Failed, Sell S (close immediately)
        while api_retry_count <= api_retry_max:
            try:
                # Sell (Close) S
                id_close = buy_client.create_market_order(sym, Client.SIDE_SELL, size=lotsize)
            except:
                api_retry_count += 1
                pass

    return id_buy, id_sell, id_close, "Buy Order ID:  " + sym + " " + str(id_buy)

#def close_all_orders (sym, buy_client, buy_price, sell_client, sell_price, size):
    #Sell S, Buy F


#markets = client.get_markets()
#print(markets)

sym = "LUNA-USDT"
sym_f = "LUNAUSDTM"
lotsize = 1

i = 2
delta, delta_pct = 0, 0
num_pos, max_pos, num_cycle = 0, 3, 0
hedge_bottom, hedge_top = -0.1, 0.1
range_bottom, range_top = -0.15, 0.15

action_rmk = ""
ob_text = ""
f = open(sym+".csv", "a", newline="")
f.truncate(0)
writer = csv.writer(f)
tup1 = ("Index", "Local-Time", "S_TimeStamp", "S_Price$", "F_TimeStamp", "F_Price$", "F-S_TimeStamp", "F-S_Price$", "(F-S)/S_Price%", "Action", "Num_Cycle", "Num_Pos", "OrderBook")
writer.writerow(tup1)

#sys.exit()


while True:
    t.sleep(2)
    local_dt = datetime.fromtimestamp(int(t.time()))

    #ob_buy = buy_client.l2_order_book(symbol=sym)
    #bcsa = client.get_aggregated_order(symbol=sym) #get_aggregated_order(symbol=sym) RETIRED ??
    #print (bcsa)

    print("=" * 156)
    print("Iteration: " + str(i) + " "*3 + "Spot: " + sym + ", Futures: " + sym_f)
    api_retry_count = 0
    while api_retry_count <= api_retry_max:
        try:
            spot = client_sm.get_ticker(sym) #float(client.get_ticker(sym)['price'])
            spot_price = float(spot['price'])
            spot_dt = datetime.fromtimestamp(int(spot['time']) / 1000)     # using the local timezone
            #print("Spot:", spot)
            future = client_fm.get_ticker(sym_f)
            #print("Future:", future)
            future_price = float(future['price'])
            #future_dt = datetime.fromtimestamp(int(future['sequence']) / 1000)  # using the local timezone
            future_dt = datetime.fromtimestamp(int(future['ts']) / 1000000000)
            break
        except:
            api_retry_count += 1
            print ("ERROR (1)!!! when <main:get_ticker>  " + " Attempt: " + str(api_retry_count))
            pass

    delta = future_price - spot_price
    delta_pct = (future_price - spot_price) / spot_price * 100
    print("Delta: " + str(future_price) + " - " + str(spot_price) + " = " + str(delta))
    print("Delta PCT: " + str(delta_pct))

    action_rmk = "--"
    proximity_text = ""
    order_text = ""

    if num_pos == 0:
        if delta_pct >= hedge_bottom and delta_pct <= hedge_top: #Very Difficult to be 0
            #Check next 2 bid/ask in OrderBook
            print('Open Hedge')
            proceed = proximity_in_orderbook(sym, sym_f, client_sm, spot_price, 0.01, client_fm, future_price, 0.01, lotsize, mode=1)
            ob_text = proceed[1]
            proximity_text = proceed[2]
            if(proceed[0] == True):
                # Open Hedge Position
                action_rmk = "Open Hedge Position (Buy S, Sell F), OrderBook within Limit, proceed to order "
                #order = place_market_order(sym, client, spot_price, client_f, future_price, lotsize)
                #order_text = order[1]
                num_pos += 1
            else:
                action_rmk = "Open Hedge Position (Buy S, Sell F) <Halted>, OrderBook exceeded Limit "
    else:
        if delta_pct >= range_top:
            if num_pos < max_pos:
                proceed = proximity_in_orderbook(sym, sym_f, client_sm, spot_price, 0.01, client_fm, future_price, 0.01, lotsize, mode=1)
                #proceed = proximity_in_orderbook(sym, sym_f, client_sm, spot_price, 0.01, client_fm, future_price, 0.01, lotsize)
                ob_text = proceed[1]
                proximity_text = proceed[2]
                if (proceed[0] == True):
                    # Add Position
                    action_rmk = "Add Position (Buy S, Sell F), OrderBook within Limit, proceed to order "
                    num_pos += 1
                else:
                    action_rmk = "Add Position (Buy S, Sell F) <Halted>, OrderBook exceeded Limit "
            else:
                action_rmk = "Should Add Position (Buy S, Sell F), but already hit max "
        if delta_pct <= range_bottom:
            proceed = proximity_in_orderbook(sym, sym_f, client_fm, future_price, 0.01, client_sm, spot_price, 0.01, lotsize*num_pos, mode=2)
            ob_text = proceed[1]
            proximity_text = proceed[2]
            if (proceed[0] == True):
                #Close All Positions
                action_rmk = "Close All (Sell S, Buy F)  " + str(num_pos) + " Positions"
                num_pos = 0
                num_cycle += 1
            else:
                action_rmk = "Close All (Sell S, Buy F) <Halted>, OrderBook exceeded Limit "

    disp = str(formatter_idx.format(i)) + ':' + \
           " Local Time: " + str(local_dt) + \
           " <Spot>: (" + spot_dt.strftime("%Y-%m-%d %H:%M:%S.%f") + ") " + str(formatter_5d.format(spot_price)) + \
           " <Future>: (" + future_dt.strftime("%Y-%m-%d %H:%M:%S.%f") + ") " + str(formatter_5d.format(future_price)) + \
           " <Time (F-S)>: " + str(formatter_5d_pn.format((future_dt - spot_dt).total_seconds())) + "\n" + \
           bcolors.OKBLUE + "<Delta>: " + str(formatter_5d_pn.format(delta)) + bcolors.NORMAL + \
           bcolors.OKCYAN + " <Delta %>: " + str(formatter_5d_pn.format(delta_pct)) + "%" + bcolors.NORMAL + \
           " <Action>: " + "{:<84}".format(action_rmk) + \
           " NumCycle:" + str(num_cycle).zfill(2) + "  NumPos:" + str(num_pos).zfill(2) + "\n" + \
           bcolors.WARNING + bcolors.BOLD + "<Proximity Check>: " + str(proximity_text) + bcolors.NORMAL + "\n" + \
           bcolors.WARNING + bcolors.BOLD + "<Order Action>: " + str(order_text) + bcolors.NORMAL
    tup1 = (str(i), str(local_dt),
            spot_dt.strftime("%Y-%m-%d %H:%M:%S.%f"),
            str(spot_price), future_dt.strftime("%Y-%m-%d %H:%M:%S.%f"),
            str(future_price), (future_dt - spot_dt).total_seconds(), str("{:.5f}".format(delta)), str("{:.5f}".format(delta_pct)), action_rmk, num_cycle, num_pos, ob_text)
    writer.writerow(tup1)
    print(disp)

    ob_text = ""
    i += 1
    if keyboard.is_pressed("q"):
        print ("q pressed, end loop")
        break
f.close()



