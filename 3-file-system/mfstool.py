"""
- Name: Daan Rosendal
- Student number: 15229394
- Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating Systems
  as a "bijvak".

This is a program that can execute various commands on a MINIX file system.
"""

import sys
import struct
import time

BLOCK_SIZE = 1024


# Parsing the superblock from its binary data
def parse_superblock(sbdata):
    sbdict = {}
    (
        sbdict["ninodes"],
        sbdict["nzones"],
        sbdict["imap_blocks"],
        sbdict["zmap_blocks"],
        sbdict["firstdatazone"],
        sbdict["log_zone_size"],
        sbdict["max_size"],
        sbdict["magic"],
        sbdict["state"],
    ) = struct.unpack("<HHHHHHIHH", sbdata[:20])

    return sbdict


# Reading an inode from the inode table
def read_inode(f, inode_table_start, inode_number):
    inode_size = 32
    inode_offset = inode_table_start + (inode_number - 1) * inode_size
    f.seek(inode_offset)
    inode_data = f.read(inode_size)
    inode = struct.unpack("<HHIIBB9H", inode_data)
    inode_dict = {
        "mode": inode[0],
        "uid": inode[1],
        "size": inode[2],
        "time": inode[3],
        "gid": inode[4],
        "nlinks": inode[5],
        "zones": inode[6:15],
    }

    return inode_dict


# Writing an inode to the inode table
def write_inode(f, inode_table_start, inode_number, inode_data):
    inode_size = 32
    inode_offset = inode_table_start + (inode_number - 1) * inode_size
    f.seek(inode_offset)
    f.write(inode_data)


