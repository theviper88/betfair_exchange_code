import lib_api_commands
import lib_markets_edit
import datetime


def ew_market_check(appKey, sessionToken, ew_eachwaymarketID, ew_placemarketID, ew_winmarketID, data, google_sheet):
    # get Betfair market parameters
    winmarketBook = lib_api_commands.getSelections(appKey, sessionToken, ew_winmarketID)
    placemarketBook = lib_api_commands.getSelections(appKey, sessionToken, ew_placemarketID)
    eachwaymarketBook = lib_api_commands.getSelections(appKey, sessionToken, ew_eachwaymarketID)
    # get Google Shets market parameters
    ew_eachwaymarketIDs = []
    for n in range(0,len(google_sheet)):
        if google_sheet[n]['complete_10'] == 1:
            ew_eachwaymarketIDs.append('1.'+str(google_sheet[n]['each_way_market_id']))
    # check if thread can continue
    if ew_eachwaymarketID not in ew_eachwaymarketIDs:
        print('\nEach Way Market '+ew_eachwaymarketID+' - Not In List')
        return 0, winmarketBook, placemarketBook, eachwaymarketBook
    elif str(eachwaymarketBook[0]['inplay']) != 'False' or str(winmarketBook[0]['inplay']) != 'False' or str(placemarketBook[0]['inplay']) != 'False':
        lib_markets_edit.make_in_play(ew_eachwaymarketID, 9, "each_way", data, google_sheet) 
        print ('\nEach Way Market '+ew_eachwaymarketID+' - In-Play')
        return 0, winmarketBook, placemarketBook, eachwaymarketBook
    elif str(eachwaymarketBook[0]['status']) != 'OPEN' or str(winmarketBook[0]['status']) != 'OPEN' or str(placemarketBook[0]['status']) != 'OPEN':
        print ('\nEach Way Market '+ew_eachwaymarketID+' - Suspended')
        return 0, winmarketBook, placemarketBook, eachwaymarketBook
    #elif eachwaymarketBook[0]['totalMatched'] == 0:
    #    print ('\nEach Way Market '+ew_eachwaymarketID+' - Empty')
    #    return 0, winmarketBook, placemarketBook, eachwaymarketBook
    else:
        return 1, winmarketBook, placemarketBook, eachwaymarketBook
    

def mobtts_market_check(appKey, sessionToken, mobtts_moandbttsID, mobtts_correctscoreID, data, google_sheet):
    # get Betfair market parameters
    correctscoreBook = lib_api_commands.getSelections(appKey, sessionToken, mobtts_correctscoreID)
    moandbttsBook = lib_api_commands.getSelections(appKey, sessionToken, mobtts_moandbttsID)
    mobtts_moandbttsIDs = []
    # get Google Shets market parameters
    for n in range(0,len(google_sheet)):
        if google_sheet[n]['complete_10'] == 1:
            mobtts_moandbttsIDs.append('1.'+str(google_sheet[n]['mo&btts_market_id']))
    # check if thread can continue
    if mobtts_moandbttsID not in mobtts_moandbttsIDs:
        print('\nMO & BTTS Market '+bd_betdaqID+' - Not In List')
        return 0, correctscoreBook, moandbttsBook
    elif str(moandbttsBook[0]['inplay']) != 'False' or str(correctscoreBook[0]['inplay']) != 'False':
        lib_markets_edit.make_in_play(mobtts_moandbttsID, 6, "mo&btts", data, google_sheet)
        print ('\nMO & BTTS Market '+mobtts_moandbttsID+' - In-Play')
        return 0, correctscoreBook, moandbttsBook
    elif str(moandbttsBook[0]['status']) != 'OPEN' or str(correctscoreBook[0]['status']) != 'OPEN':
        print ('\nMO & BTTS Market '+mobtts_moandbttsID+' - Suspended')
        return 0, correctscoreBook, moandbttsBook
    else:
        return 1, correctscoreBook, moandbttsBook


def ht_market_check(appKey, sessionToken, ht_halftimeID, ht_htftID, data, google_sheet):
    # get Betfair market parameters
    htftBook = lib_api_commands.getSelections(appKey, sessionToken, ht_htftID)
    halftimeBook = lib_api_commands.getSelections(appKey, sessionToken, ht_halftimeID)
    # get Google Shets market parameters
    ht_halftimeIDs = []
    for n in range(0,len(google_sheet)):
        if google_sheet[n]['complete_10'] == 1:
            ht_halftimeIDs.append('1.'+str(google_sheet[n]['half_time_market_id']))
    # check if thread can continue
    if ht_halftimeID not in ht_halftimeIDs:
        print('\nHalf Time Market '+bd_betdaqID+' - Not In List')
        return 0, htftBook, halftimeBook
    elif str(halftimeBook[0]['inplay']) != 'False' or str(htftBook[0]['inplay']) != 'False':
        lib_markets_edit.make_in_play(ht_halftimeID, 6, "half_time", data, google_sheet)
        print ('\nHalf Time Market '+ht_halftimeID+' - In-Play')
        return 0, htftBook, halftimeBook
    elif str(halftimeBook[0]['status']) != 'OPEN' or str(htftBook[0]['status']) != 'OPEN':
        print ('\nHalf Time Market '+ht_halftimeID+' - Suspended')
        return 0, htftBook, halftimeBook
    else:
        return 1, htftBook, halftimeBook


