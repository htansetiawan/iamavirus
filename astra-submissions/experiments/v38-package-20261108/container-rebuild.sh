#!/bin/sh
set -eu
# Repair the packaging-only failure; all source and experiment bytes stay pinned.
export DEBIAN_FRONTEND=noninteractive
apt-get install -y --no-install-recommends bsdextrautils
command -v hexdump
dpkg-query -W gcc-12 g++-12 libc6 libstdc++6 make binutils gawk python3 bsdextrautils
runuser -u builder -- sh -eu -c '
    cd /work/stockfish/src
    rm -f temp_builds/.net-done temp_builds/nnue_embed.o
    make -j2 build ARCH=x86-64-universal COMP=gcc CXX=g++-12
    strip stockfish
    test "$(wc -c < universal/network_dump.inc)" -gt 98000000
    test "$(wc -c < stockfish)" -gt 98000000
    sha256sum stockfish
'
