"""ETL: Import all 10 monthly review Excel files into SQLite."""
import sqlite3
import pandas as pd
import os
import re
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = r"D:/1AAAA报告集合/【复盘报】/集团复盘报/【报告用】"
DB_PATH = os.path.join(os.path.dirname(__file__), "data.db")

# All 10 months of data files
FILES = [
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】25年9月复盘会底表2025.9.30.xlsx", "2025-09"),
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】25年10月复盘会底表2025.10.31.xlsx", "2025-10"),
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】25年11月复盘会底表2025.12.9.xlsx", "2025-11"),
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】25年12月复盘会底表2026.1.4.xlsx", "2025-12"),
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】26年1月复盘会底表2026.2.2.xlsx", "2026-01"),
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】26年2月复盘会底表2026.3.2.xlsx", "2026-02"),
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】26年3月复盘会底表2026.4.1.xlsx", "2026-03"),
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】26年4月复盘会底表2026.4.30.xlsx", "2026-04"),
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】26年5月复盘会底表2026.6.2.xlsx", "2026-05"),
    (r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】26年6月复盘会底表2026.7.1.xlsx", "2026-06"),
]


def auto_discover_files(base_dir):
    """Scan directory for new monthly files and infer month label from filename."""
    import re as _re
    pattern = _re.compile(r"【报告用】(\d+)年(\d+)月复盘会底表")
    discovered = []
    if not os.path.isdir(base_dir):
        return discovered
    for f in os.listdir(base_dir):
        if not f.endswith('.xlsx'):
            continue
        m = pattern.search(f)
        if not m:
            continue
        year, month = int(m.group(1)), int(m.group(2))
        if year < 100:
            year += 2000
        # 月份判定：10-12 属于 2025，1-9 属于 2026（与历史数据一致）
        if month >= 10:
            label_year = 2025
        else:
            label_year = 2026
        month_label = f"{label_year}-{month:02d}"
        discovered.append((os.path.join(base_dir, f), month_label))
    return discovered


def find_sheet(sheet_names, *keywords):
    """Find sheet index by keywords (all must match)."""
    for i, name in enumerate(sheet_names):
        name_clean = str(name).replace("\n", "").replace(" ", "").strip()
        if all(k in name_clean for k in keywords):
            return i, name
    return None, None


def clean_col(col):
    """Clean column name: remove newlines, extra spaces."""
    return str(col).replace("\n", "").replace(" ", "").strip() if col else ""


def find_col_idx(df, *keywords):
    """Find column index by keywords (all must match in cleaned name)."""
    for i, c in enumerate(df.columns):
        cn = clean_col(c)
        if all(k in cn for k in keywords):
            return i
    return None


def safe_num(val):
    """Convert to float, return None on failure."""
    if pd.isna(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def import_restaurants(conn, filepath, month):
    """Import restaurant opportunity data from 餐厅机会点底表."""
    xls = pd.ExcelFile(filepath)
    idx, sname = find_sheet(xls.sheet_names, "餐厅", "机会", "底表")
    if idx is None:
        print(f"  [{month}] SKIP: no restaurant sheet")
        return 0

    df = pd.read_excel(filepath, sheet_name=sname)
    cols = [clean_col(c) for c in df.columns]

    rows = []
    for _, row in df.iterrows():
        code = row.iloc[find_col_idx(df, "餐厅编码") or 1] if find_col_idx(df, "餐厅编码") is not None else None
        name = row.iloc[find_col_idx(df, "门店名称") or 2] if find_col_idx(df, "门店名称") is not None else None

        if pd.isna(name) or str(name).strip() == "":
            continue

        record = {
            "月份": month,
            "餐厅编码": str(code) if pd.notna(code) and str(code) != "nan" else None,
            "门店名称": str(name).strip(),
            "战队": str(row.iloc[find_col_idx(df, "战队") or 3]) if find_col_idx(df, "战队") is not None and pd.notna(row.iloc[find_col_idx(df, "战队") or 3]) else None,
            "区域": str(row.iloc[find_col_idx(df, "区域") or 4]) if find_col_idx(df, "区域") is not None and pd.notna(row.iloc[find_col_idx(df, "区域") or 4]) else None,
            "教练": str(row.iloc[find_col_idx(df, "教练") or 5]) if find_col_idx(df, "教练") is not None and pd.notna(row.iloc[find_col_idx(df, "教练") or 5]) else None,
            "城市": str(row.iloc[find_col_idx(df, "城市") or 6]) if find_col_idx(df, "城市") is not None and pd.notna(row.iloc[find_col_idx(df, "城市") or 6]) else None,
            "城市类型": str(row.iloc[find_col_idx(df, "城市类型") or 7]) if find_col_idx(df, "城市类型") is not None and pd.notna(row.iloc[find_col_idx(df, "城市类型") or 7]) else None,
            "商圈类型": str(row.iloc[find_col_idx(df, "商圈类型") or 8]) if find_col_idx(df, "商圈类型") is not None and pd.notna(row.iloc[find_col_idx(df, "商圈类型") or 8]) else None,
            "开业时间": str(row.iloc[find_col_idx(df, "开业时间") or 9])[:10] if find_col_idx(df, "开业时间") is not None and pd.notna(row.iloc[find_col_idx(df, "开业时间") or 9]) else None,
            "堂食日均": safe_num(row.iloc[find_col_idx(df, "堂食日均")]) if find_col_idx(df, "堂食日均") is not None else None,
            "月消费人数": safe_num(row.iloc[find_col_idx(df, "月消费人数")]),
            "人均月频次": safe_num(row.iloc[find_col_idx(df, "人均月频次")]),
            "超会消费占比": safe_num(row.iloc[find_col_idx(df, "超会消费占比")]),
            "好友消费占比": safe_num(row.iloc[find_col_idx(df, "好友消费占比")]),
            "好友新增": safe_num(row.iloc[find_col_idx(df, "好友新增")]),
            "超会售卡": safe_num(row.iloc[find_col_idx(df, "超会售卡")]),
            "周四平均售卡": safe_num(row.iloc[find_col_idx(df, "周四平均售卡")]),
            "超会持卡人数": safe_num(row.iloc[find_col_idx(df, "超会持卡人数")]) if find_col_idx(df, "超会持卡人数") is not None else None,
            "好友现存人数": safe_num(row.iloc[find_col_idx(df, "好友现存人数")]) if find_col_idx(df, "好友现存人数") is not None else None,
        }

        # Find peer averages and opportunity points by scanning columns around metrics
        metric_map = [
            ("月消费人数", "消费人数_同类均值", "机会点_消费人数不足"),
            ("人均月频次", "频次_同类均值", "机会点_人均频次不足"),
            ("超会消费占比", "超会_同类均值", "机会点_超会不足"),
            ("好友消费占比", "好友_同类均值", "机会点_好友拉新不足"),
        ]

        for metric, peer_key, opp_key in metric_map:
            mi = find_col_idx(df, metric)
            if mi is not None:
                # Scan ±3 columns from metric position
                for offset in range(1, 4):
                    if mi + offset < len(cols):
                        cn = cols[mi + offset]
                        if "同类均值" in cn:
                            record[peer_key] = safe_num(row.iloc[mi + offset])
                        if ("机会点" in cn or "不足" in cn) and metric.replace("月", "") in cn:
                            val = row.iloc[mi + offset]
                            record[opp_key] = 1 if val == 1 or val == 1.0 or (isinstance(val, str) and "是" in val) else 0

        rows.append(record)

    # Batch insert
    cursor = conn.cursor()
    field_names = [
        "月份", "餐厅编码", "门店名称", "战队", "区域", "教练", "城市", "城市类型",
        "商圈类型", "开业时间", "堂食日均", "月消费人数", "人均月频次", "超会消费占比",
        "好友消费占比", "好友新增", "超会售卡", "周四平均售卡", "超会持卡人数",
        "好友现存人数", "消费人数_同类均值", "机会点_消费人数不足", "频次_同类均值",
        "机会点_人均频次不足", "超会_同类均值", "机会点_超会不足", "好友_同类均值",
        "机会点_好友拉新不足"
    ]
    placeholders = ", ".join(["?"] * len(field_names))
    sql = f"INSERT INTO restaurants ({', '.join(field_names)}) VALUES ({placeholders})"
    values = [[r.get(f) for f in field_names] for r in rows]
    cursor.executemany(sql, values)
    conn.commit()
    return len(rows)


def import_city_new_old(conn, filepath, month):
    """Import city-level new/old customer analysis."""
    xls = pd.ExcelFile(filepath)
    idx, sname = find_sheet(xls.sheet_names, "新老客分析")
    if idx is None:
        # Try alternative name patterns
        idx, sname = find_sheet(xls.sheet_names, "新老客")
    if idx is None:
        return 0

    df = pd.read_excel(filepath, sheet_name=sname)
    cols = [clean_col(c) for c in df.columns]

    # Find key column indices
    city_idx = find_col_idx(df, "门店城市")
    if city_idx is None:
        city_idx = find_col_idx(df, "城市")

    rows = []
    for _, row in df.iterrows():
        city = row.iloc[city_idx] if city_idx is not None else None
        if pd.isna(city) or str(city).strip() == "":
            # Maybe this is a data row where city name is in first column
            city = row.iloc[0]
        if pd.isna(city) or str(city).strip() in ["", "nan"]:
            continue

        record = {
            "月份": month,
            "城市": str(city).strip(),
            "堂食日均": safe_num(row.iloc[find_col_idx(df, "堂食日均")]) if find_col_idx(df, "堂食日均") is not None else None,
            "分析餐厅数": safe_num(row.iloc[find_col_idx(df, "分析餐厅数")]),
            "店均顾客数": safe_num(row.iloc[find_col_idx(df, "店均顾客")]),
            "新客数": safe_num(row.iloc[find_col_idx(df, "新客数")]),
            "活跃客数": safe_num(row.iloc[find_col_idx(df, "活跃客")]),
            "回流客数": safe_num(row.iloc[find_col_idx(df, "回流客数")]) if find_col_idx(df, "回流客数") is not None else safe_num(row.iloc[find_col_idx(df, "回流客")]),
            "新客复购率": safe_num(row.iloc[find_col_idx(df, "新客", "复购率")]),
            "老客回流率": safe_num(row.iloc[find_col_idx(df, "老客", "回流率")]),
            "流失客总数": safe_num(row.iloc[find_col_idx(df, "流失客总数")]),
            "回流客总数": safe_num(row.iloc[find_col_idx(df, "回流客总数")]) if find_col_idx(df, "回流客总数") is not None else None,
            "月消费频次": safe_num(row.iloc[find_col_idx(df, "月消费频次")]) if find_col_idx(df, "月消费频次") is not None else safe_num(row.iloc[find_col_idx(df, "消费频次")]),
            "新客人均频次": safe_num(row.iloc[find_col_idx(df, "新客人均频次")]),
            "老客人均频次": safe_num(row.iloc[find_col_idx(df, "老客人均频次")]),
            "单均实收": safe_num(row.iloc[find_col_idx(df, "单均实收")]),
            "新客单均实收": safe_num(row.iloc[find_col_idx(df, "新客单均实收")]),
            "老客单均实收": safe_num(row.iloc[find_col_idx(df, "老客单均实收")]),
            "付占比": safe_num(row.iloc[find_col_idx(df, "付占比")]),
            "友占比": safe_num(row.iloc[find_col_idx(df, "友占比")]),
            "城市店均售卡": safe_num(row.iloc[find_col_idx(df, "店均售卡")]) if find_col_idx(df, "店均售卡") is not None else None,
        }
        rows.append(record)

    if rows:
        field_names = list(rows[0].keys())
        placeholders = ", ".join(["?"] * len(field_names))
        sql = f"INSERT INTO city_new_old ({', '.join(field_names)}) VALUES ({placeholders})"
        conn.executemany(sql, [[r.get(f) for f in field_names] for r in rows])
        conn.commit()
    return len(rows)


def import_city_dinein(conn, filepath, month):
    """Import city dine-in daily revenue."""
    xls = pd.ExcelFile(filepath)
    idx, sname = find_sheet(xls.sheet_names, "城市堂食")
    if idx is None:
        return 0

    df = pd.read_excel(filepath, sheet_name=sname)

    rows = []
    for _, row in df.iterrows():
        city = row.iloc[0]
        if pd.isna(city) or str(city).strip() in ["", "nan"]:
            continue

        record = {
            "月份": month,
            "城市": str(city).strip(),
            "单店日均堂食实收": safe_num(row.iloc[1]) if len(row) > 1 else None,
            "门店数": safe_num(row.iloc[2]) if len(row) > 2 else None,
        }
        rows.append(record)

    if rows:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO city_dinein (月份, 城市, 单店日均堂食实收, 门店数) VALUES (?, ?, ?, ?)",
            [[r["月份"], r["城市"], r["单店日均堂食实收"], r["门店数"]] for r in rows]
        )
        conn.commit()
    return len(rows)


def import_city_lost(conn, filepath, month):
    """Import lost customers by city."""
    xls = pd.ExcelFile(filepath)
    idx, sname = find_sheet(xls.sheet_names, "流失客")
    if idx is None:
        return 0

    df = pd.read_excel(filepath, sheet_name=sname)

    rows = []
    for _, row in df.iterrows():
        label = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else None
        users = safe_num(row.iloc[1])

        if not label or users is None:
            continue
        if label == "nan":
            continue

        record = {
            "月份": month,
            "城市": label,
            "流失客数": users,
        }
        rows.append(record)

    if rows:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO city_lost (月份, 城市, 流失客数) VALUES (?, ?, ?)",
            [[r["月份"], r["城市"], r["流失客数"]] for r in rows]
        )
        conn.commit()
    return len(rows)


