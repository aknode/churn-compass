# Model card

Intended use: educational churn risk review and model evaluation.
Out of scope: automated denial of service, pricing changes, or claims of causal
retention uplift.

## Evaluation protocol

Random seed 42. Split sizes: {"train": 4225, "validation": 1409, "test": 1409}. Stratification preserves
target proportions. Median imputation, standard scaling and one-hot encoding are
fitted only on training rows. Validation average precision selects among the
two trained classifiers. A prior-only dummy classifier supplies a benchmark.
Validation F2 selects the operating threshold from 0.05 to 0.95 in increments of
0.005. Hyperparameters are fixed; this is a small comparison, not an exhaustive
search. All models then receive a single held-out evaluation. The model shipped
for inference remains trained only on the training split.

## Selected model results

Selected: `logistic_regression`. Threshold: 0.170.

| Metric | Test result |
|---|---:|
| ROC AUC | 0.832817 |
| Average precision | 0.625481 |
| Precision | 0.448598 |
| Recall | 0.898396 |
| F2 | 0.748330 |
| Brier score | 0.141302 |

Confusion matrix, rows actual [non-churn, churn], columns predicted [non-churn,
churn]: `[[622, 413], [38, 336]]`.

Probabilities have not undergone a separate calibration procedure. The Brier
score describes this test set only. Confidence intervals, fairness evaluation,
economic utility and temporal robustness are not established. Permutation
importance uses five validation permutations and the AP scoring metric;
correlated features may share or mask importance.
