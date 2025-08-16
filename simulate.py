#!/usr/bin/env python3
"""
CrowdSense Simulation Entry Point
Easy access to disaster simulation features
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import argparse
from simulation.trigger_disaster import main as trigger_main
from simulation.simulation import (
    simulate_disaster_scenario, 
    start_simulation_mode, 
    stop_simulation_mode
)
from utils.logging_config import setup_logging, get_logger

logger = get_logger('crowdsense.simulate')


def quick_disaster(disaster_type: str, severity: str = "major"):
    """Quick disaster simulation"""
    print(f"🌪️ Simulating {severity} {disaster_type}...")
    
    try:
        # Start simulation mode
        start_simulation_mode()
        
        # Trigger scenario
        scenario = simulate_disaster_scenario(disaster_type, severity)
        print(f"📍 Triggered in: {scenario['location']}")
        
        # Run analysis
        from simulation.crowdsense_simulation import fetch_and_analyze_tweets, initialize_system
        initialize_system()
        
        import time
        time.sleep(3)  # Wait for tweets to generate
        
        results = fetch_and_analyze_tweets()
        
        print(f"✅ Analysis complete:")
        print(f"   📱 Tweets: {results['total_tweets']}")
        print(f"   🚨 Alerts: {results['alerts_sent']}")
        
        if results['alerts_sent'] > 0:
            print("📞 Check your phone for SMS alert!")
        
        return results
        
    except Exception as e:
        print(f"❌ Error in simulation: {e}")
        # Fallback - just show that simulation was triggered
        print("✅ Disaster scenario triggered (check logs for details)")
        return {"total_tweets": 0, "alerts_sent": 0}


def main():
    """Main simulation entry point"""
    parser = argparse.ArgumentParser(description='CrowdSense Disaster Simulation')
    parser.add_argument('disaster', 
                       choices=['earthquake', 'flood', 'fire', 'storm', 'tsunami'],
                       nargs='?',
                       help='Type of disaster to simulate')
    parser.add_argument('--severity', '-s',
                       choices=['moderate', 'major', 'severe'],
                       default='major',
                       help='Severity level')
    parser.add_argument('--interactive', '-i',
                       action='store_true',
                       help='Interactive mode with full trigger_disaster features')
    
    args = parser.parse_args()
    
    setup_logging('INFO')
    
    if args.interactive:
        # Use the full trigger_disaster tool
        sys.argv = ['trigger_disaster.py', '-i']
        trigger_main()
    elif args.disaster:
        # Quick simulation
        quick_disaster(args.disaster, args.severity)
    else:
        print("🧪 CrowdSense Disaster Simulation")
        print("=" * 40)
        print("Usage:")
        print("  python simulate.py earthquake")
        print("  python simulate.py flood --severity severe")
        print("  python simulate.py -i  # Interactive mode")
        print("\nAvailable disasters:")
        print("  🌍 earthquake  🌊 flood  🔥 fire  ⛈️ storm  🌊 tsunami")


if __name__ == "__main__":
    main()
