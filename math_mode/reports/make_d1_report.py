# -*- coding: utf-8 -*-
"""D1 · 数据摸底报告（EDA）：生成 2 张图 + reports/D1_数据摸底报告.md。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np

from src.common import io, asof

# ---- 中文字体 ----
cands = ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "SimSun"]
avail = {f.name for f in fm.fontManager.ttflist}
font = next((c for c in cands if c in avail), None)
if font is None:
    for p in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
        if os.path.exists(p):
            fm.fontManager.addfont(p)
            font = fm.FontProperties(fname=p).get_name()
            break
plt.rcParams["font.sans-serif"] = [font, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

FIG = os.path.join(io.ROOT, "outputs", "figures")
REPORT = os.path.join(io.ROOT, "reports", "D1_数据摸底报告.md")
os.makedirs(FIG, exist_ok=True)

data = io.load_attachments()
att1, att2, att4 = data["att1"], data["att2"], data["att4"]
att3f, att3a = data["att3_forecast"], data["att3_actual"]

# ================= 图 1：典型日负荷 + 典型日价格 =================
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), dpi=150)
colors = plt.cm.tab10.colors
ax = axes[0]
for i, (d, g) in enumerate(att1.groupby("date")):
    ax.plot(g["hour"], g["load_actual"], marker="o", ms=3.5, lw=1.6,
            color=colors[i], label=f"{d} ({g['day_type'].iloc[0]})")
ax.set_xlabel("时段 (hour)")
ax.set_ylabel("实际用电量 (MWh)")
ax.set_title("附件1 · 五个典型日 24 时段负荷曲线")
ax.legend(fontsize=8, loc="upper left")
ax.grid(alpha=0.3)

ax = axes[1]
d = "2026-04-07"
g = att1[att1["date"] == d]
ax.plot(g["hour"], g["price_da"], marker="o", ms=3.5, lw=1.6, label="日前价格 P_DA")
ax.plot(g["hour"], g["price_rt"], marker="s", ms=3.5, lw=1.6, label="实时价格 P_RT")
ax.plot(g["hour"], g["contract_p"], ls="--", lw=1.4, color="gray", label="合约价格 P_C")
ax.set_xlabel("时段 (hour)")
ax.set_ylabel("价格 (元/MWh)")
ax.set_title(f"附件1 · {d} 日前/实时/合约价格")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "D1_典型日负荷与价格.png"), bbox_inches="tight")
plt.close()

# ================= 图 2：价格与价差分布（1-8月） =================
fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), dpi=150)
att4 = att4.copy()
att4["d"] = pd.to_datetime(att4["date"])
att4["spread"] = att4["price_rt"] - att4["price_da"]
daily = att4.groupby("date").agg(da=("price_da", "mean"), rt=("price_rt", "mean")).reset_index()
ax = axes[0]
ax.plot(pd.to_datetime(daily["date"]), daily["da"], lw=0.9, label="日均日前价格")
ax.plot(pd.to_datetime(daily["date"]), daily["rt"], lw=0.9, alpha=0.8, label="日均实时价格")
ax.set_xlabel("日期")
ax.set_ylabel("均价 (元/MWh)")
ax.set_title("附件4 · 2026 年 1–8 月日前/实时日均价")
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

ax = axes[1]
sp = att4["spread"]
ax.hist(sp, bins=120, color="#4C72B0", alpha=0.85)
ax.axvline(0, color="r", lw=1.2, ls="--")
ax.set_xlabel("价差 S = P_RT − P_DA (元/MWh)")
ax.set_ylabel("频次")
ax.set_title(f"价差分布（{len(sp)} 个时段，均值 {sp.mean():+.1f}，σ {sp.std():.1f}）")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "D1_价格与价差分布.png"), bbox_inches="tight")
plt.close()

# ================= 统计摘要 =================
sp = att4["spread"]
summary = {
    "load_mean": att2["load_actual"].mean(),
    "load_std": att2["load_actual"].std(),
    "da_mean": att4["price_da"].mean(),
    "rt_mean": att4["price_rt"].mean(),
    "spread_mean": sp.mean(),
    "spread_std": sp.std(),
    "spread_pos_ratio": (sp > 0).mean(),
    "contract_p_unique": data["att5"]["contract_p"].nunique(),
    "contract_p_mean": data["att5"]["contract_p"].mean(),
}

# 结算基线：附件1 五个典型日 q=合约量
baseline = []
for d, g in att1.groupby("date"):
    qc = g["contract_q"].to_numpy(); pc = g["contract_p"].to_numpy()
    L = g["load_actual"].to_numpy(); p_da = g["price_da"].to_numpy(); p_rt = g["price_rt"].to_numpy()
    from src.common import settle
    out = settle.settle_day(qc, L, p_da, p_rt, qc, pc)
    baseline.append((d, out["sums"]["total"], out["sums"]["recovery"], out["sums"]["rt_dev"]))

# ================= 报告 =================
L = []
L.append("# D1 数据摸底报告（EDA）\n")
L.append("> 生成时间：2026-10-24（D1 地基阶段） · 数据源：`data/raw/` 6 个附件 · 长表：`data/interim/`\n")

L.append("## 1. 数据总览\n")
L.append("| 附件 | 行数 | 日期范围 | 天数 | 关键列 |")
L.append("|---|---|---|---|---|")
L.append(f"| 附件1 典型日完全信息 | {len(att1)} | 2026-04-07 ~ 06-19 | 5 | 合约电量/价、实际负荷、日前/实时价、日期类型 |")
L.append(f"| 附件2 用户实际用电量 | {len(att2)} | 2026-01-01 ~ 08-31 | 243 | 实际负荷、可获得日期、星期/日期类型/节假日 |")
L.append(f"| 附件3 平台披露预测/实际信息 | {len(att3f)}×2 | 2026-01-01 ~ 08-31 | 243 | 统调负荷、A/B 类电源、风电/光伏/火电/水电、正负备用等 14 项 |")
L.append(f"| 附件4 市场价格 | {len(att4)} | 2026-01-01 ~ 08-31 | 243 | 日前价、实时价、可获得日期 |")
L.append(f"| 附件5 中长期合约 | {len(data['att5'])} | 2026-01-01 ~ 08-31 | 243 | 合约电量、合约电价 |")
L.append(f"| 附件6 结果文件 | 模板 | 4-1 ~ 8-31（153 天） | — | 各问填写模板（M6 自动填充） |")

L.append("\n## 2. 披露延迟（信息可得时间，本题核心约束）\n")
L.append("| 数据源 | 延迟 | 含义 |")
L.append("|---|---|---|")
L.append("| 附件2 实际用电量 | **T+4** | 决策 D-1 时只能用 D-5 |")
L.append("| 附件3 平台预测信息 | **T-1** | 前一日发布，D-1 可用到 D |")
L.append("| 附件3 平台实际信息 | **T+2** | D-1 时只能用 D-3 |")
L.append("| 附件4 日前/实时价格 | **T+6** | D-1 时只能用 D-7 |")
L.append("| 附件5 中长期合约 | 事前已知 | 全部可用 |")
L.append("\n> 时间闸门函数 `src/common/asof.py::asof(df, decision_date)` 已实现，全队唯一。")

L.append("\n## 3. 信息时间闸门抽查（决策日 2026-03-31，为 04-01 申报）\n")
snap = asof.availability_snapshot(data, "2026-03-31")
L.append("| 数据源 | 最新可用实际日期 |")
L.append("|---|---|")
for k, v in snap.items():
    L.append(f"| {k} | {v} |")

L.append("\n## 4. 五个典型日（问题 1 输入）\n")
L.append("| 日期 | 日期类型 | 节假日 | 平均负荷(MWh) | 平均价差(元/MWh) |")
L.append("|---|---|---|---|---|")
for d, g in att1.groupby("date"):
    hol = g["holiday"].dropna().iloc[0] if g["holiday"].notna().any() else "-"
    L.append(f"| {d} | {g['day_type'].iloc[0]} | {hol} | {g['load_actual'].mean():.2f} | {(g['price_rt']-g['price_da']).mean():+.2f} |")

L.append("\n## 5. 全局统计摘要（附件2/4/5）\n")
L.append("| 指标 | 值 |")
L.append("|---|---|")
L.append(f"| 实际用电量 均值 / 标准差 | {summary['load_mean']:.2f} / {summary['load_std']:.2f} MWh |")
L.append(f"| 日前价 均值 | {summary['da_mean']:.2f} 元/MWh |")
L.append(f"| 实时价 均值 | {summary['rt_mean']:.2f} 元/MWh |")
L.append(f"| 价差 均值 / 标准差 | {summary['spread_mean']:+.2f} / {summary['spread_std']:.2f} 元/MWh |")
L.append(f"| 价差为正（P_RT>P_DA）占比 | {summary['spread_pos_ratio']*100:.1f}% |")
L.append(f"| 合约电价 唯一值 / 均值 | {summary['contract_p_unique']} / {summary['contract_p_mean']:.2f} 元/MWh |")

L.append("\n## 6. 结算基线（q=合约量）—— 后续 Q1 优化的对照\n")
L.append("| 典型日 | 日总成本(元) | 其中回收费用(元) | 实时偏差电费(元) |")
L.append("|---|---|---|---|")
for d, total, rec, rt in baseline:
    L.append(f"| {d} | {total:,.2f} | {rec:,.2f} | {rt:,.2f} |")
L.append("\n> 注：`实时偏差` 为负表示该日部分时段合约电量超过实际负荷（超发抵扣）。`回收` 非零表示即使 q=合约量，合约电量超出 120% 实际负荷的时段也会触发收益回收。")

L.append("\n## 7. 图示\n")
L.append("![典型日负荷与价格](../outputs/figures/D1_典型日负荷与价格.png)")
L.append("\n![价格与价差分布](../outputs/figures/D1_价格与价差分布.png)")

L.append("\n## 8. D1 结论与 D2 交接\n")
L.append("- ✅ 数据底座（M0）完成：6 附件长表化，`data/interim/` 就绪；披露延迟实测 T+2/T+4/T+6。")
L.append("- ✅ 结算内核（M1）完成：`settle()` 单元测试 5 项全通过，2026-04-07 日总成本手算误差 0 元（<1 元）。")
L.append("- ✅ 时间闸门 `asof()` 完成，抽查通过。")
L.append("- ✅ 口径决策 `DECISIONS.md` 完成（5 项 + 退化点）。")
L.append("- 🔜 D2 交接：A 接手 Q1（在退化点上加申报上限约束求解）；B 着手 Q2 特征与基线。")

with open(REPORT, "w", encoding="utf-8") as f:
    f.write("\n".join(L) + "\n")

print("报告已写出:", REPORT)
print("图已写出:", os.path.join(FIG, "D1_典型日负荷与价格.png"))
print("图已写出:", os.path.join(FIG, "D1_价格与价差分布.png"))
for k, v in summary.items():
    print(f"  {k} = {v}")
