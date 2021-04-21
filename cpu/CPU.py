"""
Useful things with ints and bits:
To flip bit *n*, do (x ^ (1 << n))
To set bit *n* to 0, do (x & (max ^ (1 << n)))
To set bit *n* to 1, do (x | (1 << n))
"""
m_dict_ints = {16: "USR", 17: "FIQ", 18: "IRQ", 19: "SWI", 23: "ABT", 27: "UND", 31: "SYS"}
m_dict_modes = {v: k for k, v in m_dict_ints.items()}
import main


class CPU:
    def __init__(self):
        self.registers = [0] * 16
        self.registers_banked = [0] * 16
        self.registers_fiq = [0] * 16
        self.registers_svc = [0] * 16
        self.registers_abt = [0] * 16
        self.registers_irq = [0] * 16
        self.registers_und = [0] * 16
        self.CPSR = 0  # TODO: set this to a proper value
        self.SPSR_fiq = 0
        self.SPSR_svc = 0
        self.SPSR_abt = 0
        self.SPSR_irq = 0
        self.SPSR_und = 0

    def spsr_access(self):
        mode = self.get_state()["M"]
        if mode == "FIQ":
            return self.SPSR_fiq
        elif mode == "IRQ":
            return self.SPSR_irq
        elif mode == "SVC":
            return self.SPSR_svc
        elif mode == "UND":
            return self.SPSR_und
        elif mode == "ABT":
            return self.SPSR_abt
        else:
            print("User tried accessing SPSR!")
            exit(-1)


    def register_update(self):
        self.registers_svc[8:13] = self.registers[8:13]
        self.registers_abt[8:13] = self.registers[8:13]
        self.registers_irq[8:13] = self.registers[8:13]
        self.registers_und[8:13] = self.registers[8:13]

    def get_state(self):
        global m_dict_ints
        state = {"N": (self.CPSR & (1 << 31)) >> 31, "Z": (self.CPSR & (1 << 30)) >> 30, "C": (self.CPSR & (1 << 29)) >> 29,
                 "V": (self.CPSR & (1 << 28)) >> 28, "Q": (self.CPSR & (1 << 27)) >> 27,
                 "I": (self.CPSR & (1 << 7)) >> 7, "F": (self.CPSR & (1 << 6)) >> 6, "T": (self.CPSR & (1 << 5)) >> 5}
        mode = self.CPSR & 31
        state["M"] = m_dict_ints[mode]
        return state

    def mode_swap(self, new_mode):
        global m_dict_modes
        mode_int = m_dict_modes[new_mode]  # This *should* set the mode bits correctly
        self.CPSR &= (main.zero_set ^ 31)
        self.CPSR |= mode_int
        self.register_update()
        if new_mode == "SYS" or new_mode == "USR":
            self.registers[8:15] = self.registers_banked[8:15]
        elif new_mode == "FIQ":
            self.registers_banked[8:15] = self.registers[8:15]
            self.registers[8:15] = self.registers_fiq[8:15]
        elif new_mode == "SVC":
            self.registers_banked[8:15] = self.registers[8:15]
            self.registers[8:15] = self.registers_svc[8:15]
        elif new_mode == "ABT":
            self.registers_banked[8:15] = self.registers[8:15]
            self.registers[8:15] = self.registers_abt[8:15]
        elif new_mode == "IRQ":
            self.registers_banked[8:15] = self.registers[8:15]
            self.registers[8:15] = self.registers_irq[8:15]
        elif new_mode == "UND":
            self.registers_banked[8:15] = self.registers[8:15]
            self.registers[8:15] = self.registers_und[8:15]
        elif new_mode == "SWI":
            self.registers_banked[8:15] = self.registers[8:15]
            self.registers[8:15] = self.registers_svc[8:15]

    def exception_handling(self, prio, nn):
        # let's try implementing one
        BASE = 0
        if prio == 1:  # Reset exception
            self.registers_svc[14] = self.registers[15] + nn  # PC
            self.SPSR_svc = self.CPSR
            self.mode_swap("SVC")
            self.CPSR |= (1 << 7)  # Disable IRQs (done by all exceptions)
            self.CPSR |= (1 << 6)  # Disable FIQs (done only by Reset and FIQ)
            self.registers[15] = BASE + 0
        elif prio == 7: # Undefined instruction
            self.registers_und[14] = self.registers[15] + nn  # Old PC saved
            self.SPSR_und = self.CPSR
            self.mode_swap("UND")
            self.CPSR |= (1 << 7)  # Disable IRQs (done by all exceptions)
            self.registers[15] = BASE + 4 #Execution moved to exception vector
        elif prio == 6:  # Software interrupt
            self.registers_svc[14] = self.registers[15] + nn  # PC
            self.SPSR_svc = self.CPSR
            self.mode_swap("SWI")
            self.CPSR |= (1 << 7)  # Disable IRQs (done by all exceptions)
            self.registers[15] = BASE + 8
        """elif prio == 5:  # Prefetch Abort
            self.registers_abt[14] = self.registers[15] + nn  # PC
            self.SPSR_abt = self.CPSR
            self.mode_swap("ABT")
            self.CPSR |= (1 << 7)  # Disable IRQs (done by all exceptions)
            self.registers[15] = BASE + 12
        elif prio == 2:  # Data Abort
            self.registers_abt[14] = self.registers[15] + nn  # PC
            self.SPSR_abt = self.CPSR
            self.mode_swap("ABT")
            self.CPSR |= (1 << 7)  # Disable IRQs (done by all exceptions)
            self.registers[15] = BASE + 16"""
        if prio == 4: # IRQ
            self.registers_irq[14] = self.registers[15] + nn  # PC
            self.SPSR_irq = self.CPSR
            self.mode_swap("IRQ")
            self.CPSR |= (1 << 7)  # Disable IRQs (done by all exceptions)
            self.registers[15] = BASE + 24
        """elif prio == 3: # FIQ
            self.registers_fiq[14] = self.registers[15] + nn  # PC
            self.SPSR_fiq = self.CPSR
            self.mode_swap("FIQ")
            self.CPSR |= (1 << 7)  # Disable IRQs (done by all exceptions)
            self.CPSR |= (1 << 6)  # Disable FIQs (done only by Reset and FIQ)
            self.registers[15] = BASE + 28"""
