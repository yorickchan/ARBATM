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
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd




import ARBATM_param
if ARBATM_param.output_to_gsheet:
    import gsheet

#use_sandbox = ARBATM_param.use_sandbox
#output_to_gsheet = ARBATM_param.output_to_gsheet
#output_to_csv = ARBATM_param.output_to_csv


########################################################################
import API_Keys # from API_Keys import KC_SPOT

if ARBATM_param.use_sandbox:
    ######################
    # USE SANDBOX ACCOUNT
    ######################
    #client_sm = Market_Spot(url='https://openapi-sandbox.kucoin.com')
    client_sm = Market_Spot(key=API_Keys.KC_SPOT_SANDBOX['key'],
                            secret=API_Keys.KC_SPOT_SANDBOX['secret'],
                            passphrase=API_Keys.KC_SPOT_SANDBOX['passphrase'],
                            is_sandbox=API_Keys.KC_SPOT_SANDBOX['is_sandbox'],
                            url='https://openapi-sandbox.kucoin.com')
    #spot = client_sm.get_ticker('BTC-USDT') # WORK ONLY FOR ETH-USDT AND BTC-USDT!!!!!!!!!!!!
    #print("Sandbox-S")
    #print(spot)
    #sys.exit()
    client_st = Trade_Spot(key=API_Keys.KC_SPOT_SANDBOX['key'],
                           secret=API_Keys.KC_SPOT_SANDBOX['secret'],
                           passphrase=API_Keys.KC_SPOT_SANDBOX['passphrase'],
                           is_sandbox=API_Keys.KC_SPOT_SANDBOX['is_sandbox'])
    #client_fm = Market_Futures(url='https://api-sandbox-futures.kucoin.com')
    client_fm = Market_Futures(key=API_Keys.KC_FUTURES_SANDBOX['key'],
                               secret=API_Keys.KC_FUTURES_SANDBOX['secret'],
                               passphrase=API_Keys.KC_FUTURES_SANDBOX['passphrase'],
                               is_sandbox=API_Keys.KC_FUTURES_SANDBOX['is_sandbox'],
                               url='https://api-sandbox-futures.kucoin.com')
    #future = client_fm.get_ticker('ETHUSDTM')
    #print("Sandbox-F")
    #print(future)
    #sys.exit()

    client_ft = Trade_Futures(key=API_Keys.KC_FUTURES_SANDBOX['key'],
                              secret=API_Keys.KC_FUTURES_SANDBOX['secret'],
                              passphrase=API_Keys.KC_FUTURES_SANDBOX['passphrase'],
                              is_sandbox=API_Keys.KC_FUTURES_SANDBOX['is_sandbox'])
else:
    ######################
    # USE *REAL* ACCOUNT
    ######################
    #client_sm = Market_Spot(url='https://api.kucoin.com')
    #klines = client_sm.get_kline('BTC-USDT', '1min')
    #print(klines)
    #spot = client_sm.get_ticker('BTC-USDT')
    #print(spot)
    #print(spot)
    client_sm = Market_Spot(key=API_Keys.KC_SPOT['key'],
                            secret=API_Keys.KC_SPOT['secret'],
                            passphrase=API_Keys.KC_SPOT['passphrase'],
                            is_sandbox=API_Keys.KC_SPOT['is_sandbox'],
                            url=API_Keys.KC_SPOT['url'])
    #url = 'https://api.kucoin.com'
    #spot = client_sm.get_ticker('BTC-USDT')
    #print(spot)
    #sys.exit()

    client_st = Trade_Spot(key=API_Keys.KC_SPOT['key'],
                           secret=API_Keys.KC_SPOT['secret'],
                           passphrase=API_Keys.KC_SPOT['passphrase'],
                           is_sandbox=API_Keys.KC_SPOT['is_sandbox'],
                           url=API_Keys.KC_SPOT['url'])

    client_fm = Market_Futures(key=API_Keys.KC_FUTURES['key'],
                               secret=API_Keys.KC_FUTURES['secret'],
                               passphrase=API_Keys.KC_FUTURES['passphrase'],
                               is_sandbox=API_Keys.KC_FUTURES['is_sandbox'],
                               url=API_Keys.KC_FUTURES['url'])
    #future = client_fm.get_ticker('ONEUSDTM') #--> WORKED OK (except BTCUSDTM....)

    client_ft = Trade_Futures(key=API_Keys.KC_FUTURES['key'],
                              secret=API_Keys.KC_FUTURES['secret'],
                              passphrase=API_Keys.KC_FUTURES['passphrase'],
                              is_sandbox=API_Keys.KC_FUTURES['is_sandbox'],
                              url=API_Keys.KC_FUTURES['url'])

########################################################################

########################################################################
class actions:
    DoNothing = 0
    OpenHedge = 1       # Open Hedge Position (Buy S, Sell F)
    AddPosition = 2     # Add Position (Buy S, Sell F)
    CloseAll = 3        # Close All (Sell S, Buy F)

formatter_2d = "{0:.2f}"
formatter_5d = "{0:.5f}"
formatter_5d_pn = "{:+.5f}" # with +ve/-ve sign
formatter_3d_pn = "{:+.3f}" # with +ve/-ve sign
formatter_idx = "{:0>8d}"

########################################################################
#https://api-futures.kucoin.com/api/v1/ticker?symbol=XBTUSDM
#https://api-futures.kucoin.com/api/v1/level2/depth100?symbol=XBTUSDM
#https://api.kucoin.com/api/v1/symbols
#https://api-futures.kucoin.com/api/v1/contracts/active

def sound(type):
    if ARBATM_param.beep:
        if type == 'normal':
            #Normal
            winsound.Beep(frequency=440, duration=500)
        elif type == 'long':
            #Long Beep
            winsound.Beep(frequency=440, duration=1200)
        elif type == 'short':
            #Short Blip
            winsound.Beep(frequency=440, duration=100)
        elif type == 'shortlow':
            winsound.Beep(frequency=200, duration=100)
        elif type == 'high':
            #Add (+1)
            winsound.Beep(frequency=660, duration=500)
        elif type == 'low':
            #Subtract (-1)
            winsound.Beep(frequency=200, duration=500)


