import pandas as pd
import csv
import datetime
import time
import requests
import math as math

def cal_mid_price (gr_bid_level, gr_ask_level, mid_type):
    
    level = 5 
    #gr_rB = gr_bid_level.head(level)
    #gr_rT = gr_ask_level.head(level)
    
    if len(gr_bid_level) > 0 and len(gr_ask_level) > 0:
        bid_top_price = gr_bid_level.iloc[0].price
        bid_top_level_qty = gr_bid_level.iloc[0].quantity
        ask_top_price = gr_ask_level.iloc[0].price
        ask_top_level_qty = gr_ask_level.iloc[0].quantity
        mid_price = (bid_top_price + ask_top_price) * 0.5 
    
        if mid_type == 'wt':
            mid_price = ((gr_bid_level.head(level))['price'].mean() + (gr_ask_level.head(level))['price'].mean()) * 0.5
        elif mid_type == 'mkt':
            mid_price = ((bid_top_price*ask_top_level_qty) + (ask_top_price*bid_top_level_qty))/(bid_top_level_qty+ask_top_level_qty)
            mid_price = truncate(mid_price, 1)
        elif mid_type == 'vwap':
            mid_price = (group_t['total'].sum())/(group_t['units_traded'].sum())
            mid_price = truncate(mid_price, 1)
        
        #print mid_type, mid_price

        return (mid_price, bid_top_price, ask_top_price, bid_top_level_qty, ask_top_level_qty)

    else:
        print ('Error: serious cal_mid_price')
        return (-1, -1, -2, -1, -1)


def live_cal_book_i_v1(param, gr_bid_level, gr_ask_level, diff, var, mid):
    
    mid_price = mid

    ratio = param[0]; level = param[1]; interval = param[2]
    #print ('processing... %s %s,level:%s,interval:%s' % (sys._getframe().f_code.co_name,ratio,level,interval)), 
    
        
    #_flag = var['_flag']
        
    #if _flag: #skipping first line
       # var['_flag'] = False
       # return 0.0

    quant_v_bid = gr_bid_level.quantity**ratio
    price_v_bid = gr_bid_level.price * quant_v_bid

    quant_v_ask = gr_ask_level.quantity**ratio
    price_v_ask = gr_ask_level.price * quant_v_ask
 
    #quant_v_bid = gr_r[(gr_r['type']==0)].quantity**ratio
    #price_v_bid = gr_r[(gr_r['type']==0)].price * quant_v_bid

    #quant_v_ask = gr_r[(gr_r['type']==1)].quantity**ratio
    #price_v_ask = gr_r[(gr_r['type']==1)].price * quant_v_ask
        
    askQty = quant_v_ask.values.sum()
    bidPx = price_v_bid.values.sum()
    bidQty = quant_v_bid.values.sum()
    askPx = price_v_ask.values.sum()
    bid_ask_spread = interval
        
    book_price = 0 #because of warning, divisible by 0
    if bidQty > 0 and askQty > 0:
        book_price = (((askQty*bidPx)/bidQty) + ((bidQty*askPx)/askQty)) / (bidQty+askQty)

        
    indicator_value = (book_price - mid_price) / bid_ask_spread
    #indicator_value = (book_price - mid_price)
    
    return indicator_value



