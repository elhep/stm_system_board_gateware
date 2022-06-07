`timescale 1ns / 100ps
//`include  "build/silpa_fpga.v"

module tb_diot_lec();
	
parameter SYS_PERIOD = 8;
parameter SPI_PERIOD = 12;
parameter DUMMY_CYCLES = 8;
parameter addr_w = 8;
parameter data_w = 16;
parameter spi_model_data_width = 16;
	
integer i;

reg                rst;
reg              spi_clk;
reg              spi_mosi;
wire              spi_miso;
reg              spi_cs;
wire spisdcard_clk, spisdcard_mosi, spisdcard_cs_n;
reg spisdcard_miso = 0;
reg [spi_model_data_width-1:0] spi_model = 0;

wire     [data_w-1:0]    output0;
wire     [data_w-1:0]    output1;
reg               sys_clk;

reg [addr_w-1:0] addr_read;
reg [data_w-1:0] data_read;

wire interrupt, led_g, led_b;

integer error=0;
integer data, data_old;

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
        .user_led_2(led_b),
	.spisdcard_clk(spisdcard_clk),
	.spisdcard_mosi(spisdcard_mosi),
	.spisdcard_cs_n(spisdcard_cs_n),
	.spisdcard_miso(spisdcard_miso)
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
		#20 spi_transaction(addr | 8'h80, 16'h0000, addr_read, data_read);
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

integer offset=6;
task automatic configure_spi_machine(input [2:0] slot);
	begin
		//length = 16 bit -1
		#20 spi_transaction(offset+1, spi_model_data_width-1, addr_read, data_read);
		//active chip selects
		#20 spi_transaction(offset+2, 1'b1, addr_read, data_read);
		//cs_polarity
		#20 spi_transaction(offset+3, 1'b0, addr_read, data_read);
		//clk dif
		#20 spi_transaction(offset+4, 8'h4, addr_read, data_read);
		//offline
		#20 spi_transaction(offset+5, 1'b0, addr_read, data_read);
		//clk polarity
		#20 spi_transaction(offset+6, 1'b0, addr_read, data_read);
		//clk phase
		//#20 spi_transaction(offset+7, 1'b0, addr_read, data_read);
		//lsb_first
		#20 spi_transaction(offset+8, 1'b0, addr_read, data_read);
		//half duplex
		#20 spi_transaction(offset+9, 1'b0, addr_read, data_read);
		//end
		#20 spi_transaction(offset+10, 1'b1, addr_read, data_read);
	end
endtask

task automatic spi_machine_write_and_read(input [spi_model_data_width-1:0] data);
	begin
  		#20 spi_transaction(offset+0, data, addr_read, data_read);
		  data_read = 0;
		  while (data_read != 1) begin
			//check idle
		  	#20 spi_transaction(offset+13 | 8'h80, 16'h00, addr_read, data_read);
		  end
		  if(spi_model != data) $error("SPI master write error");
		  #20 spi_transaction(offset+0 | 8'h80, data, addr_read, data_read);
		  if(data_read != data_old) $error("SPI readback error");
		  data_old = data;
	end
endtask



always @(posedge spisdcard_clk) begin
	spisdcard_miso <= spi_model[spi_model_data_width-1];
	spi_model[0] <= spisdcard_mosi;
	spi_model[spi_model_data_width-1:1] <= spi_model[spi_model_data_width-2:0];
end
always @(negedge spisdcard_clk) begin
	spisdcard_miso <= spi_model[spi_model_data_width-1];
end

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
  //#20 output0 = 16'h5555;
  //#20 spi_transaction(8'h00, 16'haaaa, addr_read, data_read);
  //#20 spi_transaction(8'h81, 16'h0000, addr_read, data_read);
  //#20 spi_transaction(8'h00, 16'h5555, addr_read, data_read);
  //#20 output0 = 16'haaaa;
  //#20 spi_transaction(8'h81, 16'h0000, addr_read, data_read);
  //#20 spi_transaction(8'h00, 16'hffff, addr_read, data_read);
  //sanity check for reads
  spi_write_and_check(8'h00, 16'haaaa);
  spi_write_and_check(6'h00, 16'h5555);
  spi_write_and_check(6'h00, 16'h0000);
  spi_write_and_check(6'h00, 16'h0001);
  spi_write_and_check(6'h00, 16'h8000);
  spi_write_and_check(6'h00, 16'hffff);
  spi_write_and_check(6'h00, 16'h2a2a);
  

  //set_direction(3'd0, 1); //output
  //set_output(3'd0, 16'haaaa);
  //set_direction(3'd0, 0); //input
  //#20 output0 = 16'h0000;
  //set_int_mask(3'd0, 16'hffff);
  //#20 output0 = 16'h0001;
  //clear_int(3'd0, 16'hffff);
  #20 configure_spi_machine(0);
  #100
  //read idle
  #20 spi_transaction(offset+13 | 8'h80, 16'h00, addr_read, data_read);
  if(data_read != 16'h01) $error("SPI idle = 0");
  //read writable
  #20 spi_transaction(offset+12 | 8'h80, 16'h00, addr_read, data_read);
  if(data_read != 16'h01) $error("SPI writable = 0");
  
  data = 16'haa55;
  #20 spi_transaction(offset+0, data, addr_read, data_read);
  data_read = 0;
  while (data_read != 1) begin
	//check idle
  	#20 spi_transaction(offset+13 | 8'h80, 16'h00, addr_read, data_read);
  end
  if(spi_model != data) $error("SPI master write error");
  data_old = data;

  spi_machine_write_and_read(16'h8000);
  spi_machine_write_and_read(16'h0001);
  spi_machine_write_and_read(16'h5555);
  spi_machine_write_and_read(16'haaaa);
  spi_machine_write_and_read(16'hffff);
  spi_machine_write_and_read(16'h0000);
  spi_machine_write_and_read(16'h0000);

  
  #40000 if(error==0)
    $display("Testbench timed out, no error."); // Timeout
  $finish;
end

endmodule