def proximity_in_orderbook(sym, sym_f,
                           buy_client, tgt_buy_price,
                           sell_client, tgt_sell_price,
                           variance_allowed_pct,
                           lotsize, num_f_contract, mode):
    ####################################################################################
    # Mode 1: Buy S, Sell F --> Hedge, Add
    # Mode 2: Sell S, Buy F --> Close All
    # Double check that OrderBook support desired execute price within allowed variance
    # "Support" is measured using:
    #           - weighted average in OB against
    #           - target buy/sell price
    #           - with pre-determined allowance
    # Allow +/- variance  (-ve Good, +ve NOT Good)
    ####################################################################################
    print("proximity_in_orderbook.........")
    asks_size_accum, asks_price_accum, ask_orderbook, diff_buy_pct,  asks_index, buy_sym  = 0, 0, '', 0, 0, ''
    bids_size_accum, bids_price_accum, bid_orderbook, diff_sell_pct, bids_index, sell_sym = 0, 0, '', 0, 0, ''
    #ask_buy_ok, bid_sell_ok = False, False
    proximity_short_txt, proximity_in_orderbook_txt = "", ""

    if mode == 1:
        proximity_in_orderbook_txt = "Buy-S, Sell-F (Mode 1):" + "\r\n" + "VarAllow:" + str(variance_allowed_pct) + "\r\n\r\n"
        buy_sym = sym
        sell_sym = sym_f
    else:
        proximity_in_orderbook_txt = "Buy-F, Sell-S (Mode 2):" + "\r\n" + "VarAllow:" + str(variance_allowed_pct) + "\r\n\r\n"
        buy_sym = sym_f
        sell_sym = sym

    api_retry_count = 0
    while api_retry_count < ARBATM_param.max_api_retry:
        try:
            if mode == 1:
                #Mode 1: Buy S, Sell F --> Hedge, Add
                ob_buy = buy_client.get_aggregated_orderv3(symbol=sym)      # Buy S
                ob_sell = sell_client.l2_order_book(symbol=sym_f)           # Sell F
            else:
                #Mode 2: Sell S, Buy F --> Subtract, Close All
                ob_buy = buy_client.l2_order_book(symbol=sym_f)             # Buy F
                ob_sell = sell_client.get_aggregated_orderv3(symbol=sym)    # Sell S
            break
        except:
            t.sleep(2)
            api_retry_count += 1
            print("ERROR (2)!!! when <proximity_in_orderbook:get_order_book>  " + " Attempt: " + str(api_retry_count))
            pass

    ##############################################
    # <<Buy Side>>: Mode 1: Buy S, Mode 2: Buy F
    ##############################################
    if mode == 1:
        size = lotsize
    else:
        size = num_f_contract
    while True:
        asks_size_accum = asks_size_accum + float(ob_buy['asks'][asks_index][1])
        asks_price_accum = asks_price_accum + (float(ob_buy['asks'][asks_index][0]) * float(ob_buy['asks'][asks_index][1])) # [0]=Price, [1]=Size
        ask_orderbook = ask_orderbook + \
                        str(asks_index).zfill(2) + ". " + \
                        "Price: " + str(ob_buy['asks'][asks_index][0]) + ", " + \
                        "Qty: " + formatter_2d.format(float(ob_buy['asks'][asks_index][1])) + "\r\n"
        if asks_size_accum > size:
            diff_buy_pct = ((asks_price_accum / asks_size_accum) - tgt_buy_price) / tgt_buy_price * 100
            # -ve Good, +ve NOT Good
            # -ve: avg. asks on OrderBook <cheaper> than target buy price
            # +ve: avg. asks on OrderBook <more expensive> than target buy price
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<Buy Side> (" + buy_sym + "):" + "\r\n" + \
                                         "TGT_BuyPrice: " + str(tgt_buy_price) + "\r\n" + \
                                         "TGT_BuyQty: " + str(size) + "\r\n" + \
                                         "<Order Book - Asks>:" + "\r\n" + ask_orderbook + \
                                         "*"*50 + "\r\n" + \
                                         "Takes " + str(asks_index) + " (0-base) asks to reach total of:" + "\r\n" + \
                                         "Qty: " + formatter_5d.format(asks_size_accum) + ", Cost: " + formatter_5d.format(asks_price_accum) + "\r\n" + \
                                         "Avg Price: " + formatter_5d.format(float(asks_price_accum/asks_size_accum)) + "\r\n" + \
                                         "(" + formatter_5d.format(float(asks_price_accum/asks_size_accum)) + " - " + str(tgt_buy_price) + ") / " + str(tgt_buy_price) + \
                                         ": diff = " + formatter_3d_pn.format(diff_buy_pct) + "%" + "\r\n" + \
                                         "*"*50 + "\r\n\r\n"
            break
        else:
            asks_index += 1

    ##################################################
    # <<Sell Side>>: Mode 1: Sell F, Mode 2: Sell S
    ##################################################
    if mode == 1:
        size = num_f_contract
    else:
        size = lotsize
    while True:
        bids_size_accum = bids_size_accum + float(ob_sell['bids'][bids_index][1])
        bids_price_accum = bids_price_accum + (float(ob_sell['bids'][bids_index][0]) * float(ob_sell['bids'][bids_index][1])) # [0]=Price, [1]=Size
        bid_orderbook = bid_orderbook + \
                        str(bids_index).zfill(2) + ". " + \
                        "Price: " + str(ob_sell['bids'][bids_index][0]) + ", " + \
                        "Qty: " + formatter_2d.format(float(ob_sell['bids'][bids_index][1])) + "\r\n"
        if bids_size_accum > size:
            diff_sell_pct = (tgt_sell_price - (bids_price_accum / bids_size_accum)) / tgt_sell_price * 100
            # -ve Good, +ve NOT Good
            # -ve: avg. bids on OrderBook <higher> than target sell price
            # +ve: avg. bids on OrderBook <lower> than target sell price
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<Sell Side> (" + sell_sym + "):" + "\r\n" + \
                                         "TGT_SellPrice: " + str(tgt_sell_price) + "\r\n" + \
                                         "TGT_SellQty: " + str(size) + "\r\n" + \
                                         "<Order Book - Bids>:" + "\r\n" + bid_orderbook + \
                                         "*"*50 + "\r\n" + \
                                         "Takes " + str(bids_index) + " (0-base) bids to reach total of:" + "\r\n" + \
                                         "Qty: " + formatter_5d.format(bids_size_accum) + ", Cost: " + formatter_5d.format(bids_price_accum) + "\r\n" + \
                                         "Avg Price: " + formatter_5d.format(float(bids_price_accum/bids_size_accum)) + "\r\n" + \
                                         "(" + str(tgt_sell_price) + " - " + formatter_5d.format(float(bids_price_accum/bids_size_accum)) + ") / " + str(tgt_sell_price) + \
                                         ": diff = " + formatter_3d_pn.format(diff_sell_pct) + "%" + "\r\n" + \
                                         "*"*50 + "\r\n\r\n"
            break
        else:
            bids_index += 1
    """
    ask_buy_ok = False
    if abs(diff_buy_pct) <= buy_variance_allowed_pct:
        ask_buy_ok = True
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks: " + formatter_3d_pn.format(diff_buy_pct) + "% within " + str(buy_variance_allowed_pct) + "% limit " + "\r\n\r\n"
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks: " + formatter_3d_pn.format(diff_buy_pct) + "% exceeded " + str(buy_variance_allowed_pct) + "% limit " + "\r\n\r\n"

    bid_sell_ok = False
    if abs(diff_sell_pct) <= sell_variance_allowed_pct:
        bid_sell_ok = True
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Sell / Bids: " + formatter_3d_pn.format(diff_sell_pct) + "% within " + str(sell_variance_allowed_pct) + "% limit " + "\r\n\r\n"
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Sell / Bids: " + formatter_3d_pn.format(diff_sell_pct) + "% exceeded " + str(sell_variance_allowed_pct) + "% limit " + "\r\n\r\n"


    if ask_buy_ok and bid_sell_ok:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Within Limit -- OK Proceed to order>>"
        proximity_short_txt = str(formatter_5d_pn.format(diff_buy_pct))  + "% within " + str(buy_variance_allowed_pct)  + "% Limit " + "(" + str(asks_index) + ")" + ", " + \
                              str(formatter_5d_pn.format(diff_sell_pct)) + "% within " + str(sell_variance_allowed_pct) + "% Limit " + "(" + str(bids_index) + ")" + " -- OK to Proceed"
    elif ask_buy_ok:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Limit Exceeded -- Do Not Proceed>>"
        proximity_short_txt = str(formatter_5d_pn.format(diff_buy_pct))  + "% within " + str(buy_variance_allowed_pct)  + "% Limit " + "(" + str(asks_index) + ")" + ", " + \
                              str(formatter_5d_pn.format(diff_sell_pct)) + "% exceed " + str(sell_variance_allowed_pct) + "% Limit " + "(" + str(bids_index) + ")" + " -- NOT OK"
    elif bid_sell_ok:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Limit Exceeded -- Do Not Proceed>>"
        proximity_short_txt = str(formatter_5d_pn.format(diff_buy_pct))  + "% exceed " + str(buy_variance_allowed_pct)  + "% Limit " + "(" + str(asks_index) + ")" + ", " + \
                              str(formatter_5d_pn.format(diff_sell_pct)) + "% within " + str(sell_variance_allowed_pct) + "% Limit " + "(" + str(bids_index) + ")" + " -- NOT OK"
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<<Limit Exceeded -- Do Not Proceed>>"
        proximity_short_txt = str(formatter_5d_pn.format(diff_buy_pct))  + "% exceed " + str(buy_variance_allowed_pct)  + "% Limit " + "(" + str(asks_index) + ")" + ", " + \
                              str(formatter_5d_pn.format(diff_sell_pct)) + "% exceed " + str(sell_variance_allowed_pct) + "% Limit " + "(" + str(bids_index) + ")" + " -- NOT OK"
    """
    if diff_buy_pct + diff_sell_pct <= variance_allowed_pct:
        proximity_short_txt = "Buy/Ask Diff (" + buy_sym + "):" + formatter_5d_pn.format(diff_buy_pct) + "%" + "\r\n" + \
                              "Sell/Bid Diff (" + sell_sym + "):" + formatter_5d_pn.format(diff_sell_pct) + "%" + "\r\n" + \
                              formatter_5d_pn.format(diff_buy_pct + diff_sell_pct) + "%: " + \
                              " within " + formatter_5d_pn.format(variance_allowed_pct) + "% Limit -- OK"
    else:
        proximity_short_txt = "Buy/Ask Diff (" + buy_sym + "):" + formatter_5d_pn.format(diff_buy_pct) + "%" + "\r\n" + \
                              "Sell/Bid Diff (" + sell_sym + "):" + formatter_5d_pn.format(diff_sell_pct) + "%" + "\r\n" + \
                              formatter_5d_pn.format(diff_buy_pct + diff_sell_pct) + "%: " + \
                              "exceeded " + formatter_5d_pn.format(variance_allowed_pct) + "% Limit -- NOT OK"

    proximity_in_orderbook_txt = proximity_in_orderbook_txt + proximity_short_txt
    #return ask_buy_ok and bid_sell_ok, proximity_in_orderbook_txt, proximity_short_txt
    return diff_buy_pct + diff_sell_pct <= variance_allowed_pct, proximity_in_orderbook_txt, proximity_short_txt


