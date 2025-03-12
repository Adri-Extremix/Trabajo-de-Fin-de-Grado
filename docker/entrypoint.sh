#!/bin/bash

# Configura perf_event_paranoid (requiere --privileged o --security-opt seccomp=unconfined)
sysctl -w kernel.perf_event_paranoid=1 2>/dev/null || true

# Mensaje de verificación
echo "=== RR está listo ==="
exec "$@"