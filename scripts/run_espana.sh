#!/bin/bash
# ==============================================================================
# PandemicSim - Simulación Escala Nacional (España)
# ==============================================================================

# Navegar a la raíz del repositorio
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

# Compilar si el binario no existe
if [ ! -f "bin/sim" ]; then
    echo "Compilando el simulador..."
    make all || exit 1
fi

CONFIG_FILE="config/policies_espana.conf"
N_HAB=48000000        # ~48.000.000 hab -> Malla de 6928x6928 (47.997.184 celdas)
DAYS=${1:-200}        # 200 días por defecto (o argumento $1)
INITIAL_INFECTED=3200 # 3.200 focos iniciales distribuidos por CCAA y provincias
N_SIM=320             # 320 réplicas Monte Carlo por política

echo "================================================================="
echo "  LANZANDO SIMULACIÓN: ESPAÑA (ESCALA NACIONAL)"
echo "================================================================="
echo "Configuración        : $CONFIG_FILE"
echo "Población            : $N_HAB habitantes (~48.0M)"
echo "Días de simulación.  : $DAYS días"
echo "Focos iniciales      : $INITIAL_INFECTED infectados"
echo "Réplicas Monte Carlo : $N_SIM por política"
echo "================================================================="
echo ""

./bin/sim "$CONFIG_FILE" "$N_HAB" "$DAYS" "$INITIAL_INFECTED" "$N_SIM"