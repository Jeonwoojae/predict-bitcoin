from cgi import test
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LSTM, Conv1D, Lambda
from tensorflow.keras.losses import Huber
from tensorflow.keras.optimizers import Adam
from sklearn.preprocessing import MinMaxScaler
import numpy as np
import pandas as pd
import tensorflow as tf
import os

model = Sequential([
    # 1차원 feature map 생성
    Conv1D(filters=32, kernel_size=5,
           padding="causal",
           activation="relu",
           input_shape=[10, 1]), # WINDOW_SIZE = 10
    # LSTM
    LSTM(16, activation='tanh'),
    Dense(16, activation="relu"),
    Dense(1),
])

def windowed_dataset(series, window_size, batch_size, shuffle):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    if shuffle:
        ds = ds.shuffle(1000)
    ds = ds.map(lambda w: (w[:-1], w[-1]))

    return ds.batch(batch_size).prefetch(1)

def do_predict(test_data):

    scaler = MinMaxScaler()
    # 스케일을 적용할 column을 정의합니다.
    scale_cols = ['close']
    # 스케일 후 columns
    scaled = scaler.fit_transform(test_data[scale_cols])
    scaled_df = pd.DataFrame(scaled, columns=scale_cols)

    test_data = windowed_dataset(scaled_df, 10, 32, False)

    # Sequence 학습에 비교적 좋은 퍼포먼스를 내는 Huber()를 사용합니다.
    loss = Huber()
    optimizer = Adam(0.0005)
    model.compile(loss=Huber(), optimizer=optimizer, metrics=['mse'])

    filename = os.path.join('tmp', 'ckeckpointer.ckpt')
    # 저장한 modelcheckpoint를 로드
    model.load_weights(filename)
    # test_data를 사용하여 예측을 진행
    pred = model.predict(test_data)
    print("예측 완료")
    print(pred.shape)
    pred=scaler.inverse_transform(pred)

    return pred

   