#!/bin/sh

#TODO move this to nix

openocd_root=$(dirname `which openocd`)
openocd --search $openocd_root/../share/openocd/scripts \
  --command "source ./stm_sys_board.cfg; init; \
            svf progress ./build/silpa_fpga.svf; \
            exit;"
   #pld load 0 ./build/silpa_fpga.bit"