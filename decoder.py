#!/bin/python
from scipy.io import wavfile
import scipy.io
import numpy as np
from rich import print
#import pretty_errors

input_wav = 'output24-8.wav'

# Get the wave file data
samplerate, wav = wavfile.read(input_wav)
np.set_printoptions(formatter={'int':hex})
print(f"sample rate      = {samplerate}")
print(f"raw data (left)  = {wav[:, 0]}")
print(f"raw data (right) = {wav[:, 1]}")

# get num_bits from the end of the wav file
num_bits = 0
# decrement from end end of file
for i in range(wav.shape[0]-1, 0, -1):
    if type(wav[0,0]) is np.int32:
        if (wav[i,0] & 0x00000100) > 0:
            num_bits += 1
        else:
            break
    else:
        if (wav[i,0] & 1) > 0:
            num_bits += 1
        else:
            break


print(f"num_bits = {num_bits} determined by reading binary at end of file")
print("\n")


recovered_bits = np.zeros_like(wav)

if type(wav[0,0]) is np.int32:
    print("32bit internally, LSB's are off by a byte, recovery will need to be shifted")
    # First, we need to make a mask, then bitwise and out the bits we care about
    mask = np.empty_like(wav)
    mask.fill(0xffffffff)
    mask = np.left_shift(mask,num_bits+8) # +8 because of the 32 to 24 bit problem, if numbits 2 then 0x
    mask = np.invert(mask)                # make 
    recovered_bits = np.bitwise_and(wav,mask)
    # [TODO] making this 6 bits right helps
    recovered_bits = np.right_shift(recovered_bits,8)
    recovered_bits = recovered_bits.astype(np.int8)
else:
    print(f"{type(wav[0,0])} internally, LSB is correct, getting bits out")
    mask = np.empty_like(wav)
    mask.fill(0xffffffff)
    mask = np.left_shift(mask,num_bits)
    mask = np.invert(mask)
    recovered_bits = np.bitwise_and(wav,mask)
    recovered_bits = recovered_bits.astype(np.int8)

# a = 0x61 is 0b00111101 so 0b00 0b11 0b11 0b01 should be 0x0 0x3 0x3 0x1
# [TODO] I seem to be dropping the last two bits? But I don't think the mask is wrong?

print(f"recovered bits (left)   = {recovered_bits[:, 0]}")
print(f"recovered bits (right)  = {recovered_bits[:, 1]}")

# trim to only the bits we care about
# TODO we don't know the length of the data intresically, so just like how num_bit is
# store on the end of the file in the encoder, then recovered here in the decoder, we
# need to do the same for the length of the data. for now, just providing a big enough
# value to here works, but there's technically overflow.
recovered_bits = recovered_bits[:300]

recovered_bytes = np.zeros_like(recovered_bits)


# Yes, I know the following block of code is absolutely disgusting.

i = 0
k = 0
for false_byte in recovered_bits:
    # the bytes in recovered bits only contain a few bits, there's a bunch of 0's padding them.
    # this is where those sets of num_bits get turned back into bytes
    j = i%(8/num_bits)
    recovered_bytes[k,0] += int(false_byte[0]) << int(j*num_bits) #falsebyte[0] because only the left channel
    # If this mess doesn't make sense, uncomment this line and the print in the if below
    # print(f"false byte = {np.binary_repr(false_byte[0],width=2)} → recovered byte = {np.binary_repr(recovered_bytes[k,0],width=8)}")
    i+=1
    # if numbits is 2 we want j = 0,1,2,3
    if j == 8/num_bits - 1:
        # print("-----")
        k+=1
        i=0

# TODO, once we know that data size, we should also only print that much recovered of the text's hex- ref encoder.
print(f"recovered bytes (left)  = {recovered_bytes[:, 0]}")
print(f"recovered bytes (right) = {recovered_bytes[:, 1]}")
print(f"recovered chars (left)  = {recovered_bytes[:, 0].tobytes().decode('ascii')}")
print(f"recovered chars (right)  = {recovered_bytes[:, 1].tobytes().decode('ascii')}")