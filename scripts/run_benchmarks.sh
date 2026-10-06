#!/bin/bash
# ==============================================================================
# Script de automatización de experimentos con modo Verbose y Timestamps
# Práctica 2 - Ingeniería de los Computadores
# ==============================================================================

# 1. Dar permisos de ejecución a todos los scripts auxiliares
chmod +x scripts/*.sh 2>/dev/null || true

# 2. Control de argumento Verbose (-v o --verbose)
VERBOSE=false
if [ "$1" == "-v" ] || [ "$1" == "--verbose" ]; then
    VERBOSE=true
fi

# 3. Definición de directorios de salida
DIR_FLAGS="results/flags"
DIR_MARCH="results/march"
DIR_SIMD="results/simd"
DIR_LTO="results/lto"
DIR_UNROLL="results/unroll"
DIR_WIDTH="results/vector_width"
DIR_COST="results/cost_model"
DIR_MAX="results/max_opt"
DIR_SIZE="results/size"
DIR_PGO="results/pgo"

mkdir -p "$DIR_FLAGS" "$DIR_MARCH" "$DIR_SIMD" "$DIR_LTO" \
         "$DIR_UNROLL" "$DIR_WIDTH" "$DIR_COST" "$DIR_MAX" \
         "$DIR_SIZE" "$DIR_PGO"

DAYS=200
PAUSE_SHORT=5
PAUSE_LONG=10

# Función para imprimir con sello de tiempo
log_msg() {
    echo "[$(date +'%H:%M:%S')] $1"
}

# Función auxiliar para compilar y ejecutar de forma transparente
run_test() {
    local opt_flags="$1"
    local run_script="$2"
    local output_file="$3"
    local pause_time="${4:-$PAUSE_SHORT}"

    log_msg "  -> [COMPILANDO] Flags: \"$opt_flags\"..."
    make clean > /dev/null 2>&1

    if [ "$VERBOSE" = true ]; then
        make OPTFLAGS="$opt_flags"
    else
        make OPTFLAGS="$opt_flags" > /dev/null 2>&1
    fi

    if [ $? -ne 0 ]; then
        log_msg "   [ERROR] Falló la compilación con OPTFLAGS=\"$opt_flags\"."
        return 1
    fi

    log_msg "  -> [EJECUTANDO] $run_script (Guardando en $output_file)..."
    
    if [ "$VERBOSE" = true ]; then
        # En modo verbose muestra la salida por pantalla y guarda en fichero a la vez
        "$run_script" "$DAYS" 2>&1 | tee "$output_file"
    else
        "$run_script" "$DAYS" > "$output_file" 2>&1
    fi

    if [ ${PIPESTATUS[0]} -ne 0 ]; then
        log_msg "   [ERROR] Falló la ejecución de $run_script."
        return 1
    fi

    log_msg "  -> [OK] Finalizado. Reposando CPU (${pause_time}s)..."
    sleep "$pause_time"
}

echo "================================================================="
log_msg "INICIANDO BATERÍA COMPLETA DE EXPERIMENTOS DE COMPILACIÓN"
if [ "$VERBOSE" = true ]; then
    log_msg "Modo VERBOSE activado."
else
    log_msg "Modo Estándar. Para ver progreso en tiempo real usa: $0 -v"
fi
echo "================================================================="

# ------------------------------------------------------------------------------
# 1. Niveles generales de optimización (results/flags/)
# ------------------------------------------------------------------------------
log_msg "==> [1/10] Niveles generales de optimización (flags)..."
run_test "-O0" "./scripts/run_ciudad.sh" "$DIR_FLAGS/base.txt"
run_test "-O1" "./scripts/run_ciudad.sh" "$DIR_FLAGS/01.txt"
run_test "-O2" "./scripts/run_ciudad.sh" "$DIR_FLAGS/02.txt"
run_test "-O3" "./scripts/run_ciudad.sh" "$DIR_FLAGS/03.txt"
run_test "-Os" "./scripts/run_ciudad.sh" "$DIR_FLAGS/Os.txt"
run_test "-Ofast" "./scripts/run_ciudad.sh" "$DIR_FLAGS/0fast.txt"

# ------------------------------------------------------------------------------
# 2. Microarquitectura (results/march/)
# ------------------------------------------------------------------------------
log_msg "==> [2/10] Microarquitectura e instrucciones nativas (-march)..."
run_test "-O3" "./scripts/run_ciudad.sh" "$DIR_MARCH/03.txt"
run_test "-O3 -march=native" "./scripts/run_ciudad.sh" "$DIR_MARCH/03+native.txt"
run_test "-O3 -march=native -mfma" "./scripts/run_ciudad.sh" "$DIR_MARCH/03+native+fma.txt"

# ------------------------------------------------------------------------------
# 3. Diagnóstico SIMD (results/simd/)
# ------------------------------------------------------------------------------
log_msg "==> [3/10] Informes y diagnósticos de autovectorización SIMD..."
make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native" > /dev/null 2>&1 || true
log_msg "  -> [EJECUTANDO] ./scripts/run_ciudad.sh..."
./scripts/run_ciudad.sh $DAYS > "$DIR_SIMD/vec.txt" 2>&1 || true
log_msg "  -> [GENERANDO] Fichero de ensamblador anotado (.s)..."
gcc -std=c99 -Wall -Wextra -O3 -march=native -S -fverbose-asm -Iinclude src/simulador.c -o "$DIR_SIMD/simulador.s" 2>/dev/null || true
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 4. LTO (results/lto/)
# ------------------------------------------------------------------------------
log_msg "==> [4/10] Optimización en Tiempo de Enlace (-flto)..."
run_test "-O3 -march=native -flto" "./scripts/run_ciudad.sh" "$DIR_LTO/lto.txt"

# ------------------------------------------------------------------------------
# 5. Unroll (results/unroll/)
# ------------------------------------------------------------------------------
log_msg "==> [5/10] Desenrollado de bucles (-funroll-loops)..."
run_test "-O3 -march=native -funroll-loops" "./scripts/run_ciudad.sh" "$DIR_UNROLL/unroll.txt"

# ------------------------------------------------------------------------------
# 6. Ancho de vector (results/vector_width/)
# ------------------------------------------------------------------------------
log_msg "==> [6/10] Control de ancho de vector SIMD..."
run_test "-O3 -march=native -mprefer-vector-width=256" "./scripts/run_ciudad.sh" "$DIR_WIDTH/w256.txt"
run_test "-O3 -march=native -mprefer-vector-width=512" "./scripts/run_ciudad.sh" "$DIR_WIDTH/w512.txt"

# ------------------------------------------------------------------------------
# 7. Modelo de coste (results/cost_model/)
# ------------------------------------------------------------------------------
log_msg "==> [7/10] Modelo de coste vectorial sin restricciones..."
run_test "-O3 -march=native -fsimd-cost-model=unlimited -falign-loops=32" "./scripts/run_ciudad.sh" "$DIR_COST/cost_unlimited.txt"

# ------------------------------------------------------------------------------
# 8. Combinación Máxima (results/max_opt/)
# ------------------------------------------------------------------------------
log_msg "==> [8/10] Combinación máxima de optimización..."
run_test "-Ofast -march=native -flto -funroll-loops" "./scripts/run_ciudad.sh" "$DIR_MAX/max_opt.txt"

# ------------------------------------------------------------------------------
# 9. Escalado de Censo (results/size/)
# ------------------------------------------------------------------------------
log_msg "==> [9/10] Escalado de censo (Ciudad, Provincia, Comunidad, País)..."
make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native" > /dev/null 2>&1 || true

log_msg "  -> Ejecutando Escala Ciudad..."
./scripts/run_ciudad.sh $DAYS > "$DIR_SIZE/ciudad.txt" 2>&1 || true
sleep $PAUSE_SHORT

log_msg "  -> Ejecutando Escala Provincia..."
./scripts/run_provincia.sh $DAYS > "$DIR_SIZE/provincia.txt" 2>&1 || true
sleep $PAUSE_SHORT

log_msg "  -> Ejecutando Escala Comunidad..."
./scripts/run_comunidad.sh $DAYS > "$DIR_SIZE/comunidad.txt" 2>&1 || true
sleep $PAUSE_LONG

log_msg "  -> Ejecutando Escala País..."
./scripts/run_espana.sh $DAYS > "$DIR_SIZE/pais.txt" 2>&1 || true
sleep $PAUSE_LONG

# ------------------------------------------------------------------------------
# 10. PGO (results/pgo/)
# ------------------------------------------------------------------------------
log_msg "==> [10/10] Optimización Guiada por Perfil (PGO)..."
make clean > /dev/null 2>&1
rm -f src/*.gcda build/*.gcda *.gcda 2>/dev/null || true

if make OPTFLAGS="-O3 -march=native -fprofile-generate" > /dev/null 2>&1; then
    log_msg "  -> Paso PGO 1: Ejecutando simulación de entrenamiento..."
    ./scripts/run_ciudad.sh $DAYS > /dev/null 2>&1 || true
    sleep $PAUSE_SHORT
    log_msg "  -> Paso PGO 2: Recompilando con -fprofile-use..."
    make OPTFLAGS="-O3 -march=native -fprofile-use" > /dev/null 2>&1 || true
    log_msg "  -> Paso PGO 3: Ejecutando simulación de evaluación final..."
    ./scripts/run_ciudad.sh $DAYS > "$DIR_PGO/pgo.txt" 2>&1 || true
    rm -f src/*.gcda build/*.gcda *.gcda 2>/dev/null || true
else
    log_msg "   [AVISO] PGO no es soportado por el compilador actual o falló al instrumentar."
fi

echo "================================================================="
log_msg "¡PROCESO COMPLETADO EXITOSAMENTE!"
echo "================================================================="