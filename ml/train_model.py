"""
train_model.py
---------------
Trains a spam-call classifier combining:
  - TF-IDF text features from the call transcript (speech-to-text output)
  - Numeric call-metadata features (calls_per_day, avg_call_duration, is_international)

Uses a scikit-learn ColumnTransformer + RandomForestClassifier pipeline.
Saves the trained pipeline to model.pkl (loaded later by spam_detector.py).
"""

import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import joblib

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    dataset_path = os.path.join(HERE, "dataset.csv")
    if not os.path.exists(dataset_path):
        from generate_dataset import generate
        df = generate(600)
        df.to_csv(dataset_path, index=False)
    else:
        df = pd.read_csv(dataset_path)

    X = df[["transcript", "calls_per_day", "avg_call_duration", "is_international"]]
    y = df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("text", TfidfVectorizer(max_features=300, ngram_range=(1, 2)), "transcript"),
            ("num", StandardScaler(), ["calls_per_day", "avg_call_duration", "is_international"]),
        ]
    )

    pipeline = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("clf", RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)),
        ]
    )

    pipeline.fit(X_train, y_train)

    preds = pipeline.predict(X_test)
    acc = accuracy_score(y_test, preds)
    print(f"Test accuracy: {acc:.3f}")
    print(classification_report(y_test, preds, target_names=["ham", "spam"]))

    model_path = os.path.join(HERE, "model.pkl")
    joblib.dump(pipeline, model_path)
    print(f"Saved trained model -> {model_path}")


if __name__ == "__main__":
    main()
