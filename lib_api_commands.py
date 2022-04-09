import requests
import urllib
import urllib.request
import urllib.error
import json
import datetime
import sys
import time

        
############################################################
# log into Betfair API - you need a certificate

def loginAPING(userName,passWord):
  ### reurns session token or -1 if fails ###
    
    appKey = 'cVbIW2A1QobjAdHV' # seems to be needed although not a valid appkey
    
    payload = 'username='+userName+'&password='+passWord
    headers = {'X-Application': appKey,'Content-Type': 'application/x-www-form-urlencoded'}

    # now we call the cetificate
    resp = requests.post('https://identitysso-cert.betfair.com/api/certlogin', data=payload, cert=('client-2048.crt', 'client-2048.key'), headers=headers) 
    resp_json = resp.json()
    if resp_json['loginStatus'] == 'SUCCESS':
      return resp_json['sessionToken']
    else:
       return -1

############################################################
# keeps log in session alive

def keepAlive(sessionToken,appKey): 

    headers = {'Accept': 'application/json','X-Authentication': sessionToken,'X-Application': appKey}

    resp = requests.post('https://identitysso.betfair.com/api/keepAlive', headers=headers)
    resp_json = resp.json()
    #print(resp_json)
    if resp_json['status'] == 'SUCCESS':
       print('Session Renewed')
    else:
       print('Session Ending')
       
###########################################################
# needed for retrieving data from the API

def callAping(jsonrpc_req, appKey, sessionToken):

    headers = {'X-Application': appKey, 'X-Authentication': sessionToken, 'content-type': 'application/json'}
    url = "https://api.betfair.com/exchange/betting/json-rpc/v1"
    try:
        req = urllib.request.Request(url, jsonrpc_req.encode('utf-8'), headers)
        response = urllib.request.urlopen(req)  #######error#######
        jsonResponse = response.read()
        return jsonResponse.decode('utf-8')
    except urllib.error.URLError as e:
        print (e.reason) 
        print ('Oops no service available at ' + str(url))
        exit()
    except urllib.error.HTTPError:
        print ('Oops not a valid operation from the service ' + str(url))
        exit()
       
###########################################################
# returns details about a market
    
def getMarketDeets(appKey, sessionToken, marketID):

    market_catalogue_req = '{"jsonrpc": "2.0","method": "SportsAPING/v1.0/listMarketCatalogue","params": {"filter": {"marketIds": ["'+ marketID +'"]}, "maxResults": "1","marketProjection":["RUNNER_METADATA"]},"id": 1}' 
    market_catalogue_response = callAping(market_catalogue_req, appKey, sessionToken)
    decodedCatalogue = json.loads(market_catalogue_response)
    return decodedCatalogue

###########################################################
# returns details about a selection

def getSelections(appKey, sessionToken, marketID):

   market_book_req = '{"jsonrpc": "2.0","method": "SportsAPING/v1.0/listMarketBook","params": {"marketIds": ["'+ marketID +'"],"priceProjection": {"priceData": ["EX_BEST_OFFERS","EX_TRADED","SP_AVAILABLE"],"virtualise": "true"}},"id": 1}' 
   market_book_response = callAping(market_book_req, appKey, sessionToken)
   decodedSelections = json.loads(market_book_response)
   try:
       selectionsResult = decodedSelections['result']
       return selectionsResult
   except:
       print('Exception from API-NG' + str(selectionsResult['error']))

#####################################################
# places a bet

def doWager(marketId, horseId, backOrLay, stake, price, persistence, cRef, appKey, sessionToken):

    ## returns betResult access status of bet through betResult['status']
    bet_place_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId": "' +marketId+ '","instructions": \
                     [{"selectionId": "' +horseId+ '", "handicap": "0", "side": "' +backOrLay+ '", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +price+ '", "persistenceType": "' +persistence+ '" } } ] }, "id": 1 }'
                  #  [{"selectionId": "' +horseId+ '", "handicap": "0", "side": "' +backOrLay+ '", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +price+ '", "persistenceType": "' +persistence+ '" } } ],"customerRef":"' +cRef+ '"}, "id": 1 }'
                      
    # orig ---> bet_place_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId": "' +marketId+ '","instructions": [{"selectionId": "' +horseId+ '", "handicap": "0", "side": "' +backOrLay+ '", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +price+ '", "persistenceType": "' +persistence+ '" } } ]}, "id": 1 }'
    bet_place_resp = callAping(bet_place_req, appKey, sessionToken)
    decodeBetResp = json.loads(bet_place_resp)
    #print(decodeBetResp)

    return decodeBetResp['result']

