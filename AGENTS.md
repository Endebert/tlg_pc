# Repository Guidelines

## Project overview

Port of The Last Guardian (CUSA03627 / CUSA03745) from PS4 to PC. The eboot is neither interpreted
nor recompiled: it runs as host x86-64 code, with PS4 syscalls and libraries supplied by
`port/src/runtime_*.c` and the graphics API HLE'd inside `port/gpu`. A Python launcher prepares the
image, a Python patcher emits byte-level patches, and a C loader applies them and enters the game.

## Architecture and data flow

Two halves in one process, joined by a C ABI.

`port/src` is the loader and runtime. `probe.c` owns `main()` at line 827: parse `boot.bin`, map
and relocate the image, bind imports, install signal handlers, apply patches, then enter the game
on a fresh stack. `runtime.c` holds `runtime_resolve()` at line 193, the central NID dispatch that
every unresolved-import trap stub lands in; an import that resolves nowhere prints `STOP:` plus
`runtime_report()` and exits 20. `runtime_memory.c` is guest virtual memory, `runtime_thread.c` is
guest threads and FreeBSD-variant-II TLS, `runtime_ngs2.c` is a from-scratch software audio mixer,
`isa_rewrite.c`/`isa_emulate.c` patch and emulate instructions the host CPU lacks.

`port/gpu` is `libtlggpu.so`, a C++23 library wrapping a vendored shadPS4 video core behind the C
API in `tlggpu.h`. The path is guest `sceGnmSubmit` → `gnmdriver.cpp` → `Liverpool` PM4 command
processor → `Vulkan::Rasterizer` → VideoOut flip → present thread → SDL window.

The halves are not independent. `libtlggpu.so` links with `-Wl,--allow-shlib-undefined`
(`port/gpu/CMakeLists.txt:215`) because its `runtime_memory_*` and `runtime_process_*` references
resolve against the `tlg-probe` executable at load time, and `build.sh:98` gives the probe
`-rdynamic` so those symbols are exported. The library cannot run standalone and load order
matters; on Windows it is static for exactly this reason.

Guest memory is identity-mapped, guest VA equal to host VA, so a guest NULL dereference faults the
host at address 0. The user region is `USER_MIN 0x1000000000` to `USER_MAX 0xfc00000000`
(`runtime_memory.c:41`), in 16 KiB pages over one sparse memfd.

## Key directories

| path | purpose |
| --- | --- |
| `port/src/` | loader, runtime, signal handling, ISA rewrite |
| `port/gpu/` | GPU library: `shim/` C API glue, `shadps4/` vendored video core, `CMakeLists.txt` |
| `port/scripts/` | Python run as subprocesses: `prepare.py`, `link_modules.py`, `tlg_patches.py`, `isa_rewrite.py` |
| `port/launcher/` | `tlg_run.py` run core, `tlg_launcher.py` Tk GUI, `shader_cache.py` |
| `port/tests/` | Python tests plus `paths.py`, which puts `port/scripts` on `sys.path` |
| `port/tools/` | dev-loop helpers: `restart.sh`, `soak.sh`, `ab.sh`, FSR4 toolchain |
| `port/packaging/` | Linux and Windows dist scripts |
| `scripts/` | machine-specific session, dump and chart tooling |
| `docs/` | `TECNICO.md`, `PROGRESSO.md`, research notes; root `README.md` mirrors pt_BR and en_US |

## Development commands

Build. Vulkan headers live in `~/.local`, not `/usr`, and the probe compiles with
`-Wall -Wextra -Werror`, so a warning is a build failure:

    cd port && CPATH=/home/ren/.local/include CMAKE_PREFIX_PATH=/home/ren/.local TLG_LTO=OFF bash build.sh

`TLG_LTO` defaults to ON; CI and the command above turn it off for build speed. `TLG_PGO` is
`off`, `generate` or `use`, and `build.sh` picks `use` when `port/pgo/*.gcda` exists. `port/shell.nix`
is a NixOS fallback whose header still names the old `native_probe/` path.

Run the game. Every unattended run MUST set `TLG_OFFSCREEN=1`: it forces the hidden X11/XWayland
window so nothing appears on the desktop and focus is never stolen from the player's session. It
is ignored with a warning when `DISPLAY` is unset. Omitting it puts a window on screen.

    TLG_OFFSCREEN=1 ./run_tlg.sh <seconds>

`TLG_FRAME_LOG=<path>` writes a per-frame CSV of `time_ms,frame_ms,draws`. `TLG_SKIP_INTRO=0`
disables the boot-logo skip, which is on by default; an empty value counts as unset. Logs land in
`port/out/logs/run-<timestamp>.log`, with `port/out/last_run.log` pointing at the newest.

## Testing and QA

Three independent tiers, with no ctest and no aggregate target.

1. Python: `cd port && python3 -m unittest discover -s tests`. The working directory must be
   `port/`. Baseline is 184 tests, 7 errors, 59 skips.
2. C: `bash build.sh --test` compiles and immediately runs 18 binaries into `port/out/`.
3. C++: `ninja -C out/gpu <name>-test && out/gpu/<name>-test`. Targets are `EXCLUDE_FROM_ALL` in
   `port/gpu/CMakeLists.txt`; `cheat-hook-test` is the only one that is not.

C and C++ have no framework: `int main()` plus `assert()`, exit 0. Because the build type is
RelWithDebInfo they pass `-UNDEBUG`, without which every assert would compile away.

