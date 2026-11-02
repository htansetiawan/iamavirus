import json
import numpy as np
from extract_augmented import canonical_parents


def main():
    dtype=np.dtype({'names':['a','b'],'formats':['u1','<u8'],'offsets':[0,8],'itemsize':24})
    rows=np.zeros(3,dtype=dtype);rows['a']=[1,2,3];rows['b']=[11,12,13]
    raw=rows.view(np.uint8).reshape(3,24);raw[:,1:8]=113;raw[:,16:]=99
    result=canonical_parents(list(rows));canonical=result.view(np.uint8).reshape(3,24)
    assert np.array_equal(result['a'],rows['a']) and np.array_equal(result['b'],rows['b'])
    assert not canonical[:,1:8].any() and not canonical[:,16:].any()
    assert result.tobytes()==canonical_parents(list(rows)).tobytes()
    print(json.dumps(dict(fields_preserved=True,padding_zero=True,reproducible=True)))


if __name__=='__main__':main()
