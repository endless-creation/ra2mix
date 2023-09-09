import struct

import blowfish

from . import const


def decrypt_blowfish_key(encrypted_blowfish_key):
    BLOCK_SIZE = 40
    PUBLIC_EXPONENT = 65537
    PUBLIC_MODULUS = int(
        "681994811107118991598552881669230523074742337494683459234572860554038768387821"
        "901289207730765589"
    )

    if len(encrypted_blowfish_key) < const.SIZE_OF_ENCRYPTED_KEY:
        raise ValueError("Buffer is not long enough")

    blocks = [
        encrypted_blowfish_key[i : i + BLOCK_SIZE]
        for i in range(0, const.SIZE_OF_ENCRYPTED_KEY, BLOCK_SIZE)
    ]

    decrypted_blowfish_key = b""
    for encrypted_block in blocks:
        # Do RSA decryption in 40 byte blocks
        decrypted_int = pow(
            int.from_bytes(encrypted_block, byteorder="little"),
            PUBLIC_EXPONENT,
            PUBLIC_MODULUS,
        )
        decrypted = decrypted_int.to_bytes(
            (decrypted_int.bit_length() + 7) // 8, byteorder="little"
        )

        decrypted_blowfish_key += decrypted.rstrip(b"\x00")

    return decrypted_blowfish_key


def get_decryption_block_sizing(file_count: int) -> tuple[int, int]:
    index_len = file_count * const.FILE_ENTRY_SIZE
    remaining_index_len = index_len - const.SIZE_OF_FILE_COUNT
    padding_size = const.BLOCK_SIZE - remaining_index_len % const.BLOCK_SIZE
    decrypt_size = remaining_index_len + padding_size

    return decrypt_size, padding_size


def decrypt_mix_header(mix_data: bytes, key: bytes) -> tuple[int, int, bytes]:
    cipher = blowfish.Cipher(key)

    header_start = const.SIZE_OF_FLAGS + const.SIZE_OF_ENCRYPTED_KEY
    decrypted_block = cipher.decrypt_block(
        mix_data[header_start : header_start + const.BLOCK_SIZE]
    )

    (file_count, data_size) = struct.unpack(
        "=H I", decrypted_block[: const.SIZE_OF_FILE_COUNT + const.SIZE_OF_DATA_SIZE]
    )

    decrypt_size, padding_size = get_decryption_block_sizing(file_count)

    data_decrypted = b"".join(
        cipher.decrypt_ecb(
            mix_data[
                header_start
                + const.BLOCK_SIZE : header_start
                + const.BLOCK_SIZE
                + decrypt_size
            ]
        )
    )

    num_bytes_index_data_in_first_block = (
        const.BLOCK_SIZE - const.SIZE_OF_FILE_COUNT - const.SIZE_OF_DATA_SIZE
    )
    index_decrypted = (
        decrypted_block[-num_bytes_index_data_in_first_block:]
        + data_decrypted[:-padding_size]
    )

    return file_count, data_size, index_decrypted
