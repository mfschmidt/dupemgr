#!/usr/bin/env python3

""" DupeManagerApp.py contains an application class designed to provide features around directory and file nodes. """

import os
import contextlib
import time

import nodes
from localutils import *


class DupeManagerApp():
    def __init__(self, verbosity=1):
        self.real_orig = None
        self.rmqueue = []
        self.force_removal = False
        self.check_removal = False
        self.extras = []
        self.exclusions = []
        self.trash_dirs = ['.Trash', ]
        self.overlaps = []
        self.verbosity = verbosity
        self.num_orig_dupes = 0
        self.size_orig_dupes = 0
        self.num_extras_dupes = 0
        self.size_extras_dupes = 0
        self.last_run_start = 0
        self.last_run_end = 0
        self.num_files_to_check = 0

    def print(self, s, v=1):
        if self.verbosity >= v:
            print(s)

    def remove_queued(self):
        if len(self.rmqueue) == 0:
            return
        self.print("Removal queue:", v=0)
        for f in self.rmqueue:
            self.print(f, v=0)
        while True:
            if self.force_removal:
                break
            try:
                self.print("{0} duplicate files found.".format(len(self.rmqueue)))
                delete_rule = input(
                    "Shall I \n\tA) Remove them all?\n\tB) Ask again for each file?\n\tC) Quit without deleting anything?\n")
                if delete_rule == "A" or delete_rule == "a":
                    self.force_removal = True
                    break
                elif delete_rule == "B" or delete_rule == "b":
                    print("You can try the --rmlog flag to save out a removal script next time.")
                    self.check_removal = True
                    break
                elif delete_rule == "C" or delete_rule == "c":
                    print(
                        "You can use the search command rather than remove or try the --rmlog flag to save out a removal script next time.")
                    self.force_removal = False
                    self.check_removal = False
                    break
                else:
                    raise ValueError
            except ValueError:
                print("I did not understand your answer.")
                continue
            else:
                break
        if self.force_removal:
            for f in self.rmqueue:
                with contextlib.suppress(FileNotFoundError):
                    os.remove(f.full_path)
                    parent_dir = os.path.abspath(os.path.join(f.full_path, os.pardir))
                    if os.path.isdir(parent_dir) and len(os.listdir(parent_dir)) < 1 and parent_dir not in self.extras:
                        self.print("    - removing {0} too".format(parent_dir), v=1)
                        os.rmdir(parent_dir)
                        # TODO: If access is denied, hang on and ask to save a remove log or wait for permissions to be granted.
        elif self.check_removal:
            for f in self.rmqueue:
                r = input("Remove {0}?".format(f.full_path))
                if r == "Y" or r == "y":
                    with contextlib.suppress(FileNotFoundError):
                        os.remove(f.full_path)
                        parent_dir = os.path.abspath(os.path.join(f.full_path, os.pardir))
                        if len(os.listdir(parent_dir)) < 1 and parent_dir not in self.extras:
                            self.print("    - removing {0} too".format(parent_dir), v=1)
                            os.rmdir(parent_dir)
                            # TODO: If access is denied, hang on and ask to save a remove log or wait for permissions to be granted.

    def rm(self, f):
        if f.full_path not in self.rmqueue:
            self.print("Queuing {0} for removal".format(f.full_path), v=4)
            if f not in self.rmqueue:
                self.rmqueue.append(f)

    def dbconfig(self, dbfile):
        self.print("DB configuration is not yet implemented.", v=0)

    def add_to_extras(self, paths):
        if paths:
            for p in paths:
                if os.path.exists(p):
                    self.print("  will check {0}".format(os.path.abspath(p.rstrip(os.sep))), v=2)
                    self.extras.append(os.path.abspath(p.rstrip(os.sep)))
                else:
                    self.print("  {0} does not exist, cannot scan it.".format(os.path.abspath(p.rstrip(os.sep))), v=2)

    def add_to_exclusions(self, paths):
        if paths:
            for p in paths:
                if os.path.exists(p):
                    self.print("  will avoid {0}".format(os.path.abspath(p.rstrip(os.sep))), v=2)
                    self.exclusions.append(os.path.abspath(p.rstrip(os.sep)))

    def exclude_overlaps(self, extras, source):
        if extras:
            for e in extras:
                real_e = os.path.abspath(e.rstrip(os.sep))
                if os.path.exists(real_e) and source in real_e:
                    # You can search for dupes of extra folder within the tree of originals,
                    # e.g. Do the files in /home/pictures/extras/from_camera exist anywhere else in /home/pictures?
                    # In this case, we add /home/pictures/extras/from_camera as an exclusion, but only for the internal loops
                    self.print("  will ignore {0} portion of {1}".format(real_e, source), v=2)
                    self.overlaps.append(real_e)

    def is_searchable_withmaps(self, path, check_overlaps=False):
        if self.exclusions:
            if True in map(lambda exclusion: exclusion in path, self.exclusions):
                return False
        if check_overlaps and self.overlaps:
            if True in map(lambda exclusion: exclusion in path, self.overlaps):
                return False
        if True in map(lambda exclusion: exclusion in path, self.trash_dirs):
            return False
        return True

    def is_searchable(self, path, check_overlaps=False):
        if self.exclusions:
            if True in [exclusion in path for exclusion in self.exclusions]:
                return False
        if check_overlaps and self.overlaps:
            if True in [exclusion in path for exclusion in self.overlaps]:
                return False
        if self.trash_dirs:
            if True in [exclusion in path for exclusion in self.trash_dirs]:
                return False
        return True

    def search(self, orig, extras=[], excls=[], do_rm=False):
        self.last_run_start = time.time()
        self.real_orig = os.path.abspath(orig.rstrip(os.sep))

        self.print("Searching for duplicate files in {0}...".format(self.real_orig), 5)

        self.add_to_extras(extras)
        self.add_to_exclusions(excls)
        self.exclude_overlaps(extras, self.real_orig)

        # Just find dupes in one directory...
        if (extras == [] or extras is None) and os.path.isdir(self.real_orig):
            self.print("Finding all duplicate files in {0}".format(self.real_orig), 3)
            d = nodes.DirNode(self.real_orig)
            self.num_files_to_check = d.total_files
            self.print("  searching {0} nodes for {0} nodes".format(d.total_files), 1)
            for f1 in d:
                printed_1 = False
                if self.is_searchable(f1.full_path):
                    for f2 in d:
                        if self.is_searchable(f2.full_path, check_overlaps=True):
                            self.print("{0} vs {1}".format(f1, f2), v=4)
                            if f1 != f2 and f1.compare(f2):
                                if not printed_1:
                                    # Only count and print the original file once, even if it matches repeatedly
                                    self.print(f1, v=1)
                                    printed_1 = True
                                    self.num_extras_dupes += 1
                                    self.size_extras_dupes += f1.size
                                self.print("    == {0}".format(f2), v=1)
                                self.num_orig_dupes += 1
                                self.size_orig_dupes += f2.size
                        else:
                            self.print("{0} is not searchable.".format(f2.full_path), v=5)

        # For each file in a target, find dupes in a source...
        elif os.path.isdir(self.real_orig):
            d = nodes.DirNode(self.real_orig)
            for t in self.extras:
                self.print("Finding all duplicates of {0} in {1}".format(t, self.real_orig), 3)
                if os.path.isfile(t):
                    self.num_files_to_check += 1
                    self.print("  searching {0} nodes for one file".format(d.total_files), 1)
                    f1 = nodes.FileNode(t)
                    printed_1 = False
                    if self.is_searchable(f1.full_path):
                        for f2 in d:
                            if self.is_searchable(f2.full_path, check_overlaps=True):
                                self.print("{0} vs {1}".format(f1, f2), v=4)
                                if f1.compare(f2):
                                    # At this point, we have found a legitimate match and need to deal with it
                                    if not printed_1:
                                        self.print(f1, 1)
                                        printed_1 = True
                                        self.num_extras_dupes += 1
                                        self.size_extras_dupes += f1.size
                                    self.print("  = {0}".format(f2), v=1)
                                    self.num_orig_dupes += 1
                                    self.size_orig_dupes += f2.size
                                    if do_rm:
                                        self.rm(f1)
                                else:
                                    # print("    ", "miss on ", f2.node_name)
                                    pass
                            else:
                                self.print("{0} is not searchable.".format(f2.full_path), v=5)
                    else:
                        self.print("{0} is not searchable.".format(f1.full_path), v=3)
                elif os.path.isdir(t):
                    # TODO: We are going to iterate over d numerous times. We should make a hash for quick lookup
                    #       rather than full traversal of the tree. This could happen in-app, or be outsourced to a
                    #       database like redis or postgresql. Hashing on an actual hash of each file's contents would be great,
                    #       after it's done, but we only want to spend CPU hashing files we care about. So we will
                    #       need to sort and index by size. A dictionary of lists, each list of files having equal
                    #       size will speed things up enormously.
                    td = nodes.DirNode(t)
                    self.num_files_to_check += td.total_files
                    self.print("  checking {0} extra files against {1} protected files.".format(td.total_files, d.total_files), 1)
                    for f1 in td:
                        printed_1 = False
                        if self.is_searchable(f1.full_path):
                            for f2 in d:
                                if self.is_searchable(f2.full_path, check_overlaps=True):
                                    if f1.compare(f2):
                                        # At this point, we have a legitimate match and need to deal with it
                                        if not printed_1:
                                            self.print(f1, v=1)
                                            printed_1 = True
                                            self.num_extras_dupes += 1
                                            self.size_extras_dupes += f1.size
                                        self.print("  = {0}".format(f2), v=1)
                                        self.num_orig_dupes += 1
                                        self.size_orig_dupes += f2.size
                                        if do_rm:
                                            self.rm(f1)
                                else:
                                    self.print("{0} is not searchable.".format(f2.full_path), v=5)
                        else:
                            self.print("{0} is not searchable.".format(f1.full_path), v=5)
        self.last_run_end = time.time()
        self.print("{0} extra files found (out of {2} checked), consuming {1}".format(
            self.num_extras_dupes,
            size_str(self.size_extras_dupes),
            self.num_files_to_check), 1)
        self.print("    and they matched {0} protected files consuming {1}.".format(self.num_orig_dupes, size_str(self.size_orig_dupes)), 1)
        self.print("    in {0}".format(time_str(self.last_run_end - self.last_run_start)), 2)
        if do_rm:
            self.remove_queued()
            self.print("Removed {0} files in {1}".format(len(self.rmqueue), time_str(self.last_run_end - self.last_run_start)), 2)

    def remove(self, orig, extras=[], excls=[]):
        self.print("Removing files from {0} with duplicates in {1}...".format(extras, orig), 5)
        return self.search(orig, extras, excls, do_rm=True)
