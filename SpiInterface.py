from migen import *
# from migen.genlib.fsm import FSM, NextState
# from misoc.interconnect.csr import *
# from misoc.interconnect.stream import *
# from misoc.interconnect import wishbone


class SPIInterface(Module):
    """Drive one SPI bus with a single interface or passthrough pins if SPI is offline."""
    def __init__(self):
        self.cs = Signal()
        self.cs_polarity = Signal.like(self.cs)
        self.clk_next = Signal()
        self.clk_polarity = Signal()
        self.cs_next = Signal()
        self.ce = Signal()
        self.sample = Signal()
        self.offline = Signal()
        self.half_duplex = Signal()
        self.sdi = Signal()
        self.sdo = Signal()

        self.mosi = TSTriple()
        self.miso = TSTriple()
        self.clk = TSTriple()
        self.cs_spi = TSTriple()

        i = 0

        n = 1
        # TODO cs, clk, mosi to nie powinny być triple, tylko sygnały, do których z zewnątrz się podłączy własciwe
        #  tstriple utworzone w diot_lec_wb
        # cs = TSTriple(n)
        self.cs_spi.o.reset = C(1)
        # clk = TSTriple()
        # mosi = TSTriple()
        # miso = TSTriple()
        miso_reg = Signal(reset_less=True)
        mosi_reg = Signal(reset_less=True)
        # self.specials += [
        #         cs.get_tristate(p.cs_n),
        #         clk.get_tristate(p.clk),
        # ]
        # if hasattr(p, "mosi"):
        #     self.specials += mosi.get_tristate(p.mosi)
        # if hasattr(p, "miso"):
        #     self.specials += miso.get_tristate(p.miso)
        self.comb += [
                self.miso.oe.eq(0),
                self.mosi.o.eq(self.sdo),
                self.miso.o.eq(self.sdo),
                self.cs_spi.oe.eq(~self.offline),
                self.clk.oe.eq(~self.offline),
                self.mosi.oe.eq(~(self.offline | self.half_duplex)),
                If(self.cs[i:i + n] != 0,
                    self.sdi.eq(Mux(self.half_duplex, mosi_reg, miso_reg))
                )
        ]
        self.sync += [
                If(self.ce,
                    self.cs_spi.o.eq((self.cs_next
                        & self.cs[i:i + n]) ^ ~self.cs_polarity[i:i + n]),
                    self.clk.o.eq(self.clk_next ^ self.clk_polarity)
                ),
                If(self.sample,
                    miso_reg.eq(self.miso.i),
                    mosi_reg.eq(self.mosi.i)
                )
        ]
