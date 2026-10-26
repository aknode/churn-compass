# Churn Compass interview guide

## What problem does it solve?

It ranks historical telecom accounts by churn risk and makes model trade-offs reviewable through an interface and API.

## How did you prevent leakage?

Split before fitting. Imputation, scaling and encoding live inside each fitted training pipeline. Model and threshold selection use validation data; the held-out test is never used for selection.

## Why average precision instead of accuracy?

Churn is the minority class. Average precision summarises precision/recall ranking, while an always-nonchurn predictor can have deceptively high accuracy.

## Why is the threshold below 0.5?

Validation F2 places more weight on recall. It catches more churners but also flags many nonchurners. A true business threshold would require intervention cost and causal benefit estimates.

## What would you improve?

Temporal evaluation on new data, subgroup checks, calibration, confidence intervals and randomized intervention evaluation.

## Why no SMOTE?

It was not necessary for this baseline comparison. Any future resampling must happen inside training folds, never before splitting.

## How do you demonstrate it?

Show the benchmark, explain precision versus recall, score a customer, run the example CSV, and inspect metrics.json and split_ids.json.

Read and run the code before presenting it as your project. Describe the stack and results actually implemented; do not claim unmeasured business impact or a live deployment.
