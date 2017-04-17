from __future__ import division
import os
import sys
import shutil
import subprocess

import numpy as np

my_path = os.path.dirname(os.path.abspath(__file__))
#sys.path.append(os.path.join(my_path, '..', '..'))


def test_linalg():
    for mod in list(sys.modules.keys()):
        if mod.startswith('pascal_lite'):
            del sys.modules[mod]
    import pascal_lite as pascal
    subspace_dimension = 4
    V = pascal.symbolic_array(subspace_dimension)
    v = pascal.symbolic_array()

    v1 = pascal.dot(V, v)
    assert not v1.is_distributed
    v2 = pascal.outer(v1, v)
    assert v2.is_distributed
    v3 = pascal.qr_transpose(V)[0]
    assert v3.is_distributed

    g = pascal.ComputationalGraph([v1.value, v2.value, v3.value])
    n = 16

    A = np.random.rand(subspace_dimension, n)
    b = np.random.rand(n)

    def actual_inputs(x):
        if x is V.value:
            return A
        elif x is v.value:
            return b

    o1, o2, o3 = g(actual_inputs)
    assert np.allclose(o1, np.dot(A, b))
    assert np.allclose(o2, np.outer(np.dot(A, b), b))
    assert np.allclose(o3, np.linalg.qr(A.T)[0].T)

def test_plinalg():
    #np.random.seed(10)
    V = np.random.rand(4, 100)
    V_path = os.path.join(my_path,'plinalg_A.txt')
    np.savetxt(V_path, V)
    v = np.random.rand(100)
    v_path = os.path.join(my_path, 'plinalg_b.txt')
    np.savetxt(v_path, v)

    Q, R = np.linalg.qr(V.T)
    S = np.diag(np.sign(np.diag(R)))
    R = np.dot(S,R)
    Q = np.dot(Q,S)
    Q = Q.T
    plinalg_file = os.path.join(my_path, 'test_plinalg.py')
    
    returncode = subprocess.call(['mpirun', '-np', '4', sys.executable, plinalg_file, V_path, v_path])
    assert returncode == 0


    pdot = np.loadtxt(os.path.join(my_path, 'plinalg_dot.txt'))
    assert np.allclose(pdot, np.dot(V, v))

    pQ = np.loadtxt(os.path.join(my_path, 'plinalg_Q.txt')).T
    pR = np.loadtxt(os.path.join(my_path, 'plinalg_R.txt'))
    #print(np.abs(R-pR)).max()
    #print(np.abs(Q-pQ)).max()
    assert np.allclose(R, pR, rtol=1e-4, atol=1e-6)
    assert np.allclose(Q, pQ, rtol=1e-4, atol=1e-6)

if __name__ == '__main__':
    test_linalg()
    test_plinalg()
