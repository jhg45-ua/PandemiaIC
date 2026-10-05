#!/bin/bash
# ==============================================================================
# PandemicSim - Simulación Escala Ciudad (Alicante Capital)
# ==============================================================================

# Navegar a la raíz del repositorio
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

# Compilar si el binario no existe
if [ ! -f "bin/sim" ]; then
    echo "Compilando el simulador..."
    make all || exit 1
fi

CONFIG_FILE="config/policies_ciudad.conf"
N_HAB=350000        # ~350.000 hab -> Malla de 591x591 (349.281 celdas)
DAYS=${1:-200}      # 200 días por defecto (o argumento $1)
INITIAL_INFECTED=35 # 35 focos iniciales distribuidos por barrios

echo "================================================================="
echo "  LANZANDO SIMULACIÓN: ALICANTE CAPITAL"
echo "================================================================="
echo "Configuración     : $CONFIG_FILE"
echo "Población         : $N_HAB habitantes (~350k)"
echo "Días de simulación: $DAYS días"
echo "Focos iniciales   : $INITIAL_INFECTED infectados"
echo "================================================================="
echo ""

./bin/sim "$CONFIG_FILE" "$N_HAB" "$DAYS" "$INITIAL_INFECTED"
