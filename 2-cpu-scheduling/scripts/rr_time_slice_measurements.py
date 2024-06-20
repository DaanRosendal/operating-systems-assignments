"""
- Name: Daan Rosendal
- Student number: 15229394
- Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating Systems
  as a "bijvak".

This file contains a script that runs the round-robin algorithm with different time slice values and
extracts the total processing time, waiting time, and CPU utilisation from the output. The script
prints the results in a table format.
"""

import subprocess
import re

def run_command(time_slice):
    # Command setup
    command = ['./bin/round-robin', '-c', '0.5', '-i', '0.5', '-m', '0.5', '-p', '50000']
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    # Sending time slice value to the command
    output, _ = process.communicate(input=str(time_slice))

    return output

def extract_stats(output):
    # Regex to extract the required statistics
    total_processing_time_pattern = r"Histogram en statistieken van totale verwerkingstijd.*?Gemiddelde waarde:\s+(\d+\.\d+)"
    waiting_time_pattern = r"Histogram en statistieken van wachttijd op eerste CPU cycle.*?Gemiddelde waarde:\s+(\d+\.\d+)"
    cpu_utilisation_pattern = r"Gebruikte CPU-tijd:.*?CPU utilisatie:\s+(\d+\.\d+)"

    total_processing_time = re.search(total_processing_time_pattern, output, re.S)
    waiting_time = re.search(waiting_time_pattern, output, re.S)
    cpu_utilisation = re.search(cpu_utilisation_pattern, output, re.S)

    return (
        float(total_processing_time.group(1)) if total_processing_time else None,
        float(waiting_time.group(1)) if waiting_time else None,
        float(cpu_utilisation.group(1)) if cpu_utilisation else None
    )

def main():
    print(f"Time Slice | Total Processing Time | Waiting Time | CPU Utilisation")
    print("-" * 60)

    for time_slice in range(1, 101):
        output = run_command(time_slice)
        tpt, wt, cpu = extract_stats(output)
        print(f"{time_slice:>10} | {tpt:>20} | {wt:>12} | {cpu:>15}")

if __name__ == '__main__':
    main()
