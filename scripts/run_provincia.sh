#!/bin/bash
# ==============================================================================
# PandemicSim - Simulación Escala Provincia (Provincia de Alicante)
# ==============================================================================

# Navegar a la raíz del repositorio
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

# Compilar si el binario no existe
if [ ! -f "bin/sim" ]; then
    echo "Compilando el simulador..."
    make all || exit 1
fi

CONFIG_FILE="config/policies_provincia.conf"
N_HAB=2000000       # ~2.000.000 hab -> Malla de 1414x1414 (1.999.396 celdas)
DAYS=${1:-200}      # 200 días por defecto (o argumento $1)
INITIAL_INFECTED=150 # 150 focos iniciales distribuidos por comarcas

echo "================================================================="
echo "  LANZANDO SIMULACIÓN: PROVINCIA DE ALICANTE"
echo "================================================================="
echo "Configuración     : $CONFIG_FILE"
echo "Población         : $N_HAB habitantes (~2.0M)"
echo "Días de simulación: $DAYS días"
echo "Focos iniciales   : $INITIAL_INFECTED infectados"
echo "Tiempo secuencial : ~25 - 30 segundos (¡Ideal para Speedup!)"
echo "================================================================="
echo ""

./bin/sim "$CONFIG_FILE" "$N_HAB" "$DAYS" "$INITIAL_INFECTED"
