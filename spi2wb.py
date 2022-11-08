import os
from migen import *
from migen.genlib.cdc import PulseSynchronizer, MultiReg
from math import log2, ceil


class SPI2WB(Module):
    def __init__(self, platform, wb_bus, address_width=7, data_width=16):
        self.wb = wb_bus
        # 1 bit r/~w, 7 bit address, 16 bit data
        self.width = 1 + address_width + data_width

        self.sdi = Signal()
        self.sdo = Signal()
        self.sel = Signal()

        self.di = Signal(self.width)
        sr = Signal(self.width)
        sr_out = Signal(self.width)

        self.clock_domains.cd_le = ClockDomain("le", reset_less=True)
        self.specials += Instance("FD1P3BX",
                                  i_D=0, i_CK=ClockSignal("sck1"), i_SP=self.sel, i_PD=~self.sel,
                                  o_Q=self.cd_le.clk)

        self.counter1 = Signal(ceil(log2(self.width)))
        self.specials += Instance("counter",
                                  p_WIDTH=len(self.counter1),
                                  i_clk=ClockSignal("sck1"),
                                  i_reset=~self.sel | ResetSignal(),
                                  o_counter=self.counter1,
                                  i_en=self.sel
                                  )
        platform.add_source(os.path.join(os.path.abspath(os.path.dirname(__file__)), "counter.v"))

        read_sck = Signal()
        self.debug = Signal()
        read_wb = Signal()
        read_addr = Signal(address_width)
        read_data_sck = Signal(data_width)
        read_data_wb = Signal(data_width)
        read_data_valid_sck = Signal()
        read_data_valid_wb = Signal()
        read_data_valid_ack_sck = Signal()
        read_data_valid_ack_wb = Signal()
        read_data_done = Signal()

        ps = PulseSynchronizer(idomain="sck1", odomain="sys")
        self.submodules += ps
        self.comb += [ps.i.eq(read_sck), read_wb.eq(ps.o)]
        ps = PulseSynchronizer(idomain="sck1", odomain="sys")
        self.submodules += ps
        self.comb += [ps.i.eq(read_data_valid_ack_sck), read_data_valid_ack_wb.eq(ps.o)]
        self.specials += MultiReg(read_data_wb, read_data_sck, odomain="sck1")
        self.specials += MultiReg(read_data_valid_wb, read_data_valid_sck, odomain="sck1")

        self.sync.sck1 += [
            # TODO Also rewrite to FSM
            read_sck.eq(0),
            read_data_valid_ack_sck.eq(0),
            self.debug.eq(0),
            If(self.sel,
               If(self.counter1 == 0,
                  read_data_done.eq(0),
               ),
               If(self.counter1 == address_width + 1,
                  If(sr[7],  # TODO: hardcoded value
                     read_sck.eq(1),
                  ),
                  self.debug.eq(1),
                  read_addr.eq(sr[0:address_width])
               ),
               If(read_data_valid_sck & ~read_data_done,
                  read_data_valid_ack_sck.eq(1),
                  read_data_done.eq(1),
                  self.sdo.eq(read_data_sck[-1]),
                  sr_out[address_width + 2:].eq(read_data_sck[:-1])
               ).Else(
                  self.sdo.eq(sr_out[-1]),
                  sr[0].eq(self.sdi),
                  sr_out[0].eq(0),
                  sr[1:].eq(sr[:-1]),
                  sr_out[1:].eq(sr_out[:-1])
               )
            )
        ]

        self.sync.le += [
            self.di.eq(sr),
        ]

        fsm = FSM("WAIT_FOR_SPI_TRANSACTION_BEGIN")
        self.submodules += fsm

        # 0
        fsm.act("WAIT_FOR_SPI_TRANSACTION_BEGIN",
            If(self.sel,
               NextState("WAIT_FOR_SPI_TRANSACTION_READ_OR_END")
            ).Else(
                NextState("WAIT_FOR_SPI_TRANSACTION_BEGIN")
            )
        )
        # 1
        fsm.act("WAIT_FOR_SPI_TRANSACTION_READ_OR_END",
            If(read_wb & self.sel,
                NextState("READ")
            ).Elif(self.sel,
                NextState("WAIT_FOR_SPI_TRANSACTION_READ_OR_END")
            ).Else(
                NextState("WRITE")
            )
        )
        # 2
        fsm.act("READ",
            self.wb.adr.eq(read_addr),
            self.wb.we.eq(0),
            self.wb.stb.eq(1),
            self.wb.cyc.eq(1),
            NextState("WAIT_ACK_READ")
        )
        # 3
        fsm.act("WAIT_ACK_READ",
            self.wb.adr.eq(read_addr),
            self.wb.we.eq(0),
            self.wb.stb.eq(1),
            self.wb.cyc.eq(1),
            If(self.wb.ack,
               NextState("READ_DONE")
            ).Else(
               NextState("WAIT_ACK_READ")
            )
        )
        # 4
        fsm.act("READ_DONE",
            self.wb.cyc.eq(0),
            self.wb.stb.eq(0),
            self.wb.we.eq(0),
            read_data_wb.eq(self.wb.dat_r),
            read_data_valid_wb.eq(1),
            NextState("WAIT_ACK_READ_SCK")
        )
        # 5
        fsm.act("WAIT_ACK_READ_SCK",
            If(read_data_valid_ack_wb,
                read_data_valid_wb.eq(0),
                NextState("WAIT_FOR_SPI_TRANSACTION_END")
            ).Else(
                read_data_wb.eq(self.wb.dat_r),
                read_data_valid_wb.eq(1),
                NextState("WAIT_ACK_READ_SCK")
            )
        )
        fsm.act("WAIT_FOR_SPI_TRANSACTION_END",
            If(~self.sel,
                NextState("WAIT_FOR_SPI_TRANSACTION_BEGIN")
            ).Else(
                NextState("WAIT_FOR_SPI_TRANSACTION_END")
            )
        )
        # 7
        fsm.act("WRITE",
            self.wb.adr.eq(read_addr),
            self.wb.dat_w.eq(self.di[:data_width]),
            self.wb.sel.eq(2 ** len(self.wb.sel) - 1),
            self.wb.we.eq(1),
            self.wb.cyc.eq(1),
            self.wb.stb.eq(1),
            NextState("WAIT_ACK_WRITE")
        )
        # 8
        fsm.act("WAIT_ACK_WRITE",
            self.wb.adr.eq(read_addr),
            self.wb.dat_w.eq(self.di[:data_width]),
            self.wb.sel.eq(2 ** len(self.wb.sel) - 1),
            self.wb.we.eq(1),
            self.wb.cyc.eq(1),
            self.wb.stb.eq(1),
            If(self.wb.ack,
               NextState("WRITE_DONE")
            ).Else(
               NextState("WAIT_ACK_WRITE")
            )
        )
        # 9
        fsm.act("WRITE_DONE",
            self.wb.cyc.eq(0),
            self.wb.stb.eq(0),
            self.wb.we.eq(0),
            NextState("WAIT_FOR_SPI_TRANSACTION_BEGIN")
        )
