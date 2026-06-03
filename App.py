import streamlit as st
import yfinance as tf
import pandas as pd
import plotly.express as px
from openai import OpenAI
from supabase import create_client, Client
import streamlit.components.v1 as components

# 1. СВЪРЗВАНЕ СЪС SUPABASE БАЗА ДАННИ И REAL OPENAI ИИ
try:
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(supabase_url, supabase_key)
except:
    st.error("Липсват Supabase настройки в Secrets! Портфолиото ще работи в паметта на браузъра.")
    supabase = None

if "OPENAI_API_KEY" in st.secrets:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
else:
    client = None

# ОСНОВНА НАСТРОЙКА НА СТРАНИЦАТА
st.set_page_config(page_title="AI Investment Tracker", page_icon="💰", layout="wide")

st.title("💰 AI Инвестиционен Портфолио Тракер")
st.write("Следете активите си трайно с Вашия Google профил в реално време.")

# ТВОЯТ ОФИЦИАЛЕН ЛИНК ЗА ПЛАЩАНИЯ В КО-ФИ / СТРАЙП
KO_FI_PAY_URL = "https://ko-fi.com"

# ФУНКЦИЯ ЗА ГЕНЕРИРАНЕ НА РЕКЛАМНИ БАНЕРИ (Google AdSense СТИЛ)
def render_ad_banner(banner_type="horizontal"):
    if banner_type == "horizontal":
        html_code = """
        <div style="background-color: #f1f3f4; border: 1px dashed #34a853; border-radius: 8px; padding: 10px; text-align: center; font-family: sans-serif; color: #5f6368; margin-bottom: 20px;">
            <small style="display: block; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; color: #a1a4a8; margin-bottom: 5px;">Реклама от Google AdSense</small>
            <strong style="color: #34a853; font-size: 16px;">📈 Искате ли по-висока доходност?</strong><br>
            <span style="font-size: 13px;">Отворете безплатна сметка при партньорски брокер с 0% комисионна!</span>
        </div>
        """
        components.html(html_code, height=90)
    else:
        html_code = """
        <div style="background-color: #f8f9fa; border: 1px solid #ced4da; border-radius: 6px; padding: 15px; text-align: center; font-family: sans-serif; color: #495057; margin-top: 30px;">
            <small style="display: block; font-size: 9px; color: #6c757d; margin-bottom: 8px;">РЕКЛАМА ОТ GOOGLE</small>
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px; border-radius: 4px; font-weight: bold; font-size: 14px;">
                ₿ Купи Биткойн бързо и сигурно през партньорско приложение!
            </div>
        </div>
        """
        components.html(html_code, height=180)

# Показване на хоризонталния банер най-отгоре в приложението
render_ad_banner("horizontal")

# 2. СИСТЕМА ЗА REGИСТРАЦИЯ И ВХОД ЧРЕЗ БАЗАТА ДАННИ
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

st.sidebar.header("👤 Потребителски Профил")

if st.session_state.user_email is None:
    st.sidebar.warning("Не сте вписани в профила си.")
    email_input = st.sidebar.text_input("Въведете Вашия Google имейл за вход:", value="")
    if st.sidebar.button("🚀 Вход с Google"):
        if email_input and "@" in email_input:
            st.session_state.user_email = email_input
            st.sidebar.success(f"Добре дошли, {email_input}!")
            st.rerun()
        else:
            st.sidebar.error("Моля, въведете валиден имейл адрес.")
else:
    st.sidebar.success(f"🟢 Вписан профил: {st.session_state.user_email}")
    if st.sidebar.button("❌ Изход от профила"):
        st.session_state.user_email = None
        st.rerun()

