### Build

- Install [Nix package manager](https://nixos.org/download.html)
- [Enable flakes](https://nixos.wiki/wiki/Flakes)
- `nix build` to build project in sandbox (bitstream and svf will be in "output" folder)
- `nix develop` and `python stm_sys_board_hdl.py ` to build project in nix environment (outputs will be in "build" folder)

### Flash

- Build the project
- Enter nix environment: `nix develop`
- `python load.py` to temporarily load bitstream
- `./flash.sh` to write bitstream to flash memory

### Register map

| Address   | Name                                                         | R/W  |
| --------- | ------------------------------------------------------------ | ---- |
| 0x00      | Slot 1 output                                                | RW   |
| 0x01      | Slot 1 input                                                 | R    |
| 0x02      | Slot 1 output enable                                         | RW   |
| 0x03      | Slot 1 interrupt                                             | R    |
| 0x04      | Slot 1 interrupt mask                                        | RW   |
| 0x05      | Slot 1 interrupt clear                                       | W    |
| 0x06-0x13 | Slot 1 SPI controller (see [documentation](https://github.com/m-labs/misoc/blob/master/misoc/cores/spi2.py#L476)) |      |
| 0x06      | Slot 1 SPI data                                              | RW   |
| 0x07      | Slot 1 SPI data length                                       | RW   |
| 0x08      | Slot 1 SPI cs                                                | RW   |
| 0x09      | Slot 1 SPI cs polarity                                       | RW   |
| 0x0a      | Slot 1 SPI clock divider                                     | RW   |
| 0x0b      | Slot 1 SPI offline                                           | RW   |
| 0x0c      | Slot 1 SPI clock polarity                                    | RW   |
| 0x0d      | Slot 1 SPI Clock phase                                       | RW   |
| 0x0e      | Slot 1 SPI LSB first                                         | RW   |
| 0x0f      | Slot 1 SPI half duplex                                       | RW   |
| 0x10      | Slot 1 SPI end transaction                                   | RW   |
| 0x11      | Slot 1 SPI Readable                                          | R    |
| 0x12      | Slot 1 SPI writable                                          | R    |
| 0x13      | Slot 1 SPI idle                                              | R    |
| 0x14-0x27 | Slot 5 (same as Slot 1)                                      |      |
| 0x28      | ID1 = 0xaaaa                                                 | R    |
| 0x29      | ID2 = 0x5555                                                 | R    |

### Measured SPI delays

- 5 MHz SPI CLK -> 4 dummy cycles
- 10 MHz SPI CLK -> 4 dummy cycles
- 25 MHz SPI CLK -> 5 dummy cycles
- 50 MHz SPI CLK -> 7 dummy cycles
- 100 MHz SPI CLK -> 11 dummy cycles
- 133 MHz SPI CLK (max STM speed) -> 11 dummy cycles
