use_sandbox = False
simulation_mode = False # If True, No Actual Orders will be placed

exchange = "KuCoin"
symbol = "ONE"  #KuCoin Sandbox only work with "certain" coins, data is wrong too - ALL CAPS
lotsize = 1500    #Corresponding number of matching contract will be automatically calculated
max_pos_allow = 2
max_num_cycle = 1   #0 = no max

# F>S +ve
# F<S -ve

#range_bottom, subtract_top, hedge_bottom, range_top = -0.32, -0.16, 0.16, 0.32 #0.16% round-trip-fees: -0.32, -0.16, 0.16, 0.32
range_bottom, subtract_top, hedge_bottom, range_top = -0.32, -0.16, 0.16, 0.32
#range_bottom, range_top = -0.4, 0.4 #-0.25, 0.25   # in %
#subtract_top = -0.16                # 0.16% round-trip-fees

#ob_var_allow_pct = 0.03        # 0.01 # in % -- Use <Delta_Pct> instead
ts_var_allow_sec = 1.5          # ticker timestamp of S/F in seconds 0.5
ts_order_fill_gap = 10          # wait time(sec) between Order / Review, 5 sec is too early to review
timeout_to_close = 3600         #in seconds

order_type_s = "limit"
order_type_f = "market"         # only check "limit"

spot_fee_pct = 0.1      #0.1%
futures_fee_pct = 0.06  #vary from 0.03% to 0%

beep = True
output_to_terminal = 2     #0=Nothing, 1=Attempted and Order Only, 2=All
output_to_csv = True       # Only Write orderId
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
