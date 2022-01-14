######################################################
# SPOT - REAL
api_key_s = "xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
api_secret_s = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
api_passphrase_s = "xxxxxxxxxx"
api_sandbox_s = False

# FUTURES - REAL
api_key_f = "xxxxxxxxxxxxxxxxxxxxxxx"
api_secret_f = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
api_passphrase_f = "xxxxxxxxxxxxxxxxxxxxx"
api_sandbox_f = False
######################################################

######################################################
# SPOT - SANDBOX
api_key_s_sandbox = "yyyyyyyyyyyyyyyyyyyyyyyyy"
api_secret_s_sandbox = "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
api_passphrase_s_sandbox = "yyyyyyyyyyyyyyyyy"
api_sandbox_s_sandbox = True

# FUTURES - SANDBOX
api_key_f_sandbox = "yyyyyyyyyyyyyyyyyyyyy"
api_secret_f_sandbox = "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
api_passphrase_f_sandbox = "yyyyyyyyyyyyyyyyyyyyyy"
api_sandbox_f_sandbox = True
######################################################

KC_SPOT = {
    "key": api_key_s,
    "secret": api_secret_s,
    "passphrase": api_passphrase_s,
    "is_sandbox": api_sandbox_s,
}

KC_FUTURES = {
    "key": api_key_f,
    "secret": api_secret_f,
    "passphrase": api_passphrase_f,
    "is_sandbox": api_sandbox_f,
}

KC_SPOT_SANDBOX = {
    "key": api_key_s_sandbox,
    "secret": api_secret_s_sandbox,
    "passphrase": api_passphrase_s_sandbox,
    "is_sandbox": api_sandbox_s_sandbox,
}

KC_FUTURES_SANDBOX = {
    "key": api_key_f_sandbox,
    "secret": api_secret_f_sandbox,
    "passphrase": api_passphrase_f_sandbox,
    "is_sandbox": api_sandbox_f_sandbox,
}

