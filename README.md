# 🤖 AI-Powered Sales Dashboard Assistant

An interactive NLP-driven dashboard that turns natural language queries like  
> *"Show top 5 products by revenue"*  
into real-time data insights using the **DeepSeek API**, **Streamlit**, and **Pandas**.

---

## 🚀 Features

- 🧠 Translates natural language questions into SQL-like logic via DeepSeek's open LLM API
- 📊 Displays dynamic data insights from sales CSVs
- 🔁 Handles follow-up queries with conversational context (planned)
- 📦 Processes 10K+ records efficiently using **Pandas**
- 🌐 No-cost deployment via **Streamlit Cloud** (100+ test queries/month)

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Pandas
- **Frontend**: Streamlit
- **NLP/AI API**: [DeepSeek LLM API](https://platform.deepseek.com/)
- **Data**: Sample sales data from Kaggle (10,000+ records)

---

## 📂 Project Structure (Planned)

ai-sales-assistant/
├── app.py # Streamlit app main file
├── data/
│ └── sales_data.csv # Mock dataset
├── utils/
│ └── query_handler.py # DeepSeek API + NL logic
├── .env # API keys
├── requirements.txt                                    
└── README.md

Author:- Shashwat Raj
