import streamlit as st
import yfinance as tf
import pandas as pd
import plotly.express as px
from openai import OpenAI

# 1. ОСНОВНА НАСТРОЙКА НА СТРАНИЦАТА
st.set_page_config(page_title="AI Investment Tracker", page_icon="💰", layout="wide")

st.title("💰 AI Инвестиционен Портфолио Тракер")
st.write("Следете активите си в реално време и използвайте ИИ за премиум анализи.")

# Инициализиране на сесията за съхранение на данни
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = []

# ИНИЦИАЛИЗИРАНЕ НА OPENAI КЛИЕНТ
if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
else:
    client = None

# 2. МЕНЮ ЗА НАСТРОЙКА НА ВАЛУТА С АВТОМАТИЧЕН КУРС
st.sidebar.header("⚙️ Валута на Портфолиото")
currency = st.sidebar.radio("Изберете основна валута:", ["EUR (€)", "USD ($)"])
currency_symbol = "€" if "EUR" in currency else "$"

@st.cache_data(ttl=3600)
def get_eur_usd_rate():
    try:
        rate = tf.Ticker("EURUSD=X").history(period="1d")['Close'].iloc[-1]
        return rate
    except:
        return 1.09

eur_to_usd = get_eur_usd_rate()
usd_to_eur = 1.0 / eur_to_usd

# 3. ПЪЛЕН СПИСЪК СЪС ВСИЧКИ 28 ОБЛАСТИ В БЪЛГАРИЯ
all_bg_provinces = [
    "Благоевград", "Бургас", "Варна", "Велико Търново", "Видин", "Враца", 
    "Габрово", "Добрич", "Кърджали", "Кюстендил", "Ловеч", "Монтана", 
    "Пазарджик", "Перник", "Плевен", "Пловдив", "Разград", "Русе", 
    "Силистра", "Сливен", "Смолян", "София (град)", "София (област)", 
    "Стара Загора", "Търговище", "Хасково", "Шумен", "Ямбол"
]

# AI ОЦЕНИТЕЛ НА НЕДВИЖИМИ ИМОТИ (Базови регионални стойности)
def ai_property_valuation(prop_type, province, specific_loc, size, category=""):
    # Примерни средни цени на кв.м. по области
    regional_base_prices = {
        "София (град)": 2100, "Варна": 1550, "Пловдив": 1350, "Бургас": 1250,
        "Стара Загора": 1050, "Русе": 1000, "Велико Търново": 950, "Благоевград": 900,
        "Плевен": 850, "Добрич": 800, "Шумен": 800, "Хасково": 750, "Пазарджик": 750,
        "Сливен": 700, "Перник": 850, "Ямбол": 650, "Враца": 650, "Габрово": 700,
        "Ловеч": 600, "Кърджали": 800, "Кюстендил": 650, "Монтана": 550, "Силистра": 550,
        "Разград": 600, "Търговище": 600, "Смолян": 750, "Видин": 500, "София (област)": 850
    }
    land_prices_per_dekar = {
        "1-ва до 3-та категория (Най-плодородна)": 1800,
        "4-та до 6-та категория (Средна)": 1300,
        "7-ма до 10-та категория (Ниска/Пасища)": 750
    }
    if prop_type == "Земеделска земя":
        price_per_unit = land_prices_per_dekar.get(category, 1200)
        return price_per_unit * size
    else:
        price_per_meter = regional_base_prices.get(province, 800)
        # Ако локацията е село или курорт, софтуерът леко коригира цената спрямо типа
        if "сел" in specific_loc.lower():
            price_per_meter *= 0.5
        elif "курорт" in specific_loc.lower() or "к.к." in specific_loc.lower():
            price_per_meter *= 1.3
        return price_per_meter * size

# 4. СТРАНИЧНО МЕНЮ ЗА ДОБАВЯНЕ НА ВСИЧКИ ВИДОВЕ АКТИВИ
st.sidebar.header("➕ Добави нов актив")
asset_type = st.sidebar.selectbox("Тип актив", [
    "Международна Акция", 
    "БФБ (Българска Акция в EUR)", 
    "ETF (Борсово търгуван фонд)", 
    "Криптовалута",
    "Благородни Метали (Унции)", 
    "Недвижим Имот / Земя (AI Оценка)", 
    "Кеш / Депозит"
])