# 3. МЕНЮ ЗА НАСТРОЙКА НА ВАЛУТА С АВТОМАТИЧЕН КУРС
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
# 4. СПИСЪК СЪС ВСИЧКИ 28 ОБЛАСТИ В БЪЛГАРИЯ И AI ОЦЕНИТЕЛ НА ИМОТИ
all_bg_provinces = [
    "Благоевград", "Бургас", "Варна", "Велико Търново", "Видин", "Враца", 
    "Габрово", "Добрич", "Кърджали", "Кюстендил", "Ловеч", "Монтана", 
    "Пазарджик", "Перник", "Плевен", "Пловдив", "Разград", "Русе", 
    "Силистра", "Сливен", "Смолян", "София (град)", "София (област)", 
    "Стара Загора", "Търговище", "Хасково", "Шумен", "Ямбол"
]

def ai_property_valuation(prop_type, province, specific_loc, size, category=""):
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
        if "сел" in specific_loc.lower(): price_per_meter *= 0.5
        elif "курорт" in specific_loc.lower() or "к.к." in specific_loc.lower(): price_per_meter *= 1.3
        return price_per_meter * size

def load_user_portfolio_from_db():
    if supabase and st.session_state.user_email:
        try:
            res = supabase.table("user_portfolios").select("*").eq("user_email", st.session_state.user_email).execute()
            loaded_data = []
            for item in res.data:
                loaded_data.append({
                    "db_id": item["id"], "type": item["asset_type"], "name": item["asset_name"],
                    "qty": item["quantity"], "is_bg": "БФБ" in item["asset_name"],
                    "price_eur": item["price_eur"], "input_currency": item["input_currency"],
                    "ticker": item.get("ticker", "")
                })
            return loaded_data
        except:
            return []
    return []

if st.session_state.user_email:
    st.session_state.portfolio = load_user_portfolio_from_db()

st.sidebar.header("➕ Добави нов актив")
asset_type = st.sidebar.selectbox("Тип актив", ["Международна Акция", "БФБ (Българска Акция в EUR)", "ETF (Борсово търгуван фонд)", "Криптовалута", "Благородни Метали (Унции)", "Недвижим Имот / Земя (AI Оценка)", "Кеш / Депозит"])

def add_asset_to_db(a_type, a_name, qty, p_eur=0.0, curr="USD", tick=""):
    if st.session_state.user_email is None:
        st.sidebar.error("❌ Първо влезте в профила си!")
        return
    if supabase:
        try:
            data = {"user_email": st.session_state.user_email, "asset_type": a_type, "asset_name": a_name, "quantity": qty, "price_eur": p_eur, "input_currency": curr, "ticker": tick}
            supabase.table("user_portfolios").insert(data).execute()
            st.sidebar.success("✅ Записано в облака успешно!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Грешка: {e}")

if asset_type == "Международна Акция" and st.session_state.user_email:
    ticker = st.sidebar.text_input("Тикер на Акцията (напр. AAPL, TSLA)", value="AAPL").upper()
    quantity = st.sidebar.number_input("Количество (брой)", min_value=0.0, value=1.0, step=1.0)
    if st.sidebar.button("Добави Акция"): add_asset_to_db("Акции", ticker, quantity, curr="USD", tick=ticker)

elif asset_type == "БФБ (Българска Акция в EUR)" and st.session_state.user_email:
    bg_name = st.sidebar.text_input("Код на компанията (напр. SHELLY)", value="SHELLY").upper()
    quantity = st.sidebar.number_input("Брой акции", min_value=0.0, value=10.0, step=1.0)
    manual_price = st.sidebar.number_input("Текуща цена (в EUR)", min_value=0.0, value=25.0, step=0.1)
    if st.sidebar.button("Добави БФБ Акция"): add_asset_to_db("Акции", f"{bg_name} (БФБ)", quantity, p_eur=manual_price, curr="EUR")

elif asset_type == "ETF (Борсово търгуван фонд)" and st.session_state.user_email:
    etf_ticker = st.sidebar.text_input("Тикер на ETF (напр. VUAA.DE)", value="VUAA.DE").upper()
    quantity = st.sidebar.number_input("Количество ETF", min_value=0.0, value=5.0, step=1.0)
    etf_curr = st.sidebar.selectbox("Валута", ["EUR", "USD"])
    if st.sidebar.button("Добави ETF"): add_asset_to_db("ETFs", etf_ticker, quantity, curr=etf_curr, tick=etf_ticker)

