import base64
import ctypes
from contextlib import contextmanager


class SecurityItem(ctypes.Structure):
    _fields_ = [
        ('kind', ctypes.c_int),
        ('data', ctypes.POINTER(ctypes.c_ubyte)),
        ('length', ctypes.c_uint),
    ]


def load_library():
    library = ctypes.CDLL('/opt/thunderbird/libnss3.so')
    signatures = {
        'NSS_InitReadWrite': ([ctypes.c_char_p], ctypes.c_int),
        'NSS_Shutdown': ([], ctypes.c_int),
        'PK11_GetInternalKeySlot': ([], ctypes.c_void_p),
        'PK11_NeedUserInit': ([ctypes.c_void_p], ctypes.c_int),
        'PK11_InitPin': (
            [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p],
            ctypes.c_int,
        ),
        'PK11SDR_Encrypt': (
            [ctypes.POINTER(SecurityItem)] * 3 + [ctypes.c_void_p],
            ctypes.c_int,
        ),
        'SECITEM_FreeItem': ([ctypes.POINTER(SecurityItem), ctypes.c_int], None),
        'PK11_FreeSlot': ([ctypes.c_void_p], None),
    }
    for name, (arguments, result) in signatures.items():
        function = getattr(library, name)
        function.argtypes = arguments
        function.restype = result
    return library


def require_success(result):
    if result != 0:
        raise RuntimeError('Could not initialize disposable Thunderbird credentials.')


@contextmanager
def encryption_library(profile):
    library = load_library()
    require_success(library.NSS_InitReadWrite(f'sql:{profile}'.encode()))
    slot = None
    try:
        slot = library.PK11_GetInternalKeySlot()
        if not slot:
            raise RuntimeError('Could not open disposable Thunderbird credential slot.')
        if library.PK11_NeedUserInit(slot):
            require_success(library.PK11_InitPin(slot, None, b''))
        yield library
    finally:
        if slot:
            library.PK11_FreeSlot(slot)
        require_success(library.NSS_Shutdown())


def encrypt(library, value):
    encoded = value.encode()
    buffer = (ctypes.c_ubyte * len(encoded)).from_buffer_copy(encoded)
    plain = SecurityItem(0, buffer, len(encoded))
    key = SecurityItem()
    encrypted = SecurityItem()
    try:
        require_success(library.PK11SDR_Encrypt(ctypes.byref(key), ctypes.byref(plain), ctypes.byref(encrypted), None))
        return base64.b64encode(ctypes.string_at(encrypted.data, encrypted.length)).decode()
    finally:
        if encrypted.data:
            library.SECITEM_FreeItem(ctypes.byref(encrypted), False)
