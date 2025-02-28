from vdw.wrapper import wrapper

from pyscf import gto, scf, mcscf, lib
from pyscf.lib import logger
import numpy as np


class WithGCP(lib.StreamObject):
    mol = None
    model = None
    xc = None
    param = None
    verbose = None
    do_grad = False

    _result = None
    _param = None

    def __init__(self, mf, xc=None, param=None):
        self.parse_mf(mf)
        if xc:
            self.xc = xc
        self.param = param
        self.verbose = mf.verbose

    def parse_mf(self, mf):
        if isinstance(mf, gto.Mole):
            self.mol = mf
            return
        assert(isinstance(mf, scf.hf.SCF) or
               isinstance(mf, mcscf.casci.CASCI))
        self.mol = mf.mol
        if isinstance(mf, mcscf.casci.CASCI):
            self.xc = 'hf'
        else:
            self.xc = getattr(mf, 'xc', 'HF').replace(' ', '')

    @property
    def eng(self):
        self.parse_config()
        model = GCPModel(self.mol.atom_coords())
        self._result = model.get_gcp(grad=self.do_grad)
        return self._result["energy"]

    @property
    def grad(self):
        if self._result is not None and "gradient" in self._result:
            return self._result["gradient"]
        self.parse_config()
        model = GCPModel(self.mol.atom_coords())
        self._result = model.get_gcp(grad=True)
        return self._result["gradient"]


def to_gcp(mf, do_grad=False, **kwargs):
    wrap = wrapper(WithGCP, mf, **kwargs)
    wrap.with_vdw.do_grad = do_grad
    return wrap

def write_xyz(coords, basename):
    pass

def parse_output(output):
    pass

class GCPModel():
    def __init__(self, coords):

    def get_gcp(self, grad=False):
        basename = str(random.randint(1,10000))
        xyzname = write_xyz(self.coords, basename)
        command = ["mctc-gcp", xyzname, "-l", level]
        if self.do_grad:
            command += "--grad"
        p = subprocess.run(command, capture_output=True)
        output = p.stdout
        _result = parse_output(output)
        return _result


if __name__ == '__main__':
    from pyscf import dft
    mol = gto.Mole(atom="""
    C   1.40000000   0.00000000   0.00000000
    C   0.70000000   1.21243557   0.00000000
    C  -0.70000000   1.21243557   0.00000000
    C  -1.40000000   0.00000000   0.00000000
    C  -0.70000000  -1.21243557   0.00000000
    C   0.70000000  -1.21243557   0.00000000
    H   2.49000000   0.00000000   0.00000000
    H   1.24500000   2.15640326   0.00000000
    H  -1.24500000   2.15640326   0.00000000
    H  -2.49000000   0.00000000   0.00000000
    H  -1.24500000  -2.15640326   0.00000000
    H   1.24500000  -2.15640326   0.00000000
    C   1.40000000   0.00000000   2.00000000
    C   0.70000000   1.21243557   2.00000000
    C  -0.70000000   1.21243557   2.00000000
    C  -1.40000000   0.00000000   2.00000000
    C  -0.70000000  -1.21243557   2.00000000
    C   0.70000000  -1.21243557   2.00000000
    H   2.49000000   0.00000000   2.00000000
    H   1.24500000   2.15640326   2.00000000
    H  -1.24500000   2.15640326   2.00000000
    H  -2.49000000   0.00000000   2.00000000
    H  -1.24500000  -2.15640326   2.00000000
    H   1.24500000  -2.15640326   2.00000000
    """, basis="6-31G", unit="Angstrom", verbose=4).build()

    print()
    mf = dft.RKS(mol, xc="PBE0")
    #WithDFTD4(mf).dump_flags()
    assert np.allclose(WithGCP(mf).eng, -3.1667289823883E-02)


    mol = gto.Mole()
    mol.atom = ''' O                  0.00000000    0.00000000   -0.11081188
                   H                 -0.00000000   -0.84695236    0.59109389
                   H                 -0.00000000    0.89830571    0.52404783 '''
    mol.basis = 'cc-pvdz'
    mol.build()
    mf = to_gcp(scf.RHF(mol))
    e0 = mf.kernel()

    mfs = mf.as_scanner()
    e2 = mfs(''' O                 -0.00000000    0.00000000   -0.11181188
                 H                 -0.00000000   -0.84695236    0.59109389
                 H                 -0.00000000    0.89830571    0.52404783 ''')
    e1 = mfs(''' O                  0.00000000    0.00000000   -0.10981188
                   H                 -0.00000000   -0.84695236    0.59109389
                   H                 -0.00000000    0.89830571    0.52404783 ''')
    g = mf.nuc_grad_method().kernel()
    print(mf.with_vdw.grad[0, 2])
    print((e1 - e2)/0.002 * lib.param.BOHR - g[0, 2])
