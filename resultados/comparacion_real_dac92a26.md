# Model comparison on real data (dac92a26-d172-44f5-8042-17c0a4ceea26)

- Timestamp (UTC): 2026-10-09T00:03:22.613927+00:00
- Seed: 42
- Input SHA-256: 13d7b6ff6eb30b873dbff6b526aa9e882fe20373644cd65f50927e1b64541c0b
- Input rows: 242773, excluded (antiguedad_dias < 0): 70, used: 242703
- Primary metric: average_precision

## Partitions

| partition | rows | positives | positive_rate | unique_dates | date_start | date_end |
|---|---|---|---|---|---|---|
| train | 86038 | 2459 | 0.0286 | 55 | 2019-02-01 | 2023-08-01 |
| validation | 46251 | 1474 | 0.0319 | 18 | 2023-09-01 | 2025-02-01 |
| test | 110414 | 3408 | 0.0309 | 19 | 2025-03-01 | 2026-09-01 |

## Validation selection

| model | configuration | validation primary_value | selected | hyperparameters |
|---|---|---|---|---|
| xgboost | scaffold-1 | 0.1761 |  | {"learning_rate": 0.1, "max_depth": 3, "n_estimators": 50} |
| xgboost | scaffold-2 | 0.1894 | yes | {"learning_rate": 0.05, "max_depth": 4, "n_estimators": 100} |
| xgboost | scaffold-3 | 0.1760 |  | {"learning_rate": 0.1, "max_depth": 2, "n_estimators": 150} |
| random_forest | scaffold-1 | 0.1928 |  | {"max_depth": 4, "min_samples_leaf": 1, "n_estimators": 100} |
| random_forest | scaffold-2 | 0.2236 |  | {"max_depth": 6, "min_samples_leaf": 2, "n_estimators": 150} |
| random_forest | scaffold-3 | 0.2315 | yes | {"max_depth": 8, "min_samples_leaf": 1, "n_estimators": 200} |
| decision_tree | scaffold-1 | 0.1111 |  | {"max_depth": 3, "min_samples_leaf": 1} |
| decision_tree | scaffold-2 | 0.1378 | yes | {"max_depth": 5, "min_samples_leaf": 2} |
| decision_tree | scaffold-3 | 0.1187 |  | {"max_depth": 7, "min_samples_leaf": 3} |

## Test metrics

| model | configuration | average_precision | roc_auc | recall | precision | f1 | threshold | confusion_matrix |
|---|---|---|---|---|---|---|---|---|
| xgboost | scaffold-2 | 0.1911 | 0.8705 | 0.4545 | 0.1663 | 0.2435 | 0.2134 | [[99239, 7767], [1859, 1549]] |
| random_forest | scaffold-3 | 0.1843 | 0.8627 | 0.3856 | 0.1972 | 0.2609 | 0.3706 | [[101657, 5349], [2094, 1314]] |
| decision_tree | scaffold-2 | 0.1378 | 0.8240 | 0.6094 | 0.1225 | 0.2040 | 0.1737 | [[92127, 14879], [1331, 2077]] |

| model | validation average_precision | validation roc_auc | validation recall | validation precision | validation f1 |
|---|---|---|---|---|---|
| xgboost | 0.1894 | 0.8595 | 0.3860 | 0.1821 | 0.2474 |
| random_forest | 0.2315 | 0.8578 | 0.3053 | 0.2160 | 0.2530 |
| decision_tree | 0.1378 | 0.8299 | 0.4668 | 0.1589 | 0.2371 |

## Baselines (test partition)

| baseline | metrics |
|---|---|
| prevalence | {"average_precision": 0.030865651094969842} |
| rule_dias_desde_ultimo_pago_gt_180 | {"precision": 0.0, "recall": 0.0, "f1": 0.0} |
| single_feature_dias_desde_ultimo_pago | {"average_precision": 0.039063840189847585, "roc_auc": 0.5477624400904552, "missing_scores_filled": 0} |

## Inference timing

| model | ms_per_1000_rows | median_total_ms | single_row_latency_ms | repetitions | warmup | n_jobs |
|---|---|---|---|---|---|---|
| xgboost | 2.214 | 244.508 | 0.5114 | 5 | 1 | 1 |
| random_forest | 9.661 | 1066.708 | 8.7007 | 5 | 1 | 1 |
| decision_tree | 0.043 | 4.767 | 0.0716 | 5 | 1 | 1 |

## Leaves

| model | total_leaves |
|---|---|
| xgboost | 1534 |
| random_forest | 32390 |
| decision_tree | 31 |
