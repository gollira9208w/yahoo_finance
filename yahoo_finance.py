import sys
from yahoo_finance_api2 import share
from yahoo_finance_api2.exceptions import YahooFinanceError
import pandas as pd
import matplotlib.pyplot as plt
import japanize_matplotlib
import datetime 
import streamlit as st
from datetime import datetime
import os
import requests
from bs4 import BeautifulSoup


today = datetime.today().strftime('%Y%m%d')

def main():
    #サイドバーのラジオボタンを配置
    brand = st.sidebar.radio('銘柄を選択してください',tuple(data_dict.keys()))
    st.sidebar.write('*'*40)
    #サイドバーのセレクトボックスを配置
    period = st.sidebar.selectbox('ローソク足を表示する期間を選択してください。',
                ['1日','1週','1カ月','6カ月','1年','2年']
    )
    #if st.checkbox(f'グラフ表示'):
    #    brand_plot(period)  #各銘柄の折れ線グラフを表示
    brand_plot(period,brand)  #各銘柄の折れ線グラフを表示


def brand_plot(period,brand):
    try:
        res = requests.get(rf'https://finance.yahoo.co.jp/quote/{data_dict[brand]}.T')
        print(res)
        soup = BeautifulSoup(res.content,'html.parser')
        
        industry = soup.select('#industry')[0].text
        st.write(industry)

        name = soup.select('#root > main > div > div > div.XuqDlHPN > div:nth-child(3) > section._1zZriTjI._2l2sDX5w > div._1nb3c4wQ > header > div.DL5lxuTC > h1')[0].text
        st.write(name)

        realtime_price1 = soup.select('#root > main > div > div > div.XuqDlHPN > div:nth-child(3) > section._1zZriTjI._2l2sDX5w > div._1nb3c4wQ > div._23Y7QX2K > div._37FKL945 > ul')[0].text
        realtime_price2 = soup.select('#root > main > div > div > div.XuqDlHPN > div:nth-child(3) > section._1zZriTjI._2l2sDX5w > div._1nb3c4wQ > header > div.nOmR5zWz > span > span > span')[0].text
        st.write(realtime_price1 + ' : ' + realtime_price2)

        zenjitsuhi = soup.select('#root > main > div > div > div.XuqDlHPN > div:nth-child(3) > section._1zZriTjI._2l2sDX5w > div._1nb3c4wQ > div.PRD_bdfF > div._3PynB6qD > div > dl')[0].text
        st.write(zenjitsuhi)

        df_con = pd.DataFrame(columns=['詳細'])
        row_dict = {}    
        for s in soup.select('#detail > section._2Yx3YP9V._3v4W38Hq > div > ul > li'):
            t = s.select('dl > dt')[0].text.replace('用語','')
            v = s.select('dl > dd')[0].text
            print(t,v)

            row_dict[t] = v

        df_con = pd.concat([df_con,pd.DataFrame(pd.Series(row_dict),columns=['詳細'])])
        df_con.rename(columns={'0':'詳細'},inplace=True)
        
        #print(df_con.values)
        st.table(df_con)

        fig, ax = plt.subplots(figsize=(18, 6))

        #legend_list = []

        company_code = str(data_dict[brand])
        my_share = share.Share(company_code  + '.T')
    
        if period == '1日':
            # 1日毎の1年分のデータを取得する場合
            symbol_data = my_share.get_historical(share.PERIOD_TYPE_DAY,1,share.FREQUENCY_TYPE_HOUR,1)
        elif period == '1週':
            # 1日毎の1週間分のデータを取得する場合
            symbol_data = my_share.get_historical(share.PERIOD_TYPE_WEEK,1,share.FREQUENCY_TYPE_DAY,1)
        elif period == '1カ月':
            # 1日毎の1カ月分のデータを取得する場合
            symbol_data = my_share.get_historical(share.PERIOD_TYPE_MONTH,1,share.FREQUENCY_TYPE_DAY,1)
        elif period == '6カ月':
            # 1日毎の6カ月分のデータを取得する場合
            symbol_data = my_share.get_historical(share.PERIOD_TYPE_MONTH,6,share.FREQUENCY_TYPE_DAY,1)
        elif period == '1年':
            # 1週毎の1年分のデータを取得する場合
            symbol_data = my_share.get_historical(share.PERIOD_TYPE_YEAR,1,share.FREQUENCY_TYPE_WEEK,1)
        elif period == '2年':
            # 1週毎の2年分のデータを取得する場合
            symbol_data = my_share.get_historical(share.PERIOD_TYPE_YEAR,2,share.FREQUENCY_TYPE_WEEK,1)

        df = pd.DataFrame(symbol_data.values(), index=symbol_data.keys()).T
        df.timestamp = pd.to_datetime(df.timestamp, unit='ms')

        #df['company_code']  = company_code
        #df['company']       = brand
        # 日本標準時間に変換
        df.index = pd.DatetimeIndex(df.timestamp, name='timestamp').tz_localize('UTC').tz_convert('Asia/Tokyo')
        ax.plot(df.index, df.close,label='終値')

        if period in ['1カ月','6カ月']:
            # 移動平均線の計算
            ma_5d  = df['close'].rolling(window=5,  min_periods=1).mean()
            ma_25d = df['close'].rolling(window=25, min_periods=1).mean()
            ma_75d = df['close'].rolling(window=75, min_periods=1).mean()

            ax.plot(df.index, ma_5d,label ='移動平均5日')
            ax.plot(df.index, ma_25d,label='移動平均25日')
            ax.plot(df.index, ma_75d,label='移動平均75日')
        elif period in ['1年','2年']:
            # 移動平均線の計算
            ma_5d  = df['close'].rolling(window=5,  min_periods=1).mean()
            ma_25d = df['close'].rolling(window=13, min_periods=1).mean()
            ma_75d = df['close'].rolling(window=26, min_periods=1).mean()

            ax.plot(df.index, ma_5d,label ='移動平均5週')
            ax.plot(df.index, ma_25d,label='移動平均13週')
            ax.plot(df.index, ma_75d,label='移動平均26週')

        #ax.plot(df.index, df.close,label='終値')
        ax.grid(True)
        ax.set_ylabel("株価 [Yen]")

        #ax.legend(
        #        bbox_to_anchor=(1.05, 0.5, 0.5, .100), 
        #        borderaxespad=0.,
        #        ncol=1,
        #        mode="expand",
        #        title="ローソク足")
        ax.legend(loc='best')

        # x軸縦書き（90度回転）
        plt.suptitle(str(company_code) + " " + brand)
        plt.xticks(rotation=90)
        plt.rcParams['font.size'] = 18 # ラベルやタイトルなど全フォントのデフォルトサイズ
        plt.tight_layout() # ラベルレイアウトを調整する。文字がはみ出ないようにする。
        plt.show()

        st.pyplot(fig)

        fig.suptitle(f'{str(company_code)} {brand}')

        df.drop('timestamp',axis=1,inplace=True)

        csvname = today + rf"_download_{brand}({company_code}).csv"
        csv = convert_df(df)
        st.download_button(
            label='Download CSV', 
            data=csv,
            file_name=csvname,
            mime='text/csv',
            )

        chk = st.checkbox('時系列データを表示する')
        if chk:
            st.dataframe(df.style.highlight_max(axis=0))
    except YahooFinanceError as e:
        print(e.message)
        pass


def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('shift_jis')

data_dict = { 
                '日産自動車'          :  7201,
                'いすゞ自動車'        :  7202,
                'トヨタ自動車'        :  7203,
                '日野自動車'          :  7205,
                '三菱自動車工業'      :  7211,
                'マツダ'              :  7261,
                '本田技研工業'        :  7267,
                'スズキ'              :  7269,
                'SUBARU'             :  7270,
                'ヤマハ発動機'        :  7272,
                'デンソー'            :  6902
            }

res_dict = {_:False for _ in data_dict.keys()}

if __name__ == '__main__':
    main()

