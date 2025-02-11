// Store the initial screen offset into `i`
@SCREEN
D=A
@i
M=D

// Set the loop counter to 8K
@8192
D=A
@c
M=D

(LOOP)
// Set the draw value to 0 initially.
@d
M=0

// Read the scan code from the keyboard.
@KBD
D=M

// If the scan code is non-zero, set the draw value to -1.
@ZERO
D;JEQ

@d
M=-1

(ZERO)

// Render the draw value to the screen.
@d
D=M
@i
A=M
M=D

// Advance the screen index and decrement the loop counter
D=A+1
@i
M=D
@c
MD=M-1

// If the loop counter is < 0, start over from the first line.
@0
D;JLT

// Otherwise, continue iterating.
@LOOP
0;JMP
