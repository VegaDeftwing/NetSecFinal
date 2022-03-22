def shiftmap (x: []i64) (y: []i64) : []i64 = map2 (>>) x y

--def shiftbits [n] (data: [n]i64) : [n]i64 = let bits = map (\x -> 2 * x % 8) (0..<n) in map2 (>>) data bits
def shiftbits [n] (data: [n]i64) (shift: i64) : [n]i64 = let bits = map (\x -> shift * x % 8) (0..<n) in map2 (>>) data bits

-- Get the top two bits of each byte in x
--def gettop (data: []i64) : []i64 = map (&3) data
def gettop (data: []i64) (num: i64) : []i64 = map (&((2**num)-1)) data


-- replicate each element in the arary four times, stolen from https://futhark-book.readthedocs.io/en/latest/language.html#size-types
-- [1,2,3] -> [1,1,1,1,2,2,2,2,3,3,3,3]
def rep4 [n] (data: [n]i64): []i64 = map (\i -> data[i/4]) (0..<n*4)

-- rep4 is used to to expand the secret data input array,
-- by four elements, so, [1,2] -> [1,1,1,1,2,2,2,2]
-- then shiftbits is used to shift the bits of each similar group
-- for example [a,b,c,d]=[97,98,99,100]->[97,97,97,97,98,98,98,98,99,99,99,99,100,100,100,100]
-- -> [...,98,98,98,98,...] = [..,0x62,0x62,0x62,0x62,...] -> >>r2 [...,0x62,0x18,0x6,0x1,...]
-- Then, applying gettop to each group, we get the top two bits of each byte
-- -> [...,0x62,0x18,0x6,0x1,...] & 0x3 -> [...,0x2,0x0,0x2,0x1,...]
-- ---------
-- 97  = 0x61 = 01 10 00 01 = (flipped) 1 0 2 1
-- 98  = 0x62 = 01 10 00 10 = (flipped) 2 0 2 1
-- 99  = 0x63 = 01 10 00 11 = (flipped) 3 0 2 1
-- 100 = 0x64 = 01 10 01 00 = (flipped) 0 1 2 1
-- -> [1,0,2,1, 2,0,2,1, 3,0,2,1, 0,1,2,1]

def bitpack [n] (data: [n]i64): []i64 =
    let data2 = rep4 data
    let data3 = shiftbits data2 2
    in gettop data3 2