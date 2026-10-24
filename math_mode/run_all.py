# -*- coding: utf-8 -*-
"""一键复现入口（D1 版）：数据底座 -> 结算测试 -> EDA 报告。

M6 阶段会逐步加入 Q1~Q4 各问脚本，最终做到"删库重跑 30 分钟内出全部结果"。
用法：python run_all.py
"""
import os
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.abspath(__file__))


def step(cmd, label):
    print("\n" + "=" * 66)
    print("▶", label)
    print("=" * 66)
    r = subprocess.run([sys.executable] + cmd, cwd=ROOT)
    if r.returncode != 0:
        print(f"✘ {label} 失败 (exit {r.returncode})")
        sys.exit(r.returncode)
    print(f"✔ {label} 完成")


if __name__ == "__main__":
    step(["build_data.py"], "数据底座构建")
    step(["tests/test_settle.py"], "结算内核单元测试")
    step(["reports/make_d1_report.py"], "D1 数据摸底报告与图")
    print("\n🎉 D1 全部步骤通过。")
