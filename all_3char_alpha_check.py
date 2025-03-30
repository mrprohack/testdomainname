#!/usr/bin/env python3
# All 3-Character Alphabetic Domain Checker
# Checks all possible 3-letter combinations (a-z only) for .com domain availability
# Runs in alphabetical order from aaa.com to zzz.com (or custom start/end) with multi-threading
# Saves results to a text file and available domains to a separate file

import string
import sys
import time
import datetime
import os
import argparse
import threading
import concurrent.futures
from domaintest import check_domain
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# Thread-safe counters and locks
available_count = 0
checked_count = 0
counter_lock = threading.Lock()
log_lock = threading.Lock()
available_lock = threading.Lock()

def generate_3char_combinations(start_domain="aaa", end_domain="zzz"):
    """Generate 3-letter combinations from start_domain to end_domain (a-z only)"""
    letters = string.ascii_lowercase  # a-z
    
    # Validate input domains
    start_domain = start_domain.lower()[:3]
    end_domain = end_domain.lower()[:3]
    
    # Pad with 'a's if too short
    while len(start_domain) < 3:
        start_domain += 'a'
    while len(end_domain) < 3:
        end_domain += 'z'
    
    # Replace any non-a-z characters with 'a' for start or 'z' for end
    start_chars = []
    end_chars = []
    
    for char in start_domain:
        if char not in letters:
            start_chars.append('a')
        else:
            start_chars.append(char)
            
    for char in end_domain:
        if char not in letters:
            end_chars.append('z')
        else:
            end_chars.append(char)
    
    start_domain = ''.join(start_chars)
    end_domain = ''.join(end_chars)
    
    # Generate combinations in alphabetical order
    combinations = []
    
    # Convert domains to numeric values (a=0, b=1, ..., z=25)
    start_values = [letters.index(c) for c in start_domain]
    end_values = [letters.index(c) for c in end_domain]
    
    # Check if start comes after end in alphabet
    if start_domain > end_domain:
        print(f"{Fore.RED}Error: Start domain '{start_domain}' comes after end domain '{end_domain}' alphabetically.{Style.RESET_ALL}")
        print(f"Defaulting to full range (aaa-zzz).")
        start_domain = "aaa"
        end_domain = "zzz"
        start_values = [0, 0, 0]  # aaa
        end_values = [25, 25, 25]  # zzz
    
    # Generate all combinations from start to end
    current = start_values.copy()
    
    while True:
        # Convert current numeric values to a domain string
        domain = ''.join(letters[i] for i in current)
        combinations.append(domain)
        
        # Check if we've reached the end domain
        if domain == end_domain:
            break
            
        # Increment the current value (like counting)
        current[2] += 1  # Increment the rightmost character
        
        # Handle carrying over to next position
        for i in range(2, 0, -1):
            if current[i] > 25:  # If we've gone past 'z'
                current[i] = 0   # Reset to 'a'
                current[i-1] += 1  # Increment the next position left
    
    return combinations

def check_single_domain(base, all_log_file, available_log_file, total):
    """Check a single domain and update the appropriate log files"""
    global available_count, checked_count
    
    domain = f"{base}.com"
    
    # Check domain availability
    result = check_domain(domain)
    
    # Update counters with thread safety
    with counter_lock:
        checked_count += 1
        current_checked = checked_count
    
    # Save to log files with thread safety
    with log_lock:
        with open(all_log_file, 'a') as f:
            if result["available"]:
                with counter_lock:
                    available_count += 1
                f.write(f"{domain},AVAILABLE\n")
                
                # Also save to available domains file
                with available_lock:
                    with open(available_log_file, 'a') as avail_f:
                        avail_f.write(f"{domain},AVAILABLE\n")
                
                # Print available domains to console
                print(f"\n{Fore.GREEN}✅ Found available: {domain} ({current_checked}/{total}){Style.RESET_ALL}")
            else:
                # For taken domains, extract registrar and expiry if available
                registrar = "Unknown"
                expiry = "Unknown"
                
                if "Registrar:" in result.get("details", ""):
                    detail_parts = result.get("details", "").split("Registrar:", 1)[1].strip()
                    if "Expires:" in detail_parts:
                        registrar_part, expiry_part = detail_parts.split("(Expires:", 1)
                        registrar = registrar_part.strip()
                        expiry = expiry_part.replace(")", "").strip()
                    else:
                        registrar = detail_parts
                
                f.write(f"{domain},TAKEN,{registrar},{expiry}\n")
    
    return result["available"]

