import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import mplfinance as mpf
import pandas as pd

import database

form_class = uic.loadUiType("test.ui")[0]



class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)
        self.initUI()
        self.dataDB = database.bring_coin_data()
        
        # 코인 종류 ComboBox가 변경 되었을 때
        self.SelectCoincomboBox.currentIndexChanged.connect(self.getComboBoxItem)

    def initUI(self):
        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)


    def getComboBoxItem(self) :
        coinid = self.SelectCoincomboBox.currentText()
        #database.save_data(coinid)

        # coinid에 해당하는 data 가져오기
        dataset_from_DB = self.dataDB.set_index(keys='DateTime')
        dataset_from_DB.index.name=None

        df = pd.DataFrame()
        df = dataset_from_DB[dataset_from_DB['coinID'] == coinid]
        df.drop(labels='coinID', axis=1)
        print(df.shape)

        self.fig.clear()

        mc = mpf.make_marketcolors(up='r', down='b',
                                    edge='white',
                                    wick={'up':'red', 'down':'blue'},
                                    volume='in',
                                    )
        s = mpf.make_mpf_style(marketcolors=mc)
        fig = mpf.plot(df, type='line', style = s, mav=(5,20), volume=True)
        #fig.legend()
        self.canvas.draw()


if __name__ == "__main__" :
    #QApplication : 프로그램을 실행시켜주는 클래스
    app = QApplication(sys.argv) 

    #WindowClass의 인스턴스 생성
    myWindow = WindowClass() 

    #프로그램 화면을 보여주는 코드
    myWindow.show()

    #프로그램을 이벤트루프로 진입시키는(프로그램을 작동시키는) 코드
    app.exec_()