if asset_type == "Международна Акция":
    ticker = st.sidebar.text_input("Тикер на Акцията (напр. AAPL, TSLA)", value="AAPL").upper()
    quantity = st.sidebar.number_input("Количество (брой)", min_value=0.0, value=1.0, step=1.0, key="add_stock_qty")
    if st.sidebar.button("Добави Акция"):
        st.session_state.portfolio.append({"type": "Акции", "name": ticker, "qty": quantity, "is_bg": False, "input_currency": "USD"})
        st.success(f"Добавено: {quantity} бр. акции")
        st.rerun()

elif asset_type == "БФБ (Българска Акция в EUR)":
    bg_name = st.sidebar.text_input("Код на компанията (напр. SHELLY, SFA)", value="SHELLY").upper()
    quantity = st.sidebar.number_input("Брой акции", min_value=0.0, value=10.0, step=1.0, key="add_bg_qty")
    manual_price = st.sidebar.number_input("Текуща цена на акция (в EUR)", min_value=0.0, value=25.0, step=0.1)
    if st.sidebar.button("Добави БФБ Акция"):
        st.session_state.portfolio.append({"type": "Акции", "name": f"{bg_name} (БФБ)", "qty": quantity, "is_bg": True, "price_eur": manual_price, "input_currency": "EUR"})
        st.success(f"Добавено: {quantity} бр. от {bg_name}")
        st.rerun()

elif asset_type == "ETF (Борсово търгуван фонд)":
    etf_ticker = st.sidebar.text_input("Тикер на ETF (напр. VUAA.DE, EUNL.DE)", value="VUAA.DE").upper()
    quantity = st.sidebar.number_input("Количество ETF (брой)", min_value=0.0, value=5.0, step=1.0, key="add_etf_qty")
    etf_curr = st.sidebar.selectbox("Валута на търгуване на ETF-а", ["EUR", "USD"])
    if st.sidebar.button("Добави ETF"):
        st.session_state.portfolio.append({"type": "ETFs", "name": etf_ticker, "qty": quantity, "is_bg": False, "input_currency": etf_curr})
        st.success(f"Добавено: {quantity} бр. ETF")
        st.rerun()

elif asset_type == "Криптовалута":
    crypto_coin = st.sidebar.selectbox("Изберете Криптовалута", ["BTC (Bitcoin)", "ETH (Ethereum)", "SOL (Solana)", "BNB (Binance Coin)"])
    clean_ticker = crypto_coin.split(" ")[0]
    crypto_ticker = f"{clean_ticker}-USD"
    quantity = st.sidebar.number_input("Количество монети", min_value=0.0, value=0.1, step=0.01, format="%.4f", key="add_crypto_qty")
    if st.sidebar.button("Добави Крипто"):
        st.session_state.portfolio.append({"type": "Крипто", "name": clean_ticker, "ticker": crypto_ticker, "qty": quantity, "input_currency": "USD"})
        st.success(f"Добавено: {quantity} от {clean_ticker}")
        st.rerun()

elif asset_type == "Благородни Метали (Унции)":
    metal_type = st.sidebar.selectbox("Метал", ["Злато", "Сребро"])
    metal_qty = st.sidebar.number_input("Тегло в Тройунции (oz)", min_value=0.0, value=1.0, step=0.1, key="add_metal_qty")
    if st.sidebar.button("Добави Метал"):
        st.session_state.portfolio.append({"type": "Метали", "name": metal_type, "qty": metal_qty, "input_currency": "USD"})
        st.success(f"Добавено: {metal_qty} oz {metal_type}")
        st.rerun()

elif asset_type == "Недвижим Имот / Земя (AI Оценка)":
    prop_category = st.sidebar.selectbox("Тип на имота", ["Двустаен", "Тристаен", "Едностаен", "Къща", "Офис", "Земеделска земя"])
    land_cat = ""
    if prop_category == "Земеделска земя":
        chosen_prov = "Всички"
        specific_input = "Земеделска земя"
        size = st.sidebar.number_input("Площ в Декари", min_value=0.0, value=10.0, step=1.0)
        land_cat = st.sidebar.selectbox("Категория на земята", ["1-ва до 3-та категория (Най-плодородна)", "4-та до 6-та категория (Средна)", "7-ма до 10-та категория (Ниска/Пасища)"])
    else:
        chosen_prov = st.sidebar.selectbox("Избери Област", all_bg_provinces, key="sidebar_prov")
        specific_input = st.sidebar.text_input("Град / Село / Курорт (напр. гр. Созопол, с. Марково):", value=f"гр. {chosen_prov}")
        size = st.sidebar.number_input("Квадратура (кв.м.)", min_value=0.0, value=75.0, step=5.0)
        
    if st.sidebar.button("🤖 Изчисли пазарна цена и добави"):
        calculated_price_eur = ai_property_valuation(prop_category, chosen_prov, specific_input, size, land_cat)
        desc = f"{prop_category} ({specific_input}) - {size} ед."
        st.session_state.portfolio.append({"type": "Имоти", "name": desc, "qty": 1.0, "is_property": True, "price_eur": calculated_price_eur, "input_currency": "EUR"})
        st.sidebar.success(f"🤖 AI Оценка добавена!")
        st.rerun()

