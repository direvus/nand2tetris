// initialise RAM[2] to zero
@R2
M=0

// loop counter i = RAM[1]
@R1
D=M
@i
M=D

// while (i > 0):
//     RAM[2] = RAM[2] + RAM[0]
(LOOP)
@R0
D=M

@R2
M=D+M
@i
MD=M-1

@LOOP
D;JGT

(END)
@END
0;JMP
