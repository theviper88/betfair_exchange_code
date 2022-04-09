import lib_api_commands
import lib_dn_tasks
import sqlite3
import datetime


def each_way(sessionToken, appKey, \
             winmarketBook, placemarketBook, eachwaymarketBook, \
             winmarketID, placemarketID, eachwaymarketID, eachwayfraction, eachwayplaces, strategy_name,\
             trading_stake, max_runner_liability, max_market_liability, margin_multiplier_1, margin_multiplier_2, \
             old_eachway_tolay_prices, old_eachway_toback_prices, back_bet_ids, lay_bet_ids, selectionIds, selectionIds_liability, win_position, place_position, lose_position, worst_place_positions, worst_cases, ev_trend):

    # check liability  
    market_position = lib_api_commands.findPnL(appKey, sessionToken, eachwaymarketID, str(0), str(0), str(1))
            
    # get market details
    winmarketDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, winmarketID)
    placemarketDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, placemarketID)
    eachwaymarketDeets = lib_api_commands.getMarketDeets(appKey, sessionToken, eachwaymarketID)
    #winmarketBook = lib_api_commands.getSelections(appKey, sessionToken, winmarketID)
    #placemarketBook = lib_api_commands.getSelections(appKey, sessionToken, placemarketID)
    #eachwaymarketBook = lib_api_commands.getSelections(appKey, sessionToken, eachwaymarketID)
        
    # find current win market details
    for market in winmarketBook:
       runners = market['runners']
       # find removed runners
       removed_runners = 0
       for runner in runners:
           if str(runner['status']) == 'REMOVED' or str(runner['status']) == 'LOSER':
               removed_runners = removed_runners+1                           
       # get runner names
       win_selection_names = []
       eachway_selection_names = []
       for runner in range(0,len(runners)-removed_runners):
           # correct for naming inconsistencies - MANUAL
           if winmarketDeets['result'][0]['runners'][runner]['runnerName'] == '<name 1>':
               win_selection_names.append('<name 2>')    
           else:
               win_selection_names.append(winmarketDeets['result'][0]['runners'][runner]['runnerName'])
       for runner in range(0,len(runners)-removed_runners):
               eachway_selection_names.append(eachwaymarketDeets['result'][0]['runners'][runner]['runnerName']) 


    # find current place market details
    for market in placemarketBook:
       runners = market['runners']
       # find removed runners
       removed_runners = 0
       place_selection_ids = []
       for runner in runners:
           if str(runner['status']) == 'REMOVED' or str(runner['status']) == 'LOSER':
               removed_runners = removed_runners+1             
           else:
               place_selection_ids.append(runner['selectionId'])
           place_back_prices = [0 for i in range(0,len(runners)-removed_runners)]
           place_lay_prices = [0 for i in range(0,len(runners)-removed_runners)]
           # get runner back and lay prices, also names
           place_selection_names = []
           for runner in range(0,len(runners)-removed_runners):
               # correct for naming inconsistencies - MANUAL
               if placemarketDeets['result'][0]['runners'][runner]['runnerName'] == '<name 1>':
                   place_selection_names.append('<name 2>')    
               else:
                   place_selection_names.append(placemarketDeets['result'][0]['runners'][runner]['runnerName'])                       


    # find current each-way market details
    for market in eachwaymarketBook:
       runners = market['runners']
       marketId = market['marketId']
       # find each-way fraction
       ##if len(runners) >= 8:
       ##    eachwayfraction = 1/4
       ##else:
       ##    eachwayfraction = 1/4
       # find removed runners
       removed_runners = 0
       eachway_selection_ids = []
       for runner in runners:
           if str(runner['status']) == 'REMOVED' or str(runner['status']) == 'LOSER':
               removed_runners = removed_runners+1
           else:
               eachway_selection_ids.append(runner['selectionId'])                     
       # check liabilities
       for runner in range(0,len(runners)-removed_runners):
           selectionIds[runner] = eachwaymarketBook[0]['runners'][runner]['selectionId']
           selectionIds_liability[runner] = market_position[0]['profitAndLosses'][runner]['selectionId']
           win_position[runner] = market_position[0]['profitAndLosses'][runner]['ifWin']
           place_position[runner] = market_position[0]['profitAndLosses'][runner]['ifPlace']
           lose_position[runner] = market_position[0]['profitAndLosses'][runner]['ifLose']
       liability_runner_index = [selectionIds_liability.index(i) for i in selectionIds]
       win_position = [win_position[i] for i in liability_runner_index]
       place_position = [place_position[i] for i in liability_runner_index]
       lose_position = [lose_position[i] for i in liability_runner_index]
       # find worst case senarios
       for runner in range(0,len(runners)-removed_runners):        
           worst_places = 0
           other_place_positions = [i for j, i in enumerate(place_position) if j not in [runner]]
           other_lose_positions = [i for j, i in enumerate(lose_position) if j not in [runner]]
           other_place_lose_positions = [i-j for i,j in zip(other_place_positions,other_lose_positions)]
           for place in range(0,eachwayplaces-1):
               worst_place_lose = sorted(other_place_lose_positions)[place]
               worst_place_index = other_place_lose_positions.index(worst_place_lose)
               worst_place = other_place_positions[worst_place_index]
               worst_place_positions[place+1] = place_position.index(worst_place)
               worst_places = worst_places + worst_place
           worst_place_positions[0] = runner
           worst_lose_positions = [i for j, i in enumerate(lose_position) if j not in worst_place_positions]  
           worst_cases[runner] = win_position[runner] + worst_places + sum(worst_lose_positions)

       # re-order win and place market books based on names
       eachway_selection_names = []
       for runner in range(0,len(runners)-removed_runners):
           eachway_selection_names.append(eachwaymarketDeets['result'][0]['runners'][runner]['runnerName'])
       win_selection_names = [w.replace('\xa0', '') for w in win_selection_names]
       place_selection_names = [w.replace('\xa0', '') for w in place_selection_names]
       eachway_selection_names = [w.replace('\xa0', '') for w in eachway_selection_names]
       win_selection_names = [w.replace(' ', '') for w in win_selection_names]
       place_selection_names = [w.replace(' ', '') for w in win_selection_names]
       eachway_selection_names = [w.replace(' ', '') for w in win_selection_names]
       win_name_index = [win_selection_names.index(i) for i in eachway_selection_names]
       place_name_index = [place_selection_names.index(i) for i in eachway_selection_names]
       placerunners = []
       winrunners = []
       for runner in range(0,len(runners)-removed_runners):
           placerunners.append(placemarketBook[0]['runners'][place_name_index[runner]])
           winrunners.append(winmarketBook[0]['runners'][win_name_index[runner]])

       # find current runner win and place back and lay prices
       win_back_prices = [0 for i in range(0,len(runners)-removed_runners)]
       win_lay_prices = [0 for i in range(0,len(runners)-removed_runners)]
       place_back_prices = [0 for i in range(0,len(runners)-removed_runners)]
       place_lay_prices = [0 for i in range(0,len(runners)-removed_runners)]
       for runner in range(0,len(runners)-removed_runners):
           if len(winrunners[runner]['ex']['availableToBack']) == 0:
               win_back_prices[runner] = 'N/A'
           else:
               win_back_prices[runner] = winrunners[runner]['ex']['availableToBack'][0]['price']
           if len(winrunners[runner]['ex']['availableToLay']) == 0:
               win_lay_prices[runner] = 'N/A'
           else:
               win_lay_prices[runner] = winrunners[runner]['ex']['availableToLay'][0]['price']               
           if len(placerunners[runner]['ex']['availableToBack']) == 0:
               place_back_prices[runner] = 'N/A'
           else:
               place_back_prices[runner] = placerunners[runner]['ex']['availableToBack'][0]['price']
           if len(placerunners[runner]['ex']['availableToLay']) == 0:
               place_lay_prices[runner] = 'N/A'
           else:
               place_lay_prices[runner] = placerunners[runner]['ex']['availableToLay'][0]['price']    

       # estimate expected value
       win_lay_estimate = [10000 if (x=='N/A' or x==0) else x for x in win_lay_prices] # Malone's rule
       win_back_estimate = [1+(1/10000) if (x=='N/A' or x==0) else x for x in win_back_prices]
       #place_lay_estimate = [e/(3+(0.03*e)) if (x=='N/A' or x==0) else x for x, e in zip(place_lay_prices,win_lay_estimate)]
       #place_back_estimate = [e/(3+(0.03*e)) if (x=='N/A' or x==0) else x for x, e in zip(place_back_prices,win_back_estimate)]
       place_lay_estimate = [10000 if (x=='N/A' or x==0) else x for x in place_lay_prices]
       place_back_estimate = [1+(1/10000) if (x=='N/A' or x==0) else x for x in place_back_prices]
       win_probabilities =  [2/i for i in [j + i for j, i in zip(win_lay_estimate, win_back_estimate)]]
       #win_probabilities = [i/sum(win_probabilities) for i in win_probabilities] # normalise
       place_probabilities =  [j for j in [2/i for i in [j + i for j, i in zip(place_lay_estimate, place_back_estimate)]]]
       #place_probabilities = [eachwayplaces*i/sum(place_probabilities) for i in place_probabilities] # normalise
       place_only_probabilities =  [j - i for j, i in zip(place_probabilities,win_probabilities)]
       lose_probabilities = [1 - m - n for m, n in zip(win_probabilities,place_only_probabilities)]
       win_ev = sum([j * i for j, i in zip(win_probabilities, win_position)])
       place_only_ev = sum([j * i for j, i in zip(place_only_probabilities, place_position)])
       lose_ev = sum([j * i for j, i in zip(lose_probabilities, lose_position)])
       test_win_ev = [j * i for j, i in zip(win_probabilities, win_position)]
       test_place_only_ev = [j * i for j, i in zip(place_only_probabilities, place_position)]
       test_lose_ev = [j * i for j, i in zip(lose_probabilities, lose_position)]
       test_expeted_value = [i+j+k for i,j,k in zip(test_win_ev, test_place_only_ev, test_lose_ev)]
       #print(eachway_selection_names)
       #print(test_expeted_value)
       expeted_value = win_ev + place_only_ev + lose_ev
       ev_trend.append(expeted_value)
       if str(winmarketBook[0]['inplay']) != 'False':
               order = lib_api_commands.cancelOrders(str(eachwaymarketID), appKey, sessionToken)
               print ('Market is In-Play - Bets Cancelled')
               back_bet_ids = back_bet_ids*0
               lay_bet_ids = lay_bet_ids*0
       # calculate matched volume
       matched_bets = lib_api_commands.currentOrders(eachwaymarketID, 'ALL', appKey, sessionToken)
       matched_volume = 0
       for bet in range(0,len(matched_bets['currentOrders'])):
           matched_volume = matched_volume+matched_bets['currentOrders'][0]['sizeMatched']
       # get runner each lay back and lay price (excluding our bets)
       eachway_back_prices = [0 for i in range(0,len(runners)-removed_runners)]
       eachway_lay_prices = [0 for i in range(0,len(runners)-removed_runners)]
       for runner in range(0,len(runners)-removed_runners):
           # find our bet status
           if lay_bet_ids[runner] == 0:
               lay_sizeRemaining = 0
           else:
               status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
               lay_sizeRemaining = status['currentOrders'][0]['sizeRemaining']
           if back_bet_ids[runner] == 0:
               back_sizeRemaining = 0
           else:
               status = lib_api_commands.betStatus(back_bet_ids[runner], appKey, sessionToken)
               back_sizeRemaining = status['currentOrders'][0]['sizeRemaining']     
           # compare to available bets
           #print(runners[runner]['ex']['availableToBack'][0]) #lay_sizeRemaining == runners[runner]['ex']['availableToBack'][0]['stake']
           if len(runners[runner]['ex']['availableToBack']) == 0:
               eachway_back_prices[runner] = 'N/A'
           elif old_eachway_tolay_prices[runner] == runners[runner]['ex']['availableToBack'][0]['price'] and lay_sizeRemaining > 0:
               if len(runners[runner]['ex']['availableToBack']) > 1:
                   eachway_back_prices[runner] = runners[runner]['ex']['availableToBack'][1]['price']
               else:
                   eachway_back_prices[runner] = 'N/A'                      
           else:
               eachway_back_prices[runner] = runners[runner]['ex']['availableToBack'][0]['price']
           if len(runners[runner]['ex']['availableToLay']) == 0:
               eachway_lay_prices[runner] = 'N/A'
           elif old_eachway_toback_prices[runner] == runners[runner]['ex']['availableToLay'][0]['price'] and back_sizeRemaining > 0:
               if len(runners[runner]['ex']['availableToLay']) > 1:
                   eachway_lay_prices[runner] = runners[runner]['ex']['availableToLay'][1]['price']
               else:
                   eachway_lay_prices[runner] = 'N/A'
           else:
               eachway_lay_prices[runner] = runners[runner]['ex']['availableToLay'][0]['price']
       
    # calculate new each-way prices to back and lay
       raw_eachway_toback_prices = [0 for i in range(0,len(runners)-removed_runners)]
       raw_eachway_tolay_prices = [1000 for i in range(0,len(runners)-removed_runners)]
       raw_eachway_toback_prices_margin_1 = [0 for i in range(0,len(runners)-removed_runners)]
       raw_eachway_tolay_prices_margin_1 = [1000 for i in range(0,len(runners)-removed_runners)]
       raw_eachway_toback_prices_margin_2 = [0 for i in range(0,len(runners)-removed_runners)]
       raw_eachway_tolay_prices_margin_2 = [1000 for i in range(0,len(runners)-removed_runners)]
       for runner in range(0,len(runners)-removed_runners):
           # raw margin 1 price to back
           if (win_lay_prices[runner] == 'N/A') or (place_lay_prices[runner] == 'N/A'):
               raw_eachway_toback_prices[runner] = 'N/A'
               raw_eachway_toback_prices_margin_1[runner] = 'N/A'
           else:
               win_lay_price_prob = 1/win_lay_prices[runner]
               place_lay_price_prob = 1/place_lay_prices[runner]
               raw_eachway_toback_prices[runner] = (place_lay_price_prob/(win_lay_price_prob+(place_lay_price_prob/(1/eachwayfraction)))) * ((2/place_lay_price_prob)-1+eachwayfraction)
               raw_eachway_toback_prices_margin_1[runner] = ((raw_eachway_toback_prices[runner]-1)*(1+(margin_multiplier_1/2)))+1
           # raw margin 1 price to lay
           if (win_back_prices[runner] == 'N/A') or (place_back_prices[runner] == 'N/A'):
               raw_eachway_tolay_prices[runner] = 'N/A'
               raw_eachway_tolay_prices_margin_1[runner] = 'N/A'
           else:
               win_back_price_prob = 1/win_back_prices[runner]
               place_back_price_prob = 1/place_back_prices[runner]                                                                                                        
               raw_eachway_tolay_prices[runner] = (place_back_price_prob/(win_back_price_prob+(place_back_price_prob/(1/eachwayfraction)))) * ((2/place_back_price_prob)-1+eachwayfraction)
               raw_eachway_tolay_prices_margin_1[runner] = ((raw_eachway_tolay_prices[runner]-1)*(1-margin_multiplier_1))+1
           # raw margin 2 price to back
           if (win_lay_prices[runner] == 'N/A') or (place_lay_prices[runner] == 'N/A'):
               raw_eachway_toback_prices[runner] = 'N/A'
               raw_eachway_toback_prices_margin_2[runner] = 'N/A'
           else:
               win_lay_price_prob = 1/win_lay_prices[runner]
               place_lay_price_prob = 1/place_lay_prices[runner]
               raw_eachway_toback_prices[runner] = (place_lay_price_prob/(win_lay_price_prob+(place_lay_price_prob/(1/eachwayfraction)))) * ((2/place_lay_price_prob)-1+eachwayfraction)
               raw_eachway_toback_prices_margin_2[runner] = ((raw_eachway_toback_prices[runner]-1)*(1+margin_multiplier_2))+1
           # raw margin 2 price to lay
           if (win_back_prices[runner] == 'N/A') or (place_back_prices[runner] == 'N/A'):
               raw_eachway_tolay_prices[runner] = 'N/A'
               raw_eachway_tolay_prices_margin_2[runner] = 'N/A'
           else:
               win_back_price_prob = 1/win_back_prices[runner]
               place_back_price_prob = 1/place_back_prices[runner]                                                                                                        
               raw_eachway_tolay_prices[runner] = (place_back_price_prob/(win_back_price_prob+(place_back_price_prob/(1/eachwayfraction)))) * ((2/place_back_price_prob)-1+eachwayfraction)
               raw_eachway_tolay_prices_margin_2[runner] = ((raw_eachway_tolay_prices[runner]-1)*(1-margin_multiplier_2))+1
       # fix prices to odds ladder
       eachway_back_butone = [0 for i in range(0,len(runners)-removed_runners)]
       eachway_lay_butone = [0 for i in range(0,len(runners)-removed_runners)]
       new_eachway_toback_prices = [0 for i in range(0,len(runners)-removed_runners)]
       new_eachway_tolay_prices = [0 for i in range(0,len(runners)-removed_runners)]
       connection = sqlite3.connect('exchange.db')
       with connection:
           cur = connection.cursor()
           for runner in range(0,len(runners)-removed_runners):
               if eachway_back_prices[runner] == 'N/A':
                   eachway_back_butone[runner] = 1
               else:
                   cur.execute("select next_price_up from odds_ladder where price = ?", [eachway_back_prices[runner]])
                   eachway_back_butone[runner] = cur.fetchall()[0][0]
            
               if eachway_lay_prices[runner] == 'N/A':
                   eachway_lay_butone[runner] = 1001
               else:
                   cur.execute("select next_price_down from odds_ladder where price = ?", [eachway_lay_prices[runner]])
                   eachway_lay_butone[runner] = cur.fetchall()[0][0]
               # final tolay price
               if raw_eachway_tolay_prices[runner] == 'N/A':
                   new_eachway_tolay_prices[runner] = 1
               elif raw_eachway_tolay_prices[runner] < 1.01:
                   new_eachway_tolay_prices[runner] = 1
               elif eachway_back_butone[runner] < raw_eachway_tolay_prices_margin_1[runner]:
                   cur.execute("select max(price) from odds_ladder where price <= ?", [raw_eachway_tolay_prices_margin_1[runner]])  
                   new_eachway_tolay_prices[runner] = cur.fetchall()[0][0]
               elif eachway_back_butone[runner] > raw_eachway_tolay_prices_margin_2[runner]:
                   cur.execute("select max(price) from odds_ladder where price <= ?", [raw_eachway_tolay_prices_margin_2[runner]])  
                   new_eachway_tolay_prices[runner] = cur.fetchall()[0][0]
               else:
                   new_eachway_tolay_prices[runner] = eachway_back_butone[runner]                                                                                       
               # final toback price
               if raw_eachway_toback_prices[runner] == 'N/A':
                   new_eachway_toback_prices[runner] = 1001
               elif raw_eachway_toback_prices[runner] > 1000:
                   new_eachway_toback_prices[runner] = 1001
               elif eachway_lay_butone[runner] > raw_eachway_toback_prices_margin_1[runner]:
                   cur.execute("select min(price) from odds_ladder where price >= ?", [raw_eachway_toback_prices_margin_1[runner]])  
                   new_eachway_toback_prices[runner] = cur.fetchall()[0][0]
               elif eachway_lay_butone[runner] < raw_eachway_toback_prices_margin_2[runner]:
                   cur.execute("select min(price) from odds_ladder where price >= ?", [raw_eachway_toback_prices_margin_2[runner]])  
                   new_eachway_toback_prices[runner] = cur.fetchall()[0][0]
               else:
                   new_eachway_toback_prices[runner] = eachway_lay_butone[runner] 
       #back_over_round = sum(1./new_eachway_tolay_prices)
       #lay_over_round = sum(1./new_eachway_toback_prices)
                   

    # place bets in each-way market
       for runner in range(0,len(runners)-removed_runners):
           # lay bets
           if lay_bet_ids[runner] == 0:
               sizeRemaining = 0
           else:
               status = lib_api_commands.betStatus(lay_bet_ids[runner], appKey, sessionToken)
               sizeRemaining = status['currentOrders'][0]['sizeRemaining']
           if (new_eachway_tolay_prices[runner] != old_eachway_tolay_prices[runner] or sizeRemaining == 0) and worst_cases[runner] < max_runner_liability:
               suggested_stake = round(min(max(trading_stake,worst_cases[runner]/4),1000)/max(new_eachway_tolay_prices[runner],1.01),0)
               if new_eachway_tolay_prices[runner] >= 200:
                       new_eachway_tolay_prices[runner] = 200
               suggested_stake = max(suggested_stake,2)
               max_stake = round(((worst_cases[runner]+max_market_liability)/max(new_eachway_tolay_prices[runner],1.01))/2,0)
               max_stake = max(max_stake,2)
               stake = min(suggested_stake,max_stake)
               if stake < 2 or worst_cases[runner] < -max_runner_liability or new_eachway_tolay_prices[runner] < 1.01 :    
                   if sizeRemaining == 0:
                       lay_bet_ids[runner] = 0
                       result = '' + eachway_selection_names[runner] + ' Lay - No longer Laying'
                   else:
                       order = lib_api_commands.cancelBet(str(marketId), str(lay_bet_ids[runner]), appKey, sessionToken)
                       lay_bet_ids[runner] = 0
                       result = '' + eachway_selection_names[runner] + ' Lay - No longer Laying'
               elif lay_bet_ids[runner] == 0:
                   order = lib_api_commands.doWager(str(marketId), str(runners[runner]['selectionId']), "LAY", str(stake), str(new_eachway_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(runners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                   lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                   result = '' + eachway_selection_names[runner] + ' Lay - New Bet Placed'
               else:
                   if sizeRemaining == 0:
                       order = lib_api_commands.doWager(str(marketId), str(runners[runner]['selectionId']), "LAY", str(stake), str(new_eachway_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(runners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                       lay_bet_ids[runner] = order['instructionReports'][0]['betId']
                       result = '' + eachway_selection_names[runner] + ' Lay - New Bet Placed'
                   else:
                       order = lib_api_commands.replaceBet(str(marketId), str(lay_bet_ids[runner]), str(new_eachway_tolay_prices[runner]), strategy_name + str(marketId) + str(runners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                       lay_bet_ids[runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
                       result = '' + eachway_selection_names[runner] + ' Lay - Odds Updated'       
           else:
               eggs = 'eggs'                
    old_eachway_tolay_prices = new_eachway_tolay_prices
    old_eachway_toback_prices = new_eachway_toback_prices
    #print('\nEach Way Market '+marketId+' - Expected Value: £' +str(round(expeted_value, 2))+'')                   
    #print('Each Way Market '+marketId+' - Worst Case Outcome: £' +str(min([round(n, 2) for n in worst_cases]))+'')
    lib_dn_tasks.log_market_position(datetime.datetime.now(), marketId, 'Each Way', round(expeted_value, 2), min([round(n, 2) for n in worst_cases]), matched_volume)
    return round(expeted_value, 2), min([round(n, 2) for n in worst_cases])


##    # check market parameters
##    winrunners = winmarketBook[0]['runners']
##    placerunners = placemarketBook[0]['runners']
##    eachwayrunners = eachwaymarketBook[0]['runners']
##    print(winrunners)
##    if len(eachwayrunners) != len(placerunners) or len(eachwayrunners) != len(winrunners):
##        order = lib_api_commands.cancelOrders(str(eachwaymarketID), appKey, sessionToken)
##        print ('Error Market '+eachwaymarketID+': There are ' +str(len(winrunners))+ ' Win runners, '+str(len(placerunners))+ ' Place runners, '+str(len(eachwayrunners))+ ' Each Way runners, ')
##        back_bet_ids = back_bet_ids*0
##        lay_bet_ids = lay_bet_ids*0  
##    else:
