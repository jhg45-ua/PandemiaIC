#!/bin/bash
# ==============================================================================
# Script de automatización de experimentos y captura de resultados
# Práctica 2 - Ingeniería de los Computadores
# ==============================================================================

# Detener la ejecución si ocurre un error grave
set -e

# 1. Definición de directorios de salida
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

# Crear todas las carpetas si no existen
mkdir -p "$DIR_FLAGS" "$DIR_MARCH" "$DIR_SIMD" "$DIR_LTO" \
         "$DIR_UNROLL" "$DIR_WIDTH" "$DIR_COST" "$DIR_MAX" \
         "$DIR_SIZE" "$DIR_PGO"

# Parámetros de control de tiempo y pausas de reposo (CPU throttling)
DAYS=150
PAUSE_SHORT=5   # Pausa estándar entre pruebas continuas (5 s)
PAUSE_LONG=10   # Pausa prolongada tras cargas masivas (10 s)

echo "================================================================="
echo " INICIANDO BATERÍA COMPLETA DE EXPERIMENTOS DE COMPILACIÓN       "
echo " (Flags, march, SIMD, LTO, Unroll, Width, CostModel, MaxOpt, Size, PGO)"
echo "================================================================="

# ------------------------------------------------------------------------------
# 1. Niveles de optimización general de GCC (results/flags/)
# Escenario fijo: Comunidad Autónoma (scripts/sim_comunidad.sh)
# ------------------------------------------------------------------------------
echo "==> [1/10] Niveles generales de optimización (flags)..."

make clean > /dev/null 2>&1
make OPTFLAGS="-O0" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_FLAGS/base.txt" 2>&1
sleep $PAUSE_SHORT

make clean > /dev/null 2>&1
make OPTFLAGS="-O1" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_FLAGS/01.txt" 2>&1
sleep $PAUSE_SHORT

make clean > /dev/null 2>&1
make OPTFLAGS="-O2" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_FLAGS/02.txt" 2>&1
sleep $PAUSE_SHORT

make clean > /dev/null 2>&1
make OPTFLAGS="-O3" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_FLAGS/03.txt" 2>&1
sleep $PAUSE_SHORT

make clean > /dev/null 2>&1
make OPTFLAGS="-Os" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_FLAGS/Os.txt" 2>&1
sleep $PAUSE_SHORT

make clean > /dev/null 2>&1
make OPTFLAGS="-Ofast" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_FLAGS/0fast.txt" 2>&1
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 2. Microarquitectura e instrucciones vectoriales Intel (results/march/)
# Escenario fijo: Comunidad Autónoma
# ------------------------------------------------------------------------------
echo "==> [2/10] Microarquitectura e instrucciones nativas (-march)..."

make clean > /dev/null 2>&1
make OPTFLAGS="-O3" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_MARCH/03.txt" 2>&1
sleep $PAUSE_SHORT

make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_MARCH/03+native.txt" 2>&1
sleep $PAUSE_SHORT

make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native -mfma" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_MARCH/03+native+fma.txt" 2>&1
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 3. Diagnóstico y evidencias de autovectorización SIMD (results/simd/)
# Escenario fijo: Comunidad Autónoma
# ------------------------------------------------------------------------------
echo "==> [3/10] Informes y diagnósticos de autovectorización SIMD..."

make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native -fopt-info-vec-all=$DIR_SIMD/vec_report.txt" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_SIMD/vec.txt" 2>&1
sleep $PAUSE_SHORT

# Ensamblador anotado (.s)
gcc -std=c99 -Wall -Wextra -O3 -march=native -S -fverbose-asm -Iinclude src/simulador.c -o "$DIR_SIMD/simulador.s" 2>/dev/null || true
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 4. Optimización en Tiempo de Enlace - LTO (results/lto/)
# Escenario fijo: Comunidad Autónoma
# ------------------------------------------------------------------------------
echo "==> [4/10] Optimización en Tiempo de Enlace (-flto)..."

make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native -flto" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_LTO/lto.txt" 2>&1
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 5. Desenrollado Agresivo de Bucles (results/unroll/)
# Escenario fijo: Comunidad Autónoma
# ------------------------------------------------------------------------------
echo "==> [5/10] Desenrollado agresivo de bucles (-funroll-loops)..."

