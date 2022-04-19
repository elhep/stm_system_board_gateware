`timescale 1ns / 100ps

module tb_diot_lec();
	
parameter SYS_PERIOD = 12;
parameter SPI_PERIOD = 12;
parameter addr_w = 6;
parameter data_w = 16;
	
integer i;

reg                rst;
reg              spi_clk;
reg              spi_mosi;
wire              spi_miso;
reg              spi_cs;

wire     [data_w-1:0]    output0;
wire     [data_w-1:0]    output1;
reg               sys_clk;

reg [addr_w-1:0] addr_read;
reg [data_w-1:0] data_read;

integer error=0;

top uut (
    .sys_clk           (   sys_clk),
    .sys_rst           (    rst           ),
    .spi_clk (spi_clk),
	.mosi (spi_mosi),
	.miso (spi_miso),
	.cs (spi_cs),
	.output0(output0),
	.output1(output1)
);

always #(SYS_PERIOD/2) sys_clk = ~sys_clk;


task automatic spi_transaction (input [addr_w-1:0] addr, input [data_w-1:0] data, output [addr_w-1:0] addr_readback, output [data_w-1:0] data_readback);
	begin
		spi_cs = 1'b1;
		for (i = 0; i <= addr_w-1; i = i + 1) begin
			spi_mosi = addr[addr_w-i-1];
			#(SPI_PERIOD/2);
			spi_clk = 1'b1;
			#(SPI_PERIOD/2);
			spi_clk = 1'b0;
			addr_readback[addr_w-i-1] = spi_miso;
		end
		for (i = 0; i <= data_w-1; i = i + 1) begin
			spi_mosi = data[data_w-i-1];
			#(SPI_PERIOD/2);
			spi_clk = 1'b1;
			#(SPI_PERIOD/2);
			spi_clk = 1'b0;
			data_readback[data_w-i-1] = spi_miso;
		end		
		#(SPI_PERIOD/2);
		spi_cs = 1'b0;
		spi_mosi = 1'b0;
	end
endtask

task automatic spi_write_and_check(input [addr_w-1:0] addr, input [data_w-1:0] data);
	begin
		#20 spi_transaction(addr, data, addr_read, data_read);
		#20 spi_transaction(addr, 16'h0000, addr_read, data_read);
		if(addr_read != addr) begin
			$error("Invalid address read back, expected 0x%0h, seen: 0x%0h.", addr, addr_read);
			error = 1;
		end
		if(data_read != data) $error("Invalid data read back, expected 0x%0h, seen: 0x%0h.", data, data_read);
	end
endtask


// ---------------------------------------------------------------------------------------------------------------------
// RESET AND TIMEOUT
// ---------------------------------------------------------------------------------------------------------------------
initial begin
  //$dumpfile("test.vcd");
  //$dumpvars(0,tb_XS7_LTC2216_14);
  //$dumpvars(0,uut);

  sys_clk = 1'b1;
  rst = 1'b1;
  spi_clk = 1'b0;
  spi_mosi = 1'b0;
  spi_cs = 1'b0;

  #50 rst = 1'b0;
  
  spi_write_and_check(6'h01, 16'haaaa);
  spi_write_and_check(6'h05, 16'h5555);
  spi_write_and_check(6'h00, 16'h2a2a);
  spi_write_and_check(6'h01, 16'hffff);
  spi_write_and_check(6'h07, 16'h0000);
  
  #40000 if(error==0)
    $display("Testbench timed out, no error."); // Timeout
  $finish;
end

endmodule