from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform
from litex.build.dfu import DFUProg

_io = [
    ("clk100", 0, Pins("A24"), IOStandard("LVCMOS33")),
    ("clk_stm", 0, Pins("C25"), IOStandard("LVCMOS33")),

    ("dio", 0, Pins("AD25 AF25 AE25 AE26"), IOStandard("LVCMOS33")),
    ("dio_oen", 0, Pins("AD26 AB26 AC26 AA26"), IOStandard("LVCMOS33")),

    ("qspix4", 0,
        Subsignal("clk", Pins("AA25")),
        Subsignal("data", Pins("AA23 AA24 AB24 AB25")),
        Subsignal("cs_n", Pins("AA22")),
        IOStandard("LVCMOS33")
    ),
    ("qspix1", 0,
        Subsignal("clk", Pins("AA25")),
        Subsignal("mosi", Pins("AA23")),
        Subsignal("miso", Pins("AA24")),
        Subsignal("cs_n", Pins("AA22")),
        IOStandard("LVCMOS33")
    ),

    ("qspi_cfg", 0,
        Subsignal("clk", Pins("AE3")),
        Subsignal("data", Pins("AE2 AD2 AF2 AE1")),
        Subsignal("cs_n", Pins("AA2")),
        IOStandard("LVCMOS33")
    ),

    ("spi_dir_ctrl", 0,
        Subsignal("mosi", Pins("AB3")),
        Subsignal("miso", Pins("AD3")),
        Subsignal("clk", Pins("C23")),
        Subsignal("cs", Pins("C24")),
        IOStandard("LVCMOS33")
    ),
    ("fsen", 0, Pins("A25"), IOStandard("LVCMOS33")),

    ("spi_slave", 1,
        Subsignal("mosi", Pins("E24")),
        Subsignal("miso", Pins("D26")),
        Subsignal("clk", Pins("F25")),
        Subsignal("cs", Pins("B26")),
        IOStandard("LVCMOS33")
    ),
    ("spi_slave", 2,
        Subsignal("mosi", Pins("E23")),
        Subsignal("miso", Pins("F24")),
        Subsignal("clk", Pins("F22")),
        Subsignal("cs", Pins("F26")),
        IOStandard("LVCMOS33")
    ),
    ("spi_slave", 3,
         Subsignal("mosi", Pins("H22")),
         Subsignal("miso", Pins("H21")),
         Subsignal("clk", Pins("J21")),
         Subsignal("cs", Pins("F23")),
         IOStandard("LVCMOS33")
     ),
    ("spi_slave", 4,
         Subsignal("mosi", Pins("H23")),
         Subsignal("miso", Pins("L22")),
         Subsignal("clk", Pins("K22")),
         Subsignal("cs", Pins("K21")),
         IOStandard("LVCMOS33")
     ),
    ("spi_slave", 5,
         Subsignal("mosi", Pins("M21")),
         Subsignal("miso", Pins("C26")),
         Subsignal("clk", Pins("M23")),
         Subsignal("cs", Pins("J23")),
         IOStandard("LVCMOS33")
     ),
    ("spi_slave", 6,
         Subsignal("mosi", Pins("L23")),
         Subsignal("miso", Pins("N21")),
         Subsignal("clk", Pins("N22")),
         Subsignal("cs", Pins("K23")),
         IOStandard("LVCMOS33")
     ),

    ("slot_mlvds", 1, Pins("B19 E16 C16 A18 B21 C17 A19 B17"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 2, Pins("D19 A22 C19 C18 C21 E19 A21 D17"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 5, Pins("C14 E17 E13 D13 B13 D14 C13 D18"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 6, Pins("A5 A3 A2 C6 A4 B4 D5 C5"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 7, Pins("B8 C8 E6 B6 A9 A8 D6 A6"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 8, Pins("A16 D16 A15 A14 A17 B16 B14 E14"), IOStandard("LVCMOS33")),
]

_connectors_bp = [
    ("slot1", {
        "d0_p": "W22",
        # "d0_n": "W21",
        "d1_p": "U21",
        # "d1_n": "U23",
        "d2_p": "N24",
        # "d2_n": "M24",
        "d3_p": "R21",
        # "d3_n": "T23",
        "d4_p": "W25",
        # "d4_n": "W24",
        "d5_p": "K24",
        # "d5_n": "L24",
        "d6_p": "P21",
        # "d6_n": "N23",
        "d7_p": "V26",
        # "d7_n": "U25",
    }
    ),
    ("slot2", {
        "d0_p": "H3",
        # "d0_n": "J3",
        "d1_p": "K26",
        # "d1_n": "L26",
        "d2_p": "V24",
        # "d2_n": "W26",
        "d3_p": "D23",
        # "d3_n": "D24",
        "d4_p": "U1",
        # "d4_n": "T1",
        "d5_p": "V23",
        # "d5_n": "U22",
        "d6_p": "R24",
        # "d6_n": "P24",
        "d7_p": "R23",
        # "d7_n": "T22",
    }
    ),
    ("slot3", {
        "d0_p": "P23",
        # "d0_n": "P22",
        "d1_p": "J6",
        # "d1_n": "K6",
        "d2_p": "P25",
        # "d2_n": "P26",
        "d3_p": "A10",
        # "d3_n": "A11",
        "d4_p": "A12",
        # "d4_n": "A13",
        "d5_p": "N1",
        # "d5_n": "N2",
        "d6_p": "T3",
        # "d6_n": "U3",
        "d7_p": "V3",
        # "d7_n": "W1",
        "d8_p": "E8",
        # "d8_n": "D8",
        "d9_p": "D9",
        # "d9_n": "C9",
        "d10_p": "E10",
        # "d10_n": "D10",
        "d11_p": "C10",
        # "d11_n": "B10",
        "d12_p": "K2",
        # "d12_n": "J1",
        "d13_p": "C11",
        # "d13_n": "B11",
        "d14_p": "E11",
        # "d14_n": "D11",
        "d15_p": "T25",
        # "d15_n": "R26",
    }
    ),
    ("slot4", {
        "d0_p": "L2",
        # "d0_n": "M1",
        "d1_p": "H25",
        # "d1_n": "H26",
        "d2_p": "D2",
        # "d2_n": "E1",
        "d3_p": "C22",
        # "d3_n": "D22",
        "d4_p": "K3",
        # "d4_n": "L3",
        "d5_p": "H2",
        # "d5_n": "H1",
        "d6_p": "W4",
        # "d6_n": "V6",
        "d7_p": "P2",
        # "d7_n": "P1",
        "d8_p": "D4",
        # "d8_n": "D3",
        "d9_p": "H5",
        # "d9_n": "H6",
        "d10_p": "K4",
        # "d10_n": "L4",
        "d11_p": "N3",
        # "d11_n": "M3",
        "d12_p": "K25",
        # "d12_n": "J26",
        "d13_p": "C2",
        # "d13_n": "C1",
        "d14_p": "E4",
        # "d14_n": "F3",
        "d15_p": "U26",
        # "d15_n": "T26",
    }
     ),
    ("slot5", {
        "d0_p": "L25",
        # "d0_n": "M26",
        "d1_p": "K5",
        # "d1_n": "J4",
        "d2_p": "W23",
        # "d2_n": "V21",
        "d3_p": "F2",
        # "d3_n": "F1",
        "d4_p": "B1",
        # "d4_n": "B3",
        "d5_p": "P4",
        # "d5_n": "P5",
        "d6_p": "R6",
        # "d6_n": "T4",
        "d7_p": "V1",
        # "d7_n": "U2",
    }
    ),
    ("slot6", {
        "d0_p": "C4",
        # "d0_n": "C3",
        "d1_p": "D25",
        # "d1_n": "E26",
        "d2_p": "N26",
        # "d2_n": "N25",
        "d3_p": "D21",
        # "d3_n": "E21",
        "d4_p": "R3",
        # "d4_n": "P3",
        "d5_p": "U6",
        # "d5_n": "U4",
        "d6_p": "W5",
        # "d6_n": "W6",
        "d7_p": "W2",
        # "d7_n": "W3",
    }
     ),
    ("slot7", {
        "d0_p": "H24",
        # "d0_n": "J24",
        "d1_p": "T2",
        # "d1_n": "R1",
        "d2_p": "T24",
        # "d2_n": "U24",
        "d3_p": "N6",
        # "d3_n": "N5",
        "d4_p": "M6",
        # "d4_n": "M4",
        "d5_p": "R4",
        # "d5_n": "T5",
        "d6_p": "AB2",
        # "d6_n": "AC2",
        "d7_p": "V4",
        # "d7_n": "U5",
    }
     ),
    ("slot8", {
        "d0_p": "E3",
        # "d0_n": "D1",
        "d1_p": "B23",
        # "d1_n": "A23",
        "d2_p": "F5",
        # "d2_n": "F4",
        "d3_p": "H4",
        # "d3_n": "L5",
        "d4_p": "P6",
        # "d4_n": "N4",
        "d5_p": "AA1",
        # "d5_n": "AB1",
        "d6_p": "K1",
        # "d6_n": "L1",
        "d7_p": "AC1",
        # "d7_n": "AD1",
    }
     ),
]
# due to bugs in PCB, 3.3 V signals cannot be used at all
# signals with external termination must use LVDS if input and LVDS25E if output, inout is not possible
# name, i/o voltage, external termination
_connector_constraints = [
    ("slot1", [2.5]*8,
        [True]*7 + [False]*1),
    ("slot2", [2.5]*3 + [3.3] + [2.5]*4,
        [False, True] + [False]*2 + [True, False]*2),
    ("slot3", [2.5]*3 + [3.3]*2 + [2.5]*3 + [3.3]*4 + [2.5] + [3.3]*2 + [2.5],
        [False]*15 + [True]),
    ("slot4", [2.5]*3 + [3.3] + [2.5]*12,
        [False, True] + [False]*2 + [True]*2 + [False]*3 + [True, False, True] + [False]*2 + [True]*2),
    ("slot5", [2.5]*8,
        [False]*4 + [True, False]*2),
    ("slot6", [2.5, 3.3]*2 + [2.5]*4,
        [True] + [False]*3 + [True]*4),
    ("slot7", [2.5]*6 + [3.3, 2.5],
        [False, True]*2 + [True] + [False]*3),
    ("slot8", [2.5, 3.3] + [2.5]*3 + [3.3, 2.5, 3.3],
        [True] + [False]*2 + [True]*2 + [False, True, False])
]
constraints_dict = {slot[0]: [(slot[1][i], slot[2][i]) for i in range(len(slot[1]))] for slot in _connector_constraints}

def print_compatibility_table():
    print("| Signal\\Slot |", end="")
    for i in range(1, 9):
        print("\t{} |".format(i), end="")
    print("")
    for i in range(9):
        print(" | -----".format(i), end="")
    print(" |")
    for i in range(16):
        print("| {}\t |".format(i), end="")
        for j in range(1, 9):
            if j not in [3, 4] and i > 7:
                print("\t |", end="")
                continue
            signal = constraints_dict["slot{}".format(j)][i]
            if signal[0] == 3.3:
                print("\t❌️ |", end="")
            elif signal[1]:
                print("\t☑️ |", end="")
            else:
                print("\t✅️ |", end="")
        print("")

class Platform(LatticePlatform):
    default_clk_name   = "clk100"
    default_clk_period = 10

    def __init__(self, toolchain="trellis", **kwargs):
        LatticePlatform.__init__(self, "LFE5U-85F-6BG554C", _io, _connectors_bp, toolchain=toolchain, **kwargs)
        banks = [0, 1, 2, 3, 4, 6, 7, 8]
        voltages = [3.3, 3.3, 3.3, 2.5, 3.3, 2.5, 2.5, 3.3]
        for i, v in zip(banks, voltages):
            self.add_platform_command("BANK {} VCCIO {};".format(i, v))
        self.add_platform_command("VOLTAGE 1.1V;")
        self.add_platform_command("SYSCONFIG COMPRESS_CONFIG=ON;")
        self.add_platform_command("SYSCONFIG CONFIG_IOVOLTAGE=3.3;")
        self.add_platform_command("SYSCONFIG SLAVE_SPI_PORT=DISABLE;")
        self.add_platform_command("SYSCONFIG MASTER_SPI_PORT=ENABLE;")
        self.add_platform_command("SYSCONFIG SLAVE_PARALLEL_PORT=DISABLE;")
        self.add_platform_command("SYSCONFIG MCCLK_FREQ=9.7;")

    def do_finalize(self, fragment):
        LatticePlatform.do_finalize(self, fragment)

