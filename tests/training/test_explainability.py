from app.training.explainability import ExplainabilityUnavailable, explain_model


def test_explainability_reports_unavailable_without_importing_shap(monkeypatch):
    real_import = __import__

    def reject_shap(name, *args, **kwargs):
        if name == "shap":
            raise ImportError("synthetic test: shap unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", reject_shap)
    result = explain_model(object(), [[0.0]])
    assert isinstance(result, ExplainabilityUnavailable)
    assert result.available is False
