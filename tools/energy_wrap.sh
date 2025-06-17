#!/usr/bin/env bash
# Usage: energy_wrap.sh <command> [args…]

set -euo pipefail

SENSOR="/sys/class/powercap/intel-rapl:0/energy_uj"
[[ -r $SENSOR ]] || { echo "› no RAPL sensor – energy n/a"; SENSOR=""; }

start_j=0;  [[ $SENSOR ]] && read -r start_j <"$SENSOR"
start_s=$(date +%s.%N)

"$@"            # run the real workload

end_s=$(date +%s.%N)
end_j=$start_j; [[ $SENSOR ]] && read -r end_j <"$SENSOR"

dur=$(awk "BEGIN{print $end_s - $start_s}")
joules=$((end_j - start_j))
kwh=$(awk "BEGIN{print $joules / 3600000}")

rss=$(awk '/VmRSS/{print $2}' /proc/$$/status 2>/dev/null || echo 0) # kB
cpu=$(grep 'cpu ' /proc/stat | awk '{print $2+$3+$4}')               # jiffies

cat > energy_log.json <<EOF
{
  "duration_s": $dur,
  "kwh": $kwh,
  "ram_kb": $rss,
  "cpu_jiffies": $cpu,
  "cmd": "$(printf '%q ' "$@")"
}
EOF

printf '🌱  %-48s  %.3f kWh  (%ss)\n' "$*" "$kwh" "$dur" | tee energy_log.txt
