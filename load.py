import stm_sys_board

if __name__ == "__main__":
    platform = stm_sys_board.Platform()
    platform.create_programmer().load_bitstream("./build/silpa_fpga.svf")
    # platform.create_programmer().flash(0, "./build/silpa_fpga.bit")