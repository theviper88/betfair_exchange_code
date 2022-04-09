import time
import importlib
import lib_api_commands
import lib_markets_edit
import lib_markets_check
import lib_markets_import
import strategy_mo_and_btts


def mo_and_btts_class(sessionToken, appKey, gsheets_api,
                      mobtts_correctscoreID, mobtts_moandbttsID,
                      mobtts_margin_multiplier_1 = 0.30, mobtts_margin_multiplier_2 = 0.00):
    
    lib_api_commands.cancelOrders(str(mobtts_moandbttsID), appKey, sessionToken)
    
    # trading variables definitions
    #ew_trading_stake = standard lay to lose amount
    #ew_max_runner_liability = actual market liability allowed for a runner before we stop laying the runner
    #ew_max_market_liability = possible market liability allowed for a runner before we stop laying the runner
    #ew_margin_multiplier_1 = maximum margin to add onto price if we can still be better than current market price   
    #ew_margin_multiplier_2 = lowest margin to add onto price that we are willing to take
    #loop_time = number of seconds to wait before updating odds
    
    # create calculation variables
    mobtts_strategy_name = "mo&btts"
    mobtts_old_moandbtts_tolay_prices = [0]*6
    mobtts_lay_bet_ids = [0]*6
    mobtts_old_moandbtts_toback_prices = [0]*6
    mobtts_back_bet_ids = [0]*6
    mobtts_selectionIds = [0]*6
    mobtts_selectionIds_liability = [0]*6
    mobtts_pnl_positions = [0]*6    
    mobtts_ev_trend = []

    N = 0
    while N < 1:
        gsheets_api.login()
        data = gsheets_api.open('betfair_markets').worksheet(mobtts_strategy_name)
        google_sheet = data.get_all_records()
        market_check, correctscoreBook, moandbttsBook = lib_markets_check.mobtts_market_check(appKey, sessionToken, mobtts_moandbttsID, mobtts_correctscoreID, data, google_sheet)
        if market_check == 1:
            trading_stake, max_liability, loop_time = lib_markets_import.import_mobtts_parameters(mobtts_moandbttsID, gsheets_api)
            mobtts_ev, mobtts_worst = strategy_mo_and_btts.mo_and_btts(sessionToken, appKey, \
                                                                       correctscoreBook, moandbttsBook, \
                                                                       mobtts_correctscoreID, mobtts_moandbttsID, mobtts_strategy_name, \
                                                                       trading_stake, max_liability, max_liability, mobtts_margin_multiplier_1, mobtts_margin_multiplier_2, \
                                                                       mobtts_old_moandbtts_tolay_prices, mobtts_lay_bet_ids, mobtts_old_moandbtts_toback_prices, mobtts_back_bet_ids, \
                                                                       mobtts_selectionIds, mobtts_selectionIds_liability, mobtts_pnl_positions, mobtts_ev_trend)
            lib_markets_edit.update_position(mobtts_moandbttsID, 9, mobtts_strategy_name, mobtts_ev, mobtts_worst, data, google_sheet)
            time.sleep(loop_time)
        else:
            N = N+1
            lib_api_commands.cancelOrders(str(mobtts_moandbttsID), appKey, sessionToken)
            print('\nThread "MO&BTTS:' + mobtts_moandbttsID + '" killed')
