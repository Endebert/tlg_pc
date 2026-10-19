#!/usr/bin/env bash
# Reproduz o fault de saida 139 em 0x28c193 reproduzindo a entrada gravada em
# port/out/repro.rec (F9, TLG_PAD_RECORD): carregar save, pular o ledging, chamar
# o monstro com R1, cortinas, ser devorado -> crash.
# A gravacao comeca 16 s apos o lancamento (F9 manual); os timestamps sao deslocados
# para que o replay armado desde o inicio reproduza o mesmo instante.
# Uso: scripts/crash_repro.sh [segundos_de_limite=300]
set -uo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
limit=${1:-300}
rec=$root/port/out/repro.rec
shifted=$root/port/out/repro_replay.rec
pad=$root/port/out/pad_input.txt

if [[ ! -s $rec ]]; then
    echo "gravacao ausente: $rec (rode com TLG_PAD_RECORD e F9)" >&2
    exit 2
fi

awk '{ $1 = $1 + 16000; print }' "$rec" > "$shifted"
printf 'replay\n' > "$pad"

# O replay percorre uma sequencia real de historia e avanca o save do jogador; o save fica
# guardado durante a execucao e volta ao lugar depois, para reproduzir nunca custar progresso.
savedata=$root/port/user/savedata
hold=$root/port/user/savedata.repro-hold
restore_hold() {
    if [[ -d $hold ]]; then
        rm -rf "$savedata"
        mv "$hold" "$savedata"
    fi
}
if [[ -d $hold ]]; then
    echo "restaurando save de uma execucao anterior interrompida"
    restore_hold
fi
cp -a "$savedata" "$hold" || { echo "falha ao guardar o save em $hold" >&2; exit 3; }
trap restore_hold EXIT

export TLG_PAD_REPLAY=$shifted
export TLG_PAD_FILE=$pad
export TLG_OFFSCREEN=1
# Silent: no audio device is opened, so nothing to hear and no way to disturb the run
# by changing audio settings while it plays.
export TLG_AUDIO=none

"$root/run_tlg.sh" "$limit" > /dev/null   # stderr kept: a preparation failure must stay visible
rc=$?
restore_hold
trap - EXIT
log=$(readlink -f "$root/port/out/last_run.log")
if [[ $rc -eq 139 ]] && grep -q 'guest offset 0x28c193' "$log"; then
    echo "reproduzido: exit 139 em 0x28c193 (log: $log)"
else
    echo "NAO reproduzido: exit $rc (log: $log)"
fi
exit $rc
