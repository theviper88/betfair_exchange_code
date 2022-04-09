import pandas

# default = [trading_stake, max_liability, loop_time]
ew_default = [50,200,60]
mobtts_default = [50,100,300]
ht_default = [50,100,300]
elo_default = [20,20,300]
htft_default = [20,100,60]
bd_default = [50,200,300]


def import_ew_parameters(ew_eachwaymarketID, gsheets_api):
    data = gsheets_api.open('betfair_markets').worksheet("each_way")
    markets = data.get_all_records()
    markets_df = pandas.DataFrame(markets)
    market_row = markets_df.loc[markets_df['each_way_market_id']==int(ew_eachwaymarketID[2:])].index[0]
    eachwayfraction = markets_df['each_way_fraction'][market_row]
    eachwayplaces = markets_df['no_of_places'][market_row]
    if markets_df['trading_stake'][market_row] == '':
        trading_stake = ew_default[0]
    else:
        trading_stake = markets_df['trading_stake'][market_row]
    if markets_df['max_liability'][market_row] == '':
        max_liability = ew_default[1]
    else:
        max_liability = markets_df['max_liability'][market_row]
    if markets_df['loop_time'][market_row] == '':
        loop_time = ew_default[2]
    else:
        loop_time = markets_df['loop_time'][market_row]
    return eachwayfraction, eachwayplaces, trading_stake, max_liability, loop_time 


def import_mobtts_parameters(mobtts_moandbttsID, gsheets_api):
    data = gsheets_api.open('betfair_markets').worksheet("mo&btts")
    markets = data.get_all_records()
    markets_df = pandas.DataFrame(markets)
    market_row = markets_df.loc[markets_df['mo&btts_market_id']==int(mobtts_moandbttsID[2:])].index[0]
    if markets_df['trading_stake'][market_row] == '':
        trading_stake = mobtts_default[0]
    else:
        trading_stake = markets_df['trading_stake'][market_row]
    if markets_df['max_liability'][market_row] == '':
        max_liability = mobtts_default[1]
    else:
        max_liability = markets_df['max_liability'][market_row]
    if markets_df['loop_time'][market_row] == '':
        loop_time = mobtts_default[2]
    else:
        loop_time = markets_df['loop_time'][market_row]
    return trading_stake, max_liability, loop_time


def import_ht_parameters(ht_halftimeID, gsheets_api):
    data = gsheets_api.open('betfair_markets').worksheet("half_time")
    markets = data.get_all_records()
    markets_df = pandas.DataFrame(markets)
    market_row = markets_df.loc[markets_df['half_time_market_id']==int(ht_halftimeID[2:])].index[0]
    if markets_df['trading_stake'][market_row] == '':
        trading_stake = ht_default[0]
    else:
        trading_stake = markets_df['trading_stake'][market_row]
    if markets_df['max_liability'][market_row] == '':
        max_liability = ht_default[1]
    else:
        max_liability = markets_df['max_liability'][market_row]
    if markets_df['loop_time'][market_row] == '':
        loop_time = ht_default[2]
    else:
        loop_time = markets_df['loop_time'][market_row]
    return trading_stake, max_liability, loop_time


def import_elo_parameters(marketID, gsheets_api):
    data = gsheets_api.open('betfair_markets').worksheet("elo")
    markets = data.get_all_records()
    markets_df = pandas.DataFrame(markets)
    market_row = markets_df.loc[markets_df['elo_market_id']==int(marketID[2:])].index[0]
    sport = markets_df['sport'][market_row]
    no_frames = markets_df['no_frames'][market_row]
    if markets_df['max_liability'][market_row] == '':
        trading_bankroll = mobtts_default[0]
        max_liability = mobtts_default[1]
    else:
        trading_bankroll = markets_df['max_liability'][market_row]
        max_liability = markets_df['max_liability'][market_row]
    if markets_df['loop_time'][market_row] == '':
        loop_time = mobtts_default[2]
    else:
        loop_time = markets_df['loop_time'][market_row]
    return sport, no_frames, trading_bankroll, max_liability, loop_time


def import_htft_parameters(htft_htftID, gsheets_api):
    data = gsheets_api.open('betfair_markets').worksheet("htft")
    markets = data.get_all_records()
    markets_df = pandas.DataFrame(markets)
    market_row = markets_df.loc[markets_df['htft_market_id']==int(htft_htftID[2:])].index[0]
    if markets_df['trading_stake'][market_row] == '':
        trading_stake = htft_default[0]
    else:
        trading_stake = markets_df['trading_stake'][market_row]
    if markets_df['max_liability'][market_row] == '':
        max_liability = htft_default[1]
    else:
        max_liability = markets_df['max_liability'][market_row]
    if markets_df['loop_time'][market_row] == '':
        loop_time = htft_default[2]
    else:
        loop_time = markets_df['loop_time'][market_row]
    return trading_stake, max_liability, loop_time


