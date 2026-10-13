<p align="center"><img src="port/packaging/icon/tlg-icon-1024.png" width="128" alt=""></p>

<h1 align="center">The Last Guardian — port nativo para PC</h1>

<p align="center">
  <a href="#english"><b>English below</b></a> ·
  <a href="https://github.com/HayatoG/tlg_pc/releases/tag/nightly">Download</a> ·
  <a href="https://www.youtube.com/@hayatog-dev">YouTube</a> ·
  <a href="https://discord.gg/UMkdMYZh9g">Discord</a>
</p>

<p align="center"><a href="https://github.com/HayatoG/tlg_pc/actions/workflows/build.yml"><img src="https://github.com/HayatoG/tlg_pc/actions/workflows/build.yml/badge.svg" alt="Build"></a></p>

**The Last Guardian** (PS4, CUSA03627, update 01.03) rodando no PC com imagem, som, controle e saves, a 30 FPS estáveis e sem emulador de CPU. O código original do jogo roda nativo no processador. O sistema do PS4 é reimplementado, e a GPU é traduzida para Vulkan.

> **Nenhum arquivo do jogo vem com este projeto.** Para jogar, você precisa da sua própria cópia, tirada do seu PS4.

Por **HayatoG** · YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

| | |
|---|---|
| ![Menu inicial](docs/screenshots/01-menu.jpg) | ![O menino desperta na caverna](docs/screenshots/02-despertar.jpg) |
| ![O menino e o Trico](docs/screenshots/03-trico.jpg) | ![Ruínas](docs/screenshots/04-ruinas.jpg) |

<sub>Capturas na resolução nativa (1920×1080), direto da GPU, no Linux com uma RTX 2060.</sub>

## Status

