import time
import requests
import pandas as pd
import datetime

name_timestamp = 0

while (1):
    
    book = {}

    try:
        response = requests.get ('https://api.bithumb.com/public/orderbook/BTC_KRW/?count=5', timeout=10)
    except:
        continue

    book = response.json()


    data = book['data']

    bids = (pd.DataFrame(data['bids'])).apply(pd.to_numeric,errors='ignore')
    bids.sort_values('price', ascending=False, inplace=True)
    bids = bids.reset_index(); del bids['index']
    bids['type'] = 0

    asks = (pd.DataFrame(data['asks'])).apply(pd.to_numeric,errors='ignore')
    asks.sort_values('price', ascending=True, inplace=True)
    asks['type'] = 1 


    df = pd.concat([bids, asks])


    timestamp = datetime.datetime.now()
    req_timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')


    df['quantity'] = df['quantity'].round(decimals=4)
    df['timestamp'] = req_timestamp


    check_timestamp = timestamp.strftime('%Y-%m-%d')


    if name_timestamp == check_timestamp:
        name_timestamp = timestamp.strftime('%Y-%m-%d')
        filename = f'{name_timestamp}-bithumb-btc-orderbook.csv'
        df.to_csv("./"+filename, index=False, header=False, mode = 'a')
        
    else:
        name_timestamp = timestamp.strftime('%Y-%m-%d')
        filename = f'{name_timestamp}-bithumb-btc-orderbook.csv'
        df.to_csv("./"+filename, index=False, header=True, mode = 'a')
        
    
    time.sleep(1)

