#!/bin/bash
# ==============================================================================
# Script de benchmarks y escalabilidad MPI (Speedup y Eficiencia)
# Práctica 3 - Tarea 3 - Ingeniería de los Computadores
# ==============================================================================

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

# Asegurar permisos de ejecución
chmod +x scripts/*.sh 2>/dev/null || true

# Configuración del entorno de salida
RESULTS_DIR="results/mpi"
mkdir -p "$RESULTS_DIR"

CSV_FILE="$RESULTS_DIR/mpi_benchmarks.csv"
SUMMARY_FILE="$RESULTS_DIR/resumen_escalabilidad.txt"

# Compilar binario MPI si no existe
if [ ! -f "bin/sim_mpi" ]; then
    echo "Compilando versión MPI..."
    make all_mpi || exit 1
fi

# Parámetros de simulación por defecto (ajustables vía variables de entorno o argumentos)
CONFIG_FILE="${1:-config/policies_ciudad.conf}"
N_HAB="${2:-350000}"        # 100.000 habitantes
DAYS="${3:-200}"            # 150 días
INITIAL_INFECTED=35
N_SIM="${4:-80}"           # 80 réplicas (fácilmente divisible entre 1, 2, 4, 8)
SEED=29

# Lista de configuraciones de procesos a evaluar
PROCS=(1 2 4 6 8)

# Detectar si se debe usar el hostfile del clúster o modo local
MPI_EXTRA_ARGS=""
if [ -f "hosts" ] && [ "$5" != "--local" ]; then
    MPI_EXTRA_ARGS="-mca plm_rsh_no_tree_spawn 1 -hostfile hosts"
    MODO_EJECUCION="Clúster Distribuido (usando archivo 'hosts')"
else
    MODO_EJECUCION="Local (múltiples núcleos en esta máquina)"
fi

echo "================================================================="
echo "  BATERÍA DE BENCHMARKS MPI - TAREA 3"
echo "================================================================="
echo "Modo de ejecución    : $MODO_EJECUCION"
echo "Configuración        : $CONFIG_FILE"
echo "Población            : $N_HAB habitantes"
echo "Días                 : $DAYS"
echo "Réplicas Monte Carlo : $N_SIM por política"
echo "Procesos a probar    : ${PROCS[*]}"
echo "Archivo de salida    : $CSV_FILE"
echo "================================================================="
echo ""

# Cabecera del archivo CSV
echo "Procesos,Tiempo_WallClock_s,Speedup,Eficiencia_Pct,Kernel_MCUPS,Macro_Throughput_sim_s" > "$CSV_FILE"

# Variable para almacenar el tiempo base secuencial (T1)
T1=""

# Bucle sobre cada número de procesos
for np in "${PROCS[@]}"; do
    LOG_FILE="$RESULTS_DIR/log_np_${np}.txt"
    echo -n "-> Ejecutando con $np proceso(s) MPI... "

    # Ejecutar mpirun guardando salida en log
    mpirun $MPI_EXTRA_ARGS -np "$np" ./bin/sim_mpi \
        "$CONFIG_FILE" "$N_HAB" "$DAYS" "$INITIAL_INFECTED" "$N_SIM" "$SEED" > "$LOG_FILE" 2>&1

    if [ $? -ne 0 ]; then
        echo "  Error en la ejecución con np=$np (ver $LOG_FILE)"
        continue
    fi

    # Extraer métricas de rendimiento del log
    wall_time=$(grep "Total Wall-Clock Time:" "$LOG_FILE" | awk '{print $4}')
    mcups=$(grep "Kernel Throughput (MCUPS):" "$LOG_FILE" | awk '{print $4}')
    macro_tput=$(grep "Macro Throughput" "$LOG_FILE" | awk '{print $4}')

    if [ -z "$wall_time" ]; then
        echo "  No se pudo extraer el tiempo de ejecución."
        continue
    fi

    # Si es np=1, se toma como referencia secuencial T1
    if [ "$np" -eq 1 ] || [ -z "$T1" ]; then
        T1="$wall_time"
        speedup="1.00"
        efficiency="100.0"
    else
        # Calcular Speedup = T1 / Tp y Eficiencia = (Speedup / p) * 100
        speedup=$(awk -v t1="$T1" -v tp="$wall_time" 'BEGIN { printf "%.2f", t1 / tp }')
        efficiency=$(awk -v s="$speedup" -v p="$np" 'BEGIN { printf "%.1f", (s / p) * 100.0 }')
    fi

    # Guardar fila en CSV
    echo "$np,$wall_time,$speedup,$efficiency,$mcups,$macro_tput" >> "$CSV_FILE"

    echo "  Completado: Tiempo=${wall_time}s | Speedup=${speedup}x | Eficiencia=${efficiency}%"
done

echo ""
echo "================================================================="
echo "  RESUMEN DE RESULTADOS PARA LA MEMORIA (TAREA 3)"
echo "================================================================="
printf "%-10s | %-12s | %-10s | %-14s | %-14s\n" "Procesos" "Tiempo (s)" "Speed-up" "Eficiencia (%)" "MCUPS"
printf -- "-----------+--------------+------------+----------------+---------------\n"

tail -n +2 "$CSV_FILE" | while IFS=',' read -r p t s e mcu mac; do
    printf "%-10s | %-12s | %-10s | %-14s | %-14s\n" "$p" "${t} s" "${s}x" "${e}%" "$mcu"
done | tee "$SUMMARY_FILE"

printf "=================================================================\n"
echo "Datos guardados en:"
echo "  - CSV: $CSV_FILE"
echo "  - Resumen: $SUMMARY_FILE"
echo "  - Logs individuales: $RESULTS_DIR/log_np_*.txt"
echo "================================================================="
