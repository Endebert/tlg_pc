#!/usr/bin/env bash
# Abre o launcher do The Last Guardian, edição Qt Quick (PySide6) — o padrão dos pacotes.
# Sem janela (mesmas configurações do botão Play): ./tlg_launcher_qt.sh --play
# Teste de fumaça sem janela: ./tlg_launcher_qt.sh --selftest
# Variáveis TLG_* no ambiente têm prioridade (ex.: TLG_READBACKS=1 ./tlg_launcher_qt.sh --play).
#
# Não exporta LD_LIBRARY_PATH: o PySide6 é do sistema. Esse export é do launcher Tk
# (./tlg_launcher.sh), que carrega o tk8.6 extraído em ~/.local/lib — os dois abrem o mesmo
# ~/.config/tlg-launcher/settings.json e passam pelo mesmo tlg_run.prepare/launch.
exec python3 "$(dirname -- "$(realpath -- "$0")")/port/launcher/tlg_launcher_qt.py" "$@"
