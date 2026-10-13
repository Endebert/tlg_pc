# The Last Guardian — port para PC / PC port

Por HayatoG · YouTube: [@hayatog-dev](https://www.youtube.com/@hayatog-dev) · Discord: [discord.gg/UMkdMYZh9g](https://discord.gg/UMkdMYZh9g) · Código: [github.com/HayatoG/tlg_pc](https://github.com/HayatoG/tlg_pc)

**Nenhum arquivo do jogo vem neste pacote.** Você precisa da sua própria cópia de The Last Guardian para PS4. / **No game files are included.** You need your own copy of The Last Guardian for PS4.

Versão experimental: o jogo roda do início ao gameplay, mas ainda pode travar em áreas não testadas. / Experimental build: the game runs from boot to gameplay, but may still crash in untested areas.

---

## Português

### O que você precisa

| Item | Onde conseguir | Obrigatório |
|---|---|---|
| Pasta do jogo **CUSA03627 com o update 01.03** (EUA): `eboot.bin`, `sce_module/` (`libc.prx`, `libSceFios2.prx`), `sce_sys/` e `trico_boot.psarc`, `trico_001.psarc`, `trico_002.psarc`, `trico_003.psarc` | Dump do seu PS4 desbloqueado: o jogo base mesclado com o patch 1.03 (o `eboot.bin` precisa ser o do 1.03) | Sim |
| `libSceNgs2.sprx` | Firmware do seu PS4, em `/system/common/lib/` (por FTP com o GoldHEN, por exemplo) | Só para ter som |
| PC | Windows 10 (1903+) / 11 de 64 bits, ou Linux x86-64 (glibc 2.39+: Ubuntu 24.04, Fedora 40, SteamOS 3.6 ou mais novos) | Sim |
| Placa de vídeo | Vulkan 1.3 com driver atualizado; 6 GB de VRAM recomendados | Sim |
| Espaço | ~25 GB para os arquivos do jogo | Sim |

Os arquivos `.psarc` acima de 4 GiB chegam truncados pelo FTP do GoldHEN 2.2. Copie-os por USB (Itemzflow, por exemplo) e confira os tamanhos.

### Como jogar

1. Extraia o pacote numa pasta qualquer (no Windows, fora do .zip).
2. Coloque o `libSceNgs2.sprx` na pasta `system_lib/`, ao lado do executável (opcional, para ter som).
3. Abra **The Last Guardian** (`The Last Guardian.exe` no Windows).
   - No Windows, se aparecer "O Windows protegeu o computador", clique em *Mais informações* e depois em *Executar assim mesmo*. O programa não é assinado digitalmente.
4. Em **Pasta do jogo**, escolha a pasta que tem o `eboot.bin`.
5. Escolha o idioma do jogo (inglês, português, espanhol ou francês) e clique em **Jogar**. A primeira partida demora um pouco mais.

No Linux, `./install_desktop.sh` adiciona o jogo ao menu de aplicativos.

### Durante o jogo

- **F10**: liga e desliga o contador de FPS
- **Insert** (ou R3 + L2 no controle): abre o menu do port (imagem, desempenho, overlay)
- Controles de PS4/PS5, Xbox e 8BitDo funcionam via SDL3, por USB ou Bluetooth.

### Teclado e mouse

Com a janela do jogo em foco, o mouse fica preso e gira a câmera. **Esc** solta o mouse; um clique na janela prende de novo. Abrir o menu do port (Insert) também solta o mouse.

| Ação no jogo | Botão do PS4 | Teclado e mouse |
|---|---|---|
| Andar | Analógico esquerdo | W A S D |
| Câmera | Analógico direito | Mouse (ou as setas) |
| Pular | X | Espaço |
| Agarrar, segurar | Triângulo | Clique esquerdo ou Q |
| Chamar o Trico | R1 | Clique direito ou 3 |
| | Quadrado | E ou clique do meio |
| | Círculo | Shift esquerdo |
| | L1 / L2 / R2 | 1 / R / F |
| | L3 / R3 | Z / C |
| | Direcional | I J K L |
| Menu | Options | Enter |
| Modo foto / pausa | Touchpad (esquerda / direita) | Tab / Backspace |

- No launcher, a caixa **Controles** liga o mouse, muda a sensibilidade e inverte o eixo Y. **Teclas e botões do mouse…** remapeia cada botão: clique em *Definir* e aperte a tecla ou o botão do mouse (os botões laterais e a roda também servem). Vale na próxima vez que o jogo abrir.
- No jogo, a aba **Controles** do menu do port (Insert) ajusta sensibilidade, eixo Y, suavização, aceleração e anti-zona morta na hora.

### Onde ficam as coisas

- Saves: `user/savedata/`, ao lado do executável (guarde essa pasta ao atualizar)
- Logs: `out/logs/` (`out/last_run.log` é o da última sessão; mande ele junto se reportar um problema)
- Configurações do launcher: `~/.config/tlg-launcher/` (Linux) ou `%APPDATA%\tlg-launcher` (Windows)

### Problemas

- **Jogo mudo**: falta o `libSceNgs2.sprx` em `system_lib/`.
- **Não abre ou fecha sozinho**: veja a caixa de log no launcher e mande o `out/last_run.log` no [Discord](https://discord.gg/UMkdMYZh9g) ou numa [issue](https://github.com/HayatoG/tlg_pc/issues).
- **NVIDIA**: use um driver recente.

---

## English

### What you need

| Item | Where to get it | Required |
|---|---|---|
| Game folder **CUSA03627 with update 01.03** (US): `eboot.bin`, `sce_module/` (`libc.prx`, `libSceFios2.prx`), `sce_sys/` and `trico_boot.psarc`, `trico_001.psarc`, `trico_002.psarc`, `trico_003.psarc` | A dump from your own jailbroken PS4: the base game merged with patch 1.03 (`eboot.bin` must be the 1.03 one) | Yes |
| `libSceNgs2.sprx` | Your PS4 firmware, in `/system/common/lib/` (via GoldHEN FTP, for example) | For audio only |
| PC | 64-bit Windows 10 (1903+) / 11, or x86-64 Linux (glibc 2.39+: Ubuntu 24.04, Fedora 40, SteamOS 3.6 or newer) | Yes |
| Graphics card | Vulkan 1.3 with an up-to-date driver; 6 GB of VRAM recommended | Yes |
| Disk space | ~25 GB for the game files | Yes |

`.psarc` files larger than 4 GiB arrive truncated over GoldHEN 2.2's FTP. Copy them over USB (Itemzflow, for example) and check the sizes.

### How to play

1. Extract the package anywhere (on Windows, outside the .zip).
2. Put `libSceNgs2.sprx` in the `system_lib/` folder next to the executable (optional, for audio).
3. Open **The Last Guardian** (`The Last Guardian.exe` on Windows).
   - On Windows, if "Windows protected your PC" appears, click *More info*, then *Run anyway*. The program is not digitally signed.
4. Under **Game folder**, choose the folder that has `eboot.bin`.
5. Pick the game language (English, Portuguese, Spanish or French) and click **Play**. The first start takes a little longer.

On Linux, `./install_desktop.sh` adds the game to the applications menu.

### While playing

- **F10**: toggles the FPS counter
- **Insert** (or R3 + L2 on a controller): opens the port's menu (image, performance, overlay)
- PS4/PS5, Xbox and 8BitDo controllers work through SDL3, over USB or Bluetooth.

### Keyboard and mouse

While the game window has focus, it takes the mouse and the mouse turns the camera. **Esc** releases the mouse; a click in the window takes it back. Opening the port's menu (Insert) also releases it.

| In game | PS4 button | Keyboard and mouse |
|---|---|---|
| Move | Left stick | W A S D |
| Camera | Right stick | Mouse (or the arrow keys) |
| Jump | Cross | Space |
| Grab, hold on | Triangle | Left click or Q |
| Call Trico | R1 | Right click or 3 |
| | Square | E or middle click |
| | Circle | Left Shift |
| | L1 / L2 / R2 | 1 / R / F |
| | L3 / R3 | Z / C |
| | D-pad | I J K L |
| Menu | Options | Enter |
| Photo mode / pause | Touchpad (left / right) | Tab / Backspace |

- In the launcher, the **Controls** box turns the mouse on or off, sets its sensitivity and inverts the Y axis. **Keyboard and mouse buttons…** remaps each button: click *Set* and press the key or mouse button (the side buttons and the wheel work too). It applies at the next start.
- In game, the **Controls** tab of the port's menu (Insert) changes sensitivity, Y axis, smoothing, acceleration and anti-dead zone at once.

### Where things are

- Saves: `user/savedata/` next to the executable (keep this folder when updating)
- Logs: `out/logs/` (`out/last_run.log` is the latest session; attach it to bug reports)
- Launcher settings: `~/.config/tlg-launcher/` (Linux) or `%APPDATA%\tlg-launcher` (Windows)

### Problems

- **No sound**: `libSceNgs2.sprx` is missing from `system_lib/`.
- **Does not start or closes by itself**: check the log box in the launcher and send `out/last_run.log` on [Discord](https://discord.gg/UMkdMYZh9g) or in an [issue](https://github.com/HayatoG/tlg_pc/issues).
- **NVIDIA**: use a recent driver.

---

This project is not affiliated with Sony Interactive Entertainment, SIE Japan Studio or genDESIGN. The Last Guardian is a trademark of Sony Interactive Entertainment. / Este projeto não tem vínculo com a Sony Interactive Entertainment, SIE Japan Studio ou genDESIGN.
