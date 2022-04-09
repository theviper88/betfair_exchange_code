## TO DO ##
# heartbeat api

import time
import lib_api_commands
import lib_markets_import
import lib_thread_management
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import lib_betdaq_commands
from betdaq.apiclient import APIClient
from betdaq.endpoints.marketdata import MarketData

## connect to Google Sheets ##
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('exchange-markets-9b43e33952cc.json', scope)
gsheets_api = gspread.authorize(credentials)

## connect to Betfair ##
data = gsheets_api.open('betfair_markets').worksheet("creds")
credentials = data.get_all_records()
sessionToken = lib_api_commands.loginAPING(credentials[0]['bf_user'],credentials[0]['bf_pw'])
bd_username = credentials[0]['bd_user']
bd_password = credentials[0]['bd_pw']
appKey = credentials[0]['bf_appkey']

## connect to Betdaq ##
betdaq_api = APIClient(bd_username, bd_password)
betdaq_api2 = lib_betdaq_commands.BetdaqApi()
betdaq_api_data = MarketData(betdaq_api)
                
N = 0
while N < 1:
    ## check if live ##
    gsheets_api.login()
    data = gsheets_api.open('betfair_markets').worksheet("creds")
    credentials = data.get_all_records()
    if credentials[0]['ALL_ON'] == 1:
        ## find active threads ##
        active_threads = lib_thread_management.list_active_treads()
        ## import market IDs and create new threads ##
        if credentials[0]['each_way_on'] == 1:
            ew_winmarketIDs, ew_placemarketIDs, ew_eachwaymarketIDs = lib_markets_import.import_ew_markets(gsheets_api)
            lib_thread_management.create_ew_threads(appKey, sessionToken, gsheets_api, active_threads, ew_winmarketIDs, ew_placemarketIDs, ew_eachwaymarketIDs)
        if credentials[0]['mo&btts_on'] == 1:
            mobtts_correctscoreIDs, mobtts_moandbttsIDs = lib_markets_import.import_mobtts_markets(gsheets_api)
            lib_thread_management.create_mobtts_threads(appKey, sessionToken, gsheets_api, active_threads, mobtts_correctscoreIDs, mobtts_moandbttsIDs)
        if credentials[0]['half_time_on'] == 1:
            ht_htftIDs, ht_halftimeIDs = lib_markets_import.import_ht_markets(gsheets_api)
            lib_thread_management.create_ht_threads(appKey, sessionToken, gsheets_api, active_threads, ht_htftIDs, ht_halftimeIDs)
        if credentials[0]['elo_on'] == 1:
            elo_marketIDs = lib_markets_import.import_elo_markets(gsheets_api)
            lib_thread_management.create_elo_threads(appKey, sessionToken, gsheets_api, active_threads, elo_marketIDs)
        if credentials[0]['htft_on'] == 1:
            htft_matchoddsIDs, htft_htftIDs, htft_half_time_results = lib_markets_import.import_htft_markets(gsheets_api)
            lib_thread_management.create_htft_threads(appKey, sessionToken, gsheets_api, active_threads, htft_matchoddsIDs, htft_htftIDs, htft_half_time_results)
        if credentials[0]['betdaq_on'] == 1:
            betfair_marketIDs, betdaq_marketIDs, betdaq_market_names = lib_markets_import.import_betdaq_markets(gsheets_api)
            lib_thread_management.create_betdaq_threads(bd_username, bd_password, appKey, sessionToken, gsheets_api, betdaq_api, betdaq_api2, betdaq_api_data, bd_username, active_threads, betfair_marketIDs, betdaq_marketIDs, betdaq_market_names)
    else:
        #cancel all bets?
        print('\nAll Betting Paused')
    if len(active_threads) > 0:
        time.sleep(60)
    else:
        time.sleep(600)
