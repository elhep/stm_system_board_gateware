from litex_boards.platforms import gsd_orangecrab

if __name__ == "__main__":
    platform = gsd_orangecrab.Platform()
    platform.create_programmer().load_bitstream("./result/silpa_fpga.bit")