def check_domains_multithreaded(start_domain="aaa", end_domain="zzz", output_dir="domain_results", max_workers=10):
    """Check 3-letter .com domains in parallel using multiple threads"""
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Define output filenames
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    all_domains_file = os.path.join(output_dir, f"all_domains_{timestamp}.txt")
    available_domains_file = os.path.join(output_dir, f"available_domains_{timestamp}.txt")
    
    combinations = generate_3char_combinations(start_domain, end_domain)
    total = len(combinations)
    
    print(f"{Fore.CYAN}===== Multi-Threaded 3-Letter .COM Domain Availability Checker ====={Style.RESET_ALL}")
    print(f"Checking domains alphabetically from {start_domain}.com to {end_domain}.com")
    print(f"Total domains to check: {total}")
    print(f"{Fore.YELLOW}Using up to {max_workers} threads for parallel processing{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Results will be saved to: {Style.RESET_ALL}")
    print(f"  - All domains: {all_domains_file}")
    print(f"  - Available domains: {available_domains_file}")
    print(f"{Fore.YELLOW}You can press Ctrl+C at any time to stop the process.{Style.RESET_ALL}")
    print("-" * 70)
    
    # Initialize the output files
    with open(all_domains_file, 'w') as f:
        f.write(f"# 3-Letter Domain Availability Check\n")
        f.write(f"# Range: {start_domain}.com to {end_domain}.com\n")
        f.write(f"# Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Threads: {max_workers}\n")
        f.write(f"# Format: domain,status,registrar,expiry_date\n\n")
    
    with open(available_domains_file, 'w') as f:
        f.write(f"# Available 3-Letter Domains\n")
        f.write(f"# Range: {start_domain}.com to {end_domain}.com\n")
        f.write(f"# Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Format: domain,status\n\n")
    
    # Reset global counters
    global available_count, checked_count
    available_count = 0
    checked_count = 0
    
    start_time = time.time()
    last_update_time = start_time
    
    try:
        # Create and configure the thread pool
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all domain checks to the executor
            futures = {executor.submit(check_single_domain, base, all_domains_file, available_domains_file, total): base 
                       for base in combinations}
            
            # Process domains as they complete
            for future in concurrent.futures.as_completed(futures):
                # Periodically update the progress display
                current_time = time.time()
                if current_time - last_update_time >= 2:  # Update every 2 seconds
                    with counter_lock:
                        local_checked = checked_count
                        local_available = available_count
                    
                    elapsed = current_time - start_time
                    domains_per_second = local_checked / elapsed if elapsed > 0 else 0
                    percent_complete = (local_checked / total) * 100
                    
                    # Estimate time remaining
                    if domains_per_second > 0:
                        remaining_domains = total - local_checked
                        seconds_remaining = remaining_domains / domains_per_second
                        time_remaining = str(datetime.timedelta(seconds=int(seconds_remaining)))
                    else:
                        time_remaining = "unknown"
                    
                    print(f"\r{Fore.YELLOW}Progress: {local_checked}/{total} ({percent_complete:.1f}%) | "
                          f"Threads: {max_workers} | "
                          f"Found: {local_available} available | "
                          f"Speed: {domains_per_second:.2f} domains/sec | "
                          f"Est. remaining: {time_remaining}{Style.RESET_ALL}", end="")
                    
                    last_update_time = current_time
                
                # Catch any exceptions from the workers
                try:
                    future.result()  # Will raise any exceptions from the worker thread
                except Exception as e:
                    print(f"\n{Fore.RED}Error checking domain: {str(e)}{Style.RESET_ALL}")
    
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Process interrupted by user after checking {checked_count} domains.{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}You can resume by running with these parameters:{Style.RESET_ALL}")
        
        # Figure out approximately where we stopped
        if checked_count < total:
            # Estimate the next domain based on completion percentage
            completion_ratio = checked_count / total
            next_idx = min(int(len(combinations) * completion_ratio), len(combinations) - 1)
            next_domain = combinations[next_idx]
            print(f"{Fore.YELLOW}python {sys.argv[0]} --start {next_domain} --end {end_domain} --threads {max_workers}{Style.RESET_ALL}")
        
    finally:
        # Add summary to files
        elapsed_time = time.time() - start_time
        
        with open(all_domains_file, 'a') as f:
            f.write(f"\n# Check completed or interrupted at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total checked: {checked_count} out of {total}\n")
            f.write(f"# Available domains found: {available_count}\n")
            f.write(f"# Total elapsed time: {str(datetime.timedelta(seconds=int(elapsed_time)))}\n")
        
        with open(available_domains_file, 'a') as f:
            f.write(f"\n# Check completed or interrupted at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total available domains found: {available_count} out of {checked_count} checked\n")
            f.write(f"# Total elapsed time: {str(datetime.timedelta(seconds=int(elapsed_time)))}\n")
        
        # Final summary to console
        print("\n" + "=" * 70)
        print(f"{Fore.CYAN}Summary:{Style.RESET_ALL}")
        print(f"Total domains checked: {checked_count} out of {total}")
        print(f"{Fore.GREEN}Available domains found: {available_count}{Style.RESET_ALL}")
        print(f"Results saved to directory: {os.path.abspath(output_dir)}")
        print(f"  - All domains: {os.path.basename(all_domains_file)}")
        print(f"  - Available domains: {os.path.basename(available_domains_file)}")
        print(f"Total time elapsed: {str(datetime.timedelta(seconds=int(elapsed_time)))}")
        
        # Calculate and display performance metrics
        if elapsed_time > 0:
            domains_per_second = checked_count / elapsed_time
            domains_per_minute = domains_per_second * 60
            domains_per_hour = domains_per_minute * 60
            
            print(f"\n{Fore.CYAN}Performance:{Style.RESET_ALL}")
            print(f"Average speed: {domains_per_second:.2f} domains/second")
            print(f"              {domains_per_minute:.2f} domains/minute")
            print(f"              {domains_per_hour:.2f} domains/hour")
            
            if checked_count < total:
                completion_percent = (checked_count / total) * 100
                print(f"Completed: {completion_percent:.2f}% of the planned range")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Multi-threaded checker for 3-letter .com domains in alphabetical order")
    parser.add_argument("--start", default="aaa", help="Starting domain prefix (default: aaa)")
    parser.add_argument("--end", default="zzz", help="Ending domain prefix (default: zzz)")
    parser.add_argument("--threads", type=int, default=10, help="Number of threads to use (default: 10)")
    parser.add_argument("--output-dir", default="domain_results", help="Directory to save results (default: domain_results)")
    
    args = parser.parse_args()
    
    check_domains_multithreaded(args.start, args.end, args.output_dir, args.threads)
    print(f"\n{Fore.YELLOW}--- Check Complete ---{Style.RESET_ALL}") 