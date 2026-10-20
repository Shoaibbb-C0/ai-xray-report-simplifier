"""Download checksum-verified public research data; no login or patient uploads.

python -m ml.datasets.download_public
Archives and extracted files stay ignored under ml/datasets/raw/.
"""
import hashlib
from pathlib import Path
import tarfile
import urllib.request
import zipfile
from ml.datasets.registry import RAW_DATASETS_DIR

SOURCES = [
    ("https://ndownloader.figshare.com/files/65518038", "fracatlas/FracAtlas.download.zip", "fe9da2c7c285915ebee69dfdab8fd396"),
    ("https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz", "negative_samples/cifar10/cifar-10-python.tar.gz", "c58f30108f718f92721af3b95e74349a"),
    ("https://zenodo.org/records/10519652/files/retinamnist.npz?download=1", "negative_samples/retinamnist.npz", "bd4c0672f1bba3e3a89f0e4e876791e4"),
    ("https://zenodo.org/records/10519652/files/dermamnist.npz?download=1", "negative_samples/dermamnist.npz", "0744692d530f8e62ec473284d019b0c7"),
]


def download(url, destination, checksum):
    destination.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(20):
        if destination.is_file() and hashlib.md5(destination.read_bytes()).hexdigest() == checksum:
            return
        offset = destination.stat().st_size if destination.exists() else 0
        request = urllib.request.Request(url, headers={"Range": f"bytes={offset}-", "User-Agent": "AI-XRay-Academic-Reproduction/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                mode = "ab" if response.status == 206 else "wb"
                with destination.open(mode) as output:
                    while chunk := response.read(256 * 1024):
                        output.write(chunk)
        except (OSError, TimeoutError):
            print(f"Transfer interrupted; resuming {destination.name} (attempt {attempt+1})", flush=True)
    raise RuntimeError(f"Could not obtain a verified {destination.name}; do not train from a partial download")


def main():
    for url, relative, checksum in SOURCES:
        path = RAW_DATASETS_DIR / relative
        download(url, path, checksum)
        if path.suffix == ".zip" and not (path.parent / "FracAtlas/dataset.csv").is_file():
            with zipfile.ZipFile(path) as archive:
                for member in archive.namelist():
                    if not (path.parent / member).resolve().is_relative_to(path.parent.resolve()):
                        raise ValueError("Unsafe archive member")
                archive.extractall(path.parent)
        elif path.name.endswith(".tar.gz") and not (path.parent / "cifar-10-batches-py/test_batch").is_file():
            with tarfile.open(path) as archive:
                archive.extractall(path.parent, filter="data")
        print(f"Verified {path.name}", flush=True)


if __name__ == "__main__":
    main()
