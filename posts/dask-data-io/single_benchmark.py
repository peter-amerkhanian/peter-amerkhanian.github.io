# Timers
import time
# I/O Utilities
import requests
import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import json

def make_filename(url: str) -> str:
    """Generate a local filename for each URL."""
    name = os.path.basename(url)
    if not name:
        name = "download"
    return os.path.join(OUTDIR, name)


def download_one(url: str) -> str:
    """Download a single file and save it to OUTDIR."""
    filename = make_filename(url)
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(filename, "wb") as file:
                file.write(response.content)
            return f"Downloaded: {filename}"
        else:
            return f"Failed ({response.status_code}): {url}"
    except Exception as e:
        return f"Error downloading {url}: {e}"

# Benchmark functions
def reset_outdir():
    """Wipe and recreate the output folder."""
    if os.path.exists(OUTDIR):
        shutil.rmtree(OUTDIR)
    os.makedirs(OUTDIR)

def run_sequential(urls):
    """Download files one by one."""
    reset_outdir()
    start = time.perf_counter()
    for url in urls:
        download_one(url)
    end = time.perf_counter()
    return end - start

def run_parallel(urls):
    """Download files in parallel using ThreadPoolExecutor."""
    reset_outdir()
    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(download_one, url) for url in urls]
        for f in as_completed(futures):
            f.result()
    end = time.perf_counter()
    return end - start

# Run both and compare
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_urls", nargs="+", required=True)
    args = parser.parse_args()
    file_urls = args.file_urls

    gitignore_path = ".gitignore"
    entry = "data_bench/"
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            lines = [line.strip() for line in f.readlines()]
    else:
        lines = []
    if entry not in lines:
        lines.append(entry)
        with open(gitignore_path, "w") as f:
            f.write("\n".join(lines) + "\n")

    OUTDIR = "data_bench"
    MAX_WORKERS = 10  # number of parallel threads
    try:
        file_urls
    except NameError:
        raise SystemExit("Please define `file_urls` as a list of URLs before running this script.")
    os.makedirs(OUTDIR, exist_ok=True)
    print("Test with sequential for-loop...")
    seq_time = run_sequential(file_urls)
    print(f"Sequential for-loop total download time: {seq_time:.2f}s\n")
    print(f"Test with {MAX_WORKERS} parallel workers...")
    par_time = run_parallel(file_urls)
    print(f"Parallel workers total download time:   {par_time:.2f}s\n")
    if par_time > 0:
        print(f"Parallelization Speedup: {seq_time / par_time:.2f}× faster")