#####################################################
# changes a bets odds

def replaceBet(marketId, betId, newPrice, cRef, appKey, sessionToken):

   replace_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/replaceOrders", "params": {"marketId": "' +marketId+ '", "instructions": \
                  [{"betId": "' +betId+ '", "newPrice": "' +newPrice+ '"}] }, "id": 1}'
   replace_response = callAping(replace_req, appKey, sessionToken)
   replace_response_loads = json.loads(replace_response)
   try:
       replace_response_result = replace_response_loads['result']
       return replace_response_result
   except:
       print('Exception from API-NG' + str(replace_response_loads['error']))

#####################################################
# cancels a bet

def cancelBet(marketId, betId, appKey, sessionToken):

    cancel_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/cancelOrders", "params": {"marketId": "' +marketId+ '", "instructions":[{"betId": "' +betId+ '"}]}, "id": 1}'
    cancel_response = callAping(cancel_req, appKey, sessionToken)
    cancel_response_loads = json.loads(cancel_response)
    try:
        cancel_response_result = cancel_response_loads['result']
        return cancel_response_result
    except:
        print('Exception from API-NG' + str(cancel_response_loads['error']))
        
#####################################################
# finde the possible P&L ut comes of a market
       
def findPnL(appKey, sessionToken, marketId, includeSettledBets, includeBspBets, netOfCommission):

   pnl_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketProfitAndLoss",  "params": {"marketIds": ["' +marketId+ '"], "netOfCommission": 1 \
                    }, "id": 1}'
                    #, "includeSettledBets": ("'+includeSettledBets+'" == "True"), "includeBspBets": ("'+includeBspBets+'" == "True"), "netOfCommission": ("'+netOfCommission+'" == "True") \
                                     
   pnl_response = callAping(pnl_req, appKey, sessionToken)
   pnl_response_loads = json.loads(pnl_response)

   return pnl_response_loads['result']

#####################################################
# cancels all bets in a market

def cancelOrders(marketId, appKey, sessionToken):

    cancel_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/cancelOrders", "params": {"marketId": "' +marketId+ '"}, "id": 1}'
    cancel_response = callAping(cancel_req, appKey, sessionToken)
    cancel_response_loads = json.loads(cancel_response)
    try:
        cancel_response_result = cancel_response_loads['result']
        return cancel_response_result
    except:
        print('Exception from API-NG' + str(cancel_response_loads['error']))

#####################################################
# returns the satus of a bet

def betStatus(betId, appKey, sessionToken):

    status_req = '{"jsonrpc": "2.0","method": "SportsAPING/v1.0/listCurrentOrders","params": {"betIds": [' +betId+ ']}, "id": 1}'
    status_response = callAping(status_req, appKey, sessionToken)
    status_response_loads = json.loads(status_response)
    return status_response_loads['result']

#####################################################
# returns current bets in a market

def currentOrders(marketId, status, appKey, sessionToken):

    orders_req = '{"jsonrpc": "2.0","method": "SportsAPING/v1.0/listCurrentOrders","params": {"marketIds": [' +marketId+ '], "orderProjection": "' +status+ '"}, "id": 1}'
    orders_response = callAping(orders_req, appKey, sessionToken)
    orders_response_loads = json.loads(orders_response)
    return orders_response_loads['result']        























## UNUSED API FUNCTION CALLS ##



#####################################################

def findMarkets(eventTypeIds, marketNames, periodstart, periodend, appKey, sessionToken):

    market_req = '{"jsonrpc": "2.0","method": "SportsAPING/v1.0/listMarketCatalogue","params": {"filter": {eventTypeIds": [' +eventTypeIds+ '],"marketTypeCodes": ["WIN","PLACE","EACH WAY"],"marketStartTime": {"from": "2018-03-31T00:00:00Z","to": "2018-03-31T23:59:00Z"}},"maxResults": "200","marketProjection": ["MARKET_START_TIME","RUNNER_METADATA","RUNNER_DESCRIPTION","EVENT_TYPE","EVENT","COMPETITION","MARKET_DESCRIPTION"]},"id": 1}'
    market_response = callAping(market_req, appKey, sessionToken)
    market_response_loads = json.loads(market_response)
    return market_response_loads['result']

