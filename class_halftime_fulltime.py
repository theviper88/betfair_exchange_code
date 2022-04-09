import time
import importlib
import lib_api_commands
import lib_markets_edit
import lib_markets_check
import lib_markets_import
import strategy_htft


def halftime_fulltime_class(sessionToken, appKey, gsheets_api,
                            htft_matchoddsID, htft_htftID, htft_half_time_result,
                            htft_margin_multiplier_1 = 0.20, htft_margin_multiplier_2 = 0.02):

    lib_api_commands.cancelOrders(str(htft_htftID), appKey, sessionToken)

    # trading variables definitions
    #ew_trading_stake = standard lay to lose amount
    #ew_max_runner_liability = actual market liability allowed for a runner before we stop laying the runner
    #ew_max_market_liability = possible market liability allowed for a runner before we stop laying the runner
    #ew_margin_multiplier_1 = maximum margin to add onto price if we can still be better than current market price   
    #ew_margin_multiplier_2 = lowest margin to add onto price that we are willing to take
    #loop_time = number of seconds to wait before updating odds
    
    # create calculation variables
    htft_strategy_name = "htft"
    htft_old_htft_tolay_prices = [0]*3
    htft_lay_bet_ids = [0]*3
    htft_old_htft_toback_prices = [0]*3
    htft_back_bet_ids = [0]*3
    htft_selectionIds = [0]*9
    htft_selectionIds_liability = [0]*9
    htft_pnl_positions = [0]*9
    htft_ev_trend = []

    N = 0
    while N < 1:
        gsheets_api.login()
        data = gsheets_api.open('betfair_markets').worksheet(htft_strategy_name)
        google_sheet = data.get_all_records()
        market_check, matchoddsBook, htftBook = lib_markets_check.htft_market_check(appKey, sessionToken, htft_matchoddsID, htft_htftID, htft_half_time_result, data, google_sheet)
        if market_check == 1:
            trading_stake, max_liability, loop_time = lib_markets_import.import_htft_parameters(htft_htftID, gsheets_api)
            htft_ev, htft_worst = strategy_htft.halftime_fulltime(sessionToken, appKey,  \
                                                                  matchoddsBook, htftBook,  \
                                                                  htft_matchoddsID, htft_htftID, htft_half_time_result, htft_strategy_name, \
                                                                  trading_stake, max_liability, max_liability, htft_margin_multiplier_1, htft_margin_multiplier_2, \
                                                                  htft_old_htft_tolay_prices, htft_lay_bet_ids, htft_old_htft_toback_prices, htft_back_bet_ids, \
                                                                  htft_selectionIds, htft_selectionIds_liability, htft_pnl_positions, htft_ev_trend)
            lib_markets_edit.update_position(htft_htftID, 10, htft_strategy_name, htft_ev, htft_worst, data, google_sheet)
            time.sleep(loop_time)
        else:
            N = N+1
            lib_api_commands.cancelOrders(str(htft_htftID), appKey, sessionToken)
            print('\nThread "HTFT:' + htft_htftID + '" killed')
