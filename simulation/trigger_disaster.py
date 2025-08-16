#!/usr/bin/env python3
"""
Disaster Scenario Trigger Script
Use this to manually trigger disaster scenarios and test SMS alerts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import argparse
from simulation.simulation import simulate_disaster_scenario, start_simulation_mode, stop_simulation_mode
from simulation.crowdsense_simulation import fetch_and_analyze_tweets, initialize_system
from utils.logging_config import setup_logging, get_logger

setup_logging('INFO')
logger = get_logger('trigger')


def trigger_and_test_disaster(disaster_type: str, severity: str = "major", wait_time: int = 5):
    """
    Trigger a disaster scenario and test the alert system
    
    Args:
        disaster_type: Type of disaster (earthquake, flood, fire, storm, tsunami)
        severity: Severity level (moderate, major, severe)
        wait_time: Seconds to wait between triggering and analysis
    """
    print(f"🌪️ Triggering {severity} {disaster_type} scenario...")
    
    # Initialize system
    initialize_system()
    
    # Trigger the disaster scenario
    scenario = simulate_disaster_scenario(disaster_type, severity)
    
    print(f"📍 Location: {scenario['location']}")
    print(f"📊 Severity: {scenario['severity']}")
    if scenario.get('magnitude'):
        print(f"📏 Magnitude: {scenario['magnitude']}")
    
    print(f"⏳ Waiting {wait_time} seconds for tweets to generate...")
    time.sleep(wait_time)
    
    # Run analysis to detect the anomaly and send alert
    print("🔍 Running tweet analysis...")
    results = fetch_and_analyze_tweets()
    
    print("\n" + "="*50)
    print("📊 ANALYSIS RESULTS")
    print("="*50)
    print(f"Keywords processed: {results['keywords_processed']}")
    print(f"Total tweets: {results['total_tweets']}")
    print(f"Anomalies detected: {results['anomalies_detected']}")
    print(f"Alerts sent: {results['alerts_sent']}")
    print(f"Simulation mode: {results['simulation_mode']}")
    
    if results['alerts_sent'] > 0:
        print("✅ SUCCESS: Alert should have been sent to your phone!")
    else:
        print("⚠️ No alerts sent. Trying again...")
        # Run analysis again to ensure detection
        time.sleep(2)
        results2 = fetch_and_analyze_tweets()
        if results2['alerts_sent'] > 0:
            print("✅ SUCCESS: Alert sent on second analysis!")
        else:
            print("❌ No alert sent. Check your Twilio configuration.")
    
    print("="*50)


def interactive_mode():
    """Interactive mode for testing different scenarios"""
    print("🌐 CrowdSense Disaster Simulation Interactive Mode")
    print("="*50)
    
    disasters = ["earthquake", "flood", "fire", "storm", "tsunami"]
    severities = ["moderate", "major", "severe"]
    
    while True:
        print("\n📋 Available disaster types:")
        for i, disaster in enumerate(disasters, 1):
            print(f"  {i}. {disaster.title()}")
        print("  0. Exit")
        
        try:
            choice = input("\n🔢 Select disaster type (1-5, 0 to exit): ").strip()
            
            if choice == "0":
                print("👋 Exiting simulation mode...")
                stop_simulation_mode()
                break
                
            choice = int(choice)
            if 1 <= choice <= len(disasters):
                disaster_type = disasters[choice - 1]
                
                print(f"\n📊 Available severity levels for {disaster_type}:")
                for i, severity in enumerate(severities, 1):
                    print(f"  {i}. {severity.title()}")
                
                sev_choice = input("🔢 Select severity (1-3, or press Enter for 'major'): ").strip()
                
                if sev_choice == "":
                    severity = "major"
                else:
                    sev_choice = int(sev_choice)
                    if 1 <= sev_choice <= len(severities):
                        severity = severities[sev_choice - 1]
                    else:
                        severity = "major"
                
                print(f"\n🚨 Triggering {severity} {disaster_type}...")
                trigger_and_test_disaster(disaster_type, severity)
                
                input("\n⏸️ Press Enter to continue...")
                
            else:
                print("❌ Invalid choice. Please select 1-5 or 0.")
                
        except (ValueError, KeyboardInterrupt):
            print("\n👋 Exiting...")
            stop_simulation_mode()
            break


def main():
    """Main function with command line arguments"""
    parser = argparse.ArgumentParser(description='Trigger CrowdSense disaster scenarios for testing')
    parser.add_argument('--disaster', '-d', 
                       choices=['earthquake', 'flood', 'fire', 'storm', 'tsunami'],
                       help='Type of disaster to simulate')
    parser.add_argument('--severity', '-s',
                       choices=['moderate', 'major', 'severe'],
                       default='major',
                       help='Severity level of the disaster')
    parser.add_argument('--interactive', '-i', 
                       action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--wait', '-w',
                       type=int, default=5,
                       help='Seconds to wait between trigger and analysis')
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_mode()
    elif args.disaster:
        trigger_and_test_disaster(args.disaster, args.severity, args.wait)
    else:
        print("🌐 CrowdSense Disaster Trigger")
        print("Usage examples:")
        print("  python trigger_disaster.py -d earthquake -s major")
        print("  python trigger_disaster.py -i  # Interactive mode")
        print("  python trigger_disaster.py --help")


if __name__ == "__main__":
    main()
