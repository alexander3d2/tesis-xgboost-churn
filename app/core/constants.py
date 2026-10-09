RANDOM_SEED = 42

XGBOOST_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": "aucpr",
    "random_state": RANDOM_SEED,
}

RISK_LEVEL_THRESHOLDS = {
    "alto": 0.7,
    "medio": 0.4,
}
