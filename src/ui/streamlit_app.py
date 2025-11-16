import time
from itertools import chain

import pandas as pd
import streamlit as st

from algorithms.apriori import apriori, generate_rules
from algorithms.eclat import eclat
from preprocessing.cleaner import (
    normalize_item,
    safe_read_csv,
    preprocess_transactions,
)

TX_PATH = "./data/sample_transactions.csv"
PROD_PATH = "./data/products.csv"

def set_style():
    st.markdown("""
        <style>
        /* Sidebar container */
        section[data-testid="stSidebar"] {
            color: #C73C20;
            text-align: center;
            background-color: #9CE6E6;
            background-image: linear-gradient(120deg, #33CCCC, #2AA7A7);
            border-right: 1px solid rgba(27,31,35,0.1);  
        }
        section[data-testid="stSidebar"] label {color: white;}
        section[data-testid="stSidebar"] h2 {
            color: white !important;
            text-align: left !important;
        }

        /* Buttons */
        .stButton > button {
            color: white;
            background-color: #D55858;
            border: none;
            border-radius: 9999px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
        }
        .stButton > button:hover {
            background-color: #D55858;
            background-image: linear-gradient(90deg, #D55858, #A72A2A);
            transform: scale(1.02);
        }

        /* Title gradient */
        .header {
            text-align: center;
            padding: 1rem 1rem;
            font-size: 2rem;             
            font-weight: 800;
            background: linear-gradient(90deg, #D55858, #A72A2A); 
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        </style>
    """, unsafe_allow_html=True)

def load_products():
    prod_df_raw = safe_read_csv(PROD_PATH)
    if prod_df_raw.empty:
        st.warning(f"No products file found at: {PROD_PATH}. Continuing without validation.")
        product_names = [
            'milk','bread','eggs','butter','cheese','apples','bananas','cereal','coffee','tea',
            'yogurt','juice','chicken','beef','rice','pasta','tomato','onion','lettuce','cookies'
        ]
        return prod_df_raw, product_names

    cols = [c.lower() for c in prod_df_raw.columns]
    prod_df_raw.columns = cols

    # Prefer 'product_name', fall back to 'name', then last column if needed
    if 'product_name' in cols:
        name_col = 'product_name'
    elif 'name' in cols:
        name_col = 'name'
    else:
        name_col = cols[-1]

    product_names = sorted(
        {normalize_item(x) for x in prod_df_raw[name_col].astype(str) if normalize_item(x)}
    )
    return prod_df_raw, product_names

def choose_transactions_source(uploaded_file):
    if uploaded_file is not None:
        try:
            tx_df_raw = pd.read_csv(uploaded_file)
            st.sidebar.success(f"Using uploaded file with {len(tx_df_raw)} rows.")
        except Exception as e:
            st.sidebar.error(f"Error reading uploaded file: {e}")
            tx_df_raw = safe_read_csv(TX_PATH)
    else:
        tx_df_raw = safe_read_csv(TX_PATH)
    return tx_df_raw

