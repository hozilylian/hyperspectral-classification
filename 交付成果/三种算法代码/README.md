# 三种算法（SVM / 随机森林 / MLP）监督分类代码

> 本文件夹是发组员看的**算法代码**，方便理解三种模型怎么实现。
> ⚠️ 代码**需要原始数据才能运行**（依赖 `原始数据/ 训练集/ 结果/`，约 11GB，只在组长电脑上）；组员只需读懂代码即可。

## 包含脚本

| 脚本 | 作用 |
|---|---|
| `labelme_to_dataset.py` | 前置：labelme 多边形标注 → 训练集 `X/y/coords/class_map` |
| `train_classify.py` | **核心**：PCA + SVM / RF / MLP 三模型对比、随机/空间划分、整图分类图 |
| `predict_cross_strip.py` | 跨条带验证（用训练条带预测其他条带，输出跨条带精度） |
| `rf_importance.py` | 随机森林波段重要性（哪些波长对分类最关键） |

## 运行环境

```bash
pip install numpy scikit-learn matplotlib
```

在 `高光谱反射率数据/` 目录下运行（脚本依赖同目录的数据文件夹）：

```bash
python labelme_to_dataset.py raw_7216   # ① 标注 → 训练集
python train_classify.py raw_7216       # ② 训练 + 三模型对比
python predict_cross_strip.py raw_7216  # ③ 跨条带验证
python rf_importance.py raw_7216        # ④ 波段重要性
```

## 三种模型的关键代码（都在 `train_classify.py` 的 `fit_eval` 函数里）

```python
# SVM —— 最大间隔超平面 + RBF 核
SVC(kernel='rbf', C=10, gamma='scale', random_state=0)

# RF —— 300 棵决策树集成投票
RandomForestClassifier(n_estimators=300, random_state=0, n_jobs=-1)

# MLP —— 两层全连接神经网络
MLPClassifier(hidden_layer_sizes=(128, 64), max_iter=300,
              early_stopping=True, random_state=0)
```

三者共用同一套输入：**标准化 + PCA 降维（225 → 3~4 维）** 后的逐像素光谱特征。

## 结果速查

| 模型 | 条带内 OA |
|---|---|
| 随机森林 RF | **80.6%** |
| 多层感知机 MLP | 79.1% |
| 支持向量机 SVM | 76.4% |
