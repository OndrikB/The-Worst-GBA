# ARM Instructions etc

import main
import bitutils
import shifts

cond_lookup = {0: "EQ", 1: "NE", 2: "CS/HS", 3: "CC/LO",
               5: "PL", 6: "VS", 7: "VC", 8: "HI",
               9: "LS", 10: "GE", 11: "LT", 12: "GT",
               13: "LE", 14: "AL", 15: "NV"}


class ARMInstruction:
    def __init__(self, opcode):
        self.instruction = opcode
        self.condition = None  # Default is undefined
        self.type = None  # Maybe set this?

    def condition_check(self, cpsr) -> bool:
        if main.debug is True:
            print("Current opcode condition: "+str(self.condition)+" ("+cond_lookup[self.condition]+")")
        if self.condition is None:
            print("Something went horribly, horribly wrong!")
            exit(-1)
        elif self.condition == 0 and cpsr["Z"] == 1:
            return True
        elif self.condition == 1 and cpsr["Z"] == 0:
            return True
        elif self.condition == 2 and cpsr["C"] == 1:
            return True
        elif self.condition == 3 and cpsr["C"] == 0:
            return True
        elif self.condition == 4 and cpsr["N"] == 1:
            return True
        elif self.condition == 5 and cpsr["N"] == 0:
            return True
        elif self.condition == 6 and cpsr["V"] == 1:
            return True
        elif self.condition == 7 and cpsr["V"] == 0:
            return True
        elif self.condition == 8 and (cpsr["C"] == 1 and cpsr["Z"] == 0):
            return True
        elif self.condition == 9 and (cpsr["C"] == 0 or cpsr["Z"] == 1):
            return True
        elif self.condition == 10 and cpsr["C"] == cpsr["V"]:
            return True
        elif self.condition == 11 and cpsr["C"] != cpsr["V"]:
            return True
        elif self.condition == 12 and (cpsr["Z"] == 0 and cpsr["C"] == cpsr["V"]):
            return True
        elif self.condition == 13 and (cpsr["Z"] == 1 or cpsr["C"] != cpsr["V"]):
            return True
        elif self.condition == 14:
            return True  # Always
        elif self.condition == 15:
            return True  # Never (Reserved?)

    def decode(self):
        self.condition = (self.instruction & 0xF0000000) >> 28

    def execute(self, cpu):
        cn = self.condition(self, cpu.get_state())
        if cn is True:
            if main.debug is True:
                print("Condition is met")
            if bitutils.get_bits(self.instruction, 25, 27) == 4:  # Branch instruction
                nn = bitutils.get_bits(self.instruction, 0, 23)
                if bitutils.get_bit(self.instruction, 24) == 0:  # B (Branch)
                    cpu.registers[15] = cpu.registers[15]+8+(nn*4)
                elif bitutils.get_bit(self.instruction, 24) == 1:  # BL (Branch with Link)
                    cpu.registers[15] = cpu.registers[15] + 8 + (nn * 4)
                    cpu.registers[14] = cpu.registers[15] + 4
            elif bitutils.get_bits(self.instruction, 8, 27) == 0x12FFF:  # BX, BLX_reg (Branch and Exchange)
                rn = bitutils.get_bits(self.instruction, 0, 3)
                if bitutils.get_bits(self.instruction, 7, 4) == 3:  # BLX (Branch and Exchange with Link, again)
                    cpu.registers[14] = cpu.registers[15] + 4
                cpu.registers[15] = cpu.registers[rn]
                cpu.CPSR |= (bitutils.get_bit(cpu.registers[rn], 0) << 5)  # Sets T bit to 0 bit of Rn
            elif bitutils.get_bits(self.instruction, 24, 27) == 15:  # SWI (Software Interrupt)
                cpu.exception_handling(6, 4)  # Triggers software interrupt TODO: PC offset
            # TODO: Does BKPT exist?
            """if bitutils.get_bits(self.instruction, 24, 27) == 0:  # BKPT (Breakpoint)
                if bitutils.get_bits(self.instruction, 23, 20) == 2 and bitutils.get_bits(self.instruction, 7, 4) == 7:
                    pass  # TODO: find out what BKPT does"""
            if bitutils.get_bits(self.instruction, 25, 27) == 3 and bitutils.get_bit(self.instruction, 4):  # Undefined instruction
                # cpu.exception_handling(7, 4)  # Triggers undefined instruction exception TODO: PC offset
                print("Undefined instruction found! Halting execution!")
                exit()
            elif bitutils.get_bits(self.instruction, 26, 27) == 0:  # ALU
                i = bitutils.get_bit(self.instruction, 25)
                s = bitutils.get_bit(self.instruction, 20)
                opcode = bitutils.get_bits(self.instruction, 24, 21)
                rn = cpu.registers[bitutils.get_bits(self.instruction, 16, 19)]
                dest_addr = bitutils.get_bits(self.instruction, 12, 15)
                op2 = None
                carry = None
                if i == 1:  # Immediate second operand
                    shift_type = bitutils.get_bits(self.instruction, 5, 6)
                    r = bitutils.get_bit(self.instruction, 4)
                    rm = cpu.registers[bitutils.get_bits(self.instruction, 0, 3)]
                    if r == 0:  # Shift by immediate
                        i_s = bitutils.get_bits(self.instruction, 7, 11)
                        if i_s == 0:  # If shift amount is 0
                            if shift_type == 0:  # LSL 0
                                op2 = rm
                            elif shift_type == 1:  # LSR 0
                                op2 = 0
                                cpu.CPSR &= (main.zero_set ^ (1 << 29))  # cleans C bit
                                cpu.CPSR |= bitutils.get_bit(rm, 31)
                            elif shift_type == 2:  # ASR 0
                                bits = [bitutils.get_bit(rm, 31)]*32
                                op2 = bitutils.assemble(bits)
                                cpu.CPSR &= (main.zero_set ^ (1 << 29))  # cleans C bit
                                cpu.CPSR |= (bitutils.get_bit(rm, 31) << 29)
                            elif shift_type == 3:  # ROR 0
                                op2 = rm
                                sh = shifts.RRX(op2, cpu.get_state()["C"])
                                op2 = sh[0]
                                cpu.CPSR &= (main.zero_set ^ (1 << 29))  # cleans C bit
                                cpu.CPSR |= (sh[1] << 29)
                        else:
                            if shift_type == 0:  # LSL
                                shift = shifts.LSL(rm, i_s)
                                op2 = shift[0]
                                carry = shift[1]
                            elif shift_type == 1:  # LSR
                                shift = shifts.LSR(rm, i_s)
                                op2 = shift[0]
                                carry = shift[1]
                            elif shift_type == 2:  # ASR
                                shift = shifts.ASR(rm, i_s)
                                op2 = shift[0]
                                carry = shift[1]
                            elif shift_type == 3:  # ROR
                                shift = shifts.ROR(rm, i_s)
                                op2 = shift[0]
                                carry = shift[1]
                    elif r == 1:
                        r_s = (cpu.registers[bitutils.get_bits(self.instruction, 11, 8)]) & 0xFF
                        if shift_type == 0:  # LSL
                            op2 = rm
                            op2 = shifts.LSL(op2, r_s)[0]
                        elif shift_type == 1:  # LSR
                            op2 = rm
                            op2 = shifts.LSR(op2, r_s)[0]
                        elif shift_type == 2:  # ASR
                            op2 = rm
                            op2 = shifts.ASR(op2, r_s)[0]
                        elif shift_type == 3:  # ROR
                            op2 = rm
                            op2 = shifts.ROR(op2, r_s)[0]
                        if bitutils.get_bit(self.instruction, 7) == 1:
                            print("Undefined instruction in ALU. Exiting.")
                            exit()
                elif i == 0:
                    i_s = bitutils.get_bits(self.instruction, 8, 11)
                    nn = bitutils.get_bits(self.instruction, 0, 7)
                    nn = shifts.ROR(nn, i_s)[0]
                    op2 = nn
                if op2 is None:
                    print("Fatal error detected in ALU. Exiting.")
                    exit()
                # Now, on to the actual opcodes. Fuck me.
                cflag = 0
                void = None
                arith = False
                if opcode == 0:  # AND - AND logical
                    cpu.registers[dest_addr] = rn & op2
                elif opcode == 1:  # EOR - XOR logical
                    cpu.registers[dest_addr] = rn ^ op2
                elif opcode == 2:  # SUB - subtract (A)
                    arith = True
                    cpu.registers[dest_addr] = rn - op2
                elif opcode == 3:  # RSB - subtract reversed (A)
                    arith = True
                    cpu.registers[dest_addr] = op2 - rn
                elif opcode == 4:  # ADD - Add (A)
                    arith = True
                    cpu.registers[dest_addr] = op2 + rn
                    if cpu.registers[dest_addr] >= (1 << 32):
                        cpu.registers &= 0xFFFFFFFF
                        cflag = 1
                elif opcode == 5:  # ADC - Add with carry (A)
                    arith = True
                    cpu.registers[dest_addr] = op2 + rn + cpu.get_state()["C"]
                    if cpu.registers[dest_addr] >= (1 << 32):
                        cpu.registers &= 0xFFFFFFFF
                        cflag = 1
                elif opcode == 6:  # SBC - Sub with carry (A)
                    arith = True
                    cpu.registers[dest_addr] = rn - op2 + cpu.get_state()["C"] - 1
                elif opcode == 7:  # RSC - Sub with carry, reversed (A)
                    arith = True
                    cpu.registers[dest_addr] = op2 - rn + cpu.get_state()["C"] - 1
                elif opcode == 8:  # TST - test
                    void = rn & op2
                elif opcode == 9:  # TEQ - test exclusive
                    void = rn ^ op2
                elif opcode == 10:  # CMP - compare (A)
                    arith = True
                    void = rn - op2
                elif opcode == 11:  # CMN - compare negative (A)
                    arith = True
                    void = rn + op2
                elif opcode == 12:  # ORR - OR logical
                    cpu.registers[dest_addr] = rn | op2
                elif opcode == 13:  # MOV - move
                    cpu.registers[dest_addr] = op2
                elif opcode == 14:  # BIC - bit clear
                    cpu.registers[dest_addr] = rn & ~op2
                elif opcode == 15:  # MVN - not
                    cpu.registers[dest_addr] = ~op2

                if s == 1:
                    if void is None:
                        check = cpu.registers[dest_addr]
                    else:
                        check = void
                    if dest_addr != 15:
                        cpu.CPSR &= (main.zero_set ^ (1 << 29))  # cleans C bit
                        cpu.CPSR &= (main.zero_set ^ (1 << 30))  # cleans Z bit
                        cpu.CPSR &= (main.zero_set ^ (1 << 31))  # cleans N bit
                        if arith is not True:  # logical instructions
                            if carry is not None:
                                cpu.CPSR |= (carry << 29)
                            if check == 0:
                                cpu.CPSR |= (1 << 30)
                            if bitutils.get_bit(check, 31) == 1:
                                cpu.CPSR |= (1 << 31)
                        else:
                            cpu.CPSR |= (cflag << 29)
                            if check == 0:
                                cpu.CPSR |= (1 << 30)
                            if bitutils.get_bit(check, 31) == 1:
                                cpu.CPSR |= (1 << 31)
                    else:  # CPSR, SPSR - these things return from exceptions!
                        cpu.CPSR = cpu.spsr_access()
                        # Setting PC would already be done by dest_addr :>
            elif bitutils.get_bits(self.instruction, 25, 27) == 0:  # MUL, MLA
                s = bitutils.get_bit(self.instruction, 20)
                rd = bitutils.get_bits(self.instruction, 19, 16)
                rn = bitutils.get_bits(self.instruction, 15, 12)
                rs = bitutils.get_bits(self.instruction, 11, 8)

        else:
            if main.debug is True:
                print("Condition is not met")

