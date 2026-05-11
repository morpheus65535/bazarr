FROM lscr.io/linuxserver/bazarr:latest

COPY custom_libs/subliminal_patch/providers/whisperai.py /app/custom_libs/subliminal_patch/providers/whisperai.py
