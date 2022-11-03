from migen import *
from misoc.interconnect.csr import *
from misoc.interconnect import wishbone, csr_bus, wishbone2csr
from functools import reduce
from operator import or_
from misoc.interconnect.csr import CSRStatus, CSRStorage, AutoCSR
from misoc.cores.spi2 import SPIMaster
from SpiInterface import SPIInterface
from spi2wb import SPI2WB


class DiotLEC_WB(Module, AutoCSR):
    def __init__(self, platform, address_reg_len=8, slots=8):

        self.address_reg_len = address_reg_len
        self.slots_num = slots

        self.mosi = Signal()
        self.miso = Signal()
        self.cs = Signal()
        self.spi_clk = Signal()
        self.slot = [[] for _ in range(self.slots_num)]
        for i in range(self.slots_num):
            for j in range(16):
                self.slot[i].append(TSTriple(name="slot{i}_{j}".format(i=i, j=j)))
        self.io_interrupt = Signal(self.slots_num)

        # Clocks
        self.clock_domains.cd_sys = ClockDomain("sys")
        self.clock_domains.cd_sck0 = ClockDomain("sck0", reset_less=True)
        self.clock_domains.cd_sck1 = ClockDomain("sck1", reset_less=True)

        self.comb += [
            self.cd_sck0.clk.eq(~self.cd_sck1.clk),
            self.cd_sck1.clk.eq(self.spi_clk)
        ]

        # CSRs
        self.csr_bus = csr_bus.Interface(data_width=16, address_width=8)
        self.wishbone = wishbone.Interface(data_width=16, adr_width=8)
        self.submodules.buses = wishbone2csr.WB2CSR(bus_wishbone=self.wishbone, bus_csr=self.csr_bus)

        for i in range(self.slots_num):
            setattr(self, "output{}".format(i), CSRStorage(16, name="output{}".format(i)))
        for i in range(self.slots_num):
            setattr(self, "input{}".format(i), CSRStatus(16, name="input{}".format(i)))
        for i in range(self.slots_num):
            setattr(self, "oe{}".format(i), CSRStorage(16, name="oe{}".format(i)))
        for i in range(self.slots_num):
            setattr(self, "interrupt{}".format(i), CSRStatus(16, name="interrupt{}".format(i)))
        for i in range(self.slots_num):
            setattr(self, "interrupt_mask{}".format(i), CSRStorage(16, name="interrupt_mask{}".format(i)))
        for i in range(self.slots_num):
            setattr(self, "interrupt_clear{}".format(i), CSRStorage(16, name="interrupt_clear{}".format(i), write_from_dev=True))
        self.id = CSRStatus(16)
        self.id2 = CSRStatus(16)

        # SPI masters
        self.spi_master = []
        spi_if_signals = []
        for i in range(self.slots_num):
            spi_interface = SPIInterface()
            spi_master = SPIMaster(spi_interface, data_width=16, div_width=8)
            setattr(self, "spi_master{}".format(i), spi_master)
            self.spi_master.append(spi_master)
            self.submodules += spi_master
            spi_if_signals.append([spi_interface.mosi, spi_interface.miso, spi_interface.cs_spi, spi_interface.clk])

        for j in range(self.slots_num):
            for i, spi_sig in enumerate(spi_if_signals[j]):
                self.comb += [
                    self.slot[j][i].o.eq(Mux(self.spi_master[j].offline.storage,
                                            getattr(self, "output{}".format(j)).storage[i],
                                            spi_sig.o)),  # If offline then use register value, else use spi interface
                    getattr(self, "input{}".format(j)).status[i].eq(self.slot[j][i].i),
                    spi_sig.i.eq(self.slot[j][i].i),
                    self.slot[j][i].oe.eq(Mux(self.spi_master[j].offline.storage,
                                              getattr(self, "oe{}".format(j)).storage[i],
                                              spi_sig.oe))
                ]
            for i in range(4, 16):
                self.comb += [
                    self.slot[j][i].o.eq(getattr(self, "output{}".format(j)).storage[i]),
                    getattr(self, "input{}".format(j)).status[i].eq(self.slot[j][i].i),
                    self.slot[j][i].oe.eq(getattr(self, "oe{}".format(j)).storage[i]),
                ]
            self.comb += self.io_interrupt[0].eq(
                reduce(or_, getattr(self, "interrupt{}".format(j)).status & getattr(self, "interrupt_mask{}".format(j)).storage))
        self.comb += self.id.status.eq(0xaaaa)
        self.comb += self.id2.status.eq(0x5555)

        # Interrupts
        # TODO: do not trigger interrupt on spi pins if spi is active
        flat_input = [getattr(self, "input{}".format(i)).status[j] for i in range(self.slots_num) for j in range(16)]
        flat_oe = [getattr(self, "oe{}".format(i)).storage[j] for i in range(self.slots_num) for j in range(16)]
        flat_interrupt = [getattr(self, "interrupt{}".format(i)).status[j] for i in range(self.slots_num) for j in range(16)]
        flat_interrupt_clear = [getattr(self, "interrupt_clear{}".format(i)).storage[j] for i in range(self.slots_num) for j in range(16)]
        flat_interrupt_mask = [getattr(self, "interrupt_mask{}".format(i)).storage[j] for i in range(self.slots_num) for j in range(16)]
        for (input, dir, interrupt, clear, mask) in zip(flat_input, flat_oe, flat_interrupt, flat_interrupt_clear,
                                                        flat_interrupt_mask):
            edge = Signal(2)
            self.sync.sys += [
                edge[1].eq(edge[0]),
                edge[0].eq(input),
                If((edge[0] ^ edge[1]) & (mask & (~dir)),
                   interrupt.eq(1),
                ).Elif(clear,
                   interrupt.eq(0)
                )
            ]
        # Clearing interrupt clear register
        for i in range(self.slots_num):
            self.sync.sys += [
                getattr(self, "interrupt_clear{}".format(i)).dat_w.eq(0),
                getattr(self, "interrupt_clear{}".format(i)).we.eq(0),
                If(getattr(self, "interrupt_clear{}".format(i)).re,
                    getattr(self, "interrupt_clear{}".format(i)).we.eq(1)
                )
            ]

        print("# of registers:", len(self.get_csrs()))
        assert len(self.get_csrs()) < 2**(address_reg_len-1)
        self.submodules.csrs = csr_bus.CSRBank(self.get_csrs(), address=0, bus=self.csr_bus, align_bits=4)

        # SPI Slave
        # TODO: extend address to 8 bits or shrink SPI address space
        # TODO: add support to x2 and x4 SPI (QSPI)
        self.submodules.spi_slave = SPI2WB(platform=platform, wb_bus=self.wishbone)
        self.comb += [
            self.spi_slave.sdi.eq(self.mosi),
            self.spi_slave.sel.eq(self.cs),
            self.miso.eq(self.spi_slave.sdo)
        ]


