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
                            url='https://api.kucoin.com')
    #spot = client_sm.get_ticker('BTC-USDT')
    #print(spot)
    #sys.exit()

    client_st = Trade_Spot(key=API_Keys.KC_SPOT['key'],
                           secret=API_Keys.KC_SPOT['secret'],
                           passphrase=API_Keys.KC_SPOT['passphrase'],
                           is_sandbox=API_Keys.KC_SPOT['is_sandbox'],
                           url='https://api.kucoin.com')

    client_fm = Market_Futures(key=API_Keys.KC_FUTURES['key'],
                               secret=API_Keys.KC_FUTURES['secret'],
                               passphrase=API_Keys.KC_FUTURES['passphrase'],
                               is_sandbox=API_Keys.KC_FUTURES['is_sandbox'],
                               url=API_Keys.KC_FUTURES['url'])
    #future = client_fm.get_ticker('ONEUSDTM') #--> WORKED OK (except BTCUSDTM....)
    #print(future)
    #sys.exit()
    client_ft = Trade_Futures(key=API_Keys.KC_FUTURES['key'],
                              secret=API_Keys.KC_FUTURES['secret'],
                              passphrase=API_Keys.KC_FUTURES['passphrase'],
                              is_sandbox=API_Keys.KC_FUTURES['is_sandbox'],
                              url='https://api-futures.kucoin.com')

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
formatter_idx = "{:0>6d}"

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
            winsound.Beep(frequency=440, duration=1000)
        elif type == 'short':
            #Short Blip
            winsound.Beep(frequency=440, duration=100)
        elif type == 'low':
            #Low
            winsound.Beep(frequency=200, duration=500)


