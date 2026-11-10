#!/usr/bin/python3
"""Owned mock UCI child for transport contracts; never a chess opponent."""
import os
import sys
import time

mode = os.environ['FAKE_UCI_MODE']
for line in sys.stdin:
    if line.strip() == 'uci':
        if mode == 'uci-eof':
            sys.exit(3)
        if mode == 'uci-stall':
            time.sleep(30)
        if mode == 'delayed':
            time.sleep(.075)
        print('id name owned-mock', flush=True)
        print('uciok', flush=True)
    elif line.strip() == 'isready':
        if mode == 'ready-eof':
            sys.exit(4)
        if mode == 'ready-stall':
            time.sleep(30)
        if mode == 'delayed':
            time.sleep(.075)
        print('readyok', flush=True)
    elif line.strip() == 'quit':
        break
