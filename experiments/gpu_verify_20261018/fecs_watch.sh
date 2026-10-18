#!/bin/bash
# GPU fault guard (P0 incident 2026-10-18, Codex astra xhigh stopping rule): every 60 s, read the Windows nvlddmkm events
# of the last 3 minutes; on any event (FECS 13, 153, ...) or when the event log cannot be read, write ~/pfn-runs/GPU_STOP
# with the events, stop every GPU job of this project (restart loops first, then their python children) and exit.
# Jobs and chains must not start while GPU_STOP exists. Usage: fecs_watch.sh (background)
L=$HOME/pfn-runs/fecs_watch.log; STOP=$HOME/pfn-runs/GPU_STOP
echo "$(date '+%F %T') watch start" >> $L
while true; do
  ev=$(powershell.exe -NoProfile -Command "try { Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='nvlddmkm'; StartTime=(Get-Date).AddMinutes(-3)} -ErrorAction Stop | ForEach-Object { \$_.TimeCreated.ToString('HH:mm:ss') + ' ' + \$_.Id } } catch { if (\$_.Exception.Message -match 'No events') { 'NONE' } else { 'READFAIL ' + \$_.Exception.Message } }" 2>&1 | tr -d '\r')
  if [ "$ev" != "NONE" ]; then
    { echo "$(date '+%F %T') GPU STOP"; echo "$ev" | head -n 20; } | tee -a $L > $STOP
    for p in $(ps -eo pid,args | grep -E "[p]ool_gpu(_dr)?\.sh|[g]pu_chain|[v]erify_chain" | awk '{print $1}'); do kill $p; done
    sleep 2
    for p in $(ps -eo pid,args | grep -E "[p]ool_gpu\.py|[r]un_task\.py|[t]otgpu/bin/python|[d]rtabpfn/bin/python" | awk '{print $1}'); do kill $p; done
    nvidia-smi --query-compute-apps=pid,process_name --format=csv,noheader >> $L
    exit 0
  fi
  echo "$(date '+%F %T') ok" > $L.last
  sleep 60
done
