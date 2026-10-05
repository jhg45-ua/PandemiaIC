#!/bin/bash
# ==============================================================================
# PandemicSim - Simulación Escala Comunidad Autónoma (Comunitat Valenciana)
# ==============================================================================

# Navegar a la raíz del repositorio
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

# Compilar si el binario no existe
if [ ! -f "bin/sim" ]; then
    echo "Compilando el simulador..."
    make all || exit 1
fi

CONFIG_FILE="config/policies_comunidad.conf"
N_HAB=5100000       # ~5.100.000 hab -> Malla de 2258x2258 (5.098.564 celdas)
DAYS=${1:-200}      # 200 días por defecto (o argumento $1)
INITIAL_INFECTED=350 # 350 focos iniciales distribuidos por las tres provincias

echo "================================================================="
echo "  LANZANDO SIMULACIÓN: COMUNITAT VALENCIANA"
echo "================================================================="
echo "Configuración     : $CONFIG_FILE"
echo "Población         : $N_HAB habitantes (~5.1M)"
echo "Días de simulación: $DAYS días"
echo "Focos iniciales   : $INITIAL_INFECTED infectados"
echo "================================================================="
echo ""

./bin/sim "$CONFIG_FILE" "$N_HAB" "$DAYS" "$INITIAL_INFECTED"
