import lib_api_commands
import lib_dn_tasks
import sqlite3
import datetime


def hemisphere(sessionToken, appKey, \
               winnerBook, winnerID, hemisphereBook, hemisphereID, strategy_name, \
                trading_stake, max_runner_liability, max_market_liability, margin_multiplier_1, margin_multiplier_2, \
                old_hemisphere_tolay_prices, lay_bet_ids, old_hemisphere_toback_prices, back_bet_ids, \
                selectionIds, selectionIds_liability, pnl_positions, ev_trend):
                
        # get market details
        winnerDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, winnerID)
        hemisphereDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, hemisphereID)
        marketId = hemisphereBook[0]['marketId']

        # get runner details
        csrunners = correctscoreBook[0]['runners']
        moandbttsrunners = moandbttsBook[0]['runners']        
        correctscore_selection_names = []
        moandbtts_selection_names = []
        for runner in range(0,len(csrunners)):
            correctscore_selection_names.append(correctscoreDeets['result'][0]['runners'][runner]['runnerName'])
        for runner in range(0,len(moandbttsrunners)):
            moandbtts_selection_names.append(moandbttsDeets['result'][0]['runners'][runner]['runnerName'])

        # check P&L positions
        market_position = lib_api_commands.findPnL(appKey, sessionToken, moandbttsID, str(0), str(0), str(1))
        for runner in range(0,len(moandbttsrunners)):
            selectionIds[runner] = moandbttsBook[0]['runners'][runner]['selectionId']
            selectionIds_liability[runner] = market_position[0]['profitAndLosses'][runner]['selectionId']
            pnl_positions[runner] = market_position[0]['profitAndLosses'][runner]['ifWin']
        liability_runner_index = [selectionIds_liability.index(i) for i in selectionIds]
        pnl_positions = [pnl_positions[i] for i in liability_runner_index]                 
               
        # check market parameters are ok
        if len(csrunners) != 19:
            order = lib_api_commands.cancelOrders(str(moandbttsID), appKey, sessionToken)
            print ('Error Market '+moandbttsID+': There are ' +str(len(csrunners))+ ' Correct Score runners - 19 expected')
            lay_bet_ids = lay_bet_ids*0
        elif len(moandbttsrunners) != 6:
            order = lib_api_commands.cancelOrders(str(moandbttsID), appKey, sessionToken)
            print ('Error Market '+moandbttsID+': There are ' +str(len(moandbttsrunners))+ ' MO&BTTS runners - 6 expected')
            lay_bet_ids = lay_bet_ids*0
        else:

            # find current Correct Score back and lay prices
            correctscore_back_prices = [0 for i in range(0,len(csrunners))]
            correctscore_lay_prices = [0 for i in range(0,len(csrunners))]
            for runner in range(0,len(csrunners)):
                if len(csrunners[runner]['ex']['availableToBack']) == 0:
                    correctscore_back_prices[runner] = 'N/A'
                else:
                    correctscore_back_prices[runner] = csrunners[runner]['ex']['availableToBack'][0]['price']
                if len(csrunners[runner]['ex']['availableToLay']) == 0:
                    correctscore_lay_prices[runner] = 'N/A'
                else:
                    correctscore_lay_prices[runner] = csrunners[runner]['ex']['availableToLay'][0]['price'] 

            # estimate MO&BTTS probabilities
            correctscore_lay_estimate = [10000 if (x=='N/A' or x==0) else x for x in correctscore_lay_prices] # Malone's rule
            correctscore_back_estimate = [1+(1/10000) if (x=='N/A' or x==0) else x for x in correctscore_back_prices]
            correctscore_probs = [2/i for i in [j + i for j, i in zip(correctscore_lay_estimate, correctscore_back_estimate)]]
            correctscore_probs = [x/sum(correctscore_probs) for x in correctscore_probs]
            home_4_goals_prob = correctscore_probs[correctscore_selection_names.index('Any Other Home Win')]
            away_4_goals_prob = correctscore_probs[correctscore_selection_names.index('Any Other Away Win')]
            #btts_perc = 0.65#-(0.3*max(away_4_goals_prob,home_4_goals_prob))   # expected probability of both teams scoring given win/loss
            btts_home_perc = 1-((1/home_4_goals_prob)**-0.36)   # expected probability of both teams scoring given home win
            btts_away_perc = 1-((1/away_4_goals_prob)**-0.36)
            home_yes = [1.000 if x in ('2 - 1','3 - 1','3 - 2') else btts_home_perc if x == 'Any Other Home Win' else 0 for x in correctscore_selection_names]
            away_yes = [1.000 if x in ('1 - 2','1 - 3','2 - 3') else btts_away_perc if x == 'Any Other Away Win' else 0 for x in correctscore_selection_names]
            draw_yes = [1.000 if x in ('1 - 1','2 - 2','3 - 3','Any Other Draw') else 0 for x in correctscore_selection_names]
            home_no = [1.000 if x in ('1 - 0','2 - 0','3 - 0') else (1-btts_home_perc) if x == 'Any Other Home Win' else 0 for x in correctscore_selection_names]
            away_no = [1.000 if x in ('0 - 1','0 - 2','0 - 3') else (1-btts_away_perc) if x == 'Any Other Away Win' else 0 for x in correctscore_selection_names] 
            draw_no = [1.000 if x in ('0 - 0') else 0 for x in correctscore_selection_names] 
            weights = [home_yes,away_yes,draw_yes,home_no,away_no,draw_no] #assumes mo&btts selections are in a fixed order
            #is nested list comprehetion easier? -> probabilities = {el:[correctscore_probs] for el in range(0,6)}
            #are rounding errors significant?
            moandbtts_probs = []
            for runner in range(0,len(moandbttsrunners)):
                moandbtts_probs.append(sum([i*j for i,j in zip(weights[runner],correctscore_probs)]))
            moandbtts_probs = [x/sum(moandbtts_probs) for x in moandbtts_probs]
          
            # estimate expected value
            expeted_value = sum([j * i for j, i in zip(moandbtts_probs, pnl_positions)]) 
            ev_trend.append(expeted_value)

            # calculate matched volume
            matched_bets = lib_api_commands.currentOrders(moandbttsID, 'ALL', appKey, sessionToken)
            matched_volume = 0
            for bet in range(0,len(matched_bets['currentOrders'])):
                matched_volume = matched_volume+matched_bets['currentOrders'][0]['sizeMatched']
               
            # find current MO&BTTS back prices (excluding our bets)
            moandbtts_back_prices = [0 for i in range(0,len(moandbttsrunners))]
            for runner in range(0,len(moandbttsrunners)):
                # find our bet status
                if lay_bet_ids[runner] == 0:
                    sizeRemaining = 0
                else:
                    status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
                    sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
                # compare to available bets 
                if len(moandbttsrunners[runner]['ex']['availableToBack']) == 0:
                    moandbtts_back_prices[runner] = 'N/A'
                elif old_moandbtts_tolay_prices[runner] == moandbttsrunners[runner]['ex']['availableToBack'][0]['price'] and sizeRemaining > 0:
                    if len(moandbttsrunners[runner]['ex']['availableToBack']) > 1:
                        moandbtts_back_prices[runner] = moandbttsrunners[runner]['ex']['availableToBack'][1]['price']
                    else:
                        moandbtts_back_prices[runner] = 'N/A'                     
                else:
                    moandbtts_back_prices[runner] = moandbttsrunners[runner]['ex']['availableToBack'][0]['price']

            # find current MO&BTTS lay prices (excluding our bets)
            moandbtts_lay_prices = [0 for i in range(0,len(moandbttsrunners))]
            for runner in range(0,len(moandbttsrunners)):
                # find our bet status
                if back_bet_ids[runner] == 0:
                    sizeRemaining = 0
                else:
                    status = lib_api_commands.betStatus(back_bet_ids[runner], appKey, sessionToken)
                    sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
                # compare to available bets 
                if len(moandbttsrunners[runner]['ex']['availableToLay']) == 0:
                    moandbtts_lay_prices[runner] = 'N/A'
                elif old_moandbtts_toback_prices[runner] == moandbttsrunners[runner]['ex']['availableToLay'][0]['price'] and sizeRemaining > 0:
                    if len(moandbttsrunners[runner]['ex']['availableToLay']) > 1:
                        moandbtts_lay_prices[runner] = moandbttsrunners[runner]['ex']['availableToLay'][1]['price']
                    else:
                        moandbtts_lay_prices[runner] = 'N/A'                     
                else:
                    moandbtts_lay_prices[runner] = moandbttsrunners[runner]['ex']['availableToLay'][0]['price']
                    
            # calculate new MO&BTTS prices to lay
            raw_moandbtts_tolay_prices = [1.01 for i in range(0,len(moandbttsrunners))]
            raw_moandbtts_tolay_prices_margin_1 = [1.01 for i in range(0,len(moandbttsrunners))]
            raw_moandbtts_tolay_prices_margin_2 = [1.01 for i in range(0,len(moandbttsrunners))]
            correctscore_back_probs = [1/i for i in correctscore_back_estimate]
            for runner in range(0,len(moandbttsrunners)):
                raw_moandbtts_tolay_prices[runner] = 1/(sum([i*j for i,j in zip(weights[runner],correctscore_back_probs)])) 
                raw_moandbtts_tolay_prices_margin_1[runner] = ((raw_moandbtts_tolay_prices[runner]-1)*(1-margin_multiplier_1))+1
                raw_moandbtts_tolay_prices_margin_2[runner] = ((raw_moandbtts_tolay_prices[runner]-1)*(1-margin_multiplier_2))+1
            # calculate new MO&BTTS prices to back
            raw_moandbtts_toback_prices = [1000 for i in range(0,len(moandbttsrunners))]
            raw_moandbtts_toback_prices_margin_1 = [1000 for i in range(0,len(moandbttsrunners))]
            raw_moandbtts_toback_prices_margin_2 = [1000 for i in range(0,len(moandbttsrunners))]
            correctscore_lay_probs = [1/i for i in correctscore_lay_estimate]
            for runner in range(0,len(moandbttsrunners)):
                raw_moandbtts_toback_prices[runner] = 1/(sum([i*j for i,j in zip(weights[runner],correctscore_lay_probs)])) 
                raw_moandbtts_toback_prices_margin_1[runner] = ((raw_moandbtts_toback_prices[runner]-1)*(1+margin_multiplier_1))+1
                raw_moandbtts_toback_prices_margin_2[runner] = ((raw_moandbtts_toback_prices[runner]-1)*(1+margin_multiplier_2))+1    
            # fix prices to odds ladder
            moandbtts_back_butone = [0 for i in range(0,len(moandbttsrunners))]
            new_moandbtts_tolay_prices = [0 for i in range(0,len(moandbttsrunners))]
            moandbtts_lay_butone = [0 for i in range(0,len(moandbttsrunners))]
            new_moandbtts_toback_prices = [0 for i in range(0,len(moandbttsrunners))]
            connection = sqlite3.connect('exchange.db')
            with connection:
                cur = connection.cursor()
                for runner in range(0,len(moandbttsrunners)):
                    # find next-but-one prices
                    if moandbtts_back_prices[runner] =='N/A':
                        moandbtts_back_butone[runner] = 1
                    else:
                        cur.execute("select next_price_up from odds_ladder where price = ?", [moandbtts_back_prices[runner]])
                        moandbtts_back_butone[runner] = cur.fetchall()[0][0]
                    if moandbtts_lay_prices[runner] =='N/A':
                        moandbtts_lay_butone[runner] = 1001
                    else:
                        cur.execute("select next_price_down from odds_ladder where price = ?", [moandbtts_lay_prices[runner]])
                        moandbtts_lay_butone[runner] = cur.fetchall()[0][0]    
                    # final tolay price
                    if raw_moandbtts_tolay_prices[runner] < 1.01:
                        new_moandbtts_tolay_prices[runner] = 1
                    elif moandbtts_back_butone[runner] < raw_moandbtts_tolay_prices_margin_1[runner]:
                        cur.execute("select max(price) from odds_ladder where price <= ?", [raw_moandbtts_tolay_prices_margin_1[runner]])  
                        new_moandbtts_tolay_prices[runner] = cur.fetchall()[0][0]
                    elif moandbtts_back_butone[runner] > raw_moandbtts_tolay_prices_margin_2[runner]:
                        cur.execute("select max(price) from odds_ladder where price <= ?", [raw_moandbtts_tolay_prices_margin_2[runner]])  
                        new_moandbtts_tolay_prices[runner] = cur.fetchall()[0][0]
                    else:
                        new_moandbtts_tolay_prices[runner] = moandbtts_back_butone[runner]
                    # final toback price
                    if raw_moandbtts_toback_prices[runner] > 1000:
                        new_moandbtts_toback_prices[runner] = 1001
                    elif moandbtts_lay_butone[runner] > raw_moandbtts_toback_prices_margin_1[runner]:
                        cur.execute("select min(price) from odds_ladder where price >= ?", [raw_moandbtts_toback_prices_margin_1[runner]])  
                        new_moandbtts_toback_prices[runner] = cur.fetchall()[0][0]
                    elif moandbtts_lay_butone[runner] < raw_moandbtts_toback_prices_margin_2[runner]:
                        cur.execute("select min(price) from odds_ladder where price >= ?", [raw_moandbtts_toback_prices_margin_2[runner]])
                        new_moandbtts_toback_prices[runner] = cur.fetchall()[0][0]
                    else:
                        new_moandbtts_toback_prices[runner] = moandbtts_lay_butone[runner]    
            back_over_round = sum([1/i for i in new_moandbtts_tolay_prices])
            lay_over_round = sum([1/i for i in new_moandbtts_toback_prices])
                           
            # place bets in MO&BTTS market
            for runner in range(0,len(moandbttsrunners)):
                # lay bets
                if lay_bet_ids[runner] == 0:
                    sizeRemaining = 0
                else:
                    status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
                    sizeRemaining = status['currentOrders'][0]['sizeRemaining']
                if new_moandbtts_tolay_prices[runner] != old_moandbtts_tolay_prices[runner] or sizeRemaining == 0:
                    suggested_stake = round(min(max(trading_stake,pnl_positions[runner]/4),1000)/max(new_moandbtts_tolay_prices[runner],1.01),0)
                    suggested_stake = max(suggested_stake,2)
                    max_stake = max(round(((pnl_positions[runner]+max_market_liability)/max(new_moandbtts_tolay_prices[runner],1.01))/2,0),2)
                    stake = min(suggested_stake,max_stake)
                    if stake < 2 or pnl_positions[runner] < -max_runner_liability or new_moandbtts_tolay_prices[runner] < 1.01 :    
                        if sizeRemaining == 0:
                            lay_bet_ids[runner] = 0 
                            result = '' + moandbtts_selection_names[runner] + ' Lay - No longer Laying'
                        else:
                            order = lib_api_commands.cancelBet(str(marketId), str(lay_bet_ids[runner]), appKey, sessionToken)
                            lay_bet_ids[runner] = 0
                            result = '' + moandbtts_selection_names[runner] + ' Lay - No longer Laying'
                    elif lay_bet_ids[runner] == 0:
                        order = lib_api_commands.doWager(str(marketId), str(moandbttsrunners[runner]['selectionId']), "LAY", str(stake), str(new_moandbtts_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(moandbttsrunners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                        lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                        result = '' + moandbtts_selection_names[runner] + ' Lay - New Bet Placed'
                    else:
                        if sizeRemaining == 0:
                            order = lib_api_commands.doWager(str(marketId), str(moandbttsrunners[runner]['selectionId']), "LAY", str(stake), str(new_moandbtts_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(moandbttsrunners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                            lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                            result = '' + moandbtts_selection_names[runner] + ' Lay - New Bet Placed'
                        else:
                            order = lib_api_commands.replaceBet(str(marketId), str(lay_bet_ids[runner]), str(new_moandbtts_tolay_prices[runner]), strategy_name + str(marketId) + str(moandbttsrunners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                            lay_bet_ids[runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
                            result = '' + moandbtts_selection_names[runner] + ' Lay - Odds Updated'       
                else:
                    eggs = 'eggs'
                # back bets
                if back_bet_ids[runner] == 0:
                    sizeRemaining = 0
                else:
                    status = lib_api_commands.betStatus(back_bet_ids[runner], appKey, sessionToken)
                    sizeRemaining = status['currentOrders'][0]['sizeRemaining']
                if new_moandbtts_toback_prices[runner] != old_moandbtts_toback_prices[runner] or sizeRemaining == 0:
                    suggested_stake = round(min(max(trading_stake,pnl_positions[runner]/4),1000)/max(new_moandbtts_toback_prices[runner],1.01),0)
                    suggested_stake = max(suggested_stake,2)
                    max_stake = max(round(((pnl_positions[runner]+max_market_liability)/max(new_moandbtts_toback_prices[runner],1.01))/2,0),2)
                    stake = min(suggested_stake,max_stake)
                    if stake < 2 or (pnl_positions[runner] != min(pnl_positions) and min(pnl_positions) < -max_runner_liability) or new_moandbtts_toback_prices[runner] > 1000 :    #####
                        if sizeRemaining == 0:
                            back_bet_ids[runner] = 0
                            result = '' + moandbtts_selection_names[runner] + ' Back - No longer Backing'
                        else:
                            order = lib_api_commands.cancelBet(str(marketId), str(back_bet_ids[runner]), appKey, sessionToken)
                            back_bet_ids[runner] = 0
                            result = '' + moandbtts_selection_names[runner] + ' Back - No longer Backing'
                    elif back_bet_ids[runner] == 0:
                        order = lib_api_commands.doWager(str(marketId), str(moandbttsrunners[runner]['selectionId']), "BACK", str(stake), str(new_moandbtts_toback_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(moandbttsrunners[runner]['selectionId']) + "BACK", appKey, sessionToken)
                        back_bet_ids[runner] = order['instructionReports'][0]['betId']
                        result = '' + moandbtts_selection_names[runner] + ' Back - New Bet Placed'
                    else:
                        if sizeRemaining == 0:
                            order = lib_api_commands.doWager(str(marketId), str(moandbttsrunners[runner]['selectionId']), "BACK", str(stake), str(new_moandbtts_toback_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(moandbttsrunners[runner]['selectionId']) + "BACK", appKey, sessionToken)
                            back_bet_ids[runner] = order['instructionReports'][0]['betId']
                            result = '' + moandbtts_selection_names[runner] + ' Back - New Bet Placed'
                        else:
                            order = lib_api_commands.replaceBet(str(marketId), str(back_bet_ids[runner]), str(new_moandbtts_toback_prices[runner]), strategy_name + str(marketId) + str(moandbttsrunners[runner]['selectionId']) + "BACK", appKey, sessionToken)
                            back_bet_ids[runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
                            result = '' + moandbtts_selection_names[runner] + ' Back - Odds Updated'    
                else:
                    eggs = 'eggs'    
                   
        old_moandbtts_tolay_prices = new_moandbtts_tolay_prices
        #print('\nMO&BTTS Market '+marketId+' - Expected Value: £' +str(round(expeted_value, 2))+'')                  
        #print('MO&BTTS Market '+marketId+' - Wost Outcome: £' +str(min([round(n, 2) for n in pnl_positions]))+'')
        lib_dn_tasks.log_market_position(datetime.datetime.now(), marketId, 'MO & BTTS', round(expeted_value, 2), min([round(n, 2) for n in pnl_positions]), matched_volume)
        return round(expeted_value, 2), min([round(n, 2) for n in pnl_positions])


