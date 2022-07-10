
    
    !pip install pyupbit
    import pyupbit
    
    #BTC 최근 200시간의 데이터 불러옴
    df = pyupbit.get_ohlcv("KRW-BTC", interval="minute60")
    df
    
    #시간(ds)와 종가(y)값만 남김
    df = df.reset_index()
    df['ds'] = df['index']
    df['y'] = df['close']
    data = df[['ds','y']]
    data
    
    #prophet 불러옴
    from fbprophet import Prophet
    
    #학습
    model=Prophet()
    model.fit(data)
    
    #24시간 미래 예측
    future = model.make_future_dataframe(periods=24, freq='H')
    forecast = model.predict(future)
    
    #그래프1
    fig1 = model.plot(forecast)
    
    #그래프2
    fig2 = model.plot_components(forecast)
