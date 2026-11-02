echo "=== USUARIO ACTUAL ===" && whoami && id && \
echo -e "\n=== USUARIOCP ===" && (id usuariocp 2>/dev/null || echo "No existe usuariocp") && \
echo -e "\n=== PERMISOS DE HOME Y .SSH ===" && \
ls -ld /home/usuariocp $HOME 2>/dev/null && \
ls -ld /home/usuariocp/.ssh ~/.ssh 2>/dev/null && \
ls -la /home/usuariocp/.ssh 2>/dev/null || ls -la ~/.ssh 2>/dev/null && \
echo -e "\n=== PERMISOS CARPETA PROYECTO ===" && \
ls -ld ~/Documentos/PandemiaIC /home/usuariocp/Documentos/PandemiaIC 2>/dev/null