def import_city_returning(conn, filepath, month):
    """Import returning customers by city."""
    xls = pd.ExcelFile(filepath)
    idx, sname = find_sheet(xls.sheet_names, "回流客")
    if idx is None:
        return 0

    df = pd.read_excel(filepath, sheet_name=sname)
    cols = [clean_col(c) for c in df.columns]

    city_idx = find_col_idx(df, "城市")
    if city_idx is None:
        return 0

    rows = []
    for _, row in df.iterrows():
        city = str(row.iloc[city_idx]).strip() if pd.notna(row.iloc[city_idx]) else None
        if not city or city == "nan":
            continue

        record = {
            "月份": month,
            "城市": city,
            "新客数": safe_num(row.iloc[find_col_idx(df, "新客数")]),
            "回流老客": safe_num(row.iloc[find_col_idx(df, "回流老客")]),
            "顾客总数": safe_num(row.iloc[find_col_idx(df, "顾客总数")]),
            "店均新客数": safe_num(row.iloc[find_col_idx(df, "店均新客")]),
            "店均回流老客": safe_num(row.iloc[find_col_idx(df, "店均回流老客")]),
            "店均顾客": safe_num(row.iloc[find_col_idx(df, "店均顾客")]),
        }
        rows.append(record)

    if rows:
        field_names = list(rows[0].keys())
        placeholders = ", ".join(["?"] * len(field_names))
        sql = f"INSERT INTO city_returning ({', '.join(field_names)}) VALUES ({placeholders})"
        conn.executemany(sql, [[r.get(f) for f in field_names] for r in rows])
        conn.commit()
    return len(rows)


