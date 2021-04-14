#!/bin/python
from scipy.io import wavfile
import scipy.io
import numpy as np
from rich import print
import pretty_errors

# input.wav is 24bit signed pcm, input16 is signed 16 bit, input8 is unsigned 8bit
input_wav = 'input.wav'
input_data = 'input.txt'
# must be 1, 2, 4, or 8
# [TODO] only 2 works for now, will need to make others work
num_bits = 2
output_wav = 'Secret' + input_wav

assert (num_bits == 1 or num_bits == 2 or num_bits == 4 or num_bits == 8),"num_bits must be 2, 4, or 8"

# Get the wave file data
samplerate, wav = wavfile.read(input_wav)
np.set_printoptions(formatter={'int':hex})
print(f"sample rate      = {samplerate}")
print(f"raw data (left)  = {wav[:, 0]}")
print(f"raw data (right) = {wav[:, 1]}")

# Get the 'secret' input data
data = np.fromfile(input_data,dtype=np.int8,count=-1)
data = np.array(data)
print(f"secret data      = {data}")
# Make an empty np array, 'secret' the same size and type as the wav array,
# and fill it with 0's
secret = np.zeros_like(wav)
# Take num_bits at a time from data putting it into a free location in secret
# so, need to >> by num bits
# This will need a try catch to yell at the user if the input file is too big
# [TODO]
i = 0
for byte in data:
    for b in range(0,int(8/num_bits)):
        byte = byte >> num_bits
        # print(bin(byte&0b11))
        # TODO mabe & reflective of num_bits
        secret[i,0] = byte & 0b11
        i += 1

print(f"Secret bit array  = {secret[:, 0]}")

print(f"""\nlooking at a single sample and the way we're reading in the
data, threre might be extra 0's depending on the sample bit depth.
.wav files are commonly 8, 16, or 24 bit ints or 32bit float.
We'll avoid floats, so of the int types both 24's are stored
as int32's in numpy. 
For this file, samples are {type(wav[0,0])} internally\n""")

if type(wav[0,0]) is np.int32:
    print("32bit internally, LSB's are off by a byte, secret will be shifted")
    # First, we need to make room for the bits we're going to write, making them 0 in the
    # wav file. To do this, first a mask is made, then it's ANDed with the wav
    mask = np.empty_like(wav)
    mask.fill(0xffffffff)
    mask = np.left_shift(mask,num_bits+8)
    wav = np.bitwise_and(wav,mask)
    print("doing XOR of secret into file")
    wav = np.bitwise_xor(wav,(secret<<8))
else:
    print(f"{type(wav[0,0])} internally, LSB is correct:")
    print("doing XOR of secret into file")
    mask = np.empty_like(wav)
    mask.fill(0xffffffff)
    mask = np.left_shift(mask,num_bits)
    wav = np.bitwise_and(wav,mask)
    wav = np.bitwise_xor(wav,secret)

# Now we need to 0-out the bits we want to access.

print(f"Secret has now been XOR'd into the {num_bits} least significant bits")
print(f"raw data w/ secret (left)  = {wav[:, 0]}")
print(f"raw data w/ secret (right) = {wav[:, 1]}")
print(f"Writing the new .wav file to {output_wav}")

# [TODO] write data

print("You can now go listen to the file to see how audible the distortion is")

# [TODO] need to setup recovery from the output_wav file
# This will probably require that all of the above be set to a command line argument switch
# to set like -e for encode and -d for decode

recovered_bits = np.zeros_like(wav)

if type(wav[0,0]) is np.int32:
    print("32bit internally, LSB's are off by a byte, recovery will need to be shifted")
    # First, we need to make a mask, then bitwise and out the bits we care about
    mask = np.empty_like(wav)
    mask.fill(0xffffffff)
    mask = np.left_shift(mask,num_bits+8)
    mask = np.invert(mask)
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
# [TODO]
# we wouldn't know this normally, so later, to show a 'real'
# decoder, we'll need to modify this so that the number of used bits
# is always in the the last few bytes of the wav file, need to store the
# num_bits too
recovered_bits = recovered_bits[:int((len(data)*(8/num_bits)))]

recovered_bytes = np.zeros_like(recovered_bits)


# Yes, I know the following block of code is absolutely disgusting.

i = 0
k = 0
for false_byte in recovered_bits:
    # the bytes in recovered bits only contain a few bits, there's a bunch of 0's padding them.
    # this is where those sets of num_bits get turned back into bytes
    j = i%(8/num_bits)
    recovered_bytes[k,0] += int(false_byte[0]) << int(j*num_bits)
    # If this mess doesn't make sense, uncomment this line and the print in the if below
    print(f"false byte = {np.binary_repr(false_byte[0],width=2)} → recovered byte = {np.binary_repr(recovered_bytes[k,0],width=8)}")
    i+=1
    if j == 8/num_bits - 1:
        print("-----")
        k+=1
        i=0

print(f"recovered bytes (left)  = {recovered_bytes[:, 0]}")
print(f"recovered bytes (right) = {recovered_bytes[:, 1]}")
print(f"recovered chars (left)  = {recovered_bytes[:, 0].tobytes().decode('ascii')}")
print(f"recovered chars (right)  = {recovered_bytes[:, 1].tobytes().decode('ascii')}")