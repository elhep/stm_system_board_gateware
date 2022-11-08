`timescale 1ns / 100ps

module tb_diot_lec();
	
parameter SYS_PERIOD = 8;
parameter SPI_PERIOD = 12;
//dummy cycles is dependent on sys_period and spi_period
parameter DUMMY_CYCLES = 8;
parameter addr_w = 8;
parameter data_w = 16;
parameter spi_model_data_width = 16;
//number of slots in the design
parameter slots_num = 1;
	
reg [30*8-1:0] textsignal;
integer i;
//registers before spi_register
integer offset_to_spi=slots_num*6+2;

reg                rst;
reg              spi_clk;
reg              spi_mosi;
wire              spi_miso;
reg              spi_cs;
reg [spi_model_data_width-1:0] spi_model = 0;

reg     [data_w-1:0]    output0_reg;
reg     output0_dir = 0;
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

task automatic set_output(input [2:0] slot, input [data_w-1:0] data);
	begin
		#20 spi_transaction(slot+slots_num*0, data, addr_read, data_read);
	end
endtask
task automatic check_output(input [2:0] slot, input [data_w-1:0] data);
	begin
		#20 set_output(slot, data);
		#50 if(output0 != data) $error("Output not correct! Expected 0x%0h, seen: 0x%0h.", data, output0);
	end
endtask

task automatic read_input(input [2:0] slot, output [data_w-1:0] data_read);
	begin
		#20 spi_transaction(slot+slots_num*1 | 8'h80, 16'h0000, addr_read, data_read);
	end
endtask
task automatic check_input(input [2:0] slot, input [data_w-1:0] data);
	begin
		output0_reg = data;
  		read_input(slot, data_read);
  		#50 if(data_read != output0_reg) $error("Output not correct! Expected 0x%0h, seen: 0x%0h.", output0_reg, data_read);
	end
endtask

task automatic set_direction(input [2:0] slot, input direction);
	begin
		#20 spi_transaction(slot+slots_num*2, 16'hffff*direction, addr_read, data_read);
	end
endtask

task automatic read_interrupt(input [2:0] slot, output [data_w-1:0] data_read);
	begin
		#20 spi_transaction(slot+slots_num*3 | 8'h80, 16'h0000, addr_read, data_read);
	end
endtask

task automatic set_int_mask(input [2:0] slot, input [data_w-1:0] data);
	begin
		#20 spi_transaction(slot+slots_num*4, data, addr_read, data_read);
	end
endtask

task automatic clear_int(input [2:0] slot, input [data_w-1:0] data);
	begin
		#20 spi_transaction(slot+slots_num*5, data, addr_read, data_read);
	end
endtask


task automatic configure_spi_machine(input [2:0] slot);
	begin
		//length = 16 bit -1
		#20 spi_transaction(offset_to_spi+1, spi_model_data_width-1, addr_read, data_read);
		//active chip selects
		#20 spi_transaction(offset_to_spi+2, 1'b1, addr_read, data_read);
		//cs_polarity
		#20 spi_transaction(offset_to_spi+3, 1'b0, addr_read, data_read);
		//clk dif
		#20 spi_transaction(offset_to_spi+4, 8'h4, addr_read, data_read);
		//offline
		#20 spi_transaction(offset_to_spi+5, 1'b0, addr_read, data_read);
		//clk polarity
		#20 spi_transaction(offset_to_spi+6, 1'b0, addr_read, data_read);
		//clk phase
		//#20 spi_transaction(offset_to_spi+7, 1'b0, addr_read, data_read);
		//lsb_first
		#20 spi_transaction(offset_to_spi+8, 1'b0, addr_read, data_read);
		//half duplex
		#20 spi_transaction(offset_to_spi+9, 1'b0, addr_read, data_read);
		//end
		#20 spi_transaction(offset_to_spi+10, 1'b1, addr_read, data_read);
	end
endtask

task automatic spi_machine_write_and_read(input [spi_model_data_width-1:0] data);
	begin
  		#20 spi_transaction(offset_to_spi+0, data, addr_read, data_read);
		  data_read = 0;
		  while (data_read != 1) begin
			//check idle
		  	#20 spi_transaction(offset_to_spi+13 | 8'h80, 16'h00, addr_read, data_read);
		  end
		  //if(spi_model != data) $error("SPI master write error");
		  #20 spi_transaction(offset_to_spi+0 | 8'h80, data, addr_read, data_read);
		  if(data_read != data_old) $error("SPI readback error");
		  data_old = data;
	end
endtask


//always @(posedge spisdcard_clk) begin
//	spisdcard_miso <= spi_model[spi_model_data_width-1];
//	spi_model[0] <= spisdcard_mosi;
//	spi_model[spi_model_data_width-1:1] <= spi_model[spi_model_data_width-2:0];
//end
//always @(negedge spisdcard_clk) begin
//	spisdcard_miso <= spi_model[spi_model_data_width-1];
//end
assign output0 = ~output0_dir ? output0_reg : 16'bzzzzzzzzzzzzzzzz;
// ---------------------------------------------------------------------------------------------------------------------
// RESET AND TIMEOUT
// ---------------------------------------------------------------------------------------------------------------------
initial begin
  sys_clk = 1'b1;
  rst = 1'b1;
  spi_clk = 1'b0;
  spi_mosi = 1'b0;
  spi_cs = 1'b1;
  output0_reg = 16'h0000;

  #50 rst = 1'b0;
  #7;
  //spi slave interface check
  textsignal = "SPI slave interface";
  spi_write_and_check(8'h00, 16'haaaa);
  spi_write_and_check(6'h00, 16'h5555);
  spi_write_and_check(6'h00, 16'h0000);
  spi_write_and_check(6'h00, 16'h0001);
  spi_write_and_check(6'h00, 16'h8000);
  spi_write_and_check(6'h00, 16'hffff);
  spi_write_and_check(6'h00, 16'h2a2a);
  
  //output check
  textsignal = "Output";
  #20 output0_reg = 16'haaaa;
  #20 output0_dir = 1;
  set_direction(3'd0, 1); //output

  check_output(3'd0, 16'h5555);
  check_output(3'd0, 16'haaaa);
  check_output(3'd0, 16'hffff);
  check_output(3'd0, 16'h0001);
  check_output(3'd0, 16'h0000);
  check_output(3'd0, 16'h8000);

  //input check
  textsignal = "Input";
  #20 output0_reg = 16'haaaa;
  set_direction(3'd0, 0); //input
  #20 output0_dir = 0;
  check_input(3'd0, 16'h5555);
  check_input(3'd0, 16'haaaa);
  check_input(3'd0, 16'hffff);
  check_input(3'd0, 16'h0001);
  check_input(3'd0, 16'h0000);
  check_input(3'd0, 16'h8000);

  //interrupt check
  textsignal = "Interrupt";
  output0_reg = 16'h0000;
  clear_int(3'd0, 16'hffff);
  set_int_mask(3'd0, 16'hffff);
  read_interrupt(3'd0, data_read);
  if(data_read != 16'h00) $error("Interrupts not cleared!");
  output0_reg = 16'h0001;
  read_interrupt(3'd0, data_read);
  if(data_read != 16'h01) $error("Interrupt not registered!");
  if(~interrupt) $error("Interrupt to STM is low!");
  clear_int(3'd0, 16'hffff);
  read_interrupt(3'd0, data_read);
  if(data_read != 16'h00) $error("Interrupts not cleared!");
  
  #20 output0_reg = 16'h0001;
  clear_int(3'd0, 16'hffff);

  //SPI master interface check
  textsignal = "SPI master interface";
  #20 output0_dir = 1;
  #20 configure_spi_machine(0);
  #100
  //read idle
  #20 spi_transaction(offset_to_spi+13 | 8'h80, 16'h00, addr_read, data_read);
  if(data_read != 16'h01) $error("SPI idle = 0");
  //read writable
  #20 spi_transaction(offset_to_spi+12 | 8'h80, 16'h00, addr_read, data_read);
  if(data_read != 16'h01) $error("SPI writable = 0");
  
  data = 16'haa55;
  #20 spi_transaction(offset_to_spi+0, data, addr_read, data_read);
  data_read = 0;
  while (data_read != 1) begin
	//check idle
  	#20 spi_transaction(offset_to_spi+13 | 8'h80, 16'h00, addr_read, data_read);
  end
  //if(spi_model != data) $error("SPI master write error");
  data_old = data;

  spi_machine_write_and_read(16'h8000);
  spi_machine_write_and_read(16'h0001);
  spi_machine_write_and_read(16'h5555);
  spi_machine_write_and_read(16'haaaa);
  spi_machine_write_and_read(16'hffff);
  spi_machine_write_and_read(16'h0000);
  spi_machine_write_and_read(16'h0000);
  #200
  #20 spi_transaction(offset_to_spi+0, 16'haaaa , addr_read, data_read);

  #3000 spi_transaction(offset_to_spi+0, 16'h55aa , addr_read, data_read);

  
  #40000 if(error==0)
    $display("Testbench timed out, no error."); // Timeout
  $finish;
end

endmodule