import struct

data = -9129941306809768153
data = int(data)

print("Big endian -> Little endian")
ba = (data).to_bytes(64, byteorder='big', signed=True)

# print hex
print("Hex view:")
print(ba)
print("")

# convert back to int
ls = int.from_bytes(ba, byteorder="little", signed=True)
print("Little Endian / Signed: %d" % ls)

lu = int.from_bytes(ba, byteorder="little", signed=False)
print("Little Endian / Unsigned: %d" % lu)

bs = int.from_bytes(ba, byteorder="big", signed=True)
print("Little Endian / Signed: %d" % bs)

bu = int.from_bytes(ba, byteorder="big", signed=False)
print("Little Endian / Unsigned: %d" % bu)
