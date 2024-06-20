# Operating Systems Assignments

This repository contains three projects that I completed for my Operating Systems class as part of the Computer Science curriculum at the University of Amsterdam. The projects are as follows:

- [Project 1: Shell](#project-1-shell)
- [Project 2: CPU Scheduling](#project-2-cpu-scheduling)
- [Project 3: File System](#project-3-file-system)

Each project has its own directory containing its source code and any relevant documentation. The projects were written in C and Python, and the documentation was written in LaTeX. The projects were graded by the course instructors, and the grades are mentioned in the respective project sections below.

## Project 1: Shell

The goal of this project was to implement a shell program that can execute commands and manage processes. The shell supports the following features:

- Simple commands, e.g., `exit` and `cd`
- Sequences of commands
- Pipes
- CTRL-C handling
- Detached commands
- Environment variables
- Subshells
- Redirections

The [shell.c](./1-shell/shell.c) file contains the main source code for the shell.

My grade for this project was 10/10.

## Project 2: CPU Scheduling

The goal of this project was to implement several CPU scheduling algorithms and compare their performance in a [research paper](./2-cpu-scheduling/report.pdf). The scheduling algorithms that were implemented and evaluated are as follows:

- First-Come, First-Served (FCFS)
- FCFS with an optimal N-tries value
- Round Robin (RR)
- RR with improved memory efficiency
- Priority Scheduling

The [cpu-scheduling](./2-cpu-scheduling) directory contains the source code for the scheduling algorithms, as well as the [research paper](./2-cpu-scheduling/report.pdf) that compares the performance of the algorithms.

My grade for this project was 9.7/10.

## Project 3: File System

The goal of this project was to implement various commands to manage a MINIX file system. The file system supports the following features:

- Listing files in a directory (`ls`)
- Reading a file (`cat`)
- Creating a new file (`touch`)
- Creating a new directory (`mkdir`)

The [mfstool.py](./3-file-system/mfstool.py) file contains the main source code for the file system.

My grade for this project was 8/10.

## License

This repository is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more information.
