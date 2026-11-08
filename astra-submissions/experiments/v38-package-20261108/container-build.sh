#!/bin/sh
set -eu
# Dedicated, CPU-limited Ubuntu 22.04 container; no GPU and no repository/token mount.
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends g++-12 make binutils gawk python3 ca-certificates bsdextrautils
useradd --uid "$BUILD_UID" --user-group --create-home builder
dpkg-query -W gcc-12 g++-12 libc6 libstdc++6 make binutils gawk python3
runuser -u builder -- sh -eu -c '
    cd /work/stockfish/src
    command -v hexdump
    g++-12 --version
    make -j2 build ARCH=x86-64-universal COMP=gcc CXX=g++-12
    strip stockfish
    test "$(wc -c < universal/network_dump.inc)" -gt 98000000
    test "$(wc -c < stockfish)" -gt 98000000
    sha256sum stockfish
    objdump -T stockfish | sed -n "/GLIBC/p"
'