def elo_market_check(appKey, sessionToken, marketID, data, google_sheet):
    # get Betfair market parameters
    marketBook = lib_api_commands.getSelections(appKey, sessionToken, marketID)
    # get Google Shets market parameters
    marketIDs = []
    for n in range(0,len(google_sheet)):
        if google_sheet[n]['complete_10'] == 1:
            marketIDs.append('1.'+str(google_sheet[n]['elo_market_id']))
    # check if thread can continue
    if marketID not in marketIDs:
        print('\nELO Market '+bd_betdaqID+' - Not In List')
        return 0, marketBook
    elif str(marketBook[0]['inplay']) != 'False':
        lib_markets_edit.make_in_play(marketID, 6, "elo", data, google_sheet)
        print ('\nELO Market '+marketID+' - In-Play')
        return 0, marketBook
    elif str(marketBook[0]['status']) != 'OPEN':
        print ('\nELO Market '+marketID+' - Suspended')
        return 0, marketBook
    else:
        return 1, marketBook


def htft_market_check(appKey, sessionToken, htft_matchoddsID, htft_htftID, half_time_result, data, google_sheet):
    # get Betfair market parameters
    matchoddsBook = lib_api_commands.getSelections(appKey, sessionToken, htft_matchoddsID)
    htftBook = lib_api_commands.getSelections(appKey, sessionToken, htft_htftID)
    # get Google Sheets market parameters
    htft_matchoddsIDs = []
    for n in range(0,len(google_sheet)):
        if google_sheet[n]['complete_10'] == 1:
            htft_matchoddsIDs.append('1.'+str(google_sheet[n]['match_odds_market_id']))
    # check if thread can continue
    if htft_matchoddsID not in htft_matchoddsIDs:
        print('\nHTFT Market '+bd_betdaqID+' - Not In List')
        return 0, matchoddsBook, htftBook
    elif str(matchoddsBook[0]['inplay']) != 'True' or str(htftBook[0]['inplay']) != 'True':
        lib_markets_edit.make_in_play(htft_htftID, 7, "htft", data, google_sheet)
        print ('\nHTFT Market '+htft_htftID+' - Not In-Play')
        return 0, matchoddsBook, htftBook
    elif str(matchoddsBook[0]['status']) != 'OPEN' or str(htftBook[0]['status']) != 'OPEN':
        print ('\nHTFT Market '+htft_htftID+' - Suspended')
        return 0, matchoddsBook, htftBook
    elif half_time_result not in ['home', 'away', 'draw']:
        return 0, matchoddsBook, htftBook
    else:
        return 1, matchoddsBook, htftBook


def bd_market_check(appKey, sessionToken, betdaq_api, betdaq_api2, bd_betfairID, bd_betdaqID, data, google_sheet):
    # get Betfair/Betdaq market parameters
    bfBook = lib_api_commands.getSelections(appKey, sessionToken, bd_betfairID)
    bdBook = betdaq_api.marketdata.get_markets(market_ids=[bd_betdaqID])
    time_to_off = (datetime.datetime.strptime(bdBook[0]['market_start_time'], '%Y-%m-%d %H:%M:%S.%f') - datetime.datetime.now()).seconds
    # get Google Shets market parameters
    bd_betfairIDs = []
    for n in range(0,len(google_sheet)):
        if google_sheet[n]['complete_10'] == 1:
            bd_betfairIDs.append('1.'+str(google_sheet[n]['betfair_market_id']))
    # check if thread can continue
    if bd_betfairID not in bd_betfairIDs:
        print('\nBETDAQ Market '+bd_betdaqID+' - Not In List')
        return 0, bfBook, bdBook
    if str(bfBook[0]['inplay']) != 'False' or str(bdBook[0]['in_play']) != 'False':
        lib_markets_edit.make_in_play(bd_betfairID, 7, "betfair", data, google_sheet)
        print('\nBETDAQ Market '+bd_betdaqID+' - In-Play')
        return 0, bfBook, bdBook
    elif str(bfBook[0]['status']) != 'OPEN' or str(bdBook[0]['market_status']) != 'ACTIVE':
        print('\nBETDAQ Market '+bd_betdaqID+' - Suspended')
        return 0, bfBook, bdBook
    elif time_to_off < 60*15:
        lib_markets_edit.make_in_play(bd_betfairID, 7, "betfair", data, google_sheet)
        print('\nBETDAQ Market '+bd_betdaqID+' - Close to off')
        return 0, bfBook, bdBook
    else:
        return 1, bfBook, bdBook

