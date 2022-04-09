import lib_api_commands
import lib_dn_tasks
import sqlite3
import datetime


def elo_ratings(sessionToken, appKey, marketBook, marketID, sport, no_frames, strategy_name,\
                trading_bankroll, max_runner_liability, max_market_liability, \
                old_tolay_prices, old_toback_prices, back_bet_ids, lay_bet_ids, selectionIds, selectionIds_liability, pnl_positions, ev_trend):

    # check liability  
    market_position = lib_api_commands.findPnL(appKey, sessionToken, marketID, str(0), str(0), str(1))
            
    # get market details
    marketDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, marketID)
    runners = marketBook[0]['runners']
    for market in marketBook:
        selection_names = []
        for runner in range(0,len(runners)):
           # correct for naming inconsistencies - MANUAL
           if marketDeets['result'][0]['runners'][runner]['runnerName'] == 'David Gilbert':
               selection_names.append('Dave Gilbert')    
           elif marketDeets['result'][0]['runners'][runner]['runnerName'] == 'Matthew Selt':
               selection_names.append('Matt Selt')
           elif marketDeets['result'][0]['runners'][runner]['runnerName'] == 'Alexander Ursenbacher':
               selection_names.append('Alexander Ursenbache')
           else:
               selection_names.append(marketDeets['result'][0]['runners'][runner]['runnerName'].replace("'", " "))

    # check P&L positions
    market_position = lib_api_commands.findPnL(appKey, sessionToken, marketID, str(0), str(0), str(1))
    for runner in range(0,len(runners)):
        selectionIds[runner] = marketBook[0]['runners'][runner]['selectionId']
        selectionIds_liability[runner] = market_position[0]['profitAndLosses'][runner]['selectionId']
        pnl_positions[runner] = market_position[0]['profitAndLosses'][runner]['ifWin']
    liability_runner_index = [selectionIds_liability.index(i) for i in selectionIds]
    pnl_positions = [pnl_positions[i] for i in liability_runner_index]                 
           
    # check market parameters are ok
    if len(runners) != 2:
        order = lib_api_commands.cancelOrders(str(moandbttsID), appKey, sessionToken)
        print ('Error Market '+moandbttsID+': There are ' +str(len(runners))+ ' runners - 2 expected')
        lay_bet_ids = lay_bet_ids*0
    else:

        # calculate matched volume
        matched_bets = lib_api_commands.currentOrders(marketID, 'ALL', appKey, sessionToken)
        matched_volume = 0
        for bet in range(0,len(matched_bets['currentOrders'])):
            matched_volume = matched_volume+matched_bets['currentOrders'][0]['sizeMatched']
           
        # find current back prices (excluding our bets)
        back_prices = [0 for i in range(0,len(runners))]
        for runner in range(0,len(runners)):
            # find our bet status
            if lay_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
            # compare to available bets 
            if len(runners[runner]['ex']['availableToBack']) == 0:
                back_prices[runner] = 'N/A'
            elif old_tolay_prices[runner] == runners[runner]['ex']['availableToBack'][0]['price'] and sizeRemaining > 0:
                if len(runners[runner]['ex']['availableToBack']) > 1:
                    back_prices[runner] = runners[runner]['ex']['availableToBack'][1]['price']
                else:
                    back_prices[runner] = 'N/A'                     
            else:
                back_prices[runner] = runners[runner]['ex']['availableToBack'][0]['price']

        # find current back prices (excluding our bets)
        back_prices = [0 for i in range(0,len(runners))]
        for runner in range(0,len(runners)):
            # find our bet status
            if lay_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
            # compare to available bets 
            if len(runners[runner]['ex']['availableToBack']) == 0:
                back_prices[runner] = 'N/A'
            elif old_tolay_prices[runner] == runners[runner]['ex']['availableToBack'][0]['price'] and sizeRemaining > 0:
                if len(runners[runner]['ex']['availableToBack']) > 1:
                    back_prices[runner] = runners[runner]['ex']['availableToBack'][1]['price']
                else:
                    back_prices[runner] = 'N/A'                     
            else:
                back_prices[runner] = runners[runner]['ex']['availableToBack'][0]['price']

        # find current lay prices (excluding our bets)
        lay_prices = [0 for i in range(0,len(runners))]
        for runner in range(0,len(runners)):
            # find our bet status
            if back_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(back_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
            # compare to available bets 
            if len(runners[runner]['ex']['availableToLay']) == 0:
                lay_prices[runner] = 'N/A'
            elif old_toback_prices[runner] == runners[runner]['ex']['availableToLay'][0]['price'] and sizeRemaining > 0:
                if len(runners[runner]['ex']['availableToLay']) > 1:
                    lay_prices[runner] = runners[runner]['ex']['availableToLay'][1]['price']
                else:
                    lay_prices[runner] = 'N/A'                     
            else:
                lay_prices[runner] = runners[runner]['ex']['availableToLay'][0]['price']
                
        
        # calculate new prices
        # estimate player probabilities & find next-but-one prices
        player_frame_probs = [0 for i in range(0,len(runners))]
        player_match_probs = [0 for i in range(0,len(runners))]
        player_elos = [0 for i in range(0,len(runners))]
        back_butone = [0 for i in range(0,len(runners))]
        new_tolay_prices = [0 for i in range(0,len(runners))]
        lay_butone = [0 for i in range(0,len(runners))]
        new_toback_prices = [0 for i in range(0,len(runners))]
        connection = sqlite3.connect('exchange.db')
        with connection:
            cur = connection.cursor()
            for runner in range(0,len(runners)):
                cur.execute("select player_elo from snooker_elos where player_name = ?", [selection_names[runner]])
                player_elos[runner] = cur.fetchall()[0][0]
            player_frame_probs[0] = (1 / (1 + 10 ** ((player_elos[1] - player_elos[0]) / 400)))
            player_frame_probs[1] = 1-player_frame_probs[0]
            player_match_prob = 0
            for frames in range(int((no_frames+1)/2), no_frames+1):
                score_prob = lib_dn_tasks.ncr(no_frames, frames)*(player_frame_probs[0]**frames)*(player_frame_probs[1]**(no_frames-frames))
                player_match_prob = player_match_prob + score_prob                                                                                 
            player_match_probs[0] = player_match_prob
            player_match_probs[1] = 1-player_match_probs[0]
            raw_prices = [1/i for i in player_match_probs]
            
            for runner in range(0,len(runners)):
                if back_prices[runner] =='N/A':
                    back_butone[runner] = 1
                else:
                    cur.execute("select next_price_up from odds_ladder where price = ?", [back_prices[runner]])
                    back_butone[runner] = cur.fetchall()[0][0]
                if lay_prices[runner] =='N/A':
                    lay_butone[runner] = 1001
                else:
                    cur.execute("select next_price_down from odds_ladder where price = ?", [lay_prices[runner]])
                    lay_butone[runner] = cur.fetchall()[0][0]    
                # final tolay price
                if raw_prices[runner] > back_butone[runner]:
                    new_tolay_prices[runner] = back_butone[runner]
                else:
                    new_tolay_prices[runner] = 1
                # final toback price
                if raw_prices[runner] < lay_butone[runner]:
                    new_toback_prices[runner] = lay_butone[runner]
                else:
                    new_toback_prices[runner] = 1001   
        back_over_round = sum([1/i for i in new_tolay_prices])
        lay_over_round = sum([1/i for i in new_toback_prices])

        # estimate expected value
        expeted_value = sum([j * i for j, i in zip(player_match_probs, pnl_positions)])
        ev_trend.append(expeted_value)
        
        # place bets in market
        for runner in range(0,len(runners)):
            # lay bets
            if lay_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']
            if new_tolay_prices[runner] != old_tolay_prices[runner] or sizeRemaining == 0:
                #suggested_stake = round(-trading_bankroll*(((new_tolay_prices[runner]-1)/0.95)*(player_match_probs[runner])-(1-(player_match_probs[runner])))/((new_tolay_prices[runner]-1)/0.95),0)
                max_stake = round(((pnl_positions[runner]+max_market_liability)/max(new_tolay_prices[runner],1.01))/2,0)
                stake = max_stake #min(max(suggested_stake,2),max_stake)
                if stake < 2 or pnl_positions[runner] < -max_runner_liability or new_tolay_prices[runner] < 1.01 :    
                    if sizeRemaining == 0:
                        lay_bet_ids[runner] = 0 
                        result = '' + selection_names[runner] + ' Lay - No longer Laying'
                    else:
                        order = lib_api_commands.cancelBet(str(marketID), str(lay_bet_ids[runner]), appKey, sessionToken)
                        lay_bet_ids[runner] = 0
                        result = '' + selection_names[runner] + ' Lay - No longer Laying'
                elif lay_bet_ids[runner] == 0:
                    order = lib_api_commands.doWager(str(marketID), str(runners[runner]['selectionId']), "LAY", str(stake), str(new_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketID) + str(runners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                    lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                    result = '' + selection_names[runner] + ' Lay - New Bet Placed'
                else:
                    if sizeRemaining == 0:
                        order = lib_api_commands.doWager(str(marketID), str(runners[runner]['selectionId']), "LAY", str(stake), str(new_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketID) + str(runners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                        lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                        result = '' + selection_names[runner] + ' Lay - New Bet Placed'
                    else:
                        order = lib_api_commands.replaceBet(str(marketID), str(lay_bet_ids[runner]), str(new_tolay_prices[runner]), strategy_name + str(marketID) + str(runners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                        lay_bet_ids[runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
                        result = '' + selection_names[runner] + ' Lay - Odds Updated'       
            else:
                eggs = 'eggs'               
            # back bets
##            if back_bet_ids[runner] == 0:
##                sizeRemaining = 0
##            else:
##                status = lib_api_commands.betStatus(back_bet_ids[runner], appKey, sessionToken)
##                sizeRemaining = status['currentOrders'][0]['sizeRemaining']
##            if new_toback_prices[runner] != old_toback_prices[runner] or sizeRemaining == 0:
##                suggested_stake = round(trading_bankroll*(((((new_toback_prices[runner]-1)*0.95)*(player_match_probs[runner])-(1-(player_match_probs[runner])))/((new_toback_prices[runner]-1)*0.95))),0)
##                print((new_toback_prices[runner]-1)*0.95)
##                max_stake = round(((pnl_positions[runner]+max_market_liability)/max(new_toback_prices[runner],1.01))/2,0)
##                stake = min(suggested_stake,max_stake)
##                if stake < 2 or (pnl_positions[runner] != min(pnl_positions) and min(pnl_positions) < -max_runner_liability) or new_toback_prices[runner] > 1000 :    #####
##                    if sizeRemaining == 0:
##                        back_bet_ids[runner] = 0
##                        result = '' + selection_names[runner] + ' Back - No longer Backing'
##                    else:
##                        order = lib_api_commands.cancelBet(str(marketID), str(back_bet_ids[runner]), appKey, sessionToken)
##                        back_bet_ids[runner] = 0
##                        result = '' + selection_names[runner] + ' Back - No longer Backing'
##                elif back_bet_ids[runner] == 0:
##                    order = lib_api_commands.doWager(str(marketID), str(runners[runner]['selectionId']), "BACK", str(stake), str(new_toback_prices[runner]), 'LAPSE', strategy_name + str(marketID) + str(runners[runner]['selectionId']) + "BACK", appKey, sessionToken)
##                    back_bet_ids[runner] = order['instructionReports'][0]['betId']
##                    result = '' + selection_names[runner] + ' Back - New Bet Placed'
##                else:
##                    if sizeRemaining == 0:
##                        order = lib_api_commands.doWager(str(marketID), str(runners[runner]['selectionId']), "BACK", str(stake), str(new_toback_prices[runner]), 'LAPSE', strategy_name + str(marketID) + str(runners[runner]['selectionId']) + "BACK", appKey, sessionToken)
##                        back_bet_ids[runner] = order['instructionReports'][0]['betId']
##                        result = '' + selection_names[runner] + ' Back - New Bet Placed'
##                    else:
##                        order = lib_api_commands.replaceBet(str(marketID), str(back_bet_ids[runner]), str(new_toback_prices[runner]), strategy_name + str(marketID) + str(runners[runner]['selectionId']) + "BACK", appKey, sessionToken)
##                        back_bet_ids[runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
##                        result = '' + selection_names[runner] + ' Back - Odds Updated'    
##            else:
##                eggs = 'eggs'    
               
    old_tolay_prices = new_tolay_prices
    old_toback_prices = new_toback_prices
    #print('\nELO '+sport+' Market '+marketID+' - Expected Value: £' +str(round(expeted_value, 2))+'')                  
    #print('ELO '+sport+' Market '+marketID+' - Wost Outcome: £' +str(min([round(n, 2) for n in pnl_positions]))+'')
    lib_dn_tasks.log_market_position(datetime.datetime.now(), marketID, 'ELO', round(expeted_value, 2), min([round(n, 2) for n in pnl_positions]), matched_volume)
    return round(expeted_value, 2), min([round(n, 2) for n in pnl_positions])


