#!/usr/bin/env python3

""" Node classes, FileNode and DirNode, represent directory trees and files within """

import os
import time

# Support functions for this package are defined in localutils.py
from localutils import *


class BaseNode():
    """A base class for all filesystem objects (dirs and files) to inherit from."""

    def __init__(self, path, parent=None):
        """Initialize the node with a name and a path."""
        self.full_path = os.path.normpath(path.rstrip(os.sep))
        self.node_name = os.path.basename(self.full_path)
        self.node_path = os.path.dirname(self.full_path)
        self.parent = parent

    def __str__(self):
        """Stringification of node, just name for now"""
        return self.node_name


class FileNode(BaseNode):
    """Maintain information about a file node"""

    def __init__(self, path, parent=None):
        """Initialize the FileNode with actual filesystem data based on the path provided."""
        if isinstance(path, str) and os.path.isfile(path):
            BaseNode.__init__(self, path, parent)
            fstat = os.stat(self.full_path)
            self.size = int(fstat.st_size)
            # self.size = os.path.getsize(self.full_path)
            # self.created = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fstat.st_ctime))
            self.created = os.path.getctime(self.full_path)
            # self.modified = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(fstat.st_mtime))
            self.modified = os.path.getmtime(self.full_path)
            # self.tabled = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            self.tabled = time.localtime()
            self.sha256 = None
            # print("        String   -> \"{0}\"".format(self.__str__()))
        else:
            BaseNode.__init__(self, path.path, parent)
            self.size = path.stat().st_size
            self.created = path.stat().st_ctime
            self.modified = path.stat().st_mtime
            self.tabled = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            self.sha256 = None
            # print("        DirEntry -> \"{0}\"".format(self.__str__()) )
            # else:
            # print("        FAIL: got \"{0}\" as {1}, but could not find the file.".format(path, type(path)))
            # pass

    def __str__(self):
        """Provide a string representation of the important file details"""
        return "{0}, {1}, mod {2}, [{3}]".format(self.full_path,
                                                 size_str(self.size),
                                                 time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.modified)),
                                                 short_hash(self.sha256))

    def as_dict(self, host):
        """Return the members of the FileNode class structured as a python3 dictionary"""
        return {
            'name': self.node_name,
            'path': self.node_path,
            'size': self.size,
            'host': host,
            'created': self.created,
            'modified': self.modified,
            'tabled': self.tabled,
            'sha256': self.sha256,
        }

    def signature(self):
        self.sha256 = hash256(self, force=False)
        return "{0:16}-{1}".format(self.size, self.sha256)

    def compare(self, other_file):
        """Compare self file to another provided file, returning "match" "content" or False."""
        if self.size == other_file.size:
            # Hashing is expensive and hashes don't matter unless filesizes match, so don't even bother unless we're already matched on size.
            # Even so, if hashing is already done, localutils.hash256 only hashes on None hashes unless force=True
            # We really only want to do this once, and only if necessary.
            self.sha256 = hash256(self, force=False)
            other_file.sha256 = hash256(other_file, force=False)
            if self.sha256 == other_file.sha256:
                if self.node_name == other_file.node_name:
                    return "match"
                else:
                    return "content"
        return False


class DirNode(BaseNode):
    """Maintain information about a directory node."""

    def __init__(self, path, parent=None, do_walk=True, do_hidden=False, depth=0, make_size_dict=False):
        """Initialize a directory node"""
        BaseNode.__init__(self, path, parent)

        # Initialize counters and sums
        self.depth = 0
        self.subdirs = []
        self.files = []
        self.files_by_size = {}
        self.parent = parent
        self.num_subdirs = 0
        self.num_files = 0
        self.bytes = 0
        self.total_subdirs = 0
        self.total_files = 0
        self.total_bytes = 0
        self.expanded = False

        # Walk the directory if requested and existent
        if do_walk and os.path.isdir(path):
            it = os.scandir(path)
            # it is an os.DirEntry object with name, path, is_dir(), is_file(), stat() members
            for entry in it:
                if entry.is_dir():
                    # print("    {0}[ {1} ]".format( "".ljust(depth*2), entry.name ))
                    self.num_subdirs += 1
                    if do_walk:
                        # Create the node first, triggering a walk, then use its contents.
                        the_dir = DirNode(entry.path, parent=self, depth=depth + 1)
                        self.subdirs.append(the_dir)
                        self.merge_dicts(the_dir.files_by_size)
                elif entry.is_file():
                    # print("    {0} ({1} bytes)".format( entry.path, entry.stat().st_size ))
                    self.num_files += 1
                    the_file = FileNode(entry)
                    self.bytes += the_file.size
                    # Stick the file in our simple list
                    self.files.append(FileNode(entry))
                    # and stick the file in our size-indexed dictionary
                    if the_file.size in self.files_by_size:
                        self.files_by_size[the_file.size].append(the_file)
                    else:
                        self.files_by_size[the_file.size] = [the_file, ]
            self.total_files += self.num_files
            self.total_subdirs += self.num_subdirs
            self.total_bytes += self.bytes
            self.expanded = True
            if self.parent:
                # print("--update parent {0}--".format(parent.node_name))
                self.parent.total_subdirs += self.total_subdirs
                self.parent.total_files += self.total_files
                self.parent.total_bytes += self.total_bytes
            else:
                # print("--no parent to update--")
                pass
        else:
            print("Either do_walk was set to False, or \"{0}\" is not a directory.".format(path))

            # print("{0} initialized with {1}/{2} subdirs, {3}/{4} files, using {5}/{6} bytes".format(
            #     self.full_path,
            #     self.num_subdirs, self.total_subdirs,
            #     self.num_files, self.total_files,
            #     self.bytes, self.total_bytes))

    def __iter__(self):
        return DirIterator(self)

    def __reversed__(self):
        return DirIterator(self)

    def __str__(self):
        return "{0} ({2} in {1} files)".format(self.full_path, self.total_files, size_str(self.total_bytes))

    def merge_dicts(self, new_dict):
        for size_key in new_dict:
            if size_key in self.files_by_size:
                self.files_by_size[size_key] = self.files_by_size[size_key] + new_dict[size_key]
            else:
                self.files_by_size[size_key] = new_dict[size_key]


class DirIterator():
    def __init__(self, parent):
        self.parent = parent
        self.count = 0
        self.idx = 0
        self.it = None

    def __iter__(self):
        return self

    def __next__(self):
        self.count += 1
        if self.idx < len(self.parent.files):
            # Go through parent's files
            self.idx += 1
            return self.parent.files[self.idx - 1]
        elif self.idx < len(self.parent.files) + len(self.parent.subdirs):
            # For each subdir, pass the buck to a whole new iterator and act as a proxy.
            if self.it is None:
                self.it = iter(self.parent.subdirs[self.idx - len(self.parent.files)])
            try:
                return next(self.it)
            except StopIteration:
                self.idx += 1
                self.it = None
                return next(self)
        else:
            # If we're out of files and subdirs, just let our caller know
            raise StopIteration

    def __len__(self):
        return self.count
