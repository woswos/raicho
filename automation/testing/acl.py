import os
import struct

ACL_USER_OWNER = 0x01
ACL_NAMED_USER = 0x02
ACL_GROUP_OWNER = 0x04
ACL_MASK = 0x10
ACL_OTHER = 0x20
ACL_UNDEFINED_ID = 0xFFFFFFFF


def default_acl(uid):
    entries = [
        (ACL_USER_OWNER, 7, ACL_UNDEFINED_ID),
        (ACL_NAMED_USER, 7, uid),
        (ACL_GROUP_OWNER, 7, ACL_UNDEFINED_ID),
        (ACL_MASK, 7, ACL_UNDEFINED_ID),
        (ACL_OTHER, 5, ACL_UNDEFINED_ID),
    ]
    acl = b''.join(struct.pack('<HHI', *entry) for entry in entries)
    return struct.pack('<I', 2) + acl


def set_default_acl(test, directory):
    try:
        os.setxattr(directory, 'system.posix_acl_default', default_acl(os.getuid()))
    except OSError:
        test.skipTest('The test filesystem has no POSIX ACL support.')