def import_team_stats(conn, filepath, month):
    """Import team-level metrics."""
    xls = pd.ExcelFile(filepath)
    idx, sname = find_sheet(xls.sheet_names, "战队", "人频价")
    if idx is None:
        return 0

    df = pd.read_excel(filepath, sheet_name=sname)
    cols = [clean_col(c) for c in df.columns]

    rows = []
    for _, row in df.iterrows():
        team = row.iloc[0]
        if pd.isna(team) or str(team).strip() in ["", "nan"]:
            continue

        record = {
            "月份": month,
            "战队": str(team).strip(),
            "门店数": safe_num(row.iloc[1]) if len(row) > 1 else None,
            "月消费人数": safe_num(row.iloc[find_col_idx(df, "月消费人数")]) if find_col_idx(df, "月消费人数") is not None else safe_num(row.iloc[2]) if len(row) > 2 else None,
            "人均月频次": safe_num(row.iloc[find_col_idx(df, "人均月频次")]) if find_col_idx(df, "人均月频次") is not None else None,
            "单均实收": safe_num(row.iloc[find_col_idx(df, "单均实收")]) if find_col_idx(df, "单均实收") is not None else None,
        }
        rows.append(record)

    if rows:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO team_stats (月份, 战队, 门店数, 月消费人数, 人均月频次, 单均实收) VALUES (?, ?, ?, ?, ?, ?)",
            [[r["月份"], r["战队"], r["门店数"], r["月消费人数"], r["人均月频次"], r["单均实收"]] for r in rows]
        )
        conn.commit()
    return len(rows)


