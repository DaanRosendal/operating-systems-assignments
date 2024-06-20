"""
- Name: Daan Rosendal
- Student number: 15229394
- Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating Systems
  as a "bijvak".

This script compares the round robin, memory efficient, and priority scheduling algorithms for
different problem sizes and configurations. The algorithms are tested with specific parameters and
the average processing time is extracted from the output.
"""

import subprocess
import re

def run_algorithm(algorithm, params):
    command = f"./{algorithm} {' '.join(['-' + k + ' ' + str(v) for k, v in params.items()])}"
    output = subprocess.check_output(command, shell=True, universal_newlines=True)
    return output

def parse_output(output):
    statistics = {}
    matches = re.findall(r'Gemiddelde waarde:\s+([\d.]+)', output)
    if matches:
        statistics['gemiddelde'] = float(matches[0])
    matches = re.findall(r'Minimum waarde:\s+([\d.]+)', output)
    if matches:
        statistics['minimum'] = float(matches[0])
    matches = re.findall(r'Maximum waarde:\s+([\d.]+)', output)
    if matches:
        statistics['maximum'] = float(matches[0])
    # Add more statistics to parse as needed
    return statistics

def compare_algorithms(algorithms, params):
    results = {}
    for algorithm in algorithms:
        output = run_algorithm(algorithm, params)
        statistics = parse_output(output)
        results[algorithm] = statistics
    return results

if __name__ == "__main__":
    algorithms = ['rr', 'mem', 'adv']
    params = {'c': 0.5, 'i': 0.5, 'm': 0.5, 'p': 10000}
    results = compare_algorithms(algorithms, params)
    for algorithm, statistics in results.items():
        print(f"Algorithm: {algorithm}")
        print(statistics)
