"""
- Name: Daan Rosendal
- Student number: 15229394
- Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating Systems
  as a "bijvak".

This script runs the priority scheduling algorithm with aging measurements for different time slices
and aging factors.
"""

import subprocess
import re

# Function to run the command with specific parameters and extract average processing time
def run_simulation(time_slice, aging_factor):
    command = ['./bin/priority', '-c', '0.5', '-i', '0.5', '-m', '0.5', '-p', '100']
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    input_data = f"{time_slice}\n{aging_factor}\n"
    stdout, stderr = process.communicate(input=input_data.encode())

    # Extract the "Gemiddelde waarde" from the "totale verwerkingstijd" section
    match = re.search(r"totale verwerkingstijd.*Gemiddelde waarde:\s+(\d+\.\d+)", stdout.decode(), re.DOTALL)
    if match:
        return float(match.group(1))
    else:
        return float('inf')

# Try different combinations of time slices and aging factors
def find_best_configurations(time_slice_range, aging_factor_range):
    configurations = []

    for time_slice in time_slice_range:
        for aging_factor in aging_factor_range:
            avg_processing_time = run_simulation(time_slice, aging_factor)
            print(f"Time Slice: {time_slice}, Aging Factor: {aging_factor}, Avg Processing Time: {avg_processing_time}")

            configurations.append((time_slice, aging_factor, avg_processing_time))

    # Sort configurations by average processing time
    configurations.sort(key=lambda x: x[2])

    # Return the top 20 configurations
    return configurations[:20]

# Define ranges
time_slice_range = range(1, 8)
aging_factor_range = range(1, 15)

# Find the best configurations
best_configurations = find_best_configurations(time_slice_range, aging_factor_range)

# Print the 20 best configurations
print("\nTop 20 Best Configurations with the Lowest Total Average Processing Time:")
for config in best_configurations:
    print(f"Time Slice: {config[0]}, Aging Factor: {config[1]}, Avg Processing Time: {config[2]}")