def import_bd_parameters(bd_betdaqID, bd_betfairID, gsheets_api, strategy_name):
    data = gsheets_api.open('betfair_markets').worksheet(strategy_name)
    markets = data.get_all_records()
    markets_df = pandas.DataFrame(markets)
    market_row = markets_df.loc[markets_df['betfair_market_id']==int(bd_betfairID[2:])].index[0]
    if markets_df['trading_stake'][market_row] == '':
        trading_stake = bd_default[0]
    else:
        trading_stake = markets_df['trading_stake'][market_row]
    if markets_df['max_liability'][market_row] == '':
        max_liability = bd_default[1]
    else:
        max_liability = markets_df['max_liability'][market_row]
    if markets_df['loop_time'][market_row] == '':
        loop_time = bd_default[2]
    else:
        loop_time = markets_df['loop_time'][market_row]
    return trading_stake, max_liability, loop_time


#######################################################################################################################################


def import_ew_markets(gsheets_api):
    ew_winmarketIDs = []
    ew_placemarketIDs = []
    ew_eachwaymarketIDs = []
    data = gsheets_api.open('betfair_markets').worksheet("each_way")
    markets = data.get_all_records()
    for n in range(0,len(markets)):
        if markets[n]['complete_10'] == 1:
            ew_winmarketIDs.append('1.'+str(markets[n]['win_market_id']))
            ew_placemarketIDs.append('1.'+str(markets[n]['place_market_id']))
            ew_eachwaymarketIDs.append('1.'+str(markets[n]['each_way_market_id']))
    return ew_winmarketIDs, ew_placemarketIDs, ew_eachwaymarketIDs


def import_mobtts_markets(gsheets_api):
    mobtts_correctscoreIDs = []
    mobtts_moandbttsIDs = []
    data = gsheets_api.open('betfair_markets').worksheet("mo&btts")
    markets = data.get_all_records()
    for n in range(0,len(markets)):
        if markets[n]['complete_10'] == 1:
            mobtts_correctscoreIDs.append('1.'+str(markets[n]['correct_score_market_id']))
            mobtts_moandbttsIDs.append('1.'+str(markets[n]['mo&btts_market_id']))
    return mobtts_correctscoreIDs, mobtts_moandbttsIDs


def import_ht_markets(gsheets_api):
    ht_htftIDs = []
    ht_halftimeIDs = []
    data = gsheets_api.open('betfair_markets').worksheet("half_time")
    markets = data.get_all_records()
    for n in range(0,len(markets)):
        if markets[n]['complete_10'] == 1:
            ht_htftIDs.append('1.'+str(markets[n]['htft_market_id']))
            ht_halftimeIDs.append('1.'+str(markets[n]['half_time_market_id']))
    return ht_htftIDs, ht_halftimeIDs


def import_elo_markets(gsheets_api):
    elo_marketIDs = []
    data = gsheets_api.open('betfair_markets').worksheet("elo")
    markets = data.get_all_records()
    for n in range(0,len(markets)):
        if markets[n]['complete_10'] == 1:
            elo_marketIDs.append('1.'+str(markets[n]['elo_market_id']))
    return elo_marketIDs


def import_htft_markets(gsheets_api):
    htft_matchoddsIDs = []
    htft_htftIDs = []
    htft_half_time_results = []
    data = gsheets_api.open('betfair_markets').worksheet("htft")
    markets = data.get_all_records()
    for n in range(0,len(markets)):
        if markets[n]['complete_10'] == 1:
            htft_matchoddsIDs.append('1.'+str(markets[n]['match_odds_market_id']))
            htft_htftIDs.append('1.' + str(markets[n]['htft_market_id']))
            htft_half_time_results.append(markets[n]['half_time_result'])
    return htft_matchoddsIDs, htft_htftIDs, htft_half_time_results


def import_betdaq_markets(gsheets_api):
    betdaq_marketIDs = []
    betfair_marketIDs = []
    betdaq_market_names = []
    data = gsheets_api.open('betfair_markets').worksheet("betdaq")
    markets = data.get_all_records()
    for n in range(0,len(markets)):
        if markets[n]['complete_10'] == 1:
            betdaq_marketIDs.append(str(markets[n]['betdaq_market_id']))
            betfair_marketIDs.append('1.' + str(markets[n]['betfair_market_id']))
            betdaq_market_names.append(str(markets[n]['market_name']))
    return betfair_marketIDs, betdaq_marketIDs, betdaq_market_names