#############################################################

def getEventTypes(appKey,sessionToken):
    ### returns eventypeids for all sports eg racing = 7 or -1 if fails ###
    
    event_type_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listEventTypes", "params": {"filter":{ }}, "id": 1}'
   
    eventTypesResponse = callAping(event_type_req, appKey, sessionToken)
    eventTypeLoads = json.loads(eventTypesResponse)
    
    try:
        eventTypeResults = eventTypeLoads['result']
        return eventTypeResults
    except:
        print ('Exception from API-NG' + str(eventTypeLoads['error']))
        return -1

############################################################

def getEventTypeIDForEventTypeName(eventTypesResult, requestedEventTypeName):
    if(eventTypesResult is not None):
        for event in eventTypesResult:
            eventTypeName = event['eventType']['name']
            if( eventTypeName == requestedEventTypeName):
                return event['eventType']['id']
    else:
        print ('Oops there is an issue with the input')
        return -1

###########################################################

def getEvents(appKey, sessionToken, eventTypeId, countryCodes):
   
   now = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
   date,time = now.split('T');
   # check if BST if it is pull back one hour to allow for Betfair race times being behind

   if isItSummerTime() == 1:
     hrs,mins,secs = time.split(':');
     hrs = int(hrs) - 1
     hrs = str(hrs)
     now = date+"T"+hrs+':'+mins+':'+secs
     
   to = date+"T23:59:00Z"
   market_catalogue_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketCatalogue", "params": {"filter":{"eventTypeIds":['+eventTypeId+'],"marketCountries":["US"],"marketTypeCodes":["WIN"], "marketStartTime":{"from":"' + now + '","to":"' + to + '"}},"sort":"FIRST_TO_START","maxResults":"100","marketProjection":["MARKET_START_TIME","RUNNER_DESCRIPTION","RUNNER_METADATA"]}, "id": 1}'
                                                                                                                                                             
   market_catalogue_response = callAping(market_catalogue_req, appKey, sessionToken)
   decodedRaces = json.loads(market_catalogue_response)

   try:
       decodedRacesResult = decodedRaces['result']
       return decodedRacesResult
   except:
       return -1
       
#####################################################

def spbet(marketId, selectionId, backOrLay, stake, persistence, cRef, appKey, sessionToken):
    
    bet_place_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId": "' +marketId+ '","instructions": \
                     [{"selectionId": "' +selectionId+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "orderType": "MARKET_ON_CLOSE", "marketOnCloseOrder": {"liability": "' +stake+ '"}} \
                     ],"customerRef":"' +cRef+ '"}, "id": 1 }'
     
    bet_place_resp = callAping(bet_place_req, appKey, sessionToken)
    decodeBetResp = json.loads(bet_place_resp)

    return decodeBetResp['result']


#####################################################

def backandlay8(marketId, selectionId1, selectionId2, selectionId3, selectionId4, selectionId5, selectionId6, selectionId7, selectionId8, stake, liability, layprice1, backprice1, layprice2, backprice2, layprice3, backprice3, layprice4, backprice4, layprice5, backprice5, layprice6, backprice6, layprice7, backprice7, layprice8, backprice8, persistence, cRef, appKey, sessionToken):
    
    bet_place_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId": "' +marketId+ '","instructions": \
                     [{"selectionId": "' +selectionId1+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice1)))+ '", "price": "' +str(layprice1)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId1+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice1)))+ '", "price": "' +str(backprice1)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId2+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice2)))+ '", "price": "' +str(layprice2)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId2+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice2)))+ '", "price": "' +str(backprice2)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId3+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice3)))+ '", "price": "' +str(layprice3)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId3+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice3)))+ '", "price": "' +str(backprice3)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId4+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice4)))+ '", "price": "' +str(layprice4)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId4+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice4)))+ '", "price": "' +str(backprice4)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId5+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice5)))+ '", "price": "' +str(layprice5)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId5+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice5)))+ '", "price": "' +str(backprice5)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId6+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice6)))+ '", "price": "' +str(layprice6)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId6+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice6)))+ '", "price": "' +str(backprice6)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId7+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice7)))+ '", "price": "' +str(layprice7)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId7+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice7)))+ '", "price": "' +str(backprice7)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId8+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice8)))+ '", "price": "' +str(layprice8)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId8+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice8)))+ '", "price": "' +str(backprice8)+ '", "persistenceType": "' +persistence+ '" } } \
                     ]}, "id": 1 }'
                                                                                                                                                               
    bet_place_resp = callAping(bet_place_req, appKey, sessionToken)
    decodeBetResp = json.loads(bet_place_resp)

    #print(decodeBetResp)
    return decodeBetResp['result']
   

