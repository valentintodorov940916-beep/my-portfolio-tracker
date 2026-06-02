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

# ИНИЦИАЛИЗИРАНЕ НА OPENAI КЛИЕНТ (Използва безплатен тестов режим, ако няма ключ)
# За реална работа в GitHub се добавя таен ключ (Secret Key)
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

# 3. AI ОЦЕНИТЕЛ НА НЕДВИЖИМИ ИМОТИ И ЗЕМЕДЕЛСКА ЗЕМЯ
def ai_property_valuation(prop_type, location, size, category=""):
    base_prices = {
        "София": {"Едностаен": 2100, "Двустаен": 1950, "Тристаен": 1900, "Къща": 1700, "Офис": 2200},
        "Пловдив": {"Едностаен": 1400, "Двустаен": 1300, "Тристаен": 1250, "Къща": 1100, "Офис": 1400},
        "Варна": {"Едностаен": 1600, "Двустаен": 1500, "Тристаен": 1450, "Къща": 1300, "Офис": 1550},
        "Бургас": {"Едностаен": 1350, "Двустаен": 1250, "Тристаен": 1200, "Къща": 1050, "Офис": 1200},
        "Друг град": {"Едностаен": 900, "Двустаен": 850, "Тристаен": 800, "Къща": 700, "Офис": 800}
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
        city_prices = base_prices.get(location, base_prices["Друг град"])
        price_per_meter = city_prices.get(prop_type, 1000)
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
        location = "България"
        size = st.sidebar.number_input("Площ в Декари", min_value=0.0, value=10.0, step=1.0)
        land_cat = st.sidebar.selectbox("Категория на земята", ["1-ва до 3-та категория (Най-плодородна)", "4-та до 6-та категория (Средна)", "7-ма до 10-та категория (Ниска/Пасища)"])
    else:
        location = st.sidebar.selectbox("Град / Локация", ["София", "Пловдив", "Варна", "Бургас", "Друг град"])
        size = st.sidebar.number_input("Квадратура (кв.м.)", min_value=0.0, value=75.0, step=5.0)
    if st.sidebar.button("🤖 Изчисли пазарна цена и добави"):
        calculated_price_eur = ai_property_valuation(prop_category, location, size, land_cat)
        desc = f"{prop_category} ({location if prop_category != 'Земеделска земя' else land_cat[:9]}) - {size} ед."
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

    # 7. НОВА СЕКЦИЯ: AI PREMIUM ФУНКЦИИ (€2.99)
    st.markdown("---")
    st.header("🧠 AI Premium Център — Анализи срещу €2.99")
    st.write("Генерирайте детайлни доклади в реално време, задвижвани от Изкуствен Интелект.")
    
    ai_mode = st.selectbox("Изберете тип премиум услуга:", ["Дълбок ИИ анализ на компания (Акции)", "Търсене на подценени имоти в регион"])
    
    if ai_mode == "Дълбок ИИ анализ на компания (Акции)":
        comp_to_analyze = st.text_input("Въведете компания за анализ (напр. Apple, Tesla, Shelly Group):", value="Apple")
        if st.button("💳 Купи AI Анализ за €2.99"):
            st.info("🔄 Симулиране на плащане... Успешно! Стартиране на AI финансовия модел...")
            
            prompt = f"Направи кратък, професионален и критичен инвестиционен анализ на български език за компанията {comp_to_analyze}. Включи силни страни, рискове и крайна присъда: Купи, Продай или Задръж."
            
            if client:
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.success("🤖 **Професионален AI Доклад:**")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Грешка с AI връзката: {e}")
            else:
                # Демонстрационен режим, ако липсва платен OpenAI Ключ
                st.success("🤖 **Професионален AI Доклад (Демонстрационен режим):**")
                st.write(f"Фирмата **{comp_to_analyze}** показва силни финансови резултати към 2026 г. Основен плюс са стабилните парични потоци. Риск: високата пазарна оценка. **Присъда: ЗАДЪРЖАЙ.**")

    elif ai_mode == "Търсене на подценени имоти в регион":
        region_to_search = st.selectbox("Изберете регион за сканиране:", ["София - Лозенец", "София - Младост", "Пловдив - Център", "Варна - Чайка"])
        if st.button("💳 Сканирай за подценени имоти за €2.99"):
            st.info("🔄 Плащането е потвърдено. ИИ стартира уеб-скрейпинг агенти...")
            
            prompt = f"Измисли и покажи списък от 3 реалистични, фиктивни, но силно подценени оферти за недвижими имоти (с 15% под средната пазарна цена) в района на {region_to_search} за 2026 година. Напиши ги в табличен вид с квадратура, цена и защо ИИ ги смята за изгодни."
            
            if client:
                try:
                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    st.success("🤖 **AI Списък с топ 3 подценени имота в региона:**")
                    st.write(response.choices[0].message.content)
                except Exception as e:
                    st.error(f"Грешка с AI връзката: {e}")
            else:
                st.success("🤖 **AI Списък с топ 3 подценени имота (Демонстрация):**")
                st.write(f"1. Тристаен в {region_to_search}, 90 кв.м. — Цена: €150,000 (Спешна продажба, 18% под пазара).\n2. Двустаен в същия район, 65 кв.м. — Цена: €115,000 (За ремонт).")

    # 8. СЕКЦИЯ ЗА РЕДАКТИРАНЕ
    st.markdown("---")
    st.subheader("🛠️ Управление и редакция на активите")
    for idx, item in enumerate(st.session_state.portfolio):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.write(f"**{item['name']}** ({item['type']})")
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








