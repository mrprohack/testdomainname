#!/usr/bin/env python3
# Random 3-Character Domain Checker
# Generates random 3-character strings and checks their availability as .com domains

import random
import string
import sys
from domaintest import check_domain, get_purchase_links, open_purchase_link
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def generate_random_3char():
    """Generate a random 3-character string using lowercase letters and numbers"""
    chars = string.ascii_lowercase + string.digits  # a-z, 0-9
    return ''.join(random.choice(chars) for _ in range(3))

def check_3char_domains(count=3):
    """Generate and check availability of random 3-character .com domains"""
    print(f"{Fore.CYAN}===== 3-Character .COM Domain Availability Checker ====={Style.RESET_ALL}")
    print(f"Checking {count} randomly generated 3-character domains")
    print(f"{Fore.YELLOW}Note: 3-character domains are rare and valuable if available{Style.RESET_ALL}")
    print("-" * 60)
    
    available_domains = []
    checked_domains = set()  # To avoid checking duplicates
    
    while len(checked_domains) < count:
        # Generate domain and add .com
        base = generate_random_3char()
        if base in checked_domains:
            continue  # Skip duplicates
            
        domain = f"{base}.com"
        checked_domains.add(base)
        
        print(f"\n{Fore.YELLOW}Checking: {domain}{Style.RESET_ALL}")
        
        # Use the existing check_domain function from domaintest.py
        result = check_domain(domain)
        
        # Display result
        print(result["message"])
        if result["details"]:
            print(result["details"])
            
        # Save available domains
        if result["available"]:
            available_domains.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"Total domains checked: {count}")
    print(f"{Fore.GREEN}Available: {len(available_domains)}{Style.RESET_ALL}")
    print(f"{Fore.RED}Taken/Unavailable: {count - len(available_domains)}{Style.RESET_ALL}")
    
    # Interactive part for available domains
    if available_domains:
        print(f"\n{Fore.GREEN}Available Domains Found:{Style.RESET_ALL}")
        for i, domain_data in enumerate(available_domains, 1):
            domain_name = domain_data["domain"]
            print(f"{i}. {domain_name}")
            
            # Display purchase links
            purchase_links = domain_data["purchase_links"]
            if purchase_links:
                for registrar, link in purchase_links.items():
                    print(f"   → {registrar}: {link}")
        
        # Offer to open a purchase link
        if available_domains:
            print(f"\n{Fore.YELLOW}Would you like to open a purchase link in your browser?{Style.RESET_ALL}")
            while True:
                choice = input(f"Enter domain number (1-{len(available_domains)}) or press Enter to skip: ").strip()
                if not choice:
                    print("Exiting without opening browser.")
                    break
                
                if choice.isdigit() and 1 <= int(choice) <= len(available_domains):
                    selected_idx = int(choice) - 1
                    selected_domain = available_domains[selected_idx]
                    
                    # Ask which registrar
                    registrars = list(selected_domain["purchase_links"].keys())
                    if registrars:
                        print(f"Available registrars for {selected_domain['domain']}:")
                        for i, reg in enumerate(registrars, 1):
                            print(f"{i}. {reg}")
                        
                        reg_choice = input(f"Enter registrar number (1-{len(registrars)}) or press Enter for first: ").strip()
                        
                        if not reg_choice or not reg_choice.isdigit() or int(reg_choice) < 1 or int(reg_choice) > len(registrars):
                            reg_idx = 0  # Default to first registrar
                        else:
                            reg_idx = int(reg_choice) - 1
                            
                        selected_registrar = registrars[reg_idx]
                        link_to_open = selected_domain["purchase_links"][selected_registrar]
                        
                        print(f"\n{Fore.GREEN}Opening {selected_registrar} link for {selected_domain['domain']}...{Style.RESET_ALL}")
                        opened = open_purchase_link(link_to_open)
                        
                        if not opened:
                            print(f"{Fore.YELLOW}If the browser didn't open, you can manually visit:{Style.RESET_ALL}")
                            print(link_to_open)
                        
                        break
                else:
                    print(f"{Fore.RED}Invalid choice. Please enter a number between 1 and {len(available_domains)}.{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}No available domains found in this batch.{Style.RESET_ALL}")
        print("Try running the script again for a new set of random domains.")

if __name__ == "__main__":
    # Get number of domains to check from command line argument, default to 3
    try:
        if len(sys.argv) > 1:
            count = int(sys.argv[1])
            if count < 1:
                raise ValueError("Count must be positive")
        else:
            count = 3
    except ValueError as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        print(f"Usage: python {sys.argv[0]} [number_of_domains]")
        print("Example: python random_3char_domain_check.py 5")
        sys.exit(1)
    
    check_3char_domains(count)
    print(f"\n{Fore.YELLOW}--- Check Complete ---{Style.RESET_ALL}") 