import time
import importlib
import lib_betdaq_commands
import lib_markets_edit
import lib_markets_check
import lib_markets_import
import strategy_betdaq

from betdaq.apiclient import APIClient
from betdaq.endpoints.marketdata import MarketData

# cancel bets at start and end
# remove un-neccisarry variables
# use liability limit
# track EV and exposure

def betdaq_class(bd_username, bd_password, sessionToken, appKey, gsheets_api, betdaq_api, betdaq_api2, betdaq_api_data,
                 bd_betfairID, bd_betdaqID, bd_betdaq_name,
                 bd_margin_multiplier_1 = 0.20, bd_margin_multiplier_2 = 0.05):

    betdaq_api2.cancel_all_orders(bd_betdaqID, bd_username, bd_password)

    # trading variables definitions
    #ew_trading_stake = standard lay to lose amount
    #ew_max_runner_liability = actual market liability allowed for a runner before we stop laying the runner
    #ew_max_market_liability = possible market liability allowed for a runner before we stop laying the runner
    #ew_margin_multiplier_1 = maximum margin to add onto price if we can still be better than current market price   
    #ew_margin_multiplier_2 = lowest margin to add onto price that we are willing to take
    #loop_time = number of seconds to wait before updating odds
    
    # create calculation variables
    bd_strategy_name = "betdaq"
    bet_ids = {}

    N = 0
    while N < 1:
        betdaq_api = APIClient(bd_username, bd_password)
        betdaq_api2 = lib_betdaq_commands.BetdaqApi()
        betdaq_api_data = MarketData(betdaq_api)
        gsheets_api.login()
        data = gsheets_api.open('betfair_markets').worksheet(bd_strategy_name)
        google_sheet = data.get_all_records()
        market_check, bfBook, bdBook = lib_markets_check.bd_market_check(appKey, sessionToken, betdaq_api, betdaq_api2, bd_betfairID, bd_betdaqID, data, google_sheet)
        if market_check == 1:
            trading_stake, max_liability, loop_time = lib_markets_import.import_bd_parameters(bd_betdaqID, bd_betfairID, gsheets_api, bd_strategy_name)
            betdaq_ev, betdaq_worst, bet_ids = strategy_betdaq.betdaq(sessionToken, appKey, betdaq_api, betdaq_api2, betdaq_api_data,  \
                                                                      bfBook, bdBook, bet_ids, \
                                                                      bd_betfairID, bd_betdaqID, bd_betdaq_name, bd_strategy_name, \
                                                                      trading_stake, max_liability, bd_margin_multiplier_1, bd_margin_multiplier_2)
            lib_markets_edit.update_position(bd_betfairID, 10, 'betfair', betdaq_ev, betdaq_worst, data, google_sheet)
            time.sleep(loop_time)
        else:
            N = N+1
            betdaq_api2.cancel_all_orders(bd_betdaqID, bd_username, bd_password)
            print('\nThread "BETDAQ: ' + bd_betdaqID + '" killed')
