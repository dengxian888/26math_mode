# -*- coding: utf-8 -*-
"""M0 · 信息可得时间闸门 asof() —— 全队唯一，禁止任何人自行 df.lag(1)。

数据披露延迟（D1 实测）：
  附件2 实际用电量        available_date = date + 4 天   (T+4)
  附件3 平台实际运行信息  available_date = date + 2 天   (T+2)
  附件3 平台预测信息      available_date = date - 1 天   (T-1，前一日发布)
  附件4 日前/实时价格    available_date = date + 6 天   (T+6)
  附件5 中长期合约        事前已知，无 available_date 列
"""
import pandas as pd


def asof(df, decision_date):
    """对带 available_date 列的数据，返回在 decision_date 当天收盘前可获得的全部行。

    decision_date: 'YYYY-MM-DD' 字符串（决策当日）。
    例：对 D 日申报，在 D-1 日收盘决策，调用 asof(df, 'D-1')。
    """
    if "available_date" not in df.columns:
        raise ValueError("数据缺少 available_date 列，无法做时间闸门切片")
    return df[df["available_date"] <= decision_date].reset_index(drop=True)


def latest_available(df):
    """返回该数据源在切片后，最新一条记录对应的实际发生日期（date 列最大值）。"""
    return df["date"].max()


def availability_snapshot(data, decision_date):
    """返回各数据源在 decision_date 收盘时，最新可用的"实际发生日期"。

    用于 D1 数据摸底与 Q3/Q4 特征构造的对账（防未来信息泄漏）。
    """
    snap = {}
    snap["实际用电量(att2)"] = latest_available(asof(data["att2"], decision_date))
    snap["平台实际信息(att3_actual)"] = latest_available(asof(data["att3_actual"], decision_date))
    snap["平台预测信息(att3_forecast)"] = latest_available(asof(data["att3_forecast"], decision_date))
    snap["日前/实时价格(att4)"] = latest_available(asof(data["att4"], decision_date))
    snap["中长期合约(att5)"] = data["att5"]["date"].max()
    return snap
