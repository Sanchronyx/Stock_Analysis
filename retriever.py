import yfinance as yf
import requests

def fetch_yahoo_data(stock_id):
    try:
        ticker = yf.Ticker(stock_id + ".TW") 
        info = ticker.info

        return {
            "currentPrice": info.get("currentPrice", "N/A"),
            "marketCap": info.get("marketCap", "N/A"),
            "forwardPE": info.get("forwardPE", "N/A"),
            "dividendYield": info.get("dividendYield", "N/A"),
            "sector": info.get("sector", "N/A"),
            "summary": info.get("longBusinessSummary", "N/A")
        }
    except Exception as e:
        return {"error": str(e)}
