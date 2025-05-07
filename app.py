from flask import Flask, render_template, request, jsonify, redirect
import pandas as pd
import openai
from openai import OpenAI
from dotenv import load_dotenv
import os
import csv
import chromadb
from chromadb.utils import embedding_functions
from prompts import prebuilt_prompts
from retriever import fetch_yahoo_data

app = Flask(__name__)

# OPENAI API KEY
load_dotenv()
print("LOADED API KEY:", os.getenv("OPENAI_API_KEY"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize ChromaDB and embedder
chroma_client = chromadb.Client()
chroma_embedder = embedding_functions.OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_API_KEY"))
chroma_collection = chroma_client.get_or_create_collection(
    name="company_info",
    embedding_function=chroma_embedder
)

# CALCULATIONS FROM 育成 FOR THE EPS & Profit Margins
columns_needed = [
    '名稱', '代號', '股價', '配息殖利率', '預估殖利率', '去年EPS殖利率',
    '預估EPS', '去年EPS', '今年配息', '去年配息', '五年均配息率', '股數（張）'
]
calc_df = pd.read_csv("calculations.csv")
calc_df['代號'] = calc_df['代號'].astype(str).str.replace('=\"', '').str.replace('"', '')
df_selected = calc_df[columns_needed].copy()

# NO INFORMATION QUERY
df_selected['配息殖利率'] = df_selected['配息殖利率'].fillna("No information available.")
df_selected['預估殖利率'] = df_selected['預估殖利率'].fillna("No information available.")
df_selected['去年EPS殖利率'] = df_selected['去年EPS殖利率'].fillna("No information available.")

# SORT FILES
df_selected = df_selected.sort_values(by='預估殖利率', ascending=False)
df_selected.reset_index(drop=True, inplace=True)
stocks = df_selected.to_dict(orient='records')

# CACHE FILE SETUP
stocks_per_page = 50
CACHE_FILE = "ai_stock_suggestions.csv"
if os.path.exists(CACHE_FILE):
    cache_df = pd.read_csv(CACHE_FILE)
    ai_cache = dict(zip(cache_df['代號'], cache_df['ai_response']))
else:
    ai_cache = {}

# HOME PAGE
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get-stock-data')
def get_stock_data():
    return jsonify(stocks)

# TOP 12 STOCKS PAGE
@app.route('/top12')
def top12():
    def safe_float(val):
        try:
            return float(str(val).replace('%', '').strip())
        except:
            return float('-inf')  # "No information" treated as lowest

    sorted_top = df_selected.copy()
    sorted_top['sort_key'] = sorted_top['預估殖利率'].apply(safe_float)
    sorted_top = sorted_top.sort_values(by='sort_key', ascending=False)
    top_stocks = sorted_top.head(12).to_dict(orient='records')
    return render_template('top12.html', stocks=top_stocks)

# STOCK LIST TABLE
@app.route('/stock-list')
def stock_list():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', '預估殖利率')
    order = request.args.get('order', 'desc')

    sorted_df = df_selected.copy()

    def safe_float(val):
        try:
            return float(str(val).replace('%', '').strip())
        except:
            return float('-inf')

    if sort_by in sorted_df.columns:
        sorted_df['sort_key'] = sorted_df[sort_by].apply(safe_float)
        sorted_df = sorted_df.sort_values('sort_key', ascending=(order == 'asc'))

    total_stocks = len(sorted_df)
    total_pages = (total_stocks + stocks_per_page - 1) // stocks_per_page
    start = (page - 1) * stocks_per_page
    end = start + stocks_per_page
    paginated_stocks = sorted_df.iloc[start:end].to_dict(orient='records')

    return render_template(
        'stock_list.html',
        stocks=paginated_stocks,
        page=page,
        total_pages=total_pages,
        start=start,
        sort_by=sort_by,
        order=order
    )

# INDIVIDUAL STOCK PAGE
@app.route('/stock/<stock_id>')
def stock_detail(stock_id):
    stock_info = next((stock for stock in stocks if stock['代號'] == stock_id), None)
    if not stock_info:
        return render_template("stock_detail.html", stock=None)

    if stock_id in ai_cache:
        ai_data = eval(ai_cache[stock_id]) if isinstance(ai_cache[stock_id], str) else ai_cache[stock_id]
    else:
        # Retrieve the most relevant description using vector similarity
        try:
            chroma_result = chroma_collection.query(
                query_texts=[f"{stock_info['名稱']} {stock_info['代號']}"],
                n_results=1
            )
            summary_info = chroma_result['documents'][0][0] if chroma_result['documents'] else "No description found."
        except Exception as e:
            summary_info = f"Error retrieving description: {e}"

        # Fetch Yahoo Finance data
        # Fetch Yahoo Finance data
        try:
            yahoo_data = fetch_yahoo_data(stock_id)
            price_history = yahoo_data.get("price_history", {"dates": [], "prices": []})
        except Exception as e:
            yahoo_data = {}
            price_history = {"dates": [], "prices": []}
            print(f"Yahoo data fetch failed for {stock_id}: {e}")
            
        price_history = yahoo_data.get("price_history", {"dates": [], "prices": []})
        
        # Generate prompts
        investment_prompt, pros_cons_prompt, description_prompt = prebuilt_prompts(stock_info, summary_info, yahoo_data)

        try:
            main = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": investment_prompt}]
            )
            ai_message = main.choices[0].message.content

            proscons = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": pros_cons_prompt}]
            )
            ai_proscons = proscons.choices[0].message.content

            overview = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": description_prompt}]
            )
            ai_summary = overview.choices[0].message.content

            ai_data = {
                "analysis": ai_message,
                "pros_cons": ai_proscons,
                "summary": ai_summary
            }
            ai_cache[stock_id] = ai_data

            with open(CACHE_FILE, "a", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                if os.stat(CACHE_FILE).st_size == 0:
                    writer.writerow(["代號", "ai_response"])
                writer.writerow([stock_id, ai_data])

        except Exception as e:
            ai_data = {"analysis": f"Error: {e}", "pros_cons": "N/A", "summary": "N/A"}

    return render_template(
        "stock_detail.html",
        stock=stock_info,
        ai_response=ai_data["analysis"],
        pros_cons=ai_data["pros_cons"],
        ai_summary=ai_data["summary"],
        price_history=yahoo_data.get("price_history", {"dates": [], "prices": []}) 
    )

# REGENERATE BUTTON
@app.route('/regenerate/<stock_id>', methods=['POST'])
def regenerate_stock(stock_id):
    if stock_id in ai_cache:
        del ai_cache[stock_id]

    if os.path.exists(CACHE_FILE):
        df = pd.read_csv(CACHE_FILE)
        df = df[df['代號'] != stock_id]
        df.to_csv(CACHE_FILE, index=False, encoding='utf-8')

    return redirect(f"/stock/{stock_id}")

# CALCULATOR PAGE
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

if __name__ == '__main__':
    app.run(debug=True)
