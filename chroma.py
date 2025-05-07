import chromadb
from chromadb.utils import embedding_functions
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
client = chromadb.Client()
embedder = embedding_functions.OpenAIEmbeddingFunction(api_key=os.getenv("OPENAI_API_KEY"))
collection = client.get_or_create_collection(name="calculations.csv", embedding_function=embedder)

df = pd.read_csv("calculations.csv")
df['代號'] = df['代號'].astype(str)
df = df[['代號', '名稱']].dropna()

for _, row in df.iterrows():
    doc = f"""
    公司名稱：{row['名稱']}（代號 {row['代號']}）
    五年平均配息率：{row['五年均配息率']}
    去年EPS：{row['去年EPS']}，今年預估EPS：{row['預估EPS']}
    去年配息：{row['去年配息']}，今年預估配息：{row['今年配息']}
    股數（張）：{row['股數（張）']}
    本文為系統分析結果，僅供參考。
    """
    collection.add(
        documents=[doc],
        metadatas=[{"代號": row['代號'], "名稱": row['名稱']}],
        ids=[row['代號']]
    )

print("ChromaDB collection populated.")