def run_app():
    # Page config MUST be first Streamlit call
    st.set_page_config(page_title="Supermarket Miner", page_icon="🛒", layout="wide")
    set_style()

    st.markdown(
        '<div class="header"><h1>Interactive Supermarket Simulator</h1>'
        '<p>Association Rule Mining</p></div>',
        unsafe_allow_html=True
    )

    # Load products
    prod_df_raw, product_names = load_products()

    # Sidebar controls
    st.sidebar.header("Custom Transactions File")
    uploaded_file = st.sidebar.file_uploader("upload your own csv file", type=["csv"])

    st.sidebar.header("Mining Parameters")
    min_support = st.sidebar.slider("Minimum Support", 0.05, 0.9, 0.2, 0.05)
    min_conf = st.sidebar.slider("Minimum Confidence", 0.05, 0.95, 0.5, 0.05)

    # Session state
    if 'manual_txs' not in st.session_state:
        st.session_state.manual_txs = []
    if 'cleaned' not in st.session_state:
        st.session_state.cleaned = None
        st.session_state.report = None
    if 'results' not in st.session_state:
        st.session_state.results = {}

    # Choose tx source
    tx_df_raw = choose_transactions_source(uploaded_file)

    if tx_df_raw.empty:
        st.error(f"Could not load transactions from upload or default path: {TX_PATH}")
        st.stop()

    # ------------------------------
    # 1) Create Transactions Manually
    st.subheader("Create Transactions Manually")
    col1, col2 = st.columns([2, 1])
    with col1:
        sel = st.multiselect(
            "Select products to add as a transaction:",
            options=product_names,
            key="picker"
        )
        add = st.button("➕ Add Transaction", type="primary")
        if add and sel:
            norm = [normalize_item(x) for x in sel if normalize_item(x)]
            norm = sorted(set(norm))
            if len(norm) > 1:
                st.session_state.manual_txs.append(norm)
            else:
                st.warning("Single-item transactions are ignored for mining.")
    with col2:
        if st.button("Clear Manual Transactions"):
            st.session_state.manual_txs = []

    # ------------------------------
    # 2) Imported Transactions
    st.subheader("Imported Transactions")
    st.dataframe(tx_df_raw.head(200), use_container_width=True)

    # Combine imported + manual for preprocessing
    combined_df = tx_df_raw.copy()
    if st.session_state.manual_txs:
        extra = pd.DataFrame({'items': [", ".join(t) for t in st.session_state.manual_txs]})
        if 'items' in combined_df.columns:
            combined_df = pd.concat([combined_df[['items']], extra], ignore_index=True)
        else:
            combined_df = extra

    run_prep = st.button("Preprocess")
    if run_prep:
        cleaned, report = preprocess_transactions(combined_df, prod_df_raw)
        st.session_state.cleaned = [set(t) for t in cleaned]
        st.session_state.report = report

    if st.session_state.cleaned is not None:
        st.success("Preprocessing complete.")
        with st.expander("Preprocessing Report", expanded=True):
            r = st.session_state.report
            left, right = st.columns(2)
            with left:
                st.metric("Total transactions (before)", r['before_total_tx'])
                st.metric("Empty transactions removed", r['empty_tx_removed'])
                st.metric("Single-item tx removed", r['single_item_tx_removed'])
            with right:
                st.metric("Duplicate items removed", r['duplicate_items_removed'])
                st.metric("Invalid items removed", r['invalid_items_removed'])
                st.metric("Valid transactions (after)", r['after_valid_tx'])
            st.caption(
                f"Total items: {r['total_items']} • "
                f"Unique products: {r['unique_products']}"
            )

        st.subheader("Cleaned Transactions")
        sample = [' , '.join(sorted(t)) for t in st.session_state.cleaned[:25]]
        st.dataframe(
            pd.DataFrame({'transaction': sample}),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # ------------------------------
    # 3) Run Mining (Apriori & Eclat)
    st.subheader("Data Mine (Apriori & Eclat)")
    run_mining = st.button("Analyze")

    if run_mining:
        if not st.session_state.cleaned:
            st.error("Please run preprocessing first (and ensure you have at least 2-item transactions).")
        else:
            tx = [set(t) for t in st.session_state.cleaned]
            # Apriori
            t0 = time.perf_counter()
            L_ap = apriori(tx, min_support=min_support)
            rules_ap = generate_rules(L_ap, min_conf=min_conf, n_tx=len(tx))
            t1 = time.perf_counter()
            # Eclat
            t2 = time.perf_counter()
            L_ec = eclat(tx, min_support=min_support)
            rules_ec = generate_rules(L_ec, min_conf=min_conf, n_tx=len(tx))
            t3 = time.perf_counter()

            st.session_state.results = {
                'apriori': {
                    'freq': L_ap,
                    'rules': rules_ap,
                    'runtime_ms': (t1 - t0) * 1000
                },
                'eclat': {
                    'freq': L_ec,
                    'rules': rules_ec,
                    'runtime_ms': (t3 - t2) * 1000
                },
                'n_tx': len(tx)
            }

    if st.session_state.get('results'):
        res = st.session_state.results
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Apriori**")
            st.write(f"Runtime: {res['apriori']['runtime_ms']:.1f} ms")
            st.write(f"Rules generated: {len(res['apriori']['rules'])}")
        with c2:
            st.markdown("**Eclat**")
            st.write(f"Runtime: {res['eclat']['runtime_ms']:.1f} ms")
            st.write(f"Rules generated: {len(res['eclat']['rules'])}")

        # Display rules (toggle technical)
        with st.expander("Show technical rules (Apriori)"):
            st.dataframe(pd.DataFrame(res['apriori']['rules']), use_container_width=True)
        with st.expander("Show technical rules (Eclat)"):
            st.dataframe(pd.DataFrame(res['eclat']['rules']), use_container_width=True)

        st.subheader("Query Recommendations")
        if res['apriori']['freq'] and res['apriori']['freq'].get(1, {}):
            one_item_sets = list(res['apriori']['freq'][1].keys())
            all_items = sorted(set(chain.from_iterable([list(s) for s in one_item_sets])))
        else:
            all_items = product_names
        picked = st.selectbox("Pick a product to see associated items:", options=all_items)

        def recommendations_for(item, rules):
            agg = {}
            for r in rules:
                if item in r['antecedent']:
                    for c in r['consequent']:
                        best = agg.get(c)
                        score = r['confidence']
                        if best is None or score > best['confidence']:
                            agg[c] = {
                                'confidence': score,
                                'support': r['support'],
                                'lift': r['lift']
                            }
            out = [
                {
                    'item': k,
                    'confidence_pct': v['confidence'] * 100,
                    'support_pct': v['support'] * 100,
                    'lift': v['lift']
                }
                for k, v in agg.items()
            ]
            out.sort(key=lambda x: (x['confidence_pct'], x['lift']), reverse=True)
            return out

        if picked:
            ap_recs = recommendations_for(picked, res['apriori']['rules'])
            ec_recs = recommendations_for(picked, res['eclat']['rules'])
            tab1, tab2 = st.tabs(["Apriori", "Eclat"])
            with tab1:
                if ap_recs:
                    df = pd.DataFrame(ap_recs)
                    df['strength'] = pd.cut(
                        df['confidence_pct'],
                        bins=[0, 40, 70, 100],
                        labels=["Weak", "Moderate", "Strong"],
                        include_lowest=True
                    )
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.write(
                        f"**Recommendation:** Consider bundling **{picked}** "
                        f"with the top 1–2 items above."
                    )
                else:
                    st.info("No associations found for this item at current thresholds.")
            with tab2:
                if ec_recs:
                    df = pd.DataFrame(ec_recs)
                    df['strength'] = pd.cut(
                        df['confidence_pct'],
                        bins=[0, 40, 70, 100],
                        labels=["Weak", "Moderate", "Strong"],
                        include_lowest=True
                    )
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.write(
                        f"**Recommendation:** Consider placement and promotions "
                        f"pairing **{picked}** with the top items."
                    )
                else:
                    st.info("No associations found for this item at current thresholds.")
