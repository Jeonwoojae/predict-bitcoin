# -*- coding: utf-8 -*-
"""LSTM_test_2.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1tzMdNQ1GAO_fhazebRyK0WFnYM8ZY6fP
"""

# !pip install pyupbit

"""# dataset 불러오기"""
    
import pyupbit
import time
import numpy as np
import pandas as pd
import tensorflow as tf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def Inseart_data_upbit(coin_select, date_select, countofdata, to_date):
	#################################################################################
    #res = [pd.DataFrame(columns=['open','high','low', 'close', 'volume', 'value'])]


    res = []
    ##count = int(countofdata/200)
    count = 1
    for i in range(count):
        df = pyupbit.get_ohlcv('KRW-'+coin_select, interval=date_select, count=countofdata, to=to_date)
        df['idCoin'] = coin_select    # 마켓 정보 추가

        market_date = df.index
        df['dateCoin'] = market_date    # 날짜 정보 추가
        # 열 이름은 테이블의 이름과 같아야한다.

        df = df[['dateCoin','idCoin', 'open', 'high', 'low', 'close', 'volume', 'value']]     # 데이터 순서 변경
        #print(df)
        res.append(df)

        date = df.index[0]
        time.sleep(0.1)

    df = pd.concat(res).sort_index()
    
    #print(type(df))
    #print(res)
    #print(df)
    return df
    ###############################################################################

# 예측할 코인 ID
coinid = 'BTC'

# 시작가 or 종료가
col = 'close'

# 분봉 단위 및 day단위
interval = 'minute30'

# API를 통해서 가져올 데이터의 수
rows = 10000

# Date
date= '20220824 00:00:01'

loaded_data = Inseart_data_upbit(coinid, interval,rows, date)
dataset = loaded_data.drop([loaded_data.columns[0], loaded_data.columns[1]], axis=1)
times = dataset.index

# dataset

# times

## db에 저장
# !pip install pymysql
# !pip install sqlalchemy

from sqlalchemy import create_engine
import pymysql
import pandas as pd
db_connection_str = 'mysql+pymysql://root:0000@localhost:3306/upbit_data'
db_connection = create_engine(db_connection_str)
conn = db_connection.connect()

dataset.to_sql(name='upbit_data', con=db_connection, if_exists='replace',index=False)

## 시각화

# plt.figure(figsize=(16, 9))
# # plot_data = dataset[['open','close']]
# plt.plot(dataset.index,dataset['close'])
# plt.xlabel('time')
# plt.ylabel('price')

## 전처리
from sklearn.preprocessing import MinMaxScaler

scaler = MinMaxScaler()
# 스케일을 적용할 column을 정의합니다.
scale_cols = ['open', 'high', 'low', 'close', 'value']
# 스케일 후 columns
scaled = scaler.fit_transform(dataset[scale_cols])
# scaled

## 새로운 데이터셋
scaled_df = pd.DataFrame(scaled, columns=scale_cols)

# inverse 하기 위한 scaler를 저장
scaled_for_inversed = scaler.fit_transform(dataset[['close']])



"""# train / test 나누기"""

from sklearn.model_selection import train_test_split

x_train, x_test, y_train, y_test = train_test_split(scaled_df.drop('close', 1), scaled_df['close'], test_size=0.2, random_state=0, shuffle=False)

# x_train.shape, y_train.shape

# x_test.shape, y_test.shape

# x_train



"""# TensorFlow Dataset을 사용하여 시퀀스 데이터셋 구성하기"""

import tensorflow as tf

def windowed_dataset(series, window_size, batch_size, shuffle):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    if shuffle:
        ds = ds.shuffle(1000)
    ds = ds.map(lambda w: (w[:-1], w[-1]))
    return ds.batch(batch_size).prefetch(1)

# 하이퍼파라미터 정하기
WINDOW_SIZE=10        #30
BATCH_SIZE=32         #32

# trian_data는 학습용 데이터셋, test_data는 검증용 데이터셋
train_data = windowed_dataset(y_train, WINDOW_SIZE, BATCH_SIZE, True)
test_data = windowed_dataset(y_test, WINDOW_SIZE, BATCH_SIZE, False)

# 아래의 코드로 데이터셋의 구성을 확인해 볼 수 있습니다.
# X: (batch_size, window_size, feature)
# Y: (batch_size, feature)
for data in train_data.take(1):
    print(f'데이터셋(X) 구성(batch_size, window_size, feature갯수): {data[0].shape}')
    print(f'데이터셋(Y) 구성(batch_size, window_size, feature갯수): {data[1].shape}')



