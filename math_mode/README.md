# 数理大赛 · 项目 README

赛题：**电力市场中的用电申报与风险决策**（华南理工大学第二十五届"三新集团杯"数理大赛）

本仓库是"三线并行"分工方案下的工程实现。当前进度：**D1（P0 立项 + P1 地基）已完成**。

---

## 1. 目录结构

```
math_mode/
├─ data/raw/             # 赛题原始附件（只读，勿改）
├─ data/interim/         # 清洗后统一长表（csv, utf-8-sig）
├─ src/common/           # 全队唯一共享内核
│   ├─ io.py             #   纯标准库 xlsx 读取 + 6 附件加载
│   ├─ asof.py           #   信息可得时间闸门
│   ├─ settle.py         #   结算内核（口径见 DECISIONS.md）
│   └─ (features.py 待 D2) #   特征/指标
├─ src/q1 q2 q3 q4/      # 各问建模脚本（D2 起）
├─ tests/                # 单元测试
├─ outputs/figures/      # 图
├─ reports/              # EDA 报告
├─ DECISIONS.md          # 口径决策清单（唯一口径来源）
├─ build_data.py         # 构建长表
├─ run_all.py            # 一键复现
└─ README.md
```

## 2. 环境

- Python 3.13（本机 `python`）
- 依赖：`pandas / numpy / scipy / matplotlib`（已装）
- **不需要** `openpyxl / xlrd`：`src/common/io.py` 用标准库 `zipfile + ElementTree` 直接解析 xlsx。
- 无网络环境，禁止新增 pip 依赖（需要时先与队长 A 确认）。

## 3. 运行顺序

```bash
python run_all.py            # 一键：数据底座 → 结算测试 → EDA 报告
# 或分步：
python build_data.py         # 生成 data/interim/*.csv 并打印摸底摘要
python tests/test_settle.py  # 结算内核 5 项单元测试（Gate1 验收）
python reports/make_d1_report.py  # 出 2 张图 + D1 数据摸底报告
```

## 4. 接口契约（三份，任何人不得私自改）

### 契约 1 · 长表 schema
`date(str 'YYYY-MM-DD') | hour(int 0-23) | 指标列(float)`；`available_date` 仅存在于带披露延迟的数据源。

### 契约 2 · 结算函数（唯一实现 `src/common/settle.py`）
```python
settle.settle_hour(q, L, p_da, p_rt, qc, pc, lam0=0.20) -> dict
settle.settle_day(q, L, p_da, p_rt, qc, pc, lam0=0.20)  -> dict  # 24 维数组 + sums
# 返回键：contract / da_dev / rt_dev / recovery(R_t) / total
```

### 契约 3 · 时间闸门（唯一实现 `src/common/asof.py`）
```python
asof.asof(df, decision_date) -> DataFrame  # 只保留 available_date <= decision_date 的行
# 对 D 日申报，在 D-1 收盘决策：asof(df, 'D-1')
```
**任何人禁止直接 `df.lag()`；特征构造一律过 `asof()`。**

## 5. 口径与决策

所有公式、假设、口径争议的最终解释以 **[DECISIONS.md](DECISIONS.md)** 为准。修改口径 → 队长站会裁决 → 追加修订记录 → 重跑受影响结果。

## 6. D1 已完成 / 待办

- ✅ M0 数据底座、M1 结算内核、时间闸门、口径清单、EDA 报告
- 🔜 D2：A 做问题 1（申报上限约束 + 求解）；B 做问题 2（特征 + 基线预测）；C 搭论文骨架
