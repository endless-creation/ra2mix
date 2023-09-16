import json
import os
import struct
from collections import namedtuple
from importlib.resources import files

from . import cccrypto, const
from .checksum import ra2_crc

Header = namedtuple("Header", "flags file_count data_size")

FileEntry = namedtuple("FileEntry", "id offset size")

gmd_text = files("ra2mix.data").joinpath("global_mix_database.json").read_text()
gmd = json.loads(gmd_text)

gmd_id_file_map = {ra2_crc(filename): filename for filename in gmd.keys()}
gmd_file_id_map = {filename: ra2_crc(filename) for filename in gmd.keys()}

# print(f"Loaded {len(gmd)} files from global mix database")


def get_file_entries(file_count: int, index_data: bytes) -> list[FileEntry]:
    file_entries = []
    for i in range(file_count):
        start = i * const.FILE_ENTRY_SIZE
        end = start + const.FILE_ENTRY_SIZE

        # import binascii
        # print(f'data={binascii.b2a_hex(index_data[start:end], ":")}')

        entry = FileEntry._make(struct.unpack("=iII", index_data[start:end]))
        # print(f"{entry=}")
        file_entries.append(entry)

    return file_entries


def get_filenames_from_mix_db(mix_db_file_data: bytes) -> list[str]:
    filenames = []
    end = (start := const.XCC_HEADER_SIZE)
    while start < len(mix_db_file_data):
        while mix_db_file_data[end] != 0:
            end += 1
        filename = mix_db_file_data[start:end].decode("utf-8")
        filenames.append(filename)
        # print(f"{start=}, {end=}, {filename=}")
        end += 1
        start = end

    return filenames


def get_file_data_from_mix_body(file_entry: FileEntry, mix_body_data: bytes) -> bytes:
    return mix_body_data[file_entry.offset : file_entry.offset + file_entry.size]


def get_file_map(file_entries: list[FileEntry], mix_data: bytes, header: Header):
    if len(file_entries) == 1:
        return {}

    MIX_DB_ID = ra2_crc(const.MIX_DB_FILENAME)

    body_start = const.HEADER_SIZE + (const.FILE_ENTRY_SIZE * len(file_entries))
    if header.flags & 0x20000:
        body_start += const.SIZE_OF_ENCRYPTED_KEY
        body_start += cccrypto.get_decryption_block_sizing(header.file_count)[1]

    local_mix_db_file_entry = None
    for file_entry in file_entries:
        if file_entry.id != MIX_DB_ID:
            continue
        local_mix_db_file_entry = file_entry
        break

    mix_body_data = mix_data[body_start:]

    if local_mix_db_file_entry is None:
        # print(f"No local mix db detected, using global mix db")
        id_filename_map = gmd_id_file_map
    else:
        local_mix_db_data = get_file_data_from_mix_body(
            local_mix_db_file_entry, mix_body_data
        )

        filenames = get_filenames_from_mix_db(local_mix_db_data)
        id_filename_map = {ra2_crc(filename): filename for filename in filenames}

    # print(f"{filename_id_map=}")

    filemap = {}
    for file_entry in file_entries:
        file_data = get_file_data_from_mix_body(file_entry, mix_body_data)
        try:
            filemap[id_filename_map[file_entry.id]] = file_data
        except KeyError:
            print(f"Can't find ID {file_entry.id}")

    return filemap


def read_file_info(
    mix_filepath: str | None = None, mix_data: bytes | None = None
) -> tuple[Header, list[FileEntry], bytes]:
    if mix_filepath is None and mix_data is None:
        raise ValueError("Must specify either mix_filepath or mix_data")

    if mix_filepath is not None and mix_data is not None:
        raise ValueError("Cannot specify both mix_filepath and mix_data")

    if mix_data is None:
        with open(mix_filepath, "rb") as fp:
            mix_data = fp.read()

    # print(f"{len(mix_data)=}")

    header = Header._make(struct.unpack("=I H I", mix_data[: const.HEADER_SIZE]))
    # print(bin(header.flags))
    is_encrypted = (header.flags & 0x20000) != 0
    if is_encrypted:
        encrypted_blowfish_key = mix_data[
            const.SIZE_OF_FLAGS : const.SIZE_OF_FLAGS + const.SIZE_OF_ENCRYPTED_KEY
        ]
        decrypted_blowfish_key = cccrypto.decrypt_blowfish_key(encrypted_blowfish_key)
        file_count, data_size, index_data = cccrypto.decrypt_mix_header(
            mix_data, decrypted_blowfish_key
        )

        # print(f"Decrypted header, {file_count=}, {len(index_data)=}")
        file_entries = get_file_entries(file_count, index_data)
        header = header._replace(file_count=file_count, data_size=data_size)
    else:
        file_entries = get_file_entries(
            header.file_count, mix_data[const.HEADER_SIZE :]
        )

    return header, file_entries, mix_data


def read(
    mix_filepath: str | None = None, mix_data: bytes | None = None
) -> dict[str, bytes]:
    if mix_filepath is None and mix_data is None:
        raise ValueError("Must specify either mix_filepath or mix_data")

    if mix_filepath is not None and mix_data is not None:
        raise ValueError("Cannot specify both mix_filepath and mix_data")

    header, file_entries, mix_data = read_file_info(mix_filepath, mix_data)

    return get_file_map(file_entries, mix_data, header)


def extract(mix_filepath: str, folder_path: str) -> None:
    file_map = read(mix_filepath)

    os.makedirs(folder_path, exist_ok=True)
    # print(f"Writing files to {folder_path}..")

    for filename, file_data in file_map.items():
        # print(f"Creating {filename}")
        with open(os.path.join(folder_path)) as fp:
            fp.write(file_data)