def market_order_hedge_add (sym, sym_f,
                            buy_client, tgt_buy_price,
                            sell_client, tgt_sell_price,
                            lotsize, num_f_contract):
    ##########################################
    # ** Place Market Orders **
    # Buy S, Sell F --> (+1) Hedge (F=S), Add (F>S)
    # Place Market and RollBack if necessary
    ##########################################
    id_buy, id_sell, id_sell2 = '', '', ''
    mission, place_market_order_txt = "", ""

    print('<market_order_hedge_add>:')
    print("Buy S: " + str(lotsize) + " " + sym)
    print("Sell F: " + str(num_f_contract) + " (contract, lot of" + str(lotsize_fcont) + ") " + sym_f)

    #######################
    # Part A: Buy SPOT
    # Qty: <lotsize>
    #######################
    try:
        # Buy Spot
        if ARBATM_param.order_type_s != "limit":
            id_buy = buy_client.create_market_order(sym, 'buy', size=lotsize, clientOid=API_Keys.clientOid)['orderId'] # This Actually work
        else:
            id_buy = buy_client.create_limit_order(symbol=sym, side='buy', price=tgt_buy_price, size=lotsize, clientOid=API_Keys.clientOid)['orderId']
    except:
        print("ERROR (3A)!!! when <place_market_order:create_market_order(BUY-S)> ")
        pass

    #######################
    # Part B: Sell FUTURES
    # Qty: <num_f_contract>
    #######################
    if id_buy != '':
        try:
            if ARBATM_param.order_type_f != "limit":
                id_sell = sell_client.create_market_order(symbol=sym_f, side='sell', lever=1, clientOid=API_Keys.clientOid, size=num_f_contract)['orderId'] # ACTUALLY WORK!!!!!
            else:
                id_sell = sell_client.create_limit_order (symbol=sym_f, side='sell', price=tgt_sell_price, lever=1, clientOid=API_Keys.clientOid, size=num_f_contract)['orderId']  # ACTUALLY WORK!!!!!
        except:
            print("ERROR (3B)!!! when <place_market_order:create_market_order(SELL " + str(num_f_contract) + " F)> ")
            pass

    ##############################################
    # Part C: Sell SPOT IMMEDIATELY,
    #         Sell FUTURES <failed>
    # Qty: <lotsize>
    ##############################################
    if id_buy != '' and id_sell == '':
        t.sleep(ARBATM_param.ts_order_fill_gap)
        #s_order = buy_client.get_order_details(orderId=id_buy)
        try:
            # Bought S Successful, Sell F Failed, Sell S (close IMMEDIATELY!!)
            #id_sell2 = buy_client.create_market_order(sym, 'sell', size=lotsize)
            id_sell2 = buy_client.create_market_order(symbol=sym, side='sell', size=buy_client.get_order_details(orderId=id_buy)['size'], clientOid=API_Keys.clientOid)
        except:
            print("ERROR (3C)!!! when <place_market_order:create_market_order(SELL " + str(lotsize) + " S: due to SELL-F Failed)> ")
            pass

    mission = "Mission: (Hedge / Add)" + "\r\n" + \
              "<market_order_hedge_add>" + "\r\n" + \
              "Buy " + str(lotsize) + " " + sym + "@ " + str(tgt_buy_price) + "\r\n" + \
              "Sell " + str(num_f_contract) + " " + sym_f + f_lot_size_txt + "@ " + str(tgt_sell_price)

    place_market_order_txt = sym + " / " + sym_f + "\r\n\r\n" + \
                             "Buy-S ID: " + str(id_buy) + "\r\n" + \
                             "Sell-F ID: " + str(id_sell) + "\r\n" + \
                             "Sell-S2(Rev) ID: " + str(id_sell2) + "\r\n\r\n"

    if id_buy != '' and id_sell != '':
        place_market_order_txt = place_market_order_txt + "Both Buy-S <Successful>, Sell-F <Successful>"
    elif id_sell == '' and id_sell2 != '':
        place_market_order_txt = place_market_order_txt + "Buy-S <OK>, Sell-F <Failed>" + "\r\n"
        place_market_order_txt = place_market_order_txt + "Sell-F_2 <Reversed Buy-S (Sell) OK>"
    elif id_sell == '' and id_sell2 == '':
        place_market_order_txt = place_market_order_txt + "Buy-S <OK>, Sell-F <Failed>" + "\r\n"
        place_market_order_txt = place_market_order_txt + "Sell-F_2 <Reversed Buy-S (Sell) Failed>"
    else:
        place_market_order_txt = place_market_order_txt + "Buy-S <Failed>, Sell-F <Not Executed>"

    #return list is [0] based
    return id_buy != '' and id_sell != '', \
           id_buy, id_sell, id_sell2, \
           mission, place_market_order_txt