The 7 Python errors are pre-existing and unrelated to any change. Two are module-level import
failures: `test_launcher_stream_memory` imports `tlg_launcher_win` and `test_upscaler_assets`
imports `tlg_assets`, neither of which exists. Five are `FileNotFoundError` from
`test_patches.py`, whose `TLG` is `port/patches/God_of_War_III_Remastered.xml`, a file that is not
in the repository. Compare against this baseline instead of chasing them.

Of the 59 skips, 14 are `test_content`, `test_runtime` and `test_sema` waiting on
`out/{content,runtime,sema}-test`, which only `build.sh --test` produces — run that first to
exercise them. Others gate on `iced-x86` being installed or on `TLG_GAME` pointing at a real eboot.

Conventions for a new test: `port/tests/test_*.py`, a `unittest.TestCase` named `*Tests`, methods
named `test_*`, starting with `from paths import ROOT`. Never depend on real game files — synthesize
ELF, SELF and boot images with `struct.pack`, use `tempfile.TemporaryDirectory`, and mock the
environment with `unittest.mock.patch.dict`. Gate anything environment-dependent behind
`skipUnless`. For C, add a compile-and-run pair to `build.sh --test`; for C++, add an
`EXCLUDE_FROM_ALL` target with `-UNDEBUG -Wall -Wextra -Werror` and link
`test_gpu_runtime_stubs.cpp` when renderer runtime symbols are needed.

## Code conventions and patterns

C is C11 with `-Wall -Wextra -Werror`; C++ is C++23 with `-fno-omit-frame-pointer`. Errors are
reported by returning a status and printing through the runtime's own reporting path rather than
by aborting, and the fatal signal handler deliberately uses `snprintf`, `dladdr` and
`process_vm_readv` because the process is already terminating. Guest-facing reads always go
through `process_vm_readv` with an explicit length check so a bad address cannot fault the handler.

Python is stdlib only, run as subprocesses with `cwd` set to `port/scripts`, each file a CLI with
`argparse` and a `main()`. Environment variables are read with `os.environ.get(key, default)`, and
an empty value is treated as unset so a stray variable cannot silently override a setting.

The patcher never writes game files. `tlg_patches.py` emits a `G3PATCH2` blob that the loader
applies after relocation, and every write is gated by expected-byte, sha256 and segment checks
with a silent fallback to unpatched behaviour. It can only replace bytes in place: it cannot insert
instructions or branches, so a fix needing new control flow does not belong there.

## Runtime and tooling preferences

Python 3 with no third-party packages required for the build; `iced-x86` is optional and gates the
ISA-rewrite and red-zone tests. The build needs `gcc`, `cmake`, `ninja`, SDL3, Vulkan headers and
loader, Zydis, fmt and FFmpeg; `port/packaging/linux/build_deps.sh` builds the non-system ones into
`/opt/tlgdeps` in CI. CI (`.github/workflows/build.yml`) builds and packages for Linux and Windows
but runs no tests.

Two launch pipelines exist and are not interchangeable: the TLG player path
(`tlg_launcher.sh` / `run_tlg.sh` → `tlg_run.py` → `tlg_patches.py`) and a gow3_pc-inherited
generic path (`port/run.sh` / `port/run.py` → `patches.py`, `mods.py`). `patches.py` only knows
God of War III, so for this game it writes an empty patch file.

## Important files

`port/src/probe.c` is the entry point and owns the signal handlers. `port/src/runtime.h` is the
contract every `runtime_*.c` module implements. `port/gpu/tlggpu.h` is the public GPU API.
`port/scripts/tlg_patches.py` is this game's patcher; `port/scripts/prepare.py` parses the SELF and
exposes `parse_self`. `port/launcher/tlg_run.py` is the run core shared by the CLI and the GUI.
`port/user/tlg.ini` holds the in-game settings.

## Crash triage

Exit 139 is SIGSEGV. `fault()` in `port/src/probe.c` (line 312) classifies it: `Guest fault` means
the faulting RIP is inside the eboot image, `Host fault` means it is in a host library. It prints
the registers, the 16 bytes at the faulting RIP, up to 12 qwords at every readable register, the
guest frame-pointer chain and the host backtrace, then exits `128 + signal`.

The eboot is a SELF dump, sha256 `b7f61057…`, at
`/home/ren/Downloads/_PS4ROMS/_backup/CUSA03745-patch/eboot.bin`, reached by symlink from
`CUSA03745-1.03-merged/`. `EBOOT_103_SHA256` in the patcher is the hash of the plain dump, not of
this file. Extract the ELF with `prepare.parse_self`; the text segment maps file offset `0x4000` to
vaddr `0`, so guest offsets are vaddrs. The eboot is stripped, so disassemble with `llvm-objdump -d`
and expect no symbols.

Open: a guest NULL dereference at `0x28c193` (`movq (%rcx,%rax,8),%rax`, with the object's `+0x28`
table null) closes the game after roughly four minutes of play. It is pre-existing — upstream
issue #60 carries the identical fault from 2026-10-16, before `skip_intro` existed. Root cause not
yet found.

## Remotes and commits

`mine` is `github.com/Endebert/tlg_pc`, the fork that `main` tracks and the push target. `origin` is
`github.com/HayatoG/tlg_pc`, upstream; never push there. Commit with a subject line plus a body
explaining the mechanism and the evidence, matching the style of the existing history.
