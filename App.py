import streamlit as st
import yfinance as tf
import pandas as pd
import plotly.express as px

# Настройка на страницата
st.set_page_config(page_title="AI Investment Tracker", page_icon="💰", layout="wide")

st.title("💰 AI Инвестиционен Портфолио Тракер")
st.write("Следете и управлявайте активите си на нива и категории в реално време.")

# Инициализиране на портфолиото
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# МЕНЮ ЗА НАСТРОЙКА НА ВАЛУТА
st.sidebar.header("⚙️ Валута на Портфолиото")
currency = st.sidebar.radio("Изберете основна валута:", ["EUR (€)", "USD ($)"])
currency_symbol = "€" if "EUR" in currency else "$"

# Бутон за вземане на курса USD/EUR в реално време
@st.cache_data(ttl=3600)
def get_eur_usd_rate():
    try:
        rate = tf.Ticker("EURUSD=X").history(period="1d")['Close'].iloc[-1]
        return rate
    except:
        return 1.08

eur_to_usd = get_eur_usd_rate()
usd_to_eur = 1.0 / eur_to_usd

# МЕНЮ ЗА ВЪВЕЖДАНЕ НА АКТИВИ
st.sidebar.header("➕ Добави нов актив")
asset_type = st.sidebar.selectbox("Тип актив", ["Международна Акция / ETF", "БФБ (Българска Акция в EUR)", "Благородни Метали (Унции)", "Кеш / Депозит"])

if asset_type == "Международна Акция / ETF":
    ticker = st.sidebar.text_input("Тикер (напр. AAPL, TSLA, 3CP.F)", value="AAPL").upper()
    quantity = st.sidebar.number_input("Количество (брой)", min_value=0.0, value=1.0, step=1.0, key="add_int_qty")
    if st.sidebar.button("Добави Акция"):
        st.session_state.portfolio.append({"type": "Акции", "name": ticker, "qty": quantity, "is_bg": False, "input_currency": "USD"})
        st.success(f"Добавено: {quantity} бр. от {ticker}")
        st.rerun()

elif asset_type == "БФБ (Българска Акция в EUR)":
    bg_name = st.sidebar.text_input("Име/Код на компанията (напр. SHELLY, SFA)", value="SHELLY").upper()
    quantity = st.sidebar.number_input("Брой акции", min_value=0.0, value=10.0, step=1.0, key="add_bg_qty")
    manual_price = st.sidebar.number_input("Текуща цена на акция (в EUR)", min_value=0.0, value=25.0, step=0.1)
    if st.sidebar.button("Добави БФБ Акция"):
        st.session_state.portfolio.append({"type": "Акции", "name": f"{bg_name} (БФБ)", "qty": quantity, "is_bg": True, "price_eur": manual_price, "input_currency": "EUR"})
        st.success(f"Добавено: {quantity} бр. от {bg_name}")
        st.rerun()

elif asset_type == "Благородни Метали (Унции)":
    metal_type = st.sidebar.selectbox("Метал", ["Злато", "Сребро"])
    metal_qty = st.sidebar.number_input("Тегло в Тройунции (oz)", min_value=0.0, value=1.0, step=0.1, key="add_metal_qty")
    if st.sidebar.button("Добави Метал"):
        st.session_state.portfolio.append({"type": "Метали", "name": metal_type, "qty": metal_qty, "input_currency": "USD"})
        st.success(f"Добавено: {metal_qty} oz {metal_type}")
        st.rerun()

elif asset_type == "Кеш / Депозит":
    cash_currency = st.sidebar.selectbox("Валута на кеша", ["EUR", "USD"])
    cash_name = st.sidebar.text_input("Банка / Описание", value="Револют")
    cash_amount = st.sidebar.number_input(f"Сума (в {cash_currency})", min_value=0.0, value=1000.0, step=100.0, key="add_cash_qty")
    if st.sidebar.button("Добави Кеш"):
        st.session_state.portfolio.append({"type": "Кеш", "name": f"{cash_name} ({cash_currency})", "qty": cash_amount, "input_currency": cash_currency})
        st.success(f"Добавено: {cash_amount} {cash_currency} към {cash_name}")
        st.rerun()