make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native -funroll-loops" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_UNROLL/unroll.txt" 2>&1
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 6. Control de Ancho de Registro SIMD (results/vector_width/)
# Escenario fijo: Comunidad Autónoma
# ------------------------------------------------------------------------------
echo "==> [6/10] Control de ancho de vector SIMD (256 bits vs 512 bits)..."

# Ancho preferido: 256 bits (registros YMM / AVX2)
make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native -mprefer-vector-width=256" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_WIDTH/w256.txt" 2>&1
sleep $PAUSE_SHORT

# Ancho preferido: 512 bits (registros ZMM / AVX-512)
make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native -mprefer-vector-width=512" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_WIDTH/w512.txt" 2>&1
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 7. Modelo de Coste SIMD y Alineación de Bucles (results/cost_model/)
# Escenario fijo: Comunidad Autónoma
# ------------------------------------------------------------------------------
echo "==> [7/10] Modelo de coste vectorial sin restricciones y alineación..."

make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native -fsimd-cost-model=unlimited -falign-loops=32" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_COST/cost_unlimited.txt" 2>&1
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 8. Combinación de Rendimiento Máximo Absoluto (results/max_opt/)
# Escenario fijo: Comunidad Autónoma
# ------------------------------------------------------------------------------
echo "==> [8/10] Combinación máxima de optimización (-Ofast -march=native -flto -funroll-loops)..."

make clean > /dev/null 2>&1
make OPTFLAGS="-Ofast -march=native -flto -funroll-loops" > /dev/null 2>&1
./scripts/sim_comunidad.sh $DAYS > "$DIR_MAX/max_opt.txt" 2>&1
sleep $PAUSE_SHORT

# ------------------------------------------------------------------------------
# 9. Escalado y carga de trabajo según el censo (results/size/)
# Lanzando los scripts individuales para cada escala geográfica
# ------------------------------------------------------------------------------
echo "==> [9/10] Escalado de censo (Ciudad, Provincia, Comunidad, País)..."

make clean > /dev/null 2>&1
make OPTFLAGS="-O3 -march=native" > /dev/null 2>&1

# 1. Escenario Ciudad (~350.000 habitantes)
./scripts/sim_ciudad.sh $DAYS > "$DIR_SIZE/ciudad.txt" 2>&1
sleep $PAUSE_SHORT

# 2. Escenario Provincia (~2.000.000 habitantes)
./scripts/sim_provincia.sh $DAYS > "$DIR_SIZE/provincia.txt" 2>&1
sleep $PAUSE_SHORT

# 3. Escenario Comunidad (~5.100.000 habitantes)
./scripts/sim_comunidad.sh $DAYS > "$DIR_SIZE/comunidad.txt" 2>&1
sleep $PAUSE_LONG

# 4. Escenario País / España (~48.000.000 habitantes)
./scripts/sim_espana.sh $DAYS > "$DIR_SIZE/pais.txt" 2>&1
sleep $PAUSE_LONG

# ------------------------------------------------------------------------------
# 10. Optimización Guiada por Perfil - PGO (results/pgo/)
# Escenario fijo: Comunidad Autónoma
# ------------------------------------------------------------------------------
echo "==> [10/10] Optimización Guiada por Perfil (PGO)..."

# Paso A: Limpieza previa
make clean > /dev/null 2>&1
rm -f src/*.gcda build/*.gcda *.gcda 2>/dev/null || true

# Paso B: Compilación instrumentada
make OPTFLAGS="-O3 -march=native -fprofile-generate" > /dev/null 2>&1

# Paso C: Ejecución de entrenamiento
./scripts/sim_comunidad.sh $DAYS > /dev/null 2>&1
sleep $PAUSE_SHORT

# Paso D: Recompilación basada en perfil
make OPTFLAGS="-O3 -march=native -fprofile-use" > /dev/null 2>&1

# Paso E: Evaluación final guardando resultados
./scripts/sim_comunidad.sh $DAYS > "$DIR_PGO/pgo.txt" 2>&1
sleep $PAUSE_SHORT

# Paso F: Limpieza final de temporales
rm -f src/*.gcda build/*.gcda *.gcda 2>/dev/null || true

echo "================================================================="
echo " ¡PROCESO COMPLETADO!                                            "
echo " Todos los resultados se han generado en la estructura 'results/'"
echo "================================================================="