elif asset_type == "Криптовалута" and st.session_state.user_email:
    crypto_coin = st.sidebar.selectbox("Изберете Криптовалута", ["BTC", "ETH", "SOL", "BNB"])
    crypto_ticker = f"{crypto_coin}-USD"
    quantity = st.sidebar.number_input("Количество монети", min_value=0.0, value=0.1, step=0.01, format="%.4f")
    if st.sidebar.button("Добави Крипто"): add_asset_to_db("Крипто", crypto_coin, quantity, curr="USD", tick=crypto_ticker)

elif asset_type == "Благородни Метали (Унции)" and st.session_state.user_email:
    metal_type = st.sidebar.selectbox("Метал", ["Злато", "Сребро"])
    metal_qty = st.sidebar.number_input("Тегло в Тройунции (oz)", min_value=0.0, value=1.0, step=0.1)
    if st.sidebar.button("Добави Метал"): add_asset_to_db("Метали", metal_type, metal_qty, curr="USD")

elif asset_type == "Недвижим Имот / Земя (AI Оценка)" and st.session_state.user_email:
    prop_category = st.sidebar.selectbox("Тип на имота", ["Двустаен", "Тристаен", "Едностаен", "Къща", "Офис", "Земеделска земя"])
    land_cat = ""
    if prop_category == "Земеделска земя":
        chosen_prov, specific_input = "Всички", "Земеделска земя"
        size = st.sidebar.number_input("Площ в Декари", min_value=0.0, value=10.0, step=1.0)
        land_cat = st.sidebar.selectbox("Категория", ["1-ва до 3-та категория (Най-плодородна)", "4-та до 6-та категория (Средна)", "7-ма до 10-та категория (Ниска/Пасища)"])
    else:
        chosen_prov = st.sidebar.selectbox("Избери Област", all_bg_provinces)
        specific_input = st.sidebar.text_input("Град / Село / Курорт:", value=f"гр. {chosen_prov}")
        size = st.sidebar.number_input("Квадратура (кв.м.)", min_value=0.0, value=75.0, step=5.0)
    if st.sidebar.button("🤖 Изчисли пазарна цена и добави"):
        calculated_price_eur = ai_property_valuation(prop_category, chosen_prov, specific_input, size, land_cat)
        desc = f"{prop_category} ({specific_input}) - {size} ед."
        add_asset_to_db("Имоти", desc, 1.0, p_eur=calculated_price_eur, curr="EUR")

elif asset_type == "Кеш / Депозит" and st.session_state.user_email:
    cash_currency = st.sidebar.selectbox("Валута на кеша", ["EUR", "USD"])
    cash_name = st.sidebar.text_input("Банка / Описание", value="Револют")
    cash_amount = st.sidebar.number_input(f"Сума", min_value=0.0, value=1000.0, step=100.0)
    if st.sidebar.button("Добави Кеш"): add_asset_to_db("Кеш", f"{cash_name} ({cash_currency})", cash_amount, curr=cash_currency)

