from litex.build.generic_platform import *
from litex.build.lattice import LatticePlatform
from litex.build.lattice.programmer import OpenOCDJTAGProgrammer

_io = [
    ("clk100", 0, Pins("A24"), IOStandard("LVCMOS33")),
    ("clk_stm", 0, Pins("A2"), IOStandard("LVCMOS33")),

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
        Subsignal("clk", Pins("C16")),
        Subsignal("cs", Pins("A15")),
        IOStandard("LVCMOS33")
    ),
    ("fsen", 0, Pins("A25"), IOStandard("LVCMOS33")),

    ("spi_slave", 1,
        Subsignal("mosi", Pins("E17")),
        Subsignal("miso", Pins("E16")),
        Subsignal("clk", Pins("D14")),
        Subsignal("cs", Pins("E13")),
        IOStandard("LVCMOS33")
    ),
    ("spi_slave", 2,
        Subsignal("mosi", Pins("D9")),
        Subsignal("miso", Pins("E10")),
        Subsignal("clk", Pins("E14")),
        Subsignal("cs", Pins("AB1")),
        IOStandard("LVCMOS33")
    ),
    ("spi_slave", 3,
         Subsignal("mosi", Pins("E8")),
         Subsignal("miso", Pins("D11")),
         Subsignal("clk", Pins("D13")),
         Subsignal("cs", Pins("D8")),
         IOStandard("LVCMOS33")
     ),
    ("spi_slave", 4,
         Subsignal("mosi", Pins("AD1")),
         Subsignal("miso", Pins("AC2")),
         Subsignal("clk", Pins("D10")),
         Subsignal("cs", Pins("E19")),
         IOStandard("LVCMOS33")
     ),
    ("spi_slave", 5,
         Subsignal("mosi", Pins("AB2")),
         Subsignal("miso", Pins("AA1")),
         Subsignal("clk", Pins("D21")),
         Subsignal("cs", Pins("AC1")),
         IOStandard("LVCMOS33")
     ),
    ("spi_slave", 6,
         Subsignal("mosi", Pins("D16")),
         Subsignal("miso", Pins("D18")),
         Subsignal("clk", Pins("D19")),
         Subsignal("cs", Pins("E11")),
         IOStandard("LVCMOS33")
     ),

    ("slot_mlvds", 1, Pins("C18 C17 B23 A18 E21 D22 C22 C21"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 2, Pins("B17 A21 C19 B19 A23 B21 A19 A22"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 3, Pins("A17 B16 A16 A14 C14 B14 A13 A6"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 4, Pins("B13 A12 A11 B11 A10 C13 D6 C11"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 5, Pins("B10 B8 A9 B6 A8 A5 C6 B4"), IOStandard("LVCMOS33")),
    ("slot_mlvds", 6, Pins("C10 E6 C5 A4 D5 A3 C9 C8"), IOStandard("LVCMOS33")),
]

_connectors_bp = [
    ("slot1", {
        "d0_p": "W22",
        # "d0_n": "W21",
        "d1_p": "W25",
        # "d1_n": "",
        "d2_p": "W23",
        # "d2_n": "",
        "d3_p": "U21",
        # "d3_n": "",
        "d4_p": "V24",
        # "d4_n": "",
        "d5_p": "V26",
        # "d5_n": "",
        "d6_p": "V23",
        # "d6_n": "",
        "d7_p": "T24",
        # "d7_n": "",
    }
    ),
    ("slot2", {
        "d0_p": "R21",
        # "d0_n": "",
        "d1_p": "K26",
        # "d1_n": "",
        "d2_p": "K23",
        # "d2_n": "",
        "d3_p": "C23",
        # "d3_n": "",
        "d4_p": "D23",
        # "d4_n": "",
        "d5_p": "P23",
        # "d5_n": "",
        "d6_p": "R23",
        # "d6_n": "",
        "d7_p": "P25",
        # "d7_n": "",
    }
    ),
    ("slot3", {
        "d0_p": "R24",
        # "d0_n": "",
        "d1_p": "H25",
        # "d1_n": "",
        "d2_p": "K22",
        # "d2_n": "",
        "d3_p": "H5",
        # "d3_n": "",
        "d4_p": "F25",
        # "d4_n": "",
        "d5_p": "J6",
        # "d5_n": "",
        "d6_p": "C2",
        # "d6_n": "",
        "d7_p": "K5",
        # "d7_n": "",
    }
    ),
    ("slot4", {
        "d0_p": "P21",
        # "d0_n": "",
        "d1_p": "E24",
        # "d1_n": "",
        "d2_p": "H24",
        # "d2_n": "",
        "d3_p": "E4",
        # "d3_n": "",
        "d4_p": "F22",
        # "d4_n": "",
        "d5_p": "K4",
        # "d5_n": "",
        "d6_p": "D2",
        # "d6_n": "",
        "d7_p": "F2",
        # "d7_n": "",
    }
     ),
    ("slot5", {
        "d0_p": "H22",
        # "d0_n": "",
        "d1_p": "M21",
        # "d1_n": "",
        "d2_p": "N26",
        # "d2_n": "",
        "d3_p": "C4",
        # "d3_n": "",
        "d4_p": "D25",
        # "d4_n": "",
        "d5_p": "H3",
        # "d5_n": "",
        "d6_p": "P4",
        # "d6_n": "",
        "d7_p": "R4",
        # "d7_n": "",
    }
    ),
    ("slot6", {
        "d0_p": "K24",
        # "d0_n": "",
        "d1_p": "N21",
        # "d1_n": "",
        "d2_p": "K25",
        # "d2_n": "",
        "d3_p": "E3",
        # "d3_n": "",
        "d4_p": "C25",
        # "d4_n": "",
        "d5_p": "K2",
        # "d5_n": "",
        "d6_p": "L2",
        # "d6_n": "",
        "d7_p": "T3",
        # "d7_n": "",
    }
     ),
    ("slot7", {
        "d0_p": "H23",
        # "d0_n": "",
        "d1_p": "B26",
        # "d1_n": "",
        "d2_p": "J21",
        # "d2_n": "",
        "d3_p": "H4",
        # "d3_n": "",
        "d4_p": "D4",
        # "d4_n": "",
        "d5_p": "P2",
        # "d5_n": "",
        "d6_p": "V4",
        # "d6_n": "",
        "d7_p": "W4",
        # "d7_n": "",
        "d8_p": "H2",
        # "d8_n": "",
        "d9_p": "K1",
        # "d9_n": "",
        "d10_p": "M6",
        # "d10_n": "",
        "d11_p": "N6",
        # "d11_n": "",
        "d12_p": "P6",
        # "d12_n": "",
        "d13_p": "R6",
        # "d13_n": "",
        "d14_p": "R3",
        # "d14_n": "",
        "d15_p": "U26",
        # "d15_n": "",
    }
     ),
    ("slot8", {
        "d0_p": "E23",
        # "d0_n": "",
        "d1_p": "N24",
        # "d1_n": "",
        "d2_p": "L25",
        # "d2_n": "",
        "d3_p": "B1",
        # "d3_n": "",
        "d4_p": "F5",
        # "d4_n": "",
        "d5_p": "V1",
        # "d5_n": "",
        "d6_p": "N1",
        # "d6_n": "",
        "d7_p": "V3",
        # "d7_n": "",
        "d8_p": "T2",
        # "d8_n": "",
        "d9_p": "N3",
        # "d9_n": "",
        "d10_p": "K3",
        # "d10_n": "",
        "d11_p": "U6",
        # "d11_n": "",
        "d12_p": "U1",
        # "d12_n": "",
        "d13_p": "W2",
        # "d13_n": "",
        "d14_p": "W5",
        # "d14_n": "",
        "d15_p": "T25",
        # "d15_n": "",
    }
     ),
]
# due to bugs in PCB, 3.3 V signals cannot be used at all
# signals with external termination must use LVDS if input and LVDS25E if output, inout is not possible
# name, i/o voltage, external termination
_connector_constraints = [
    ("slot1", [2.5]*8,
        [True]*2 + [False, True] + [False]*4),
    ("slot2", [2.5]*8,
        [True]*2 + [False, True] + [False]*4),
    ("slot3", [2.5]*8,
        [True]*2 + [False, True] + [False]*4),
    ("slot4", [2.5]*8,
        [True]*2 + [False, True] + [False]*4),
    ("slot5", [2.5]*8,
        [True]*2 + [False, True] + [False]*4),
    ("slot6", [2.5]*8,
        [True]*2 + [False, True] + [False]*4),
    ("slot7", [2.5]*16,
        [True]*2 + [False, True] + [False]*4 + [True]*8),
    ("slot8", [2.5]*16,
        [True]*2 + [False, True] + [False]*4 + [True]*8)
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
        voltages = [3.3, 3.3, 2.5, 2.5, 3.3, 2.5, 2.5, 3.3]
        for i, v in zip(banks, voltages):
            self.add_platform_command("BANK {} VCCIO {};".format(i, v))
        self.add_platform_command("VOLTAGE 1.1V;")
        self.add_platform_command("SYSCONFIG COMPRESS_CONFIG=ON CONFIG_IOVOLTAGE=3.3 SLAVE_SPI_PORT=DISABLE MASTER_SPI_PORT=ENABLE SLAVE_PARALLEL_PORT=DISABLE MCCLK_FREQ=9.7;")

    def create_programmer(self):
        return OpenOCDJTAGProgrammer(config="stm_sys_board.cfg", flash_proxy_basename="bscan_spi_lfe5u85f_custom.svf")

    def do_finalize(self, fragment):
        LatticePlatform.do_finalize(self, fragment)