def market_order_subtract (sym, sym_f,
                           buy_client, tgt_buy_price,
                           sell_client, tgt_sell_price,
                           lotsize, num_f_contract):
    ##########################################
    # ** Place Market Orders **
    # Buy F, Sell S --> Subtract (-1) (F<S)
    # Place Market and RollBack if necessary
    ##########################################
    id_buy, id_sell, id_sell2 = '', '', ''
    mission, place_market_order_txt = "", ""

    print('<market_order_subtract (-1)>:')
    print("Buy F: " + str(num_f_contract) + " (contract, lot of" + str(lotsize_fcont) + ") " + sym_f)
    print("Sell S: " + str(lotsize) + " " + sym)

    #######################
    # Part A: Buy FUTURES
    # Qty: <num_f_contract>
    #######################
    try:
        # Buy Futures
        #id_buy = buy_client.create_market_order (sym, 'buy', size=lotsize)['orderId'] # This Actually work
        if ARBATM_param.order_type_f != "limit":
            id_buy = buy_client.create_market_order(symbol=sym_f, side='buy', lever=1, clientOid=API_Keys.clientOid,
                                                    size=num_f_contract)['orderId']  # ACTUALLY WORK!!!!!
        else:
            id_buy = buy_client.create_limit_order(symbol=sym_f, side='buy', price=tgt_buy_price, lever=1,
                                                   clientOid=API_Keys.clientOid, size=num_f_contract)['orderId']  # ACTUALLY WORK!!!!!
        #print ("Buy Simulatino")
        #break
    except:
        #print("ERROR (4A)!!! when <market_order_subtract:create_market_order(BUY-F)> ")
        print("ERROR (4A)!!! when <market_order_subtract(-1):create_market_order(BUY " + str(num_f_contract) + " F)> ")
        pass
    #print ("(Part A) Buy-S:", id_buy)

    #sys.exit()
    #######################
    # Part B: Sell Spot
    # Qty: <lotsize>
    #######################
    if id_buy != '':
        try:
            if ARBATM_param.order_type_s != "limit":
                id_sell = sell_client.create_market_order (sym, 'sell', size=lotsize, clientOid=API_Keys.clientOid)['orderId'] # This Actually work
            else:
                id_sell = sell_client.create_limit_order(symbol=sym, side='sell', price=tgt_sell_price, size=lotsize,
                                                         clientOid=API_Keys.clientOid)['orderId']
            #id_sell = sell_client.create_market_order(symbol=sym_f, side='sell', lever=1, clientOid=API_Keys.clientOid, size=num_f_contract)['orderId'] # ACTUALLY WORK!!!!!
            # {'orderId': '61e82f61ac21e400010905d3'}
            #break
        except:
            print("ERROR (4B)!!! when <market_order_subtract(-1):create_market_order(Sell-S)> ")
            pass
    #print("(Part B) Sell-F:", id_sell)

    ##############################################
    # Part C: Sell FUTURES IMMEDIATELY,
    #         Sell SPOT <failed>
    # Qty: <num_f_contract>
    ##############################################
    if id_buy != '' and id_sell == '':
        try:
            # Bought S Successful, Sell F Failed, Sell S (close IMMEDIATELY!!)
            # id_sell2 = buy_client.create_market_order(sym, 'sell', size=lotsize)
            #id_sell2 = buy_client.create_market_order(sym, 'sell', size=buy_client.get_order_details(orderId=id_buy)['size'], clientOid=API_Keys.clientOid)
            #id_sell2 = buy_client.create_market_order(symbol=sym_f, side='sell', lever=1, clientOid=API_Keys.clientOid,
            #                                          size=num_f_contract)['orderId']
            id_sell2 = buy_client.create_market_order(symbol=sym_f, side='sell', lever=1, clientOid=API_Keys.clientOid,
                                                      size=buy_client.get_order_details(orderId=id_buy)['size'])['orderId']
        except:
            print("ERROR (4C)!!! when <market_order_subtract(-1):create_market_order(SELL " + str(num_f_contract) + " F: due to SELL-S Failed))> ")
            #print("ERROR (4C)!!! when <market_order_subtract:create_market_order(SELL " + str(lotsize) + " S: due to SELL-F Failed)> ")
            pass

    mission = "Mission: (Subtract)" + "\r\n" + \
              "<market_order_subtract>" + "\r\n" + \
              "Buy " + str(num_f_contract) + sym_f + f_lot_size_txt + "@ " + str(tgt_buy_price) + "\r\n" + \
              "Sell " + str(lotsize) + " " + sym + " @ " + str(tgt_sell_price)

    place_market_order_txt = sym + " / " + sym_f + "\r\n\r\n" + \
                             "Buy-F ID: " + str(id_buy) + "\r\n" + \
                             "Sell-S ID: " + str(id_sell) + "\r\n" + \
                             "Sell-F2(Rev) ID: " + str(id_sell2) + "\r\n\r\n"

    if id_buy != '' and id_sell != '':
        place_market_order_txt = place_market_order_txt + "Both Buy-F <Successful>, Sell-S <Successful>"
    elif id_sell == '' and id_sell2 != '':
        place_market_order_txt = place_market_order_txt + "Buy-F <OK>, Sell-S <Failed>" + "\r\n"
        place_market_order_txt = place_market_order_txt + "Sell-F_2 <Reversed Buy-F (Sell) OK>"
    elif id_sell == '' and id_sell2 == '':
        place_market_order_txt = place_market_order_txt + "Buy-F <OK>, Sell-S <Failed>" + "\r\n"
        place_market_order_txt = place_market_order_txt + "Sell-F_2 <Reversed Buy-F (Sell) Failed>"
    else:
        place_market_order_txt = place_market_order_txt + "Buy-F <Failed>, Sell-F <Not Executed>"

    #return list is [0] based
    return id_buy != '' and id_sell != '', \
           id_sell, id_buy, id_sell2, \
           id_sell, id_buy, id_sell2, \
           mission, place_market_order_txt


def market_order_closeAll (sym, sym_f,
                           sell_client, tgt_sell_price,
                           buy_client, tgt_buy_price,
                           lotsize, num_f_contract, num_pos):
    #order = market_order_closeAll(sym, sym_f,
    #                              client_st, spot_price,
    #                              client_ft, future_price,
    #                              ARBATM_param.lotsize * num_pos, int(equiv_num_fcont) * num_pos)
    ##########################################
    # ** Place Market Orders (Close All) **
    # Sell S,  Buy F --> Close All
    ##########################################
    id_buy, id_sell = '', ''
    print('<market_order_closeAll>:')
    print("Sell S: " + str(lotsize * num_pos) + " " +
          "(" + str(lotsize) + "*" + str(num_pos) + ")" + " " + sym)
    print("Buy F: " + str(num_f_contract * num_pos) + f_lot_size_txt +
          "(" + str(num_f_contract) + "*" + str(num_pos) + ") " + sym_f)
    mission, market_order_closeAll_txt = "", "market_order_closeAll_txt" + "\r\n"

    #######################
    # Part A: Sell SPOT
    # Qty: <lotsize>
    #######################
    try:
        print ('<market_order_closeAll>: Try to sell ' + str(lotsize) + ' ' + sym)
        if ARBATM_param.order_type_s != "limit":
            id_sell = sell_client.create_market_order(sym, 'sell', size=lotsize)['orderId']
        else:
            id_sell = sell_client.create_limit_order(symbol=sym, side='sell', price=tgt_sell_price, size=lotsize, clientOid=API_Keys.clientOid)['orderId']
    except:
        print("ERROR (5A)!!! when <market_order_closeAll:create_market_order(SELL-S)> ")
        #sys.exit()
        pass

    #######################
    # Part B: Buy FUTURES
    # Qty: <num_f_contract>
    #######################
    if id_sell != '':
        try:
            print(',market_order_closeAll.: Try to buy back ' + str(num_f_contract) + ' ' + sym_f)
            if ARBATM_param.order_type_f != "limit":
                id_buy = buy_client.create_market_order(symbol=sym_f, side='buy', lever=1, clientOid=API_Keys.clientOid, size=num_f_contract)['orderId']
            else:
                id_buy = buy_client.create_limit_order(symbol=sym_f, side='buy', price=tgt_buy_price, lever=1,
                                                       clientOid=API_Keys.clientOid, size=num_f_contract)['orderId']  # ACTUALLY WORK!!!!!
        except:
            print("ERROR (5B)!!! when <place_market_order:create_market_order(SELL-F)> ")
            pass

    mission = "Mission (Close All): " + "\r\n" + \
              "<market_order_closeAll>" + "\r\n" + \
              "Buy Back " + str(num_f_contract) + sym_f + f_lot_size_txt + "@ " + str(tgt_sell_price) + "\r\n" + \
              "Sell " + str(lotsize) + " " + sym + " @ " + str(tgt_buy_price) + "\r\n"

    market_order_closeAll_txt = sym_f + " / " + sym + "\r\n\r\n" + \
                             "Sell-S ID: " + str(id_sell) + "\r\n" + \
                             "Buy-F ID:  " + str(id_buy) + "\r\n\r\n"
    if id_sell != '' and id_buy != '':
        market_order_closeAll_txt = market_order_closeAll_txt + "Both Sell-S <Successful>, BuyBack-F <Successful>" + "\r\n"
    elif id_buy == '':
        market_order_closeAll_txt = market_order_closeAll_txt + "Sell-S <Successful>, BuyBack-F <Failed>" + "\r\n"
    else:
        market_order_closeAll_txt = market_order_closeAll_txt + "Sell-S <Failed>, Sell-F <Not Executed>"

    # return list is [0] based
    return id_buy != '' and id_sell != '', \
           id_sell, id_buy, \
           mission, market_order_closeAll_txt


