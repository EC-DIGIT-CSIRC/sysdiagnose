data = -9129941306809768153
data = int(data)

print("Big endian -> Little endian")
ba = (data).to_bytes(64, byteorder="big", signed=True)

# print hex
print("Hex view:")
print(ba)
print("")

# convert back to int
ls = int.from_bytes(ba, byteorder="little", signed=True)
print(f"Little Endian / Signed: {ls}")

lu = int.from_bytes(ba, byteorder="little", signed=False)
print(f"Little Endian / Unsigned: {lu}")

bs = int.from_bytes(ba, byteorder="big", signed=True)
print(f"Big Endian / Signed: {bs}")

bu = int.from_bytes(ba, byteorder="big", signed=False)
print(f"Big Endian / Unsigned: {bu}")
