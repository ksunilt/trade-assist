from authentication.fyers_authentication import *
from utility.telegram_utility import *

if __name__ == "__main__":
    fyers_login()
    send_tele_msg(message="Fyers Login check completed.")

    import sys
    print(sys.path)
    sys.path.append("../trading_bot/trade-assist/")
    sys.path.append("../trading_bot/trade-assist/utility/")
    print(sys.path)
