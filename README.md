# NIUDU

Prototypes of several GUI utilities for observing and controlling GNU/Linux internals which miss on Linux desktop. Written in Python3 with Qt (via PySide6 bindings). Project currently includes:

- niudu-devices, which visualises device hierarchy (as provided by kernel via /sys/devices) and device properties
- niudu-nix, which visualises Nix store and scope

## Building and installing

[![built with nix](https://builtwithnix.org/badge.svg)](https://builtwithnix.org)

Unlike most software around, this project doesn't use autotools/Python setuptools/whatever as a (meta)build system. It uses Nix instead. Nix is package manager which is core of NixOS GNU/Linux distro but can be side-installed on (almost) any other distro, together with nixpkgs packages collection. For most software nixpkgs relies on build systems used by upstream projects, but Nix can be used as a self-sufficient build system, provided that dependencies all the way down to libc are handled by it. If you have it installed, you can:

- build NIUDU, via `nix-build`, which will produce "result" symlink pointing to build directory in Nix store, so that applications can be launched from "result/bin/"
- install it into user profile, via `nix-env -i -f default.nix`
- run it from project directory from shell, which can be entered via `nix-shell`; buildPhase has to be run manually via `eval "${buildPhase:-buildPhase}"` to produce missing files and symlinks in-place

Actual expression is "derivation.nix" which is, like most nixpkgs expressions, intended to be used via callPackage. "default.nix" is wrapper which allows it to be used out-of-tree. Note that unlike nixpkgs expressions which are guaranteed to produce working builds, out-of-tree expression can fail depending on which nixpkgs it's evaluated against, e. g. this expression produced non-working build against nixpkgs revision which had PySide<5.14 and Python3 aliased to Python3.7

You may notice that the project uses an unorthodox layout for files which get into the produced build, virtually being a simplified FHS layout of the build. This simplifies buildPhase and allows installPhase to be as simple as a single cp command.


## Project name

NIUDU is for "Non Idiot User's Desktop Utilities" (referring to well-known L. Torvalds citate). It also sounds Chinese and coincidentally means "calf" in Mandarin (牛犊, Gnu calf probably).
