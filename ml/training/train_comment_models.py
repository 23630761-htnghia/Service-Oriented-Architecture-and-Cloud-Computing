from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


ROOT_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT_DIR / "ml" / "data" / "comments_labeled.csv"
MODELS_DIR = ROOT_DIR / "ml" / "models"


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )


def train_classifier(dataframe: pd.DataFrame, target_column: str):
    features = dataframe["comment"]
    labels = dataframe[target_column]

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    return pipeline, report


def main() -> None:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dataframe = pd.read_csv(DATA_PATH)

    intent_model, intent_report = train_classifier(dataframe, "intent")
    sentiment_model, sentiment_report = train_classifier(dataframe, "sentiment")

    joblib.dump(intent_model, MODELS_DIR / "intent_model.joblib")
    joblib.dump(sentiment_model, MODELS_DIR / "sentiment_model.joblib")

    metrics = {
        "intent": intent_report,
        "sentiment": sentiment_report,
        "dataset_size": len(dataframe),
    }
    (MODELS_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Saved intent model to {MODELS_DIR / 'intent_model.joblib'}")
    print(f"Saved sentiment model to {MODELS_DIR / 'sentiment_model.joblib'}")
    print(f"Saved metrics to {MODELS_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
