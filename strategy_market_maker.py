import myAPILib
import sqlite3
import time
import datetime


## get session token ##
sessionToken = myAPILib.loginAPING("Mirrornandi","Mirrorrush1")
if sessionToken != -1:
    appKey = 'cVbIW2A1QobjAdHV'

    
    ## define markets ##  
    marketIDs = ['1.117991336'] 

    ## set trading variables ##
    trading_stake = [50]           # standard lay to lose amount
    max_runner_liability = [100]  # actual market liability allowed for a runner before we stop laying the runner
    max_market_liability = [100]  # possible market liability allowed for a runner before we stop laying the runner
    loop_time = 600                 # number of seconds between re-checking odds for each market    
    margin_multiplier_1 = 0.20     # maximum margin to add onto price if we can still be better than current market price   
    margin_multiplier_2 = 0.00     # lowest margin to add onto price that we are willing to take  
    
    ## create calculation variables ##
    strategy_name = 'market_maker'
    selections = [['England','India','Australia','South Africa','New Zealand','Pakistan','Sri Lanka','West Indies','Bangladesh','Afghanistan']]
    my_tolay_prices = [[3.5,5.0,5.5,7.0,10.0,10.0,30.0,20.0,50.0,50.0]]
    probabilities = [[1/i for i in j] for j in my_tolay_prices]
    norm_probabilities = [[i/sum(j) for i in j] for j in probabilities]
    old_market_tolay_prices = {el:[0]*99 for el in range(0,len(marketIDs))}
    lay_bet_ids = {el:[0]*99 for el in range(0,len(marketIDs))}
    selectionIds = {el:[0]*99 for el in range(0,len(marketIDs))}
    selectionIds_liability = {el:[0]*99 for el in range(0,len(marketIDs))}
    pnl_positions = {el:[0]*99 for el in range(0,len(marketIDs))}
    ev_trend_exists = 'ev_trend' in globals()
    if ev_trend_exists == False:
        ev_trend = {el:[] for el in range(0,len(marketIDs))}


    ## impliment trading strategy ##        
    N = 0
    for n in range(0,len(marketIDs)):
        order = myAPILib.cancelOrders(str(marketIDs[n]), appKey, sessionToken)
    while N < 1:
        #N = N+1

        print("")
        print("")
        print(datetime.datetime.now())
        
        for n in range(0,len(marketIDs)):
                
            # get market details
            marketDeets = myAPILib.getMarketDeets(appKey, sessionToken, marketIDs[n])
            marketBook = myAPILib.getSelections(appKey, sessionToken, marketIDs[n])
            marketId = marketBook[0]['marketId']
            print("")
            print(marketDeets['result'][0]['marketName'] + ' - ' + marketId)

            # get runner details
            runners = marketBook[0]['runners']        
            selection_names = []
            active_runners = 0
            for runner in range(0,len(runners)):
                if marketBook[0]['runners'][runner]['status'] == 'ACTIVE':
                    active_runners = active_runners + 1
                    selection_names.append(marketDeets['result'][0]['runners'][runner]['runnerName'])
            selection_name_index = [selections[n].index(i) for i in selection_names]
            norm_probabilities[n] = [norm_probabilities[n][i] for i in selection_name_index]
            my_tolay_prices[n] = [my_tolay_prices[n][i] for i in selection_name_index]

            # check P&L positions
            market_position = myAPILib.findPnL(appKey, sessionToken, marketIDs[n], str(0), str(0), str(1))
            for runner in range(0,active_runners):
                selectionIds[n][runner] = marketBook[0]['runners'][runner]['selectionId']
                selectionIds_liability[n][runner] = market_position[0]['profitAndLosses'][runner]['selectionId']
                pnl_positions[n][runner] = market_position[0]['profitAndLosses'][runner]['ifWin']
            liability_runner_index = [selectionIds_liability[n].index(i) for i in selectionIds[n]]
            pnl_positions[n] = [pnl_positions[n][i] for i in liability_runner_index]                 
                   
            # check market parameters are ok
            if str(marketBook[0]['inplay']) != 'False':
                order = myAPILib.cancelOrders(str(marketIDs[n]), appKey, sessionToken)
                print ('Market is In-Play - Bets Cancelled')
                lay_bet_ids[n] = lay_bet_ids[n]*0
            if str(marketBook[0]['status']) != 'OPEN':
                order = myAPILib.cancelOrders(str(marketIDs[n]), appKey, sessionToken)
                print ('Market is Suspended - Bets Cancelled')
                lay_bet_ids[n] = lay_bet_ids[n]*0    
            else:
 
              
                # estimate expected value
                expeted_value = sum([j * i for j, i in zip(norm_probabilities[n], pnl_positions[n])]) 
                ev_trend[n].append(expeted_value)
                   
                # find current back prices (excluding our bets)
                market_back_prices = [0 for i in range(0,active_runners)]
                for runner in range(0,active_runners):
                    # find our bet status
                    if lay_bet_ids[n][runner] == 0:
                        sizeRemaining = 0
                    else:
                        status = myAPILib.betStatus(lay_bet_ids[n][runner], appKey, sessionToken)
                        sizeRemaining = status['currentOrders'][0]['sizeRemaining']                    
                    # compare to available bets 
                    if len(runners[runner]['ex']['availableToBack']) == 0:
                        market_back_prices[runner] = 1.01
                    elif old_market_tolay_prices[n][runner] == runners[runner]['ex']['availableToBack'][0]['price'] and sizeRemaining > 0:
                        if len(runners[runner]['ex']['availableToBack']) > 1:
                            market_back_prices[runner] = runners[runner]['ex']['availableToBack'][1]['price']
                        else:
                            market_back_prices[runner] = 1.01                       
                    else:
                        market_back_prices[runner] = runners[runner]['ex']['availableToBack'][0]['price']
                   
                # calculate new prices to lay
                raw_market_tolay_prices_margin_1 = [((i-1)*(1-margin_multiplier_1))+1 for i in my_tolay_prices[n]]
                raw_market_tolay_prices_margin_2 = [((i-1)*(1-margin_multiplier_2))+1 for i in my_tolay_prices[n]]
                # fix prices to odds ladder
                market_back_butone = [0 for i in range(0,active_runners)]
                new_market_tolay_prices = [0 for i in range(0,active_runners)]
                connection = sqlite3.connect('exchange.db')
                with connection:
                    cur = connection.cursor()
                    for runner in range(0,active_runners):
                        cur.execute("select next_price_up from odds_ladder where price = ?", [market_back_prices[runner]])
                        market_back_butone[runner] = cur.fetchall()[0][0]
                        # final tolay price
                        if my_tolay_prices[n][runner] < 1.01:
                            new_market_tolay_prices[runner] = 0
                        elif market_back_butone[runner] < raw_market_tolay_prices_margin_1[runner]:
                            cur.execute("select max(price) from odds_ladder where price <= ?", [raw_market_tolay_prices_margin_1[runner]])  
                            new_market_tolay_prices[runner] = cur.fetchall()[0][0]
                        elif market_back_butone[runner] > raw_market_tolay_prices_margin_2[runner]:
                            cur.execute("select max(price) from odds_ladder where price <= ?", [raw_market_tolay_prices_margin_2[runner]])  
                            new_market_tolay_prices[runner] = cur.fetchall()[0][0]
                        else:
                            new_market_tolay_prices[runner] = market_back_butone[runner]                                                                                       
                back_over_round = sum([1/i for i in new_market_tolay_prices])
                print('Over-round: ' +str(round(back_over_round*100,1))+'%')
                               
                # place bets in market
                for runner in range(0,active_runners):
                    # lay bets
                    if lay_bet_ids[n][runner] == 0:
                        sizeRemaining = 0
                    else:
                        status = myAPILib.betStatus(lay_bet_ids[n][runner], appKey, sessionToken)
                        sizeRemaining = status['currentOrders'][0]['sizeRemaining']
                    if new_market_tolay_prices[runner] != old_market_tolay_prices[n][runner] or sizeRemaining == 0:
                        suggested_stake = max(round(min(max(trading_stake[n],pnl_positions[n][runner]/4),1000)/max(new_market_tolay_prices[runner],1.01),0),2)
                        max_stake = round(((pnl_positions[n][runner]+max_market_liability[n])/max(new_market_tolay_prices[runner],1.01))/2,0)
                        stake = min(suggested_stake,max_stake)
                        if stake < 2 or pnl_positions[n][runner] < -max_runner_liability[n] or new_market_tolay_prices[runner] < 1.01 :    
                            if sizeRemaining == 0:
                                lay_bet_ids[n][runner] = 0
                                result = 'Selection ' + str(runner+1) + ' Lay - No longer Laying'
                            else:
                                order = myAPILib.cancelBet(str(marketId), str(lay_bet_ids[n][runner]), appKey, sessionToken)
                                lay_bet_ids[n][runner] = 0
                                result = 'Selection ' + str(runner+1) + ' Lay - No longer Laying'
                        elif lay_bet_ids[n][runner] == 0:
                            order = myAPILib.doWager(str(marketId), str(runners[runner]['selectionId']), "LAY", str(stake), str(new_market_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(runners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                            lay_bet_ids[n][runner] = order['instructionReports'][0]['betId']
                            result = 'Selection ' + str(runner+1) + ' Lay - New Bet Placed'
                        else:
                            if sizeRemaining == 0:
                                order = myAPILib.doWager(str(marketId), str(runners[runner]['selectionId']), "LAY", str(stake), str(new_market_tolay_prices[runner]), 'LAPSE', strategy_name + str(marketId) + str(runners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                                lay_bet_ids[n][runner] = order['instructionReports'][0]['betId']
                                result = 'Selection ' + str(runner+1) + ' Lay - New Bet Placed'
                            else:
                                order = myAPILib.replaceBet(str(marketId), str(lay_bet_ids[n][runner]), str(new_market_tolay_prices[runner]), strategy_name + str(marketId) + str(runners[runner]['selectionId']) + "LAY", appKey, sessionToken)
                                lay_bet_ids[n][runner] = order['instructionReports'][0]['placeInstructionReport']['betId']
                                result = 'Selection ' + str(runner+1) + ' Lay - Odds Updated'
                        print(result)        
                    else:
                        print('Selection ' + str(runner+1) + ' Lay - Odds Have not Changed')                   
                       
            old_market_tolay_prices[n] = new_market_tolay_prices
            print('Expected Value: £' +str(round(expeted_value, 2))+'')
            print('EV Trend: ' +str([round(n, 2) for n in ev_trend[n][max(0,len(ev_trend[n])-20):len(ev_trend[n])]])+'')                   
            print('Wost Outcome: £' +str(min([round(n, 2) for n in pnl_positions[n]]))+'')
            print('P&L Positions: ' +str([round(i, 2) for i in pnl_positions[n][0:active_runners]])+'')

        time.sleep(loop_time)
