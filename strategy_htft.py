import lib_api_commands
import lib_dn_tasks
import sqlite3
import datetime


def halftime_fulltime(sessionToken, appKey, \
                      matchoddsBook, htftBook,  \
                      matchoddsID, htftID, half_time_result, strategy_name, \
                      trading_stake, max_runner_liability, max_market_liability, margin_multiplier_1, margin_multiplier_2, \
                      old_htft_tolay_prices, lay_bet_ids, old_htft_toback_prices, back_bet_ids, \
                      selectionIds, selectionIds_liability, pnl_positions, ev_trend):
                
    # get market details
    matchoddsDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, matchoddsID)
    htftDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, htftID)
    #matchoddsBook = lib_api_commands.getSelections(appKey, sessionToken, matchoddsID)
    #htftBook = lib_api_commands.getSelections(appKey, sessionToken, htftID)
    marketId = htftBook[0]['marketId']

    # get runner details
    matchoddsrunners = matchoddsBook[0]['runners']
    htftrunners = htftBook[0]['runners']
##    matchodds_selection_names = []
##    htft_selection_names = []
##    for runner in range(0,len(matchoddsrunners)):
##        matchoddsname = matchoddsDeets['result'][0]['runners'][runner]['runnerName']
##        matchoddsname = matchoddsname.replace("The Draw","Draw")
##        matchodds_selection_names.append(matchoddsname)
##    for runner in range(0, len(htftrunners)):
##        htftname = htftDeets['result'][0]['runners'][runner]['runnerName']
##        if htftname[:htftname.find('/')] == half_time_result:
##            htftname = htftname[htftname.find('/'):]
##            htft_selection_names.append(htftname)
    # check P&L positions
    market_position = lib_api_commands.findPnL(appKey, sessionToken, htftID, str(0), str(0), str(1))
    for runner in range(0,len(htftrunners)):
        selectionIds[runner] = htftBook[0]['runners'][runner]['selectionId']
        selectionIds_liability[runner] = market_position[0]['profitAndLosses'][runner]['selectionId']
        pnl_positions[runner] = market_position[0]['profitAndLosses'][runner]['ifWin']
    liability_runner_index = [selectionIds_liability.index(i) for i in selectionIds]
    pnl_positions = [pnl_positions[i] for i in liability_runner_index]
    # limit HT/FT runners to possible outcomes
    if half_time_result == 'home':
        htftrunners = htftBook[0]['runners'][0:3]
        pnl_positions = pnl_positions[0:3]
    elif half_time_result == 'draw':
        htftrunners = htftBook[0]['runners'][3:6]
        pnl_positions = pnl_positions[3:6]
    else:
        htftrunners = htftBook[0]['runners'][6:9]
        pnl_positions = pnl_positions[6:9]
           
    # check market parameters are ok
    if len(matchoddsrunners) != 3:
        order = lib_api_commands.cancelOrders(str(htftID), appKey, sessionToken)
        print('Error Market ' + htftID + ': There are ' + str(len(matchoddsrunners)) + ' Match Odds runners - 3 expected')
        lay_bet_ids = lay_bet_ids * 0
    elif len(htftrunners) != 3:
        order = lib_api_commands.cancelOrders(str(htftID), appKey, sessionToken)
        print ('Error Market '+htftID+': There are ' +str(len(htftrunners))+ ' active HT/FT runners - 3 expected')
        lay_bet_ids = lay_bet_ids*0
    else:

        # find current Match Odds back and lay prices
        matchodds_back_prices = [0 for i in range(0,len(matchoddsrunners))]
        matchodds_lay_prices = [0 for i in range(0,len(matchoddsrunners))]
        for runner in range(0,len(matchoddsrunners)):
            if len(matchoddsrunners[runner]['ex']['availableToBack']) == 0:
                matchodds_back_prices[runner] = 'N/A'
            else:
                matchodds_back_prices[runner] = matchoddsrunners[runner]['ex']['availableToBack'][0]['price']
            if len(matchoddsrunners[runner]['ex']['availableToLay']) == 0:
                matchodds_lay_prices[runner] = 'N/A'
            else:
                matchodds_lay_prices[runner] = matchoddsrunners[runner]['ex']['availableToLay'][0]['price']

        # estimate HT/FT probabilities
        matchodds_lay_estimate = [10000 if (x=='N/A' or x==0) else x for x in matchodds_lay_prices] # Malone's rule
        matchodds_back_estimate = [1+(1/10000) if (x=='N/A' or x==0) else x for x in matchodds_back_prices]
        matchodds_probs = [2/i for i in [j + i for j, i in zip(matchodds_lay_estimate, matchodds_back_estimate)]]
        matchodds_probs = [x/sum(matchodds_probs) for x in matchodds_probs]
        htft_probs = [matchodds_probs[0], matchodds_probs[2], matchodds_probs[1]]
      
        # estimate expected value
        expeted_value = sum([j * i for j, i in zip(htft_probs, pnl_positions)])        
        ev_trend.append(expeted_value)

        # calculate matched volume
        matched_bets = lib_api_commands.currentOrders(htftID, 'ALL', appKey, sessionToken)
        matched_volume = 0
        for bet in range(0,len(matched_bets['currentOrders'])):
            matched_volume = matched_volume+matched_bets['currentOrders'][0]['sizeMatched']
            
        # find current HT/FT back prices (excluding our bets)
        htft_back_prices = [0 for i in range(0,len(htftrunners))]
        for runner in range(0,len(htftrunners)):
            # find our bet status
            if lay_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
            # compare to available bets 
            if len(htftrunners[runner]['ex']['availableToBack']) == 0:
                htft_back_prices[runner] = 'N/A'
            elif old_htft_tolay_prices[runner] == htftrunners[runner]['ex']['availableToBack'][0]['price'] and sizeRemaining > 0:
                if len(htftrunners[runner]['ex']['availableToBack']) > 1:
                    htft_back_prices[runner] = htftrunners[runner]['ex']['availableToBack'][1]['price']
                else:
                    htft_back_prices[runner] = 'N/A'
            else:
                htft_back_prices[runner] = htftrunners[runner]['ex']['availableToBack'][0]['price']

        # find current HT/FT lay prices (excluding our bets)
        htft_lay_prices = [0 for i in range(0,len(htftrunners))]
        for runner in range(0,len(htftrunners)):
            # find our bet status
            if back_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(back_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
            # compare to available bets 
            if len(htftrunners[runner]['ex']['availableToLay']) == 0:
                htft_lay_prices[runner] = 'N/A'
            elif old_htft_toback_prices[runner] == htftrunners[runner]['ex']['availableToLay'][0]['price'] and sizeRemaining > 0:
                if len(htftrunners[runner]['ex']['availableToLay']) > 1:
                    htft_lay_prices[runner] = htftrunners[runner]['ex']['availableToLay'][1]['price']
                else:
                    htft_lay_prices[runner] = 'N/A'
            else:
                htft_lay_prices[runner] = htftrunners[runner]['ex']['availableToLay'][0]['price']
                
        # calculate new HT/FT prices to lay
        raw_htft_tolay_prices = [matchodds_back_estimate[0], matchodds_back_estimate[2], matchodds_back_estimate[1]]
        raw_htft_tolay_prices_margin_1 = [1000 for i in range(0,len(htftrunners))]
        raw_htft_tolay_prices_margin_2 = [1000 for i in range(0,len(htftrunners))]
        for runner in range(0,len(htftrunners)):
            raw_htft_tolay_prices_margin_1[runner] = ((raw_htft_tolay_prices[runner]-1)*(1-margin_multiplier_1))+1
            raw_htft_tolay_prices_margin_2[runner] = ((raw_htft_tolay_prices[runner]-1)*(1-margin_multiplier_2))+1
        # calculate new HT/FT prices to back
        raw_htft_toback_prices = [matchodds_lay_estimate[0], matchodds_lay_estimate[2], matchodds_lay_estimate[1]]
        raw_htft_toback_prices_margin_1 = [1000 for i in range(0,len(htftrunners))]
        raw_htft_toback_prices_margin_2 = [1000 for i in range(0,len(htftrunners))]
        for runner in range(0,len(htftrunners)):
            raw_htft_toback_prices_margin_1[runner] = ((raw_htft_toback_prices[runner]-1)*(1+margin_multiplier_1))+1
            raw_htft_toback_prices_margin_2[runner] = ((raw_htft_toback_prices[runner]-1)*(1+margin_multiplier_2))+1
        # fix prices to odds ladder
        htft_back_butone = [0 for i in range(0,len(htftrunners))]
        new_htft_tolay_prices = [0 for i in range(0,len(htftrunners))]
        htft_lay_butone = [0 for i in range(0,len(htftrunners))]
        new_htft_toback_prices = [0 for i in range(0,len(htftrunners))]
        connection = sqlite3.connect('exchange.db')
        with connection:
            cur = connection.cursor()
            for runner in range(0,len(htftrunners)):
                # find next-but-one prices
                if htft_back_prices[runner] =='N/A':
                    htft_back_butone[runner] = 1
                else:
                    cur.execute("select next_price_up from odds_ladder where price = ?", [htft_back_prices[runner]])
                    htft_back_butone[runner] = cur.fetchall()[0][0]
                if htft_lay_prices[runner] =='N/A':
                    htft_lay_butone[runner] = 1001
                else:
                    cur.execute("select next_price_down from odds_ladder where price = ?", [htft_lay_prices[runner]])
                    htft_lay_butone[runner] = cur.fetchall()[0][0]
                # final tolay price
                if raw_htft_tolay_prices[runner] < 1.01:
                    new_htft_tolay_prices[runner] = 1
                elif htft_back_butone[runner] < raw_htft_tolay_prices_margin_1[runner]:
                    cur.execute("select max(price) from odds_ladder where price <= ?", [raw_htft_tolay_prices_margin_1[runner]])
                    new_htft_tolay_prices[runner] = cur.fetchall()[0][0]
                elif htft_back_butone[runner] > raw_htft_tolay_prices_margin_2[runner]:
                    cur.execute("select max(price) from odds_ladder where price <= ?", [raw_htft_tolay_prices_margin_2[runner]])
                    new_htft_tolay_prices[runner] = cur.fetchall()[0][0]
                else:
                    new_htft_tolay_prices[runner] = htft_back_butone[runner]
                # final toback price
                if raw_htft_toback_prices[runner] > 1000:
                    new_htft_toback_prices[runner] = 1001
                elif htft_lay_butone[runner] > raw_htft_toback_prices_margin_1[runner]:
                    cur.execute("select min(price) from odds_ladder where price >= ?", [raw_htft_toback_prices_margin_1[runner]])
                    new_htft_toback_prices[runner] = cur.fetchall()[0][0]
                elif htft_lay_butone[runner] < raw_htft_toback_prices_margin_2[runner]:
                    cur.execute("select min(price) from odds_ladder where price >= ?", [raw_htft_toback_prices_margin_2[runner]])
                    new_htft_toback_prices[runner] = cur.fetchall()[0][0]
                else:
                    new_htft_toback_prices[runner] = htft_lay_butone[runner]
        back_over_round = sum([1/i for i in new_htft_tolay_prices])
        lay_over_round = sum([1/i for i in new_htft_toback_prices])

        #print('matchodds_back_estimate:'+ str(matchodds_back_estimate))
        #print('matchodds_lay_estimate:'+ str(matchodds_lay_estimate))
        #print('new_htft_tolay_prices:'+ str(new_htft_tolay_prices))
        #print('new_htft_toback_prices:'+ str(new_htft_toback_prices))
        
        # place bets in HT/FT market
        for runner in range(0,len(htftrunners)):
            # lay bets
            if lay_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']
            if new_htft_tolay_prices[runner] != old_htft_tolay_prices[runner] or sizeRemaining == 0:
                suggested_stake = round(min(max(trading_stake,pnl_positions[runner]/4),1000)/max(new_htft_tolay_prices[runner],1.01),0)
                suggested_stake = max(suggested_stake,2)
                max_stake = max(round(((pnl_positions[runner]+max_market_liability)/max(new_htft_tolay_prices[runner],1.01))/2,0),2)
                stake = min(suggested_stake,max_stake)
                if stake < 2 or pnl_positions[runner] < -max_runner_liability or new_htft_tolay_prices[runner] < 1.01 :
                    if sizeRemaining == 0:
                        lay_bet_ids[runner] = 0
                        #result = '' + htft_selection_names[runner] + ' Lay - No longer Laying'
                    else:
                        order = lib_api_commands.cancelBet(str(marketId), str(lay_bet_ids[runner]), appKey, sessionToken)
                        lay_bet_ids[runner] = 0
                        #result = '' + htft_selection_names[runner] + ' Lay - No longer Laying'
                elif lay_bet_ids[runner] == 0:
                    order = lib_api_commands.doWager(str(marketId), str(htftrunners[runner]['selectionId']), "LAY", str(stake), str(new_htft_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(htftrunners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                    lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                    #result = '' + htft_selection_names[runner] + ' Lay - New Bet Placed'
                else:
                    if sizeRemaining == 0:
                        order = lib_api_commands.doWager(str(marketId), str(htftrunners[runner]['selectionId']), "LAY", str(stake), str(new_htft_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(htftrunners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                        lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                        #result = '' + htft_selection_names[runner] + ' Lay - New Bet Placed'
                    else:
                        order = lib_api_commands.replaceBet(str(marketId), str(lay_bet_ids[runner]), str(new_htft_tolay_prices[runner]), strategy_name + str(marketId) + str(htftrunners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                        lay_bet_ids[runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
                        #result = '' + htft_selection_names[runner] + ' Lay - Odds Updated'
            else:
                eggs = 'eggs'
            # back bets
            if back_bet_ids[runner] == 0:
                sizeRemaining = 0
            else:
                status = lib_api_commands.betStatus(back_bet_ids[runner], appKey, sessionToken)
                sizeRemaining = status['currentOrders'][0]['sizeRemaining']
            if new_htft_toback_prices[runner] != old_htft_toback_prices[runner] or sizeRemaining == 0:
                suggested_stake = round(min(max(trading_stake,pnl_positions[runner]/4),1000)/max(new_htft_toback_prices[runner],1.01),0)
                suggested_stake = max(suggested_stake,2)
                max_stake = max(round(((pnl_positions[runner]+max_market_liability)/max(new_htft_toback_prices[runner],1.01))/2,0),2)
                stake = min(suggested_stake,max_stake)
                if stake < 2 or (pnl_positions[runner] != min(pnl_positions) and min(pnl_positions) < -max_runner_liability) or new_htft_toback_prices[runner] > 1000:
                    if sizeRemaining == 0:
                        back_bet_ids[runner] = 0
                        #result = '' + htft_selection_names[runner] + ' Back - No longer Backing'
                    else:
                        order = lib_api_commands.cancelBet(str(marketId), str(back_bet_ids[runner]), appKey, sessionToken)
                        back_bet_ids[runner] = 0
                        #result = '' + htft_selection_names[runner] + ' Back - No longer Backing'
                elif back_bet_ids[runner] == 0:
                    order = lib_api_commands.doWager(str(marketId), str(htftrunners[runner]['selectionId']), "BACK", str(stake), str(new_htft_toback_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(htftrunners[runner]['selectionId']) + "BACK", appKey, sessionToken)
                    back_bet_ids[runner] = order['instructionReports'][0]['betId']
                    #result = '' + htft_selection_names[runner] + ' Back - New Bet Placed'
                else:
                    if sizeRemaining == 0:
                        order = lib_api_commands.doWager(str(marketId), str(htftrunners[runner]['selectionId']), "BACK", str(stake), str(new_htft_toback_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(htftrunners[runner]['selectionId']) + "BACK", appKey, sessionToken)
                        back_bet_ids[runner] = order['instructionReports'][0]['betId']
                        #result = '' + htft_selection_names[runner] + ' Back - New Bet Placed'
                    else:
                        order = lib_api_commands.replaceBet(str(marketId), str(back_bet_ids[runner]), str(new_htft_toback_prices[runner]), strategy_name + str(marketId) + str(htftrunners[runner]['selectionId']) + "BACK", appKey, sessionToken)
                        back_bet_ids[runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
                        #result = '' + htft_selection_names[runner] + ' Back - Odds Updated'
            else:
                eggs = 'eggs'
               
    old_htft_tolay_prices = new_htft_tolay_prices
    #print('\nHT/FT Market '+marketId+' - Expected Value: £' +str(round(expeted_value, 2))+'')
    #print('HT/FT Market '+marketId+' - Wost Outcome: £' +str(min([round(n, 2) for n in pnl_positions]))+'')
    lib_dn_tasks.log_market_position(datetime.datetime.now(), marketId, 'HT/FT', round(expeted_value, 2), min([round(n, 2) for n in pnl_positions]), matched_volume)
    return round(expeted_value, 2), min([round(n, 2) for n in pnl_positions])


