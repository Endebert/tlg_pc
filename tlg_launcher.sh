#!/usr/bin/env bash
# Abre o launcher do The Last Guardian (configurações, idioma, jogar).
# Sem janela (mesmas configurações do botão Play): ./tlg_launcher.sh --play
# Teste cronometrado com sonda de upscaler: ./tools/test-run [segundos]
# Variáveis TLG_* no ambiente têm prioridade (ex.: TLG_RESOLUTION=1920x1080 ./tlg_launcher.sh --play).
#
# Tk foi extraído em ~/.local/lib (o sistema não tem tk8.6): a janela precisa do LD_LIBRARY_PATH
# e das bibliotecas TCL/TK. Só para a GUI — tlg_run/test-run não importam tkinter.
export LD_LIBRARY_PATH="$HOME/.local/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export TCL_LIBRARY="${TCL_LIBRARY:-/usr/lib/tcl8.6}"
export TK_LIBRARY="${TK_LIBRARY:-$HOME/.local/lib/tk8.6}"
exec python3 "$(dirname -- "$(realpath -- "$0")")/port/launcher/tlg_launcher.py" "$@"
