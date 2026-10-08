"""Complex sparse LU with MKL PARDISO (ctypes; pypardiso supports real matrices only)."""
import ctypes
import glob
import os

import numpy as np
from scipy import sparse

_lib = None


def _mkl():
    global _lib
    if _lib is None:
        path = os.environ.get("PYPARDISO_MKL_RT") or (glob.glob("/usr/local/lib/libmkl_rt.so*") + [None])[0]
        _lib = ctypes.CDLL(path)
        f = _lib.pardiso
        P32 = ctypes.POINTER(ctypes.c_int32)
        f.argtypes = [ctypes.POINTER(ctypes.c_int64), P32, P32, P32, P32, P32, ctypes.c_void_p, P32, P32,
                      P32, P32, P32, P32, ctypes.c_void_p, ctypes.c_void_p, P32]
        f.restype = None
    return _lib


class Factor:
    """A = complex sparse matrix (any format); solve(b) for 1-D or 2-D complex b."""
    MTYPE = 13                                     # complex, nonsymmetric

    def __init__(self, A, ooc=False):
        A = sparse.csr_matrix(A, dtype=np.complex128)
        A.sort_indices()
        self.n = A.shape[0]
        self.a = np.ascontiguousarray(A.data)
        self.ia = (A.indptr + 1).astype(np.int32)
        self.ja = (A.indices + 1).astype(np.int32)
        self.pt = np.zeros(64, np.int64)
        self.iparm = np.zeros(64, np.int32)
        self.iparm[0] = 1                          # user iparm
        self.iparm[1] = 3                          # parallel nested dissection
        self.iparm[7] = 2                          # iterative refinement steps
        self.iparm[9] = 13                         # pivot perturbation 1e-13
        self.iparm[10] = 1                         # scaling
        self.iparm[12] = 1                         # weighted matching
        self.iparm[59] = 2 if ooc else 0
        self._call(12, np.zeros(1, complex), np.zeros(1, complex), 1)

    def _call(self, phase, b, x, nrhs):
        err = ctypes.c_int32(0)
        i32 = lambda v: ctypes.byref(ctypes.c_int32(v))
        P32 = ctypes.POINTER(ctypes.c_int32)
        _mkl().pardiso(self.pt.ctypes.data_as(ctypes.POINTER(ctypes.c_int64)), i32(1), i32(1), i32(self.MTYPE),
                       i32(phase), i32(self.n), self.a.ctypes.data, self.ia.ctypes.data_as(P32),
                       self.ja.ctypes.data_as(P32), np.zeros(1, np.int32).ctypes.data_as(P32), i32(nrhs),
                       self.iparm.ctypes.data_as(P32), i32(0), b.ctypes.data, x.ctypes.data, ctypes.byref(err))
        if err.value != 0:
            raise RuntimeError(f"PARDISO error {err.value} in phase {phase}")

    def solve(self, b):
        b = np.asfortranarray(b, dtype=np.complex128)
        x = np.zeros_like(b)
        self._call(33, b, x, 1 if b.ndim == 1 else b.shape[1])
        return x

    @property
    def mem_GB(self):
        return max(self.iparm[14], self.iparm[15] + self.iparm[16])/1e6

    def free(self):
        self._call(-1, np.zeros(1, complex), np.zeros(1, complex), 1)
