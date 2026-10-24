# -*- coding: utf-8 -*-
"""D1 · 数据底座构建：加载 6 附件 -> 长表 -> data/interim/*.csv + 打印摸底摘要。"""
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.common import io, asof

INTERIM = io.INTERIM_DIR
os.makedirs(INTERIM, exist_ok=True)

data = io.load_attachments()

SAVE = {
    "att1_典型日": "att1",
    "att2_用电量": "att2",
    "att3_预测信息": "att3_forecast",
    "att3_实际信息": "att3_actual",
    "att4_价格": "att4",
    "att5_合约": "att5",
}

def banner(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)

for name, key in SAVE.items():
    df = data[key]
    df.to_csv(os.path.join(INTERIM, f"{name}.csv"), index=False, encoding="utf-8-sig")
    dmin, dmax = df["date"].min(), df["date"].max()
    ndays = df["date"].nunique()
    print(f"[{name}]  shape={df.shape}  {dmin} ~ {dmax}  天数={ndays}")

# ---- 附件1 典型日 ----
banner("附件1 典型日（问题1 输入）")
att1 = data["att1"]
for d, g in att1.groupby("date"):
    dt = g["day_type"].iloc[0]
    hol = g["holiday"].iloc[0]
    print(f"  {d}  类型={dt}  节假日={hol or '-'}  平均负荷={g['load_actual'].mean():.2f} MWh  平均价差={ (g['price_rt']-g['price_da']).mean():+.2f} 元/MWh")

# ---- 披露延迟核对 ----
banner("披露延迟核对（available_date - date，天数）")
for key, label in [("att2", "附件2 实际用电量"), ("att3_forecast", "附件3 预测信息"),
                   ("att3_actual", "附件3 实际信息"), ("att4", "附件4 价格")]:
    df = data[key]
    lag = (pd.to_datetime(df["available_date"]) - pd.to_datetime(df["date"])).dt.days
    cnt = lag.value_counts().to_dict()
    print(f"  {label}: 延迟分布 {cnt}")

# ---- 信息时间闸门抽查 ----
banner("信息时间闸门抽查（对 2026-04-01 申报，在 2026-03-31 收盘决策）")
snap = asof.availability_snapshot(data, "2026-03-31")
for k, v in snap.items():
    print(f"  可用到 {v}  <- {k}")

print("\n数据底座构建完成，长表已写入 data/interim/")