def order_status_review(orderId_s, orderId_f, orderId_rev,
                        lotsize, num_f_contract, mode):

    ttl_s, fee_s, index_s, slept_cnt_s, s_txt = 0, 0, 0, 0, ''
    ttl_f, fee_f, index_f, slept_cnt_f, f_txt = 0, 0, 0, 0, ''
    gross_pl, net_pl, order_review_txt = 0, 0, ''

    #print("order_status_review: wait " + str(ARBATM_param.ts_order_fill_gap) + "sec")
    #print("Spot: " + orderId_s)
    #print("Futures: " + orderId_f)

    t.sleep(ARBATM_param.ts_order_fill_gap)

    ########################################################
    # Part A-1: Sleep until Spot-order is no-longer Active
    ########################################################
    print("Review - BEFORE A1 - Sleep")
    s_order = client_st.get_order_details(orderId=orderId_s) # '61e8df144b81fa00012b3c62'
    while s_order['isActive']:
        slept_cnt_s += 1
        print (orderId_s + ": sleep " + str(slept_cnt_s))
        t.sleep(15)
        s_order = client_st.get_order_details(orderId=orderId_s)
    s_txt = '<' + s_order['side'].upper() + ' SPOT: ' + s_order['symbol'] + ": " + " " + str(s_order['size']) + '>' + "\r\n" + \
            'orderId: ' + s_order['id'] + " (" + s_order['type'] + ")" + "\r\n"
    print("Review - Finished A1 - Sleep")
    ########################################################
    # Part A-2: Get total Spot-order price, size, and fees
    ########################################################
    print("Review - BEFORE A2")
    s_order = client_st.get_fill_list(tradeType='TRADE')['items']  # Either TRADE or MARGIN_TRADE, #24hrs
    fills = list(filter(lambda filled_entry: filled_entry['orderId'] == orderId_s, s_order))  # [1]['price']
    if len(fills) == 0:
        return 0, "S Not Found"
    for entry in fills: #Each Fills can be in multiple entries
        s_txt = s_txt + str(index_s).zfill(2) + ". " + \
                           "Side: " + entry['side'].upper() + ": " + \
                           "Price: " + str(float(entry['price'])) + ", " + \
                           "Qty: " + str(float(entry['size'])) + ", " + \
                           "Fees: " + str(float(entry['fee'])) + "\r\n"
        ttl_s = ttl_s + (float(entry['price']) * float(entry['size']))
        fee_s = fee_s + float(entry['fee'])
        index_s += 1
    s_txt = s_txt + "Total (S): " + formatter_5d_pn.format(ttl_s) + "\r\n" + \
            "Fees (S): " + formatter_5d_pn.format(fee_s) + " (" + formatter_2d.format(fee_s/ttl_s*100) + "%)"

    print("Review - Finished A2")
    ########################################################
    # Part B-1: Sleep until Futures-order is no-longer Active
    ########################################################
    print("Review - BEFORE B1 - Sleep")
    f_order = client_ft.get_order_details(orderId=orderId_f)
    while f_order['isActive']:
        slept_cnt_f += 1
        print (orderId_f + ": sleep " + str(slept_cnt_f))
        t.sleep(15)
        f_order = client_ft.get_order_details(orderId=orderId_f)
    f_txt = '<' + f_order['side'].upper() + ' Futures: ' + f_order['symbol'] + ": " + " " + str(f_order['size']) + f_lot_size_txt + '>' + "\r\n" + \
            'orderId: ' + f_order['id'] + " (" + f_order['type'] + ")" + "\r\n"

    print("Review - Finished B1 - Sleep")
    ########################################################
    # Part B-2: Get total Futures-order price, size, and fees
    ########################################################
    print("Review - BEFORE B2")
    f_order = client_ft.get_recent_fills()
    fills = list(filter(lambda filled_entry: filled_entry['orderId'] == orderId_f, f_order))  # [1]['price']
    if len(fills) == 0:
        return 0, "F Not Found"
    for entry in fills:  # Each Fills can be in multiple entries
        f_txt = f_txt + str(index_f).zfill(2) + ". " + \
                "Side: " + entry['side'].upper() + ": " + \
                "Price: " + str(float(entry['price'])) + ", " + \
                           "Qty: " + str(float(entry['size'])) + " (mul:" + str(f_multiplier) + ")" + ", " + \
                           "Fees: " + str(float(entry['fee'])) + "\r\n"
        ttl_f = ttl_f + (float(entry['price']) * float(entry['size'] * int(f_multiplier)))
        fee_f = fee_f + float(entry['fee'])
        index_f += 1
    f_txt = f_txt + "Total (F): " + formatter_5d_pn.format(ttl_f) + "\r\n" + \
            "Fees (F): " + formatter_5d_pn.format(fee_f) + " (" + formatter_2d.format(fee_f/ttl_f*100) + "%)"

    print("Review - Finished B2")

    if mode==1:
        #Buy S, Sell F
        gross_pl = ttl_f - ttl_s
        net_pl = ttl_f - ttl_s - fee_s - fee_f
        order_review_txt = s_txt + "\r\n\r\n" + \
                           f_txt + "\r\n\r\n" + \
                           "Gross: " + formatter_5d.format(gross_pl) + "\r\n" + \
                           "Net: " + formatter_5d.format(net_pl)
    else:
        #Buy F, Sell S
        gross_pl = ttl_s - ttl_f
        net_pl = ttl_s - ttl_f - fee_s - fee_f # * lotsize_fcont # DOUBLE CHECK
        order_review_txt = f_txt + "\r\n\r\n" + \
                           s_txt + "\r\n\r\n" + \
                           "Gross: " + formatter_5d.format(gross_pl) + "\r\n" + \
                           "Net: " + formatter_5d.format(net_pl)

    print("order_review_txt::::: " + order_review_txt)
    return gross_pl, net_pl, order_review_txt

delta_dict = {
    "idx": [],
    "lt": [],
    "delta": []
}


########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################
########################################################################################################################

# Get Parameters from ARBATM_param
symbol = ARBATM_param.symbol
sym, sym_f = symbol+"-USDT", symbol+"USDTM"
lotsize = ARBATM_param.lotsize
equiv_num_fcont, lotsize_fcont = 0, 0

###################################################
# Get Corresponding Futures Multiplier (Lot size)
# <Stop> if mismatch
###################################################
all_open_contract = client_fm.get_contracts_list()
#contract = [open_contract for open_contract in all_open_contract if open_contract['symbol'] == sym_f] # --> Also Work, but use lambda
#print ("LotSize: " + str(list(filter(lambda open_contract: open_contract['symbol'] == sym_f, all_open_contract))[0]['lotSize']))
#print ("Multiplier: " + str(list(filter(lambda open_contract: open_contract['symbol'] == sym_f, all_open_contract))[0]['multiplier']))

f_min_lot = list(filter(lambda open_contract: open_contract['symbol'] == sym_f, all_open_contract))[0]['lotSize']
f_multiplier = list(filter(lambda open_contract: open_contract['symbol'] == sym_f, all_open_contract))[0]['multiplier']
print ("Min Lot Size: " + str(f_min_lot))
print ("Multiplier: " + str(f_multiplier))
print ("MOD: " + str(float(ARBATM_param.lotsize) % float(f_multiplier)))

print("equiv_num_fcont: " + str(float(ARBATM_param.lotsize) / float(f_multiplier)))
if equiv_num_fcont % 1 == 0:
    print ("proceed")

#if float(ARBATM_param.lotsize) % float(f_lot_size) != 0:
#if float(ARBATM_param.lotsize) < float(f_min_lot) or float(ARBATM_param.lotsize) % float(f_multiplier) != 0:
if float(ARBATM_param.lotsize) < float(f_min_lot) or equiv_num_fcont % 1 != 0:
    print ('Invalid Lot Size to multiplier')
    print(str(ARBATM_param.lotsize) + ' ' + sym + ' = ' +
          str(float(ARBATM_param.lotsize) / float(f_multiplier)) + ' ' + sym_f + ' futures contracts')
    sys.exit()
else:
    #lotsize_fcont = f_multiplier
    equiv_num_fcont = float(ARBATM_param.lotsize) / float(f_multiplier)
    print(str(ARBATM_param.lotsize) + ' ' + sym + ' = ' + \
          str(equiv_num_fcont) + ' (multiplier:' + str(float(f_multiplier)) + ') ' + sym_f + ' futures contracts')

f_lot_size_txt = " (" + str(equiv_num_fcont) + " contract, mult: " + str(f_multiplier) + ") "
print ("OK to Proceed:")
print (f_lot_size_txt)
# For 500 ONE:
# equiv_num_fcont = 50
# lotsize_fcont = 10


