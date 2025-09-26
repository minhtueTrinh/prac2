import subprocess
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
from pathlib import Path

class MemoryAnalyser:
    def __init__(self):
        self.traces = ['bzip', 'gcc', 'sixpack', 'swim']
        self.algorithms = ['clock', 'lru', 'rand']
        self.algorithm_names = {'clock': 'Clock', 'lru': 'LRU', 'rand': 'Random'}
        self.colors = {'clock': '#1f77b4', 'lru': '#ff7f0e', 'rand': '#2ca02c'}
        self.markers = {'clock': 'o', 'lru': 's', 'rand': '^'}
        
    def run_simulation(self, trace_file, frames, algorithm, debug_mode='quiet'):
        """Run the memory simulator and parse results"""
        try:
            cmd = ['python', 'memsim.py', trace_file, str(frames), algorithm, debug_mode]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                print(f"Error running simulation: {result.stderr}")
                return None
                
            # Parse output
            lines = result.stdout.strip().split('\n')
            results = {}
            
            for line in lines:
                if 'total memory frames:' in line:
                    results['frames'] = int(line.split(':')[1].strip())
                elif 'events in trace:' in line:
                    results['events'] = int(line.split(':')[1].strip())
                elif 'total disk reads:' in line:
                    results['disk_reads'] = int(line.split(':')[1].strip())
                elif 'total disk writes:' in line:
                    results['disk_writes'] = int(line.split(':')[1].strip())
                elif 'page fault rate:' in line:
                    results['fault_rate'] = float(line.split(':')[1].strip())
                    
            return results
            
        except subprocess.TimeoutExpired:
            print(f"Simulation timed out for {trace_file} with {frames} frames")
            return None
        except Exception as e:
            print(f"Error running simulation: {e}")
            return None
    
    def find_optimal_frame_ranges(self):
        """Find appropriate frame ranges for each trace by testing with a wide range"""
        print("Finding optimal frame ranges for each trace...")
        frame_ranges = {}
        
        # Test with a wide range to find the "knee" of the curve
        test_frames = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192]
        
        for trace in self.traces:
            trace_file = f"{trace}.trace"
            if not os.path.exists(trace_file):
                print(f"Warning: {trace_file} not found, using default range")
                frame_ranges[trace] = list(range(1, 101, 5))
                continue
                
            print(f"  Testing {trace}...")
            fault_rates = []
            valid_frames = []
            
            # Use LRU as reference algorithm for finding ranges
            for frames in test_frames:
                result = self.run_simulation(trace_file, frames, 'lru')
                if result:
                    fault_rates.append(result['fault_rate'])
                    valid_frames.append(frames)
            
            if not fault_rates:
                frame_ranges[trace] = list(range(1, 101, 5))
                continue
            
            # Find where fault rate drops significantly (working set size)
            working_set_size = valid_frames[0]  # Start with minimum
            for i in range(1, len(fault_rates)):
                if fault_rates[i] < 0.1:  # Less than 10% fault rate
                    working_set_size = valid_frames[i]
                    break
            
            # Create a range from low memory (stress) to high memory (comfortable)
            min_frames = max(1, valid_frames[0])
            max_frames = min(working_set_size * 3, valid_frames[-1])
            
            # Create a logarithmic-like distribution for better resolution
            if max_frames <= 50:
                step = 2
            elif max_frames <= 200:
                step = 5
            else:
                step = max(10, max_frames // 40)
                
            frame_range = list(range(min_frames, max_frames + 1, step))
            
            # Add some specific points of interest
            if working_set_size not in frame_range:
                frame_range.append(working_set_size)
            if working_set_size // 2 not in frame_range:
                frame_range.append(working_set_size // 2)
                
            frame_ranges[trace] = sorted(frame_range)
            print(f"    Range for {trace}: {min(frame_range)} to {max(frame_range)} frames (working set ~{working_set_size})")
            
        return frame_ranges
    
    def collect_data(self, frame_ranges=None):
        """Collect performance data for all combinations"""
        if frame_ranges is None:
            frame_ranges = self.find_optimal_frame_ranges()
        
        data = {}
        total_runs = sum(len(frame_ranges[trace]) * len(self.algorithms) for trace in self.traces)
        current_run = 0
        
        print(f"Collecting data for {total_runs} simulation runs...")
        
        for trace in self.traces:
            trace_file = f"{trace}.trace"
            if not os.path.exists(trace_file):
                print(f"Warning: {trace_file} not found, skipping...")
                continue
                
            data[trace] = {}
            
            for algorithm in self.algorithms:
                data[trace][algorithm] = {
                    'frames': [],
                    'fault_rates': [],
                    'disk_reads': [],
                    'disk_writes': [],
                    'total_io': []
                }
                
                for frames in frame_ranges[trace]:
                    current_run += 1
                    print(f"  Progress: {current_run}/{total_runs} - {trace} {algorithm} {frames} frames", end='\r')
                    
                    result = self.run_simulation(trace_file, frames, algorithm)
                    if result:
                        data[trace][algorithm]['frames'].append(frames)
                        data[trace][algorithm]['fault_rates'].append(result['fault_rate'])
                        data[trace][algorithm]['disk_reads'].append(result['disk_reads'])
                        data[trace][algorithm]['disk_writes'].append(result['disk_writes'])
                        data[trace][algorithm]['total_io'].append(result['disk_reads'] + result['disk_writes'])
        
        print("\nData collection complete!")
        return data
    
    def create_individual_graphs(self, data):
        """Create individual performance graphs for each trace"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for i, trace in enumerate(self.traces):
            if trace not in data:
                continue
                
            ax = axes[i]
            
            for algorithm in self.algorithms:
                if algorithm in data[trace] and data[trace][algorithm]['frames']:
                    frames = data[trace][algorithm]['frames']
                    fault_rates = data[trace][algorithm]['fault_rates']
                    
                    ax.plot(frames, fault_rates, 
                           color=self.colors[algorithm],
                           marker=self.markers[algorithm],
                           markersize=6,
                           linewidth=2,
                           label=self.algorithm_names[algorithm],
                           alpha=0.8)
            
            ax.set_xlabel('Number of Frames')
            ax.set_ylabel('Page Fault Rate')
            ax.set_title(f'{trace.upper()} Memory Trace')
            ax.grid(True, alpha=0.3)
            ax.legend()
            ax.set_ylim(0, 1.05)
            
            # Add some context annotations
            if trace in data and self.algorithms[0] in data[trace]:
                max_frames = max(data[trace][self.algorithms[0]]['frames']) if data[trace][self.algorithms[0]]['frames'] else 0
                if max_frames > 0:
                    # Find working set size (where fault rate drops below 0.1)
                    for alg in self.algorithms:
                        if alg in data[trace]:
                            frames_list = data[trace][alg]['frames']
                            fault_list = data[trace][alg]['fault_rates']
                            for j, fault_rate in enumerate(fault_list):
                                if fault_rate < 0.1 and j < len(frames_list):
                                    ax.axvline(x=frames_list[j], color='red', linestyle='--', alpha=0.5)
                                    ax.text(frames_list[j], 0.5, f'~{frames_list[j]} frames\n(working set)', 
                                           rotation=90, verticalalignment='center', fontsize=8)
                                    break
                            break
        
        plt.tight_layout()
        plt.savefig('individual_trace_performance.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_comparison_graph(self, data):
        """Create a comparison graph showing all traces for one metric"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Page Fault Rate Comparison
        ax1 = axes[0, 0]
        for trace in self.traces:
            if trace in data and 'lru' in data[trace]:
                frames = data[trace]['lru']['frames']
                fault_rates = data[trace]['lru']['fault_rates']
                ax1.plot(frames, fault_rates, marker='o', label=trace.upper(), linewidth=2)
        ax1.set_xlabel('Number of Frames')
        ax1.set_ylabel('Page Fault Rate')
        ax1.set_title('LRU Algorithm: Fault Rate by Trace')
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_ylim(0, 1.05)
        
        # Algorithm comparison for one trace (pick the first available)
        available_trace = None
        for trace in self.traces:
            if trace in data:
                available_trace = trace
                break
        
        if available_trace:
            ax2 = axes[0, 1]
            for algorithm in self.algorithms:
                if algorithm in data[available_trace]:
                    frames = data[available_trace][algorithm]['frames']
                    fault_rates = data[available_trace][algorithm]['fault_rates']
                    ax2.plot(frames, fault_rates, 
                            color=self.colors[algorithm],
                            marker=self.markers[algorithm],
                            label=self.algorithm_names[algorithm],
                            linewidth=2)
            ax2.set_xlabel('Number of Frames')
            ax2.set_ylabel('Page Fault Rate')
            ax2.set_title(f'Algorithm Comparison: {available_trace.upper()}')
            ax2.grid(True, alpha=0.3)
            ax2.legend()
            ax2.set_ylim(0, 1.05)
        
        # Disk I/O comparison
        ax3 = axes[1, 0]
        for trace in self.traces:
            if trace in data and 'lru' in data[trace]:
                frames = data[trace]['lru']['frames']
                total_io = data[trace]['lru']['total_io']
                ax3.plot(frames, total_io, marker='s', label=trace.upper(), linewidth=2)
        ax3.set_xlabel('Number of Frames')
        ax3.set_ylabel('Total Disk I/O Operations')
        ax3.set_title('LRU Algorithm: Total I/O by Trace')
        ax3.grid(True, alpha=0.3)
        ax3.legend()
        ax3.set_yscale('log')
        
        # Working set analysis
        ax4 = axes[1, 1]
        working_sets = []
        trace_names = []
        for trace in self.traces:
            if trace in data and 'lru' in data[trace]:
                frames_list = data[trace]['lru']['frames']
                fault_list = data[trace]['lru']['fault_rates']
                working_set = frames_list[-1]  # Default to max
                for j, fault_rate in enumerate(fault_list):
                    if fault_rate < 0.1:
                        working_set = frames_list[j]
                        break
                working_sets.append(working_set)
                trace_names.append(trace.upper())
        
        if working_sets:
            bars = ax4.bar(trace_names, working_sets, color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'])
            ax4.set_ylabel('Estimated Working Set Size (Frames)')
            ax4.set_title('Working Set Size Comparison')
            ax4.grid(True, alpha=0.3, axis='y')
            
            # Add value labels on bars
            for bar, value in zip(bars, working_sets):
                height = bar.get_height()
                ax4.text(bar.get_x() + bar.get_width()/2., height,
                        f'{value}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('comparison_analysis.png', dpi=300, bbox_inches='tight')
        plt.show()
    
    def create_summary_table(self, data):
        """Create a summary table of key metrics"""
        print("\n" + "="*80)
        print("SUMMARY ANALYSIS")
        print("="*80)
        
        for trace in self.traces:
            if trace not in data:
                continue
                
            print(f"\n{trace.upper()} TRACE:")
            print("-" * 40)
            
            # Find working set size (fault rate < 0.1)
            working_set = "Unknown"
            min_fault_rate = 1.0
            best_algorithm = "Unknown"
            
            for algorithm in self.algorithms:
                if algorithm in data[trace] and data[trace][algorithm]['frames']:
                    frames_list = data[trace][algorithm]['frames']
                    fault_list = data[trace][algorithm]['fault_rates']
                    
                    # Find working set
                    for j, fault_rate in enumerate(fault_list):
                        if fault_rate < 0.1:
                            if working_set == "Unknown":
                                working_set = f"~{frames_list[j]} frames"
                            break
                    
                    # Find best algorithm at low memory
                    if len(fault_list) > 0 and fault_list[0] < min_fault_rate:
                        min_fault_rate = fault_list[0]
                        best_algorithm = self.algorithm_names[algorithm]
            
            print(f"  Estimated working set size: {working_set}")
            print(f"  Best algorithm under memory pressure: {best_algorithm}")
            
            # Performance at different memory levels
            for algorithm in self.algorithms:
                if algorithm in data[trace] and data[trace][algorithm]['frames']:
                    frames_list = data[trace][algorithm]['frames']
                    fault_list = data[trace][algorithm]['fault_rates']
                    
                    if len(fault_list) >= 3:
                        low_mem = fault_list[0]
                        mid_mem = fault_list[len(fault_list)//2]
                        high_mem = fault_list[-1]
                        
                        print(f"  {self.algorithm_names[algorithm]:8} - Low mem: {low_mem:.3f}, Mid mem: {mid_mem:.3f}, High mem: {high_mem:.3f}")
    
    def run_full_analysis(self):
        """Run the complete analysis"""
        print("Starting Memory Management Performance Analysis")
        print("=" * 50)
        
        # Check if trace files exist
        missing_files = []
        for trace in self.traces:
            if not os.path.exists(f"{trace}.trace"):
                missing_files.append(f"{trace}.trace")
        
        if missing_files:
            print("Missing trace files:")
            for file in missing_files:
                print(f"  - {file}")
            print("\nPlease ensure all trace files are in the current directory.")
            return
        
        # Collect data
        data = self.collect_data()
        
        if not data:
            print("No data collected. Please check your trace files and simulator.")
            return
        
        # Create visualizations
        print("\nCreating visualisations...")
        self.create_individual_graphs(data)
        self.create_comparison_graph(data)
        self.create_summary_table(data)
        
        print("\nAnalysis complete!")
        print("Generated files:")
        print("  - individual_trace_performance.png")
        print("  - comparison_analysis.png")

# Usage example
if __name__ == "__main__":
    analyzer = MemoryAnalyser()
    analyzer.run_full_analysis()