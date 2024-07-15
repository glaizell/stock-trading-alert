import requests
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

STOCK = "TSLA"
COMPANY_NAME = "Tesla Inc"

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

STOCK_API_KEY = os.getenv("STOCK_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_TOKEN = os.getenv("TWILIO_TOKEN")


class StockAnalyzer:
    def __init__(self):
        self.symbol = STOCK
        self.api_key = STOCK_API_KEY
        self.endpoint = STOCK_ENDPOINT

    def get_stock_data(self):
        stock_params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": self.symbol,
            "apikey": self.api_key,
        }
        try:
            stock_response = requests.get(self.endpoint, params=stock_params)
            stock_response.raise_for_status()
            data = stock_response.json()
            return data
        except requests.RequestException as e:
            print(f"Failed to fetch stock data: {e}")
            return None


class NewsFetcher:
    def __init__(self):
        self.company_name = COMPANY_NAME
        self.api_key = NEWS_API_KEY
        self.endpoint = NEWS_ENDPOINT

    def fetch_news(self):
        params = {
            "apiKey": self.api_key,
            "q": self.company_name,
            "searchIn": "title,content,description",
            'language': 'en',
            'pageSize': '3',
            'sortBy': 'publishedAt',
        }
        try:
            response = requests.get(self.endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            return data["articles"]
        except requests.RequestException as e:
            print(f"Failed to fetch news: {e}")
            return []


class SMSMessenger:
    def __init__(self):
        self.sid = os.environ.get("TWILIO_SID")  # Fetching Twilio SID from environment variable
        self.token = os.environ.get("TWILIO_TOKEN")  # Fetching Twilio token from environment variable
        self.client = Client(self.sid, self.token)

    def send_message(self, body, to_number, from_number):
        try:
            message = self.client.messages.create(
                body=body,
                from_=from_number,
                to=to_number
            )
            print(f"Message sent successfully to {to_number}. Message SID: {message.sid}")
        except Exception as e:
            print(f"Failed to send message: {str(e)}")


if __name__ == "__main__":

    sender_number = os.getenv("SENDER_NUMBER")
    recipient_number = os.getenv("RECIPIENT_NUMBER")

    #==========================STOCK===================================#
    stock_analyzer = StockAnalyzer()
    stock_data = stock_analyzer.get_stock_data()

    time_series = stock_data["Time Series (Daily)"]
    if not time_series:
        print("Error: Unable to fetch stock data.")
        exit()

    dates = list(time_series.keys())
    yesterday = dates[0]
    day_before_yesterday = dates[1]

    yesterday_close = float(time_series[yesterday]["4. close"])
    day_before_yesterday_close = float(time_series[day_before_yesterday]["4. close"])

    print(f"Yesterday's Close: {yesterday_close}, Day Before Yesterday's Close: {day_before_yesterday_close}")

    increase = yesterday_close - day_before_yesterday_close

    percentage_change = round((increase / day_before_yesterday_close) * 100,
                              2) if day_before_yesterday_close != 0 else 0

    direction = "🔼" if increase > 0 else "🔽"

    #==========================NEWS===================================#
    news_fetcher = NewsFetcher()
    articles = news_fetcher.fetch_news()

    if abs(percentage_change) > 2:
        print("Get News")
        print(articles)
    else:
        print("No News")

    #==========================SMS===================================#
    sms_messenger = SMSMessenger()

    formatted_articles = [
        f"{COMPANY_NAME}: {direction} {percentage_change}% \nHeadline: {article['title']}. \nBrief: {article['description']} "
        for article in articles]

    for article in formatted_articles:
        sms_messenger.send_message(article, recipient_number, sender_number)
        print(article)
