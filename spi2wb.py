from migen import *
from migen.genlib.cdc import PulseSynchronizer, MultiReg
from math import log2, ceil


class SPI2WB(Module):
    def __init__(self, wb_bus, address_width=7, data_width=16):
        self.wb = wb_bus
        # 1 bit r/~w, 7 bit address, 16 bit data
        self.width = 1 + address_width + data_width

        self.sdi = Signal()
        self.sdo = Signal()
        self.sel = Signal()

        self.di = Signal(self.width)
        sr = Signal(self.width)

        self.clock_domains.cd_le = ClockDomain("le", reset_less=True)
        self.specials += Instance("FD1P3BX",
                                  i_D=0, i_CK=ClockSignal("sck1"), i_SP=self.sel, i_PD=~self.sel,
                                  o_Q=self.cd_le.clk)
        self.clock_domains.cd_le_n = ClockDomain("le_n", reset_less=True)
        self.comb += [self.cd_le_n.clk.eq(~self.cd_le.clk)]

        self.counter1 = Signal(ceil(log2(self.width)))
        self.sync.sck1 += [
            If(self.sel,
               self.counter1.eq(self.counter1 + 1),
               )
        ]

        read_sck = Signal()
        read_wb = Signal()
        read_addr = Signal(address_width)
        read_data_sck = Signal(data_width)
        read_data_wb = Signal(data_width)
        read_data_valid_sck = Signal()
        read_data_valid_wb = Signal()
        read_data_valid_ack_sck = Signal()
        read_data_valid_ack_wb = Signal()
        read_data_done = Signal()
        spi_trans_done = Signal()

        ps = PulseSynchronizer(idomain="sck1", odomain="sys")
        self.submodules += ps
        self.comb += [ps.i.eq(read_sck), read_wb.eq(ps.o)]
        ps = PulseSynchronizer(idomain="sck1", odomain="sys")
        self.submodules += ps
        self.comb += [ps.i.eq(read_data_valid_ack_sck), read_data_valid_ack_wb.eq(ps.o)]
        self.specials += MultiReg(read_data_wb, read_data_sck, odomain="sck1")
        self.specials += MultiReg(read_data_valid_wb, read_data_valid_sck, odomain="sck1")

        self.sync.sck1 += [
            read_sck.eq(0),
            read_data_valid_ack_sck.eq(0),
            If(self.sel,
               If(self.counter1 == address_width + 1,
                  If(sr[7],
                     read_sck.eq(1),
                  ),
                  read_addr.eq(sr[0:address_width])
               ),
               If(read_data_valid_sck & ~read_data_done,
                  read_data_valid_ack_sck.eq(1),
                  read_data_done.eq(1),
                  self.sdo.eq(read_data_sck[-1]),
                  sr[address_width + 2:].eq(read_data_sck[:-1])
               ).Else(
                  self.sdo.eq(sr[-1]),
                  sr[0].eq(self.sdi),
                  sr[1:].eq(sr[:-1])
               )
            )
        ]

        self.sync.le += [
            self.di.eq(sr),
            If(~read_data_done,
               spi_trans_done.eq(1)
            ),
            read_data_done.eq(0),
            self.counter1.eq(0),
        ]

        self.sync.sys += [
            If(read_data_valid_ack_wb,
               read_data_valid_wb.eq(0),
            ),
            If(self.wb.ack,
               self.wb.cyc.eq(0),
               self.wb.stb.eq(0),
               self.wb.we.eq(0),
               If(~self.wb.we,
                  read_data_wb.eq(self.wb.dat_r),
                  read_data_valid_wb.eq(1)
               )
            ).Elif(read_wb,
               self.wb.adr.eq(read_addr),
               self.wb.we.eq(0),
               self.wb.stb.eq(1),
               self.wb.cyc.eq(1),
            ).Elif(spi_trans_done & ~read_data_done,
               self.wb.adr.eq(read_addr),
               self.wb.dat_w.eq(self.di[:data_width]),
               self.wb.sel.eq(2 ** len(self.wb.sel) - 1),
               self.wb.we.eq(1),
               self.wb.cyc.eq(1),
               self.wb.stb.eq(1),
               spi_trans_done.eq(0)
            )
        ]
