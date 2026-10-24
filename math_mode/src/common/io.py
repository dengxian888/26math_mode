# -*- coding: utf-8 -*-
"""M0 数据底座 · 纯标准库读取 .xlsx，并把 6 个附件整理为统一长表。

不依赖 openpyxl / xlrd（本机未安装且无网络）。依赖 pandas（已装）。
统一约定：
  - 数值列一律 float（MWh / 元/MWh / MW / 元）
  - date / available_date 为字符串 'YYYY-MM-DD'
  - hour 为 int(0..23)，由 '时段'（'HH:MM'）解析
"""
import os
import re
import zipfile
from xml.etree import ElementTree as ET

import pandas as pd

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

_HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(_HERE))
RAW_DIR = os.path.join(ROOT, "data", "raw")
INTERIM_DIR = os.path.join(ROOT, "data", "interim")

ATTACHMENTS = {
    "att1": "附件1_典型日完全信息.xlsx",
    "att2": "附件2_用户实际用电量.xlsx",
    "att3": "附件3_市场披露信息.xlsx",
    "att4": "附件4_市场价格.xlsx",
    "att5": "附件5_中长期合约.xlsx",
    "att6": "附件6_结果文件.xlsx",
}

# 清洗后中文表头 -> 英文列名（清洗 = 去掉所有空白字符）
COLUMN_MAP = {
    "日期": "date", "时段": "time",
    "中长期合约电量（MWh）": "contract_q", "中长期合约电量": "contract_q",
    "中长期合约价格（元/MWh）": "contract_p", "中长期合约电价（元/MWh）": "contract_p",
    "实际用电量（MWh）": "load_actual", "实际用电量": "load_actual",
    "日前价格（元/MWh）": "price_da", "日前电价（元/MWh）": "price_da",
    "实时价格（元/MWh）": "price_rt", "实时电价（元/MWh）": "price_rt",
    "可获得日期": "available_date",
    "星期": "weekday", "日期类型": "day_type", "节假日名称": "holiday",
    "统调负荷（MW）": "load_total", "省内A类电源（MW）": "gen_A",
    "省内B类电源（MW）": "gen_B", "地方电源出力（MW）": "gen_local",
    "粤港联络线（MW）": "tie_yuegang", "地方风电（MW）": "wind",
    "地方光伏（MW）": "pv", "地方火电（MW）": "thermal", "地方水电（MW）": "hydro",
    "发电总出力（MW）": "gen_total", "新能源总出力（MW）": "renew_total",
    "水电含抽蓄总出力（MW）": "hydro_total", "正备用（MW）": "reserve_up",
    "负备用（MW）": "reserve_down",
}


def _clean(s):
    return re.sub(r"\s+", "", str(s))


def _col_index(letters):
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _cell_value(c, shared):
    t = c.get("t")
    v = c.find(NS + "v")
    is_ = c.find(NS + "is")
    if t == "s" and v is not None:
        return shared[int(v.text)]
    if is_ is not None:
        return "".join(t.text or "" for t in is_.iter(NS + "t"))
    if t == "inlineStr":
        return "".join(t.text or "" for t in c.iter(NS + "t"))
    if t == "str" and v is not None:
        return v.text
    if t == "b" and v is not None:
        return v.text == "1"
    if v is not None:
        try:
            return float(v.text)
        except (TypeError, ValueError):
            return v.text
    return None


def read_sheet(path, sheet_index=0):
    """读取一个 sheet，返回按列字母对齐的 list[list[value]]（首行为表头）。"""
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in sst.findall(NS + "si"):
            shared.append("".join(t.text or "" for t in si.iter(NS + "t")))
    names = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
    ws = ET.fromstring(z.read(names[sheet_index]))
    raw_rows = []
    max_col = 0
    for row in ws.iter(NS + "row"):
        cells = {}
        for c in row.findall(NS + "c"):
            ref = c.get("r")
            letters = re.match(r"[A-Z]+", ref).group(0)
            idx = _col_index(letters)
            cells[idx] = _cell_value(c, shared)
            max_col = max(max_col, idx)
        raw_rows.append(cells)
    out = []
    for cells in raw_rows:
        out.append([cells.get(i) for i in range(max_col + 1)])
    return out


