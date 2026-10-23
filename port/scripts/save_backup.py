#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Backups of the game's saves: <user>/savedata copied to <user>/savedata_backups/<time>.

run.py makes one before every start; the launcher lists them and restores one. A restore
first backs up the current saves, so it can always be undone.

pin() marks a backup the rotation keeps for good, recording why: the pins file sits next to
the backup folders, so list_backups() never returns it.
"""
import datetime
from pathlib import Path
import os
import shutil

KEEP = 10
STAMP = '%Y%m%d-%H%M%S'
PINS = 'pins'


def backups_dir(user_dir):
    return Path(user_dir) / 'savedata_backups'


def list_backups(user_dir):
    """Backup names, newest first."""
    root = backups_dir(user_dir)
    return sorted((p.name for p in root.iterdir() if p.is_dir()), reverse=True) if root.is_dir() else []


def _has_saves(savedata):
    return savedata.is_dir() and any(p.is_file() for p in savedata.rglob('*'))


def pins_path(user_dir):
    return backups_dir(user_dir) / PINS


def pinned(user_dir):
    """Pinned backup names mapped to the reason they were pinned."""
    path = pins_path(user_dir)
    if not path.is_file():
        return {}
    pins = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        name, _, reason = line.partition('\t')
        if name:
            pins[name] = reason.strip()
    return pins


def is_pinned(user_dir, name):
    return name in pinned(user_dir)


def pin(user_dir, name, reason=''):
    """Marks a backup the rotation keeps for good; raises ValueError for an unknown name or a
    reason containing a tab or newline (the pins file is line- and tab-separated)."""
    if name not in list_backups(user_dir):
        raise ValueError(f'No save backup named {name!r}')
    reason = reason.strip()
    if any(char in reason for char in '\t\n'):
        raise ValueError('A pin reason cannot contain a tab or newline')
    pins = pinned(user_dir)
    pins[name] = reason
    _write_pins(user_dir, pins)


def unpin(user_dir, name):
    """Forgets the pin; the backup rotates out with the rest."""
    pins = pinned(user_dir)
    if pins.pop(name, None) is not None:
        _write_pins(user_dir, pins)


def _write_pins(user_dir, pins):
    path = pins_path(user_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')          # a crash mid-write must not lose the pins
    tmp.write_text(''.join(f'{name}\t{reason}\n' for name, reason in sorted(pins.items())),
                   encoding='utf-8')
    os.replace(tmp, path)


def _prune(user_dir, keep=KEEP):
    keepers = set(pinned(user_dir))
    for name in list_backups(user_dir)[keep:]:
        if name not in keepers:
            shutil.rmtree(backups_dir(user_dir) / name, ignore_errors=True)


def _copy(user_dir, now):
    savedata = Path(user_dir) / 'savedata'
    if not _has_saves(savedata):
        return None
    root = backups_dir(user_dir)
    root.mkdir(parents=True, exist_ok=True)
    base = (now or datetime.datetime.now()).strftime(STAMP)
    target, n = root / base, 2
    while target.exists():
        target, n = root / f'{base}-{n}', n + 1
    shutil.copytree(savedata, target)
    return target


def backup(user_dir, now=None, keep=KEEP):
    """Copies savedata; returns the new folder, or None when there is nothing to save."""
    made = _copy(user_dir, now)
    if made:
        _prune(user_dir, keep)
    return made


def restore(user_dir, name, now=None, keep=KEEP):
    """Replaces savedata with backup `name`; returns the backup of the saves it replaced."""
    if not name or name not in list_backups(user_dir):
        raise ValueError(f'No save backup named {name!r}')
    source = backups_dir(user_dir) / name
    savedata = Path(user_dir) / 'savedata'
    # Pruning waits until the copy is done: the restored backup may be the oldest one.
    safety = _copy(user_dir, now)
    staging = Path(user_dir) / 'savedata.restoring'
    shutil.rmtree(staging, ignore_errors=True)
    shutil.copytree(source, staging)
    # Swap by renames: the current saves stay on disk (as `savedata.replaced`) until the restored
    # ones are in place, so a failure never leaves the folder without saves.
    aside = Path(user_dir) / 'savedata.replaced'
    shutil.rmtree(aside, ignore_errors=True)
    if savedata.exists():
        savedata.rename(aside)
    try:
        staging.rename(savedata)
    except OSError:
        if aside.exists():
            aside.rename(savedata)
        raise
    shutil.rmtree(aside, ignore_errors=True)
    _prune(user_dir, keep)
    return safety

