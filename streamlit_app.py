# Streamlit consumindo a API /dump
import os, requests, pandas as pd, streamlit as st

API_DEFAULT = os.environ.get("API_BASE", "http://localhost:5000")
st.set_page_config(page_title="Simulador (via API)", layout="wide")
st.title("Simulador (via API)")

st.sidebar.subheader("API")
api_base = st.sidebar.text_input("Base URL da API", API_DEFAULT)
token = st.sidebar.text_input("Bearer token (opcional)", type="password")
if st.sidebar.button("🔄 Atualizar agora"):
    st.cache_data.clear()

@st.cache_data(ttl=30)
def fetch_dump(api, tok):
    h = {"Authorization": f"Bearer {tok}"} if tok else {}
    r = requests.get(f"{api.rstrip('/')}/dump", headers=h, timeout=20)
    r.raise_for_status()
    return r.json()

def df_from_path(dump, path):
    obj = dump.get("data", {})
    for p in path.split("."):
        obj = obj.get(p, {})
    return pd.DataFrame(obj) if isinstance(obj, list) else pd.DataFrame()

def filter_df(df, term):
    if not term or df.empty: return df
    term = term.lower()
    m = df.astype(str).apply(lambda c: c.str.lower().str.contains(term, na=False))
    return df[m.any(axis=1)]

try:
    dump = fetch_dump(api_base, token)
except Exception as e:
    st.error(f"Erro ao buscar {api_base}/dump: {e}")
    st.stop()

tot = dump.get("meta", {}).get("totals", {})
st.info(f"Totais — Associados: {tot.get('associates',0)} | Eventos: {tot.get('events',0)} | Faturas: {tot.get('invoices',0)} | Pagamentos: {tot.get('payments',0)}")

tabs_def = [
    ("associates","Associados"), ("invoices","Faturas"), ("payments","Pagamentos"),
    ("events","Eventos"), ("registrations","Inscrições"),
    ("reports.monthly_revenue","Relatório: Receita"),
    ("reports.delinquency","Relatório: Inadimplência"),
]
tabs = st.tabs([t[1] for t in tabs_def])

for i,(key,label) in enumerate(tabs_def):
    with tabs[i]:
        st.subheader(label)
        df = df_from_path(dump, key)
        term = st.text_input("Pesquisar nesta aba…", key=f"q_{key.replace('.','_')}")
        dff = filter_df(df, term)
        st.dataframe(dff, use_container_width=True)
        st.download_button("⬇️ CSV", dff.to_csv(index=False).encode("utf-8"),
                           f"{key.replace('.','_')}.csv", "text/csv")
        if key=="reports.monthly_revenue" and not dff.empty:
            st.line_chart(dff.set_index("month")["revenue"])
        if key=="reports.delinquency" and not dff.empty:
            st.line_chart(dff.set_index("month")["delinquency_rate"])