def create_tables(conn):
    """Create all tables."""
    conn.execute("DROP TABLE IF EXISTS restaurants")
    conn.execute("DROP TABLE IF EXISTS city_new_old")
    conn.execute("DROP TABLE IF EXISTS city_dinein")
    conn.execute("DROP TABLE IF EXISTS city_lost")
    conn.execute("DROP TABLE IF EXISTS city_returning")
    conn.execute("DROP TABLE IF EXISTS team_stats")
    conn.execute("DROP TABLE IF EXISTS city_stats")

    conn.execute("""
        CREATE TABLE restaurants (
            月份 TEXT,
            餐厅编码 TEXT,
            门店名称 TEXT,
            战队 TEXT,
            区域 TEXT,
            教练 TEXT,
            城市 TEXT,
            城市类型 TEXT,
            商圈类型 TEXT,
            开业时间 TEXT,
            堂食日均 REAL,
            月消费人数 REAL,
            人均月频次 REAL,
            超会消费占比 REAL,
            好友消费占比 REAL,
            好友新增 REAL,
            超会售卡 REAL,
            周四平均售卡 REAL,
            超会持卡人数 REAL,
            好友现存人数 REAL,
            消费人数_同类均值 REAL,
            机会点_消费人数不足 INTEGER DEFAULT 0,
            频次_同类均值 REAL,
            机会点_人均频次不足 INTEGER DEFAULT 0,
            超会_同类均值 REAL,
            机会点_超会不足 INTEGER DEFAULT 0,
            好友_同类均值 REAL,
            机会点_好友拉新不足 INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
        CREATE TABLE city_new_old (
            月份 TEXT,
            城市 TEXT,
            堂食日均 REAL,
            分析餐厅数 REAL,
            店均顾客数 REAL,
            新客数 REAL,
            活跃客数 REAL,
            回流客数 REAL,
            新客复购率 REAL,
            老客回流率 REAL,
            流失客总数 REAL,
            回流客总数 REAL,
            月消费频次 REAL,
            新客人均频次 REAL,
            老客人均频次 REAL,
            单均实收 REAL,
            新客单均实收 REAL,
            老客单均实收 REAL,
            付占比 REAL,
            友占比 REAL,
            城市店均售卡 REAL
        )
    """)

    conn.execute("""
        CREATE TABLE city_dinein (
            月份 TEXT,
            城市 TEXT,
            单店日均堂食实收 REAL,
            门店数 REAL
        )
    """)

    conn.execute("""
        CREATE TABLE city_lost (
            月份 TEXT,
            城市 TEXT,
            流失客数 REAL
        )
    """)

    conn.execute("""
        CREATE TABLE city_returning (
            月份 TEXT,
            城市 TEXT,
            新客数 REAL,
            回流老客 REAL,
            顾客总数 REAL,
            店均新客数 REAL,
            店均回流老客 REAL,
            店均顾客 REAL
        )
    """)

    conn.execute("""
        CREATE TABLE team_stats (
            月份 TEXT,
            战队 TEXT,
            门店数 REAL,
            月消费人数 REAL,
            人均月频次 REAL,
            单均实收 REAL
        )
    """)

    # Old table for compatibility
    conn.execute("""
        CREATE TABLE city_stats (
            月份 TEXT,
            城市 TEXT,
            月消费人数 REAL,
            单店日均堂食实收 REAL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            role TEXT DEFAULT 'user',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()


def create_indexes(conn):
    """Create performance indexes."""
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rest_store ON restaurants(门店名称)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rest_code ON restaurants(餐厅编码)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rest_month ON restaurants(月份)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rest_city ON restaurants(城市)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_rest_team ON restaurants(战队)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cno_month ON city_new_old(月份)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cno_city ON city_new_old(城市)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cdi_month ON city_dinein(月份)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cl_month ON city_lost(月份)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cr_month ON city_returning(月份)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ts_month ON team_stats(月份)")
    conn.commit()


def main():
    """Run full ETL pipeline."""
    print("=" * 60)
    print("ICU餐厅会员看板 - ETL 数据导入")
    print("=" * 60)

    # 自动扫描：合并内置列表 + 新发现的文件
    base = r"D:\1AAAA报告集合\【复盘报】\集团复盘报\【报告用】"
    all_files = list(FILES) + auto_discover_files(base)
    # 去重（按月标签保留最后出现的）
    seen = {}
    for fp, m in all_files:
        seen[m] = fp
    all_files = sorted(seen.items())
    print(f"待处理文件: {len(all_files)} 个\n")

    conn = sqlite3.connect(DB_PATH)
    create_tables(conn)

    total_restaurants = 0
    total_city_no = 0
    total_city_di = 0
    total_city_lost = 0
    total_city_ret = 0
    total_team = 0

    for month, filepath in all_files:
        fname = os.path.basename(filepath)
        if not os.path.exists(filepath):
            print(f"\n[{month}] SKIP: file not found: {fname}")
            continue

        print(f"\n[{month}] Processing: {fname}")

        n = import_restaurants(conn, filepath, month)
        print(f"  restaurants: {n} rows")
        total_restaurants += n

        n = import_city_new_old(conn, filepath, month)
        print(f"  city_new_old: {n} rows")
        total_city_no += n

        n = import_city_dinein(conn, filepath, month)
        print(f"  city_dinein: {n} rows")
        total_city_di += n

        n = import_city_lost(conn, filepath, month)
        print(f"  city_lost: {n} rows")
        total_city_lost += n

        n = import_city_returning(conn, filepath, month)
        print(f"  city_returning: {n} rows")
        total_city_ret += n

        n = import_team_stats(conn, filepath, month)
        print(f"  team_stats: {n} rows")
        total_team += n

        # Also populate city_stats compatibility table
        conn.execute("""
            INSERT INTO city_stats (月份, 城市, 月消费人数)
            SELECT 月份, 城市, 月消费人数 FROM restaurants WHERE 月份 = ?
            ON CONFLICT DO NOTHING
        """, (month,))
        conn.commit()

    # Populate city_stats dinein data from city_new_old
    conn.execute("""
        UPDATE city_stats SET 单店日均堂食实收 = (
            SELECT 堂食日均 FROM city_new_old
            WHERE city_new_old.城市 = city_stats.城市 AND city_new_old.月份 = city_stats.月份
        )
    """)
    conn.commit()

    create_indexes(conn)

    # Add admin user
    import bcrypt
    hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, display_name, role) VALUES (?, ?, ?, ?)",
        ("admin", hashed, "管理员", "admin")
    )
    conn.commit()

    # Summary
    store_count = conn.execute("SELECT COUNT(DISTINCT 门店名称) FROM restaurants").fetchone()[0]
    city_count = conn.execute("SELECT COUNT(DISTINCT 城市) FROM restaurants WHERE 城市 IS NOT NULL").fetchone()[0]
    month_count = conn.execute("SELECT COUNT(DISTINCT 月份) FROM restaurants").fetchone()[0]

    print(f"\n{'=' * 60}")
    print(f"ETL Complete!")
    print(f"  restaurants:     {total_restaurants} records")
    print(f"  city_new_old:    {total_city_no} records")
    print(f"  city_dinein:     {total_city_di} records")
    print(f"  city_lost:       {total_city_lost} records")
    print(f"  city_returning:  {total_city_ret} records")
    print(f"  team_stats:      {total_team} records")
    print(f"  ---")
    print(f"  Unique Stores:   {store_count}")
    print(f"  Unique Cities:   {city_count}")
    print(f"  Months:          {month_count}")
    print(f"  Database:        {DB_PATH}")
    print(f"{'=' * 60}")

    conn.close()


if __name__ == "__main__":
    main()
