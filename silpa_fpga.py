from migen import *
from migen.genlib.coding import Decoder
from migen.genlib.cdc import PulseSynchronizer, BusSynchronizer
from misoc.interconnect.csr import *
from misoc.interconnect import wishbone, csr_bus, wishbone2csr
from misoc.integration.wb_slaves import WishboneSlaveManager
from functools import reduce
from operator import or_


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
    def __init__(self, address_reg_len=8, slots=8):
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
        # self.specials += [
        #     Instance("BUFG", i_I=self.spi_clk, o_O=self.cd_sck1.clk),
        # ]
        self.comb += [
            self.cd_sck0.clk.eq(~self.cd_sck1.clk),
            self.cd_sck1.clk.eq(self.spi_clk)
        ]

        self.submodules.address_reg = SR(self.address_reg_len)
        self.registers = []
        for _ in range(self.slots_num):
            self.add_register("output")
        for _ in range(self.slots_num):
            self.add_register("input")
        for _ in range(self.slots_num):
            self.add_register("dir")
        for _ in range(self.slots_num):
            self.add_register("interrupt")
        for _ in range(self.slots_num):
            self.add_register("interrupt_mask")
        for _ in range(self.slots_num):
            self.add_register("interrupt_clear")
        self.select = Cat([register.sel for register in self.registers])

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
            miso_selector.cases[C(i)] = [self.miso.eq(self.registers[i].sdo)]

        self.comb += [
            # SPI
            self.address_reg.sdi.eq(self.mosi),
            self.address_reg.do.eq(self.address_reg.di),
            [register.sdi.eq(self.mosi) for register in self.registers],
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

            # These registers hold their value when written to
            [register.do.eq(register.di) for register in self.output + self.dir + self.interrupt_mask],

            [self.slot[i][j].o.eq(self.output[i].di[j]) for i in range(self.slots_num) for j in range(16)],
            [self.input[i].do[j].eq(self.slot[i][j].i) for i in range(self.slots_num) for j in range(16)],
            [self.slot[i][j].oe.eq(self.dir[i].di[j]) for i in range(self.slots_num) for j in range(16)],

        ]

        # Interrupts
        flat_input = [self.input[i].do[j] for i in range(self.slots_num) for j in range(16)]
        flat_dir = [self.dir[i].di[j] for i in range(self.slots_num) for j in range(16)]
        flat_interrupt = [self.interrupt[i].do[j] for i in range(self.slots_num) for j in range(16)]
        flat_interrupt_clear = [self.interrupt_clear[i].di[j] for i in range(self.slots_num) for j in range(16)]
        flat_interrupt_mask = [self.interrupt_mask[i].di[j] for i in range(self.slots_num) for j in range(16)]
        for (input, dir, interrupt, clear, mask) in zip(flat_input, flat_dir, flat_interrupt, flat_interrupt_clear, flat_interrupt_mask):
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

        # self.sync.sys += [
        #     [interrupt_clear_reg.do.eq(0) for interrupt_clear_reg in self.interrupt_clear],
        # ]
        # for i in range(self.slots_num):
            # cd = getattr(self.sync, "interrupt_clear{}_le".format(i+1))
            # cd += timeline(True, [(1, [self.interrupt_clear[i].sel.eq(1)]), (2, [self.interrupt_clear[i].sel.eq(0)])])
            # cd += self.interrupt_clear[i].di.eq(self.interrupt_clear[i].do)
            # ResetInserter(clock_domains=["sck1", "le"])(self.interrupt_clear[i])
            # self.sync.sys += self.interrupt_clear[i].cd_sck1.rst.eq(1)

        self.comb += [self.io_interrupt[i].eq(reduce(or_, self.interrupt[i].do & self.interrupt_mask[i].di)) for i in range(self.slots_num)]

    def add_register(self, name):
        assert len(self.registers) < 2**self.address_reg_len
        sr = SR(16)
        # add it to named register list
        if not hasattr(self, name):
            setattr(self, name, [])
        getattr(self, name).append(sr)
        # add it to all registers list
        self.registers.append(sr)
        # add it to submodules
        setattr(self.submodules, "{}{}".format(name, len(getattr(self, name))), sr)


from misoc.interconnect.csr import CSRStatus, CSRStorage, AutoCSR
import misoc.interconnect
from math import log2, ceil