# ИЗЧИСЛЯВАНЕ НА ЦЕНИТЕ В РЕАЛНО ВРЕМЕ
def process_portfolio(target_currency):
    try:
        gold_price_per_oz_usd = tf.Ticker("GLD").history(period="1d")['Close'].iloc[-1] * 10
        silver_price_per_oz_usd = tf.Ticker("SLV").history(period="1d")['Close'].iloc[-1] * 5
    except:
        gold_price_per_oz_usd, silver_price_per_oz_usd = 2300.0, 28.0

    processed = []
    total_display_value = 0.0

    for idx, asset in enumerate(st.session_state.portfolio):
        price_in_original_currency = 0.0
        asset_currency = asset["input_currency"]

        if asset["type"] == "Акции":
            if asset.get("is_bg"):
                price_in_original_currency = asset["price_eur"]
            else:
                try:
                    hist = tf.Ticker(asset["name"]).history(period="1d")
                    price_in_original_currency = hist['Close'].iloc[-1] if not hist.empty else 0.0
                except:
                    price_in_original_currency = 0.0
        elif asset["type"] == "Метали":
            price_in_original_currency = gold_price_per_oz_usd if asset["name"] == "Злато" else silver_price_per_oz_usd
        elif asset["type"] == "Кеш":
            price_in_original_currency = 1.0

        val_original = price_in_original_currency * asset["qty"]

        if target_currency == "USD ($)":
            if asset_currency == "EUR":
                val_final = val_original * eur_to_usd
                price_final = price_in_original_currency * eur_to_usd
            else:
                val_final = val_original
                price_final = price_in_original_currency
        else:
            if asset_currency == "USD":
                val_final = val_original * usd_to_eur
                price_final = price_in_original_currency * usd_to_eur
            else:
                val_final = val_original
                price_final = price_in_original_currency

        total_display_value += val_final
        processed.append({
            "id": idx,
            "Категория": asset["type"],
            "Актив": asset["name"],
            "Количество": asset["qty"],
            f"Стойност ({currency_symbol})": round(val_final, 2),
            "Ед. Цена": round(price_final, 2)
        })
        
    return total_display_value, pd.DataFrame(processed)

# ЕКРАН НА ПРИЛОЖЕНИЕТО
if st.session_state.portfolio:
    total_val, df_portfolio = process_portfolio(currency)
    
    st.metric(label=f"📊 Обща стойност на портфолиото ({currency_symbol})", value=f"{currency_symbol}{total_val:,.2f}")
    st.caption(f"Текущ обменен курс: 1 EUR = {eur_to_usd:.4f} USD")
    
    # Главна диаграма
    st.subheader("🍕 Общо разпределение на активите")
    val_column = f"Стойност ({currency_symbol})"
    df_main_pie = df_portfolio.groupby("Категория")[val_column].sum().reset_index()
    
    fig_main = px.pie(df_main_pie, values=val_column, names="Категория", hole=0.4, title="Портфолио по класове активи")
    st.plotly_chart(fig_main, use_container_width=True)
    
    # Детайлен преглед с табове
    st.markdown("---")
    st.subheader("🔍 Детайлен преглед на категориите")
    
    available_categories = df_portfolio["Категория"].unique()
    tabs = st.tabs(list(available_categories))
    
    for index, cat_name in enumerate(available_categories):
        with tabs[index]:
            st.write(f"### Вътрешно разпределение за клас: **{cat_name}**")
            df_sub = df_portfolio[df_portfolio["Категория"] == cat_name]
            
            fig_sub = px.pie(df_sub, values=val_column, names="Актив", hole=0.3, title=f"Активи в сектор {cat_name}")
            st.plotly_chart(fig_sub, use_container_width=True)
            st.dataframe(df_sub[["Актив", "Количество", "Ед. Цена", val_column]], use_container_width=True)

    # НОВА СЕКЦИЯ: РЕДАКТИРАНЕ И ТРИЕНЕ НА ИНДИВИДУАЛНИ ПОЗИЦИИ
    st.markdown("---")
    st.subheader("🛠️ Управление и редакция на активите")
    st.write("Променете количеството или изтрийте отделна позиция без рестартиране:")

    for idx, item in enumerate(st.session_state.portfolio):
        # Създаваме ред с бутони за всеки актив
        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
        with col1:
            st.write(f"**{item['name']}** ({item['type']})")
        with col2:
            # Поле за директна промяна на бройката
            new_qty = st.number_input(f"Количество", min_value=0.0, value=float(item['qty']), step=0.1, key=f"edit_qty_{idx}")
            if new_qty != item['qty']:
                st.session_state.portfolio[idx]['qty'] = new_qty
                st.rerun()
        with col3:
            st.write(f"Текущо: {item['qty']}")
        with col4:
            # Бутон за изтриване само на този ред
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()

    if st.button("❌ Изчисти цялото портфолио"):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.info("Портфолиото ви е празно. Добавете активи от страничното меню.")




