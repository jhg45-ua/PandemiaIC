#!/bin/bash
# ==============================================================================
# Script de sincronización de ejecutables con los nodos del clúster MPI
# Práctica 3 - Ingeniería de los Computadores
# ==============================================================================

# Navegar a la raíz del repositorio
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT" || exit 1

HOSTS_FILE="hosts"
TARGET_DIR="~/"

# 1. Compilar la versión MPI si es necesario
echo "=== [1/3] Compilando binario MPI (sim_mpi) ==="
make all_mpi
if [ $? -ne 0 ]; then
    echo "❌ Error en la compilación. Abortando sincronización."
    exit 1
fi
echo "Binario listo: bin/sim_mpi"
echo ""

chmod 777 -R *

# 2. Obtener lista de nodos remotos
if [ ! -f "$HOSTS_FILE" ]; then
    echo "Archivo '$HOSTS_FILE' no encontrado."
    echo "Introduce las IPs de los nodos separadas por espacio (ej: 172.21.242.232 172.21.242.233):"
    read -r -a NODES
else
    # Extraer IPs o hostnames evitando localhost y comentarios
    mapfile -t NODES < <(grep -v '^[[:space:]]*#' "$HOSTS_FILE" | grep -v '^[[:space:]]*$' | awk '{print $1}' | grep -v '127.0.0.1' | grep -v 'localhost')
fi

if [ ${#NODES[@]} -eq 0 ]; then
    echo "No se detectaron nodos remotos en $HOSTS_FILE (solo localhost o lista vacía)."
    exit 0
fi

echo "=== [2/3] Nodos destino detectados ==="
for node in "${NODES[@]}"; do
    echo "  - $node"
done
echo ""

# 3. Transferir el ejecutable y configuraciones a cada nodo
echo "=== [3/3] Sincronizando con los nodos ==="
for node in "${NODES[@]}"; do
    echo "-> Enviando a $node..."
    # Asegurar que el directorio de destino existe
    ssh -o ConnectTimeout=4 -o BatchMode=yes "$node" "mkdir -p $TARGET_DIR/bin $TARGET_DIR/config" 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "     No se pudo conectar vía SSH con $node. Comprueba la IP y la clave SSH."
        continue
    fi

    # Copiar binario y archivos de configuración
    scp bin/sim_mpi "$node:$TARGET_DIR/bin/" >/dev/null 2>&1
    scp config/*.conf "$node:$TARGET_DIR/config/" >/dev/null 2>&1
    ssh "$node" "chmod +x $TARGET_DIR/bin/sim_mpi" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "     Sincronización exitosa en $node"
    else
        echo "     Fallo al copiar archivos a $node"
    fi
done

echo ""
echo "================================================================="
echo "  SINCRONIZACIÓN FINALIZADA"
echo "================================================================="
