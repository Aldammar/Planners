import os
from matplotlib import ticker
from matplotlib.ticker import LogLocator, NullFormatter
import pandas as pd
import matplotlib.pyplot as plt
import argparse

def plot_csv_data(file_paths, labels, output_dir, root_dir, phases):
    # Initialize lists to store pkg and dram values for each phase
    phase_data = {phase: {'pkg_values': [], 'dram_values': [], 'duration_values': []} for phase in phases}
    
    for file_path in file_paths:
        # Read the CSV file
        data = pd.read_csv(file_path)

        for phase in phases:
            row_number_of_phase = data.index[data['label'] == phase].tolist().pop()

            # Summarize the pkg and dram values
            pkg = data['pkg'].values[row_number_of_phase] / 1_000_000  # Convert micro joules to joules
            dram = data['dram'].values[row_number_of_phase] / 1_000_000  # Convert micro joules to joules
            duration = data['duration'].values[row_number_of_phase] / 1_000_000  # Convert micro seconds to seconds

            phase_data[phase]['pkg_values'].append(pkg)
            phase_data[phase]['dram_values'].append(dram)
            phase_data[phase]['duration_values'].append(duration)
    
    # Plotting
    x = range(len(labels))
    bar_width = 0.2
    
    fig, axs = plt.subplots(len(phases), 1, figsize=(10, 4 * len(phases)), sharex=True)

    for ax, phase in zip(axs, phases):
        pkg_values = phase_data[phase]['pkg_values']
        dram_values = phase_data[phase]['dram_values']
        duration_values = phase_data[phase]['duration_values']

        # Plot pkg and dram values with logarithmic scale
        pkg_bars = ax.bar([i - bar_width/2 for i in x], pkg_values, width=bar_width, label='pkg (CPU)', color='blue')
        dram_bars = ax.bar([i + bar_width/2 for i in x], dram_values, width=bar_width, label='dram (RAM)', color='green')

        # Add values above the bars
        for bar in pkg_bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2 - 0.11, yval, round(yval, 2), ha='center', va='bottom', color='blue')
        
        for bar in dram_bars:
            yval = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2 + 0.11, yval, round(yval, 2), ha='center', va='bottom', color='green')

        ax.set_ylabel('Energy (joules)')
        ax.set_title(phase)
        ax.legend(loc='upper left', bbox_to_anchor=(0, 0.91))
        
        # Create secondary y-axis for duration with logarithmic scale
        ax2 = ax.twinx()
        ax2.plot(x, duration_values, label='duration (seconds)', color='black', marker='o', alpha=0.3)
        ax2.set_ylabel('Time (seconds)')
        
        ax2.legend(loc='upper left',bbox_to_anchor=(0, 1))
    
    axs[-1].set_xlabel('Problem Instances')
    axs[-1].set_xticks(x)
    axs[-1].set_xticklabels(labels, rotation=45, ha='right')
    
    plt.tight_layout()

    # Save the plot
    domain_name = os.path.dirname(root_dir)
    planner_name = os.path.basename(os.path.dirname(os.path.abspath(__file__)))
    output_file = os.path.join(output_dir, f'{planner_name}_{domain_name}.png')
    
    plt.savefig(output_file)
    plt.close()
    
    # Create a new plot for the sum of phases
    sum_pkg_values = [sum(phase_data[phase]['pkg_values'][i] for phase in phases) for i in range(len(labels))]
    sum_dram_values = [sum(phase_data[phase]['dram_values'][i] for phase in phases) for i in range(len(labels))]
    sum_duration_values = [sum(phase_data[phase]['duration_values'][i] for phase in phases) for i in range(len(labels))]

    fig, ax = plt.subplots(figsize=(10, 4))

    # Plot pkg and dram values with logarithmic scale
    pkg_bars = ax.bar([i - bar_width/2 for i in x], sum_pkg_values, width=bar_width, label='pkg (CPU)', color='blue')
    dram_bars = ax.bar([i + bar_width/2 for i in x], sum_dram_values, width=bar_width, label='dram (RAM)', color='green')

    # Add values above the bars
    for bar in pkg_bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2 - 0.11, yval, round(yval, 2), ha='center', va='bottom', color='blue')

    for bar in dram_bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2 + 0.11, yval, round(yval, 2), ha='center', va='bottom', color='green')

    ax.set_ylabel('Energy (joules)')
    ax.set_title('All Phases')
    ax.legend(loc='upper left', bbox_to_anchor=(0, 0.91))
    
    # Create secondary y-axis for duration with logarithmic scale
    ax2 = ax.twinx()
    ax2.plot(x, sum_duration_values, label='duration (seconds)', color='black', marker='o',alpha=0.3)
    ax2.set_ylabel('Time (seconds)')
    
    ax2.legend(loc='upper left',bbox_to_anchor=(0, 1))
    
    ax.set_xlabel('Problem Instances')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    
    plt.tight_layout()

    # Save the sum plot
    sum_output_file = os.path.join(output_dir, f'{planner_name}_{domain_name}_sum.png')
    
    plt.savefig(sum_output_file)
    plt.close()

def traverse_and_plot(root_dir):
    #print(root_dir)
    output_dir = os.path.join(root_dir, f'plots_{root_dir}')
    os.makedirs(output_dir, exist_ok=True)

    file_paths = []
    labels = []

    for subdir, _, files in sorted(os.walk(root_dir)):
        for file in sorted(files):
            if file.endswith('.csv'):
                file_path = os.path.join(subdir, file)
                file_paths.append(file_path)
                labels.append(os.path.splitext(file)[0])

    data = pd.read_csv(file_paths[0])
    phases = data['label'].values

    plot_csv_data(file_paths, labels, output_dir, root_dir, phases)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Plot CSV data.')
    parser.add_argument('directory', type=str, help='directory containing CSV files')
    args = parser.parse_args()
    root_directory = args.directory
    traverse_and_plot(root_directory)
