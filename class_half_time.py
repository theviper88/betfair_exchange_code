import time
import importlib
import lib_api_commands
import lib_markets_edit
import lib_markets_check
import lib_markets_import
import strategy_half_time


def half_time_class(sessionToken, appKey, gsheets_api,
                    ht_htftID, ht_halftimeID,
                    ht_margin_multiplier_1 = 0.20, ht_margin_multiplier_2 = 0.00):

    lib_api_commands.cancelOrders(str(ht_halftimeID), appKey, sessionToken)

    # trading variables definitions
    #ew_trading_stake = standard lay to lose amount
    #ew_max_runner_liability = actual market liability allowed for a runner before we stop laying the runner
    #ew_max_market_liability = possible market liability allowed for a runner before we stop laying the runner
    #ew_margin_multiplier_1 = maximum margin to add onto price if we can still be better than current market price   
    #ew_margin_multiplier_2 = lowest margin to add onto price that we are willing to take
    #loop_time = number of seconds to wait before updating odds
    
    # create calculation variables
    ht_strategy_name = "half_time"
    ht_old_halftime_tolay_prices = [0]*3
    ht_lay_bet_ids = [0]*3
    ht_old_halftime_toback_prices = [0]*3
    ht_back_bet_ids = [0]*3
    ht_selectionIds = [0]*3
    ht_selectionIds_liability = [0]*3
    ht_pnl_positions = [0]*3 
    ht_ev_trend = [] 

    N = 0
    while N < 1:
        gsheets_api.login()
        data = gsheets_api.open('betfair_markets').worksheet(ht_strategy_name)
        google_sheet = data.get_all_records()
        market_check, htftBook, halftimeBook = lib_markets_check.ht_market_check(appKey, sessionToken, ht_halftimeID, ht_htftID, data, google_sheet)
        if market_check == 1:
            trading_stake, max_liability, loop_time = lib_markets_import.import_ht_parameters(ht_halftimeID, gsheets_api)
            half_time_ev, half_time_worst = strategy_half_time.half_time(sessionToken, appKey,  \
                                                                         htftBook, halftimeBook,  \
                                                                         ht_htftID, ht_halftimeID, ht_strategy_name, \
                                                                         trading_stake, max_liability, max_liability, ht_margin_multiplier_1, ht_margin_multiplier_2, \
                                                                         ht_old_halftime_tolay_prices, ht_lay_bet_ids, ht_old_halftime_toback_prices, ht_back_bet_ids, \
                                                                         ht_selectionIds, ht_selectionIds_liability, ht_pnl_positions, ht_ev_trend)
            lib_markets_edit.update_position(ht_halftimeID, 9, ht_strategy_name, half_time_ev, half_time_worst, data, google_sheet)
            time.sleep(loop_time)
        else:
            N = N+1
            lib_api_commands.cancelOrders(str(ht_halftimeID), appKey, sessionToken)
            print('\nThread "Half Time:' + ht_halftimeID + '" killed')