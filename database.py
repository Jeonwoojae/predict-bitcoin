from sqlalchemy import create_engine
import pymysql
import pandas as pd
import numpy as np
import pyupbit
import time


db_connection_str = 'mysql+pymysql://root:0000@localhost:3306/upbit_data'
db_connection = create_engine(db_connection_str)
conn = db_connection.connect()

def bring_coin_data():
    DBdata = pd.read_sql_table('upbit_data',conn)
    
    return DBdata 

def Inseart_data_upbit(coin_select, date_select, countofdata, to_date):
	#################################################################################
    #res = [pd.DataFrame(columns=['open','high','low', 'close', 'volume', 'value'])]


    res = []
    ##count = int(countofdata/200)
    count = 1
    for i in range(count):
        df = pyupbit.get_ohlcv('KRW-'+coin_select, interval=date_select, count=countofdata, to=to_date)
        

        market_date = df.index
        df['DateTime'] = market_date    # 날짜 정보 추가
        df['coinID'] = coin_select    # 마켓 정보 추가
        # 열 이름은 테이블의 이름과 같아야한다.

        #df = df[['dateCoin','idCoin','open', 'high', 'low', 'close', 'volume', 'value']]     # 데이터 순서 변경
        #print(df)
        res.append(df)

        date = df.index[0]
        time.sleep(0.1)

    df = pd.concat(res).sort_index()
    
    return df

def save_data(coin_name):
    # 예측할 코인 ID
    coinid = coin_name

    # 시작가 or 종료가
    col = 'close'

    # 분봉 단위 및 day단위
    interval = 'minute30'

    # API를 통해서 가져올 데이터의 수
    rows = 10000

    # Date
    date= '20220824 00:00:01'

    loaded_data = Inseart_data_upbit(coinid, interval, rows, date)

    return loaded_data

