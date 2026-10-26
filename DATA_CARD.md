# Data card

- Source: IBM Telco Customer Churn sample, downloaded from
  https://github.com/IBM/telco-customer-churn-on-icp4d/tree/master/data
- Source file: `Telco-Customer-Churn.csv`; 7,043 rows.
- Original source repository: https://github.com/IBM/telco-customer-churn-on-icp4d
  (archived upstream). Its code pattern uses Apache License 2.0. The portfolio's
  MIT license covers original application code, not a claim of ownership of
  the IBM sample data. Raw source data is downloaded separately and excluded
  from this release and Git.
- SHA-256: `16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91`.
- Target prevalence: 26.54%; observation-level classification.
- Numeric features: tenure in months, MonthlyCharges and TotalCharges in source
  currency units. Source billing-period assumptions are not inferred.
- Categorical values preserve the upstream spelling and explicit absence labels
  such as `No internet service`.
- Customer IDs are unique; the three split ID sets are disjoint.
- No observation timestamps are supplied for a reliable temporal split.
- This historical educational sample does not prove transfer to another company,
  geography, time period, pricing plan or intervention policy.
