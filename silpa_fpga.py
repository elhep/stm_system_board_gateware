from migen import *
from misoc.interconnect.csr import *
from misoc.interconnect import wishbone, csr_bus, wishbone2csr
from functools import reduce
from operator import or_
from misoc.interconnect.csr import CSRStatus, CSRStorage, AutoCSR
from misoc.cores.spi2 import SPIMaster
from SpiInterface import SPIInterface
from spi2wb import SPI2WB


class SlotController(Module, AutoCSR):
    def __init__(self, platform):
        self.slot = []
        for j in range(16):
            self.slot.append(TSTriple(name="slot_{j}".format(j=j)))
        self.io_interrupt = Signal()

        # CSRs
        self.output = CSRStorage(16)
        self.input = CSRStatus(16)
        self.oe = CSRStorage(16)
        self.interrupt = CSRStatus(16)
        self.interrupt_mask = CSRStorage(16)
        self.interrupt_clear = CSRStorage(16, write_from_dev=True)

        # SPI masters
        spi_interface = SPIInterface()
        self.submodules.spi_master = SPIMaster(spi_interface, data_width=16, div_width=8)
        spi_if_signals = [spi_interface.mosi, spi_interface.miso, spi_interface.cs_spi, spi_interface.clk]

        for i, spi_sig in enumerate(spi_if_signals):
            self.comb += [
                self.slot[i].o.eq(Mux(self.spi_master.offline.storage,
                                        self.output.storage[i],
                                        spi_sig.o)),  # If offline then use register value, else use spi interface
                self.input.status[i].eq(self.slot[i].i),
                spi_sig.i.eq(self.slot[i].i),
                self.slot[i].oe.eq(Mux(self.spi_master.offline.storage,
                                          self.oe.storage[i],
                                          spi_sig.oe))
            ]
        for i in range(4, 16):
            self.comb += [
                self.slot[i].o.eq(self.output.storage[i]),
                self.input.status[i].eq(self.slot[i].i),
                self.slot[i].oe.eq(self.oe.storage[i]),
            ]
        self.comb += self.io_interrupt.eq(reduce(or_, self.interrupt.status & self.interrupt_mask.storage))

        # Interrupts
        # TODO: do not trigger interrupt on spi pins if spi is active
        for i in range(16):
            edge = Signal(2)
            self.sync.sys += [
                edge[1].eq(edge[0]),
                edge[0].eq(self.input.status[i]),
                If((edge[0] ^ edge[1]) & (self.interrupt_mask.storage[i] & (~self.oe.storage[i])),
                   self.interrupt.status[i].eq(1),
                ).Elif(self.interrupt_clear.storage[i],
                   self.interrupt.status[i].eq(0)
                )
            ]
        # Clearing interrupt clear register
        self.sync.sys += [
            self.interrupt_clear.dat_w.eq(0),
            self.interrupt_clear.we.eq(0),
            If(self.interrupt_clear.re,
                self.interrupt_clear.we.eq(1)
            )
        ]


class SilpaFPGA(Module, AutoCSR):
    def __init__(self, platform):
        self.reset = Signal()
        self.spi_clk = Signal()
        self.specials += Instance("GSR", i_GSR=~ResetSignal() & self.reset, name="GSR_INST")
        self.specials += Instance("PUR", i_PUR=~ResetSignal(), name="PUR_INST")

        # Clocks
        self.clock_domains.cd_sys = ClockDomain("sys")
        self.clock_domains.cd_sck0 = ClockDomain("sck0", reset_less=True)
        self.clock_domains.cd_sck1 = ClockDomain("sck1", reset_less=True)

        self.comb += [
            self.cd_sck0.clk.eq(~self.spi_clk),
            self.cd_sck1.clk.eq(self.spi_clk)
        ]

        self.address_reg_len = 7
        self.csr_bus = csr_bus.Interface(data_width=16, address_width=self.address_reg_len)
        self.wishbone = wishbone.Interface(data_width=16, adr_width=self.address_reg_len)
        self.submodules.buses = wishbone2csr.WB2CSR(bus_wishbone=self.wishbone, bus_csr=self.csr_bus)

        self.logic = SlotController(platform=platform)
        self.submodules += self.logic

        self.id = CSRStatus(16)
        self.id2 = CSRStatus(16)
        self.comb += self.id.status.eq(0xaaaa)
        self.comb += self.id2.status.eq(0x5555)

        self.submodules.csrs = csr_bus.CSRBank(self.get_csrs(), address=0, bus=self.csr_bus,
                                               align_bits=12 - self.address_reg_len)
        print("# of registers:", len(self.get_csrs()))
        assert len(self.get_csrs()) < 2 ** (self.address_reg_len - 1)

        # SPI Slave
        # TODO: add support to x2 and x4 SPI (QSPI)
        spi = platform.request("spi", 0)
        self.submodules.spi_slave = SPI2WB(platform=platform, wb_bus=self.wishbone, address_width=self.address_reg_len)
        self.comb += [
            self.spi_slave.sdi.eq(spi.mosi),
            self.spi_slave.sel.eq(~spi.cs_n),
            spi.miso.eq(self.spi_slave.sdo),
            self.spi_clk.eq(spi.clk)
        ]

        # for slot in [self.logic.slot[0]]:
        io = platform.request("slot")
        for i, triple in enumerate(self.logic.slot):
            self.specials += triple.get_tristate(io[i])

        self.r_led = platform.request("user_led")
        self.g_led = platform.request("user_led")
        self.b_led = platform.request("user_led")
        self.button = platform.request("usr_btn")

        self.comb += [
            self.cd_sys.clk.eq(platform.request("clk48", 0)),
            self.r_led.eq(self.logic.io_interrupt[0]),
            self.g_led.eq(self.logic.slot[0].o),
            self.reset.eq(self.button),
        ]

        counter = Signal(24)
        self.sync += [
            counter.eq(counter+1),
            If(counter == 0,
               self.b_led.eq(~self.b_led))
        ]
        # platform.add_period_constraint(self.cd_sys.clk, 20.83)
        platform.add_period_constraint(spi.clk, 20)
        # platform.request("GPIO", 0)


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
    from gsd_orangecrab import Platform
    platform = Platform(device="85F")
    silpa_fpga = SilpaFPGA(platform)

    from migen.fhdl.specials import Tristate
    sim = True
    so = {}
    if sim:
        so = {Tristate: LatticeECP5TrellisTristateDiamond}
    platform.build(silpa_fpga, build_name="silpa_fpga", run=not sim, special_overrides=so)
