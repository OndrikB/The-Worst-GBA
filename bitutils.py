def get_bit(num: int, addr: int) -> int:
    return (num & (1 << addr)) >> addr

def get_bits(num: int, a1: int, a2: int) -> int: # Inclusive on both
    if a1 > a2:
        a1, a2 = a2, a1
    res = 0
    for i in range(a1, a2+1):
        res *= 2
        res += get_bit(num, i)
    return res

def assemble(bits):
    res = 0
    for i in range(len(bits)):
        res += bits[i] << i
    return res