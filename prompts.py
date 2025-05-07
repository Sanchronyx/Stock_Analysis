def prebuilt_prompts(stock_info, summary_info, yahoo_data):
    # Extract Yahoo Finance live data
    sector = yahoo_data.get("sector", "N/A")
    pe_ratio = yahoo_data.get("forwardPE", "N/A")
    dividend_yield = yahoo_data.get("dividendYield", "N/A")
    market_cap = yahoo_data.get("marketCap", "N/A")
    current_price = yahoo_data.get("currentPrice", stock_info.get("股價", "N/A"))
    live_summary = yahoo_data.get("summary", "N/A")

    # Extract additional fields from calculations.csv
    five_year_yield = stock_info.get("五年均配息率", "N/A")
    dividend_this_year = stock_info.get("今年配息", "N/A")
    dividend_last_year = stock_info.get("去年配息", "N/A")
    eps_this_year = stock_info.get("預估EPS", "N/A")
    eps_last_year = stock_info.get("去年EPS", "N/A")
    shares_outstanding = stock_info.get("股數（張）", "N/A")

    # Investment decision prompt
    investment_prompt = f"""
    以下是關於一間上市公司的資料：

    - 名稱：{stock_info['名稱']}（代號 {stock_info['代號']}）
    - 所屬產業：{sector}
    - 股價（Yahoo 即時）：{current_price}
    - 市值：{market_cap}
    - 本益比（P/E Ratio）：{pe_ratio}
    - 預估殖利率：{stock_info['預估殖利率']}，配息殖利率：{stock_info['配息殖利率']}，去年 EPS 殖利率：{stock_info['去年EPS殖利率']}
    - 預估 EPS：{eps_this_year}，去年 EPS：{eps_last_year}
    - 今年配息：{dividend_this_year}，去年配息：{dividend_last_year}，五年均配息率：{five_year_yield}
    - 發行股數（張）：{shares_outstanding}
    - 配息率（即時）：{dividend_yield}

    根據以上資訊，你認為這家公司是否值得投資？
    請明確以一句話回答：
    "這家公司值得投資" 或 "這家公司不值得投資"，並簡要說明理由。
    回答請使用繁體中文。
    """

    # Pros and Cons prompt
    pros_cons_prompt = f"""
    請根據以下股票資訊分析其投資優勢與風險，務必遵守以下格式輸出，否則將無法正確解析：

    股票資訊：
    - 名稱：{stock_info['名稱']}（代號 {stock_info['代號']}）
    - 股價：{current_price}
    - 預估殖利率：{stock_info['預估殖利率']}
    - 配息殖利率：{stock_info['配息殖利率']}
    - 去年 EPS：{stock_info.get('去年EPS', 'N/A')}
    - P/E 本益比：{pe_ratio}
    - 市值：{market_cap}
    - 所屬產業：{sector}

    請使用下列格式完整輸出，使用繁體中文：

    Strengths:
    - 優勢一...
    - 優勢二...
    - 優勢三...

    Risks:
    - 風險一...
    - 風險二...
    - 風險三...
    """

    # Company overview generation
    description_prompt = f"""
    請針對以下公司撰寫一段完整的公司概覽，包括其所屬產業、商業模式、公司規模、市場定位、股東報酬政策與未來潛力：

    - 名稱：{stock_info['名稱']}（代號 {stock_info['代號']}）
    - 所屬產業：{sector}
    - 公司簡介（資料庫）：{summary_info}
    - 公司描述（Yahoo）：{live_summary}

    請勿使用項目符號，請用完整段落敘述，並使用繁體中文。
    """

    return investment_prompt.strip(), pros_cons_prompt.strip(), description_prompt.strip()
