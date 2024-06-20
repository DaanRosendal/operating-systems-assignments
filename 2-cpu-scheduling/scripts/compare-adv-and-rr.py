"""
- Name: Daan Rosendal
- Student number: 15229394
- Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating Systems
  as a "bijvak".

This script compares the priority scheduling algorithm with the round robin algorithm for different
problem sizes (linearly spaced).
"""

import subprocess
import re
import numpy as np

# Function to run the advanced algorithm with specific parameters and extract average processing time
def run_advanced_simulation(aging_time_interval, aging_factor, p_value):
    command = ['./bin/priority', '-c', '0.5', '-i', '0.5', '-m', '0.5', '-p', str(p_value)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    input_data = f"{aging_time_interval}\n{aging_factor}\n"
    stdout, stderr = process.communicate(input=input_data.encode())

    # Extract the "Gemiddelde waarde" from the "totale verwerkingstijd" section
    match = re.search(r"totale verwerkingstijd.*Gemiddelde waarde:\s+(\d+\.\d+)", stdout.decode(), re.DOTALL)
    if match:
        return float(match.group(1))
    else:
        return float('inf')

# Function to run the round-robin algorithm with specific parameters and extract average processing time
def run_round_robin_simulation(p_value):
    command = ['./bin/round-robin', '-c', '0.5', '-i', '0.5', '-m', '0.5', '-p', str(p_value)]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # Extract the "Gemiddelde waarde" from the "totale verwerkingstijd" section
    match = re.search(r"totale verwerkingstijd.*Gemiddelde waarde:\s+(\d+\.\d+)", stdout.decode(), re.DOTALL)
    if match:
        return float(match.group(1))
    else:
        return float('inf')

# Generate linearly spaced values between 100 and 40960
def generate_linear_space_values(start, stop, num_values):
    return np.linspace(start, stop, num_values, dtype=int).tolist()

# Function to compare the two algorithms across different problem sizes and configurations
def compare_algorithms(p_values):
    results = []

    # Define different configurations for the advanced algorithm
    advanced_configs = [
        {'aging_time_interval': 2, 'aging_factor': 10, 'name': 'Advanced (t=2, a=10)'},
        # {'aging_time_interval': 3, 'aging_factor': 11, 'name': 'Advanced (t=3, a=11)'}
    ]

    for p_value in p_values:
        # Collect results for each advanced configuration
        advanced_results = {}
        for config in advanced_configs:
            avg_advanced = run_advanced_simulation(config['aging_time_interval'], config['aging_factor'], p_value)
            advanced_results[config['name']] = avg_advanced

        # Get the round-robin results
        avg_round_robin = run_round_robin_simulation(p_value)

        # Store the results
        results.append((p_value, advanced_results, avg_round_robin))

        # Print progress
        print(f"Problem Size (-p): {p_value}, {', '.join([f'{k}: {v}' for k, v in advanced_results.items()])}, Round Robin Avg Processing Time: {avg_round_robin}")

    # Sort results by problem size
    results.sort(key=lambda x: x[0])

    return results

# Define the problem sizes between 100 and 40960 using linear spacing
p_values = generate_linear_space_values(100, 40960, 20)

# Compare the algorithms
results = compare_algorithms(p_values)

# Print the results in a formatted way
header = f"{'Problem Size (-p)':<15}"
for config in ['Advanced (t=2, a=10)', 'Round Robin']:
    header += f"{config:<25}"
print("\nComparison Results (Problem Size vs Avg Processing Time for Multiple Configurations):")
print(header)
for result in results:
    result_str = f"{result[0]:<15}"
    for config_name, avg_time in result[1].items():
        result_str += f"{avg_time:<25}"
    result_str += f"{result[2]:<25}"
    print(result_str)
