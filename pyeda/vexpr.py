"""
Boolean Vector Logic Expressions

Interface Functions:
    vec
    svec
    uint2vec
    int2vec

Interface Classes:
    VectorExpression
        LogicVector
"""

__copyright__ = "Copyright (c) 2012, Chris Drake"

from .common import clog2, bit_on
from .boolfunc import VectorFunction as VF
from .expr import var, Not, Or, And, Xor, Xnor

def vec(name, *args, **kwargs):
    """Return a vector of variables."""
    if len(args) == 0:
        raise TypeError("vec() expected at least two argument")
    elif len(args) == 1:
        start, stop = 0, args[0]
    elif len(args) == 2:
        start, stop = args
    else:
        raise TypeError("vec() expected at most three arguments")
    if not 0 <= start < stop:
        raise ValueError("invalid range: [{}:{}]".format(start, stop))
    fs = [var(name, index=i) for i in range(start, stop)]
    return LogicVector(*fs, start=start, **kwargs)

def svec(name, *args, **kwargs):
    """Return a signed vector of variables."""
    return vec(name, *args, bnr=VF.TWOS_COMPLEMENT, **kwargs)

def uint2vec(num, length=None):
    """Convert an unsigned integer to a LogicVector."""
    assert num >= 0

    logvec = LogicVector()
    while num != 0:
        logvec.append(num & 1)
        num >>= 1

    if length:
        if length < len(logvec):
            raise ValueError("overflow: " + str(num))
        else:
            logvec.ext(length - len(logvec))

    return logvec

def int2vec(num, length=None):
    """Convert a signed integer to a LogicVector."""
    if num < 0:
        req_length = clog2(abs(num)) + 1
        logvec = uint2vec(2 ** req_length + num)
    else:
        req_length = clog2(num + 1) + 1
        logvec = uint2vec(num)
        logvec.ext(req_length - len(logvec))
    logvec.bnr = VF.TWOS_COMPLEMENT

    if length:
        if length < req_length:
            raise ValueError("overflow: " + str(num))
        else:
            logvec.ext(length - req_length)

    return logvec


class VectorExpression(VF):
    """Vector Boolean function"""

    def __init__(self, *fs, **kwargs):
        self.fs = list(fs)
        self._start = kwargs.get("start", 0)
        self._bnr = kwargs.get("bnr", VF.UNSIGNED)

    def __str__(self):
        return str(self.fs)

    # Operators
    def uor(self):
        return Or(*self.fs)

    def uand(self):
        return And(*self.fs)

    def uxor(self):
        return Xor(*self.fs)

    def __invert__(self):
        fs = [Not(v) for v in self.fs]
        return self.__class__(*fs, start=self._start, bnr=self._bnr)

    def __or__(self, other):
        assert isinstance(other, VectorExpression) and len(self) == len(other)
        return self.__class__(*[Or(*t) for t in zip(self.fs, other.fs)])

    def __and__(self, other):
        assert isinstance(other, VectorExpression) and len(self) == len(other)
        return self.__class__(*[And(*t) for t in zip(self.fs, other.fs)])

    def __xor__(self, other):
        assert isinstance(other, VectorExpression) and len(self) == len(other)
        return self.__class__(*[Xor(*t) for t in zip(self.fs, other.fs)])

    def to_uint(self):
        """Convert vector to an unsigned integer."""
        n = 0
        for i, f in enumerate(self.fs):
            if type(f) is int:
                if f:
                    n += 2 ** i
            else:
                raise ValueError("cannot convert to uint")
        return n

    def to_int(self):
        """Convert vector to an integer."""
        n = self.to_uint()
        if self._bnr == VF.TWOS_COMPLEMENT and self.fs[-1]:
            return -2 ** self.__len__() + n
        else:
            return n

    def restrict(self, constraints):
        """Substitute numbers into a Boolean vector."""
        cpy = self[:]
        for i, _ in enumerate(cpy.fs):
            cpy[i] = cpy[i].restrict(constraints)
        return cpy

    def ext(self, n):
        """Extend this vector by N bits.

        If this vector uses two's complement representation, sign extend;
        otherwise, zero extend.
        """
        if self.bnr == VF.TWOS_COMPLEMENT:
            bit = self.fs[-1]
        else:
            bit = 0
        for _ in range(n):
            self.append(bit)


class LogicVector(VectorExpression):
    """Vector Expression with logical functions."""

    def eq(self, B):
        """banana banana banana"""
        assert isinstance(B, LogicVector) and len(self) == len(B)
        return And(*[Xnor(*t) for t in zip(self.fs, B.fs)])

    def decode(self):
        """banana banana banana"""
        fs = [ And(*[f if bit_on(i, j) else -f
                        for j, f in enumerate(self.fs)])
                  for i in range(2 ** len(self)) ]
        return LogicVector(*fs)

    def ripple_carry_add(self, B, ci=0):
        """banana banana banana"""
        assert isinstance(B, LogicVector) and len(self) == len(B)
        if self.bnr == VF.TWOS_COMPLEMENT or B.bnr == VF.TWOS_COMPLEMENT:
            sum_bnr = VF.TWOS_COMPLEMENT
        else:
            sum_bnr = VF.UNSIGNED
        S = LogicVector(bnr=sum_bnr)
        C = LogicVector()
        for i, A in enumerate(self.fs):
            carry = (ci if i == 0 else C[i-1])
            S.append(Xor(A, B.getifz(i), carry))
            C.append(A * B.getifz(i) + A * carry + B.getifz(i) * carry)
        return S, C
