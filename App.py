import streamlit as st
import yfinance as tf
import pandas as pd

# Настройка на заглавието на страницата
st.set_page_config(page_title="AI Investment Tracker", page_icon="💰", layout="centered")

st.title("💰 AI Инвестиционен Портфолио Тракер")
st.write("Следете всичките си активи на едно място в реално време.")

# Инициализиране на сесия за съхранение на активите (в паметта)
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# Форма за добавяне на нов актив
st.sidebar.header("➕ Добави нов актив")
asset_type = st.sidebar.selectbox("Тип актив", ["Акция / ETF", "Физическо Злато (грамове)", "Кеш / Депозит"])

if asset_type == "Акция / ETF":
    ticker = st.sidebar.text_input("Тикер (напр. AAPL, TSLA, VUAA.DE)", value="AAPL").upper()
    quantity = st.sidebar.number_input("Количество (брой акции)", min_value=0.0, value=1.0, step=0.1)
    if st.sidebar.button("Добави Акция"):
        st.session_state.portfolio.append({"type": "Stock", "symbol": ticker, "qty": quantity})
        st.success(f"Добавено: {quantity} бр. от {ticker}")

elif asset_type == "Физическо Злато (грамове)":
    gold_qty = st.sidebar.number_input("Тегло в грамове", min_value=0.0, value=10.0, step=1.0)
    if st.sidebar.button("Добави Злато"):
        st.session_state.portfolio.append({"type": "Gold", "symbol": "GOLD", "qty": gold_qty})
        st.success(f"Добавено: {gold_qty} грама Злато")

elif asset_type == "Кеш / Депозит":
    cash_amount = st.sidebar.number_input("Сума (в USD)", min_value=0.0, value=1000.0, step=100.0)
    if st.sidebar.button("Добави Кеш"):
        st.session_state.portfolio.append({"type": "Cash", "symbol": "USD", "qty": cash_amount})
        st.success(f"Добавено: ${cash_amount} Кеш")

# Функция за извличане на цени в реално време
def get_live_prices():
    total_value = 0.0
    report_data = []
    
    # Вземане на текущата цена на златото за грам (чрез ETF-а GLD като референция / 31.1035 за грам)
    try:
        gold_ticker = tf.Ticker("GLD")
        gold_price_oz = gold_ticker.history(period="1d")['Close'].iloc[-1]
        price_per_gram_gold = (gold_price_oz / 31.1035) * 10 # Приблизителна оценка за физическо кюлче
    except:
        price_per_gram_gold = 75.0 # Резервна цена в USD при срив на API

    for asset in st.session_state.portfolio:
        if asset["type"] == "Stock":
            try:
                stock = tf.Ticker(asset["symbol"])
                price = stock.history(period="1d")['Close'].iloc[-1]
            except:
                price = 0.0
            current_value = price * asset["qty"]
            total_value += current_value
            report_data.append([asset["symbol"], asset["qty"], f"${price:.2f}", f"${current_value:.2f}"])
            
        elif asset["type"] == "Gold":
            current_value = price_per_gram_gold * asset["qty"]
            total_value += current_value
            report_data.append(["Физическо Злато", f"{asset['qty']} гр.", f"${price_per_gram_gold:.2f}/гр", f"${current_value:.2f}"])
            
        elif asset["type"] == "Cash":
            total_value += asset["qty"]
            report_data.append(["Кеш / Депозит", "-", "-", f"${asset['qty']:.2f}"])
            
    return total_value, report_data

# Показване на портфолиото
if st.session_state.portfolio:
    total_val, grid_data = get_live_prices()
    
    # Голямо табло с общата сума
    st.metric(label="Обща стойност на портфолиото (USD)", value=f"${total_val:,.2f}")
    
    # Таблица с активите
    df = pd.DataFrame(grid_data, columns=["Актив", "Количество", "Текуща цена", "Обща стойност"])
    st.dataframe(df, use_container_width=True)
    
    # Бутон за изчистване
    if st.button("Изчисти портфолиото"):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.info("Портфолиото ви е празно. Използвайте менюто вляво, за да въведете активи.")

# Демонстрация на платената ИИ функция (Premium сектор)
st.markdown("---")
st.header("🧠 AI Premium Функции (€2.99)")
if st.button("🔍 Стартирай AI Анализ на активите"):
    st.info("Изпращане на данни към AI модела... (Демонстрационен режим)")
    st.success("🤖 **ИИ Препоръка:** Портфолиото ви е добре балансирано. Внимавайте с теглото на технологичните акции. Златото ви служи като чудесен хедж срещу инфлацията.")