#print("Num Contract: " + str(equiv_num_fcont))
#sys.exit()

#id_buy = buy_client.create_limit_order(symbol=sym, price=tgt_buy_price, size=lotsize, clientOid=API_Keys.clientOid)['orderId']
#id_buy = client_st.create_limit_order(symbol=sym, side='buy', price=0.12, size=equiv_num_fcont, clientOid=API_Keys.clientOid)['orderId']
#print (id_buy)
#sys.exit()

##################################################
# THIS IS WEIRD, USE SAME NUMBER FOR FUTURES INSTEAD
# OF DIVIDING BY THE "MULTIPLIER"
#equiv_num_fcont = ARBATM_param.lotsize
##################################################

probe_idx = 2
delta, delta_pct = 0, 0
max_delta_pct, min_delta_pct, zero_delta_pct = 0, 0, 1000
num_pos, num_order_attempted, num_order_placed, num_cycle = 0, 0, 0, 0
start_dt = datetime.fromtimestamp(int(t.time()))
tgt_pl_g, tgt_pl_n, actual_pl_g, actual_pl_n = 0, 0, 0, 0
#f_fee_discount, s_fee_discount = 0.9994, 0.999
f_fee_rate, s_fee_rate = 0.06, 0.1

condition = ""
state_text = "0: Look for <Hedge>"
ob_text = ""
review_text = ""

if ARBATM_param.output_to_gsheet:
    file_ws_name = ARBATM_param.exchange + "_" + symbol + "_" +  str(start_dt)
    tup1 = ("Index", "Local-Time",
            "OrderPlaced",
            "F_TimeStamp", "F_Price$",
            "S_TimeStamp", "S_Price$",
            "F-S_TimeStamp", "F-S_$", "(F-S)/S_%",
            "Condition", "Evaluation",
            "Num_Cycle", "Num_Order_Placed", "Num_Pos",
            "OrderBook (proxim)", "Mission", "Order Status",
            "Review",
            "Target_GP", "Target_NP", "Actual_GP", "Actual_NP")

###################################
# Output to CSV File - Header
###################################
#if ARBATM_param.output_to_csv:
    #f = open(file_ws_name.replace(":","-") + ".csv", "a", newline="")
    #f.truncate(0)
    #writer = csv.writer(f)
    #writer.writerow(tup1)
#    f = open(ARBATM_param.exchange + "_orders_" + ".csv", "a", newline="")
#    writer = csv.writer(f)

###################################
# Output to Google Sheet - Header
###################################
file_ws_name = ARBATM_param.exchange + "_" + symbol + "_" +  str(start_dt)
if ARBATM_param.output_to_gsheet:
    gsheet.rename_worksheet(file_ws_name)
    gsheet.set_current_ws(file_ws_name)
    gsheet.clean()
    gsheet.freeze(2)
    gsheet.write_cell(1, 1,
                      "Started On: " + str(start_dt) + "\r\n" +
                      "Simulation Mode: " + str(ARBATM_param.simulation_mode) + "\r\n\r\n" +
                      "Exchange: " + ARBATM_param.exchange + "\r\n" +
                      "Sandbox: " + str(ARBATM_param.use_sandbox) + "\r\n" +
                      "Spot: " + sym + "\r\n" +
                      "Futures: " + sym_f + "\r\n" +
                      "Lot Size: " + str(lotsize) + " / " + f_lot_size_txt + "\r\n" +
                      "Order Type (S): " + ARBATM_param.order_type_s + "\r\n" +
                      "Order Type (F): " + ARBATM_param.order_type_f + "\r\n\r\n" +
                      "Parameters:" + "\r\n" +
                      "F/S Time Diff Allow: " + str(ARBATM_param.ts_var_allow_sec) + " seconds" + "\r\n" +
                      "Hedge (F=S): " + str(ARBATM_param.hedge_bottom) + " to " + str(ARBATM_param.range_top) + "%" + "\r\n" +
                      "Add (F>=S): " + str(ARBATM_param.range_top) + "%" + "\r\n" +
                      "Subtract (F=S): " + str(ARBATM_param.range_bottom) + " to " + str(ARBATM_param.subtract_top) + "%" + "\r\n" +
                      "Close All (F<=S): " + str(ARBATM_param.range_bottom) + "%")
    gsheet.write_cell(1, 20, '=sum(T3:T)') #T
    gsheet.write_cell(1, 21, '=sum(U3:U)') #U
    gsheet.write_cell(1, 22, '=sum(V3:V)') #V
    gsheet.write_cell(1, 23, '=sum(W3:W)') #W
    tup1 = ("Index", "Local-Time",
            "OrderPlaced",
            "F_TimeStamp", "F_Price$",
            "S_TimeStamp", "S_Price$",
            "F-S_TimeStamp", "F-S_$", "(F-S)/S_%",
            "Condition", "Evaluation",
            "Num_Cycle", "Num_Order_Placed", "Num_Pos",
            "OrderBook (proxim)", "Mission", "Order Status",
            "Review",
            "Target_GP", "Target_NP", "Actual_GP", "Actual_NP")
    gsheet.write_tuple(2, tup1)
    #gsheet.write_tuple(num_order_placed + 2, tup1)

#############
# Main Body #
#############
run = True
while run:
    t.sleep(0)
    local_dt = datetime.fromtimestamp(int(t.time()))

    api_retry_count = 0
    while api_retry_count < ARBATM_param.max_api_retry:
        ########################
        # Get S/F ticker price #
        ########################
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

    ts_diff = (future_dt - spot_dt).total_seconds()
    if abs(ts_diff) <= ARBATM_param.ts_var_allow_sec:
        ts_within_allowance = True
        ts_diff_txt = str(formatter_5d_pn.format(ts_diff)) + "sec is within +/-" + str(ARBATM_param.ts_var_allow_sec) + "sec limit"

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

    else:
        ts_within_allowance = False
        ts_diff_txt = str(formatter_5d_pn.format(ts_diff)) + "sec exceeded +/-" + str(ARBATM_param.ts_var_allow_sec) + "sec limit"
        condition = 'Void (Time-Delta exceeded limit)'

#    delta_dict['idx'].append(probe_idx)
#    delta_dict['lt'].append(local_dt)
#    delta_dict['delta'].append(delta_pct)
#    plt.plot(delta_dict['lt'], delta_dict['delta'], label="delta_ts")
#    plt.draw()

#    delta_dict['idx'].append(probe_idx)
#    delta_dict['lt'].append(local_dt)
#    delta_dict['delta'].append(delta_pct)

    #ani = FuncAnimation(plt.gcf(), animate, 1000)
    #plt.tight_layout()
    #plt.show()

    proximity_text = ""
    order_text = ""
    mission = ""
    order_placed = "--"
    order_attempted = False

    if num_pos == 0 and \
        delta_pct >= ARBATM_param.hedge_bottom and \
        delta_pct < ARBATM_param.range_top and \
        ts_within_allowance:
        #############################
        # Try to: Open Hedge Position
        #############################
        eval = "Open Hedge" + "\r\n" + \
               "1: NumPos = " + str(num_pos) + "\r\n" + \
               "2: " + ts_diff_txt + "\r\n" + \
               "3: Delta_Pct:" + str(formatter_5d_pn.format(delta_pct)) + "% is between " + str(formatter_3d_pn.format(ARBATM_param.hedge_bottom)) + "% and " + str(formatter_3d_pn.format(ARBATM_param.range_top)) + "%"
        num_order_attempted += 1
        order_attempted = True
        sound('short')