def proximity_in_orderbook(sym, sym_f,
                           buy_client, tgt_buy_price, buy_variance_allowed_pct,
                           sell_client, tgt_sell_price, sell_variance_allowed_pct,
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
    asks_size_accum, asks_price_accum, ask_orderbook, diff_buy_pct,  asks_index, buy_sym  = 0, 0, '', 0, 0, ''
    bids_size_accum, bids_price_accum, bid_orderbook, diff_sell_pct, bids_index, sell_sym = 0, 0, '', 0, 0, ''
    ask_buy_ok, bid_sell_ok = False, False
    proximity_short_txt, proximity_in_orderbook_txt = "", ""

    if mode == 1:
        proximity_in_orderbook_txt="Buy-S,  Sell-F (Mode 1):" + "\r\n\r\n"
        buy_sym=sym
        sell_sym=sym_f
    else:
        proximity_in_orderbook_txt = "Buy-F, Sell-S (Mode 2):" + "\r\n\r\n"
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
                #Mode 2: Sell S, Buy F --> Close All
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
    if mode==1:
        size=lotsize
    else:
        size=num_f_contract
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
                                         "Qty: " + str(int(asks_size_accum)) + ", Cost: " + str(formatter_2d.format(asks_price_accum)) + "\r\n" + \
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
    if mode==1:
        size=num_f_contract
    else:
        size=lotsize
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
            proximity_in_orderbook_txt = proximity_in_orderbook_txt + "<Buy Side> (" + sell_sym + "):" + "\r\n" + \
                                         "TGT_SellPrice: " + str(tgt_sell_price) + "\r\n" + \
                                         "TGT_SellQty: " + str(size) + "\r\n" + \
                                         "<Order Book - Bids>:" + "\r\n" + bid_orderbook + \
                                         "*"*50 + "\r\n" + \
                                         "Takes " + str(bids_index) + " (0-base) bids to reach total of:" + "\r\n" + \
                                         "Qty: " + str(int(bids_size_accum)) + ", Cost: " + str(formatter_2d.format(bids_price_accum)) + "\r\n" + \
                                         "Avg Price: " + formatter_5d.format(float(bids_price_accum/bids_size_accum)) + "\r\n" + \
                                         "(" + str(tgt_sell_price) + " - " + formatter_5d.format(float(bids_price_accum/bids_size_accum)) + ") / " + str(tgt_sell_price) + \
                                         ": diff = " + formatter_3d_pn.format(diff_sell_pct) + "%" + "\r\n" + \
                                         "*"*50 + "\r\n\r\n"
            break
        else:
            bids_index += 1
    ask_buy_ok = False
    if diff_buy_pct <= buy_variance_allowed_pct:
        ask_buy_ok = True
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks: " + formatter_3d_pn.format(diff_buy_pct) + "% within " + str(buy_variance_allowed_pct) + "% limit " + "\r\n\r\n"
    else:
        proximity_in_orderbook_txt = proximity_in_orderbook_txt + "Buy / Asks: " + formatter_3d_pn.format(diff_buy_pct) + "% exceeded " + str(buy_variance_allowed_pct) + "% limit " + "\r\n\r\n"

    bid_sell_ok = False
    if diff_sell_pct <= sell_variance_allowed_pct:
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

    return ask_buy_ok and bid_sell_ok, proximity_in_orderbook_txt, proximity_short_txt


def market_order_hedge_add (sym, sym_f,
                            buy_client, tgt_buy_price,
                            sell_client, tgt_sell_price,
                            lotsize, num_f_contract):
    ##########################################
    # ** Place Market Orders **
    # Buy S, Sell F --> Hedge, Add
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
        id_buy = buy_client.create_market_order (sym, 'buy', size=lotsize)['orderId'] # This Actually work
        #print ("Buy Simulatino")
        # {'orderId': '61e8df144b81fa00012b3c62'}
        #break
    except:
        print("ERROR (3A)!!! when <place_market_order:create_market_order(BUY-S)> ")
        pass
    #print ("(Part A) Buy-S:", id_buy)

    #######################
    # Part B: Sell FUTURES
    # Qty: <num_f_contract>
    #######################
    if id_buy != '':
        try:
            id_sell = sell_client.create_market_order(symbol=sym_f, side='sell', lever=1, clientOid=API_Keys.clientOid, size=num_f_contract)['orderId'] # ACTUALLY WORK!!!!!
            # {'orderId': '61e82f61ac21e400010905d3'}
            #break
        except:
            print("ERROR (3B)!!! when <place_market_order:create_market_order(SELL " + str(num_f_contract) + " F)> ")
            pass
    #print("(Part B) Sell-F:", id_sell)

    ##############################################
    # Part C: Sell SPOT IMMEDIATELY,
    #         Sell FUTURES <failed>
    # Qty: <lotsize>
    ##############################################
    if id_sell == '':
        try:
            # Bought S Successful, Sell F Failed, Sell S (close IMMEDIATELY!!)
            id_sell2 = buy_client.create_market_order(sym, 'sell', size=lotsize)
        except:
            print("ERROR (3C)!!! when <place_market_order:create_market_order(SELL " + str(lotsize) + " S: due to SELL-F Failed)> ")
            pass

    mission = "Mission: (Hedge / Add)" + "\r\n" + \
              "<market_order_hedge_add>" + "\r\n" + \
              "Buy " + str(lotsize) + " " + sym + " @ " + str(tgt_buy_price) + "\r\n" + \
              "Sell " + str(num_f_contract) + sym_f + f_lot_size_txt + "@ " + str(tgt_sell_price)

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
        id_sell = sell_client.create_market_order(sym, 'sell', size=lotsize)['orderId']
    except:
        print("ERROR (4A)!!! when <market_order_closeAll:create_market_order(SELL-S)> ")
        sys.exit()
        pass

    #######################
    # Part B: Buy FUTURES
    # Qty: <num_f_contract>
    #######################
    if id_sell != '':
        try:
            print(',market_order_closeAll.: Try to buy back ' + str(num_f_contract) + ' ' + sym_f)
            id_buy = buy_client.create_market_order(symbol=sym_f, side='buy', lever=1, clientOid=API_Keys.clientOid, size=num_f_contract)['orderId']
        except:
            print("ERROR (4B)!!! when <place_market_order:create_market_order(SELL-F)> ")
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

    ttl_s, index_s, slept_cnt_s, s_txt = 0, 0, 0, ''
    ttl_f, index_f, slept_cnt_f, f_txt = 0, 0, 0, ''
    actual_pl, order_review_txt = 0, ''

    #print("order_status_review: wait " + str(ARBATM_param.ts_order_fill_gap) + "sec")
    #print("Spot: " + orderId_s)
    #print("Futures: " + orderId_f)

    t.sleep(ARBATM_param.ts_order_fill_gap)

    ########################################################
    # Part A-1: Sleep until Spot-order is no-longer Active
    ########################################################
    s_order = client_st.get_order_details(orderId=orderId_s) # '61e8df144b81fa00012b3c62'
    while s_order['isActive']:
        slept_cnt_s += 1
        print (orderId_s + ": sleep " + slept_cnt_s)
        t.sleep(5)
    #print("Slept " + str(slept_cnt_s) + " times, order SS is NOT active - OK finished")
    #print (s_order['id'])
    s_txt = '<' + s_order['side'].upper() + ' SPOT: ' + s_order['symbol'] + ": " + " " + str(s_order['size']) + '>' + "\r\n" + \
            'orderId: ' + s_order['id'] + "\r\n"

    ########################################################
    # Part A-2: Get total Spot-order price, size, and fees
    ########################################################
    s_order = client_st.get_fill_list(tradeType='TRADE')['items']  # Either TRADE or MARGIN_TRADE, #24hrs
    fills = list(filter(lambda filled_entry: filled_entry['orderId'] == orderId_s, s_order))  # [1]['price']
    for entry in fills: #Each Fills can be in multiple entries
        s_txt = s_txt + str(index_s).zfill(2) + ". " + \
                           "Price: " + str(float(entry['price'])) + ", " + \
                           "Qty: " + str(float(entry['size'])) + ", " + \
                           "Fees: " + str(float(entry['fee'])) + "\r\n"
        ttl_s = ttl_s + (float(entry['price']) * float(entry['size']) + float(entry['fee']))
        index_s += 1
    s_txt = s_txt + "Total: " + str(ttl_s)


    ########################################################
    # Part B-1: Sleep until Futures-order is no-longer Active
    ########################################################
    f_order = client_ft.get_order_details(orderId=orderId_f)
    while f_order['isActive']:
        slept_cnt_f += 1
        print (orderId_f + ": sleep " + slept_cnt_f)
        t.sleep(5)
    f_txt = '<' + f_order['side'].upper() + ' Futures: ' + f_order['symbol'] + ": " + " " + str(f_order['size']) + f_lot_size_txt + '>' + "\r\n" + \
            'orderId: ' + f_order['id'] + "\r\n"

    ########################################################
    # Part B-2: Get total Futures-order price, size, and fees
    ########################################################
    f_order = client_ft.get_recent_fills()
    fills = list(filter(lambda filled_entry: filled_entry['orderId'] == orderId_f, f_order))  # [1]['price']
    for entry in fills:  # Each Fills can be in multiple entries
        f_txt = f_txt + str(index_f).zfill(2) + ". " + \
                           "Price: " + str(float(entry['price'])) + ", " + \
                           "Qty: " + str(float(entry['size']))  + ", " + \
                           "Fees: " + str(float(entry['fee'])) + "\r\n"
        ttl_f = ttl_f + (float(entry['price']) * float(entry['size']) + float(entry['fee']))
        index_f += 1
    f_txt = f_txt + "Total: " + str(ttl_f)

    if mode==1:
        actual_pl = ttl_f - ttl_s
        order_review_txt = s_txt + "\r\n\r\n" + \
                           f_txt + "\r\n\r\n" + \
                           "Actual PL: " + str(formatter_5d_pn.format(actual_pl))
    else:
        actual_pl = (ttl_s - ttl_f) # * lotsize_fcont # DOUBLE CHECK
        order_review_txt = f_txt + "\r\n\r\n" + \
                           s_txt + "\r\n\r\n" + \
                           "Actual PL: " + str(formatter_5d_pn.format(actual_pl))

    return actual_pl, order_review_txt

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
#print ("all_open_contract: " , all_open_contract)
#contract = [open_contract for open_contract in all_open_contract if open_contract['symbol'] == sym_f] # --> Also Work, but use lambda
#print(contract[0]['multiplier'])
f_lot_size = list(filter(lambda open_contract: open_contract['symbol'] == sym_f, all_open_contract))[0]['multiplier']
print (f_lot_size)
if float(ARBATM_param.lotsize) % float(f_lot_size) != 0:
    print ('Invalid Lot Size to multiplier')
    print(str(ARBATM_param.lotsize) + ' ' + sym + ' = ' +
          str(float(ARBATM_param.lotsize) / float(f_lot_size)) + ' ' + sym_f + ' futures contracts')
    sys.exit()
else:
    lotsize_fcont = f_lot_size
    equiv_num_fcont = float(ARBATM_param.lotsize) / float(f_lot_size)
    print(str(ARBATM_param.lotsize) + ' ' + sym + ' = ' + \
          str(equiv_num_fcont) + ' (mul:' + str(int(f_lot_size)) + ') ' + sym_f + ' futures contracts')

f_lot_size_txt = " (" + str(equiv_num_fcont) + " contract, mult: " + str(lotsize_fcont) + ") "
# For 500 ONE:
# equiv_num_fcont = 50
# lotsize_fcont = 10
##################################################
# THIS IS WEIRD, USE SAME NUMBER FOR FUTURES INSTEAD
# OF DIVIDING BY THE "MULTIPLIER"
equiv_num_fcont = ARBATM_param.lotsize
##################################################

probe_idx = 2
delta, delta_pct = 0, 0
max_delta_pct, min_delta_pct, zero_delta_pct = 0, 0, 1000
num_pos, num_order_placed, num_cycle = 0, 0, 0
start_dt = datetime.fromtimestamp(int(t.time()))
tgt_pl = 0

condition = ""
ob_text = ""
review_text = ""

if ARBATM_param.output_to_csv or ARBATM_param.output_to_gsheet:
    file_ws_name = ARBATM_param.exchange + "_" + symbol + "_" +  str(start_dt)
    tup1 = ("Index", "Local-Time",
            "OrderPlaced", "Target_PL",
            "F_TimeStamp", "F_Price$",
            "S_TimeStamp", "S_Price$",
            "F-S_TimeStamp", "F-S_$", "(F-S)/S_%",
            "Condition", "Evaluation",
            "Num_Cycle", "Num_Order_Placed", "Num_Pos",
            "OrderBook", "Mission", "Order Status",
            "Review")

###################################
# Output to CSV File - Header
###################################
if ARBATM_param.output_to_csv:
    f = open(file_ws_name.replace(":","-") + ".csv", "a", newline="")
    f.truncate(0)
    writer = csv.writer(f)
    writer.writerow(tup1)

###################################
# Output to Google Sheet - Header
###################################
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
                      "Lot Size: " + str(lotsize) + " / " + f_lot_size_txt + "\r\n\r\n" +
                      "Parameters:" + "\r\n" +
                      "F/S Time Diff Allow: " + str(ARBATM_param.ts_var_allow_sec) + " seconds" + "\r\n" +
                      "Hedge (F=S): " + str(ARBATM_param.hedge_bottom) + " to " + str(ARBATM_param.hedge_top) + "%" + "\r\n" +
                      "Add (F>=S): " + str(ARBATM_param.range_top) + "%" + "\r\n" +
                      "Close All (F<=S):" + str(ARBATM_param.range_bottom) + "%")
    gsheet.write_tuple(num_order_placed + 2, tup1)


