FROM lscr.io/linuxserver/bazarr:latest

COPY custom_libs/subliminal_patch/providers/whisperai.py /tmp/whisperai-fix.py
RUN echo "=== Replacing whisperai.py ===" && \
    find /app -type f -name "whisperai.py" -path "*/providers/*" -exec echo "Replacing: {}" \; -exec cp /tmp/whisperai-fix.py {} \; && \
    echo "=== Clearing __pycache__ ===" && \
    find /app -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    echo "=== Done ==="
