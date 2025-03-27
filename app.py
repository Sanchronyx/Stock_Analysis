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
company_info_df = pd.read_csv("company_info.csv")
df_selected['代號'] = df_selected['代號'].astype(str)
company_info_df['代號'] = company_info_df['代號'].astype(str)
company_info_df = company_info_df.drop(columns=['名稱'])
df_selected = pd.merge(df_selected, company_info_df, on='代號', how='left')
df_selected['公司簡介'] = df_selected['公司簡介'].replace(['nan', 'NaN'], None)
df_selected['公司簡介'] = df_selected['公司簡介'].fillna("No description available.")
stocks = df_selected.to_dict(orient='records')


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get-stock-data')
def get_stock_data():
    return jsonify(stocks)

@app.route('/top12')
def top12():
    top_stocks = stocks[:12] 
    return render_template('top12.html', stocks=top_stocks)


stocks_per_page = 50

@app.route('/stock-list')
def stock_list():
    page = request.args.get('page', 1, type=int)
    total_stocks = len(df_selected)
    total_pages = (total_stocks + stocks_per_page - 1) // stocks_per_page 
    start = (page - 1) * stocks_per_page
    end = start + stocks_per_page
    paginated_stocks = df_selected.iloc[start:end].to_dict(orient='records')

    return render_template('stock_list.html', stocks=paginated_stocks, page=page, total_pages=total_pages, start=start)

@app.route('/stock/<stock_id>')
def stock_detail(stock_id):
    stock_info = next((stock for stock in stocks if stock["代號"] == stock_id), None)
    return render_template('stock_detail.html', stock=stock_info)

@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    result = None
    if request.method == 'POST':
        try:
            stock_price = float(request.form['stock_price'])
            shares = int(request.form['shares'])
            yield_percent = float(request.form['yield'])

            dividend_per_share = stock_price * (yield_percent / 100)
            total_dividend = dividend_per_share * shares

            result = {
                "dividend_per_share": round(dividend_per_share, 2),
                "total_dividend": round(total_dividend, 2)
            }
        except:
            result = "Invalid input. Please enter valid numbers."

    return render_template('calculator.html', result=result)