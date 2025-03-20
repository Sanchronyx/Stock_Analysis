from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)

file_path = "scrape.csv"
df = pd.read_csv(file_path)
df_selected = df[['名稱', '代號', '平均配息率']].copy()
df_selected['代號'] = df_selected['代號'].astype(str).str.replace('="', '').str.replace('"', '')
df_selected = df_selected.sort_values(by='平均配息率', ascending=False)
df_selected.reset_index(drop=True, inplace=True)
stocks = df_selected.to_dict(orient='records')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get-stock-data')
def get_stock_data():
    return jsonify(stocks)

@app.route('/top12')
def top12():
    top_stocks = stocks[:12]  # Get the top 12 highest dividend payout stocks
    return render_template('top12.html', stocks=top_stocks)


stocks_per_page = 50

@app.route('/stock-list')
def stock_list():
    page = request.args.get('page', 1, type=int)
    total_stocks = len(df_selected)
    total_pages = (total_stocks + stocks_per_page - 1) // stocks_per_page  # Calculate total pages
    start = (page - 1) * stocks_per_page
    end = start + stocks_per_page
    paginated_stocks = df_selected.iloc[start:end].to_dict(orient='records')

    return render_template('stock_list.html', stocks=paginated_stocks, page=page, total_pages=total_pages, start=start)