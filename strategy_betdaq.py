import lib_api_commands
import lib_dn_tasks
import sqlite3
import datetime
import numpy as np
from betdaq.filters import create_order, update_order
from betdaq.enums import Boolean, PriceFormat


def betdaq(sessionToken, appKey, api, api2, api_data, \
                 bfBook, bdBook, bet_ids,  \
                 betfairID, betdaqID, betdaq_name, strategy_name, \
                 trading_stake, max_liability, margin_multiplier_1, margin_multiplier_2):
                
    # Betfair odds
    runner_dict = {'Sheffield Utd': 'Sheff Utd', 'Leeds United': 'Leeds', 'Sungjae Im': 'Sung-Jae Im', 'Byeong Hun An': 'Byeong-Hun An', 'Haotong Li': 'Hao Tong Li', \
                   'Kings Lynn': 'King\'s Lynn', 'Atalantas Boy': 'Atalanta\'s Boy', 'Bernardo OReilly': 'Bernardo O\'Reilly', 'Louie de Palma': 'Louie De Palma'}
    bfDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, betfairID)
    betfair_odds = {}
    bfrunners = bfBook[0]['runners']
    for runner in range(0,len(bfrunners)):
        runner_name = bfDeets['result'][0]['runners'][runner]['runnerName']
        runner_name = runner_name.lstrip()
        runner_name = runner_dict.get(runner_name, runner_name)
        if (len(bfrunners[runner]['ex']['availableToBack']) > 0) & ~(runner_name in ['Tyrrell Hatton']): 
            betfair_odds[runner_name] = bfrunners[runner]['ex']['availableToBack'][0]['price']

    # get Betdaq market details
    #market_deets = bdBook
    market_prices = api.marketdata.get_prices(market_ids=[betdaqID], NumberForPricesRequired=2, NumberAgainstPricesRequired=0)
    runners = {}
    betdaq_runners = {}
    betdaq_odds = {}
    betdaq_SelectionResetCount = {}
    withdrawalSequenceNumber = bdBook[0]['withdrawal_sequence_number']
    race_grade = bdBook[0]['race_grade']
    for runner in bdBook[0]['runners']:
        if runner['runner_status'] == 'Active':
            runner_name = runner['runner_name']
            if race_grade is not None:
                runner_name = runner_name[3:]
            if betdaq_name == 'Correct Score':
                home = bdBook[0]['runners'][0]['runner_name']
                home = home[:len(home)-4]
                away = bdBook[0]['runners'][10]['runner_name']
                away = away[:len(away)-4]
                if runner_name[:len(runner_name)-4] == home:
                    runner_name = runner_name[len(runner_name)-3:]
                    runner_name = " ".join(runner_name)
                elif runner_name[:len(runner_name)-4] == away:
                    runner_name = runner_name[len(runner_name)-3:][::-1]
                    runner_name = " ".join(runner_name)
                elif runner_name[:5] == 'Draw ':
                    runner_name = runner_name[5:8]
                    runner_name = " ".join(runner_name)
            if runner_name in betfair_odds.keys():
                betdaq_SelectionResetCount[runner_name] = runner['reset_count']
    for runner in market_prices[0]['runners']:
        if runner['runner_status'] == 'Active':
            runner_name = runner['runner_name']
            if race_grade is not None:
                runner_name = runner_name[3:]
            if betdaq_name == 'Correct Score':
                home = bdBook[0]['runners'][0]['runner_name']
                home = home[:len(home)-4]
                away = bdBook[0]['runners'][10]['runner_name']
                away = away[:len(away)-4]
                if runner_name[:len(runner_name)-4] == home:
                    runner_name = runner_name[len(runner_name)-3:]
                    runner_name = " ".join(runner_name)
                elif runner_name[:len(runner_name)-4] == away:
                    runner_name = runner_name[len(runner_name)-3:][::-1]
                    runner_name = " ".join(runner_name)
                elif runner_name[:5] == 'Draw ':
                    runner_name = runner_name[5:8]
                    runner_name = " ".join(runner_name)
            if runner_name in betfair_odds.keys():
                betdaq_runners[runner_name] = runner['runner_id']
    for runner in market_prices[0]['runners']:
        if runner['runner_status'] == 'Active':
            runner_name = runner['runner_name']
            if race_grade is not None:
                runner_name = runner_name[3:]
            if betdaq_name == 'Correct Score':
                home = bdBook[0]['runners'][0]['runner_name']
                home = home[:len(home)-4]
                away = bdBook[0]['runners'][10]['runner_name']
                away = away[:len(away)-4]
                if runner_name[:len(runner_name)-4] == home:
                    runner_name = runner_name[len(runner_name)-3:]
                    runner_name = " ".join(runner_name)
                elif runner_name[:len(runner_name)-4] == away:
                    runner_name = runner_name[len(runner_name)-3:][::-1]
                    runner_name = " ".join(runner_name)
                elif runner_name[:5] == 'Draw ':
                    runner_name = runner_name[5:8]
                    runner_name = " ".join(runner_name)
            if runner_name in betfair_odds.keys():
                prev_odds = 0
                remaining_stake = 0
                if betdaq_runners[runner_name] in bet_ids:
                    bet_id = bet_ids[betdaq_runners[runner_name]]
                    order = api.betting.get_single_order(bet_id)
                    remaining_stake = order[0]['remaining_size']
                    prev_odds = order[0]['requested_price']
                if len(runner['runner_book']['batb']) == 0:
                    runner_price = 1
                elif (runner['runner_book']['batb'][0][1] == prev_odds) & (runner['runner_book']['batb'][0][2]==remaining_stake):
                    runner_price = runner['runner_book']['batb'][1][1]
                else:
                    runner_price = runner['runner_book']['batb'][0][1]
                betdaq_odds[runner_name] = runner_price

    # calculate current EV & Liability
    matched_volume = 0
    expected_value = 0
    pnl_positions = [0]

    # load Odds Ladder
    odds_ladder = api_data.get_odds_ladder(PriceFormat=PriceFormat.Decimal.value)
    odds_ladder_prices = []
    for tick in odds_ladder:
        odds_ladder_prices = odds_ladder_prices + [tick['price']]

    # calculate lay odds
    lay_odds = {}
    for runner in betdaq_odds:
        if betdaq_odds[runner] >= ((betfair_odds[runner]-1)*(1-margin_multiplier_2))+1:
            raw_lay_odds = ((betfair_odds[runner]-1)*(1-margin_multiplier_2))+1
            lay_odds[runner] = max([i for i in odds_ladder_prices if i <= raw_lay_odds])
        elif betdaq_odds[runner] <= ((betfair_odds[runner]-1)*(1-margin_multiplier_1))+1:
            raw_lay_odds = ((betfair_odds[runner]-1)*(1-margin_multiplier_1))+1
            lay_odds[runner] = max([i for i in odds_ladder_prices if i <= raw_lay_odds])
        else:
            lay_odds[runner] = min([i for i in odds_ladder_prices if i > betdaq_odds[runner]])

    # place lay bets
    order_list = []
    update_list = []
    for runner in betdaq_runners:
        odds = min(lay_odds[runner],100)
        stake = max(round(trading_stake/odds),1)
        remaining_stake = 0
        status = 'Cancelled'
        if betdaq_runners[runner] in bet_ids:
            bet_id = bet_ids[betdaq_runners[runner]]
            order = api.betting.get_single_order(bet_id)
            remaining_stake = order[0]['remaining_size']
            prev_odds = order[0]['requested_price']
            status = order[0]['status']
        if (remaining_stake == 0) | (status=='Cancelled'):
            order = create_order(SelectionId=betdaq_runners[runner], Stake=stake, Price=odds, Polarity=2,
                                 ExpectedSelectionResetCount=betdaq_SelectionResetCount[runner], ExpectedWithdrawalSequenceNumber=withdrawalSequenceNumber,
                                 CancelOnInRunning=Boolean.T, CancelIfSelectionReset=Boolean.T, ExpiresAt=None,
                                 WithdrawalRepriceOption=1, KillType=4, FillOrKillThreshold=0.0, PunterReferenceNumber=1)
            order_list = order_list + [order]
        elif (remaining_stake != stake) | (prev_odds != odds):
            print('update bet')
            order = update_order(BetId=bet_ids[betdaq_runners[runner]], DeltaStake=stake-remaining_stake, Price=odds,
                                 ExpectedSelectionResetCount=betdaq_SelectionResetCount[runner], ExpectedWithdrawalSequenceNumber=withdrawalSequenceNumber,
                                 CancelOnInRunning=None, CancelIfSelectionReset=None, SetToBeSPIfUnmatched=None)
            update_list = update_list + [order]
    all_orders = []
    if len(order_list) > 0:
        for batch in range(int(np.ceil(len(order_list)/10))):
            batch_list = order_list[batch*10:(batch+1)*10] 
            bets = api.betting.place_orders(order_list=batch_list, WantAllOrNothingBehaviour=Boolean.F.value)
            all_orders = all_orders+bets
            for bet in bets:
                bet_ids[bet['runner_id']] = bet['order_id']
    if len(update_list) > 0:
        for batch in range(int(np.ceil(len(update_list)/10))):
            batch_list = update_list[batch*10:(batch+1)*10] 
            updates = api.betting.update_orders(order_list=batch_list)
            all_orders = all_orders+updates
            #for bet in updates:
            #    print(bet)
            #    bet_ids[bet['runner_id']] = bet['order_id']

    over_round = sum([1/value for key, value in lay_odds.items()])

    lib_dn_tasks.log_market_position(datetime.datetime.now(), betdaqID, 'betdaq', round(expected_value, 2), min([round(n, 2) for n in pnl_positions]), matched_volume)
    return round(expected_value, 2), min([round(n, 2) for n in pnl_positions]), bet_ids


