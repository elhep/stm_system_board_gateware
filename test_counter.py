from migen import *
import os

class SilpaFPGA(Module):
    def __init__(self, platform):
        self.reset = Signal()
        self.spi_clk = Signal()
        self.specials += Instance("GSR", i_GSR=~ResetSignal(), name="GSR_INST")
        self.specials += Instance("PUR", i_PUR=~ResetSignal(), name="PUR_INST")

        self.clock_domains.cd_sys = ClockDomain("sys")
        self.clock_domains.cd_sck1 = ClockDomain("sck1", reset_less=True)
        spi = platform.request("qspix1", 0)
        self.comb += [
            self.cd_sys.clk.eq(platform.request("clk100")),
            self.cd_sck1.clk.eq(spi.clk)
        ]
        dio = platform.request("dio")
        dio_oen = platform.request("dio_oen")
        # fsen = platform.request("fsen")

        # self.counter = Signal(4)
        # self.sync += self.counter.eq(self.counter+1)

        self.counter1 = Signal(5)

        self.sel = Signal()
        self.comb += self.sel.eq(~spi.cs_n)
        self.specials += Instance("counter",
                                  p_WIDTH=len(self.counter1),
                                  i_clk=ClockSignal("sck1"),
                                  i_reset=~self.sel | ResetSignal(),
                                  o_counter=self.counter1,
                                  i_en=self.sel
                                  )
        platform.add_source(os.path.join(os.path.abspath(os.path.dirname(__file__)), "counter.v"))

        # self.comb += fsen.eq(self.counter1 == 0)

        self.comb += dio_oen.eq(0b0000)
        for i, sig in enumerate(dio):
            self.comb += sig.eq(self.counter1[i])


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
