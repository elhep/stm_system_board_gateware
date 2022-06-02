`timescale 1ns / 100ps
//`include  "build/silpa_fpga.v"

module tb_diot_lec();
	
parameter SYS_PERIOD = 4;
parameter SPI_PERIOD = 12;
parameter DUMMY_CYCLES = 6;
parameter addr_w = 8;
parameter data_w = 16;
	
integer i;

reg                rst;
reg              spi_clk;
reg              spi_mosi;
wire              spi_miso;
reg              spi_cs;

reg     [data_w-1:0]    output0;
wire     [data_w-1:0]    output1;
reg               sys_clk;

reg [addr_w-1:0] addr_read;
reg [data_w-1:0] data_read;

wire interrupt, led_g, led_b;

integer error=0;

silpa_fpga uut (
    .clk480           (   sys_clk),
    //.sys_rst           (    rst           ),
    .spi0_clk (spi_clk),
	.spi0_mosi (spi_mosi),
	.spi0_miso (spi_miso),
	.spi0_cs_n (spi_cs),
	.slot(output0),
	.user_led(interrupt),
        .user_led_1(led_g),
        .user_led_2(led_b)
	//.slot1(output1)
);

always #(SYS_PERIOD/2) sys_clk = ~sys_clk;


task automatic spi_transaction (input [addr_w-1:0] addr, input [data_w-1:0] data, output [addr_w-1:0] addr_readback, output [data_w-1:0] data_readback);
	begin
		spi_cs = 1'b0;
		for (i = 0; i <= addr_w-1; i = i + 1) begin
			spi_mosi = addr[addr_w-i-1];
			#(SPI_PERIOD/2);
			spi_clk = 1'b1;
			#(SPI_PERIOD/2);
			spi_clk = 1'b0;
			addr_readback[addr_w-i-1] = spi_miso;
		end
		for (i = 0; i < DUMMY_CYCLES; i = i + 1) begin
			#(SPI_PERIOD/2);
			spi_clk = 1'b1;
			#(SPI_PERIOD/2);
			spi_clk = 1'b0;
		end
		for (i = 0; i <= data_w-1; i = i + 1) begin
			spi_mosi = data[data_w-i-1];
			#(SPI_PERIOD/2);
			spi_clk = 1'b1;
			#(SPI_PERIOD/2);
			spi_clk = 1'b0;
			data_readback[data_w-i-1] = spi_miso;
		end		
		//for (i = 0; i < 0; i = i + 1) begin
		//	#(SPI_PERIOD/2);
		//	spi_clk = 1'b1;
		//	#(SPI_PERIOD/2);
		//	spi_clk = 1'b0;
		//end
		#(SPI_PERIOD/2);
		spi_cs = 1'b1;
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

task automatic set_direction(input [2:0] slot, input direction);
	begin
		#20 spi_transaction(slot+16, 16'hffff*direction, addr_read, data_read);
	end
endtask

task automatic set_output(input [2:0] slot, input [data_w-1:0] data);
	begin
		#20 spi_transaction(slot, data, addr_read, data_read);
	end
endtask

task automatic read_input(input [2:0] slot, input [data_w-1:0] data, output [data_w-1:0] data_read);
	begin
		#20 spi_transaction(slot+8, 16'h0000, addr_read, data_read);
	end
endtask

task automatic set_int_mask(input [2:0] slot, input [data_w-1:0] data);
	begin
		#20 spi_transaction(slot+32, data, addr_read, data_read);
	end
endtask

task automatic clear_int(input [2:0] slot, input [data_w-1:0] data);
	begin
		#20 spi_transaction(slot+40, data, addr_read, data_read);
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
  spi_cs = 1'b1;
  //output0 = 16'bzzzzzzzzzzzzzzzz;

  #50 rst = 1'b0;
  #7;
  //#20 spi_transaction(8'h00, 16'hffff, addr_read, data_read);
  //#20 spi_transaction(8'h02, 16'hffff, addr_read, data_read);
  //#20 spi_transaction(8'h00, 16'h0000, addr_read, data_read);
  //#20 spi_transaction(8'h02, 16'h0000, addr_read, data_read);
  //#20 spi_transaction(8'h02, 16'hffff, addr_read, data_read);
  #20 output0 = 16'h5555;
  //#20 spi_transaction(8'h00, 16'haaaa, addr_read, data_read);
  #20 spi_transaction(8'h81, 16'h0000, addr_read, data_read);
  #20 output0 = 16'haaaa;
  #20 spi_transaction(8'h81, 16'h0000, addr_read, data_read);
  //#20 spi_transaction(8'h00, 16'hffff, addr_read, data_read);
  //spi_write_and_check(8'h01, 16'haaaa);
  //spi_write_and_check(6'h05, 16'h5555);
  //spi_write_and_check(6'h00, 16'h2a2a);
  //spi_write_and_check(6'h01, 16'hffff);
  //spi_write_and_check(6'h07, 16'h0000);

  //set_direction(3'd0, 1); //output
  //set_output(3'd0, 16'haaaa);
  //set_direction(3'd0, 0); //input
  //#20 output0 = 16'h0000;
  //set_int_mask(3'd0, 16'hffff);
  //#20 output0 = 16'h0001;
  //clear_int(3'd0, 16'hffff);
  
  
  #40000 if(error==0)
    $display("Testbench timed out, no error."); // Timeout
  $finish;
end

endmodule