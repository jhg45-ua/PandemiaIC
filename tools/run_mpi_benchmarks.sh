#!/bin/bash
# ==============================================================================
# Script de benchmarks y escalabilidad MPI (Speedup y Eficiencia)
# Práctica 3 - Tarea 3 - Ingeniería de los Computadores
# ==============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

RESULTS_DIR="results/mpi"
mkdir -p "$RESULTS_DIR"

CSV_FILE="$RESULTS_DIR/mpi_benchmarks.csv"

# Compilar binario MPI si no existe
if [ ! -f "bin/sim_mpi" ]; then
    echo "[INFO] Compilando version MPI..."
    make all_mpi || exit 1
fi

# Parámetros de simulación por defecto
CONFIG_FILE="${1:-config/policies_ciudad.conf}"
N_HAB="${2:-350000}"
DAYS="${3:-200}"
INITIAL_INFECTED=35
N_SIM="${4:-80}"
SEED=29
STRATEGY="${6:-macro}"     # "macro" o "micro"

# Lista de procesos a evaluar
PROCS=(1 2 4 6 8)

# Detectar hostfile
MPI_EXTRA_ARGS=""
if [ -f "hosts" ] && [ "$5" != "--local" ]; then
    MPI_EXTRA_ARGS="-mca plm_rsh_no_tree_spawn 1 -hostfile hosts"
    MODO_EJECUCION="Cluster (archivo hosts)"
else
    MODO_EJECUCION="Local"
fi

echo "================================================================="
echo "BENCHMARKS MPI - TAREA 3"
echo "================================================================="
echo "Modo        : $MODO_EJECUCION"
echo "Estrategia  : $STRATEGY"
echo "Config      : $CONFIG_FILE"
echo "Poblacion   : $N_HAB habitantes"
echo "Dias        : $DAYS dias"
echo "Replicas    : $N_SIM por politica"
echo "Procesos    : ${PROCS[*]}"
echo "================================================================="
echo ""

echo "Procesos,Estrategia,Tiempo_s,Speedup,Eficiencia_Pct,MCUPS,Pct_Comm" > "$CSV_FILE"

T1=""

for np in "${PROCS[@]}"; do
    LOG_FILE="$RESULTS_DIR/log_np_${np}_${STRATEGY}.txt"
    echo -n "Ejecutando con np=$np ($STRATEGY)... "

    mpirun $MPI_EXTRA_ARGS -np "$np" ./bin/sim_mpi \
        "$CONFIG_FILE" "$N_HAB" "$DAYS" "$INITIAL_INFECTED" "$N_SIM" "$SEED" "$STRATEGY" > "$LOG_FILE" 2>&1

    if [ $? -ne 0 ]; then
        echo "ERROR (ver $LOG_FILE)"
        continue
    fi

    wall_time=$(grep "Total Wall-Clock Time:" "$LOG_FILE" | awk '{print $4}')
    mcups=$(grep "Kernel Throughput (MCUPS):" "$LOG_FILE" | awk '{print $4}')
    comm_pct=$(grep "Total Comm & Sync Time" "$LOG_FILE" | awk -F'(' '{print $2}' | awk -F'%' '{print $1}')

    if [ -z "$wall_time" ]; then
        echo "ERROR extrayendo tiempos."
        continue
    fi

    if [ "$np" -eq 1 ] || [ -z "$T1" ]; then
        T1="$wall_time"
        speedup="1.00"
        efficiency="100.0"
    else
        speedup=$(awk -v t1="$T1" -v tp="$wall_time" 'BEGIN { printf "%.2f", t1 / tp }')
        efficiency=$(awk -v s="$speedup" -v p="$np" 'BEGIN { printf "%.1f", (s / p) * 100.0 }')
    fi

    [ -z "$comm_pct" ] && comm_pct="0.0"

    echo "$np,$STRATEGY,$wall_time,$speedup,$efficiency,$mcups,$comm_pct" >> "$CSV_FILE"
    echo "Hecho (Tiempo: ${wall_time}s | Speedup: ${speedup}x | Eficiencia: ${efficiency}% | Comm: ${comm_pct}%)"
done

echo ""
echo "================================================================="
echo "TABLA DE RESULTADOS (COPIAR Y PEGAR EN LA MEMORIA)"
echo "================================================================="
printf "%-10s | %-12s | %-10s | %-15s | %-10s | %-10s\n" "Procesos" "Tiempo (s)" "Speed-up" "Eficiencia (%)" "MCUPS" "% Comm"
printf -- "-----------+--------------+------------+-----------------+------------+-----------\n"

tail -n +2 "$CSV_FILE" | while IFS=',' read -r p strat t s e mcu comm; do
    printf "%-10s | %-12s | %-10s | %-15s | %-10s | %-10s\n" "$p" "${t} s" "${s}x" "${e}%" "$mcu" "${comm}%"
done

echo "================================================================="
echo "Datos guardados en CSV: $CSV_FILE"
echo "================================================================="
