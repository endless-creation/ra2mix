import struct

from crc import Calculator, Crc32


def obfuscate_filename(filename: str) -> str:
    filename_length = len(filename)
    obfuscated_name = filename.upper()
    salt = filename_length & 0xFFFFFFFC
    if filename_length & 3:
        obfuscated_name += chr(filename_length - salt)
        fill_count = 3 - (filename_length & 3)
        for _ in range(fill_count):
            obfuscated_name += obfuscated_name[salt]
    return obfuscated_name


def ra2_crc(filename: str) -> int:
    obfuscated_name = obfuscate_filename(filename)
    binary_data = obfuscated_name.encode()
    crc = Calculator(Crc32.CRC32).checksum(binary_data)

    # CRC must be interpreted as a 32-bit signed integer for proper sorting
    # in mix file header/body
    (signed_crc,) = struct.unpack("=i", struct.pack("=I", crc))
    return signed_crc
