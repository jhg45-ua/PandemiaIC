#!/bin/bash
# ==============================================================================
# Script de benchmarks y escalabilidad MPI (Speedup y Eficiencia)
# Práctica 3 - Tarea 3 - Ingeniería de los Computadores
# Salida directa por terminal (sin ficheros de logs)
# ==============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

# Compilar binario MPI si no existe
if [ ! -f "bin/sim_mpi" ]; then
    echo "[INFO] Compilando version MPI..."
    make all_mpi || exit 1
fi

# Parámetros de simulación
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
    MPI_EXTRA_ARGS="-hostfile hosts"
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

T1=""
TABLE_ROWS=()

for np in "${PROCS[@]}"; do
    echo "================================================================="
    echo ">>> EJECUTANDO CON NP=$np ($STRATEGY) <<<"
    echo "================================================================="

    # Usar buffer temporal en /tmp que se borra al instante
    TMP_OUT=$(mktemp /tmp/sim_mpi.XXXXXX)

    mpirun $MPI_EXTRA_ARGS -np "$np" ./bin/sim_mpi \
        "$CONFIG_FILE" "$N_HAB" "$DAYS" "$INITIAL_INFECTED" "$N_SIM" "$SEED" "$STRATEGY" > "$TMP_OUT" 2>&1

    # Imprimir todo el contenido por la terminal
    cat "$TMP_OUT"

    wall_time=$(grep "Total Wall-Clock Time:" "$TMP_OUT" | awk '{print $4}')
    mcups=$(grep "Kernel Throughput (MCUPS):" "$TMP_OUT" | awk '{print $4}')
    comm_pct=$(grep "Total Comm & Sync Time" "$TMP_OUT" | awk -F'(' '{print $2}' | awk -F'%' '{print $1}')

    rm -f "$TMP_OUT"

    if [ -z "$wall_time" ]; then
        echo "[ERROR] No se pudo obtener el tiempo para np=$np"
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

    TABLE_ROWS+=("$np,$wall_time,$speedup,$efficiency,$mcups,$comm_pct")
    echo ""
done

echo "================================================================="
echo "TABLA DE RESULTADOS FINAL (COPIAR Y PEGAR EN LA MEMORIA)"
echo "================================================================="
printf "%-10s | %-12s | %-10s | %-15s | %-10s | %-10s\n" "Procesos" "Tiempo (s)" "Speed-up" "Eficiencia (%)" "MCUPS" "% Comm"
printf -- "-----------+--------------+------------+-----------------+------------+-----------\n"

for row in "${TABLE_ROWS[@]}"; do
    IFS=',' read -r p t s e mcu comm <<< "$row"
    printf "%-10s | %-12s | %-10s | %-15s | %-10s | %-10s\n" "$p" "${t} s" "${s}x" "${e}%" "$mcu" "${comm}%"
done

echo "================================================================="
