import struct

message = 'hello'
# message = struct.pack('>I', len(message)) + bytes(message, 'utf-8')
message = struct.pack('>I', len(message))
print(message)
slen = struct.unpack('>L', b'\x00\x00\x00\x05')
print(slen)


pack_str = struct.pack('>I', 10240099)
print(pack_str)  # b'\x00\x9c@c'

unpack_str = struct.unpack('>I', pack_str)
print(unpack_str)