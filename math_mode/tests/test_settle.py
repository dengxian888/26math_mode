# -*- coding: utf-8 -*-
"""M1 · 结算内核单元测试（用附件1 典型日 2026-04-07 逐时段手算核对，误差<1元）。

运行：python tests/test_settle.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

from src.common import io, settle


def close(a, b, tol=1e-6, label=""):
    ok = abs(a - b) <= tol
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}: {a:.6f} vs 期望 {b:.6f}")
    return ok


def main():
    passed = True
    LAM = 0.20

    # ============ 测试 1：单时段，q = 合约量（不触发 R） ============
    qc, pc, L, p_da, p_rt = 27.585, 372.0, 37.4517, 413.48, 844.37
    r = settle.settle_hour(qc, L, p_da, p_rt, qc, pc)
    exp_contract = qc * pc
    exp_da = 0.0
    exp_rt = (L - qc) * p_rt
    exp_R = 0.0
    print("\n[测试1] q=合约量，S>0 但 q 在带内（q < (1-λ)L），不触发回收")
    passed &= close(r["contract"], exp_contract, 1e-9, "中长期合约电费")
    passed &= close(r["da_dev"], exp_da, 1e-9, "日前偏差电费")
    passed &= close(r["rt_dev"], exp_rt, 1e-9, "实时偏差电费")
    passed &= close(r["recovery"], exp_R, 1e-9, "回收费用 R=0")
    passed &= close(r["total"], exp_contract + exp_rt, 1e-6, "总成本")

    # ============ 测试 2：触发回收，q > (1+λ)L 且 S>0 ============
    q = 50.0
    r = settle.settle_hour(q, L, p_da, p_rt, qc, pc)
    S = p_rt - p_da
    exp_R = (q - (1 + LAM) * L) * S
    print("\n[测试2] q=50 > (1+λ)L=44.942，S>0，应触发回收")
    passed &= close(r["recovery"], exp_R, 1e-9, "回收费用 R")

    # ============ 测试 3：触发回收，q < (1-λ)L 且 S<0（合成 S<0）============
    p_da2, p_rt2 = 844.37, 413.48  # S<0
    q = 20.0
    r = settle.settle_hour(q, L, p_da2, p_rt2, qc, pc)
    S2 = p_rt2 - p_da2
    exp_R = ((1 - LAM) * L - q) * (-S2)
    print("\n[测试3] q=20 < (1-λ)L=29.961，S<0，应触发回收")
    passed &= close(r["recovery"], exp_R, 1e-9, "回收费用 R")

    # ============ 测试 4：退化平台性质 total(45) ≈ total(50) ============
    print("\n[测试4] 越带后成本平台：total(45) 应等于 total(50)")
    r45 = settle.settle_hour(45.0, L, p_da, p_rt, qc, pc)
    r50 = settle.settle_hour(50.0, L, p_da, p_rt, qc, pc)
    passed &= close(r45["total"], r50["total"], 1e-6, "total(45)==total(50)")

    # ============ 测试 5：整日结算，用附件1 典型日逐时段核对 ============
    print("\n[测试5] 整日结算 settle_day：附件1 2026-04-07，q=合约量")
    att1 = io.load_attachments()["att1"]
    day = att1[att1["date"] == "2026-04-07"].reset_index(drop=True)
    qc = day["contract_q"].to_numpy()
    pc = day["contract_p"].to_numpy()
    L = day["load_actual"].to_numpy()
    p_da = day["price_da"].to_numpy()
    p_rt = day["price_rt"].to_numpy()
    q = qc.copy()  # 申报=合约
    out = settle.settle_day(q, L, p_da, p_rt, qc, pc)

    # 逐时段独立手算
    for t in range(24):
        ref = settle.settle_hour(qc[t], L[t], p_da[t], p_rt[t], qc[t], pc[t])
        if abs(out["total"][t] - ref["total"]) > 1e-6:
            print(f"  [FAIL] 时段{t} 不符: {out['total'][t]:.4f} vs {ref['total']:.4f}")
            passed = False
    exp_sum = float(sum(settle.settle_hour(qc[t], L[t], p_da[t], p_rt[t], qc[t], pc[t])["total"] for t in range(24)))
    passed &= close(out["sums"]["total"], exp_sum, 1e-4, "日总成本（逐时段和核对）")
    print(f"  2026-04-07 日总成本 = {out['sums']['total']:.2f} 元")
    print(f"    其中 合约={out['sums']['contract']:.2f}  日前偏差={out['sums']['da_dev']:.2f}  "
          f"实时偏差={out['sums']['rt_dev']:.2f}  回收={out['sums']['recovery']:.2f}")

    # 对照"误差<1元"验收线
    print(f"\n  验收：日总成本与手算误差 = {abs(out['sums']['total'] - exp_sum):.6f} 元"
          f"（Gate1 要求 < 1 元）-> {'PASS' if abs(out['sums']['total'] - exp_sum) < 1 else 'FAIL'}")

    print("\n" + ("=" * 60))
    print("结算内核测试结果：", "全部通过 ✅" if passed else "存在失败 ❌")
    print("=" * 60)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
