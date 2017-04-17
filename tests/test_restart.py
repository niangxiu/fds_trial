import os
import sys
import shutil
import tempfile
from subprocess import *

from numpy import *

my_path = os.path.dirname(os.path.abspath(__file__))
#sys.path.append(os.path.join(my_path, '..'))

from fds import *

solver_path = os.path.join(my_path, 'solvers', 'circular')
solver = os.path.join(solver_path, 'solver')
u0 = loadtxt(os.path.join(solver_path, 'u0'))

BASE_PATH = os.path.join(my_path, 'checkpoint_test')
if os.path.exists(BASE_PATH):
    shutil.rmtree(BASE_PATH)
os.mkdir(BASE_PATH)

def solve(u, s, nsteps):
    tmp_path = tempfile.mkdtemp()
    with open(os.path.join(tmp_path, 'input.bin'), 'wb') as f:
        f.write(asarray(u, dtype='>d').tobytes())
    with open(os.path.join(tmp_path, 'param.bin'), 'wb') as f:
        f.write(asarray(s, dtype='>d').tobytes())
    call([solver, str(int(nsteps))], cwd=tmp_path)
    with open(os.path.join(tmp_path, 'output.bin'), 'rb') as f:
        out = frombuffer(f.read(), dtype='>d')
    with open(os.path.join(tmp_path, 'objective.bin'), 'rb') as f:
        J = frombuffer(f.read(), dtype='>d')
    shutil.rmtree(tmp_path)
    return out, J[:,newaxis]

def put_garbage_files_in(path, m_modes):
    files = 'jf234fsd_segment', 'm{0}_segment_dsgh324fs'.format(m_modes)
    for f in files:
        open(os.path.join(path, f), 'w').close()

def test_checkpoint():
#if __name__ == '__main__':
    s = 1
    m_modes = 2
    segments0, segments1 = 10, 20

    put_garbage_files_in(BASE_PATH, m_modes)

    random.seed(0)
    shadowing(solve, u0, s, m_modes, segments0, 100, 0,
              checkpoint_path=BASE_PATH, checkpoint_interval=5)
    cp = checkpoint.load_last_checkpoint(BASE_PATH, m_modes)
    assert cp.lss.K_segments() == segments0
    assert cp.lss.m_modes() == m_modes
    J2, G2 = continue_shadowing(solve, s, cp, segments1, 100,
                                checkpoint_path=BASE_PATH,
                                checkpoint_interval=5)

    random.seed(0)
    J1, G1 = shadowing(solve, u0, s, m_modes, segments1, 100, 0,
                       checkpoint_path=BASE_PATH, checkpoint_interval=5)
    assert J1 == J2
    assert allclose(G1,G2)