def live_cal_book_d_v1(param, gr_bid_level, gr_ask_level, diff, var, mid):

    #print gr_bid_level
    #print gr_ask_level

    ratio = param[0]; level = param[1]; interval = param[2]
    #print ('processing... %s %s,level:%s,interval:%s' % (sys._getframe().f_code.co_name,ratio,level,interval)), 

    decay = math.exp(-1.0/interval)
    
    flag = var['flag']
    prevBidQty = var['prevBidQty']
    prevAskQty = var['prevAskQty']
    prevBidTop = var['prevBidTop']
    prevAskTop = var['prevAskTop']
    bidSideAdd = var['bidSideAdd']
    bidSideDelete = var['bidSideDelete']
    askSideAdd = var['askSideAdd']
    askSideDelete = var['askSideDelete']
    bidSideFlip = var['bidSideFlip']
    askSideFlip = var['askSideFlip']
    bidSideCount = var['bidSideCount']
    askSideCount = var['askSideCount'] 
  
    curBidQty = gr_bid_level['quantity'].sum()
    curAskQty = gr_ask_level['quantity'].sum()
    curBidTop = gr_bid_level.iloc[0].price #what is current bid top?
    curAskTop = gr_ask_level.iloc[0].price

    #curBidQty = gr_r[(gr_r['type']==0)].quantity.sum()
    #curAskQty = gr_r[(gr_r['type']==1)].quantity.sum()
    #curBidTop = gr_r.iloc[0].price #what is current bid top?
    #curAskTop = gr_r.iloc[level].price


    if flag:
        var['prevBidQty'] = curBidQty
        var['prevAskQty'] = curAskQty
        var['prevBidTop'] = curBidTop
        var['prevAskTop'] = curAskTop
        var['flag'] = False
        return 0.0
        
    if curBidQty > prevBidQty:
        bidSideAdd += 1
        bidSideCount += 1
    if curBidQty < prevBidQty:
        bidSideDelete += 1
        bidSideCount += 1
    if curAskQty > prevAskQty:
        askSideAdd += 1
        askSideCount += 1
    if curAskQty < prevAskQty:
        askSideDelete += 1
        askSideCount += 1
        
    if curBidTop < prevBidTop:
        bidSideFlip += 1
        bidSideCount += 1
    if curAskTop > prevAskTop:
        askSideFlip += 1
        askSideCount += 1
    if bidSideCount == 0:
        bidSideCount += 1
    if askSideCount == 0:
        askSideCount += 1
    if bidSideCount == 0:
        bidSideCount = 1
    if askSideCount == 0:
        askSideCount = 1

    bidBookV = (-bidSideDelete + bidSideAdd - bidSideFlip) / (bidSideCount**ratio)
    askBookV = (askSideDelete - askSideAdd + askSideFlip ) / (askSideCount**ratio)
    bookDIndicator = askBookV + bidBookV
    var['bidSideCount'] = bidSideCount * decay #exponential decay
    var['askSideCount'] = askSideCount * decay
    var['bidSideAdd'] = bidSideAdd * decay
    var['bidSideDelete'] = bidSideDelete * decay
    var['askSideAdd'] = askSideAdd * decay
    var['askSideDelete'] = askSideDelete * decay
    var['bidSideFlip'] = bidSideFlip * decay
    var['askSideFlip'] = askSideFlip * decay

    var['prevBidQty'] = curBidQty
    var['prevAskQty'] = curAskQty
    var['prevBidTop'] = curBidTop
    var['prevAskTop'] = curAskTop
    #var['df1'] = df1
 
    return bookDIndicator


df = pd.read_csv('./2023-05-07-bithumb-btc-orderbook.csv', low_memory=False).apply(pd.to_numeric, errors='ignore')
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['quantity'] = pd.to_numeric(df['price'], errors='coerce')
gr_o = df.groupby(['timestamp'])
param = [0.2, 5, 1]
var = {'flag' : 0, 'bidSideCount' : 1, 'askSideCount' : 0, 'bidSideAdd' : 0, 'bidSideDelete': 0, 'askSideAdd': 0, 'askSideDelete' : 0, 
        'bidSideFlip' : 0, 'askSideFlip' : 0, 'prevBidQty' : 0, 'prevAskQty' : 0, 'prevBidTop' : 0, 'prevAskTop' : 0}
df_f = pd.DataFrame(columns = ['book-delta', 'book-imbalance', 'mid_price', 'timestamp'])
df_f.to_csv("./2023-05-07-bithumb-btc-feature.csv", index=False, header=True, mode = 'a')
var['flag'] = True

for group in gr_o:
    timestamp = (group[1].iloc[0])['timestamp']
    group = group[1]
    gr_bid_level = group[(group.type == '0')]
    gr_ask_level = group[(group.type == '1')]
    mid_price, bid_top_price, ask_top_price, bid_top_level_qty, ask_top_level_qty = cal_mid_price(gr_bid_level, gr_ask_level, 0)
    bookI = live_cal_book_i_v1(param, gr_bid_level, gr_ask_level, 0, 0, mid_price)
    bookD = live_cal_book_d_v1(param, gr_bid_level, gr_ask_level, 0, var, mid_price)
    Indicators = [bookD, bookI, mid_price, timestamp]
    df_f = pd.DataFrame([Indicators], columns = ['book-delta', 'book-imbalance', 'mid_price', 'timestamp'])
    df_f.to_csv("./2023-05-07-bithumb-btc-feature.csv", index=False, header=False, mode = 'a')
    

