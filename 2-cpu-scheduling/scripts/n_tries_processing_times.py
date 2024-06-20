"""
- Name: Daan Rosendal
- Student number: 15229394
- Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating Systems
  as a "bijvak".

This script runs the n_tries algorithm with different memory allocations and captures the average
total processing time for each run.
"""

import subprocess
import re

# Define the parameters for the command
cpu = 0.5
io = 0.5
mem_values = [0.1, 0.3, 0.5, 0.7, 0.9]
num_runs = 30
processes = 50000

# Define the base command template
base_command = "./bin/ntries -c {cpu} -i {io} -m {mem} -p {processes}"

# Function to run the command and capture specific average total processing time
def run_command(mem):
    results = []
    for n in range(1, num_runs + 1):
        command = base_command.format(cpu=cpu, io=io, mem=mem, processes=processes)
        try:
            # Start the process
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)
            # Send n_tries value to stdin automatically
            stdout, stderr = proc.communicate(input=f'{n}\n'.encode())
            output = stdout.decode()

            # Parse output to find the correct average total processing time
            target_section = False
            for line in output.split('\n'):
                if 'Histogram en statistieken van totale verwerkingstijd' in line:
                    target_section = True
                if target_section and 'Gemiddelde waarde:' in line:
                    avg_time = float(line.split(':')[1].strip().split(',')[0])
                    results.append((n, avg_time))
                    break
        except Exception as e:
            print(f"An error occurred: {e}")
    return results

# Collect and print results for each memory allocation parameter
all_results = {}
for mem in mem_values:
    results = run_command(mem)
    all_results[mem] = results
    print(f"Results for -m {mem}: {results}")

# Optionally, output results to a file or handle them further
