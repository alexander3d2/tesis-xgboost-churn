# Model comparison on real data (c5dae8cd-b932-48e9-8433-4d85cf2ca2c2)

- Timestamp (UTC): 2026-10-08T23:58:37.625178+00:00
- Seed: 42
- Input SHA-256: 04735010cc1da18fdd6abf8dbcdcb0e9c20e9630cc75a30b1c1ba9e5c6174d19
- Input rows: 500620, excluded (antiguedad_dias < 0): 78, used: 500542
- Primary metric: average_precision

## Partitions

| partition | rows | positives | positive_rate | unique_dates | date_start | date_end |
|---|---|---|---|---|---|---|
| train | 148067 | 38514 | 0.2601 | 55 | 2019-02-01 | 2023-08-01 |
| validation | 133227 | 49977 | 0.3751 | 18 | 2023-09-01 | 2025-02-01 |
| test | 219248 | 70610 | 0.3221 | 19 | 2025-03-01 | 2026-09-01 |

## Validation selection

| model | configuration | validation primary_value | selected | hyperparameters |
|---|---|---|---|---|
| xgboost | scaffold-1 | 0.8071 |  | {"learning_rate": 0.1, "max_depth": 3, "n_estimators": 50} |
| xgboost | scaffold-2 | 0.8294 | yes | {"learning_rate": 0.05, "max_depth": 4, "n_estimators": 100} |
| xgboost | scaffold-3 | 0.8220 |  | {"learning_rate": 0.1, "max_depth": 2, "n_estimators": 150} |
| random_forest | scaffold-1 | 0.7896 |  | {"max_depth": 4, "min_samples_leaf": 1, "n_estimators": 100} |
| random_forest | scaffold-2 | 0.8274 |  | {"max_depth": 6, "min_samples_leaf": 2, "n_estimators": 150} |
| random_forest | scaffold-3 | 0.8544 | yes | {"max_depth": 8, "min_samples_leaf": 1, "n_estimators": 200} |
| decision_tree | scaffold-1 | 0.6651 |  | {"max_depth": 3, "min_samples_leaf": 1} |
| decision_tree | scaffold-2 | 0.7184 |  | {"max_depth": 5, "min_samples_leaf": 2} |
| decision_tree | scaffold-3 | 0.7461 | yes | {"max_depth": 7, "min_samples_leaf": 3} |

## Test metrics

| model | configuration | average_precision | roc_auc | recall | precision | f1 | threshold | confusion_matrix |
|---|---|---|---|---|---|---|---|---|
| xgboost | scaffold-2 | 0.8023 | 0.9046 | 0.8878 | 0.6535 | 0.7529 | 0.4807 | [[115406, 33232], [7925, 62685]] |
| random_forest | scaffold-3 | 0.7877 | 0.9002 | 0.8900 | 0.6484 | 0.7503 | 0.5305 | [[114562, 34076], [7764, 62846]] |
| decision_tree | scaffold-3 | 0.6395 | 0.8429 | 0.9260 | 0.6269 | 0.7476 | 0.2857 | [[109722, 38916], [5226, 65384]] |

| model | validation average_precision | validation roc_auc | validation recall | validation precision | validation f1 |
|---|---|---|---|---|---|
| xgboost | 0.8294 | 0.8940 | 0.8649 | 0.6764 | 0.7591 |
| random_forest | 0.8544 | 0.9059 | 0.8652 | 0.6845 | 0.7643 |
| decision_tree | 0.7461 | 0.8532 | 0.9042 | 0.6323 | 0.7442 |

## Baselines (test partition)

| baseline | metrics |
|---|---|
| prevalence | {"average_precision": 0.32205538933080347} |
| rule_dias_desde_ultimo_pago_gt_180 | {"precision": 0.6174724810261499, "recall": 0.9517348817447954, "f1": 0.7490024743095339} |
| single_feature_dias_desde_ultimo_pago | {"average_precision": 0.6472819685190191, "roc_auc": 0.8360851492130139, "missing_scores_filled": 0} |

## Inference timing

| model | ms_per_1000_rows | median_total_ms | single_row_latency_ms | repetitions | warmup | n_jobs |
|---|---|---|---|---|---|---|
| xgboost | 2.304 | 505.202 | 0.6200 | 5 | 1 | 1 |
| random_forest | 10.753 | 2357.521 | 10.2837 | 5 | 1 | 1 |
| decision_tree | 0.070 | 15.313 | 0.0819 | 5 | 1 | 1 |

## Leaves

| model | total_leaves |
|---|---|
| xgboost | 1593 |
| random_forest | 42949 |
| decision_tree | 115 |
