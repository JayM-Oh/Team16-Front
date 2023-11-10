import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

import streamlit as st
import requests


class Stock():
    def __init__(self, corporation, ticker_symbol) -> None:
        self.corporation = corporation
        st.title(f'{self.corporation} 주식 그래프')
        self.ticker_symbol = ticker_symbol
        self.data = yf.download(self.ticker_symbol, period="max")
        self.time_range = st.selectbox("시간 범위 선택:", 
                                       ('일봉', '주봉', '월봉', '일주일', '3개월', '6개월', '1년', '3년'))
        today = datetime.now()
        if self.time_range == '일봉':
            start_date = today
        if self.time_range == '일주일' or self.time_range == '주봉':
            start_date = today - timedelta(days=7)
        if self.time_range == '월봉':
            start_date = today - timedelta(days=30)
        if self.time_range == '3개월':
            start_date = today - timedelta(days=90)
        if self.time_range == '6개월':
            start_date = today - timedelta(days=180)
        if self.time_range == '1년':
            start_date = today - timedelta(days=365)
        if self.time_range == '3년':
            start_date = today - timedelta(days=365*3)

        self.data_period = self.data[start_date:]

    def draw(self):
        # 차트 생성
        if self.time_range in ['일주일', '3개월', '6개월', '1년', '3년']:
            fig = px.area(self.data_period, x=self.data_period.index, y='Close')
        else:  # 다른 시간 범위는 캔들스틱 차트로 표시
            fig = go.Figure(data=[go.Candlestick(x=self.data_period.index,
                                                 open=self.data_period['Open'],
                                                 high=self.data_period['High'],
                                                 low=self.data_period['Low'],
                                                 close=self.data_period['Close'])])

        # 차트 업데이트 (레이아웃, 축 이름 등)
        fig.update_layout(title=f'{self.corporation}({self.ticker_symbol}) 주식 차트 ({self.time_range})',
                          xaxis_title='날짜',
                          yaxis_title='가격')

        st.plotly_chart(fig)

def get_market_cap_change():
    url = "https://finance.naver.com/sise/sise_market_sum.nhn"

    # 네이버 금융 시가총액 페이지에 접속
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # 시가총액 정보가 담긴 테이블을 찾음
    market_cap_table = soup.find('table', {'class': 'type_2'})

    # 테이블 데이터를 DataFrame으로 변환
    df = pd.read_html(str(market_cap_table), header=0)[0]

    # 필요한 정보만 선택
    selected_columns = ['종목명', '등락률', '전일비', '현재가', '시가총액']
    df = df[selected_columns]

    return df

# 네이버 금융 시가총액 정보 가져오기
market_cap_data = get_market_cap_change()

# 상위 10개만 선택
selected_data = pd.concat([market_cap_data.iloc[1:6], market_cap_data.iloc[9:14]])

# 등락률이 음수일 때 전일비에 '-' 부호 추가
selected_data['전일비'] = selected_data.apply(lambda row: f"+{int(row['전일비'])}" if float(row['등락률'].replace('%', '')) >= 0 
else f"-{int(row['전일비'])}", axis=1)  

# '종목명' 열을 인덱스로 설정
selected_data_styled = selected_data.set_index('종목명')

def get_rss_feed(feed_url, num_items=3):
    feed = feedparser.parse(feed_url)
    return feed.entries[:num_items]

def get_thumbnail_from_webpage(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_tags = soup.find_all('meta', {'property': 'og:image'})

        if meta_tags:
            thumbnail_url = meta_tags[0]['content']
            return thumbnail_url
        else:
            return None
    except Exception as e:
        print(f"Error fetching thumbnail from webpage: {e}")
        return None

# 사용자 입력 받기
rss_feed_url = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtdHZHZ0pMVWlnQVAB?hl=ko&gl=KR&ceid=KR%3Ako"
key = st.text_input("종목명을 입력하세요")

st.markdown("Komin.ai, dashboard modify")


if key:
    st.markdown(requests.get("http://ec2-3-39-46-151.ap-northeast-2.compute.amazonaws.com/analyze/analyze/industrial/?query={0}".format(key)).content.decode('utf-8'))
    st.markdown(requests.get("http://ec2-3-39-46-151.ap-northeast-2.compute.amazonaws.com/analyze/analyze/finance/?query={0}".format(key)).content.decode('utf-8'))
    st.markdown(requests.get("http://ec2-3-39-46-151.ap-northeast-2.compute.amazonaws.com/analyze/analyze/news/").content.decode('utf-8'))
    num_items=3
    # RSS 피드 가져오기
    feed_entries = get_rss_feed(rss_feed_url, num_items)
    if feed_entries:
        corDB:dict = {'한미반도체': '042700.KS','삼성전자':'005930.KS', 'Apple': 'AAPL', 'Alphbet':'GOOG', '에코프로':'086520.KQ', '포스코홀딩스':'005490.KS'}
        
        stock = Stock(key, corDB[key])
        stock.draw() 
    # 각 뉴스에 대해 출력
        st.title("최신뉴스 정리")
        for index, entry in enumerate(feed_entries, start=1):
            # 웹페이지 메타데이터에서 이미지 URL 추출
            thumbnail_url = get_thumbnail_from_webpage(entry['link'])
            if thumbnail_url:
                st.image(thumbnail_url, width=200, use_column_width=None)
            else:
                st.warning("No thumbnail available.")
                st.markdown("---")
            st.write(f"[URL]({entry['link']})")
            st.write(f"{entry['title']}")
            
            
        st.title("시가총액 증감")
        # 출력
        st.dataframe(selected_data_styled)
                
    st.markdown("---")
