#!/bin/bash
# ==============================================================================
# Script de automatización de experimentos y captura de resultados
# Práctica 2 - Ingeniería de los Computadores
# ==============================================================================

# 1. Dar permisos de ejecución a todos los scripts auxiliares
chmod +x scripts/*.sh 2>/dev/null || true

# 2. Definición de directorios de salida
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

DAYS=150
PAUSE_SHORT=5
PAUSE_LONG=10

# Función auxiliar para compilar y ejecutar de forma segura
run_test() {
    local opt_flags="$1"
    local run_script="$2"
    local output_file="$3"
    local pause_time="$4"

    make clean > /dev/null 2>&1
    if ! make OPTFLAGS="$opt_flags" > /dev/null 2>&1; then
        echo "   [ERROR] Falló la compilación con OPTFLAGS=\"$opt_flags\"."
        echo "   Revisa si el compilador soporta estos flags en tu sistema."
        return 1
    fi

    if ! "$run_script" "$DAYS" > "$output_file" 2>&1; then
        echo "   [ERROR] Falló la ejecución de $run_script."
        return 1
    fi

    sleep "${pause_time:-$PAUSE_SHORT}"
}

echo "================================================================="
echo " INICIANDO BATERÍA COMPLETA DE EXPERIMENTOS DE COMPILACIÓN       "
echo "================================================================="

# ------------------------------------------------------------------------------
# 1. Niveles generales de optimización (results/flags/)
# ------------------------------------------------------------------------------
echo "==> [1/10] Niveles generales de optimización (flags)..."
run_test "-O0" "./scripts/run_comunidad.sh" "$DIR_FLAGS/base.txt"
run_test "-O1" "./scripts/run_comunidad.sh" "$DIR_FLAGS/01.txt"
run_test "-O2" "./scripts/run_comunidad.sh" "$DIR_FLAGS/02.txt"
run_test "-O3" "./scripts/run_comunidad.sh" "$DIR_FLAGS/03.txt"
run_test "-Os" "./scripts/run_comunidad.sh" "$DIR_FLAGS/Os.txt"
run_test "-Ofast" "./scripts/run_comunidad.sh" "$DIR_FLAGS/0fast.txt"

# ------------------------------------------------------------------------------
# 2. Microarquitectura (results/march/)
# ------------------------------------------------------------------------------
echo "==> [2/10] Microarquitectura e instrucciones nativas (-march)..."
run_test "-O3" "./scripts/run_comunidad.sh" "$DIR_MARCH/03.txt"
run_test "-O3 -march=native" "./scripts/run_comunidad.sh" "$DIR_MARCH/03+native.txt"
run_test "-O3 -march=native -mfma" "./scripts/run_comunidad.sh" "$DIR_MARCH/03+native+fma.txt"

# ------------------------------------------------------------------------------
# 3. Diagnóstico SIMD (results/simd/)
# ------------------------------------------------------------------------------
echo "==> [3/10] Informes y diagnósticos de autovectorización SIMD..."
make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native" > /dev/null 2>&1 || true
./scripts/run_comunidad.sh $DAYS > "$DIR_SIMD/vec.txt" 2>&1 || true
gcc -std=c99 -Wall -Wextra -O3 -march=native -S -fverbose-asm -Iinclude src/simulador.c -o "$DIR_SIMD/simulador.s" 2>/dev/null || true
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 4. LTO (results/lto/)
# ------------------------------------------------------------------------------
echo "==> [4/10] Optimización en Tiempo de Enlace (-flto)..."
run_test "-O3 -march=native -flto" "./scripts/run_comunidad.sh" "$DIR_LTO/lto.txt"

# ------------------------------------------------------------------------------
# 5. Unroll (results/unroll/)
# ------------------------------------------------------------------------------
echo "==> [5/10] Desenrollado de bucles (-funroll-loops)..."
run_test "-O3 -march=native -funroll-loops" "./scripts/run_comunidad.sh" "$DIR_UNROLL/unroll.txt"

# ------------------------------------------------------------------------------
# 6. Ancho de vector (results/vector_width/)
# ------------------------------------------------------------------------------
echo "==> [6/10] Control de ancho de vector SIMD..."
run_test "-O3 -march=native -mprefer-vector-width=256" "./scripts/run_comunidad.sh" "$DIR_WIDTH/w256.txt"
run_test "-O3 -march=native -mprefer-vector-width=512" "./scripts/run_comunidad.sh" "$DIR_WIDTH/w512.txt"

# ------------------------------------------------------------------------------
# 7. Modelo de coste (results/cost_model/)
# ------------------------------------------------------------------------------
echo "==> [7/10] Modelo de coste vectorial sin restricciones..."
run_test "-O3 -march=native -fsimd-cost-model=unlimited -falign-loops=32" "./scripts/run_comunidad.sh" "$DIR_COST/cost_unlimited.txt"

# ------------------------------------------------------------------------------
# 8. Combinación Máxima (results/max_opt/)
# ------------------------------------------------------------------------------
echo "==> [8/10] Combinación máxima de optimización..."
run_test "-Ofast -march=native -flto -funroll-loops" "./scripts/run_comunidad.sh" "$DIR_MAX/max_opt.txt"

# ------------------------------------------------------------------------------
# 9. Escalado de Censo (results/size/)
# ------------------------------------------------------------------------------
echo "==> [9/10] Escalado de censo (Ciudad, Provincia, Comunidad, País)..."
make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native" > /dev/null 2>&1 || true

./scripts/run_ciudad.sh $DAYS > "$DIR_SIZE/ciudad.txt" 2>&1 || true
sleep $PAUSE_SHORT

./scripts/run_provincia.sh $DAYS > "$DIR_SIZE/provincia.txt" 2>&1 || true
sleep $PAUSE_SHORT

./scripts/run_comunidad.sh $DAYS > "$DIR_SIZE/comunidad.txt" 2>&1 || true
sleep $PAUSE_LONG

./scripts/run_espana.sh $DAYS > "$DIR_SIZE/pais.txt" 2>&1 || true
sleep $PAUSE_LONG

# ------------------------------------------------------------------------------
# 10. PGO (results/pgo/)
# ------------------------------------------------------------------------------
echo "==> [10/10] Optimización Guiada por Perfil (PGO)..."
make clean > /dev/null 2>&1
rm -f src/*.gcda build/*.gcda *.gcda 2>/dev/null || true

if make OPTFLAGS="-O3 -march=native -fprofile-generate" > /dev/null 2>&1; then
    ./scripts/run_comunidad.sh $DAYS > /dev/null 2>&1 || true
    sleep $PAUSE_SHORT
    make OPTFLAGS="-O3 -march=native -fprofile-use" > /dev/null 2>&1 || true
    ./scripts/run_comunidad.sh $DAYS > "$DIR_PGO/pgo.txt" 2>&1 || true
    rm -f src/*.gcda build/*.gcda *.gcda 2>/dev/null || true
else
    echo "   [AVISO] PGO no es soportado por el compilador actual o fallo al instrumentar."
fi

echo "================================================================="
echo " ¡PROCESO COMPLETADO!                                            "
echo "================================================================="