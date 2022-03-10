#!/bin/python
from scipy.io import wavfile
import numpy as np
import numpy.ma as ma
from rich import print
import soundfile as sf
import arrayfire as af

def get_wav_data(input_wav):
    samplerate, wav = wavfile.read(input_wav)
    return samplerate, wav

def get_secret_data(input_data):
    data = np.fromfile(input_data,dtype=np.int8,count=-1)
    data = np.array(data)
    return data

def secret_data_to_bit_array(data,num_bits,wav_to_clone):
    # Make an empty np array, 'secret' the same size and type as the wav array,
    # and fill it with 0's
    secret = np.zeros_like(wav_to_clone)
    max_bit = 2**num_bits - 1
    i = 0

    for i in range(0,data.shape[0]*(8//num_bits)):
        if i%(8//num_bits) == 0:
            byte = data[(i//(8//num_bits))]
        secret[i,0] = byte & max_bit
        byte = byte >> num_bits

    return secret

def secret_data_to_bit_array_af(data,num_bits,wav_to_clone):
    # afData = af.interop.to_array(wav_to_clone, copy=True)
    # Make an empty np array, 'secret' the same size and type as the wav array,
    # and fill it with 0's
    secret = np.zeros_like(wav_to_clone)
    anded = af.logical_and(secret,0xffffffff,out=secret)
    multed = af.multiply(anded,0xffffffff,out=anded)
    max_bit = 2**num_bits - 1
    i = 0

    for i in range(0,data.shape[0]*(8//num_bits)):
        if i%(8//num_bits) == 0:
            byte = data[(i//(8//num_bits))]
        secret[i,0] = byte & max_bit
        byte = byte >> num_bits

    return secret


def secret_data_to_wav(num_bits,wav_to_clone,secret):
    mask = np.empty_like(wav_to_clone)
    mask.fill(0xffffffff)
    mask = np.left_shift(mask,num_bits)
    wav = np.bitwise_and(wav_to_clone,mask)
    wav = np.bitwise_xor(wav,secret)
    return wav

def bit_indicator_to_wav(num_bits,wav):
    # set the lsb of the file read backwards to contain as many 1's as num_bits
    # followed by a 0 This let's us know the num-bits for decode.
    if type(wav[0,0]) is np.int32:
        or_val = 1<<8
    else:
        or_val = 1
    for i in range(wav.shape[0]-1, wav.shape[0]-(2+num_bits), -1):
        wav[i,0] = wav[i,0] | or_val
        if i==wav.shape[0]-(1+num_bits):
            wav[i,0] = wav[i,0] & ~or_val

    return wav

def write_wave(wav,samplerate):
    if type(wav[0,0]) is np.int32:
        sf.write("output24-2.wav", wav, samplerate, 'PCM_24')
    elif type(wav[0,0]) is np.int16:
        sf.write("output16-2.wav", wav, samplerate, 'PCM_16')
    elif type(wav[0,0]) is np.uint8:
        wavfile.write("output8-1.wav", samplerate, wav)
    else:
        print("Output file unable to be written ... something about datatypes probably")

def get_num_bits(wav):
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

    print("\n")
    return num_bits

def recover_bits(wav,num_bits):
    recovered_bits = np.zeros_like(wav)

    # if type(wav[0,0]) is np.int32:
    #     # First, we need to make a mask, then bitwise and out the bits we care about
    #     mask = np.empty_like(wav)
    #     mask.fill(0xffffffff)
    #     mask = np.left_shift(mask,num_bits+8) # +8 because of the 32 to 24 bit problem, if numbits 2 then 0x
    #     mask = np.invert(mask)                # make 
    #     recovered_bits = np.bitwise_and(wav,mask)
    #     # [TODO] making this 6 bits right helps
    #     recovered_bits = np.right_shift(recovered_bits,8)
    #     recovered_bits = recovered_bits.astype(np.int8)
    # else:
    mask = np.empty_like(wav)
    mask.fill(0xffffffff)
    mask = np.left_shift(mask,num_bits)
    mask = np.invert(mask)
    recovered_bits = np.bitwise_and(wav,mask)
    recovered_bits = recovered_bits.astype(np.int8)
    return recovered_bits

def recover_bytes(recovered_bits,num_bits):
    recovered_bits = recovered_bits[:10000]
    # The following is way to big, but that's fine
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
    return recovered_bytes

#--------------------------------------------------------------------------------

input_wav = 'lemons24.wav'
input_data = 'input.txt'
num_bits = 2

assert (num_bits == 1 or num_bits == 2 or num_bits == 4 or num_bits == 8),"num_bits must be 1, 2, 4, or 8"

samplerate, wav = get_wav_data(input_wav)
print(f"sample rate      = {samplerate}")
print(f"raw data (left)  = {wav[:, 0]}")
print(f"raw data (right) = {wav[:, 1]}")

secret = get_secret_data(input_data)
print(f"secret data      = {secret}")

secret_bit_array = secret_data_to_bit_array(secret,num_bits,wav)

secret_wav = secret_data_to_wav(num_bits,wav,secret_bit_array)
print(f"Secret has now been XOR'd into the {num_bits} least significant bits")
print(f"raw data w/ secret (left)  = {wav[:, 0]}")
print(f"raw data w/ secret (right) = {wav[:, 1]}")

secret_wav = bit_indicator_to_wav(num_bits,secret_wav)
print("Added bit indicator to end of file")

write_wave(secret_wav,samplerate)
print("Wave file written... Decoding")
print("-----------------------------------------------------")

new_num_bits = get_num_bits(secret_wav)
print(f"num_bits = {new_num_bits} determined by reading binary at end of file")


if type(wav[0,0]) is np.int32:
    print("32bit internally, LSB's are off by a byte, recovery will need to be shifted")
else:
    print(f"{type(wav[0,0])} internally, LSB is correct, getting bits out")
recovered_bits = recover_bits(secret_wav,new_num_bits)
print(f"recovered bits (left)   = {recovered_bits[:, 0]}")
print(f"recovered bits (right)  = {recovered_bits[:, 1]}")


recovered_bytes = recover_bytes(recovered_bits,new_num_bits)
print(f"recovered bytes (left)  = {recovered_bytes[:, 0]}")
print(f"recovered bytes (right) = {recovered_bytes[:, 1]}")
print(f"recovered chars (left)  = {recovered_bytes[:, 0].tobytes().decode('ascii')}")
print(f"recovered chars (right)  = {recovered_bytes[:, 1].tobytes().decode('ascii')}")