class SilpaFPGA(Module):
    def __init__(self, platform):
        self.reset = Signal()
        self.specials += Instance("GSR", i_GSR=~ResetSignal() & self.reset, name="GSR_INST")
        self.specials += Instance("PUR", i_PUR=~ResetSignal(), name="PUR_INST")

        self.clock_domains.cd_sys = ClockDomain("sys")

        self.logic = DiotLEC_WB(platform=platform, address_reg_len=7, slots=1)
        self.submodules += self.logic

        for slot in [self.logic.slot[0]]:
            io = platform.request("slot")
            for i, triple in enumerate(slot):
                self.specials += triple.get_tristate(io[i])

        self.r_led = platform.request("user_led")
        self.g_led = platform.request("user_led")
        self.b_led = platform.request("user_led")
        self.button = platform.request("usr_btn")

        spi = platform.request("spi", 0)
        self.comb += [
            self.logic.mosi.eq(spi.mosi),
            spi.miso.eq(self.logic.miso),
            self.logic.cs.eq(~spi.cs_n),
            self.logic.spi_clk.eq(spi.clk),
            self.cd_sys.clk.eq(platform.request("clk48", 0)),
            self.r_led.eq(self.logic.io_interrupt[0]),
            self.g_led.eq(self.logic.slot[0][0].o),
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
