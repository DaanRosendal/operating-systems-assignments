"""
- Name: Daan Rosendal
- Student number: 15229394
- Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating Systems
  as a "bijvak".

This script generates a graph comparing the memory utilisation of the round robin and memory
efficient round robin algorithms for different goal memory usage values.
"""

import subprocess
import re
import matplotlib.pyplot as plt
from tabulate import tabulate

# Function to run the specified command with given memory parameter and extract memory utilization from its output
def run_command(command, memory_param):
    # Adjust the command with the provided memory parameter
    command = f"{command} -m {memory_param}"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, _ = process.communicate()
    output = output.decode('utf-8')
    # Extract memory utilization value from the output
    memory_utilization_match = re.search(r'Gemiddeld gebruik geheugen:\s+(\d+)\s+woorden,\s+utilisatie\s+([\d.]+)', output)
    if memory_utilization_match:
        return float(memory_utilization_match.group(2))
    else:
        return None

# Function to run the command specified number of times with given memory parameter and return the average memory utilization
def get_average_memory_utilization(command, memory_param, num_iterations):
    total_memory_utilization = 0
    for _ in range(num_iterations):
        memory_utilization = run_command(command, memory_param)
        if memory_utilization is not None:
            total_memory_utilization += memory_utilization
        else:
            # Handle case where memory utilization couldn't be extracted
            print("Failed to extract memory utilization from output.")
    return total_memory_utilization / num_iterations

# Main function
def main():
    # Commands to run
    mem_command = "./mem -c 0.5 -i 0.5 -p 10000"
    rr_command = "./rr -c 0.5 -i 0.5 -p 10000"

    # Memory parameters to try
    memory_params = [0.1, 0.3, 0.5, 0.7, 0.9]

    # Number of iterations for each algorithm
    num_iterations = 20

    # Lists to store results
    mem_average_utilizations = []
    rr_average_utilizations = []
    percentage_improvements = []

    print("Comparing memory utilization for different memory parameters:")
    for memory_param in memory_params:
        # Get average memory utilization for memory efficient algorithm with current memory parameter
        mem_average_utilization = get_average_memory_utilization(mem_command, memory_param, num_iterations)
        mem_average_utilizations.append(mem_average_utilization)

        # Get average memory utilization for round robin algorithm with current memory parameter
        rr_average_utilization = get_average_memory_utilization(rr_command, memory_param, num_iterations)
        rr_average_utilizations.append(rr_average_utilization)

        # Calculate percentage improvement
        percentage_improvement = ((mem_average_utilization - rr_average_utilization) / rr_average_utilization) * 100
        percentage_improvements.append(percentage_improvement)

    # Print the table
    table_data = []
    for i, memory_param in enumerate(memory_params):
        table_data.append([memory_param, mem_average_utilizations[i], rr_average_utilizations[i], percentage_improvements[i]])

    headers = ["Memory Parameter", "Memory Efficient Avg", "Round Robin Avg", "Percentage Improvement (%)"]
    print(tabulate(table_data, headers=headers, floatfmt=".2f", numalign="right"))

    # Plotting the results
    plt.figure(figsize=(10, 6))

    # Bar width
    bar_width = 0.35

    # X-axis values
    x = range(len(memory_params))

    # Plot memory utilizations
    mem_bars = plt.bar(x, mem_average_utilizations, width=bar_width, label='Memory Efficient Algorithm')
    rr_bars = plt.bar([i + bar_width for i in x], rr_average_utilizations, width=bar_width, label='Round Robin Algorithm')

    # X-axis labels
    plt.xlabel('Memory Parameter', fontsize=12)
    plt.xticks([i + bar_width / 2 for i in x], memory_params)

    # Y-axis label
    plt.ylabel('Average Memory Utilization', fontsize=12)

    # Title
    plt.title('Comparison of Memory Utilization for Different Memory Parameters', fontsize=14)

    # Add legend
    plt.legend()

    # Annotate bars with percentage improvements
    for i, (mem_bar, rr_bar) in enumerate(zip(mem_bars, rr_bars)):
        plt.text(mem_bar.get_x() + mem_bar.get_width() / 2, mem_bar.get_height(), f"+{percentage_improvements[i]:.2f}%", ha='center', va='bottom')
        # plt.text(rr_bar.get_x() + rr_bar.get_width() / 2, rr_bar.get_height(), f"{percentage_improvements[i]:.2f}%", ha='center', va='bottom')

    # Show plot
    plt.savefig('./scripts/memory_utilization_comparison.png')

if __name__ == "__main__":
    main()