#        proceed = proximity_in_orderbook(sym, sym_f,
#                                         client_sm, spot_price, ARBATM_param.ob_var_allow_pct,
#                                         client_fm, future_price, ARBATM_param.ob_var_allow_pct,
#                                         ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)
        proceed = proximity_in_orderbook(sym, sym_f,
                                         client_sm, spot_price,
                                         client_fm, future_price,
                                         delta_pct - ARBATM_param.hedge_bottom,
                                         ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)

        ob_text, proximity_text = proceed[1], proceed[2]
        if (proceed[0] == False):
            sound('shortlow') #OB Fail
        else:
            sound('normal')
            tgt_pl_g = (future_price - spot_price) * ARBATM_param.lotsize #Buy S, Sell F
            tgt_pl_n = tgt_pl_g - (future_price*f_fee_rate + spot_price*s_fee_rate) / 100 * ARBATM_param.lotsize
            ###############################
            # ***<<Place HEDGE Order>>*** #
            ###############################
            order_success = False
            if not ARBATM_param.simulation_mode:
                order = market_order_hedge_add(sym, sym_f,
                                               client_st, spot_price,
                                               client_ft, future_price,
                                               ARBATM_param.lotsize, int(equiv_num_fcont))
                order_success, mission, order_text = order[0], order[4], order[5]

                if order_success:
                    state_text = "1: <Hedged>, Look for Add / Close-All"
                    review = order_status_review(order[1], order[2], order[3],
                                                 ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)
                    review_text = "Target PL: " + str(tgt_pl_g) + "\r\n\r\n" + review[2]
                    actual_pl_g, actual_pl_n = review[0], review[1]
                    ###set var###############
                    num_pos += 1
                    order_placed = "Hedged"
                    num_order_placed += 1
                    ##########################
            else:
                state_text = "1: <Hedged>, Look for Add / Close-All"
                order_success, mission, order_text = True, "", ""   # Always Success in Simulation Mode
                review_text = "SIMULATION MODE" + "\r\n" + "Target PL: " + str(tgt_pl_g) + "\r\n\r\n" + "Simulation Mode"
                actual_pl_g, actual_pl_n = 0, 0

    elif num_pos >= 1 and num_pos < ARBATM_param.max_pos_allow and \
            delta_pct >= ARBATM_param.range_top and \
            ts_within_allowance:
        ########################
        # Try to: Add Position (+1)
        ########################
        eval = "Add Position (+1)" + "\r\n" + \
               "1: NumPos = " + str(num_pos) + "\r\n" + \
               "2: " + ts_diff_txt + "\r\n" + \
               "3: Delta_Pct:" + str(formatter_3d_pn.format(delta_pct)) + "% >= " + str(formatter_3d_pn.format(ARBATM_param.range_top)) + "%"
        num_order_attempted += 1
        order_attempted = True
        sound('short')
#        proceed = proximity_in_orderbook(sym, sym_f,
#                                         client_sm, spot_price, ARBATM_param.ob_var_allow_pct,
#                                         client_fm, future_price, ARBATM_param.ob_var_allow_pct,
#                                         ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)
        proceed = proximity_in_orderbook(sym, sym_f,
                                         client_sm, spot_price,
                                         client_fm, future_price,
                                         delta_pct - ARBATM_param.range_top,
                                         ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)

        ob_text, proximity_text = proceed[1], proceed[2]
        if (proceed[0] == False):
            sound('shortlow')  # OB Fail
        else:
            sound('high') #(+1)
            tgt_pl_g = (future_price - spot_price) * ARBATM_param.lotsize #Buy S, Sell F
            tgt_pl_n = tgt_pl_g - (future_price*f_fee_rate + spot_price*s_fee_rate) / 100 * ARBATM_param.lotsize
            ###############################
            #  ***<<Place ADD Order>>***  #
            ###############################
            order_success = False
            if not ARBATM_param.simulation_mode:
                order = market_order_hedge_add(sym, sym_f,
                                               client_st, spot_price,
                                               client_ft, future_price,
                                               ARBATM_param.lotsize, int(equiv_num_fcont))
                order_success, mission, order_text = order[0], order[4], order[5]
                if order_success:
                    state_text = "2: <Added> (+1), Look for Add / Subtract / Close-All"
                    review = order_status_review(order[1], order[2], order[3],
                                                 ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)
                    review_text = "Target PL: " + str(tgt_pl_g) + "\r\n\r\n" + review[2]
                    actual_pl_g, actual_pl_n = review[0], review[1]
                    ###set var###############
                    num_pos += 1
                    order_placed = "Added"
                    num_order_placed += 1
                    #########################
            else:
                state_text = "2: <Added> (+1), Look for Add / Subtract / Close-All"
                order_success, mission, order_text = True, "", ""  # Always Success in Simulation Mode
                review_text = "SIMULATION MODE" + "\r\n" + "Target PL: " + str(tgt_pl_g) + "\r\n\r\n" + "Simulation Mode"
                actual_pl_g, actual_pl_n = 0, 0

    elif num_pos >= 2 and \
            delta_pct <= ARBATM_param.subtract_top and \
            delta_pct > ARBATM_param.range_bottom and \
            ts_within_allowance:
        ########################
        # Try to: Subtract Position (-1)
        # F=S and already has added position
        ########################
        eval = "Subtract Position (-1)" + "\r\n" + \
               "1: NumPos = " + str(num_pos) + "\r\n" + \
               "2: " + ts_diff_txt + "\r\n" + \
               "3: Delta_Pct:" + str(formatter_5d_pn.format(delta_pct)) + "% is between " + str(formatter_3d_pn.format(ARBATM_param.range_bottom)) + "% and " + str(formatter_3d_pn.format(ARBATM_param.subtract_top)) + "%"
        num_order_attempted += 1
        order_attempted = True
        sound('short')
#        proceed = proximity_in_orderbook(sym, sym_f,
#                                         client_fm, future_price, ARBATM_param.ob_var_allow_pct,
#                                         client_sm, spot_price, ARBATM_param.ob_var_allow_pct,
#                                         ARBATM_param.lotsize, int(equiv_num_fcont), mode=2)
        proceed = proximity_in_orderbook(sym, sym_f,
                                         client_fm, future_price,
                                         client_sm, spot_price,
                                         abs(delta_pct - ARBATM_param.subtract_top),
                                         ARBATM_param.lotsize, int(equiv_num_fcont), mode=2)
        ob_text, proximity_text = proceed[1], proceed[2]
        if (proceed[0] == False):
            sound('shortlow')  # OB Fail
        else:
            sound('low') #(-1)
            #tgt_pl_g = (future_price - spot_price) * ARBATM_param.lotsize
            tgt_pl_g = (spot_price - future_price) * ARBATM_param.lotsize #Sell S, Buy F
            tgt_pl_n = tgt_pl_g - (future_price*f_fee_rate + spot_price*s_fee_rate) / 100 * ARBATM_param.lotsize
            ####################################
            #  ***<<Place SUBTRACT Order>>***  #
            ####################################
            order_success = False
            if not ARBATM_param.simulation_mode:
                order = market_order_subtract(sym, sym_f,
                                              client_ft, future_price,
                                              client_st, spot_price,
                                              ARBATM_param.lotsize, int(equiv_num_fcont))
                order_success, mission, order_text = order[0], order[4], order[5]
                if order_success:
                    state_text = "3: <Subtracted (-1)>, Look for Add / Subtract (if numpos still > 1)/ Close-All"
                    review = order_status_review(order[1], order[2], order[3],
                                                 int(equiv_num_fcont), ARBATM_param.lotsize, mode=2)
                    review_text = "Target PL: " + str(tgt_pl_g) + "\r\n\r\n" + review[2]
                    actual_pl_g, actual_pl_n = review[0], review[1]
                    ###set var###############
                    num_pos -= 1
                    order_placed = "Subtracted"
                    num_order_placed += 1
                    #########################
            else:
                state_text = "3: <Subtracted (-1)>, Look for Add / Subtract (if numpos still > 1)/ Close-All"
                order_success, mission, order_text = True, "", ""  # Always Success in Simulation Mode
                review_text = "SIMULATION MODE" + "\r\n" + "Target PL: " + str(tgt_pl_g) + "\r\n\r\n" + "Simulation Mode"
                actual_pl_g, actual_pl_n = 0, 0

    elif num_pos >= 1 and \
            delta_pct <= ARBATM_param.range_bottom and \
            ts_within_allowance:
        ########################
        # Try to Close All Positions - Normal
        ########################
        eval = "Close All Positions" + "\r\n" + \
               "1: NumPos = " + str(num_pos) + "\r\n" + \
               "2: " + ts_diff_txt + "\r\n" + \
               "3: Delta_Pct:" + str(formatter_5d_pn.format(delta_pct)) + "% <= " + str(formatter_3d_pn.format(ARBATM_param.range_bottom)) + "%"
        num_order_attempted += 1
        order_attempted = True
        sound('short')
