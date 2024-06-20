"""
- Name: Daan Rosendal
- Student number: 15229394
- Study: Bachelor HBO-ICT (Software Engineering) at Windesheim in Zwolle. I follow Operating Systems
  as a "bijvak".

This script generates a graph comparing the memory utilisation of the round robin and memory
efficient round robin algorithms for different goal memory usage values.
"""

import matplotlib.pyplot as plt

# Data
memory_params = [0.1, 0.3, 0.5, 0.7, 0.9]
round_robin_values = [0.1090, 0.3112, 0.4498, 0.5418, 0.6053]
memory_efficient_final_values = [0.1216, 0.3302, 0.4790, 0.5690, 0.6331]

# Calculate the differences in percentage
final_percentage_differences = [
    (memory_efficient_final_values[i] - round_robin_values[i]) / round_robin_values[i] * 100
    for i in range(len(memory_params))
]

# Creating the figure and the plot
fig, ax = plt.subplots()
width = 0.03  # Width of the bars

# Setting positions for the two sets of bars
rr_positions = [x for x in memory_params]
me_positions = [x + width for x in memory_params]

# Plotting Round Robin and Memory Efficient Round Robin bars
ax.bar(rr_positions, round_robin_values, width, label='Round Robin', color='orange')
ax.bar(me_positions, memory_efficient_final_values, width, label='Memory Efficient Round Robin', color='blue')

# Adding percentage difference labels above bars
for i in range(len(memory_params)):
    diff = (memory_efficient_final_values[i] - round_robin_values[i]) / round_robin_values[i] * 100
    ax.text(me_positions[i], max(round_robin_values[i], memory_efficient_final_values[i]) + 0.01, f'+{diff:.2f}%', ha='center')

# Setting labels and titles
ax.set_xlabel('Goal Memory Usage')
ax.set_ylabel('Average Memory Utilisation')
ax.set_title('Memory Utilisation Comparison for Memory Efficient Round Robin')
ax.set_xticks([x + width / 2 for x in memory_params])
ax.set_xticklabels([f'{x:.1f}' for x in memory_params])

# Adding a legend
ax.legend()

# Show and save the plot
plt.show()
plt.savefig('Memory_Utilisation_Comparison.png')
