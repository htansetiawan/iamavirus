"""Binary round trips and actor privacy boundaries, not a model test."""
import struct
import pytest
import reconstructed_cache as cache


def record(move='e2e4',side=0,flags=0):
    full='RNBQKBNRPPPPPPPP--------------------------------pppppppprnbqkbnr'
    white=full[:32]+'?'*32;black='?'*32+full[32:]
    return cache.encode(full,white,black,0x8100000000000081,-1,37,side,move,7,flags)


@pytest.mark.parametrize('move',['e2e4','a7a8q','a7a8r','a7b8b','h2h1n',None])
def test_record_round_trip_and_both_views(move):
    raw=record(move);assert len(raw)==64
    r=cache.fields(raw)
    assert r[3:7]==(0x8100000000000081,-1,37,0)
    assert cache.decode_move(r[7])==move and r[8:]==(7,0)
    assert cache.actor_view(raw,0)=='RNBQKBNRPPPPPPPP----------------'+'?'*32
    assert cache.actor_view(raw,1)=='?'*32+'----------------pppppppprnbqkbnr'


def test_hidden_truth_and_privileged_flags_do_not_change_actor_view():
    raw=record();values=list(cache.fields(raw))
    board=bytearray(values[0]);board[31]^=0x11;values[0]=bytes(board)
    values[3]=0;values[4]=27;values[5]=99;values[7]=0;values[8]=0;values[9]=31
    changed=cache.ROW.pack(*values)
    assert cache.actor_view(raw,0)==cache.actor_view(changed,0)
    assert cache.actor_view(raw,1)!=cache.actor_view(changed,1)


def test_actor_history_excludes_opponent_and_current_actions():
    rows=[record('e2e4',0),record('e7e5',1),record('g1f3',0)]
    changed=[rows[0],record('a7a6',1,flags=31),record('d2d4',0,flags=31)]
    assert cache.actor_context(rows,0,2)==cache.actor_context(changed,0,2)
    assert cache.actor_context(rows,0,2)['own_actions']==[(0,'e2e4')]
    changed[0]=record('d2d4',0)
    assert cache.actor_context(rows,0,2)!=cache.actor_context(changed,0,2)


def test_hidden_and_visible_empty_remain_distinct():
    raw=record();visible=cache.actor_view(raw,0)
    assert visible[24]=='-' and visible[40]=='?'
    with pytest.raises(ValueError):cache.actor_view(raw,2)
    with pytest.raises(ValueError):cache.fields(raw[:-1])
    with pytest.raises(ValueError):cache.decode_move(5<<12)


def test_streaming_events_reveal_only_previous_own_action():
    rows=[record('e2e4',0),record('e7e5',1),record('g1f3',0)]
    white=list(cache.actor_events(rows,0));black=list(cache.actor_events(rows,1))
    assert [e['known_own_action'] for e in white]==[None,'e2e4',None]
    assert [e['known_own_action'] for e in black]==[None,None,'e7e5']
    assert all(e['clocks'] is None for e in white+black)
    with pytest.raises(ValueError):cache.decode_move(-1)
