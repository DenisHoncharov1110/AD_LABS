# ──────────────────────────────────────────────────────────────────────────────
# 1) ЄДИНИЙ Streamlit-виклик перед будь-чим іншим
import streamlit as st
st.set_page_config(
    page_title="Аналіз VCI/TCI/VHI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# 2) Тепер решта імпортів йде вже після set_page_config
import pandas as pd
import os

# ──────────────────────────────────────────────────────────────────────────────
# 3) Завантаження й очищення даних
@st.cache_data
def load_data():
    path = os.path.join("data", "full_df.csv")
    df = pd.read_csv(path)

    # Очищення 'year'
    years = (
        df["year"].astype(str)
             .str.extract(r"(\d{4})")[0]
             .pipe(pd.to_numeric, errors="coerce")
    )
    valid = years.notna()
    df = df.loc[valid].copy()
    df["year"] = years[valid].astype(int)

    # Очищення 'week'
    df["week"] = (
        pd.to_numeric(df["week"], errors="coerce")
          .fillna(1).astype(int)
    )

    return df

df = load_data()

# ──────────────────────────────────────────────────────────────────────────────
# 4) Інтерфейс Streamlit
st.title("🌱 Візуалізація VCI / TCI / VHI для областей України")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("🔎 Фільтри")
    index_type = st.selectbox("Індекс", ["VCI", "TCI", "VHI"])
    region = st.selectbox("Область", sorted(df["area"].unique()))

    year_min, year_max = int(df["year"].min()), int(df["year"].max())
    year_range = st.slider("Роки", year_min, year_max, (year_min, year_max))

    week_range = st.slider("Тижні", 1, 52, (1, 52))

    st.markdown("---")
    sort_asc = st.checkbox("Сортувати за зростанням", value=False)
    sort_desc = st.checkbox("Сортувати за спаданням", value=False)

    if st.button("🔄 Скинути фільтри"):
        st.experimental_rerun()

with col2:
    st.header("📊 Результати")

    # Фільтрація
    df_filt = df[
        (df["area"] == region) &
        (df["year"].between(year_range[0], year_range[1])) &
        (df["week"].between(week_range[0], week_range[1]))
    ][["year", "week", index_type]].copy()

    # Сортування
    if sort_asc and not sort_desc:
        df_filt = df_filt.sort_values(index_type, ascending=True)
    elif sort_desc and not sort_asc:
        df_filt = df_filt.sort_values(index_type, ascending=False)

    # Вкладки
    tab1, tab2, tab3 = st.tabs(["📋 Таблиця", "📈 Графік", "🗺 Порівняння"])

    with tab1:
        st.subheader("Таблиця")
        if df_filt.empty:
            st.warning("Немає даних за цими фільтрами.")
        else:
            st.dataframe(df_filt, use_container_width=True)

    with tab2:
        st.subheader(f"{index_type} по тижнях для «{region}»")
        if df_filt.empty:
            st.warning("Немає даних для графіка.")
        else:
            df_plot = df_filt.sort_values("week").set_index("week")[index_type]
            st.line_chart(df_plot)

    with tab3:
        st.subheader(f"Середній {index_type} по областях")
        df_cmp = df[
            (df["year"].between(year_range[0], year_range[1])) &
            (df["week"].between(week_range[0], week_range[1]))
        ]
        comp = df_cmp.groupby("area")[index_type].mean().sort_values()
        st.bar_chart(comp)
