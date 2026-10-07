"""Bounded overnight queue. Only owns its children; no broad process kills or force pushes."""
import argparse
from collections import deque
from datetime import datetime
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from worker import atomic_json

STOP = False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('root'); parser.add_argument('repo')
    parser.add_argument('--hours', type=float, default=8)
    parser.add_argument('--max-workers', type=int, choices=range(1, 11), default=1)
    parser.add_argument('--breaker', type=int, default=6,
                        help='multi-worker failures within ten minutes that stop the run')
    args = parser.parse_args()
    root, repo = Path(args.root), Path(args.repo)
    lock = (root / 'supervisor.lock').open('w')
    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: sys.exit('A supervisor already owns this run')
    controller = Path(__file__).resolve().parent
    tasks = json.loads((root / 'tasks.json').read_text())
    state_path = root / 'queue_state.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    for task in tasks:
        state.setdefault(task['id'], dict(attempts=0, failures=0, next=0, blocked=False))
        state[task['id']].setdefault('stalled_failures', 0)
        state[task['id']].setdefault('checkpoint_mtime', 0)
    running, history, recent_failures = {}, deque(maxlen=20), deque()
    reports = None
    started, last_launch, cooldown = time.time(), 0, 0
    cap = args.max_workers
    target, consecutive_gpu_errors = cap, 0
    allowed_paths = ['experiments/night_20261007', 'MICE/logs/OVERNIGHT_20261007.md',
                     'MiceDuo/logs/OVERNIGHT_20261007.md', 'MICE/results/night_20261007',
                     'MiceDuo/results/night_20261007']

    def event(message):
        stamp = datetime.now().astimezone().isoformat(timespec='seconds')
        print(stamp, message, flush=True)
        with (root / 'events.log').open('a') as handle: handle.write(f'{stamp} {message}\n')

    def stop_job(job_id, why, immediate=False):
        job = running[job_id]
        if job.get('stopping'): return
        job['stopping'], job['stopped_at'] = why, time.time()
        os.killpg(job['p'].pid, signal.SIGKILL if immediate else signal.SIGTERM)
        event(f'PAUSE {job_id}: {why}')

    def publish():
        existing = [p for p in allowed_paths if (repo / p).exists()]
        def git(*arguments):
            return subprocess.run(['git', *arguments], cwd=repo, text=True, capture_output=True, timeout=90)
        # Never consume somebody else's staged work or auto-merge a concurrently edited worktree.
        staged = git('diff', '--cached', '--name-only')
        if staged.returncode or staged.stdout.strip():
            event('PUBLISH deferred: staging area is not empty'); return
        changed = git('status', '--porcelain', '--', *existing)
        if changed.stdout.strip():
            added = git('add', '--', *existing)
            if added.returncode: event('PUBLISH add failed: ' + added.stderr); return
            committed = git('commit', '-m', 'Record overnight MICE replication and DUO development results')
            if committed.returncode: event('PUBLISH commit failed: ' + committed.stderr); return
        pushed = git('push', 'origin', 'HEAD:main')
        if pushed.returncode:
            event('PUBLISH deferred; normal push rejected/failed (no force): ' + pushed.stderr)
        else: event('PUBLISH success: ' + pushed.stderr.strip())

    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
               PYTHONDONTWRITEBYTECODE='1', MICE_CKPT_EVERY='20',
               CUDA_LAUNCH_BLOCKING='0', MICE_ALLOC_MIB='4096',
               TABPFN_MODEL_CACHE_DIR=str(Path.home() / 'pfn-venvs/cache/tabpfn'),
               HF_HUB_OFFLINE='1', TABPFN_DISABLE_TELEMETRY='1')
    env.pop('PYTORCH_CUDA_ALLOC_CONF', None)
    telemetry = (root / 'gpu.csv').open('a', buffering=1)
    if telemetry.tell() == 0: telemetry.write('time,utilization,gpu_mib,ram_available_mib,running,target,done,blocked\n')
    event(f'START: GPU target >=90% subject to stability cap {cap}; pause at 22000 MiB, emergency 23200 MiB, allocator cap 4096 MiB/worker; CUDA_LAUNCH_BLOCKING=0; breaker {args.breaker}/10min')
    try:
        while not STOP and time.time() - started < args.hours * 3600:
            now = time.time()
            for job_id, job in list(running.items()):
                code = job['p'].poll()
                if code is None:
                    if job.get('stopping') and now - job['stopped_at'] > 30:
                        os.killpg(job['p'].pid, signal.SIGKILL)
                    progress = root / 'progress' / (job_id + '.json')
                    last = progress.stat().st_mtime if progress.exists() else job['start']
                    if now - max(last, job['start']) > 1200: stop_job(job_id, 'no progress for 20 minutes')
                    continue
                job['handle'].close(); del running[job_id]
                item = state[job_id]
                if code == 0 and (root / 'done' / (job_id + '.json')).exists():
                    event(f'DONE {job_id}'); consecutive_gpu_errors = 0
                elif job.get('stopping'):
                    item['next'] = now + 90
                else:
                    item['failures'] += 1; item['next'] = now + min(600, 60 * item['failures'])
                    task = next(t for t in tasks if t['id'] == job_id)
                    ck = (root / task['out'] / f"{task['stream']}__{task['method']}.ckpt" if task['kind'] == 'mice'
                          else (root / task['out']).with_suffix('.part.pkl'))
                    mtime = ck.stat().st_mtime if ck.exists() else 0
                    advanced = mtime > item['checkpoint_mtime']
                    item['stalled_failures'] = 0 if advanced else item['stalled_failures'] + 1
                    item['checkpoint_mtime'] = mtime
                    item['blocked'] = item['stalled_failures'] >= 4 or item['failures'] >= 20
                    consecutive_gpu_errors += 1
                    recent_failures.append(now)
                    while recent_failures and recent_failures[0] < now - 600:
                        recent_failures.popleft()
                    failure_limit = 1 if cap == 1 else args.breaker
                    if len(recent_failures) >= failure_limit:
                        reason = f'Circuit breaker: {failure_limit} worker failure(s) within ten minutes; investigate before resuming.'
                        (root / 'STOP').write_text(reason + '\n')
                        event('CIRCUIT BREAKER: ' + reason)
                    event(f'RETRY {job_id} exit={code} failures={item["failures"]} checkpoint_advanced={advanced} blocked={item["blocked"]}')
                    if consecutive_gpu_errors >= 2:
                        target = max(1, len(running)); cooldown = now + 180
                        event(f'COOLDOWN after errors; target={target}')
                atomic_json(state_path, state)
            if reports and reports['p'].poll() is not None:
                code = reports['p'].returncode; reports['handle'].close()
                event(f'ANALYSIS {reports["stage"]} exit={code}')
                if code: (root / 'reports' / (reports['stage'] + '.failed')).write_text(str(code))
                reports = None
                try: publish()
                except Exception as error: event('PUBLISH error: ' + repr(error))
            done = {t['id'] for t in tasks if (root / 'done' / (t['id'] + '.json')).exists()}
            if reports is None:
                for stage in ('k2', 'duo_dev', 'duo_replicates'):
                    members = [t for t in tasks if t['stage'] == stage]
                    marker = root / 'reports' / (stage + '.done')
                    failed = root / 'reports' / (stage + '.failed')
                    if all(t['id'] in done for t in members) and not marker.exists() and not failed.exists():
                        handle = (root / 'logs' / (stage + '_analysis.log')).open('a')
                        p = subprocess.Popen([sys.executable, str(controller / 'analyse.py'), str(root), str(repo), stage],
                                             env=env, stdout=handle, stderr=subprocess.STDOUT)
                        reports = dict(p=p, handle=handle, stage=stage)
                        event('ANALYSIS start ' + stage); break
            sample = subprocess.run(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used',
                                     '--format=csv,noheader,nounits'], capture_output=True, text=True, timeout=10)
            if sample.returncode:
                for job_id in list(running): stop_job(job_id, 'GPU query failed')
                cooldown = now + 90; event('GPU query failed; pausing owned workers'); time.sleep(3); continue
            util, memory = map(int, sample.stdout.strip().splitlines()[0].split(','))
            meminfo = dict(line.split(':', 1) for line in Path('/proc/meminfo').read_text().splitlines())
            available = int(meminfo['MemAvailable'].split()[0]) // 1024
            history.append(util)
            pending = [t for t in tasks if t['id'] not in done and t['id'] not in running
                       and not state[t['id']]['blocked'] and state[t['id']]['next'] <= now]
            blocked = sum(item['blocked'] for item in state.values())
            telemetry.write(f'{datetime.now().astimezone().isoformat(timespec="seconds")},{util},{memory},{available},{len(running)},{target},{len(done)},{blocked}\n')
            if (memory >= 22000 or available < 4096) and running:
                candidates = [k for k,v in running.items() if not v.get('stopping')]
                if candidates:
                    stop_job(candidates[-1], f'resource pressure GPU={memory} MiB RAM_available={available}', memory >= 23200)
                    target = max(1, len(running) - 1); cooldown = now + 180
            elif not (root / 'STOP').exists() and now >= cooldown and pending and memory < 18500 and available > 6500:
                if len(history) >= 8 and np_mean(history) < 94 and now - last_launch > 25:
                    target = min(cap, target + 1)
                if len(running) < target and now - last_launch > 8:
                    task = pending[0]; job_id = task['id']; item = state[job_id]
                    item['attempts'] += 1
                    handle = (root / 'logs' / (job_id + '.log')).open('a', buffering=1)
                    p = subprocess.Popen([sys.executable, '-u', str(controller / 'worker.py'), str(root), job_id],
                                         env=env, stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
                    running[job_id] = dict(p=p, handle=handle, start=now)
                    last_launch = now; event(f'LAUNCH {job_id} pid={p.pid} target={target}')
                    atomic_json(state_path, state)
            atomic_json(root / 'status.json', dict(time=datetime.now().astimezone().isoformat(),
                        utilization=util, gpu_mib=memory, ram_available_mib=available, target=target,
                        running={k:v['p'].pid for k,v in running.items()}, done=len(done), total=len(tasks), blocked=blocked))
            if (root / 'STOP').exists():
                event('STOP file requested graceful shutdown'); break
            if len(done) + blocked == len(tasks) and not running and reports is None: break
            time.sleep(3)
    finally:
        for job_id in list(running): stop_job(job_id, 'supervisor shutdown')
        for job in running.values():
            try: job['p'].wait(timeout=35)
            except subprocess.TimeoutExpired:
                os.killpg(job['p'].pid, signal.SIGKILL); job['p'].wait()
            job['handle'].close()
        if reports:
            try: reports['p'].wait(timeout=120)
            except subprocess.TimeoutExpired: reports['p'].terminate()
        atomic_json(state_path, state)
        status_path = root / 'status.json'
        final_status = json.loads(status_path.read_text()) if status_path.exists() else {}
        final_status.update(state='stopped', running={}, stopped_at=datetime.now().astimezone().isoformat(),
                            reason=(root / 'STOP').read_text().strip() if (root / 'STOP').exists() else 'finished or interrupted')
        atomic_json(status_path, final_status)
        event('STOP: results/checkpoints retained; resume with launch.sh')
        for project in ('MICE', 'MiceDuo'):
            with (repo / project / 'logs/OVERNIGHT_20261007.md').open('a') as handle:
                handle.write(f'\n- {datetime.now().astimezone().isoformat(timespec="seconds")}: 调度器结束；'
                             f'总完成 {sum((root / "done" / (t["id"] + ".json")).exists() for t in tasks)}/{len(tasks)}，'
                             f'失败阻塞 {sum(s["blocked"] for s in state.values())}。详细事件与资源曲线：`{root}`。\n')
        try: publish()
        except Exception as error: event('Final publication failed: ' + repr(error))
        telemetry.close()


def np_mean(values): return sum(values) / len(values)


if __name__ == '__main__':
    def stop(signum, frame):
        global STOP
        STOP = True
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGHUP, stop)
    main()