| Área | Estado |
|---|---|
| Boot, menu, intro e gameplay | ✅ Funciona; sessões de 10+ minutos sem falhas |
| Imagem | ✅ Nativa, 1080p, sem tremores |
| Áudio | ✅ Com o `libSceNgs2.sprx` do firmware do seu console |
| Controle | ✅ DualSense, DualShock 4, Xbox e 8BitDo via SDL3, com hot-plug |
| Saves | ✅ Autosave e Continuar |
| Desempenho | ✅ 30 FPS travados, como no PS4 ([60 FPS: #5](https://github.com/HayatoG/tlg_pc/issues/5)) |
| Linux | ✅ Testado (Nobara/Fedora 44) |
| Windows | 🧪 Build automático, ainda sem teste em jogo |
| macOS (Apple Silicon) | 📋 Planejado ([#1](https://github.com/HayatoG/tlg_pc/issues/1)) |

![Desempenho de uma sessão de 10 minutos](docs/screenshots/desempenho.png)

<sub>FPS, pior quadro e draws por quadro a cada 5 s, tirados do log do port (`TLG_FRAME_STATS=1`). Gerado por `scripts/session_chart.py`.</sub>

## Download

O [**build nightly**](https://github.com/HayatoG/tlg_pc/releases/tag/nightly) é gerado pelo GitHub Actions a cada mudança e substitui o anterior:

- **Linux x86-64** (glibc 2.39+: Ubuntu 24.04, Fedora 40, SteamOS 3.6 ou mais novos): `tlg-linux-x86_64.tar.gz`
- **Windows 10/11 64 bits**: `tlg-windows-x86_64.zip`

## Arquivos do jogo necessários

Tudo vem do **seu** PS4 (GoldHEN + Itemzflow). Nada disso vai no download. Use **The Last Guardian CUSA03627 (EUA) com o update 01.03**, montado numa pasta só, com o jogo base e o update por cima. São ~25 GB.

| Arquivo | Vem de | Tamanho | Para quê |
|---|---|---|---|
| `eboot.bin` | update 01.03 | 89 MB | o código do jogo (tem que ser o do 1.03) |
| `sce_module/libc.prx`, `sce_module/libSceFios2.prx` | update 01.03 | 1,5 MB | bibliotecas do próprio jogo |
| `sce_sys/` (`param.sfo`, `playgo-chunk.dat`, `icon0.png`, `pic0.png`, `pic1.png`) | jogo base + update | ~5 MB | metadados, instalação e a arte do launcher |
| `trico_boot.psarc`, `trico_001.psarc`, `trico_002.psarc`, `trico_003.psarc` | jogo base | 2,8 + 5,8 + 5,4 + 6,8 GB | conteúdo principal |
| `trico_bootp.psarc`, `trico_001p.psarc`, `trico_002p.psarc`, `trico_003p.psarc` | update 01.03 | ~1,6 GB | correções do update |
| `trico_enu.psarc` / `trico_ptb.psarc` / `trico_esl.psarc` / `trico_frc.psarc` (+ os `…p.psarc` do update) | base + update | ~280 MB cada | vozes e textos: inglês, português, espanhol, francês |
| `sce_discmap.plt`, `sce_discmap_patch.plt` | base, update | pequenos | mapa de arquivos (recomendado) |

**Do firmware do console (opcional, para ter som):** `libSceNgs2.sprx` (372 KB), de `/system/common/lib/` do seu PS4. Ele vai na pasta `system_lib/` ao lado do executável.

**Como montar a pasta:**
1. No Itemzflow, faça o dump do jogo (`CUSA03627`) e do update (`CUSA03627-patch`) para um pendrive exFAT.
2. No PC, copie a pasta do jogo base e depois copie o conteúdo do update **por cima**, substituindo os arquivos (`eboot.bin`, `sce_module/`, `sce_sys/`).
3. Confira os tamanhos. Arquivos acima de 4 GB vindos pelo FTP do GoldHEN 2.2 chegam cortados, então use o pendrive.

**PC:** placa de vídeo com Vulkan 1.3 (6 GB de VRAM recomendados) e ~25 GB livres.

## Como jogar

1. Extraia o pacote e coloque o `libSceNgs2.sprx` na pasta `system_lib/`.
2. Abra o **The Last Guardian**, escolha a pasta do jogo e o idioma (inglês, português, espanhol ou francês) e clique em **Jogar**.
3. No jogo, **F10** liga o contador de FPS, e **Insert** (ou R3 + L2 no controle) abre o menu do port.
4. Controle (PS4/PS5, Xbox) ou teclado e mouse: o mouse gira a câmera, **Esc** solta o mouse e um clique prende de novo. O layout e o remapeamento estão no [`README-player.md`](port/packaging/README-player.md) e na caixa **Controles** do launcher.

O passo a passo completo, com os problemas mais comuns, está em [`README-player.md`](port/packaging/README-player.md), que também vem dentro do pacote.

## Compilar do código-fonte

```bash
git clone --recursive https://github.com/HayatoG/tlg_pc.git && cd tlg_pc
cd port && TLG_LTO=OFF bash build.sh   # Linux: SDL3, Vulkan, FFmpeg, Boost, fmt, Zydis, glslang
cd .. && ./tlg_launcher.sh             # ou ./run_tlg.sh pelo terminal
```

No Windows, o build roda no MSYS2 CLANG64 ([`port/packaging/windows/README.md`](port/packaging/windows/README.md)). O workflow [`.github/workflows/build.yml`](.github/workflows/build.yml) mostra o processo completo nas duas plataformas.

## Como funciona

| Camada | O que faz | Base |
|---|---|---|
| Loader | Carrega o `eboot.bin` 1.03 e liga os módulos do jogo (`libc.prx`, `libSceFios2.prx`) e o `libSceNgs2.sprx` do console | [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc) |
| Runtime | Reimplementa as bibliotecas do PS4: kernel, threads, arquivos, controle, áudio, saves | gow3_pc + 54 funções novas para o TLG |
| Vídeo | Traduz os comandos Gnm e os shaders GCN para Vulkan/SPIR-V | núcleo de vídeo do [shadPS4](https://github.com/shadps4-emu/shadPS4) |

Os detalhes técnicos (achados no Ghidra, bugs resolvidos, opções `TLG_*`) estão em [`docs/TECNICO.md`](docs/TECNICO.md). O histórico do que foi feito e do que falta está em [`docs/PROGRESSO.md`](docs/PROGRESSO.md).

## Próximos passos

[Roadmap gráfico (#7)](https://github.com/HayatoG/tlg_pc/issues/7): pós-processamento (#2), 60 FPS (#5), efeitos do jogo (#3), resolução interna (#4) e FSR/DLSS (#6). Também estão nas issues o macOS (#1) e as correções que forem aparecendo.

## Créditos e aviso legal

Base de código: [gow3_pc](https://github.com/FelipePrado0/gow3_pc) (FelipePrado0), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) e [shadPS4](https://github.com/shadps4-emu/shadPS4), todos GPL-2.0, assim como este projeto ([LICENSE](port/LICENSE)). Áudio ATRAC9 via [LibAtrac9](https://github.com/Thealexbarney/LibAtrac9).

Este projeto não tem vínculo com a Sony Interactive Entertainment, a SIE Japan Studio ou a genDESIGN. The Last Guardian é marca da Sony Interactive Entertainment. Nenhum código, arquivo ou arte do jogo é distribuído aqui. O ícone é uma arte original do projeto.

---

<a id="english"></a>

# The Last Guardian — native PC port

**The Last Guardian** (PS4, CUSA03627, update 01.03) running on PC with graphics, audio, controller and saves, at a steady 30 FPS and without a CPU emulator. The game's original code runs natively on the processor. The PS4 system is reimplemented, and the GPU is translated to Vulkan.

> **No game files come with this project.** To play, you need your own copy, dumped from your own PS4.

By **HayatoG** · YouTube [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g)

The screenshots and the performance chart are at the top of this page.

## Status

| Area | State |
|---|---|
| Boot, menu, intro and gameplay | ✅ Works; 10+ minute sessions without failures |
| Graphics | ✅ Native 1080p, no shimmering |
| Audio | ✅ With `libSceNgs2.sprx` from your console's firmware |
| Controller | ✅ DualSense, DualShock 4, Xbox and 8BitDo via SDL3, with hot-plug |
| Saves | ✅ Autosave and Continue |
| Performance | ✅ Locked 30 FPS, as on PS4 ([60 FPS: #5](https://github.com/HayatoG/tlg_pc/issues/5)) |
| Linux | ✅ Tested (Nobara/Fedora 44) |
| Windows | 🧪 Automatic build, not yet tested in game |
| macOS (Apple Silicon) | 📋 Planned ([#1](https://github.com/HayatoG/tlg_pc/issues/1)) |

## Download

The [**nightly build**](https://github.com/HayatoG/tlg_pc/releases/tag/nightly) is produced by GitHub Actions on every change and replaces the previous one:

- **Linux x86-64** (glibc 2.39+: Ubuntu 24.04, Fedora 40, SteamOS 3.6 or newer): `tlg-linux-x86_64.tar.gz`
- **Windows 10/11 64-bit**: `tlg-windows-x86_64.zip`

## Required game files

Everything comes from **your own** PS4 (GoldHEN + Itemzflow). None of it is in the download. Use **The Last Guardian CUSA03627 (US) with update 01.03**, merged into one folder, with the base game and the update on top. About 25 GB.

| File | From | Size | Purpose |
|---|---|---|---|
| `eboot.bin` | update 01.03 | 89 MB | the game code (must be the 1.03 one) |
| `sce_module/libc.prx`, `sce_module/libSceFios2.prx` | update 01.03 | 1.5 MB | the game's own libraries |
| `sce_sys/` (`param.sfo`, `playgo-chunk.dat`, `icon0.png`, `pic0.png`, `pic1.png`) | base + update | ~5 MB | metadata, install info and the launcher art |
| `trico_boot.psarc`, `trico_001.psarc`, `trico_002.psarc`, `trico_003.psarc` | base game | 2.8 + 5.8 + 5.4 + 6.8 GB | main content |
| `trico_bootp.psarc`, `trico_001p.psarc`, `trico_002p.psarc`, `trico_003p.psarc` | update 01.03 | ~1.6 GB | update fixes |
| `trico_enu.psarc` / `trico_ptb.psarc` / `trico_esl.psarc` / `trico_frc.psarc` (+ the update's `…p.psarc`) | base + update | ~280 MB each | voices and text: English, Portuguese, Spanish, French |
| `sce_discmap.plt`, `sce_discmap_patch.plt` | base, update | small | file map (recommended) |

**From the console firmware (optional, for audio):** `libSceNgs2.sprx` (372 KB), from `/system/common/lib/` on your PS4. It goes in the `system_lib/` folder next to the executable.

**How to build the folder:**
1. In Itemzflow, dump the game (`CUSA03627`) and the update (`CUSA03627-patch`) to an exFAT USB drive.
2. On the PC, copy the base game folder, then copy the update's contents **over it**, replacing files (`eboot.bin`, `sce_module/`, `sce_sys/`).
3. Check the sizes. Files over 4 GB sent through GoldHEN 2.2's FTP arrive truncated, so use the USB drive.

**PC:** a graphics card with Vulkan 1.3 (6 GB of VRAM recommended) and ~25 GB free.

## How to play

1. Extract the package and put `libSceNgs2.sprx` in the `system_lib/` folder.
2. Open **The Last Guardian**, pick the game folder and the language (English, Portuguese, Spanish or French), and click **Play**.
3. In game, **F10** toggles the FPS counter, and **Insert** (or R3 + L2 on a controller) opens the port's menu.
4. Controller (PS4/PS5, Xbox) or keyboard and mouse: the mouse turns the camera, **Esc** releases the mouse and a click takes it back. The layout and remapping are in [`README-player.md`](port/packaging/README-player.md) and in the launcher's **Controls** box.

The full guide, with common problems, is in [`README-player.md`](port/packaging/README-player.md), which also ships inside the package.

## Building from source

```bash
git clone --recursive https://github.com/HayatoG/tlg_pc.git && cd tlg_pc
cd port && TLG_LTO=OFF bash build.sh   # Linux: SDL3, Vulkan, FFmpeg, Boost, fmt, Zydis, glslang
cd .. && ./tlg_launcher.sh             # or ./run_tlg.sh from a terminal
```

On Windows, the build runs in MSYS2 CLANG64 ([`port/packaging/windows/README.md`](port/packaging/windows/README.md)). The workflow [`.github/workflows/build.yml`](.github/workflows/build.yml) shows the full process on both platforms.

## How it works

| Layer | What it does | Based on |
|---|---|---|
| Loader | Loads `eboot.bin` 1.03 and links the game's modules (`libc.prx`, `libSceFios2.prx`) and the console's `libSceNgs2.sprx` | [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc), [gow3_pc](https://github.com/FelipePrado0/gow3_pc) |
| Runtime | Reimplements the PS4 libraries: kernel, threads, files, controller, audio, saves | gow3_pc + 54 new functions for TLG |
| Video | Translates Gnm commands and GCN shaders to Vulkan/SPIR-V | [shadPS4](https://github.com/shadps4-emu/shadPS4) video core |

Technical notes (Ghidra findings, fixed bugs, `TLG_*` options) are in [`docs/TECNICO.md`](docs/TECNICO.md), in Portuguese. The history of what was done and what is left is in [`docs/PROGRESSO.md`](docs/PROGRESSO.md).

## Next steps

[Graphics roadmap (#7)](https://github.com/HayatoG/tlg_pc/issues/7): post-processing (#2), 60 FPS (#5), game effects (#3), internal resolution (#4) and FSR/DLSS (#6). macOS (#1) and new fixes are tracked in the issues as well.

## Credits and legal notice

Code base: [gow3_pc](https://github.com/FelipePrado0/gow3_pc) (FelipePrado0), [bloodborne_pc](https://github.com/deadinside28/bloodborne_pc) and [shadPS4](https://github.com/shadps4-emu/shadPS4), all GPL-2.0, as is this project ([LICENSE](port/LICENSE)). ATRAC9 audio via [LibAtrac9](https://github.com/Thealexbarney/LibAtrac9).

This project is not affiliated with Sony Interactive Entertainment, SIE Japan Studio or genDESIGN. The Last Guardian is a trademark of Sony Interactive Entertainment. No game code, files or art are distributed here. The icon is original artwork made for this project.