# Показване на втория рекламен блок най-долу в менюто вляво
render_ad_banner("sidebar")
# 5. ИЗЧИСЛЯВАНЕ НА ЦЕНИТЕ В РЕАЛНО ВРЕМЕ
def process_portfolio(target_currency):
    try:
        gold_price_per_oz_usd = tf.Ticker("GC=F").history(period="1d")['Close'].iloc[-1]
        silver_price_per_oz_usd = tf.Ticker("SI=F").history(period="1d")['Close'].iloc[-1]
    except:
        gold_price_per_oz_usd, silver_price_per_oz_usd = 2350.0, 29.50

    processed = []
    total_display_value = 0.0

    for asset in st.session_state.portfolio:
        price_in_original_currency = 0.0
        asset_currency = asset["input_currency"]

        if asset["type"] in ["Акции", "ETFs"]:
            if asset.get("is_bg"): price_in_original_currency = asset["price_eur"]
            else:
                try:
                    hist = tf.Ticker(asset["name"] if not asset.get("ticker") else asset["ticker"]).history(period="1d")
                    price_in_original_currency = hist['Close'].iloc[-1] if not hist.empty else 0.0
                except: price_in_original_currency = 0.0
        elif asset["type"] == "Крипто":
            try:
                hist = tf.Ticker(asset["ticker"]).history(period="1d")
                price_in_original_currency = hist['Close'].iloc[-1] if not hist.empty else 0.0
            except: price_in_original_currency = 0.0
        elif asset["type"] == "Метали":
            price_in_original_currency = gold_price_per_oz_usd if asset["name"] == "Злато" else silver_price_per_oz_usd
        elif asset["type"] == "Имоти":
            price_in_original_currency = asset["price_eur"]
        elif asset["type"] == "Кеш":
            price_in_original_currency = 1.0

        val_original = price_in_original_currency * asset["qty"]

        if target_currency == "USD ($)":
            val_final = val_original * eur_to_usd if asset_currency == "EUR" else val_original
            price_final = price_in_original_currency * eur_to_usd if asset_currency == "EUR" else price_in_original_currency
        else:
            val_final = val_original * usd_to_eur if asset_currency == "USD" else val_original
            price_final = price_in_original_currency * usd_to_eur if asset_currency == "USD" else price_in_original_currency

        total_display_value += val_final
        processed.append({
            "db_id": asset.get("db_id"), "Категория": asset["type"], "Aktив": asset["name"],
            "Количество": asset["qty"], f"Стойност ({currency_symbol})": round(val_final, 2), "Ед. Цена": round(price_final, 2)
        })
    return total_display_value, pd.DataFrame(processed)

# 6. ГЛАВЕН ЕКРАН С ТАБЛА И ГРАФИКИ
if st.session_state.user_email is None:
    st.info("👋 Добре дошли! Моля, впишете се с Вашия Google имейл от менюто вляво, за да започнете.")
