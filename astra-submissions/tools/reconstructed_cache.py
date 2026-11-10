"""64-byte privileged training records, with a restricted actor projection.

Reuses011's nibble codec. This is not a raw replay format: clocks and recorded
results are absent. Only actor_context/actor_view expose permitted inputs;
full state, action flags, selection flags and world metadata are privileged.
"""
import hashlib
import json
import mmap
from pathlib import Path
import struct

from experience_index import pack_view,unpack_view,pack_move

ROW=struct.Struct('<32sQQQbHBHBB')
assert ROW.size==64
NO_ACTION=65535
CAPTURE,EN_PASSANT,CASTLE,PROMOTION,FATAL=1,2,4,8,16
SELECTED,REFERENCE,AFTER_EIGHT=1,2,4
SCHEMA='astra-reconstructed-training64-v1'


def decode_move(value):
    if not 0<=value<=NO_ACTION:raise ValueError('packed action range')
    if value==NO_ACTION:return None
    promo=value>>12
    if promo>4:raise ValueError('invalid packed promotion')
    sq=lambda n:chr(97+n%8)+str(1+n//8)
    return sq(value&63)+sq((value>>6)&63)+('qrbn'[promo-1] if promo else '')


def mask(view):
    if len(view)!=64:raise ValueError('observation length')
    return sum(1<<i for i,c in enumerate(view) if c!='?')


def encode(full,white,black,castle,ep,halfmove,side,move,selection,flags):
    if '?' in full:raise ValueError('full board cannot contain hidden cells')
    if side not in (0,1) or not -1<=ep<64 or not 0<=halfmove<=65535:
        raise ValueError('invalid world metadata')
    if not 0<=selection<8 or not 0<=flags<32:raise ValueError('invalid flags')
    for view in (white,black):
        if len(view)!=64 or any(c!='?' and c!=full[i] for i,c in enumerate(view)):
            raise ValueError('visible cells disagree with full board')
    value=NO_ACTION if move is None else struct.unpack('<H',pack_move(move))[0]
    return ROW.pack(pack_view(full),mask(white),mask(black),castle,ep,halfmove,side,value,selection,flags)


def fields(raw):
    if len(raw)!=ROW.size:raise ValueError('record size')
    return ROW.unpack(raw)


def actor_view(raw,side):
    if side not in (0,1):raise ValueError('actor side')
    row=fields(raw);full=unpack_view(row[0]);visible=row[1+side]
    return ''.join(c if visible>>i&1 else '?' for i,c in enumerate(full))


def actor_events(records,side):
    """One linear pass for causal recurrent batches; no prefix rescanning."""
    if side not in (0,1):raise ValueError('actor side')
    previous=None
    for ply,raw in enumerate(records):
        known=None
        if previous is not None and previous[6]==side:known=decode_move(previous[7])
        yield dict(ply=ply,observation=actor_view(raw,side),known_own_action=known,clocks=None)
        previous=fields(raw)


def actor_context(records,side,target):
    """No opponent moves, target action, truth flags, names or world metadata."""
    if side not in (0,1) or target<0 or target>=len(records):raise ValueError('actor context range')
    import itertools
    events=list(itertools.islice(actor_events(records,side),target+1))
    own=[(e['ply']-1,e['known_own_action']) for e in events if e['known_own_action'] is not None]
    return dict(side=side,ply=target,observations=[e['observation'] for e in events],own_actions=own,clocks=None)


class Cache:
    def __init__(self,folder):
        self.folder=Path(folder)
        self.manifest=json.loads((self.folder/'manifest.json').read_text())
        if self.manifest['schema']!=SCHEMA:raise ValueError('cache schema')
        if self.manifest['record_size']!=ROW.size:raise ValueError('cache record size')
        self.games=json.loads((self.folder/'games.json').read_text())
        for name in ('records.bin','games.json'):
            with (self.folder/name).open('rb') as handle:
                digest=hashlib.file_digest(handle,'sha256').hexdigest()
            if digest!=self.manifest['sha256'][name]:raise ValueError('cache checksum: '+name)
        self.handle=(self.folder/'records.bin').open('rb')
        self.data=mmap.mmap(self.handle.fileno(),0,access=mmap.ACCESS_READ)
        if len(self.data)!=ROW.size*self.manifest['records']:self.close();raise ValueError('cache row count')

    def record(self,number):
        if not 0<=number<self.manifest['records']:raise IndexError(number)
        return self.data[number*ROW.size:(number+1)*ROW.size]

    def close(self):
        self.data.close();self.handle.close()
