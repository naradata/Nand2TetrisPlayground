"""
Project 2 chips, simulated in Python.

Every chip here is built ONLY from nand(), exactly like in nand2tetris.
Each function matches one .hdl file:
    - the function's arguments  = the chip's IN pins
    - what it returns           = the chip's OUT pins
    - each line inside          = one line under PARTS:

Run it from Terminal (or VS Code's terminal):
    python3 chips.py
"""

# ======================================================================
# PROJECT 1 — basic gates, all built from NAND
# ======================================================================

def nand(a, b):
    # The one chip we're given for free. Everything else is built from it.
    return 0 if (a == 1 and b == 1) else 1

def not_(a):
    return nand(a, a)                       # Nand(a=in, b=in, out=out);

def and_(a, b):
    return not_(nand(a, b))                 # NOT of NAND = AND

def or_(a, b):
    return nand(not_(a), not_(b))           # De Morgan: a OR b = NOT(NOT a AND NOT b)

def xor(a, b):
    return and_(or_(a, b), nand(a, b))      # "at least one" AND "not both"

def mux(a, b, sel):
    # A switch: sel=0 lets a through, sel=1 lets b through.
    return or_(and_(a, not_(sel)), and_(b, sel))


# ----------------------------------------------------------------------
# 16-bit versions. A BUS (like x[16] in HDL) is a Python list of 16 bits.
# Index 0 is the rightmost bit, just like x[0] in HDL.
# ----------------------------------------------------------------------

def not16(x):
    return [not_(x[i]) for i in range(16)]

def and16(x, y):
    return [and_(x[i], y[i]) for i in range(16)]

def mux16(a, b, sel):
    return [mux(a[i], b[i], sel) for i in range(16)]

def or16way(x):
    # 1 if ANY of the 16 bits is 1. (The course uses two Or8Way chips.)
    result = x[0]
    for i in range(1, 16):
        result = or_(result, x[i])
    return result


# ======================================================================
# PROJECT 2 — the chips you're building now
# ======================================================================

def half_adder(a, b):
    """Add two bits. Returns (sum, carry)."""
    sum_ = xor(a, b)        # Xor(a=a, b=b, out=sum);
    carry = and_(a, b)      # And(a=a, b=b, out=carry);
    return sum_, carry


def full_adder(a, b, c):
    """Add THREE bits (two digits + the carry coming in from the right)."""
    sum1, carry1 = half_adder(a, b)         # HalfAdder(a=a, b=b, sum=sum1, carry=carry1);
    sum_, carry2 = half_adder(sum1, c)      # HalfAdder(a=sum1, b=c, sum=sum, carry=carry2);
    carry = or_(carry1, carry2)             # Or(a=carry1, b=carry2, out=carry);
    return sum_, carry


def add16(x, y):
    """Add two 16-bit numbers, column by column, right to left —
    exactly like adding by hand in school."""
    out = []
    carry = 0                               # nothing to carry into the first column
    for i in range(16):
        s, carry = full_adder(x[i], y[i], carry)
        out.append(s)
    return out                              # the final carry falls off the end (overflow)


def inc16(x):
    """Add 1."""
    one = [1] + [0] * 15                    # 0000000000000001
    return add16(x, one)


def alu(x, y, zx, nx, zy, ny, f, no):
    """The ALU. Follows the 6-step recipe in the comments of ALU.hdl."""
    zero = [0] * 16

    x = mux16(x, zero, zx)                  # 1. zx: replace x with 0?
    x = mux16(x, not16(x), nx)              # 2. nx: flip every bit of x?
    y = mux16(y, zero, zy)                  # 3. zy: replace y with 0?
    y = mux16(y, not16(y), ny)              # 4. ny: flip every bit of y?

    out = mux16(and16(x, y), add16(x, y), f)  # 5. f: AND (0) or ADD (1)?
    out = mux16(out, not16(out), no)        # 6. no: flip the answer?

    zr = not_(or16way(out))                 # answer is zero  -> no bit is 1
    ng = out[15]                            # answer negative -> leftmost bit is 1
    return out, zr, ng


