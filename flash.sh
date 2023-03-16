#!/bin/sh

#TODO move this to nix

openocd_root=$(dirname `which openocd`)

openocd --search $openocd_root/../share/openocd/scripts \
  --command "source ./stm_sys_board.cfg; \
            init; \
            flash probe 0; \
            flash write_image erase ./build/silpa_fpga.bit 0;
	          flash verify_bank 0 ./build/silpa_fpga.bit 0;
            exit;"
# flash erase_sector 0 0 last;
# svf quiet progress ./build/silpa_fpga.svf; \
