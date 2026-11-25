# 高光谱校园地物分类 · 代码说明

> 脚本按处理流程分成 **01–06 六步**（文件夹名即运行顺序）。所有脚本都在 `高光谱反射率数据/` 目录下运行（脚本依赖同目录的 `原始数据/ 标注/ 训练集/ 结果/`）。
> 本目录是**按流程整理的提交用副本**，方便阅读；实际运行请到 `高光谱反射率数据/`。

---

## 各脚本一览

### 01_导出标注图
生成「真彩色」PNG（植被呈绿色），供 labelme 人工标注。

| 脚本 | 作用 | 运行 |
|---|---|---|
| `export_all_rgb.py` | 5 条条带各导出一张真彩色 PNG | `python export_all_rgb.py` |
| `export_rgb.py` | 单条带版（默认 raw_10096） | `python export_rgb.py` |

### 02_标注转数据集
把 labelme 的多边形标注转成训练集。

| 脚本 | 作用 | 运行 |
|---|---|---|
| `labelme_to_dataset.py` | labelme json → `X/y/coords/class_map`（含标签别名归并） | `python labelme_to_dataset.py raw_7216` |

### 03_任务一_聚类
无标注条件下探索数据可分性，确定类别数 K=5。

| 脚本 | 作用 | 运行 |
|---|---|---|
| `cluster_unsupervised.py` | MiniBatchKMeans + SSE/CH 选 K → 聚类图 + 平均光谱 | `python cluster_unsupervised.py` |
| `cluster_summary.py` | 打印每簇光谱指标（NDVI 等），帮助判断地物 | `python cluster_summary.py` |

### 04_任务二_分类
监督分类（PCA + SVM / RF / MLP），随机/空间划分 + 跨条带。

| 脚本 | 作用 | 运行 |
|---|---|---|
| `train_classify.py` | 三模型对比 + 随机/空间划分 + 整图分类图 | `python train_classify.py raw_7216` |
| `predict_cross_strip.py` | 用训练条带预测其他条带，输出跨条带精度 | `python predict_cross_strip.py raw_7216` |

### 05_验证与机理
真值验证 + 机理分析。

| 脚本 | 作用 | 运行 |
|---|---|---|
| `sam_validate.py` | 地面实测光谱 vs 影像同类光谱的光谱角(SAM)验证 | `python sam_validate.py raw_7216` |
| `rf_importance.py` | 随机森林波段重要性（哪些波长最关键） | `python rf_importance.py raw_7216` |

### 06_报告与PPT
生成三个交付文档。

| 脚本 | 作用 | 运行 |
|---|---|---|
| `build_report_docx.py` | 生成 Word 实验报告 | `python build_report_docx.py` |
| `build_ppt.py` | 生成汇报 PPT（暗色） | `python build_ppt.py` |
| `build_mlp_ppt.py` | 生成 MLP 讲解 PPT（含自制 SVG 图） | `python build_mlp_ppt.py` |

`ReadRS.py` —— 老师提供的读图参考脚本（rasterio）。

---

## 完整流程（一句话）

```
01 导出标注图 → 02 标注转数据集 → 03 聚类定类 → 04 训练+跨条带 → 05 验证+机理 → 06 生成报告/PPT
```

---

## 关键参数速查（写报告/答辩用）

| 项 | 值 |
|---|---|
| 类别 | 水体/阴影、草地、树木、建筑、道路（5 类） |
| 波段 | 400–1000nm 共 272 波段 → 截取 450–950nm（225）→ PCA 3~4 维 |
| 训练/测试 | 7216 训练（10000 均衡样本）；10096、5232 测试 |
| 模型精度（条带内） | **RF 80.6% > MLP 79.1% > SVM 76.4%** |
| 跨条带精度 | 10096 → 69.2%；5232 → 71.4% |
| 真值验证 | SAM：树木 5/5 强吻合（平均 ~7.6°） |
| 关键波段 | 近红外 750–950nm（33.9%）+ 蓝 450–500nm（23.4%） |
