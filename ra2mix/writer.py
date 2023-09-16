import struct
from pathlib import Path
from typing import TypedDict

from . import const
from .checksum import ra2_crc


def get_mix_db_data(filenames: list[str], game: const.XCCGame):
    num_files = len(filenames)
    db_size_in_bytes = (
        const.XCC_HEADER_SIZE
        + sum([len(filename) for filename in filenames])
        + num_files
    )

    bytes_data = struct.pack("=32s", const.XCC_ID_BYTES) + struct.pack(
        "=5I",
        db_size_in_bytes,
        const.XCC_FILE_TYPE,
        const.XCC_FILE_VERSION,
        game.value,
        num_files,
    )

    for filename in filenames:
        # each filename will end with a \x00 (null) byte in the output data
        bytes_data += struct.pack(f"={len(filename) + 1}s", filename.encode())

    return bytes_data


def coalesce_input_files(
    game: const.XCCGame,
    file_map: dict[str, bytes] | None,
    input_folder: str | None,
    filepaths: list[str] | None,
):
    if sum(map(bool, [file_map, input_folder, filepaths])) > 1:
        raise ValueError(
            "Must provide exactly one of the following args: file_map, input_folder, "
            "filepaths"
        )

    if not file_map:
        if input_folder:
            folder_path = Path(input_folder)
            assert folder_path.exists(), f"{folder_path} does not exist!"

            paths = list(folder_path.rglob("*.*"))
        else:
            paths = [Path(filepath) for filepath in filepaths]
            for path in paths:
                assert path.exists(), f"{path} does not exist!"

        file_map = {}
        for path in paths:
            file_map[path.name] = path.read_bytes()

    filenames = list(file_map.keys())
    filenames.append(const.MIX_DB_FILENAME)

    db_data = get_mix_db_data(filenames, game)

    file_map[const.MIX_DB_FILENAME] = db_data

    filetypes = {}
    for filename in file_map.keys():
        filetype = filename.split(".")[-1]
        if filetype in filetypes:
            filetypes[filetype] = filetypes[filetype] + 1
        else:
            filetypes[filetype] = 1

    # print("The following files will be written to the .mix file:")
    # for filetype, count in filetypes.items():
    # print(f"\t*.{filetype}: {count}")

    return file_map


class FileInfo(TypedDict):
    file_id: int
    data: bytes


def create_mix_header(file_map: dict[str, bytes]) -> bytes:
    flags = 0
    file_count = len(file_map)
    data_size = sum(len(data) for data in file_map.values())

    # print(f"Writing {file_count} files to mix file; total size = {data_size}")

    header = struct.pack("=I H I", flags, file_count, data_size)

    return header


def write(
    mix_filepath: str | None,
    game: const.XCCGame = const.XCCGame.RA2,
    file_map: dict[str, bytes] | None = None,
    folder_path: str | None = None,
    filepaths: list[str] | None = None,
) -> bytes:
    # print("---")
    file_map = coalesce_input_files(game, file_map, folder_path, filepaths)

    file_information_list = [
        FileInfo(file_id=ra2_crc(filename), data=data)
        for filename, data in file_map.items()
    ]
    sorted_file_info_list = sorted(
        file_information_list, key=lambda file_info: file_info["file_id"]
    )

    offset = 0
    file_entry_data = b""
    body_data = b""
    # print("Generating .mix data")
    for file_info in sorted_file_info_list:
        size = len(file_info["data"])

        file_entry_data += struct.pack("=iII", file_info["file_id"], offset, size)
        body_data += file_info["data"]

        offset += size

    mix_data = create_mix_header(file_map) + file_entry_data + body_data

    if mix_filepath is not None:
        # print(f"Writing mix data to file {mix_filepath}")
        with open(mix_filepath, "wb") as fp:
            fp.write(mix_data)

    return mix_data