class SR_WB(Module):
    def __init__(self, wb_bus, address_width=7, data_width=16):
        self.wb = wb_bus
        # 1 bit r/w, 7 bit address, 16 bit data
        self.width = 1 + address_width + data_width

        self.sdi = Signal()
        self.sdo = Signal()
        self.sel = Signal()

        self.di = Signal(self.width)
        self.do = Signal(self.width)

        # # #

        sr = Signal(self.width)

        self.clock_domains.cd_le = ClockDomain("le", reset_less=True)
        self.specials += Instance("FD1P3BX",
              i_D=0, i_CK=ClockSignal("sck1"), i_SP=self.sel, i_PD=~self.sel,
              o_Q=self.cd_le.clk)

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
            self.di.eq(sr),
            #write
            If(self.di[0] == 1,
                self.wb.adr.eq(self.di[1:1+address_width]),
                self.wb.dat_w.eq(self.di[1+address_width:]),
                self.wb.sel.eq(2**len(self.wb.sel) - 1),
                self.wb.we.eq(1),
                self.wb.cyc.eq(1),
                self.wb.stb.eq(1)
            ).Else(
                self.wb.we.eq(0),
                self.wb.cyc.eq(0),
                self.wb.stb.eq(0)
            )
        ]

        self.counter1 = Signal(ceil(log2(self.width)))
        self.counter1_reset_done = Signal()
        self.counter1_reset = Signal()
        self.sync.sck1 += [
            If(self.counter1_reset & ~self.counter1_reset_done,
               self.counter1.eq(0),
               self.counter1_reset_done.eq(1)
            ).Elif(self.sel,
               self.counter1.eq(self.counter1 + 1),
               self.counter1_reset_done.eq(0)
            )
        ]


class DiotLEC_WB(Module, AutoCSR):
    def __init__(self, address_reg_len=8, slots=8):
        self.specials += Instance("GSR", i_GSR=~ResetSignal(), name="GSR_INST")
        self.specials += Instance("PUR", i_PUR=~ResetSignal(), name="PUR_INST")

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
        # self.specials += [
        #     Instance("BUFG", i_I=self.spi_clk, o_O=self.cd_sck1.clk),
        # ]
        self.comb += [
            self.cd_sck0.clk.eq(~self.cd_sck1.clk),
            self.cd_sck1.clk.eq(self.spi_clk)
        ]

        self.csr_bus = csr_bus.Interface(data_width=16, address_width=8)
        self.wishbone = wishbone.Interface(data_width=16, adr_width=8)
        self.buses = wishbone2csr.WB2CSR(bus_wishbone=self.wishbone, bus_csr=self.csr_bus)

        self.output = CSRStorage(16)
        self.input = CSRStatus(16)
        for i in range(16):
            self.slot[0][i].o.eq(self.output.storage[i])
            self.input.status[i].eq(self.slot[0][i].i)
        self.csr_devices = ["output", "input"]

    # def do_finalize(self):
        print(self.get_csrs())
        # for name, obj in util.misc.xdir(self, True):
        #     print(name, obj)
        # self.submodules.csrbankarray = csr_bus.CSRBankArray(self, self.get_csr_registers, align_bits=0, data_width=16, address_width=8)
        # print(self.csrbankarray.submodules.rmap)
        # print(self.csrbankarray.banks)
        # self.submodules.csrcon = csr_bus.Interconnect(self.buses.csr, self.csrbankarray.get_buses())
        self.submodules.csrs = csr_bus.CSRBank(self.get_csrs(), address=0, bus=self.csr_bus, align_bits=4)
        # self.submodules.csrcon = csr_bus.Interconnect(self.buses.csr, [self.csrs])

        self.submodules.spi_slave = SR_WB(self.wishbone)

    def get_csr_registers(self, name, memory):
        try:
            print(self.csr_devices.index(name))
            return self.csr_devices.index(name)
        except ValueError:
            return None





class SilpaFPGA(Module):
    def __init__(self, platform):
        self.reset = Signal()
        self.specials += Instance("GSR", i_GSR=~ResetSignal() & self.reset, name="GSR_INST")
        self.specials += Instance("PUR", i_PUR=~ResetSignal(), name="PUR_INST")

        self.clock_domains.cd_sys = ClockDomain("sys")

        # self.logic = DiotLEC_Simple(address_reg_len=8, slots=8)
        self.logic = DiotLEC_WB(address_reg_len=8, slots=1)
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

    # test = DiotLEC_WB(slots=1)
    # platform.build(test, build_name="silpa_fpga", run=False)