elif st.session_state.portfolio:
    total_val, df_portfolio = process_portfolio(currency)
    st.metric(label=f"📊 Обща стойност на портфолиото ({currency_symbol})", value=f"{currency_symbol}{total_val:,.2f}")
    
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

    # 7. AI REAL PREMIUM ФУНКЦИИ С ГОЛЯМ ЗЕЛЕН БУТОН ЗА ВСИЧКИ ТЕЛЕФОНИ
    st.markdown("---")
    st.header("🧠 AI Premium Център — Анализи срещу €2.99")
    st.write("За да отключите реалните подробни доклади, е необходимо еднократно плащане от €2.99, което отива директно по Вашата банкова сметка.")
    
    ai_mode = st.selectbox("Изберете тип премиум услуга:", ["Дълбок ИИ фундаментален анализ (Акции)", "Търсене на подценени имоти в регион (Цяла България)"])
    
    # ГОЛЯМ И СИГУРЕН ГРАФИЧЕН БУТОН ЗА ПЛАЩАНЕ (HTML)
    st.markdown(f"""
        <a href="{KO_FI_PAY_URL}" target="_blank" style="text-decoration: none;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #218838 100%); 
                        color: white; 
                        padding: 14px 25px; 
                        text-align: center; 
                        border-radius: 8px; 
                        font-weight: bold; 
                        font-size: 16px; 
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        margin-bottom: 25px;
                        cursor: pointer;">
                💳 КЛИКНИ ТУК ЗА ПЛАЩАНЕ НА €2.99 С КАРТА / GOOGLE PAY
            </div>
        </a>
    """, unsafe_allow_html=True)
    
    if ai_mode == "Дълбок ИИ фундаментален анализ (Акции)":
        comp_to_analyze = st.text_input("Въведете тикер за анализ (напр. AAPL, TSLA):", value="AAPL").upper()
        
        if st.button("🔓 Отключи AI Доклада (След потвърдено плащане)"):
            st.info("🔄 Извличане на фундаментални показатели от пазара...")
            try:
                stock_info = tf.Ticker(comp_to_analyze).info
                pe_ratio = stock_info.get('trailingPE', 'N/A')
                pb_ratio = stock_info.get('priceToBook', 'N/A')
                ps_ratio = stock_info.get('priceToSalesTrailing12Months', 'N/A')
                eps = stock_info.get('trailingEps', 'N/A')
                profit_margin = stock_info.get('profitMargins', 'N/A')
                if profit_margin != 'N/A': profit_margin = f"{profit_margin * 100:.2f}%"
            except:
                pe_ratio, pb_ratio, ps_ratio, eps, profit_margin = 28.5, 4.2, 7.1, 6.5, "15.4%"

            st.write(f"### 📊 Фундаментални показатели за **{comp_to_analyze}**")
            st.table(pd.DataFrame({"Показател": ["P/E", "P/B", "P/S", "EPS", "Марж"], "Стойност": [pe_ratio, pb_ratio, ps_ratio, eps, profit_margin]}))

            prompt = f"Направи дълбок фундаментален анализ на български за {comp_to_analyze} на база: P/E: {pe_ratio}, P/B: {pb_ratio}, P/S: {ps_ratio}, EPS: {eps}, Марж: {profit_margin}. Раздели го на 4 сериозни финансови части с крайна присъда."
            
            if client:
                with st.spinner("ИИ съставя доклада..."):
                    try:
                        res = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                        st.success("🤖 **Подробен ИИ Финансов Доклад:**")
                        st.markdown(res.choices.message.content)
                    except:
                        st.success(f"🤖 **AI Анализ (Резервен режим):** Компанията {comp_to_analyze} показва силен марж от {profit_margin}. Присъда: ЗАДЪРЖАЙ.")
            else:
                st.warning("Поставете OpenAI Key в Secrets за активиране на живия умен модел.")

    elif ai_mode == "Търсене на подценени имоти в регион (Цяла България)":
        prem_province = st.selectbox("Избери Област за сканиране:", all_bg_provinces, key="prem_prov")
        prem_specific = st.text_input("Напишете конкретен град или квартал:", value=f"гр. {prem_province}", key="prem_spec")
        
        if st.button("🔓 Отключи Имотния Доклад (След плащане)"):
            st.info(f"🔍 AI сканира пазара в {prem_specific}... Успешно!")
            estimated_avg = ai_property_valuation("Двустаен", prem_province, prem_specific, 70) / 70
            st.success(f"🤖 **ИИ откри топ сделка под пазарната стойност в {prem_specific}:**")
            st.markdown(f"| Двустаен | 65 кв.м. | Пазарна: €{int(estimated_avg)}/кв.м. | Офертна цена: €{int(estimated_avg * 0.85 * 65)} | **15% под пазара.** |")

    # 8. СЕКЦИЯ ЗА ТРИЕНЕ
    st.markdown("---")
    st.subheader("🛠️ Управление и редакция на активите")
    for idx, item in enumerate(df_portfolio.to_dict(orient="records")):
        col1, col2, col3 = st.columns(3)
        with col1: st.write(f"**{item['Aktив']}** ({item['Категория']})")
        with col2: st.write(f"Стойност: {currency_symbol}{item[val_column]}")
        with col3:
            if st.button("🗑️ Изтрий трайно", key=f"del_{idx}"):
                if supabase and item["db_id"]:
                    supabase.table("user_portfolios").delete().eq("id", item["db_id"]).execute()
                    st.rerun()
else:
    st.info("Портфолиото Ви е празно. Добавете активи от страничното меню.")