# Listing directory entries in an inode
def list_directory(f, inode, filename_length):
    entry_size = 2 + filename_length
    directory_entries = []
    for zone in inode["zones"]:
        if zone == 0:
            continue
        f.seek(zone * BLOCK_SIZE)
        for _ in range(BLOCK_SIZE // entry_size):
            entry_data = f.read(entry_size)
            inode_num, name = struct.unpack(f"<H{filename_length}s", entry_data)
            if inode_num == 0:
                continue
            name = name.rstrip(b"\0")
            directory_entries.append((inode_num, name))

    return directory_entries


# Finding a directory entry by filename
def find_entry(f, inode, filename, filename_length):
    directory_entries = list_directory(f, inode, filename_length)
    for inode_num, name in directory_entries:
        if name == filename:
            return inode_num

    return None


# Reading file content from an inode
def read_file(f, inode):
    file_content = bytearray()
    for zone in inode["zones"]:
        if zone == 0:
            continue
        f.seek(zone * BLOCK_SIZE)
        file_content.extend(f.read(BLOCK_SIZE))

    return file_content[: inode["size"]]


# Allocating a new inode
def allocate_inode(f, sb):
    f.seek(BLOCK_SIZE * 2)
    imap = bytearray(f.read(BLOCK_SIZE * sb["imap_blocks"]))
    for i in range(1, sb["ninodes"]):
        byte_index = i // 8
        bit_index = i % 8
        if not (imap[byte_index] & (1 << bit_index)):
            imap[byte_index] |= 1 << bit_index
            f.seek(BLOCK_SIZE * 2)
            f.write(imap)
            return i

    return None


# Allocating a new zone
def allocate_zone(f, sb):
    f.seek(BLOCK_SIZE * (2 + sb["imap_blocks"]))
    zmap = bytearray(f.read(BLOCK_SIZE * sb["zmap_blocks"]))
    for i in range(1, sb["nzones"]):
        byte_index = i // 8
        bit_index = i % 8
        if not (zmap[byte_index] & (1 << bit_index)):
            zmap[byte_index] |= 1 << bit_index
            f.seek(BLOCK_SIZE * (2 + sb["imap_blocks"]))
            f.write(zmap)
            return i + sb["firstdatazone"] - 1

    return None


# Adding a new directory entry
def add_directory_entry(
    f, inode, filename, inode_num, filename_length, inode_table_start
):
    entry_size = 2 + filename_length
    new_entry = struct.pack(
        f"<H{filename_length}s", inode_num, filename.ljust(filename_length, b"\0")
    )
    for zone in inode["zones"]:
        if zone == 0:
            continue
        if add_entry_to_zone(f, zone, entry_size, new_entry):
            update_inode_size(f, inode, inode_table_start, entry_size)
            return

    print("Error: No space left in the root directory", file=sys.stderr)
    sys.exit(1)


# Adding an entry to a specific zone
def add_entry_to_zone(f, zone, entry_size, new_entry):
    f.seek(zone * BLOCK_SIZE)
    for _ in range(BLOCK_SIZE // entry_size):
        entry_data = f.read(entry_size)
        existing_inode_num, _ = struct.unpack(f"<H{len(new_entry)-2}s", entry_data)
        if existing_inode_num == 0:
            f.seek(-entry_size, 1)
            f.write(new_entry)
            return True

    return False


# Updating the size of an inode
def update_inode_size(f, inode, inode_table_start, entry_size):
    inode["size"] += entry_size
    inode_data = struct.pack(
        "<HHIIBB9H",
        inode["mode"],
        inode["uid"],
        inode["size"],
        inode["time"],
        inode["gid"],
        inode["nlinks"],
        *inode["zones"],
    )
    write_inode(f, inode_table_start, 1, inode_data)


# Creating a new directory
def create_directory(f, sb, root_inode, dirname, inode_table_start, filename_length):
    new_inode_num = allocate_inode(f, sb)
    if new_inode_num is None:
        print("Error: No free inodes available", file=sys.stderr)
        sys.exit(1)
    new_zone_num = allocate_zone(f, sb)
    if new_zone_num is None:
        print("Error: No free zones available", file=sys.stderr)
        sys.exit(1)
    initialise_directory_inode(
        f, new_inode_num, new_zone_num, inode_table_start, filename_length
    )
    update_root_directory(
        f, root_inode, dirname, new_inode_num, filename_length, inode_table_start
    )


# Initialising a new directory inode
def initialise_directory_inode(
    f, new_inode_num, new_zone_num, inode_table_start, filename_length
):
    current_time = int(time.time())
    new_inode = struct.pack(
        "<HHIIBB9H",
        0o040700,  # Directory mode with 700 permissions
        0,  # uid
        2 * (2 + filename_length),  # size
        current_time,  # time
        0,  # gid
        2,  # nlinks
        new_zone_num,  # zones
        *([0] * 8),  # zones
    )
    write_inode(f, inode_table_start, new_inode_num, new_inode)
    entry_size = 2 + filename_length
    new_zone = bytearray(BLOCK_SIZE)
    new_zone[:entry_size] = struct.pack(
        f"<H{filename_length}s", new_inode_num, b".".ljust(filename_length, b"\0")
    )

    start = entry_size
    end = 2 * entry_size
    new_zone[start:end] = struct.pack(
        f"<H{filename_length}s", 1, b"..".ljust(filename_length, b"\0")
    )

    f.seek(new_zone_num * BLOCK_SIZE)
    f.write(new_zone)


# Updating the root directory with a new entry
def update_root_directory(
    f, root_inode, dirname, new_inode_num, filename_length, inode_table_start
):
    root_inode["nlinks"] += 1
    root_inode_data = struct.pack(
        "<HHIIBB9H",
        root_inode["mode"],
        root_inode["uid"],
        root_inode["size"],
        root_inode["time"],
        root_inode["gid"],
        root_inode["nlinks"],
        *root_inode["zones"],
    )
    write_inode(f, inode_table_start, 1, root_inode_data)
    add_directory_entry(
        f, root_inode, dirname, new_inode_num, filename_length, inode_table_start
    )


# Handling the 'ls' command
def handle_ls(f, root_inode, filename_length):
    filenames = list_directory(f, root_inode, filename_length)
    for _, filename in filenames:
        sys.stdout.buffer.write(filename)
        sys.stdout.buffer.write(b"\n")


# Handling the 'cat' command
def handle_cat(f, inode_table_start, root_inode, filename_length, path):
    if len(path) == 1:
        file_inode = get_file_inode(
            f, inode_table_start, root_inode, filename_length, path[0]
        )
    elif len(path) == 2:
        file_inode = get_subdir_file_inode(
            f, inode_table_start, root_inode, filename_length, path
        )
    else:
        print(
            "Error: Only supports files in root or one level subdirectories",
            file=sys.stderr,
        )
        sys.exit(1)
    file_content = read_file(f, file_inode)
    sys.stdout.buffer.write(file_content)


# Getting inode of a file in the root directory
def get_file_inode(f, inode_table_start, root_inode, filename_length, filename):
    file_inode_num = find_entry(f, root_inode, filename.encode(), filename_length)
    if file_inode_num is None:
        print(f"Error: File '{filename}' not found in root directory", file=sys.stderr)
        sys.exit(1)

    return read_inode(f, inode_table_start, file_inode_num)


# Getting inode of a file in a subdirectory
def get_subdir_file_inode(f, inode_table_start, root_inode, filename_length, path):
    dirname, filename = path
    subdir_inode_num = find_entry(f, root_inode, dirname.encode(), filename_length)
    if subdir_inode_num is None:
        print(f"Error: Directory '{dirname}' not found", file=sys.stderr)
        sys.exit(1)
    subdir_inode = read_inode(f, inode_table_start, subdir_inode_num)
    file_inode_num = find_entry(f, subdir_inode, filename.encode(), filename_length)
    if file_inode_num is None:
        print(
            f"Error: File '{filename}' not found in directory '{dirname}'",
            file=sys.stderr,
        )
        sys.exit(1)

    return read_inode(f, inode_table_start, file_inode_num)


# Handling the 'touch' command
def handle_touch(f, root_inode, filename_length, sbdict, filename, inode_table_start):
    if len(filename) > filename_length:
        print(f"Error: Filename '{filename.decode()}' too long", file=sys.stderr)
        sys.exit(1)
    if find_entry(f, root_inode, filename, filename_length) is not None:
        print(f"Error: File '{filename.decode()}' already exists", file=sys.stderr)
        sys.exit(1)
    new_inode_num = allocate_inode(f, sbdict)
    if new_inode_num is None:
        print("Error: No free inodes available", file=sys.stderr)
        sys.exit(1)
    current_time = int(time.time())
    new_inode = struct.pack(
        "<HHIIBB9H",
        0o100700,  # Regular file mode with 700 permissions
        0,  # uid
        0,  # size
        current_time,  # time
        0,  # gid
        1,  # nlinks
        *([0] * 9),  # zones
    )
    write_inode(f, inode_table_start, new_inode_num, new_inode)
    add_directory_entry(
        f, root_inode, filename, new_inode_num, filename_length, inode_table_start
    )


# Handling the 'mkdir' command
def handle_mkdir(f, root_inode, filename_length, sbdict, dirname, inode_table_start):
    if len(dirname) > filename_length:
        print(f"Error: Directory name '{dirname.decode()}' too long", file=sys.stderr)
        sys.exit(1)
    if find_entry(f, root_inode, dirname, filename_length) is not None:
        print(f"Error: Directory '{dirname.decode()}' already exists", file=sys.stderr)
        sys.exit(1)
    create_directory(f, sbdict, root_inode, dirname, inode_table_start, filename_length)


# Main function to handle command line arguments and execute corresponding commands
def main():
    if len(sys.argv) < 3:
        print("Usage: mfstool.py image command params", file=sys.stderr)
        sys.exit(1)
    diskimg = sys.argv[1]
    cmd = sys.argv[2]
    with open(diskimg, "r+b") as f:
        f.seek(BLOCK_SIZE, 0)
        sbdata = f.read(BLOCK_SIZE)
        sbdict = parse_superblock(sbdata)
        inode_table_start = (2 * BLOCK_SIZE) + (
            sbdict["imap_blocks"] + sbdict["zmap_blocks"]
        ) * BLOCK_SIZE
        root_inode = read_inode(f, inode_table_start, 1)
        print(root_inode)
        filename_length = 14 if sbdict["magic"] == 0x137F else 30
        execute_command(f, cmd, inode_table_start, root_inode, filename_length, sbdict)


# Executing the given command
def execute_command(f, cmd, inode_table_start, root_inode, filename_length, sbdict):
    if cmd == "ls":
        handle_ls(f, root_inode, filename_length)
    elif cmd == "cat":
        if len(sys.argv) != 4:
            print("Usage: mfstool.py image cat [dirname1/]filename1", file=sys.stderr)
            sys.exit(1)
        path = sys.argv[3].split("/")
        handle_cat(f, inode_table_start, root_inode, filename_length, path)
    elif cmd == "touch":
        if len(sys.argv) != 4:
            print("Usage: mfstool.py image touch filename1", file=sys.stderr)
            sys.exit(1)
        filename = sys.argv[3].encode()
        handle_touch(
            f, root_inode, filename_length, sbdict, filename, inode_table_start
        )
    elif cmd == "mkdir":
        if len(sys.argv) != 4:
            print("Usage: mfstool.py image mkdir dirname1", file=sys.stderr)
            sys.exit(1)
        dirname = sys.argv[3].encode()
        handle_mkdir(f, root_inode, filename_length, sbdict, dirname, inode_table_start)


if __name__ == "__main__":
    main()
