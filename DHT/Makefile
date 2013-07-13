CC = gcc
CFLAGS =  -std=c99 -I. -lbcm2835
DEPS = 
OBJ = DHT.o

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

DHT: $(OBJ)
	gcc -o $@ $^ $(CFLAGS)