#####################################################

def backandlay9(marketId, selectionId1, selectionId2, selectionId3, selectionId4, selectionId5, selectionId6, selectionId7, selectionId8, selectionId9, stake, liability, layprice1, backprice1, layprice2, backprice2, layprice3, backprice3, layprice4, backprice4, layprice5, backprice5, layprice6, backprice6, layprice7, backprice7, layprice8, backprice8, layprice9, backprice9, persistence, cRef, appKey, sessionToken):
    
    bet_place_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId": "' +marketId+ '","instructions": \
                     [{"selectionId": "' +selectionId1+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice1)))+ '", "price": "' +str(layprice1)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId1+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice1)))+ '", "price": "' +str(backprice1)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId2+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice2)))+ '", "price": "' +str(layprice2)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId2+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice2)))+ '", "price": "' +str(backprice2)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId3+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice3)))+ '", "price": "' +str(layprice3)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId3+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice3)))+ '", "price": "' +str(backprice3)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId4+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice4)))+ '", "price": "' +str(layprice4)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId4+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice4)))+ '", "price": "' +str(backprice4)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId5+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice5)))+ '", "price": "' +str(layprice5)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId5+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice5)))+ '", "price": "' +str(backprice5)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId6+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice6)))+ '", "price": "' +str(layprice6)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId6+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice6)))+ '", "price": "' +str(backprice6)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId7+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice7)))+ '", "price": "' +str(layprice7)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId7+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice7)))+ '", "price": "' +str(backprice7)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId8+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice8)))+ '", "price": "' +str(backprice8)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId9+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice9)))+ '", "price": "' +str(layprice9)+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId9+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/backprice9)))+ '", "price": "' +str(backprice9)+ '", "persistenceType": "' +persistence+ '" } }  \
                     ]}, "id": 1 }'
    # {"selectionId": "' +selectionId8+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +str(max(stake,int(liability/layprice8)))+ '", "price": "' +str(layprice8)+ '", "persistenceType": "' +persistence+ '" } }, \
                                                                                                                                                                                               
    bet_place_resp = callAping(bet_place_req, appKey, sessionToken)
    decodeBetResp = json.loads(bet_place_resp)

    print(decodeBetResp)
    return decodeBetResp['result']
   

#####################################################

def backandlay2(marketId, selectionId1, selectionId2, stake, layprice1, layprice2, backprice1, backprice2, persistence, cRef, appKey, sessionToken):
    
    bet_place_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId": "' +marketId+ '","instructions": \
                     [{"selectionId": "' +selectionId1+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +layprice1+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId1+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +backprice1+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId2+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +layprice2+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId2+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +backprice2+ '", "persistenceType": "' +persistence+ '" } } \
                     ],"customerRef":"' +cRef+ '"}, "id": 1 }'
     
    bet_place_resp = callAping(bet_place_req, appKey, sessionToken)
    decodeBetResp = json.loads(bet_place_resp)

    return decodeBetResp['result']

#####################################################

