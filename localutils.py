#!/usr/bin/env python3

""" Utility functions to assist the dupemgr app """

import hashlib

import nodes


def short_hash(hash, chars=11):
    """Return the first and last few characters of the hash as a string for approximate visual comparison"""
    ch_ea = int((chars - 3) / 2)
    if hash is None:
        return ("0" * ch_ea) + "..." + ("0" * ch_ea)
    return hash[:ch_ea] + "..." + hash[(-1 * ch_ea):]


def hash256(the_file, blocksize=32768, force=False):
    """Return the sha256 hash of the file provided."""
    if not force and the_file.sha256 is not None:
        # If we already have a hash, use it.
        return the_file.sha256
    # We only do the expensive job of hashing if it doesn't exist, or we're asked to force it.
    try:
        with open(the_file.full_path, 'rb') as f:
            hasher = hashlib.sha256()
            while True:
                buf = f.read(blocksize)
                if not buf:
                    break
                hasher.update(buf)
    except:
        return None
    return hasher.hexdigest()


def size_str(num):
    """Stringify a file size in human-friendly terms."""
    if num > 2 ** 30:
        return "%0.2fGB" % (num / 2 ** 30)
    elif num > 2 ** 20:
        return "%0.2fMB" % (num / 2 ** 20)
    elif num > 2 ** 10:
        return "%0.2fkB" % (num / 2 ** 10)
    else:
        return "%d bytes" % num


def time_str(num):
    """Stringify a number of seconds in human-friendly terms."""
    if num > 3600:
        return "%0.2f hrs" % (num / 3600)
    elif num > 60:
        return "%0.2f mins" % (num / 60)
    else:
        return "%d seconds" % num
