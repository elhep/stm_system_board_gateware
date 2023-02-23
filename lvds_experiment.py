from migen import *

class SilpaFPGA(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain("sys")
        self.comb += [
            self.cd_sys.clk.eq(platform.request("clk100")),
        ]
        self.slot = []
        for j in range(4):
            self.slot.append(TSTriple(name="slot_{j}".format(j=j)))
        spi = platform.request("qspix4")
        for i, slot in enumerate(self.slot):
            self.comb += [
                slot.o.eq(spi.clk),
                spi.data[i].eq(slot.i),
                slot.oe.eq(spi.cs_n)
            ]
        io = platform.request("slot").flatten()
        for i in range(4):
            self.specials += self.slot[i].get_tristate(io[i])

        spi_slave = platform.request("spi_slave", 1)
        self.sync += [
            spi_slave.mosi.eq(spi_slave.miso),
            spi_slave.cs.eq(spi_slave.clk)
        ]


from stm_sys_board import _connector_constraints
from litex.build.generic_platform import *
def handle_connector_mess(slot_num):
    extension = [
        ("slot", slot_num) + tuple([
            Subsignal("d{}_p".format(j),
                      Pins("slot{}:d{}_p".format(slot_num, j)),
                      IOStandard("LVDS25E" if _connector_constraints[slot_num-1][2][j] else "LVDS"))
            for j in range(8 if slot_num not in [3, 4] else 16)])

    ]
    return(extension)
#IOStandard("LVDS25E" if _connector_constraints[slot_num][2][j] else "LVDS"))

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
    platform.add_extension(handle_connector_mess(6))
    # print(platform.constraint_manager.available)
    silpa_fpga = SilpaFPGA(platform)

    from migen.fhdl.specials import Tristate
    sim = True
    so = {}
    if sim:
        so = {Tristate: LatticeECP5TrellisTristateDiamond}
    platform.build(silpa_fpga, build_name="silpa_fpga", run=not sim, special_overrides=so)
