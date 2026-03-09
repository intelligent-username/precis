"""
Clean up the raw data files so as to curate specifically-required 
"""

import subprocess
import threading
import os

def run_script(script_path):
    subprocess.run(["python", script_path], cwd=os.path.dirname(__file__))

t1 = threading.Thread(target=run_script, args=("cleaners/clean_ms.py",))
t2 = threading.Thread(target=run_script, args=("cleaners/clean_ds.py",))
t3 = threading.Thread(target=run_script, args=("cleaners/clean_msm.py",))
t4 = threading.Thread(target=run_script, args=("cleaners/clean_qmsum.py",))
t5 = threading.Thread(target=run_script, args=("cleaners/clean_squality.py",))

t1.start()
t2.start()
t3.start()
t4.start()
t5.start()

t1.join()
t2.join()
t3.join()
t4.join()
t5.join()

print("All cleaning scripts completed.")
