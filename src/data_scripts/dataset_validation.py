"""
Complete Dataset Validation Script
Validates event logs and generates comprehensive reports
"""

import pm4py
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

from pm4py.statistics.traces.generic.log import case_statistics

from repoRoot import REPO_ROOT


def seconds_to_human_readable(seconds):
    """Converts duration in seconds to human-readable format"""
    if pd.isna(seconds):
        return 'N/A'
    
    duration = timedelta(seconds=seconds)
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0 and days == 0: 
        parts.append(f"{minutes} min")
    
    if not parts:
        return f"{seconds:.2f} sec"
    
    return ", ".join(parts[:2])


class DatasetValidator:
    def __init__(self, output_dir=str(REPO_ROOT) + '/docs/data_validation'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results = {}
        
    def validate_dataset(self, csv_path, name):
        """Comprehensive validation of a single dataset"""
        print(f"\n{'='*70}")
        print(f"🔍 Validating: **{name}**")
        print('='*70)
        
        # Load and prepare data
        df = pd.read_csv(csv_path)
        df['case_id'] = df['case_id'].astype(str)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Basic statistics
        stats = {
            'total_events': len(df),
            'total_cases': df['case_id'].nunique(),
            'total_activities': df['activity'].nunique(),
            'date_range': (df['timestamp'].min(), df['timestamp'].max()),
            'activities': df['activity'].unique().tolist()
        }
        
        print(f"📊 Basic Statistics:")
        print(f"   Events: {stats['total_events']:,}")
        print(f"   Cases: {stats['total_cases']:,}")
        print(f"   Activities: {stats['total_activities']}")
        print(f"   Date Range: {stats['date_range'][0].date()} to {stats['date_range'][1].date()}")
        
        # Rename columns to PM4Py standard
        df.rename(columns={
            'case_id': 'case:concept:name',
            'activity': 'concept:name',
            'timestamp': 'time:timestamp'
        }, inplace=True)
        
        # Convert to event log
        print("\n⏳ Converting DataFrame to Event Log...")
        try:
            log = pm4py.convert_to_event_log(df)
            print("   ✅ Conversion successful.")
        except Exception as e:
            print(f"   ❌ Conversion failed: {str(e)}")
            stats['conversion_success'] = False
            return stats

        # Process Discovery
        print("\n🔍 Running Process Discovery (Inductive Miner)...")
        try:
            net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log)
            stats['discovery_success'] = True
            print("   ✅ Process model discovered successfully") 
        except Exception as e:
            print(f"   ❌ Discovery failed: {str(e)}")
            stats['discovery_success'] = False
        
        # Generate DFG visualisation (without Graphviz dependency)
        print("\n📈 Generating Process Map (DFG)...")
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as mpatches
            import math
            from matplotlib.patches import FancyArrowPatch
            
            # Discover DFG - returns tuple (dfg, start_activities, end_activities)
            dfg_result = pm4py.discover_dfg(log)
            
            # Handle both return formats (pm4py version differences)
            if isinstance(dfg_result, tuple):
                dfg_frequency = dfg_result[0]
                start_activities = dfg_result[1] if len(dfg_result) > 1 else {}
                end_activities = dfg_result[2] if len(dfg_result) > 2 else {}
            else:
                dfg_frequency = dfg_result
                start_activities = {}
                end_activities = {}
            
            # Extract unique activities
            activities = set()
            for (act1, act2), freq in dfg_frequency.items():
                activities.add(act1)
                activities.add(act2)
            
            if len(activities) == 0:
                print("   ⚠️  No activities found in DFG")
                stats['dfg_path'] = None
                return stats
            
            # Use hierarchical layout for better readability
            activities_list = list(activities)
            
            # Identify start, middle, and end activities
            start_acts = set(start_activities.keys()) if start_activities else set()
            end_acts = set(end_activities.keys()) if end_activities else set()
            
            # Calculate activity frequencies for sizing
            activity_freq = {}
            for (act1, act2), freq in dfg_frequency.items():
                activity_freq[act1] = activity_freq.get(act1, 0) + freq
                activity_freq[act2] = activity_freq.get(act2, 0) + freq
            
            # Create hierarchical layout (left to right flow)
            fig, ax = plt.subplots(figsize=(20, 12))
            ax.set_title(f'Process Flow Map - {name}', fontsize=18, fontweight='bold', pad=20)
            ax.axis('off')
            
            # Simple hierarchical layout: start → middle → end
            positions = {}
            layers = []
            
            # Layer 0: Start activities
            layer_0 = [act for act in activities_list if act in start_acts]
            if not layer_0:
                layer_0 = [activities_list[0]]
            
            # Layer N: End activities
            layer_n = [act for act in activities_list if act in end_acts and act not in layer_0]
            
            # Middle layers: Everything else
            middle = [act for act in activities_list if act not in layer_0 and act not in layer_n]
            
            # Arrange activities in layers
            if len(activities_list) <= 10:
                # Simple layout for small processes
                layers = [layer_0, middle, layer_n]
            else:
                # Split middle into multiple columns
                chunk_size = max(8, len(middle) // 3)
                middle_chunks = [middle[i:i + chunk_size] for i in range(0, len(middle), chunk_size)]
                layers = [layer_0] + middle_chunks + [layer_n]
            
            # Clean up empty layers
            layers = [layer for layer in layers if layer]
            
            # Calculate positions
            layer_spacing = 4
            for layer_idx, layer in enumerate(layers):
                x = layer_idx * layer_spacing
                y_spacing = 1.2
                y_offset = -(len(layer) - 1) * y_spacing / 2
                
                for act_idx, activity in enumerate(sorted(layer)):
                    y = y_offset + act_idx * y_spacing
                    positions[activity] = (x, y)
            
            # Draw edges (transitions) with curved paths
            max_freq = max(dfg_frequency.values()) if dfg_frequency else 1
            
            # Sort edges by frequency (draw high-frequency edges on top)
            sorted_edges = sorted(dfg_frequency.items(), key=lambda x: x[1])
            
            for (act1, act2), freq in sorted_edges:
                if act1 in positions and act2 in positions:
                    x1, y1 = positions[act1]
                    x2, y2 = positions[act2]
                    
                    # Calculate line properties based on frequency
                    width = 0.5 + (freq / max_freq) * 4
                    alpha = 0.2 + (freq / max_freq) * 0.7
                    
                    # Determine colour based on frequency
                    if freq / max_freq > 0.7:
                        colour = '#2E7D32'  # Dark green (high frequency)
                    elif freq / max_freq > 0.3:
                        colour = '#1976D2'  # Blue (medium frequency)
                    else:
                        colour = '#757575'  # Grey (low frequency)
                    
                    # Use curved arrows for better visibility
                    connection_style = "arc3,rad=0.2" if act1 == act2 else "arc3,rad=0.1"
                    
                    arrow = FancyArrowPatch(
                        (x1, y1), (x2, y2),
                        arrowstyle='-|>',
                        linewidth=width,
                        alpha=alpha,
                        color=colour,
                        connectionstyle=connection_style,
                        zorder=1
                    )
                    ax.add_patch(arrow)
            
            # Draw nodes (activities) with improved styling
            max_activity_freq = max(activity_freq.values()) if activity_freq else 1
            
            for activity, (x, y) in positions.items():
                freq = activity_freq.get(activity, 0)
                
                # Box size based on activity frequency
                base_width = 0.8
                base_height = 0.35
                size_factor = 0.8 + (freq / max_activity_freq) * 0.4
                width = base_width * size_factor
                height = base_height * size_factor
                
                # Colour coding
                if activity in start_acts:
                    face_colour = '#C8E6C9'  # Light green (start)
                    edge_colour = '#2E7D32'
                elif activity in end_acts:
                    face_colour = '#FFCCBC'  # Light orange (end)
                    edge_colour = '#E64A19'
                else:
                    face_colour = '#BBDEFB'  # Light blue (middle)
                    edge_colour = '#1976D2'
                
                # Activity box with shadow
                shadow = mpatches.FancyBboxPatch(
                    (x - width/2 + 0.02, y - height/2 - 0.02), width, height,
                    boxstyle="round,pad=0.08",
                    edgecolor='none',
                    facecolor='grey',
                    alpha=0.3,
                    zorder=2
                )
                ax.add_patch(shadow)
                
                box = mpatches.FancyBboxPatch(
                    (x - width/2, y - height/2), width, height,
                    boxstyle="round,pad=0.08",
                    edgecolor=edge_colour,
                    facecolor=face_colour,
                    linewidth=2.5,
                    zorder=3
                )
                ax.add_patch(box)
                
                # Activity label with better formatting
                label = activity
                if len(label) > 25:
                    # Split long labels into multiple lines
                    words = label.split()
                    lines = []
                    current_line = []
                    
                    for word in words:
                        current_line.append(word)
                        if len(' '.join(current_line)) > 20:
                            lines.append(' '.join(current_line[:-1]))
                            current_line = [word]
                    
                    if current_line:
                        lines.append(' '.join(current_line))
                    
                    label = '\n'.join(lines[:3])  # Max 3 lines
                    if len(words) > 3:
                        label += '...'
                
                ax.text(x, y, label, ha='center', va='center',
                       fontsize=9, fontweight='600', 
                       color='#212121', zorder=4)
            
            # Enhanced legend with colour coding
            legend_elements = [
                mpatches.Patch(facecolor='#C8E6C9', edgecolor='#2E7D32', label='Start Activities'),
                mpatches.Patch(facecolor='#BBDEFB', edgecolor='#1976D2', label='Process Activities'),
                mpatches.Patch(facecolor='#FFCCBC', edgecolor='#E64A19', label='End Activities'),
                plt.Line2D([0], [0], color='#2E7D32', linewidth=3, label='High Frequency'),
                plt.Line2D([0], [0], color='#1976D2', linewidth=2, label='Medium Frequency'),
                plt.Line2D([0], [0], color='#757575', linewidth=1, label='Low Frequency')
            ]
            
            ax.legend(handles=legend_elements, loc='upper right', 
                     fontsize=10, framealpha=0.95)
            
            # Add statistics box
            stats_text = f"Activities: {len(activities)}\n"
            stats_text += f"Transitions: {len(dfg_frequency)}\n"
            stats_text += f"Variants: {stats.get('total_variants', 'N/A')}"
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=11, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='white', 
                            edgecolor='grey', alpha=0.95, pad=0.8))
            
            # Set axis limits with padding
            all_x = [pos[0] for pos in positions.values()]
            all_y = [pos[1] for pos in positions.values()]
            
            margin = 1.5
            ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
            ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
            ax.set_aspect('equal')
            
            # Save figure with high quality
            output_path = self.output_dir / f"{name}_dfg.png"
            plt.tight_layout()
            plt.savefig(output_path, dpi=200, bbox_inches='tight', 
                       facecolor='white', edgecolor='none')
            plt.close()
            
            print(f"   ✅ Saved: {output_path}") 
            stats['dfg_path'] = str(output_path)
            
        except Exception as e:
            print(f"   ⚠️  DFG generation warning: {str(e)}")
            print(f"   💡 Continuing without visualisation...")
            stats['dfg_path'] = None
        
        # Variant Analysis
        print("\n🔀 Analyzing Process Variants...")
        variants = pm4py.get_variants_as_tuples(log)
        stats['total_variants'] = len(variants)
        print(f"   Total variants: {len(variants)}")
        
        sorted_variants = sorted(variants.items(), 
                                 key=lambda x: len(x[1]), reverse=True)
        stats['top_variants'] = []
        print(f"   Top 5 variants:")
        for i, (variant, cases) in enumerate(sorted_variants[:5], 1):
            variant_info = {
                'path': ' → '.join(variant),
                'case_count': len(cases),
                'percentage': (len(cases) / stats['total_cases']) * 100
            }
            stats['top_variants'].append(variant_info)
            print(f"      {i}. {variant_info['path'][:80]}... "
                  f"({variant_info['case_count']} cases, "
                  f"{variant_info['percentage']:.1f}%)")
        
        # Performance Analysis
        print("\n⏱️  Performance Analysis:")
        
        durations = case_statistics.get_all_case_durations(log)
        if durations:
            stats['avg_duration_seconds'] = sum(durations) / len(durations)
            stats['min_duration_seconds'] = min(durations)
            stats['max_duration_seconds'] = max(durations)
            
            print(f"   Average case duration: {seconds_to_human_readable(stats['avg_duration_seconds'])}")
            print(f"   Min duration: {seconds_to_human_readable(stats['min_duration_seconds'])}")
            print(f"   Max duration: {seconds_to_human_readable(stats['max_duration_seconds'])}")
        else:
            stats['avg_duration_seconds'] = 0
            stats['min_duration_seconds'] = 0
            stats['max_duration_seconds'] = 0
            print("   ⚠️ Cannot calculate duration: Log is empty or missing timestamps.")
        
        # Check for rework patterns
        print("\n🔄 Checking for Rework Patterns...")
        rework_cases = 0
        rework_activities = {}
        
        for trace in log:
            activities_in_trace = [event['concept:name'] for event in trace]
            duplicates = [act for act in set(activities_in_trace) 
                          if activities_in_trace.count(act) > 1]
            if duplicates:
                rework_cases += 1
                for act in duplicates:
                    rework_activities[act] = rework_activities.get(act, 0) + 1
        
        stats['rework_cases'] = rework_cases
        stats['rework_percentage'] = (rework_cases / len(log)) * 100 if len(log) > 0 else 0
        
        print(f"   Cases with rework: {rework_cases} ({stats['rework_percentage']:.1f}%)")
        if rework_activities:
            print(f"   Most common rework activities:")
            sorted_rework = sorted(rework_activities.items(), 
                                   key=lambda x: x[1], reverse=True)[:3]
            for act, count in sorted_rework:
                print(f"      - **{act}**: {count} cases")
        
        # Bottleneck Detection - FIXED VERSION
        print("\n🚨 Bottleneck Detection:")
        try:
            # Calculate activity durations using case statistics
            activity_durations = {}
            
            for trace in log:
                events = list(trace)
                for i in range(len(events) - 1):
                    current_event = events[i]
                    next_event = events[i + 1]
                    
                    activity = current_event['concept:name']
                    current_time = current_event['time:timestamp']
                    next_time = next_event['time:timestamp']
                    
                    duration = (next_time - current_time).total_seconds()
                    
                    if activity not in activity_durations:
                        activity_durations[activity] = []
                    activity_durations[activity].append(duration)
            
            # Calculate average durations
            avg_durations = {
                activity: sum(durations) / len(durations)
                for activity, durations in activity_durations.items()
                if len(durations) > 0
            }
            
            stats['bottlenecks'] = []
            sorted_activities = sorted(avg_durations.items(), 
                                     key=lambda x: x[1], reverse=True)[:3]
            
            print(f"   Top 3 slowest activities (Avg Time to Next Activity):")
            for i, (activity, avg_time) in enumerate(sorted_activities, 1):
                bottleneck_info = {
                    'activity': activity,
                    'avg_time_seconds': avg_time,
                    'avg_time_human': seconds_to_human_readable(avg_time)
                }
                stats['bottlenecks'].append(bottleneck_info)
                print(f"      {i}. **{activity}**: {bottleneck_info['avg_time_human']}")
        except Exception as e:
            print(f"   ⚠️  Bottleneck analysis warning: {str(e)}")
            stats['bottlenecks'] = []
        
        # Data Quality Checks
        print("\n✅ Data Quality Checks:")
        quality_issues = []
        
        null_counts = df[['case:concept:name', 'concept:name', 'time:timestamp']].isnull().sum()
        if null_counts.any():
            quality_issues.append(f"Null values found: {null_counts.to_dict()}")
            print(f"   ⚠️  Null values: {null_counts.to_dict()}")
        else:
            print(f"   ✅ No null values in critical columns")
        
        # Check chronological ordering
        chronological_errors = 0
        if 'time:timestamp' in df.columns:
            case_timestamps = df.groupby('case:concept:name')['time:timestamp'].apply(
                lambda x: x.is_monotonic_increasing
            )
            chronological_errors = case_timestamps[~case_timestamps].count()

        if chronological_errors > 0:
            quality_issues.append(f"{chronological_errors} cases with non-chronological events")
            print(f"   ⚠️  {chronological_errors} cases with timestamp issues")
        else:
            print(f"   ✅ All cases have chronological events")
        
        stats['quality_issues'] = quality_issues
        
        self.results[name] = stats
        print(f"\n✅ Validation Complete for **{name}**")
        
        return stats
    
    def generate_report(self):
        """Generate comprehensive validation report"""
        report_path = self.output_dir / 'validation_report.md'
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Milestone 1: Dataset Validation Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            for name, stats in self.results.items():
                f.write(f"## Dataset: {name}\n\n")
                
                # Basic Stats
                f.write("### Basic Statistics\n\n")
                f.write(f"- **Total Events:** {stats['total_events']:,}\n")
                f.write(f"- **Total Cases:** {stats['total_cases']:,}\n")
                f.write(f"- **Unique Activities:** {stats['total_activities']}\n")
                f.write(f"- **Date Range:** {stats['date_range'][0].date()} to {stats['date_range'][1].date()}\n")
                
                discovery_status = '✅ Success' if stats.get('discovery_success') else '❌ Failed'
                f.write(f"- **Process Discovery:** {discovery_status}\n\n")
                
                # Variants
                f.write("### Process Variants\n\n")
                f.write(f"**Total Variants:** {stats['total_variants']}\n\n")
                f.write("**Top 5 Variants:**\n\n")
                for i, variant in enumerate(stats.get('top_variants', []), 1):
                    f.write(f"{i}. `{variant['path'][:100]}...`\n")
                    f.write(f"   - Cases: {variant['case_count']} ({variant['percentage']:.1f}%)\n\n")
                
                # Performance
                f.write("### Performance Metrics\n\n")
                f.write(f"- **Average Case Duration:** {seconds_to_human_readable(stats['avg_duration_seconds'])}\n")
                f.write(f"- **Min Duration:** {seconds_to_human_readable(stats['min_duration_seconds'])}\n")
                f.write(f"- **Max Duration:** {seconds_to_human_readable(stats['max_duration_seconds'])}\n\n")
                
                # Rework
                f.write("### Rework Analysis\n\n")
                f.write(f"- **Cases with Rework:** {stats['rework_cases']} ({stats['rework_percentage']:.1f}%)\n\n")
                
                # Bottlenecks
                if stats.get('bottlenecks'):
                    f.write("### Bottleneck Activities\n\n")
                    f.write("**Top 3 Activities by Average Time to Next Activity:**\n\n")
                    for i, bottleneck in enumerate(stats['bottlenecks'], 1):
                        f.write(f"{i}. **{bottleneck['activity']}**: {bottleneck['avg_time_human']} average\n")
                    f.write("\n")
                
                # Quality
                f.write("### Data Quality\n\n")
                if stats['quality_issues']:
                    f.write("⚠️ **Issues Found:**\n\n")
                    for issue in stats['quality_issues']:
                        f.write(f"- {issue}\n")
                else:
                    f.write("✅ **No quality issues detected**\n")
                
                f.write("\n---\n\n")
            
            # Summary
            f.write("## Summary\n\n")
            f.write(f"**Total Datasets Validated:** {len(self.results)}\n\n")
            f.write("**Ready for Next Phase:** ")
            all_ready = all(stats.get('discovery_success', False) 
                             for stats in self.results.values())
            f.write("✅ Yes\n" if all_ready and len(self.results) > 0 else "⚠️ Review needed\n")
        
        print(f"\n📄 Report generated: {report_path}")
        return report_path


def main():
    """Main validation workflow"""
    CLEAN_DIR = Path('data/clean')
    SYNTHETIC_DIR = Path('data/synthetic')
    
    validator = DatasetValidator()
    
    # Define datasets to validate
    datasets = [
        (CLEAN_DIR / 'BPI_2012_clean.csv', 'BPI_2012'),
        (CLEAN_DIR / 'BPI_2017_clean.csv', 'BPI_2017'),
        (SYNTHETIC_DIR / 'synthetic_invoice_process.csv', 'Synthetic_Invoice'),
    ]
    
    # Validate each dataset
    for csv_path_obj, name in datasets:
        csv_path = str(csv_path_obj)
        if os.path.exists(csv_path):
            validator.validate_dataset(csv_path, name)
        else:
            print(f"\n⚠️  File not found: {csv_path}")
    
    # Generate comprehensive report
    if validator.results:
        validator.generate_report()
    else:
        print("\n⚠️ Skipping report generation - no datasets validated")
    
    print("\n" + "="*70)
    print("🎉 All validations complete!")
    print("="*70)
    print("\nNext steps:")
    print("1. Review validation/validation_report.md")
    print("2. Check process maps in validation/*.png")

if __name__ == "__main__":
    main()