#        proceed = proximity_in_orderbook(sym, sym_f,
#                                         client_fm, future_price, ARBATM_param.ob_var_allow_pct,
#                                         client_sm, spot_price, ARBATM_param.ob_var_allow_pct,
#                                         ARBATM_param.lotsize*num_pos, int(equiv_num_fcont)*num_pos, mode=2)
        proceed = proximity_in_orderbook(sym, sym_f,
                                         client_fm, future_price,
                                         client_sm, spot_price,
                                         abs(delta_pct - ARBATM_param.range_bottom),
                                         ARBATM_param.lotsize*num_pos, int(equiv_num_fcont)*num_pos, mode=2)

        ob_text, proximity_text = proceed[1], proceed[2]
        if (proceed[0] == False):
            sound('shortlow')  # OB Fail
        else:
            sound('long') #LongBeep
            tgt_pl_g = (spot_price - future_price) * ARBATM_param.lotsize #Sell S, Buy F
            tgt_pl_n = tgt_pl_g - (future_price*f_fee_rate + spot_price*s_fee_rate) / 100 * ARBATM_param.lotsize
            #tgt_pl = (future_price - spot_price) * ARBATM_param.lotsize
            ###############################
            #  ***<<Place Close All>>***  #
            ###############################
            order_success = False
            if not ARBATM_param.simulation_mode:
                order = market_order_closeAll(sym, sym_f,
                                              client_st, spot_price,
                                              client_ft, future_price,
                                              ARBATM_param.lotsize, int(equiv_num_fcont), num_pos)
                order_success, mission, order_text = order[0], order[3], order[4]
                if order_success:
                    state_text = "4: <Closed All>, Look for next <Hedge>"
                    review = order_status_review(order[1], order[2], order[3],
                                                 ARBATM_param.lotsize, int(equiv_num_fcont), mode=2)
                    review_text = "Target PL: " + str(tgt_pl_g) + "\r\n\r\n" + review[2]
                    actual_pl_g, actual_pl_n = review[0], review[1]
                    ###set var###############
                    num_pos = 0
                    num_cycle += 1
                    order_placed = "Closed"
                    num_order_placed += 1
                    #########################
            else:
                state_text = "4: <Closed All>, Look for next <Hedge>"
                order_success, mission, order_text = True, "", ""  # Always Success in Simulation Mode
                review_text = "SIMULATION MODE" + "\r\n" + "Target PL: " + str(tgt_pl_g) + "\r\n\r\n" + "Simulation Mode"
                actual_pl_g, actual_pl_n = 0, 0

    # 0=Nothing, 1=Attempted Only, 2=All
    if (ARBATM_param.output_to_terminal == 1 and (order_attempted == True or order_placed != "--")) or \
        ARBATM_param.output_to_terminal == 2:
        disp = ("=" * 156) + "\n" + \
                "Local Time: " + str(local_dt) + " (Started: " + str(start_dt) + ", " + str(local_dt-start_dt) + " ago)" + " "*59 + \
                "NumCycle:" + str(num_cycle).zfill(2) + "  NumPos:" + str(num_pos).zfill(2) + "\n" + \
                "Iteration: " + str(formatter_idx.format(probe_idx)) + " "*3 + \
                "Spot: " + sym + "(" + str(ARBATM_param.lotsize) + ")" + ", " + \
                "Futures: " + sym_f + "(" + str(equiv_num_fcont) + f_lot_size_txt + " "*38 + "NumOrderPlaced:" + str(num_order_placed).zfill(2) + " " + ARBATM_param.bcolors.Red + order_placed + ARBATM_param.bcolors.NORMAL + "\n" + \
                "<Future>: (" + future_dt.strftime("%Y-%m-%d %H:%M:%S.%f") + ") " + str(formatter_5d.format(future_price)) + \
                " <Spot>: (" + spot_dt.strftime("%Y-%m-%d %H:%M:%S.%f") + ") " + str(formatter_5d.format(spot_price)) + " "*40 + "NumOrderAttempted:" + str(num_order_attempted).zfill(5) + "\n" + \
                ARBATM_param.bcolors.Blue + "<Delta>: " + str(formatter_5d_pn.format(delta)) + ARBATM_param.bcolors.NORMAL + \
                ARBATM_param.bcolors.Cyan + " <Delta_Pct>: " + str(formatter_5d_pn.format(delta_pct)) + "% " + \
                ARBATM_param.bcolors.Green + " (Min_Delta_Pct:" + str(formatter_5d_pn.format(min_delta_pct)) + "% Max_Delta_Pct:" + str(formatter_5d_pn.format(max_delta_pct)) + "% Zero_Delta_Pct:" + str(formatter_5d_pn.format(zero_delta_pct)) + "%)" + ARBATM_param.bcolors.NORMAL + "\n" + \
                ARBATM_param.bcolors.Yellow + "<Time Delta (F-S)>: " + ts_diff_txt + ARBATM_param.bcolors.NORMAL + "\n" + \
                ARBATM_param.bcolors.Yellow + "<State>: " + state_text + ARBATM_param.bcolors.NORMAL + "\n" + \
                ARBATM_param.bcolors.Yellow + "{:<20}".format("<Condition>:") + ARBATM_param.bcolors.Red + "{:<20}".format(condition) + ARBATM_param.bcolors.Yellow +  ARBATM_param.bcolors.NORMAL + "\n" + \
                ARBATM_param.bcolors.Yellow + "<Proximity Check>:  " + ARBATM_param.bcolors.Magenta + str(proximity_text) + ARBATM_param.bcolors.NORMAL + "\n" + \
                ARBATM_param.bcolors.Yellow + "<Order Action>: " + str(order_text) + ARBATM_param.bcolors.NORMAL
        print(disp)

    #####################################
    # Output to GSheet - Executed Orders
    #####################################
    if ARBATM_param.output_to_gsheet and order_placed != "--":
        tup1 = (str(probe_idx), local_dt.strftime("%H:%M:%S") + "\r\n" + local_dt.strftime("%Y-%m-%d"),
                order_placed,
                future_dt.strftime("%H:%M:%S") + "\r\n" + future_dt.strftime("%Y-%m-%d"), str(future_price),
                spot_dt.strftime("%H:%M:%S")   + "\r\n" + spot_dt.strftime("%Y-%m-%d"), str(spot_price),
                (future_dt - spot_dt).total_seconds(), str("{:.5f}".format(delta)), str("{:.5f}".format(delta_pct)),
                condition, eval,
                num_cycle, num_order_placed, num_pos,
                ob_text,
                mission, order_text,
                review_text,
                str(tgt_pl_g), str(tgt_pl_n), str(actual_pl_g), str(actual_pl_n))
        gsheet.write_tuple(num_order_placed + 2, tup1) #num_order_placed' # num_order_placed + 2

    ###################################
    # Output to CSV File - Executed Orders
    ###################################
    if ARBATM_param.output_to_csv and order_placed != "--":
        print ("WRLN TO CSV")
        f = open(ARBATM_param.exchange + "_orders" + ".csv", "a", newline="")
        writer = csv.writer(f)
        tup2 = ("G_WS:" + file_ws_name,
                str(probe_idx),
                local_dt.strftime("%Y-%m-%d %H:%M:%S"),
                ARBATM_param.symbol, ARBATM_param.lotsize,
                order[1], order[2], mission) #[1]=SPOT, [2]=FUTURES (Always:Add/Subtract)
        writer.writerow(tup2)
        f.close()

    ob_text = ""
    review_text = ""
    mission, order_text = "", ""
    probe_idx += 1

    #if keyboard.is_pressed("q"):
    #    print ("q pressed, end loop")
    #    break

    # Determine Stop / Continue
    if ARBATM_param.max_num_cycle != 0 and num_cycle >= ARBATM_param.max_num_cycle:
        run = False
        print("Auto Stopped (Max Cycle Reached)")

#if ARBATM_param.output_to_csv:
#    f.close()


