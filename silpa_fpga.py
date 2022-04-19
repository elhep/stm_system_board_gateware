from migen import *
from migen.genlib.coding import Decoder
from migen.genlib.cdc import PulseSynchronizer, BusSynchronizer


class SR(Module):
    """
    Shift register, SPI slave
    * CPOL = 0 (clock idle low during ~SEL)
    * CPHA = 0 (sample on first edge, shift on second)
    * SPI mode 0
    * samples SDI on rising clock edges (SCK1 domain)
    * shifts out SDO on falling clock edges (SCK0 domain)
    * MSB first
    * the first output bit (MSB) is undefined
    * the first output bit is available from the start of the SEL cycle until
      the first falling edge
    * the first input bit is sampled on the first rising edge
    * on the first rising edge with SEL assered, the parallel data DO
      is loaded into the shift register
    * following at least one rising clock edge, on the deassertion of SEL,
      the shift register is loaded into the parallel data register DI
    """
    def __init__(self, width):
        self.width = width

        self.sdi = Signal()
        self.sdo = Signal()
        self.sel = Signal()

        self.di = Signal(width)
        self.do = Signal(width)

        # # #

        sr = Signal(width)

        self.clock_domains.cd_le = ClockDomain("le", reset_less=True)
        # clock the latch domain from selection deassertion but only after
        # there was a serial clock edge with asserted select (i.e. ignore
        # glitches).
        # self.specials += Instance("FDPE", p_INIT=1,
        #         i_D=0, i_C=ClockSignal("sck1"), i_CE=self.sel, i_PRE=~self.sel,
        #         o_Q=self.cd_le.clk)
        self.specials += Instance("FD1P3BX",
              i_D=0, i_CK=ClockSignal("sck1"), i_SP=self.sel, i_PD=~self.sel,
              o_Q=self.cd_le.clk)

        # self.sync.sck0 += [
        #         If(self.sel,
        #             self.sdo.eq(sr[-1]),
        #         )
        # ]
        self.sync.sck1 += [
                If(self.sel,
                   self.sdo.eq(sr[-1]),
                    sr[0].eq(self.sdi),
                    If(self.cd_le.clk,
                        sr[1:].eq(self.do[:-1])
                    ).Else(
                        sr[1:].eq(sr[:-1])
                    )
                )
        ]
        self.sync.le += [
            self.di.eq(sr)
        ]


