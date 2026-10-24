# -*- coding: utf-8 -*-
"""M1 · 结算内核 settle() —— 全队唯一实现，口径见 DECISIONS.md。

逐时段成本恒等式：
    C_t = Qc·Pc + (q-Qc)·P_da + (L-q)·P_rt + R_t
    R_t 为偏差风险调整（收益回收）费用，λ0=20%。
"""
import numpy as np

LAM0 = 0.20


def settle_hour(q, L, p_da, p_rt, qc, pc, lam0=LAM0):
    """单时段结算。返回 dict(contract, da_dev, rt_dev, recovery, total)。"""
    S = p_rt - p_da
    contract = qc * pc
    da_dev = (q - qc) * p_da
    rt_dev = (L - q) * p_rt
    R = 0.0
    if q > (1 + lam0) * L and S > 0:
        R = (q - (1 + lam0) * L) * S
    elif q < (1 - lam0) * L and S < 0:
        R = ((1 - lam0) * L - q) * (-S)
    total = contract + da_dev + rt_dev + R
    return {"contract": float(contract), "da_dev": float(da_dev),
            "rt_dev": float(rt_dev), "recovery": float(R), "total": float(total)}


def settle_day(q, L, p_da, p_rt, qc, pc, lam0=LAM0):
    """24 时段结算。入参为长度 24 的数组（或标量广播）。

    返回 dict：各分量 24 维 ndarray + sums（各分量日合计）。
    """
    q = np.asarray(q, dtype=float)
    L = np.asarray(L, dtype=float)
    p_da = np.asarray(p_da, dtype=float)
    p_rt = np.asarray(p_rt, dtype=float)
    qc = np.asarray(qc, dtype=float)
    pc = np.asarray(pc, dtype=float)

    S = p_rt - p_da
    contract = qc * pc
    da_dev = (q - qc) * p_da
    rt_dev = (L - q) * p_rt

    R = np.zeros_like(q)
    up = (q > (1 + lam0) * L) & (S > 0)
    dn = (q < (1 - lam0) * L) & (S < 0)
    R[up] = (q[up] - (1 + lam0) * L[up]) * S[up]
    R[dn] = ((1 - lam0) * L[dn] - q[dn]) * (-S[dn])

    total = contract + da_dev + rt_dev + R
    sums = {
        "contract": float(contract.sum()),
        "da_dev": float(da_dev.sum()),
        "rt_dev": float(rt_dev.sum()),
        "recovery": float(R.sum()),
        "total": float(total.sum()),
    }
    return {"contract": contract, "da_dev": da_dev, "rt_dev": rt_dev,
            "recovery": R, "total": total, "sums": sums}