# ======================================================================
# Helpers: convert between normal numbers and lists of bits
# (two's complement, the way Hack stores negative numbers)
# ======================================================================

def to_bits(n):
    n = n & 0xFFFF                          # wrap negatives into 16 bits
    return [(n >> i) & 1 for i in range(16)]

def from_bits(bits):
    n = sum(bit << i for i, bit in enumerate(bits))
    return n - 65536 if bits[15] == 1 else n

def show(bits):
    # Print with the leftmost bit first, the way humans write numbers.
    return "".join(str(b) for b in reversed(bits))


# ======================================================================
# Demo — run the file to see every chip working
# ======================================================================

if __name__ == "__main__":

    print("\nHALF ADDER")
    print(" a b | sum carry")
    for a in (0, 1):
        for b in (0, 1):
            s, c = half_adder(a, b)
            print(f" {a} {b} |  {s}    {c}")

    print("\nFULL ADDER")
    print(" a b c | sum carry")
    for a in (0, 1):
        for b in (0, 1):
            for c in (0, 1):
                s, carry = full_adder(a, b, c)
                print(f" {a} {b} {c} |  {s}    {carry}")

    print("\nADD16")
    for a, b in [(5, 7), (100, 23), (-3, 10)]:
        result = add16(to_bits(a), to_bits(b))
        print(f" {a:>4} + {b:>3} = {from_bits(result):>4}    {show(result)}")

    print("\nINC16")
    for a in (0, 41, -1):
        print(f" {a:>3} + 1 = {from_bits(inc16(to_bits(a)))}")

    # ------------------------------------------------------------------
    # The ALU: every one of its 18 functions, using the switch settings
    # from the book. TRY THIS: change x and y, then run again.
    # ------------------------------------------------------------------
    x, y = 5, 3

    #   name    zx nx zy ny f  no   what Python says it should be
    table = [
        ("0",    (1, 0, 1, 0, 1, 0), 0),
        ("1",    (1, 1, 1, 1, 1, 1), 1),
        ("-1",   (1, 1, 1, 0, 1, 0), -1),
        ("x",    (0, 0, 1, 1, 0, 0), x),
        ("y",    (1, 1, 0, 0, 0, 0), y),
        ("!x",   (0, 0, 1, 1, 0, 1), ~x),
        ("!y",   (1, 1, 0, 0, 0, 1), ~y),
        ("-x",   (0, 0, 1, 1, 1, 1), -x),
        ("-y",   (1, 1, 0, 0, 1, 1), -y),
        ("x+1",  (0, 1, 1, 1, 1, 1), x + 1),
        ("y+1",  (1, 1, 0, 1, 1, 1), y + 1),
        ("x-1",  (0, 0, 1, 1, 1, 0), x - 1),
        ("y-1",  (1, 1, 0, 0, 1, 0), y - 1),
        ("x+y",  (0, 0, 0, 0, 1, 0), x + y),
        ("x-y",  (0, 1, 0, 0, 1, 1), x - y),
        ("y-x",  (0, 0, 0, 1, 1, 1), y - x),
        ("x&y",  (0, 0, 0, 0, 0, 0), x & y),
        ("x|y",  (0, 1, 0, 1, 0, 1), x | y),
    ]

    print(f"\nALU   (x = {x}, y = {y})")
    print(" function  zx nx zy ny f no |  out   zr ng | check")
    for name, switches, expected in table:
        out, zr, ng = alu(to_bits(x), to_bits(y), *switches)
        value = from_bits(out)
        ok = "ok" if value == expected else f"WRONG (expected {expected})"
        bits = "  ".join(str(s) for s in switches)
        print(f" {name:<8}  {bits} | {value:>4}   {zr}  {ng} | {ok}")
    print()
