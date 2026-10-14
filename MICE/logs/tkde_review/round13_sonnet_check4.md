bench_pools.py:gpu_state (compute-apps query) | `a.returncode` is never checked, so a failed `--query-compute-apps` yields empty stdout, counts as 0 apps, and the GPU reads idle, contradicting "failed query counts as busy" | return None when `a.returncode != 0` as well as when `q.returncode != 0`

bench_pools.py:gpu_state (subprocess.run and parsing) | can still raise: `FileNotFoundError` if nvidia-smi is missing, and `ValueError` from `float()` or tuple unpacking on `[N/A]` or multi-GPU output. An exception here would abort main before a record is written | wrap the whole body in `try/except (OSError, ValueError)` and return None
duration_ms 12164
