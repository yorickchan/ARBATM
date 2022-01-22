use_sandbox = False
simulation_mode = False # If True, No Actual Orders will be placed

exchange = "KuCoin"
symbol = "ONE"  #KuCoin Sandbox only work with "certain" coins, data is wrong too
lotsize = 50    #Corresponding number of matching contract will be automatically calculated
max_pos_allow = 5   #0 = no max

hedge_bottom, hedge_top = -0.15, 0.15 #-0.01, 0.01   # in %
range_bottom, range_top = -0.4, 0.4   #-0.25, 0.25   # in %
ob_var_allow_pct  = 0.3          # 0.01 # in %
ts_var_allow_sec = 1.5           # ticker timestamp of S/F in seconds
ts_order_fill_gap = 10           # wait time(sec) between Order / Review, 5 sec is too early to review
timeout_to_close = 3600 #in seconds

spot_fee_pct = 0.1      #0.1%
futures_fee_pct = 0.03  #vary from 0.03% to 0%

beep = True
output_to_terminal = True
output_to_csv = False       # Can run faster if False
output_to_gsheet = True    # Can run faster if False

max_api_retry = 5 #Do **NOT** use to place order

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