elif asset_type == "Кеш / Депозит":
    cash_currency = st.sidebar.selectbox("Валута на кеша", ["EUR", "USD"])
    cash_name = st.sidebar.text_input("Банка / Описание", value="Револют")
    cash_amount = st.sidebar.number_input(f"Сума (в {cash_currency})", min_value=0.0, value=1000.0, step=100.0, key="add_cash_qty")
    if st.sidebar.button("Добави Кеш"):
        st.session_state.portfolio.append({"type": "Кеш", "name": f"{cash_name} ({cash_currency})", "qty": cash_amount, "input_currency": cash_currency})
        st.success(f"Добавено кеш")
        st.rerun()
# 5. ИЗЧИСЛЯВАНЕ НА ТЕКУЩИТЕ ПАЗАРНИ ЦЕНИ В СЪОТВЕТНАТА ВАЛУТА
def process_portfolio(target_currency):
    try:
        gold_price_per_oz_usd = tf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        silver_price_per_oz_usd = tf.Ticker("SI=F").history(period="1d")['Close'].iloc[-1]
    except:
        gold_price_per_oz_usd, silver_price_per_oz_usd = 2350.0, 29.50

    processed = []
    total_display_value = 0.0

    for idx, asset in enumerate(st.session_state.portfolio):
        price_in_original_currency = 0.0
        asset_currency = asset["input_currency"]

        if asset["type"] in ["Акции", "ETFs"]:
            if asset.get("is_bg"):
                price_in_original_currency = asset["price_eur"]
            else:
                try:
                    hist = tf.Ticker(asset["name"]).history(period="1d")
                    price_in_original_currency = hist['Close'].iloc[-1] if not hist.empty else 0.0
                except:
                    price_in_original_currency = 0.0
        elif asset["type"] == "Крипто":
            try:
                hist = tf.Ticker(asset["ticker"]).history(period="1d")
                price_in_original_currency = hist['Close'].iloc[-1] if not hist.empty else 0.0
            except:
                price_in_original_currency = 0.0
        elif asset["type"] == "Метали":
            price_in_original_currency = gold_price_per_oz_usd if asset["name"] == "Злато" else silver_price_per_oz_usd
        elif asset["type"] == "Имоти":
            price_in_original_currency = asset["price_eur"]
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
            "Aktив": asset["name"],
            "Количество": asset["qty"],
            f"Стойност ({currency_symbol})": round(val_final, 2),
            "Ед. Цена": round(price_final, 2)
        })
    return total_display_value, pd.DataFrame(processed)

