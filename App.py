import streamlit as st
import yfinance as tf
import pandas as pd
import plotly.express as px

# Настройка на страницата
st.set_page_config(page_title="AI Investment Tracker", page_icon="💰", layout="wide")

st.title("💰 AI Инвестиционен Портфолио Тракер")
st.write("Следете активите си на нива и категории в реално време.")

# Инициализиране на портфолиото
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# Меню за въвеждане вляво
st.sidebar.header("➕ Добави нов актив")
asset_type = st.sidebar.selectbox("Тип актив", ["Международна Акция / ETF", "БФБ (Българска Акция)", "Благородни Метали", "Кеш / Депозит"])

if asset_type == "Международна Акция / ETF":
    ticker = st.sidebar.text_input("Тикер (напр. AAPL, TSLA, 3CP.F)", value="AAPL").upper()
    quantity = st.sidebar.number_input("Количество (брой)", min_value=0.0, value=1.0, step=1.0)
    if st.sidebar.button("Добави Акция"):
        st.session_state.portfolio.append({"type": "Акции", "name": ticker, "qty": quantity, "is_bg": False})
        st.success(f"Добавено: {quantity} бр. от {ticker}")

elif asset_type == "БФБ (Българска Акция)":
    bg_name = st.sidebar.text_input("Име/Код на компанията (напр. SFA, SGH)", value="SHELLY")
    quantity = st.sidebar.number_input("Брой акции", min_value=0.0, value=10.0, step=1.0)
    manual_price = st.sidebar.number_input("Текуща цена на акция (в лв.)", min_value=0.0, value=50.0, step=0.1)
    if st.sidebar.button("Добави БФБ Акция"):
        st.session_state.portfolio.append({"type": "Акции", "name": f"{bg_name} (БФБ)", "qty": quantity, "is_bg": True, "price": manual_price / 1.80}) # Конвертиране в USD за баланс
        st.success(f"Добавено: {quantity} бр. от {bg_name}")

elif asset_type == "Благородни Метали":
    metal_type = st.sidebar.selectbox("Метал", ["Злато", "Сребро"])
    metal_qty = st.sidebar.number_input("Тегло в грамове", min_value=0.0, value=10.0, step=1.0)
    if st.sidebar.button("Добави Метал"):
        st.session_state.portfolio.append({"type": "Метали", "name": metal_type, "qty": metal_qty})
        st.success(f"Добавено: {metal_qty} гр. {metal_type}")

elif asset_type == "Кеш / Депозит":
    cash_name = st.sidebar.text_input("Банка / Валута (напр. ОББ, Револют)", value="Кеш USD")
    cash_amount = st.sidebar.number_input("Сума (в USD)", min_value=0.0, value=1000.0, step=100.0)
    if st.sidebar.button("Добави Кеш"):
        st.session_state.portfolio.append({"type": "Кеш", "name": cash_name, "qty": cash_amount})
        st.success(f"Добавено: ${cash_amount} към {cash_name}")

# Извличане на цени
def process_portfolio():
    try:
        gold_oz = tf.Ticker("GLD").history(period="1d")['Close'].iloc[-1]
        silver_oz = tf.Ticker("SLV").history(period="1d")['Close'].iloc[-1]
        gold_gram = (gold_oz / 31.1035) * 10
        silver_gram = (silver_oz / 31.1035) * 10
    except:
        gold_gram, silver_gram = 75.0, 1.0

    processed = []
    total_usd = 0.0

    for asset in st.session_state.portfolio:
        price = 0.0
        if asset["type"] == "Акции":
            if asset.get("is_bg"):
                price = asset["price"]
            else:
                try:
                    hist = tf.Ticker(asset["name"]).history(period="1d")
                    price = hist['Close'].iloc[-1] if not hist.empty else 0.0
                except:
                    price = 0.0
        elif asset["type"] == "Метали":
            price = gold_gram if asset["name"] == "Злато" else silver_gram
        elif asset["type"] == "Кеш":
            price = 1.0

        val = price * asset["qty"]
        total_usd += val
        processed.append({
            "Категория": asset["type"],
            "Актив": asset["name"],
            "Количество": asset["qty"],
            "Стойност (USD)": round(val, 2)
        })
    return total_usd, pd.DataFrame(processed)

# Показване на интерфейса
if st.session_state.portfolio:
    total_portfolio_value, df_portfolio = process_portfolio()
    
    st.metric(label="📊 Обща стойност на портфолиото", value=f"${total_portfolio_value:,.2f}")
    
    # Секция 1: Главна диаграма
    st.subheader("🍕 Общо разпределение на активите")
    df_main_pie = df_portfolio.groupby("Категория")["Стойност (USD)"].sum().reset_index()
    
    fig_main = px.pie(df_main_pie, values="Стойност (USD)", names="Категория", hole=0.4, title="Портфолио по класове активи")
    st.plotly_chart(fig_main, use_container_width=True)
    
    # Секция 2: Влизане в детайли по категории
    st.markdown("---")
    st.subheader("🔍 Детайлен преглед на категориите (Кликни, за да отвориш)")
    
    available_categories = df_portfolio["Категория"].unique()
    
    # Създаване на табове за всяка съществуваща категория
    tabs = st.tabs(list(available_categories))
    
    for index, cat_name in enumerate(available_categories):
        with tabs[index]:
            st.write(f"### Вътрешно разпределение за клас: **{cat_name}**")
            df_sub = df_portfolio[df_portfolio["Категория"] == cat_name]
            
            # Диаграма за конкретната категория
            fig_sub = px.pie(df_sub, values="Стойност (USD)", names="Актив", hole=0.3, title=f"Активи в сектор {cat_name}")
            st.plotly_chart(fig_sub, use_container_width=True)
            
            # Списък/Таблица с активите в тази категория
            st.dataframe(df_sub[["Актив", "Количество", "Стойност (USD)"]], use_container_width=True)

    if st.button("❌ Изчисти цялото портфолио"):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.info("Портфолиото ви е празно. Добавете активи от страничното меню.")


