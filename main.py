import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
import pyqtgraph as pg

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import mplfinance as mpf
import pandas as pd
import time
import numpy as np

import database
import trained_model

form_class = uic.loadUiType("test.ui")[0]



class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.dataDB = database.bring_coin_data()
        

        # predict 버튼을 눌렀을 때
        self.button_Predict.clicked.connect(self.predict_coin)

        # 현재가 버튼을 눌렀을 때
        self.button_Chart.clicked.connect(self.displayChart)


    def predict_coin(self):
        print('predict')

        # 예측할 coin 가져오기
        text = self.SelectCoincomboBox.currentText()
        df = pd.DataFrame(self.dataDB)
        df = df[df['coinID'] == text]
        df.drop(labels='coinID', axis=1)

        # 예측할 날짜 가져오기
        select_date = self.dateTimeEdit.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        print('선택한 날짜 : ' + select_date)
        df = df[df['DateTime'] > select_date]
        
        df = df.set_index(keys='DateTime')
        DateTime = df.index
        df.index.name=None

        # 시간 단위 나누기
        if self.UnitofTime_Button_d.isChecked():
            df = df.resample(rule='1D').first()
        elif self.UnitofTime_Button_h.isChecked():
            df = df.resample(rule='1H').first()
        elif self.UnitofTime_Button_m.isChecked():
            df = df.resample(rule='30T').first()
        
        print(df.shape)

        # 예측 시작
        res = trained_model.do_predict(df).flatten().tolist()
        #print(res.shape)
        date = np.arange(0,len(res),)

        # 예측 결과 출력
        self.priceChart.setBackground('w')
        self.priceChart.setTitle('Predict result')
        self.priceChart.plot(date,res,pen=(0,0,255))

    def displayChart(self) :
        coinid = self.SelectCoincomboBox.currentText()
        #database.save_data(coinid) # 데이터 업데이트 필요

        # coinid에 해당하는 data 가져오기
        df = pd.DataFrame(self.dataDB)
        df = df[df['coinID'] == coinid]
        df.drop(labels='coinID', axis=1)
        df = df.set_index(keys='DateTime')
        df.index.name=None

        # 시간 단위 나누기
        # 거래량 합치기, 종가, 시가 작업 필요할
        if self.UnitofTime_Button_d.isChecked():
            df = df.resample(rule='1D').first()
        elif self.UnitofTime_Button_h.isChecked():
            df = df.resample(rule='1H').first()
        elif self.UnitofTime_Button_m.isChecked():
            df = df.resample(rule='30T').first()

        print(df.shape)

        mc = mpf.make_marketcolors(up='r', down='b',
                                    edge='white',
                                    wick={'up':'red', 'down':'blue'},
                                    volume='in',
                                    )
        s = mpf.make_mpf_style(marketcolors=mc)
        fig = mpf.plot(df, type='line', style = s, mav=(5,20), volume=True)
        #fig.legend()


if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #WindowClass의 인스턴스 생성
    myWindow = WindowClass() 

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()