class DiotLEC_Simple(Module):
    def __init__(self, address_reg_len=6, slots=8):
        self.specials += Instance("GSR", i_GSR=~ResetSignal(), name="GSR_INST")
        self.specials += Instance("PUR", i_PUR=~ResetSignal(), name="PUR_INST")

        self.address_reg_len = address_reg_len
        self.slots_num = slots

        self.mosi = Signal()
        self.miso = Signal()
        self.cs = Signal()
        self.spi_clk = Signal()
        self.output = []
        for i in range(self.slots_num):
            self.output.append(Signal(16, name="output{}".format(i)))

        # Clocks
        self.clock_domains.cd_sys = ClockDomain("sys")
        self.clock_domains.cd_sck0 = ClockDomain("sck0", reset_less=True)
        self.clock_domains.cd_sck1 = ClockDomain("sck1", reset_less=True)
        # self.specials += [
        #     Instance("BUFG", i_I=self.spi_clk, o_O=self.cd_sck1.clk),
        # ]
        self.comb += [
            self.cd_sck0.clk.eq(~self.cd_sck1.clk),
            self.cd_sck1.clk.eq(self.spi_clk)
        ]

        self.submodules.address_reg = SR(self.address_reg_len)
        self.output_reg = []
        for i in range(self.slots_num):
            self.output_reg.append(SR(16))
            setattr(self.submodules, "output_reg{}".format(i), self.output_reg[i])
        self.select = Cat([self.output_reg[i].sel for i in range(self.slots_num)])

        self.select_decoder = Decoder(2**self.address_reg_len+1)
        self.submodules += self.select_decoder

        self.counter1 = Signal(10)
        self.counter1_reset_done = Signal()
        self.counter1_reset = Signal()
        self.sync.sck1 += [
            If(self.counter1_reset & ~self.counter1_reset_done,
               self.counter1.eq(1),
               self.counter1_reset_done.eq(1)
            ).Elif(self.cs,
               self.counter1.eq(self.counter1 + 1),
               self.counter1_reset_done.eq(0)
            )
        ]
        self.counter0 = Signal(10)
        self.counter0_reset_done = Signal()
        self.counter0_reset = Signal()
        self.sync.sck0 += [
            If(self.counter0_reset & ~self.counter0_reset_done,
               self.counter0.eq(1),
               self.counter0_reset_done.eq(1)
            ).Elif(self.cs,
                self.counter0.eq(self.counter0 + 1),
                self.counter0_reset_done.eq(0)
            )
        ]

        self.cs_edge = Signal(2)
        self.counter0_reset_start = Signal()
        self.counter1_reset_start = Signal()
        self.sync.sys += [
            self.cs_edge[1].eq(self.cs_edge[0]),
            self.cs_edge[0].eq(self.cs),
            If(self.cs_edge == C(2),  # Falling edge
               self.counter0_reset_start.eq(1),
               self.counter1_reset_start.eq(1)
            ).Else(
                If(self.counter0_reset_done,
                   self.counter0_reset_start.eq(0)
                   ),
                If(self.counter1_reset_done,
                   self.counter1_reset_start.eq(0))
            )
        ]

        self.comb += [
            self.counter0_reset.eq(self.counter0_reset_start),
            self.counter1_reset.eq(self.counter1_reset_start)
        ]

        miso_selector = Case(self.address_reg.di,
                             {}
                             )
        for i in range(self.slots_num):
            miso_selector.cases[C(i)] = [self.miso.eq(self.output_reg[i].sdo)]

        self.comb += [
            self.address_reg.sdi.eq(self.mosi),
            self.address_reg.do.eq(self.address_reg.di),
            [self.output_reg[i].sdi.eq(self.mosi) for i in range(self.slots_num)],
            [self.output[i].eq(self.output_reg[i].di) for i in range(self.slots_num)],
            [self.output_reg[i].do.eq(self.output_reg[i].di) for i in range(self.slots_num)],
            If((self.counter1 >= C(self.address_reg_len)) & (self.counter1 < C(self.address_reg_len + 16)),
               self.select_decoder.i.eq(self.address_reg.di + 1),
               ).Else(
                self.select_decoder.i.eq(0),
            ),
            If((self.counter0 >= C(self.address_reg_len)) & (self.counter0 < C(self.address_reg_len + 16)),
               miso_selector,
               ).Else(
                self.miso.eq(self.address_reg.sdo)
            ),
            self.address_reg.sel.eq(self.select_decoder.o[0] & self.cs),
            self.select.eq(self.select_decoder.o[1:]),
        ]


class SilpaFPGA(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain("sys")

        self.logic = DiotLEC_Simple(address_reg_len=6, slots=8)
        self.submodules += self.logic

        spi = platform.request("spi", 0)
        self.comb += [
            self.logic.mosi.eq(spi.mosi),
            self.logic.miso.eq(spi.miso),
            self.logic.cs.eq(~spi.cs_n),
            self.logic.spi_clk.eq(spi.clk),
            self.cd_sys.clk.eq(platform.request("clk48", 0))
        ]
        # platform.add_period_constraint(self.cd_sys.clk, 20.83)
        platform.add_period_constraint(spi.clk, 20)
        # platform.request("GPIO", 0)

if __name__ == "__main__":
    from gsd_orangecrab import Platform
    from migen.fhdl.verilog import convert
    platform = Platform(device="85F")
    silpa_fpga = SilpaFPGA(platform)
    # platform.build(silpa_fpga, build_name="silpa_fpga")

    #Simulation
    logic = DiotLEC_Simple()
    #
    ios = {logic.mosi, logic.miso, logic.cs, logic.spi_clk, logic.cd_sys.clk, logic.cd_sys.rst}
    for item in logic.output:
        ios.add(item)
    convert(logic, ios=ios).write("output.v")
    # convert(silpa_fpga).write("output.v")