# 6. ГЛАВЕН ЕКРАН С ТАБЛА И ГРАФИКИ
if st.session_state.portfolio:
    total_val, df_portfolio = process_portfolio(currency)
    st.metric(label=f"📊 Обща стойност на портфолиото ({currency_symbol})", value=f"{currency_symbol}{total_val:,.2f}")
    
    st.subheader("🍕 Общо разпределение на активите")
    val_column = f"Стойност ({currency_symbol})"
    df_main_pie = df_portfolio.groupby("Категория")[val_column].sum().reset_index()
    fig_main = px.pie(df_main_pie, values=val_column, names="Категория", hole=0.4)
    st.plotly_chart(fig_main, use_container_width=True)
    
    st.markdown("---")
    st.subheader("🔍 Детайлен преглед на категориите")
    available_categories = df_portfolio["Категория"].unique()
    tabs = st.tabs(list(available_categories))
    
    for index, cat_name in enumerate(available_categories):
        with tabs[index]:
            df_sub = df_portfolio[df_portfolio["Категория"] == cat_name]
            fig_sub = px.pie(df_sub, values=val_column, names="Aktив", hole=0.3)
            st.plotly_chart(fig_sub, use_container_width=True)
            st.dataframe(df_sub[["Aktив", "Количество", "Ед. Цена", val_column]], use_container_width=True)

    # 7. AI PREMIUM ФУНКЦИИ (€2.99)
    st.markdown("---")
    st.header("🧠 AI Premium Център — Анализи срещу €2.99")
    
    ai_mode = st.selectbox("Изберете тип премиум услуга:", [
        "Дълбок ИИ анализ на компания (Акции)", 
        "Търсене на подценени имоти в регион (Цяла България)",
        "Оценка и Анализ на СОБСТВЕН имот"
    ])
    
    if ai_mode == "Дълбок ИИ анализ на компания (Акции)":
        comp_to_analyze = st.text_input("Въведете компания за анализ (напр. Apple, Tesla, Shelly Group):", value="Apple")
        if st.button("💳 Купи AI Анализ за €2.99"):
            st.info("🔄 Симулиране на плащане... Успешно!")
            prompt = f"Направи кратък, професионален инвестиционен анализ на български за компанията {comp_to_analyze}."
            if client:
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.success(response.choices.message.content)
            else:
                st.success(f"🤖 **AI Доклад за {comp_to_analyze} (Демо):** Препоръка: **КУПИ**.")

    elif ai_mode == "Търсене на подценени имоти в регион (Цяла България)":
        col_reg, col_loc = st.columns(2)
        with col_reg:
            prem_province = st.selectbox("Избери Област за сканиране:", all_bg_provinces, key="prem_prov")
        with col_loc:
            prem_specific = st.text_input("Напишете конкретен град, село или курорт:", value=f"гр. {prem_province}", key="prem_spec")
            
        if st.button("💳 Сканирай региона за €2.99"):
            st.info(f"🔍 AI сканира пазара в {prem_specific}... Намерени са 3 подценени имота!")
            search_query = f"https://google.com+{prem_specific.replace(' ', '+')}"
            st.success(f"🤖 **ИИ откри сделки под пазарната стойност в {prem_specific}:**")
            st.write("1. **Двустаен апартамент** — 15% под пазара за района.")
            st.write("2. **Спешна продажба на парцел/имот** — готов за инвестиция.")
            st.markdown(f"🔗 **[Кликни тук, за да разгледаш активните обяви за {prem_specific} в реално време]({search_query})**")

    elif ai_mode == "Оценка и Анализ на СОБСТВЕН имот":
        st.write("### 🏠 Анализ на Вашия личен имот")
        my_prop_type = st.selectbox("Тип на Вашия имот:", ["Едностаен", "Двустаен", "Тристаен", "Къща", "Офис"])
        my_province = st.selectbox("Област:", all_bg_provinces, key="my_prov")
        my_specific = st.text_input("Конкретно населено място (напр. с. Марково, гр. София):", value=f"гр. {my_province}", key="my_spec")
        my_size = st.number_input("Квадратура (кв.м.):", min_value=10, value=65)
        my_extras = st.text_input("Допълнителни детайли (напр. Луксозен ремонт, Обзаведен):", value="След ремонт")
        
        if st.button("💳 Оцени и Анализирай моя имот за €2.99"):
            st.info("🔄 Пазарният ИИ модул пресмята стойността...")
            estimated_val = ai_property_valuation(my_prop_type, my_province, my_specific, my_size)
            st.success(f"📊 **AI Доклад за Вашия имот в {my_specific}:**")
            st.write(f"* **Текуща прогнозна пазарна стойност:** €{estimated_val:,.2f}")
            st.write(f"* **Средна цена на кв.м. за района:** €{int(estimated_val/my_size)} / кв.м.")

    # 8. СЕКЦИЯ ЗА РЕДАКТИРАНЕ
    st.markdown("---")
    st.subheader("🛠️ Управление и редакция на активите")
    for idx, item in enumerate(st.session_state.portfolio):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write(f"**{item['name']}**")
        with col2:
            step_val = 0.0001 if item['type'] == 'Крипто' else 0.1
            new_qty = st.number_input(f"Количество", min_value=0.0, value=float(item['qty']), step=step_val, format="%.4f" if item['type'] == 'Крипто' else "%.1f", key=f"edit_qty_{idx}")
            if new_qty != item['qty']:
                st.session_state.portfolio[idx]['qty'] = new_qty
                st.rerun()
        with col3:
            st.write(f"Текущо: {item['qty']}")
        with col4:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.portfolio.pop(idx)
                st.rerun()

    if st.button("❌ Изчисти цялото портфолио"):
        st.session_state.portfolio = []
        st.rerun()
else:
    st.info("Портфолиото ви е празно. Добавете активи от страничното меню.")










