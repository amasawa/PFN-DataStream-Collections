bench_pools.py:~99 (retry loop `for attempt in range(5)`) | `gpu_busy()` is checked only before attempt 0. Attempts 1–4 start right after a failed child, without confirming the GPU is still alone, so a retry can run beside another process and still be recorded `ok`. | Move the `while gpu_busy(): time.sleep(30)` inside the attempt loop, before each `subprocess.run`.
duration_ms 15008
