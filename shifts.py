# Shifts from ARM, emulated
import bitutils
import main

def LSL(num, shift):
    res = 0
    carry = 0
    if shift == 1:
        num_bits = [bitutils.get_bit(num, i) for i in range(32)]
        res_bits = [0] * 32
        for i in range(31):
            res_bits[i + 1] = num_bits[i]
        carry = num_bits[31]
        res = bitutils.assemble(res_bits)
    else:
        res = num
        for i in range(shift):
            res = LSL(res[0], 1)
    return (res, carry)

def LSR(num, shift):
    res = 0
    if shift == 1:
        num_bits = [bitutils.get_bit(num, i) for i in range(32)]
        res_bits = [0] * 32
        carry = num_bits[0]
        for i in range(31):
            res_bits[i + 1] = num_bits[i]
        res = bitutils.assemble(res_bits)
    else:
        res = num
        for i in range(shift):
            res = LSR(res, 1)
    return (res, carry)

def ASR(num, shift):
    res = 0
    carry = None
    if shift == 1:
        num_bits = [bitutils.get_bit(num, i) for i in range(32)]
        res_bits = [0] * 32
        carry = num_bits[0]
        for i in range(31):
            res_bits[i + 1] = num_bits[i]
        res_bits[31] = res_bits[30]
        res = bitutils.assemble(res_bits)
    else:
        res = num
        for i in range(shift):
            res = LSR(res, 1)
    return (res, carry)

def ROR(num, shift):
    res = 0
    lsb = None
    if shift == 1:
        num_bits = [bitutils.get_bit(num, i) for i in range(32)]
        res_bits = [0] * 32
        lsb = res_bits[0]
        for i in range(31):
            res_bits[i + 1] = num_bits[i]
        res_bits[31] = lsb
        res = bitutils.assemble(res_bits)
    else:
        res = num
        for i in range(shift):
            res = ROR(res, 1)
    return (res, lsb)

def RRX(num, cflag):
    res = 0
    num_bits = [bitutils.get_bit(num, i) for i in range(32)]
    res_bits = [0] * 32
    lsb = res_bits[0]
    for i in range(31):
        res_bits[i + 1] = num_bits[i]
    res_bits[31] = cflag
    res = bitutils.assemble(res_bits)
    return (res, lsb)
