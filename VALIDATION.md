# Release validation

Validated on Python 3.12 in a Linux authoring environment. Windows instructions are provided but were not executed on Windows.

- Trained all three models on IBM Telco sample; froze selection before test evaluation.
- Verified disjoint train/validation/test customer IDs.
- Browser: real single-customer scoring and CSV prediction download.

Automated tests pass; see `validation/unit-test-results.txt`. Browser workflows passed in headless Chromium at 1440px desktop and 390px mobile, with no uncaught JavaScript errors or page-level horizontal overflow. Internal screenshots were visually inspected and are not part of the release.

Static Python undefined/unused-name checks passed. JavaScript syntax checks and formatting completed. Each repository includes a CI workflow, but GitHub-hosted CI was not executed here. Docker files are provided but Docker images were not built. No public deployment was performed.

