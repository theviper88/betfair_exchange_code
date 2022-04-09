import lib_api_commands
import lib_dn_tasks
import sqlite3
import datetime


def half_time(sessionToken, appKey, \
              htftBook, halftimeBook,  \
              htftID, halftimeID, strategy_name, \
              trading_stake, max_runner_liability, max_market_liability, margin_multiplier_1, margin_multiplier_2, \
              old_halftime_tolay_prices, lay_bet_ids, old_halftime_toback_prices, back_bet_ids, \
              selectionIds, selectionIds_liability, pnl_positions, ev_trend):
                
    # get market details
    htftDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, htftID)
    halftimeDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, halftimeID)
    #htftBook = lib_api_commands.getSelections(appKey, sessionToken, htftID)
    #halftimeBook = lib_api_commands.getSelections(appKey, sessionToken, halftimeID)
    marketId = halftimeBook[0]['marketId']

    # get runner details
    htftrunners = htftBook[0]['runners']
    htrunners = halftimeBook[0]['runners']        
    htft_selection_names = []
    halftime_selection_names = []
    for runner in range(0,len(htftrunners)):
        htftname = htftDeets['result'][0]['runners'][runner]['runnerName']
        htftname = htftname[:htftname.find('/')]
        htft_selection_names.append(htftname)
    for runner in range(0,len(htrunners)):
        halftimename = halftimeDeets['result'][0]['runners'][runner]['runnerName']
        halftimename = halftimename.replace("The Draw","Draw")
        halftime_selection_names.append(halftimename)   
    # check P&L positions
    market_position = lib_api_commands.findPnL(appKey, sessionToken, halftimeID, str(0), str(0), str(1))
    for runner in range(0,len(htrunners)):
        selectionIds[runner] = halftimeBook[0]['runners'][runner]['selectionId']
        selectionIds_liability[runner] = market_position[0]['profitAndLosses'][runner]['selectionId']
        pnl_positions[runner] = market_position[0]['profitAndLosses'][runner]['ifWin']
    liability_runner_index = [selectionIds_liability.index(i) for i in selectionIds]
    pnl_positions = [pnl_positions[i] for i in liability_runner_index]                 
           
    # check market parameters are ok
    if len(htftrunners) != 9:
        order = lib_api_commands.cancelOrders(str(halftimeIDs), appKey, sessionToken)
        print ('Error Market '+halftimeID+': There are ' +str(len(htftrunners))+ ' HT/FT runners - 9 expected')
        lay_bet_ids = lay_bet_ids*0
    elif len(htrunners) != 3:
        order = lib_api_commands.cancelOrders(str(halftimeIDs), appKey, sessionToken)
        print ('Error Market '+halftimeID+': There are ' +str(len(htrunners))+ ' Half Time runners - 3 expected')
        lay_bet_ids = lay_bet_ids*0
    else:

        # find current Half Time/Full Time back and lay prices
        htft_back_prices = [0 for i in range(0,len(htftrunners))]
        htft_lay_prices = [0 for i in range(0,len(htftrunners))]
        for runner in range(0,len(htftrunners)):
            if len(htftrunners[runner]['ex']['availableToBack']) == 0:
                htft_back_prices[runner] = 'N/A'
            else:
                htft_back_prices[runner] = htftrunners[runner]['ex']['availableToBack'][0]['price']
            if len(htftrunners[runner]['ex']['availableToLay']) == 0:
                htft_lay_prices[runner] = 'N/A'
            else:
                htft_lay_prices[runner] = htftrunners[runner]['ex']['availableToLay'][0]['price'] 

        # estimate Half Time probabilities
        htft_lay_estimate = [10000 if (x=='N/A' or x==0) else x for x in htft_lay_prices] # Malone's rule
        htft_back_estimate = [1+(1/10000) if (x=='N/A' or x==0) else x for x in htft_back_prices]
        htft_probs = [2/i for i in [j + i for j, i in zip(htft_lay_estimate, htft_back_estimate)]]
        htft_probs = [x/sum(htft_probs) for x in htft_probs]
        halftime_probs = []
        for runner in range(0,len(htrunners)):
            indices = [i for i, x in enumerate(htft_selection_names) if x == halftime_selection_names[runner]]
            halftime_probs.append(sum([htft_probs[j] for j in indices]))
        halftime_probs = [x/sum(halftime_probs) for x in halftime_probs]
      
        # estimate expected value
        expeted_value = sum([j * i for j, i in zip(halftime_probs, pnl_positions)]) 
        ev_trend.append(expeted_value)

        # calculate matched volume
        matched_bets = lib_api_commands.currentOrders(halftimeID, 'ALL', appKey, sessionToken)
        matched_volume = 0
        for bet in range(0,len(matched_bets['currentOrders'])):
            matched_volume = matched_volume+matched_bets['currentOrders'][0]['sizeMatched']
            
        # find current Half Time back prices (excluding our bets)
        halftime_back_prices = [0 for i in range(0,len(htrunners))]
        for runner in range(0,len(htrunners)):
            # find our bet status
            if lay_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
            # compare to available bets 
            if len(htrunners[runner]['ex']['availableToBack']) == 0:
                halftime_back_prices[runner] = 'N/A'
            elif old_halftime_tolay_prices[runner] == htrunners[runner]['ex']['availableToBack'][0]['price'] and sizeRemaining > 0:
                if len(htrunners[runner]['ex']['availableToBack']) > 1:
                    halftime_back_prices[runner] = htrunners[runner]['ex']['availableToBack'][1]['price']
                else:
                    halftime_back_prices[runner] = 'N/A'                     
            else:
                halftime_back_prices[runner] = htrunners[runner]['ex']['availableToBack'][0]['price']

        # find current half Time lay prices (excluding our bets)
        halftime_lay_prices = [0 for i in range(0,len(htrunners))]
        for runner in range(0,len(htrunners)):
            # find our bet status
            if back_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(back_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
            # compare to available bets 
            if len(htrunners[runner]['ex']['availableToLay']) == 0:
                halftime_lay_prices[runner] = 'N/A'
            elif old_halftime_toback_prices[runner] == htrunners[runner]['ex']['availableToLay'][0]['price'] and sizeRemaining > 0:
                if len(htrunners[runner]['ex']['availableToLay']) > 1:
                    halftime_lay_prices[runner] = htrunners[runner]['ex']['availableToLay'][1]['price']
                else:
                    halftime_lay_prices[runner] = 'N/A'                     
            else:
                halftime_lay_prices[runner] = htrunners[runner]['ex']['availableToLay'][0]['price']
                
        # calculate new Half Time prices to lay
        raw_halftime_tolay_prices = [1000 for i in range(0,len(htrunners))]
        raw_halftime_tolay_prices_margin_1 = [1000 for i in range(0,len(htrunners))]
        raw_halftime_tolay_prices_margin_2 = [1000 for i in range(0,len(htrunners))]
        htft_back_probs = [1/i for i in htft_back_estimate]
        for runner in range(0,len(htrunners)):
            indices = [i for i, x in enumerate(htft_selection_names) if x == halftime_selection_names[runner]]
            raw_halftime_tolay_prices[runner] = 1/sum([htft_back_probs[j] for j in indices])
            raw_halftime_tolay_prices_margin_1[runner] = ((raw_halftime_tolay_prices[runner]-1)*(1-margin_multiplier_1))+1
            raw_halftime_tolay_prices_margin_2[runner] = ((raw_halftime_tolay_prices[runner]-1)*(1-margin_multiplier_2))+1
        # calculate new Half Time prices to back
        raw_halftime_toback_prices = [1000 for i in range(0,len(htrunners))]
        raw_halftime_toback_prices_margin_1 = [1000 for i in range(0,len(htrunners))]
        raw_halftime_toback_prices_margin_2 = [1000 for i in range(0,len(htrunners))]
        htft_lay_probs = [1/i for i in htft_lay_estimate]
        for runner in range(0,len(htrunners)):
            indices = [i for i, x in enumerate(htft_selection_names) if x == halftime_selection_names[runner]]
            raw_halftime_toback_prices[runner] = 1/sum([htft_lay_probs[j] for j in indices]) 
            raw_halftime_toback_prices_margin_1[runner] = ((raw_halftime_toback_prices[runner]-1)*(1+margin_multiplier_1))+1
            raw_halftime_toback_prices_margin_2[runner] = ((raw_halftime_toback_prices[runner]-1)*(1+margin_multiplier_2))+1    
        # fix prices to odds ladder
        halftime_back_butone = [0 for i in range(0,len(htrunners))]
        new_halftime_tolay_prices = [0 for i in range(0,len(htrunners))]
        halftime_lay_butone = [0 for i in range(0,len(htrunners))]
        new_halftime_toback_prices = [0 for i in range(0,len(htrunners))]
        connection = sqlite3.connect('exchange.db')
        with connection:
            cur = connection.cursor()
            for runner in range(0,len(htrunners)):
                # find next-but-one prices
                if halftime_back_prices[runner] =='N/A':
                    halftime_back_butone[runner] = 1
                else:
                    cur.execute("select next_price_up from odds_ladder where price = ?", [halftime_back_prices[runner]])
                    halftime_back_butone[runner] = cur.fetchall()[0][0]
                if halftime_lay_prices[runner] =='N/A':
                    halftime_lay_butone[runner] = 1001
                else:
                    cur.execute("select next_price_down from odds_ladder where price = ?", [halftime_lay_prices[runner]])
                    halftime_lay_butone[runner] = cur.fetchall()[0][0]    
                # final tolay price
                if raw_halftime_tolay_prices[runner] < 1.01:
                    new_halftime_tolay_prices[runner] = 1
                elif halftime_back_butone[runner] < raw_halftime_tolay_prices_margin_1[runner]:
                    cur.execute("select max(price) from odds_ladder where price <= ?", [raw_halftime_tolay_prices_margin_1[runner]])  
                    new_halftime_tolay_prices[runner] = cur.fetchall()[0][0]
                elif halftime_back_butone[runner] > raw_halftime_tolay_prices_margin_2[runner]:
                    cur.execute("select max(price) from odds_ladder where price <= ?", [raw_halftime_tolay_prices_margin_2[runner]])  
                    new_halftime_tolay_prices[runner] = cur.fetchall()[0][0]
                else:
                    new_halftime_tolay_prices[runner] = halftime_back_butone[runner]
                # final toback price
                if raw_halftime_toback_prices[runner] > 1000:
                    new_halftime_toback_prices[runner] = 1001
                elif halftime_lay_butone[runner] > raw_halftime_toback_prices_margin_1[runner]:
                    cur.execute("select min(price) from odds_ladder where price >= ?", [raw_halftime_toback_prices_margin_1[runner]])  
                    new_halftime_toback_prices[runner] = cur.fetchall()[0][0]
                elif halftime_lay_butone[runner] < raw_halftime_toback_prices_margin_2[runner]:
                    cur.execute("select min(price) from odds_ladder where price >= ?", [raw_halftime_toback_prices_margin_2[runner]])
                    new_halftime_toback_prices[runner] = cur.fetchall()[0][0]
                else:
                    new_halftime_toback_prices[runner] = halftime_lay_butone[runner]    
        back_over_round = sum([1/i for i in new_halftime_tolay_prices])
        lay_over_round = sum([1/i for i in new_halftime_toback_prices])
                       
        # place bets in Half Time market
        for runner in range(0,len(htrunners)):
            # lay bets
            if lay_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']
            if new_halftime_tolay_prices[runner] != old_halftime_tolay_prices[runner] or sizeRemaining == 0:
                suggested_stake = round(min(max(trading_stake,pnl_positions[runner]/4),1000)/max(new_halftime_tolay_prices[runner],1.01),0)
                suggested_stake = max(suggested_stake,2)
                max_stake = max(round(((pnl_positions[runner]+max_market_liability)/max(new_halftime_tolay_prices[runner],1.01))/2,0),2)
                stake = min(suggested_stake,max_stake)
                if stake < 2 or pnl_positions[runner] < -max_runner_liability or new_halftime_tolay_prices[runner] < 1.01 :    
                    if sizeRemaining == 0:
                        lay_bet_ids[runner] = 0
                        result = '' + halftime_selection_names[runner] + ' Lay - No longer Laying'
                    else:
                        order = lib_api_commands.cancelBet(str(marketId), str(lay_bet_ids[runner]), appKey, sessionToken)
                        lay_bet_ids[runner] = 0
                        result = '' + halftime_selection_names[runner] + ' Lay - No longer Laying'
                elif lay_bet_ids[runner] == 0:
                    order = lib_api_commands.doWager(str(marketId), str(htrunners[runner]['selectionId']), "LAY", str(stake), str(new_halftime_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(htrunners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                    lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                    result = '' + halftime_selection_names[runner] + ' Lay - New Bet Placed'
                else:
                    if sizeRemaining == 0:
                        order = lib_api_commands.doWager(str(marketId), str(htrunners[runner]['selectionId']), "LAY", str(stake), str(new_halftime_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(htrunners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                        lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                        result = '' + halftime_selection_names[runner] + ' Lay - New Bet Placed'
                    else:
                        order = lib_api_commands.replaceBet(str(marketId), str(lay_bet_ids[runner]), str(new_halftime_tolay_prices[runner]), strategy_name + str(marketId) + str(htrunners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                        lay_bet_ids[runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
                        result = '' + halftime_selection_names[runner] + ' Lay - Odds Updated'  
            else:
                eggs = 'eggs'
            # back bets
            if back_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(back_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']
            if new_halftime_toback_prices[runner] != old_halftime_toback_prices[runner] or sizeRemaining == 0:
                suggested_stake = round(min(max(trading_stake,pnl_positions[runner]/4),1000)/max(new_halftime_toback_prices[runner],1.01),0)
                suggested_stake = max(suggested_stake,2)
                max_stake = max(round(((pnl_positions[runner]+max_market_liability)/max(new_halftime_toback_prices[runner],1.01))/2,0),2)
                stake = min(suggested_stake,max_stake)
                if stake < 2 or (pnl_positions[runner] != min(pnl_positions) and min(pnl_positions) < -max_runner_liability) or new_halftime_toback_prices[runner] > 1000 :    #####
                    if sizeRemaining == 0:
                        back_bet_ids[runner] = 0
                        result = '' + halftime_selection_names[runner] + ' Back - No longer Backing'
                    else:
                        order = lib_api_commands.cancelBet(str(marketId), str(back_bet_ids[runner]), appKey, sessionToken)
                        back_bet_ids[runner] = 0
                        result = '' + halftime_selection_names[runner] + ' Back - No longer Backing'
                elif back_bet_ids[runner] == 0:
                    order = lib_api_commands.doWager(str(marketId), str(htrunners[runner]['selectionId']), "BACK", str(stake), str(new_halftime_toback_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(htrunners[runner]['selectionId']) + "BACK", appKey, sessionToken)
                    back_bet_ids[runner] = order['instructionReports'][0]['betId']
                    result = '' + halftime_selection_names[runner] + ' Back - New Bet Placed'
                else:
                    if sizeRemaining == 0:
                        order = lib_api_commands.doWager(str(marketId), str(htrunners[runner]['selectionId']), "BACK", str(stake), str(new_halftime_toback_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(htrunners[runner]['selectionId']) + "BACK", appKey, sessionToken)
                        back_bet_ids[runner] = order['instructionReports'][0]['betId']
                        result = '' + halftime_selection_names[runner] + ' Back - New Bet Placed'
                    else:
                        order = lib_api_commands.replaceBet(str(marketId), str(back_bet_ids[runner]), str(new_halftime_toback_prices[runner]), strategy_name + str(marketId) + str(htrunners[runner]['selectionId']) + "BACK", appKey, sessionToken)
                        back_bet_ids[runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
                        result = '' + halftime_selection_names[runner] + ' Back - Odds Updated'       
            else:
                eggs = 'eggs'
               
    old_halftime_tolay_prices = new_halftime_tolay_prices
    #print('\nHalf Time Market '+marketId+' - Expected Value: £' +str(round(expeted_value, 2))+'')                  
    #print('Half Time Market '+marketId+' - Wost Outcome: £' +str(min([round(n, 2) for n in pnl_positions]))+'')
    lib_dn_tasks.log_market_position(datetime.datetime.now(), marketId, 'Half Time', round(expeted_value, 2), min([round(n, 2) for n in pnl_positions]), matched_volume)
    return round(expeted_value, 2), min([round(n, 2) for n in pnl_positions])


