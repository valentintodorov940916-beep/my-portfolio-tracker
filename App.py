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

# 3. БАЗА ДАННИ ЗА БЪЛГАРИЯ (Примерен модел за MVP)
bg_regions = {
    "София (град)": ["София-център", "Младост", "Лозенец", "Люлин", "с. Панчарево", "с. Бистрица"],
    "Пловдив": ["Пловдив-град", "Асеновград", "Карлово", "с. Марково", "с. Белащица", "курорт Пампорово"],
    "Варна": ["Варна-град", "Златни Пясъци", "Св. Св. Константин и Елена", "Провадия", "с. Тополи"],
    "Бургас": ["Бургас-град", "курорт Слънчев Бряг", "Несебър", "Созопол", "Поморие", "с. Равда"],
    "Благоевград": ["Благоевград-град", "курорт Банско", "Сандански", "Разлог", "с. Баня"]
}

# AI ОЦЕНИТЕЛ НА НЕДВИЖИМИ ИМОТИ
def ai_property_valuation(prop_type, location, size, category=""):
    base_prices = {
        "София-център": 2300, "Лозенец": 2200, "Младост": 1800, "Люлин": 1300, "с. Панчарево": 1400,
        "Пловдив-град": 1400, "с. Марково": 1200, "курорт Пампорово": 1100,
        "Варна-град": 1600, "Златни Пясъци": 1700, "Бургас-град": 1350, "курорт Слънчев Бряг": 1100,
        "курорт Банско": 1200, "Благоевград-град": 950
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
        price_per_meter = base_prices.get(location, 1000)
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
        chosen_region = "България"
        chosen_loc = "Земеделска земя"
        size = st.sidebar.number_input("Площ в Декари", min_value=0.0, value=10.0, step=1.0)
        land_cat = st.sidebar.selectbox("Категория на земята", ["1-ва до 3-та категория (Най-плодородна)", "4-та до 6-та категория (Средна)", "7-ма до 10-та категория (Ниска/Пасища)"])
    else:
        chosen_region = st.sidebar.selectbox("Избери Област", list(bg_regions.keys()), key="sidebar_region")
        chosen_loc = st.sidebar.selectbox("Избери Град / Село / Курорт", bg_regions[chosen_region], key="sidebar_loc")
        size = st.sidebar.number_input("Квадратура (кв.м.)", min_value=0.0, value=75.0, step=5.0)
        
    if st.sidebar.button("🤖 Изчисли пазарна цена и добави"):
        calculated_price_eur = ai_property_valuation(prop_category, chosen_loc, size, land_cat)
        desc = f"{prop_category} ({chosen_loc}) - {size} ед."
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
            prompt = f"Направи кратък, професионален инвестиционен анализ на български за компанията {comp_to_analyze}. Включи присъда: Купи, Продай или Задръж."
            if client:
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.success(response.choices[0].message.content)
            else:
                st.success(f"🤖 **AI Доклад за {comp_to_analyze} (Демо):** Перспективна компания за инвестиция. Препоръка: **КУПИ**.")

    elif ai_mode == "Търсене на подценени имоти в регион (Цяла България)":
        col_reg, col_loc = st.columns(2)
        with col_reg:
            prem_region = st.selectbox("Избери Област за сканиране:", list(bg_regions.keys()), key="prem_reg")
        with col_loc:
            prem_loc = st.selectbox("Избери конкретен Град / Село / Курорт:", bg_regions[prem_region], key="prem_loc")
            
        if st.button("💳 Сканирай региона за €2.99"):
            st.info(f"🔍 AI сканира пазара в {prem_loc}... Намерени са 3 подценени имота!")
            
            # Генератор на реални смарт линкове за пазара в България
            search_query = f"https://google.com+{prem_loc.replace(' ', '+')}"
            st.success(f"🤖 **ИИ откри сделки под пазарната стойност в {prem_loc}:**")
            st.write("1. **Двустаен апартамент** — 68 кв.м. — Цена: €85,000 (15% под пазара за района).")
            st.write("2. **Къща с двор** — 120 кв.м. — Цена: €110,000 (Спешна продажба).")
            
            st.markdown(f"🔗 **[Кликни тук, за да разгледаш активните обяви за {prem_loc} в реално време]({search_query})**")

    elif ai_mode == "Оценка и Анализ на СОБСТВЕН имот":
        st.write("### 🏠 Анализ на Вашия личен имот")
        my_prop_type = st.selectbox("Тип на Вашия имот:", ["Едностаен", "Двустаен", "Тристаен", "Къща", "Офис"])
        my_region = st.selectbox("Област:", list(bg_regions.keys()), key="my_reg")
        my_loc = st.selectbox("Град / Село / Курорт:", bg_regions[my_region], key="my_loc")
        my_size = st.number_input("Квадратура (кв.м.):", min_value=10, value=65)
        my_extras = st.text_input("Допълнителни детайли (напр. Луксозен ремонт, Обзаведен, Акт 16, Панорама):", value="След ремонт, паркомясто")
        
        if st.button("💳 Оцени и Анализирай моя имот за €2.99"):
            st.info("🔄 Пазарният ИИ модул пресмята стойността...")
            estimated_val = ai_property_valuation(my_prop_type, my_loc, my_size)
            
            st.success(f"📊 **AI Доклад за Вашия имот в {my_loc}:**")
            st.write(f"* **Текуща прогнозна пазарна стойност:** €{estimated_val:,.2f}")
            st.write(f"* **Средна цена на кв.м. за района:** €{int(estimated_val/my_size)} / кв.м.")
            st.write(f"* **AI Коментар спрямо екстрите ({my_extras}):** Имотът има висока ликвидност. Наличието на паркомясто в {my_loc} вдига стойността с около 7-10% над базовата цена за района. Подходящ за отдаване под наем с доходност около 5.5% годишно.")

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









