`timescale 1ns / 100ps

module tb_stm_system_board();

parameter SYS_PERIOD = 10;
parameter SPI_PERIOD = 10;
//dummy cycles is dependent on sys_period and spi_period
parameter DUMMY_CYCLES = 10;
parameter addr_w = 7;
parameter data_w = 16;
parameter spi_model_data_width = 16;
//number of slots in the design
parameter slots_num = 2;

reg [30*8-1:0] textsignal;
integer i;
//registers before spi_register
integer offset_to_spi=slots_num*6;

reg                rst;
reg              spi_clk;
reg              spi_mosi;
wire              spi_miso;
reg              spi_cs;
reg [spi_model_data_width-1:0] spi_model = 0;

reg     [7:0]    slot1_reg;
reg     slot1_dir = 0;
wire     [7:0]    slot1;
wire     [7:0]    slot5;
wire [3:0] dio, dio_oen;
reg               sys_clk;

reg [data_w-1:0] data_read;

wire interrupt;

integer error=0;
integer data, data_old;

stm_sys_board uut (
    .clk100           (   sys_clk),
    .qspix10_clk (spi_clk),
	.qspix10_mosi (spi_mosi),
	.qspix10_miso (spi_miso),
	.qspix10_cs_n (spi_cs),
	.slot1_d0_p (slot1[0]),
	.slot1_d1_p (slot1[1]),
	.slot1_d2_p (slot1[2]),
	.slot1_d3_p (slot1[3]),
	.slot1_d4_p (slot1[4]),
	.slot1_d5_p (slot1[5]),
	.slot1_d6_p (slot1[6]),
	.slot1_d7_p (slot1[7]),
	.slot5_d0_p (slot5[0]),
	.slot5_d1_p (slot5[1]),
	.slot5_d2_p (slot5[2]),
	.slot5_d3_p (slot5[3]),
	.slot5_d4_p (slot5[4]),
	.slot5_d5_p (slot5[5]),
	.slot5_d6_p (slot5[6]),
	.slot5_d7_p (slot5[7]),
	.dio (dio),
	.dio_oen (dio_oen)
	//.slot1(output1)
);

always #(SYS_PERIOD/2) sys_clk = ~sys_clk;


task automatic spi_transaction (input read, input [addr_w-1:0] addr, input [data_w-1:0] data, output [data_w-1:0] data_readback);
	begin
		spi_cs = 1'b0;
		// r / ~w
		spi_mosi = read;
		#(SPI_PERIOD/2);
		spi_clk = 1'b1;
		#(SPI_PERIOD/2);
		spi_clk = 1'b0;
		// address
		for (i = 0; i <= addr_w-1; i = i + 1) begin
			spi_mosi = addr[addr_w-i-1];
			#(SPI_PERIOD/2);
			spi_clk = 1'b1;
			#(SPI_PERIOD/2);
			spi_clk = 1'b0;
		end
		// dummy cycles
		for (i = 0; i < DUMMY_CYCLES; i = i + 1) begin
			#(SPI_PERIOD/2);
			spi_clk = 1'b1;
			#(SPI_PERIOD/2);
			spi_clk = 1'b0;
		end
		// data
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

task automatic spi_write(input [addr_w-1:0] addr, input [data_w-1:0] data);
	begin
		#20 spi_transaction(0, addr, data, data_read);
	end
endtask

task automatic spi_read(input [addr_w-1:0] addr, input [data_w-1:0] data, output [data_w-1:0] data_read);
	begin
		#20 spi_transaction(1, addr, data, data_read);
	end
endtask

task automatic spi_write_and_check(input [addr_w-1:0] addr, input [data_w-1:0] data);
	begin
		spi_write(addr, data);
		spi_read(addr, 16'h0000, data_read);
		if(data_read != data) $error("Invalid data read back, expected 0x%0h, seen: 0x%0h.", data, data_read);
	end
endtask

task automatic set_output(input [2:0] slot, input [data_w-1:0] data);
	begin
		spi_write(slot+slots_num*0, data);
	end
endtask
task automatic check_output(input [2:0] slot, input [data_w-1:0] data);
	begin
		#20 set_output(slot, data);
		#50 if(slot1 != data) $error("Output not correct! Expected 0x%0h, seen: 0x%0h.", data, slot1);
	end
endtask

task automatic read_input(input [2:0] slot, output [data_w-1:0] data_read);
	begin
		spi_read(slot+slots_num*1, 16'h0000, data_read);
	end
endtask
task automatic check_input(input [2:0] slot, input [data_w-1:0] data);
	begin
		slot1_reg = data;
  		read_input(slot, data_read);
  		#50 if(data_read != slot1_reg) $error("Output not correct! Expected 0x%0h, seen: 0x%0h.", slot1_reg, data_read);
	end
endtask

task automatic set_direction(input [2:0] slot, input direction);
	begin
		spi_write(slot+slots_num*2, 16'hffff*direction);
	end
endtask

task automatic read_interrupt(input [2:0] slot, output [data_w-1:0] data_read);
	begin
		spi_read(slot+slots_num*3, 16'h0000, data_read);
	end
endtask

task automatic set_int_mask(input [2:0] slot, input [data_w-1:0] data);
	begin
		spi_write(slot+slots_num*4, data);
	end
endtask

task automatic clear_int(input [2:0] slot, input [data_w-1:0] data);
	begin
		spi_write(slot+slots_num*5, data);
	end
endtask


task automatic configure_spi_machine(input [2:0] slot);
	begin
		offset_to_spi = (slot+1)*6;
		//length = 16 bit -1
		spi_write(offset_to_spi+1, spi_model_data_width-1);
		//active chip selects
		spi_write(offset_to_spi+2, 1'b1);
		//cs_polarity
		spi_write(offset_to_spi+3, 1'b0);
		//clk dif
		spi_write(offset_to_spi+4, 8'h4);
		//offline
		spi_write(offset_to_spi+5, 1'b0);
		//clk polarity
		spi_write(offset_to_spi+6, 1'b0);
		//clk phase
		//spi_write(offset_to_spi+7, 1'b0);
		//lsb_first
		spi_write(offset_to_spi+8, 1'b0);
		//half duplex
		spi_write(offset_to_spi+9, 1'b0);
		//end
		spi_write(offset_to_spi+10, 1'b1);
	end
endtask

task automatic spi_machine_write_and_read(input [spi_model_data_width-1:0] data);
	begin
  		spi_write(offset_to_spi+0, data);
		  data_read = 0;
		  while (data_read != 1) begin
			//check idle
		  	spi_read(offset_to_spi+13, 16'h00, data_read);
		  end
		  //if(spi_model != data) $error("SPI master write error");
		  spi_read(offset_to_spi+0, data, data_read);
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

//assign slot1 = ~slot1_dir ? slot1_reg : 16'bzzzzzzzzzzzzzzzz;

// ---------------------------------------------------------------------------------------------------------------------
// RESET AND TIMEOUT
// ---------------------------------------------------------------------------------------------------------------------
initial begin
  sys_clk = 1'b1;
  rst = 1'b1;
  spi_clk = 1'b0;
  spi_mosi = 1'b0;
  spi_cs = 1'b1;
  slot1_reg = 8'h00;

  #50 rst = 1'b0;
  #7;
  //spi slave interface check
  textsignal = "SPI slave interface";
  spi_write_and_check(8'h00, 16'haaaa);

  //#100 spi_write(offset_to_spi+0, 16'haaaa );

  spi_write_and_check(6'h00, 16'h5555);
  spi_write_and_check(6'h00, 16'h0000);
  spi_write_and_check(6'h00, 16'h0001);
  spi_write_and_check(6'h00, 16'h8000);
  spi_write_and_check(6'h00, 16'hffff);
  spi_write_and_check(6'h00, 16'h2a2a);

  //output check
  //textsignal = "Output";
  //#20 slot1_reg = 8'haa;
  //#20 slot1_dir = 1;
  //set_direction(3'd0, 1); //output

  //check_output(3'd0, 16'h5555);
  //check_output(3'd0, 16'haaaa);
  //check_output(3'd0, 16'hffff);
  //check_output(3'd0, 16'h0001);
  //check_output(3'd0, 16'h0000);
  //check_output(3'd0, 16'h8000);

  //input check
  //textsignal = "Input";
  //#20 slot1_reg = 8'haa;
  //set_direction(3'd0, 0); //input
  //#20 slot1_dir = 0;
  //check_input(3'd0, 16'h5555);
  //check_input(3'd0, 16'haaaa);
  //check_input(3'd0, 16'hffff);
  //check_input(3'd0, 16'h0001);
  //check_input(3'd0, 16'h0000);
  //check_input(3'd0, 16'h8000);

  //interrupt check
  //textsignal = "Interrupt";
  //slot1_reg = 8'h00;
  //clear_int(3'd0, 16'hffff);
  //set_int_mask(3'd0, 16'hffff);
  //read_interrupt(3'd0, data_read);
  //if(data_read != 16'h00) $error("Interrupts not cleared!");
  //slot1_reg = 8'h01;
  //read_interrupt(3'd0, data_read);
  //if(data_read != 16'h01) $error("Interrupt not registered!");
  //if(~interrupt) $error("Interrupt to STM is low!");
  //clear_int(3'd0, 16'hffff);
  //read_interrupt(3'd0, data_read);
  //if(data_read != 16'h00) $error("Interrupts not cleared!");

  //#20 slot1_reg = 8'h01;
  //clear_int(3'd0, 16'hffff);

  //SPI master interface check
  //textsignal = "SPI master interface";
  #20 slot1_dir = 1;
  #20 configure_spi_machine(0);
  #100
  //read idle
  spi_read(offset_to_spi+13, 16'h00, data_read);
  if(data_read != 16'h01) $error("SPI idle = 0");
  //read writable
  spi_read(offset_to_spi+12, 16'h00, data_read);
  if(data_read != 16'h01) $error("SPI writable = 0");

  data = 16'haa55;
  spi_write(offset_to_spi+0, data);
  data_read = 0;
  while (data_read != 1) begin
	//check idle
  	spi_read(offset_to_spi+13, 16'h00, data_read);
  end
  //if(spi_model != data) $error("SPI master write error");
  data_old = data;

  //spi_machine_write_and_read(16'h8000);
  //spi_machine_write_and_read(16'h0001);
  //spi_machine_write_and_read(16'h5555);
  //spi_machine_write_and_read(16'haaaa);
  //spi_machine_write_and_read(16'hffff);
  //spi_machine_write_and_read(16'h0000);
  //spi_machine_write_and_read(16'h0000);
  #200
  spi_write(offset_to_spi+0, 16'haaaa );

  #3000 spi_write(offset_to_spi+0, 16'h55aa);

  #20 spi_write(offset_to_spi+0, 16'haaaa);

  
  #40000 if(error==0)
    $display("Testbench timed out, no error."); // Timeout
  $finish;
end

endmodule