def backandlay3(marketId, selectionId1, selectionId2, selectionId3, stake, layprice1, layprice2, layprice3, backprice1, backprice2, backprice3, persistence, cRef, appKey, sessionToken):
    
    bet_place_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId": "' +marketId+ '","instructions": \
                     [{"selectionId": "' +selectionId1+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +layprice1+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId1+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +backprice1+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId2+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +layprice2+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId2+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +backprice2+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId3+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +layprice3+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId3+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +backprice3+ '", "persistenceType": "' +persistence+ '" } } \
                     ],"customerRef":"' +cRef+ '"}, "id": 1 }'

              
    bet_place_resp = callAping(bet_place_req, appKey, sessionToken)
    decodeBetResp = json.loads(bet_place_resp)

    return decodeBetResp['result']

   
#####################################################

def tradesp_back(marketId, selectionId, stake, layprice, persistence, cRef, appKey, sessionToken):
    
    bet_place_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId": "' +marketId+ '","instructions": \
                     [{"selectionId": "' +selectionId+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +layprice+ '", "persistenceType": "' +persistence+ '" } }, \
                      {"selectionId": "' +selectionId+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "orderType": "MARKET_ON_CLOSE", "marketOnCloseOrder": {"liability": "' +stake+ '"}} \
                     ],"customerRef":"' +cRef+ '"}, "id": 1 }'
     
    bet_place_resp = callAping(bet_place_req, appKey, sessionToken)
    decodeBetResp = json.loads(bet_place_resp)

    return decodeBetResp['result']

                      

#####################################################

def tradesp_lay(marketId, selectionId, stake, layliability, backprice, persistence, cRef, appKey, sessionToken):
    
    bet_place_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/placeOrders", "params": {"marketId": "' +marketId+ '","instructions": \
                     [{"selectionId": "' +selectionId+ '", "handicap": "0", "side": "LAY", "orderType": "LIMIT", "orderType": "MARKET_ON_CLOSE", "marketOnCloseOrder": {"liability": "' +layliability+ '"}}, \
                      {"selectionId": "' +selectionId+ '", "handicap": "0", "side": "BACK", "orderType": "LIMIT", "limitOrder": { "size": "' +stake+ '", "price": "' +backprice+ '", "persistenceType": "' +persistence+ '" } }, \
                      ],"customerRef":"' +cRef+ '"}, "id": 1 }'
     
    bet_place_resp = callAping(bet_place_req, appKey, sessionToken)
    decodeBetResp = json.loads(bet_place_resp)

    return decodeBetResp['result']


#####################################################

#def eachway():
   

   
#####################################################

#http://docs.developer.betfair.com/docs/display/1smk3cen4v3lu3yomq5qye0ni/Python#

def getMarketBook(marketId, appKey, sessionToken):
    market_book_req = '{"jsonrpc": "2.0", "method": "SportsAPING/v1.0/listMarketBook", "params": {"marketIds":["' + marketId + '"],"priceProjection":{"priceData":["EX_BEST_OFFERS"]}}, "id": 1}'
    market_book_response = callAping(market_book_req, appKey, sessionToken)
    market_book_loads = json.loads(market_book_response)
    try:
        market_book_result = market_book_loads['result']
        return market_book_result
    except:
        print('Exception from API-NG' + str(market_book_loads['error']))
        
##################################################### 
 
def printPriceInfo(market_book_result):
    for marketBook in market_book_result:
        try:
            runners = marketBook['runners']
            print(runners)
            for runner in runners:
                print('Selection ID: ' + str(runner['selectionId']))
                if (runner['status'] == 'ACTIVE'):
                    print('Available to back price :' + str(runner['ex']['availableToBack']))
                    print('Available to lay price :' + str(runner['ex']['availableToLay']))
                else:
                    print('This runner is not active')
        except:
            print('No runners available for this market')

###########################################################

#https://markatsmartersig.wordpress.com/2014/04/26/betfair-api-ng-session-10/#

def isItSummerTime ():
    return time.localtime()[-1]

########################################################### 

def checkSummerTime(raceTime):
    
   date,time = raceTime.split('T');
   # check if BST if it is pull back one hour to allow for Betfair race times being behind
   if isItSummerTime() == 1:
     hrs,mins,secs = time.split(':');
     hrs = int(hrs) + 1
     hrs = str(hrs)
     raceTime = date+"T"+hrs+':'+mins+':'+secs

   return raceTime

#####################################################



