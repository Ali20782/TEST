"""
Synthetic Event Log Generator
Creates realistic event logs with known rework patterns and bottlenecks
"""

import pandas as pd
import pm4py
from pm4py.objects.log.obj import EventLog, Event, Trace
from datetime import datetime, timedelta
import random
import os


class SyntheticLogGenerator:
    def __init__(self, seed=42):
        random.seed(seed)
        self.start_date = datetime(2024, 1, 1, 8, 0, 0)
        
    def generate_invoice_process(self, num_cases=200):
        """
        Generate invoice approval process with three variants:
        - Happy path (60%): Fast automated approval
        - Rework path (30%): Manual review with corrections
        - Escalation path (10%): Manager approval delays
        """
        
        log = EventLog()
        
        # Define process variants
        happy_path = [
            'Create Invoice',
            'Validate Data',
            'Auto-Approve',
            'Send to Payment',
            'Mark Complete'
        ]
        
        rework_path = [
            'Create Invoice',
            'Validate Data',
            'Manual Review',
            'Request Correction',
            'Manual Review',
            'Approve',
            'Send to Payment',
            'Mark Complete'
        ]
        
        escalation_path = [
            'Create Invoice',
            'Validate Data',
            'Manual Review',
            'Manager Approval',
            'Approve',
            'Send to Payment',
            'Mark Complete'
        ]
        
        paths = [happy_path, rework_path, escalation_path]
        weights = [0.6, 0.3, 0.1]
        
        # Resources
        resources = {
            'Create Invoice': ['System', 'Clerk_A', 'Clerk_B'],
            'Validate Data': ['System'],
            'Manual Review': ['Reviewer_1', 'Reviewer_2'],
            'Request Correction': ['Reviewer_1', 'Reviewer_2'],
            'Auto-Approve': ['System'],
            'Approve': ['Supervisor'],
            'Manager Approval': ['Manager'],
            'Send to Payment': ['System'],
            'Mark Complete': ['System']
        }
        
        # Cost structure
        costs = {
            'Create Invoice': 5,
            'Validate Data': 1,
            'Manual Review': 25,
            'Request Correction': 15,
            'Auto-Approve': 0,
            'Approve': 10,
            'Manager Approval': 50,
            'Send to Payment': 2,
            'Mark Complete': 1
        }
        
        # Locations
        locations = ['Texas', 'California', 'New York', 'Florida']
        
        print(f"   🏭 Generating {num_cases} invoice cases...")
        
        for case_num in range(num_cases):
            trace = Trace()
            case_id = f'INV_{case_num:05d}'
            trace.attributes['concept:name'] = case_id
            
            # Select variant
            selected_path = random.choices(paths, weights=weights)[0]
            variant_name = 'Happy' if selected_path == happy_path else \
                          'Rework' if selected_path == rework_path else 'Escalation'
            
            # Select location (Texas has more rework)
            if variant_name == 'Rework':
                location = random.choices(locations, weights=[0.5, 0.2, 0.2, 0.1])[0]
            else:
                location = random.choice(locations)
            
            # Start time with business hours logic
            days_offset = random.randint(0, 90)
            current_time = self.start_date + timedelta(days=days_offset)
            
            # Generate events
            for activity in selected_path:
                event = Event()
                event['concept:name'] = activity
                event['time:timestamp'] = current_time
                event['org:resource'] = random.choice(resources.get(activity, ['Unknown']))
                event['case:id'] = case_id
                event['cost'] = costs.get(activity, 0)
                event['location'] = location
                
                # Add delay based on activity type
                if activity == 'Manager Approval':
                    delay_days = random.uniform(5, 12)
                    event['bottleneck'] = True
                elif activity == 'Manual Review':
                    delay_days = random.uniform(1, 4)
                elif activity == 'Request Correction':
                    delay_days = random.uniform(2, 5)
                elif 'System' in resources.get(activity, []):
                    delay_days = random.uniform(0.001, 0.01)
                else:
                    delay_days = random.uniform(0.04, 0.2)
                
                current_time += timedelta(days=delay_days)
                
                # Skip weekends
                while current_time.weekday() >= 5:
                    current_time += timedelta(days=1)
                
                trace.append(event)
            
            log.append(trace)
            
            if (case_num + 1) % 50 == 0:
                print(f"      ✓ Generated {case_num + 1}/{num_cases} cases")
        
        print(f"   ✅ Generated {len(log)} cases successfully")
        return log
    
    def save_log(self, log, output_dir='data/synthetic'):
        """Save log in both XES and CSV formats"""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n   💾 Saving event log...")
        
        # Save XES
        xes_path = os.path.join(output_dir, 'synthetic_invoice_process.xes')
        pm4py.write_xes(log, xes_path)
        print(f"      ✓ XES format: {xes_path}")
        
        # Convert to DataFrame and save CSV
        df = pm4py.convert_to_dataframe(log)
        
        # Column renaming
        column_mapping = {
            'case:concept:name': 'case_id',
            'concept:name': 'activity',
            'time:timestamp': 'timestamp',
            'org:resource': 'resource',
            'cost': 'cost',
            'location': 'location'
        }
        
        df = df.rename(columns=column_mapping, errors='ignore')

        # Fallback for case_id
        if 'case:id' in df.columns and 'case_id' not in df.columns:
             df = df.rename(columns={'case:id': 'case_id'}, errors='ignore')
        
        # Ensure proper column order
        canonical_columns = ['case_id', 'activity', 'timestamp', 'resource', 
                             'cost', 'location']
        
        df = df.reindex(columns=canonical_columns)
        
        csv_path = os.path.join(output_dir, 'synthetic_invoice_process.csv')
        df.to_csv(csv_path, index=False)
        print(f"      ✓ CSV format: {csv_path}")
        
        return xes_path, csv_path
    
    def generate_report(self, log):
        """Generate descriptive statistics"""
        print("\n" + "="*70)
        print("📊 SYNTHETIC DATA GENERATION REPORT")
        print("="*70)
        
        # Convert to DataFrame for analysis
        df = pm4py.convert_to_dataframe(log)
        
        print(f"\n   📈 Basic Statistics:")
        print(f"      • Total Cases: {len(log):,}")
        print(f"      • Total Events: {len(df):,}")
        print(f"      • Unique Activities: {df['concept:name'].nunique()}")
        
        date_min = df['time:timestamp'].min().date()
        date_max = df['time:timestamp'].max().date()
        print(f"      • Date Range: {date_min} to {date_max}")
        
        # Variant distribution
        print(f"\n   🔀 Process Variants:")
        variants = {}
        for trace in log:
            variant = tuple([event['concept:name'] for event in trace])
            variants[variant] = variants.get(variant, 0) + 1
        
        sorted_variants = sorted(variants.items(), key=lambda x: x[1], reverse=True)
        for i, (variant, count) in enumerate(sorted_variants[:3], 1):
            variant_name = 'Happy Path' if len(variant) == 5 else \
                          'Rework Loop' if 'Request Correction' in variant else 'Escalation'
            percentage = (count / len(log)) * 100
            print(f"      {i}. {variant_name}: {count} cases ({percentage:.1f}%)")
        
        # Rework analysis
        print(f"\n   🔄 Rework Pattern Validation:")
        rework_cases = sum(1 for trace in log 
                          if any(event['concept:name'] == 'Request Correction' 
                                 for event in trace))
        rework_percentage = (rework_cases / len(log)) * 100
        print(f"      • Cases with Rework: {rework_cases} ({rework_percentage:.1f}%)")
        
        status = '✅' if 25 <= rework_percentage <= 35 else '⚠️'
        print(f"      {status} Target: ~30% | Actual: {rework_percentage:.1f}%")
        
        # Bottleneck analysis
        print(f"\n   ⚡ Bottleneck Activity Validation:")
        manager_approvals = df[df['concept:name'] == 'Manager Approval']
        
        if len(manager_approvals) > 0:
            manager_cases = manager_approvals['case:concept:name'].unique()
            durations = []
            
            for case in manager_cases:
                case_events = df[df['case:concept:name'] == case].sort_values('time:timestamp')
                manager_idx = case_events[case_events['concept:name'] == 'Manager Approval'].index[0]
                manager_pos = case_events.index.get_loc(manager_idx)
                
                if manager_pos > 0:
                    prev_event = case_events.iloc[manager_pos - 1]
                    manager_event = case_events.iloc[manager_pos]
                    duration = (manager_event['time:timestamp'] - 
                               prev_event['time:timestamp']).total_seconds() / 86400
                    durations.append(duration)
            
            if durations:
                avg_duration = sum(durations) / len(durations)
                print(f"      • Manager Approval Duration: {avg_duration:.1f} days average")
                
                status = '✅' if 5 <= avg_duration <= 12 else '⚠️'
                print(f"      {status} Target: 5-12 days | Actual: {avg_duration:.1f} days")
        
        # Location distribution
        print(f"\n   📍 Location Distribution:")
        location_counts = df.groupby('location')['case:concept:name'].nunique()
        for location, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(log)) * 100
            print(f"      • {location}: {count} cases ({percentage:.1f}%)")
        
        print("\n" + "="*70)
        print("✅ Synthetic Data Generation Complete")
        print("="*70)


def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🚀 SYNTHETIC EVENT LOG GENERATOR")
    print("="*70)
    print("\n   Creating realistic invoice approval process...")
    print("   • 60% Happy path (fast automated)")
    print("   • 30% Rework path (manual corrections)")
    print("   • 10% Escalation path (manager approval)\n")
    
    generator = SyntheticLogGenerator(seed=42)
    
    # Generate log
    log = generator.generate_invoice_process(num_cases=200)
    
    # Save files
    xes_path, csv_path = generator.save_log(log)
    
    # Generate report
    generator.generate_report(log)
    
    print("\n📝 Next Steps:")
    print("   1. Run validation: python -m scripts.dataset_validation")
    print("   2. Check process maps for rework loops") 
    print("   3. Verify Manager Approval bottleneck")
    print("   4. Review generated CSV file\n")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()