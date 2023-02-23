from migen import *

class SilpaFPGA(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain("sys")
        self.comb += [
            self.cd_sys.clk.eq(platform.request("clk100")),
        ]
        dio = platform.request("dio")
        dio_oen = platform.request("dio_oen")
        fsen = platform.request("fsen")

        # self.comb += fsen.eq(0)

        self.counter = Signal(10)
        self.sync += self.counter.eq(self.counter+1)

        self.comb += fsen.eq(self.counter == 0)

        self.comb += dio_oen.eq(0b0000)
        for sig in dio:
            # self.comb += sig.eq(self.counter == 0)
            # self.comb += sig.eq(1)
            self.sync += If(self.counter == 0, sig.eq(~sig))


from migen.fhdl.module import Module
from migen.fhdl.bitcontainer import value_bits_sign
class LatticeECP5TrellisTristateImplDiamond(Module):
    def __init__(self, io, o, oe, i):
        nbits, sign = value_bits_sign(io)
        for bit in range(nbits):
            self.specials += Instance("BB",
                i_B   = io[bit] if nbits > 1 else io,
                i_I   = o[bit]  if nbits > 1 else o,
                o_O   = i[bit]  if nbits > 1 else i,
                i_T   = ~oe
            )


class LatticeECP5TrellisTristateDiamond(Module):
    @staticmethod
    def lower(dr):
        return LatticeECP5TrellisTristateImplDiamond(dr.target, dr.o, dr.oe, dr.i)


if __name__ == "__main__":
    from stm_sys_board import Platform
    platform = Platform()
    silpa_fpga = SilpaFPGA(platform)

    from migen.fhdl.specials import Tristate
    sim = False
    so = {}
    if sim:
        so = {Tristate: LatticeECP5TrellisTristateDiamond}
    platform.build(silpa_fpga, build_name="silpa_fpga", run=not sim, special_overrides=so)
