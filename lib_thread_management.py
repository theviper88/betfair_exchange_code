import lib_api_commands
import lib_markets_edit
import class_each_way
import class_mo_and_btts
import class_half_time
import class_elo_ratings
import class_halftime_fulltime
import class_betdaq
import threading
import importlib
import time


###########################################################

def create_ew_threads(appKey, sessionToken, gsheets_api, active_threads,
                      ew_winmarketIDs, ew_placemarketIDs, ew_eachwaymarketIDs):
    market_list = ew_eachwaymarketIDs
    for n in range(0,len(market_list)):
        if 'Each Way: '+market_list[n] not in active_threads:
            ew_thread = threading.Thread(name = 'Each Way: '+market_list[n],
                                         target = class_each_way.each_way_class,
                                         args = (sessionToken, appKey, gsheets_api, ew_winmarketIDs[n], ew_placemarketIDs[n], ew_eachwaymarketIDs[n],))
            ew_thread.start()
            time.sleep(1)

###########################################################

def create_mobtts_threads(appKey, sessionToken, gsheets_api, active_threads,
                          mobtts_correctscoreIDs, mobtts_moandbttsIDs):
    market_list = mobtts_moandbttsIDs
    for n in range(0,len(mobtts_moandbttsIDs)):
        if 'MO & BTTS: '+market_list[n] not in active_threads:
            mobtts_thread = threading.Thread(name = 'MO & BTTS: '+market_list[n],
                                             target = class_mo_and_btts.mo_and_btts_class,
                                             args = (sessionToken, appKey, gsheets_api, mobtts_correctscoreIDs[n], mobtts_moandbttsIDs[n],))
            mobtts_thread.start()
            time.sleep(1)

###########################################################

def create_ht_threads(appKey, sessionToken, gsheets_api, active_threads,
                      ht_htftIDs, ht_halftimeIDs):
    market_list = ht_halftimeIDs
    for n in range(0,len(ht_halftimeIDs)):
        if 'Half Time: '+market_list[n] not in active_threads:
            ht_thread = threading.Thread(name = 'Half Time: '+market_list[n],
                                         target = class_half_time.half_time_class,
                                         args = (sessionToken, appKey, gsheets_api, ht_htftIDs[n], ht_halftimeIDs[n],))
            ht_thread.start()
            time.sleep(1)

###########################################################

def create_elo_threads(appKey, sessionToken, gsheets_api, active_threads,
                       elo_marketIDs):
    market_list = elo_marketIDs
    for n in range(0,len(elo_marketIDs)):
        if 'Elo: '+market_list[n] not in active_threads:
            eld_thread = threading.Thread(name = 'Elo: '+market_list[n],
                                          target = class_elo_ratings.elo_ratings_class,
                                          args = (sessionToken, appKey, gsheets_api, elo_marketIDs[n]))
            eld_thread.start()
            time.sleep(1)

###########################################################

def create_htft_threads(appKey, sessionToken, gsheets_api, active_threads,
                        htft_matchoddsIDs, htft_htftIDs, htft_half_time_results):
    market_list = htft_htftIDs
    for n in range(0,len(htft_htftIDs)):
        if 'HT/FT: '+market_list[n] not in active_threads:
            htft_thread = threading.Thread(name = 'HT/FT: '+market_list[n],
                                           target = class_halftime_fulltime.halftime_fulltime_class,
                                           args = (sessionToken, appKey, gsheets_api, htft_matchoddsIDs[n], htft_htftIDs[n], htft_half_time_results[n]))
            htft_thread.start()
            time.sleep(1)

###########################################################

def create_betdaq_threads(bd_username, bd_password, appKey, sessionToken, gsheets_api, betdaq_api, betdaq_api2, betdaq_api_data, username, active_threads,
                          betfair_marketIDs, betdaq_marketIDs, betdaq_market_names):
    market_list = betdaq_marketIDs
    for n in range(0,len(betdaq_marketIDs)):
        events = betdaq_api2.get_events(market_list[n], bd_username)
        #print(events)
        market_names = []
        for market in events[1]:
            market_names.append(market[0])
        market_index = market_names.index(betdaq_market_names[n])
        market_id = str(events[1][market_index][1])
        if 'BETDAQ: '+market_id not in active_threads:
            betdaq_thread = threading.Thread(name = 'BETDAQ: '+market_id,
                                             target = class_betdaq.betdaq_class,
                                             args = (bd_username, bd_password, sessionToken, appKey, gsheets_api, betdaq_api, betdaq_api2, betdaq_api_data, betfair_marketIDs[n], market_id, betdaq_market_names[n]))
            betdaq_thread.start()
            time.sleep(1)

###########################################################

def list_active_treads():
    active_threads = []
    print('\nActive Threads:')
    for thread in threading.enumerate():
        active_threads.append(thread.name)
        print(thread.name)
    return active_threads
