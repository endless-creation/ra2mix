from enum import Enum

# Byte Size of various data types
BLOCK_SIZE = 8
HEADER_SIZE = 10
FILE_ENTRY_SIZE = 12
SIZE_OF_FLAGS = 4
SIZE_OF_FILE_COUNT = 2
SIZE_OF_DATA_SIZE = 4
SIZE_OF_ENCRYPTED_KEY = 80

MIX_DB_FILENAME = "local mix database.dat"

XCC_HEADER_SIZE = 52
XCC_FILE_TYPE = 0
XCC_FILE_VERSION = 0

XCC_ID_BYTES = b"XCC by Olaf van der Spek\x1a\x04\x17\x27\x10\x19\x80"


class XCCGame(Enum):
    TD = 0
    RA = 1
    TS = 2
    DUNE2 = 3
    DUNE2000 = 4
    RA2 = 5
    RA2_YR = 6
    RG = 7
    GR = 8
    GR_ZH = 9
    EBFD = 10
    NOX = 11
    BFME = 12
    BFME2 = 13
    TW = 14
    TS_FS = 15
    UNKNOWN = 16
