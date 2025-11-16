from pathlib import Path
from itertools import chain
import pandas as pd

def normalize_item(x: str) -> str:
    """Normalize product names (trim, lowercase, collapse spaces)."""
    if not isinstance(x, str):
        return ""
    return " ".join(x.strip().lower().split())

def safe_read_csv(path_str: str) -> pd.DataFrame:
    """Safely load a CSV file or return empty DataFrame if missing or unreadable."""
    p = Path(path_str)
    if not p.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(p)
    except Exception:
        return pd.DataFrame()

def preprocess_transactions(df: pd.DataFrame, products_df: pd.DataFrame):
    """Perform required cleaning and return cleaned transactions + report dict."""
    if df.shape[1] == 1:
        df = df.copy()
        df.columns = ['items']
    else:
        # heuristics: use last column as items column
        items_col = df.columns[-1]
        df = df[[items_col]].rename(columns={items_col: 'items'})

    before_total = len(df)

    # split comma separated into lists
    tx_lists = []
    for raw in df['items'].astype(str).fillna(""):
        if "," in raw:
            tx_lists.append([normalize_item(x) for x in raw.split(',') if normalize_item(x)])
        else:
            parts = [normalize_item(x) for x in raw.split(' ') if normalize_item(x)]
            tx_lists.append(parts)

    # remove empties
    empty_count = sum(1 for t in tx_lists if len(t) == 0)
    tx_lists = [t for t in tx_lists if len(t) > 0]

    # remove duplicates within each transaction
    dup_instances = 0
    deduped = []
    for t in tx_lists:
        seen = []
        for it in t:
            if it not in seen:
                seen.append(it)
            else:
                dup_instances += 1
        deduped.append(seen)

    # single-item handling: remove
    single_count = sum(1 for t in deduped if len(t) == 1)
    deduped = [t for t in deduped if len(t) > 1]

    # invalid product handling using products_df (if provided)
    invalid_instances = 0
    valid_names = None
    if products_df is not None and not products_df.empty:
        # normalize column names
        cols = [c.lower().strip() for c in products_df.columns]
        products_df.columns = cols

        # Prefer 'product_name', then 'name', then last column
        if 'product_name' in cols:
            name_col = 'product_name'
        elif 'name' in cols:
            name_col = 'name'
        else:
            name_col = cols[-1] if cols else None

        if name_col is not None:
            valid_names = set(
                normalize_item(x) for x in products_df[name_col].astype(str)
            )

    cleaned = []
    for t in deduped:
        if valid_names is None:
            cleaned.append(t)
            continue
        keep = [it for it in t if it in valid_names]
        invalid_instances += len(t) - len(keep)
        if len(keep) > 1:
            cleaned.append(keep)

    after_total = len(cleaned)
    total_items = sum(len(t) for t in cleaned)
    unique_products = len(set(chain.from_iterable(cleaned)))

    report = {
        'before_total_tx': before_total,
        'empty_tx_removed': empty_count,
        'single_item_tx_removed': single_count,
        'duplicate_items_removed': dup_instances,
        'invalid_items_removed': invalid_instances,
        'after_valid_tx': after_total,
        'total_items': total_items,
        'unique_products': unique_products,
    }
    return cleaned, report
