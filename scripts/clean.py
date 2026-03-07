"""
Clean up the raw data files so as to curate specifically-required 
"""

import subprocess
import threading
import os

def run_script(script_path):
    subprocess.run(["python", script_path], cwd=os.path.dirname(__file__))

# Run both cleaning scripts in parallel for speed
t1 = threading.Thread(target=run_script, args=("cleaners/clean_ms.py",))
t2 = threading.Thread(target=run_script, args=("cleaners/clean_ds.py",))

t1.start()
t2.start()

t1.join()
t2.join()

print("All cleaning scripts completed.")
