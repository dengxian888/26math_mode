# -*- coding: utf-8 -*-
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import matplotlib.font_manager as fm
import os

# ---- 中文字体 ----
cands = ['Microsoft YaHei', 'SimHei', 'Noto Sans CJK SC', 'Source Han Sans SC', 'SimSun']
avail = {f.name for f in fm.fontManager.ttflist}
font = next((c for c in cands if c in avail), None)
if font is None:
    for p in [r'C:\Windows\Fonts\msyh.ttc', r'C:\Windows\Fonts\simhei.ttf']:
        if os.path.exists(p):
            fm.fontManager.addfont(p)
            font = fm.FontProperties(fname=p).get_name()
            break
plt.rcParams['font.sans-serif'] = [font, 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

COL = {'A': '#4C72B0', 'B': '#55A868', 'C': '#C44E52'}
OWNER = {'A': 'A 建模与优化（队长）', 'B': 'B 数据与算法工程', 'C': 'C 论文与独立验证'}

tasks = [
    ('A', '口径裁决 · 模型假设 · 技术路线', 0, 8),
    ('A', '问题1 建模 / 求解 / 成本构成', 8, 30),
    ('A', '问题3 申报衔接与经济效果评价', 30, 46),
    ('A', '问题4 风险决策模型设计', 46, 60),
    ('A', '问题4 求解 · 5/10/30天滚动 · 敏感性', 60, 84),

    ('B', '数据底座 + asof 时间闸门', 0, 10),
    ('B', '结算内核 settle() + 单元测试', 10, 16),
    ('B', '问题2 特征工程 + 基线预测', 16, 32),
    ('B', '问题2 三方案对比 + 信息增量价值', 32, 44),
    ('B', '问题3 价格 / 价差预测', 44, 58),
    ('B', '附件6 自动填表 + run_all 复现', 58, 70),
    ('B', '附录代码清单与复现说明', 84, 94),

    ('C', '论文骨架 + 图表规范', 0, 14),
    ('C', '正文滚动写作（含每日独立复算）', 14, 84),
    ('C', '合规检查 · AI声明 · 打包提交', 84, 104),
]

gates = [
    (16, '地基验收\n结算口径一致'),
    (24, '口径冻结'),
    (36, '首版结果\nQ1+Q2基线'),
    (60, '模型结构定稿'),
    (84, '数字冻结\n只改文字'),
    (96, '初稿完整'),
    (104, '提交'),
]

fig, ax = plt.subplots(figsize=(15.5, 8.2), dpi=170)
n = len(tasks)
rows = {}
y = 0
labels = []
yticks = []
for i, (owner, name, s, e) in enumerate(tasks):
    ax.barh(y, e - s, left=s, height=0.62, color=COL[owner], alpha=0.9,
            edgecolor='white', linewidth=0.8, zorder=3)
    ax.text(s + (e - s) / 2, y, f'{s}-{e}h', ha='center', va='center',
            fontsize=7.2, color='white', zorder=4)
    labels.append(name)
    yticks.append(y)
    y -= 1
    if i + 1 < n and tasks[i + 1][0] != owner:
        y -= 0.55

ax.set_yticks(yticks)
ax.set_yticklabels(labels, fontsize=9.2)
for tick, (owner, *_rest) in zip(ax.get_yticklabels(), tasks):
    tick.set_color(COL[owner])

for x, txt in gates:
    ax.axvline(x, color='#555555', linestyle=(0, (4, 3)), linewidth=1.0, zorder=2, alpha=0.75)
    ax.text(x, 1.55, txt, rotation=0, ha='center', va='bottom', fontsize=7.4,
            color='#333333',
            bbox=dict(boxstyle='round,pad=0.28', fc='#F7F7F7', ec='#BBBBBB', lw=0.6))

phases = [(0, 4, 'P0 立项'), (4, 16, 'P1 地基'), (16, 36, 'P2 首版'),
          (36, 60, 'P3 攻坚'), (60, 80, 'P4 闭环'), (80, 96, 'P5 冻结'), (96, 104, 'P6 提交')]
for s, e, name in phases:
    ax.axvspan(s, e, color='#000000', alpha=0.028, zorder=0, lw=0)
    ax.text((s + e) / 2, 1.02, name, ha='center', va='bottom', fontsize=8.2, color='#8A8A8A')
    if s > 0:
        ax.axvline(s, color='#DDDDDD', lw=0.8, zorder=0)

ax.set_xlim(-1, 108)
ax.set_ylim(y + 0.6, 2.05)
ax.set_xlabel('距赛题发布的小时数 H（示例：4~5 天赛程，共 104h）', fontsize=10)
ax.set_title('电力市场赛题 · 三人队分工甘特图（按交付物分线，三线并行）',
             fontsize=14, fontweight='bold', pad=26)
ax.grid(axis='x', color='#E5E5E5', linewidth=0.7, zorder=0)
ax.set_axisbelow(True)
for side in ['top', 'right', 'left']:
    ax.spines[side].set_visible(False)
ax.tick_params(axis='x', labelsize=8.5)

handles = [Patch(facecolor=COL[k], label=OWNER[k]) for k in 'ABC']
handles.append(Line2D([0], [0], color='#555555', linestyle=(0, (4, 3)), label='里程碑 / Gate'))
ax.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.175),
          ncol=4, frameon=False, fontsize=9)

plt.tight_layout()
plt.savefig('figs_分工甘特图.png', bbox_inches='tight', facecolor='white')
print('saved, font=', font)