#############
# Main Body #
#############
while True:
    t.sleep(0)
    local_dt = datetime.fromtimestamp(int(t.time()))
    last_hedge_add_dt = datetime.fromtimestamp(int(t.time()))

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
    if abs(ts_diff) <= ARBATM_param.ts_var_allow_sec:
        ts_within_allowance = True
        ts_diff_txt = str(formatter_5d_pn.format(ts_diff)) + "sec is within +/-" + str(ARBATM_param.ts_var_allow_sec) + "sec limit"
    else:
        ts_within_allowance = False
        ts_diff_txt = str(formatter_5d_pn.format(ts_diff)) + "sec exceeded +/-" + str(ARBATM_param.ts_var_allow_sec) + "sec limit"


    proximity_text = ""
    order_text = ""
    mission = ""
    order_placed = "--"

    if num_pos == 0 and \
            delta_pct >= ARBATM_param.hedge_bottom and delta_pct <= ARBATM_param.hedge_top and \
            ts_within_allowance:
        #############################
        # Try to: Open Hedge Position
        #############################
        eval = "Open Hedge" + "\r\n" + \
               "1: NumPos = " + str(num_pos) + "\r\n" + \
               "2: " + ts_diff_txt + "\r\n" + \
               "3: Delta_Pct:" + str(formatter_5d_pn.format(delta_pct)) + "% is between " + str(formatter_3d_pn.format(ARBATM_param.hedge_bottom)) + "% and " + str(formatter_3d_pn.format(ARBATM_param.hedge_top)) + "%"

        proceed = proximity_in_orderbook(sym, sym_f,
                                         client_sm, spot_price, ARBATM_param.ob_var_allow_pct,
                                         client_fm, future_price, ARBATM_param.ob_var_allow_pct,
                                         ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)
        ob_text, proximity_text = proceed[1], proceed[2]
        #return ask_buy_ok and bid_sell_ok, proximity_in_orderbook_txt, proximity_short_txt
        if (proceed[0] == True):
            sound('normal') #NormalBeep
            tgt_pl = (future_price - spot_price) * ARBATM_param.lotsize
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
                    review = order_status_review(order[1], order[2], order[3],
                                                 ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)
                    review_text = "Target PL: " + str(tgt_pl) + "\r\n\r\n" + review[1]
            else:
                order_success, mission, order_text = True, "", ""   # Always Success in Simulation Mode
                if order_success:
                    review = order_status_review('61ea2d9e66e4c70001dde95a', '61ea2d9eaf4fb500011b4930', '',
                                                 ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)
                    review_text = "SIMULATION MODE" + "\r\n" + "Target PL: " + str(tgt_pl) + "\r\n\r\n" + review[1]
            if order_success:
                last_hedge_add_dt = datetime.fromtimestamp(int(t.time()))
                num_pos += 1
                order_placed = "Hedged"
                num_order_placed += 1

    elif num_pos > 0 and num_pos < ARBATM_param.max_pos_allow and \
            delta_pct >= ARBATM_param.range_top and \
            ts_within_allowance:
        ########################
        # Try to: Add Position
        ########################
        eval = "Add Position" + "\r\n" + \
               "1: NumPos = " + str(num_pos) + "\r\n" + \
               "2: " + ts_diff_txt + "\r\n" + \
               "3: Delta_Pct:" + str(formatter_3d_pn.format(delta_pct)) + "% >= " + str(formatter_3d_pn.format(ARBATM_param.range_top)) + "%"
        proceed = proximity_in_orderbook(sym, sym_f,
                                         client_sm, spot_price, ARBATM_param.ob_var_allow_pct,
                                         client_fm, future_price, ARBATM_param.ob_var_allow_pct,
                                         ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)
        ob_text, proximity_text = proceed[1], proceed[2]
        #last_hedge_add_dt
        if (proceed[0] == True):
            sound('normal') #NormalBeep
            tgt_pl = (future_price - spot_price) * ARBATM_param.lotsize
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
                    review = order_status_review(order[1], order[2], order[3],
                                                 ARBATM_param.lotsize, int(equiv_num_fcont), mode=1)
                    review_text = "Target PL: " + str(tgt_pl) + "\r\n\r\n" + review[1]
            else:
                order_success, mission, order_text = True, "", ""  # Always Success in Simulation Mode

            if order_success:
                last_hedge_add_dt = datetime.fromtimestamp(int(t.time()))
                num_pos += 1
                order_placed = "Added"
                num_order_placed += 1

    elif num_pos > 0 and \
            delta_pct <= ARBATM_param.range_bottom and \
            ts_within_allowance:
        ########################
        # Try to Close All Positions - Normal
        ########################
        eval = "Close All Positions" + "\r\n" + \
               "1: NumPos = " + str(num_pos) + "\r\n" + \
               "2: " + ts_diff_txt + "\r\n" + \
               "3: Delta_Pct:" + str(formatter_5d_pn.format(delta_pct)) + "% <= " + str(formatter_3d_pn.format(ARBATM_param.range_bottom)) + "%"
        proceed = proximity_in_orderbook(sym, sym_f,
                                         client_fm, future_price, ARBATM_param.ob_var_allow_pct,
                                         client_sm, spot_price, ARBATM_param.ob_var_allow_pct,
                                         ARBATM_param.lotsize*num_pos, int(equiv_num_fcont)*num_pos, mode=2)
        ob_text, proximity_text = proceed[1], proceed[2]
        if (proceed[0] == True):
            sound('long') #LongBeep
            tgt_pl = (future_price - spot_price) * ARBATM_param.lotsize
            ###############################
            #  ***<<Place Close All>>***  #
            ###############################
            order_success = False
            if not ARBATM_param.simulation_mode:
                print ('aaaaa')
                order = market_order_closeAll(sym, sym_f,
                                              client_st, spot_price,
                                              client_ft, future_price,
                                              ARBATM_param.lotsize, int(equiv_num_fcont), num_pos)
                #return id_buy != '' and id_sell != '',
                #id_sell, id_buy,
                #mission, place_market_order_txt
                print('bbbbb')
                order_success, mission, order_text = order[0], order[3], order[4]
                if order_success:
                    print('cccc')
                    review = order_status_review(order[1], order[2], order[3],
                                                 ARBATM_param.lotsize, int(equiv_num_fcont), mode=2)
                    print('ddddd')
                    review_text = "Target PL: " + str(tgt_pl) + "\r\n\r\n" + review[1]

            else:
                order_success, mission, order_text = True, "", ""  # Always Success in Simulation Mode
            if order_success:
                #last_hedge_add_dt = datetime.fromtimestamp(int(t.time())) RESET!!!
                #num_pos += 1
                #order_placed = "Added"
                #num_order_placed += 1
                num_pos = 0
                num_cycle += 1
                order_placed = "Closed"
                num_order_placed += 1


    if ARBATM_param.output_to_terminal:
        disp = ("=" * 156) + "\n" + \
                "Local Time: " + str(local_dt) + " (Started: " + str(start_dt) + ", " + str(local_dt-start_dt) + " ago)" + " "*59 + \
                "NumCycle:" + str(num_cycle).zfill(2) + "  NumPos:" + str(num_pos).zfill(2) + "\n" + \
                "Iteration: " + str(formatter_idx.format(probe_idx)) + " "*3 + \
                "Spot: " + sym + "(" + str(ARBATM_param.lotsize) + ")" + ", " + \
                "Futures: " + sym_f + "(" + str(equiv_num_fcont) + f_lot_size_txt + " "*47 + "NumOrderPlaced:" + str(num_order_placed).zfill(2) + " " + ARBATM_param.bcolors.Red + order_placed + ARBATM_param.bcolors.NORMAL + "\n" + \
                "<Future>: (" + future_dt.strftime("%Y-%m-%d %H:%M:%S.%f") + ") " + str(formatter_5d.format(future_price)) + \
                " <Spot>: (" + spot_dt.strftime("%Y-%m-%d %H:%M:%S.%f") + ") " + str(formatter_5d.format(spot_price)) + "\n" + \
                ARBATM_param.bcolors.Blue + "<Delta>: " + str(formatter_5d_pn.format(delta)) + ARBATM_param.bcolors.NORMAL + \
                ARBATM_param.bcolors.Cyan + " <Delta_Pct>: " + str(formatter_5d_pn.format(delta_pct)) + "% " + \
                ARBATM_param.bcolors.Green + " (Min_Delta_Pct:" + str(formatter_5d_pn.format(min_delta_pct)) + "% Max_Delta_Pct:" + str(formatter_5d_pn.format(max_delta_pct)) + "% Zero_Delta_Pct:" + str(formatter_5d_pn.format(zero_delta_pct)) + "%)" + ARBATM_param.bcolors.NORMAL + "\n" + \
                ARBATM_param.bcolors.Yellow + "<Time Delta (F-S)>: " + ts_diff_txt + ARBATM_param.bcolors.NORMAL + "\n" + \
                ARBATM_param.bcolors.Yellow + "{:<20}".format("<Condition>:") + ARBATM_param.bcolors.Red + "{:<20}".format(condition) + ARBATM_param.bcolors.Yellow +  ARBATM_param.bcolors.NORMAL + "\n" + \
                ARBATM_param.bcolors.Yellow + "<Proximity Check>:  " + str(proximity_text) + ARBATM_param.bcolors.NORMAL + "\n" + \
                ARBATM_param.bcolors.Yellow + "<Order Action>: " + str(order_text) + ARBATM_param.bcolors.NORMAL
        print(disp)

    ###################################
    # Create tuple for CSV or GSheet
    ###################################
    if ARBATM_param.output_to_csv or ARBATM_param.output_to_gsheet:
        tup1 = (str(probe_idx), local_dt.strftime("%H:%M:%S") + "\r\n" + local_dt.strftime("%Y-%m-%d"),
                order_placed, str(tgt_pl),
                future_dt.strftime("%H:%M:%S") + "\r\n" + future_dt.strftime("%Y-%m-%d"), str(future_price),
                spot_dt.strftime("%H:%M:%S")   + "\r\n" + spot_dt.strftime("%Y-%m-%d"), str(spot_price),
                (future_dt - spot_dt).total_seconds(), str("{:.5f}".format(delta)), str("{:.5f}".format(delta_pct)),
                condition, eval,
                num_cycle, num_order_placed, num_pos,
                ob_text,
                mission, order_text,
                review_text)

    ###################################
    # Output to CSV File - Data Entries
    ###################################
    if ARBATM_param.output_to_csv:
        writer.writerow(tup1)

    #####################################
    # Output to GSheet - Executed Orders
    #####################################
    if ARBATM_param.output_to_gsheet and order_placed != "--":
        #gsheet.insert_empty_row(3)
        #print("After Insert")
        gsheet.write_tuple(num_order_placed + 2, tup1) #num_order_placed' # num_order_placed + 2

    ob_text = ""
    review_text = ""
    mission, order_text = "", ""
    probe_idx += 1
    if keyboard.is_pressed("q"):
        print ("q pressed, end loop")
        break

if ARBATM_param.output_to_csv:
    f.close()


