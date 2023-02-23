module counter
(
	clk,
	reset,
	counter,
	en
);
    parameter WIDTH = 8;
	input clk;
	input reset;
	input en;
	output reg [WIDTH-1:0] counter;

	always @(posedge clk or posedge reset)
	begin
	    if (reset) begin
			counter = 0;
		end	else if (en) begin
			counter = counter + 1;
		end
	end
endmodule		
