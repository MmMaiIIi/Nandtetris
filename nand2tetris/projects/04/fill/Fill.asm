// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

// 32 * 256 of 16 bit of pixel

// 8192

@8192
D = A
@n
M = D // n = 8192

@16384
D = A 
@addr
M = D // addr = 16384

(LOOP) 
	@KBD
	D = M
	@BLACK // kbd > 0, pressed
	D; JGT
	@WHITE
	0; JMP

	(BLACK)
		@i 
		M = 0 // i = 0
		(BLOOP)
			@i
			D = M
			@n
			D = D - M
			@LOOP
			D; JEQ

			@i
			D = M
			@addr
			A = M + D
			M = -1
			
			@i
			M = M + 1

			@BLOOP
			0; JMP
	
	(WHITE)
		@i 
		M = 0 // i = 0
		(WLOOP)
			@i
			D = M
			@n
			D = D - M
			@LOOP
			D; JEQ

			@i
			D = M
			@addr
			A = M + D
			M = 0
			
			@i
			M = M + 1

			@WLOOP
			0; JMP