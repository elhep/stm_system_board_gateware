from migen import *
from misoc.interconnect import wishbone, csr_bus, wishbone2csr
from functools import reduce
from operator import or_
from misoc.interconnect.csr import CSRStatus, CSRStorage, AutoCSR
from misoc.cores.spi2 import SPIMaster
from SpiInterface import SPIInterface
from spi2wb import SPI2WB


class SlotController(Module, AutoCSR):
    def __init__(self):
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


class STMSysBoard(Module, AutoCSR):
    def __init__(self, platform):
        self.spi_clk = Signal()
        self.specials += Instance("GSR", i_GSR=~ResetSignal(), name="GSR_INST")
        self.specials += Instance("PUR", i_PUR=~ResetSignal(), name="PUR_INST")

        # Clocks
        self.clock_domains.cd_sys = ClockDomain("sys")
        self.clock_domains.cd_sck0 = ClockDomain("sck0", reset_less=True)
        self.clock_domains.cd_sck1 = ClockDomain("sck1", reset_less=True)

        self.comb += [
            self.cd_sys.clk.eq(platform.request("clk100")),
            self.cd_sck0.clk.eq(~self.spi_clk),
            self.cd_sck1.clk.eq(self.spi_clk)
        ]
        platform.add_period_constraint(platform.lookup_request("clk100", loose=True), 10)

        self.address_reg_len = 7
        self.csr_bus = csr_bus.Interface(data_width=16, address_width=self.address_reg_len)
        self.wishbone = wishbone.Interface(data_width=16, adr_width=self.address_reg_len)
        self.submodules.buses = wishbone2csr.WB2CSR(bus_wishbone=self.wishbone, bus_csr=self.csr_bus)

        for i in range(8):
            setattr(self, "logic{}".format(i), SlotController())
            self.submodules += getattr(self, "logic{}".format(i))

        self.id = CSRStatus(16)
        self.id2 = CSRStatus(16)
        self.comb += self.id.status.eq(0xaaaa)
        self.comb += self.id2.status.eq(0x5555)

        self.submodules.csrs = csr_bus.CSRBank(self.get_csrs(), address=0, bus=self.csr_bus,
                                               align_bits=12 - self.address_reg_len)
        print("# of registers:", len(self.get_csrs()))
        # TODO: increase address length
        # assert len(self.get_csrs()) < 2 ** (self.address_reg_len)

        # SPI Slave
        # TODO: add support to x2 and x4 SPI (QSPI)
        spi = platform.request("qspix1", 0)
        self.submodules.spi_slave = SPI2WB(platform=platform, wb_bus=self.wishbone, address_width=self.address_reg_len)
        self.comb += [
            self.spi_slave.sdi.eq(spi.mosi),
            self.spi_slave.sel.eq(~spi.cs_n),
            spi.miso.eq(self.spi_slave.sdo),
            self.spi_clk.eq(spi.clk)
        ]
        platform.add_period_constraint(spi.clk, 1000/133)
        # spi_sig = platform.request("spi_slave", 1).flatten()
        spi_sig = platform.request("dio")
        interrupts = spi_sig
        # spi_sig = platform.request("spi_slave", 2).flatten()
        spi_sig = platform.request("dio_oen")
        # interrupts += spi_sig
        interrupts = Cat(interrupts, spi_sig)

        for i in range(8):
            connector_num = i+1
            silpa_outputs = [0, 1, 3, 6, 7]
            platform.add_extension(handle_connector_mess(connector_num, silpa_outputs))
            io = platform.request("slot{}".format(connector_num)).flatten()
            if len(io) == 8:
                mlvds = platform.request("slot_mlvds", connector_num)
                io += [mlvds[j] for j in range(len(mlvds))]
            interrupt = interrupts[i]
            self.connect_extension(getattr(self, "logic{}".format(i)), io, silpa_outputs, interrupt, connector_num)

        # hvsup_outputs = [0, 1, 3, 4, 5]

        

        # DIO used for debug
        # dio = platform.request("dio")
        # dio_oen = platform.request("dio_oen")
        # self.comb += dio_oen.eq(0b0000)
        # sig_list = [self.logic0.slot[0].o, self.logic0.slot[1].i, self.logic0.slot[2].o, self.logic0.slot[3].o]
        # for i, sig in enumerate(sig_list):
        #     self.comb += dio[i].eq(sig)

        # Code to place all other  possible clock inputs to verify pinout
        # SPI buses with clock input
        for i in range(1,7):
            spis = platform.request("spi_slave", i)
            spi_clk_domain = "cd_spi{}".format(i)
            setattr(self.clock_domains, spi_clk_domain, ClockDomain("spi{}".format(i), reset_less=True))
            self.comb += [
                getattr(self, spi_clk_domain).clk.eq(spis.clk),
                spis.cs.eq(1)
            ]
            getattr(self.sync, "spi{}".format(i)).__iadd__([
                spis.mosi.eq(spis.miso)
            ])
        clk_stm = platform.request("clk_stm")
        self.clock_domains.cd_stm = ClockDomain("stm")
        self.comb += self.cd_stm.clk.eq(clk_stm)
        fsen = platform.request("fsen")
        self.sync.stm += fsen.eq(~fsen)


    def connect_extension(self, slot_controller, external_signals, outputs, external_interrupt, connector_num):
        internal_interrupt = slot_controller.io_interrupt
        internal_signals = slot_controller.slot
        self.comb += external_interrupt.eq(internal_interrupt)
        for i in range(len(external_signals)):
            triple = internal_signals[i]
            sig = external_signals[i]
            constraint = constraints_dict["slot{}".format(connector_num)][i]
            if constraint[0] == 2.5:
                if not constraint[1]:
                    # Full I/O
                    self.specials += triple.get_tristate(sig)
                elif i in outputs:
                    # Only output
                    self.comb += sig.eq(triple.o)
                else:
                    # Only input
                    self.comb += triple.i.eq(sig)
            elif constraint[0] == 3.3:
                # SE signal connected to MLVDS transceiver
                self.specials += triple.get_tristate(sig)


from stm_sys_board import constraints_dict
from litex.build.generic_platform import *
def handle_connector_mess(slot_num, outputs):
    slot = "slot{}".format(slot_num)
    extension = [
        (slot, 0) + tuple([
            Subsignal("d{}_p".format(i),
                      Pins("{}:d{}_p".format(slot, i)),
                      IOStandard("LVDS25E" if constraint[1] and i in outputs else "LVDS"))
            for i, constraint in enumerate(constraints_dict[slot]) if constraint[0] == 2.5])
    ]
    return(extension)

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
    stm_sys_board = STMSysBoard(platform)

    from migen.fhdl.specials import Tristate
    sim = False
    so = {}
    if sim:
        so = {Tristate: LatticeECP5TrellisTristateDiamond}
    platform.build(stm_sys_board, build_name="stm_sys_board", run=not sim, special_overrides=so)
