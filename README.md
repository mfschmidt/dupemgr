# dupemgr

dupemgr is a multifunction utility to manage duplicate files and directories on any operating system.

## Finding duplicates

    $ dupemgr search /path

"search" lists all duplicate files found in /path, recursively. By default, results are sorted by number of duplicates first, size of duplicates second. This behavior can be changed by specifying --by quantity or --by size or --by name.


    $ dupemgr search /path --for /some/file.txt

"search" lists all files found in /path, recursively, that are duplicates of /some/file.txt.

## Removing duplicates

    $ dupemgr remove /path/protected --from /path/deletable

"remove" removes all files from /path/deletable that have duplicates in /path/protected. This can be useful if you have a backup copy you would like to delete, but want to make sure you aren't getting rid of anything unique. It can also be helpful if you have a camera or phone with images you may have already uploaded to your PC. You can remove all duplicate images from a temporary folder holding the camera's images, even if they've been renamed and put into different directories, then decide to move what's left into your photos directories or not.

