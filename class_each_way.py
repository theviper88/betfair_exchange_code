import time
import importlib
import lib_api_commands
import lib_markets_edit
import lib_markets_check
import lib_markets_import
import strategy_each_way


def each_way_class(sessionToken, appKey, gsheets_api, 
                   ew_winmarketID, ew_placemarketID, ew_eachwaymarketID, 
                   ew_margin_multiplier_1 = 0.50, ew_margin_multiplier_2 = 0.05):

    lib_api_commands.cancelOrders(str(ew_eachwaymarketID), appKey, sessionToken)

    # trading variables definitions
    #ew_trading_stake = standard lay to lose amount
    #ew_max_runner_liability = actual market liability allowed for a runner before we stop laying the runner
    #ew_max_market_liability = possible market liability allowed for a runner before we stop laying the runner
    #ew_margin_multiplier_1 = maximum margin to add onto price if we can still be better than current market price   
    #ew_margin_multiplier_2 = lowest margin to add onto price that we are willing to take
    #loop_time = number of seconds to wait before updating odds

    # create calculation variables
    ew_strategy_name = "each_way"
    ew_old_eachway_tolay_prices = [0]*299
    ew_old_eachway_toback_prices = [0]*299
    ew_back_bet_ids = [0]*299
    ew_lay_bet_ids = [0]*299
    ew_selectionIds = [0]*299
    ew_selectionIds_liability = [0]*299
    ew_win_position = [0]*299
    ew_place_position = [0]*299
    ew_lose_position = [0]*299
    ew_worst_place_positions = [0]*299
    ew_worst_cases = [0]*299
    ew_ev_trend = []

    N = 0
    while N < 1:
        gsheets_api.login()
        data = gsheets_api.open('betfair_markets').worksheet(ew_strategy_name)
        google_sheet = data.get_all_records()
        market_check, winmarketBook, placemarketBook, eachwaymarketBook = lib_markets_check.ew_market_check(appKey, sessionToken, ew_eachwaymarketID, ew_placemarketID, ew_winmarketID, data, google_sheet)
        if market_check == 1:
            eachwayfraction, eachwayplaces, trading_stake, max_liability, loop_time = lib_markets_import.import_ew_parameters(ew_eachwaymarketID, gsheets_api)
            each_way_ev, each_way_worst = strategy_each_way.each_way(sessionToken, appKey, \
                                                                     winmarketBook, placemarketBook, eachwaymarketBook, \
                                                                     ew_winmarketID, ew_placemarketID, ew_eachwaymarketID, eachwayfraction, eachwayplaces, ew_strategy_name,\
                                                                     trading_stake, max_liability, max_liability, ew_margin_multiplier_1, ew_margin_multiplier_2, \
                                                                     ew_old_eachway_tolay_prices, ew_old_eachway_toback_prices, ew_back_bet_ids, ew_lay_bet_ids, \
                                                                     ew_selectionIds, ew_selectionIds_liability, ew_win_position, ew_place_position, ew_lose_position, ew_worst_place_positions, ew_worst_cases, ew_ev_trend)
            lib_markets_edit.update_position(ew_eachwaymarketID, 12, ew_strategy_name, each_way_ev, each_way_worst, data, google_sheet)
            time.sleep(loop_time)
        else:
            N = N+1
            lib_api_commands.cancelOrders(str(ew_eachwaymarketID), appKey, sessionToken)
            print('\nThread "Each Way: ' + ew_eachwaymarketID + '" killed')
