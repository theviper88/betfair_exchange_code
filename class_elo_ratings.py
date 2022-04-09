import time
import importlib
import lib_api_commands
import lib_markets_edit
import lib_markets_check
import lib_markets_import
import strategy_elo_ratings


def elo_ratings_class(sessionToken, appKey, gsheets_api, 
                      elo_marketID):

    lib_api_commands.cancelOrders(str(elo_marketID), appKey, sessionToken)

    # trading variables definitions
    #elo_trading_stake = standard lay to lose amount
    #elo_max_runner_liability = actual market liability allowed for a runner before we stop laying the runner
    #elo_max_market_liability = possible market liability allowed for a runner before we stop laying the runner
    #loop_time = number of seconds to wait before updating odds

    # create calculation variables
    elo_strategy_name = "elo"
    elo_old_tolay_prices = [0]*2
    elo_old_toback_prices = [0]*2
    elo_back_bet_ids = [0]*2
    elo_lay_bet_ids = [0]*2
    elo_selectionIds = [0]*2
    elo_selectionIds_liability = [0]*2
    elo_pnl_positions = [0]*2
    elo_ev_trend = []

    N = 0
    while N < 1:
        gsheets_api.login()
        data = gsheets_api.open('betfair_markets').worksheet(elo_strategy_name)
        google_sheet = data.get_all_records()
        market_check, marketBook = lib_markets_check.elo_market_check(appKey, sessionToken, elo_marketID, data, google_sheet)
        if market_check == 1:
            sport, no_frames, trading_bankroll, max_liability, loop_time = lib_markets_import.import_elo_parameters(elo_marketID, gsheets_api)
            elo_ev, elo_worst = strategy_elo_ratings.elo_ratings(sessionToken, appKey, \
                                                                 marketBook, elo_marketID, sport, no_frames, elo_strategy_name,\
                                                                 trading_bankroll, max_liability, max_liability, \
                                                                 elo_old_tolay_prices, elo_old_toback_prices, elo_back_bet_ids, elo_lay_bet_ids, \
                                                                 elo_selectionIds, elo_selectionIds_liability, elo_pnl_positions, elo_ev_trend)
            lib_markets_edit.update_position(elo_marketID, 9, elo_strategy_name, elo_ev, elo_worst, data, google_sheet)
            time.sleep(loop_time)
        else:
            N = N+1
            lib_api_commands.cancelOrders(str(elo_marketID), appKey, sessionToken)
            print('\nThread "Elo:' + elo_marketID + '" killed')
