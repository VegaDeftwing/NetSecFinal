-- For each byte in the array, make a new array with 8/num_bit elemetns per byte, and extract the bits from the byte
-- map (\x -> map (\y -> (y `shiftR` (8 - num_bit)) .&. 0xFF) $ replicate 8 x)

-- def offset_bits (x: []i8): []i8 = map2 (\x -> x << [0,2,4,8])

def shiftmap (x: []i32) (y: []i32) : []i32 = map (<<) x y