def read_xlsx(path, skip_title_rows=0):
    """读取 xlsx 全部 sheet，返回 {sheet_name: DataFrame}。"""
    z = zipfile.ZipFile(path)
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    relmap = {r.get("Id"): r.get("Target") for r in rels}
    sheet_names = []
    for sh in wb.iter(NS + "sheet"):
        sheet_names.append(sh.get("name"))
    result = {}
    for i, name in enumerate(sheet_names):
        rows = read_sheet(path, i)
        if not rows:
            result[name] = pd.DataFrame()
            continue
        header = [_clean(str(x)) for x in rows[skip_title_rows]]
        body = rows[skip_title_rows + 1:]
        df = pd.DataFrame(body, columns=header)
        result[name] = df
    return result


def _finalize(df, keep_cols):
    """中文表头 -> 英文，加 hour，转 date 为字符串。keep_cols: 英文列名白名单。"""
    df = df.copy()
    df.columns = [_clean(c) for c in df.columns]
    df = df.rename(columns=COLUMN_MAP)
    if "time" in df.columns:
        df["hour"] = df["time"].apply(_to_hour)
    if "date" in df.columns:
        df["date"] = df["date"].astype(str).str[:10]
    if "available_date" in df.columns:
        df["available_date"] = df["available_date"].astype(str).str[:10]
    keep = [c for c in keep_cols if c in df.columns]
    df = df[keep]
    return df.reset_index(drop=True)


def _to_hour(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(round(v * 24)) % 24
    s = str(v)
    if ":" in s:
        try:
            return int(s.split(":")[0])
        except ValueError:
            return None
    return None


def load_attachments():
    """加载 6 个附件，返回规范化长表 dict。"""
    d = {}
    # 附件1 典型日完全信息（5 典型日 × 24 时段）
    d["att1"] = _finalize(
        read_xlsx(os.path.join(RAW_DIR, ATTACHMENTS["att1"]))["典型日数据"],
        ["date", "hour", "contract_q", "contract_p", "load_actual",
         "price_da", "price_rt", "day_type", "holiday"],
    )
    # 附件2 用户实际用电量
    d["att2"] = _finalize(
        read_xlsx(os.path.join(RAW_DIR, ATTACHMENTS["att2"]))["用户用电"],
        ["date", "hour", "load_actual", "available_date", "weekday",
         "day_type", "holiday"],
    )
    # 附件3 市场披露信息（两张 sheet：预测 / 实际）
    att3 = read_xlsx(os.path.join(RAW_DIR, ATTACHMENTS["att3"]))
    cols3 = ["date", "hour", "available_date", "load_total", "gen_A", "gen_B",
             "gen_local", "tie_yuegang", "wind", "pv", "thermal", "hydro",
             "gen_total", "renew_total", "hydro_total", "reserve_up", "reserve_down"]
    d["att3_forecast"] = _finalize(att3["平台披露预测信息"], cols3)
    d["att3_actual"] = _finalize(att3["平台披露实际信息"], cols3)
    # 附件4 市场价格
    d["att4"] = _finalize(
        read_xlsx(os.path.join(RAW_DIR, ATTACHMENTS["att4"]))["市场价格"],
        ["date", "hour", "price_da", "price_rt", "available_date"],
    )
    # 附件5 中长期合约
    d["att5"] = _finalize(
        read_xlsx(os.path.join(RAW_DIR, ATTACHMENTS["att5"]))["中长期合约"],
        ["date", "hour", "contract_q", "contract_p"],
    )
    # 附件6 结果文件模板（保留原始 sheet，供 M6 自动填表使用）
    d["att6"] = read_xlsx(os.path.join(RAW_DIR, ATTACHMENTS["att6"]))
    return d


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    data = load_attachments()
    for k, df in data.items():
        if isinstance(df, dict):
            print(f"{k}: {len(df)} sheets -> {list(df)}")
        else:
            print(f"{k}: {df.shape} cols={list(df.columns)}")
