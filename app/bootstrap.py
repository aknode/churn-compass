from pathlib import Path
import argparse, urllib.request, hashlib
from app.model import BASE, train

URL = "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path)
    args = p.parse_args()
    path = args.csv or BASE / "data/raw/telco.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        print("Downloading IBM sample dataset...")
        urllib.request.urlretrieve(URL, path)
    if (
        not args.csv
        and hashlib.sha256(path.read_bytes()).hexdigest()
        != "16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91"
    ):
        raise ValueError(
            "Dataset checksum changed. Inspect the upstream file before training."
        )
    result = train(path)
    print("Selected:", result["selected_model"])
    print(result["test"][result["selected_model"]])


if __name__ == "__main__":
    main()