"""# 모델"""

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Conv1D, Lambda
from tensorflow.keras.losses import Huber
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import os
import warnings


model = Sequential([
    # 1차원 feature map 생성
    Conv1D(filters=32, kernel_size=5,
           padding="causal",
           activation="relu",
           input_shape=[WINDOW_SIZE, 1]),
    # LSTM
    LSTM(16, activation='tanh'),
    Dense(16, activation="relu"),
    Dense(1),
])

# Sequence 학습에 비교적 좋은 퍼포먼스를 내는 Huber()를 사용합니다.
loss = Huber()
optimizer = Adam(0.0005)
model.compile(loss=Huber(), optimizer=optimizer, metrics=['mse'])

# earlystopping은 10번 epoch통안 val_loss 개선이 없다면 학습을 멈춥니다.
earlystopping = EarlyStopping(monitor='val_loss', patience=30)
# val_loss 기준 체크포인터도 생성합니다.
filename = os.path.join('tmp', 'ckeckpointer.ckpt')
checkpoint = ModelCheckpoint(filename, 
                             save_weights_only=True, 
                             save_best_only=True, 
                             monitor='val_loss', 
                             verbose=1)

history = model.fit(train_data, 
                    validation_data=(test_data), 
                    epochs=500, 
                    callbacks=[checkpoint, earlystopping])



history_DF = pd.DataFrame(history.history)

# # 꺾은선 그래프를 그리자.
# # 그래프의 크기와 선의 굵기를 설정해주었다.
# history_DF.plot(figsize=(12, 8), linewidth=3)

# # 교차선을 그린다.
# plt.grid(True)

# # 그래프를 꾸며주는 요소들
# plt.legend(loc = "upper right", fontsize =15)
# plt.title("Learning Curve", fontsize=30, pad = 30)
# plt.xlabel('Epoch', fontsize=20)
# plt.ylabel('Variable', fontsize = 20)
# plt.ylim([0, 0.0002]) 

# # 위 테두리 제거
# ax=plt.gca()
# ax.spines["right"].set_visible(False) # 오른쪽 테두리 제거
# ax.spines["top"].set_visible(False) # 위 테두리 제거

# test_data

# 저장한 modelcheckpoint를 로드
model.load_weights(filename)

# test_data를 사용하여 예측을 진행
pred = model.predict(test_data)

# pred.shape



"""# 예측 데이터 시각화"""

pred=scaler.inverse_transform(pred)
# pred

actual = np.asarray(y_test)[WINDOW_SIZE:]
actual = np.reshape(actual, (len(actual),1))
actual = scaler.inverse_transform(actual)
print(actual.shape)
print(pred.shape)



# plt.figure(figsize=(12, 9))
# plt.plot(actual, label='actual')
# plt.plot(pred, label='prediction')
# plt.legend()
# plt.show()

# plt.figure(figsize=(12, 9))
# plt.plot(np.asarray(actual)[1900:], label='actual')
# plt.plot(pred[1900:], label='prediction')
# plt.legend()
# plt.show()

# pred[1979]

# actual[1979]

from sklearn.metrics import mean_absolute_error

mean_absolute_error(actual,pred)

from sklearn.metrics import mean_squared_error
# MSE
MSE = mean_squared_error(actual, pred)
MSE

# RMSE
np.sqrt(MSE)

# RMSSE
def RMSSE(y_true, y_pred, y_test): 
    
    n = len(y_test)

    numerator = np.mean(np.sum(np.square(y_true - y_pred)))
    
    denominator = 1/(n-1)*np.sum(np.square((y_test[1:] - y_test[:-1])))
    
    msse = numerator/denominator
    
    return msse ** 0.5

from sklearn.metrics import mean_squared_log_error
# MSLE
MSLE = mean_squared_log_error(actual, pred)
MSLE

# RMSLE
RMSLE = np.sqrt(MSLE)
RMSLE

# MAPE
def MAPE(y_test, y_pred):
	return np.mean(np.abs((y_test - y_pred) / y_test)) * 100
    
MAPE(actual, pred)

# SMAPE
def SMAPE(y_test, y_pred):
	return np.mean((np.abs(y_test-y_pred))/(np.abs(y_test)+np.abs(y_pred)))*100

SMAPE(actual, pred)

# MAE
def MAE(y_test, y_pred):
	res = np.mean((y_test, y_pred) / y_test) * 100
	return res
    
MAE(actual, pred)