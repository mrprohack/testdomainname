# Required packages: pip install python-whois requests colorama
import whois
import concurrent.futures
import socket
import requests
from colorama import init, Fore, Style
import webbrowser
import sys
import os

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)

# List of top 20 most popular domain extensions
TOP_20_TLDS = [
    'com', 'net', 'org', 'io', 'co',
    'ai', 'app', 'dev', 'me', 'info',
    'xyz', 'tech', 'online', 'site', 'store',
    'blog', 'shop', 'biz', 'edu', 'ly'
]

# TLDs that might benefit from double checking due to whois inconsistencies
SPECIAL_TLDS = ['ai', 'io', 'co', 'me']

# Popular domain registrars - using standard search URLs
REGISTRARS = {
    'Porkbun': 'https://porkbun.com/checkout/search?q={}',
    'GoDaddy': 'https://www.godaddy.com/domainsearch/find?domainToCheck={}'
}

def get_purchase_links(domain):
    """Generate purchase links for an available domain at popular registrars."""
    links = {}
    for name, url_template in REGISTRARS.items():
        links[name] = url_template.format(domain)
    return links

def open_purchase_link(url):
    """Open the purchase link in the default web browser."""
    try:
        print(f"{Fore.CYAN}Attempting to open: {url}{Style.RESET_ALL}")
        webbrowser.open(url)
        return True
    except Exception as e:
        print(f"{Fore.RED}Error opening browser: {str(e)}{Style.RESET_ALL}")
        return False

def double_check_availability(domain):
    """
    Secondary verification using DNS/HTTP checks.
    Returns True if domain seems available, False if it's likely taken.
    """
    # --- Check 1: DNS Lookup ---
    try:
        socket.gethostbyname(domain)
        # If DNS resolves, it's likely taken.
        return False
    except socket.gaierror:
        # Expected if domain isn't registered or has no A/AAAA records. Continue checks.
        pass

    # --- Check 2: HTTP/S HEAD Request ---
    for scheme in ["https://", "http://"]:
        try:
            response = requests.head(f"{scheme}{domain}", timeout=3, allow_redirects=True)
            if response.status_code < 400:
                # If we get a successful response, it implies the domain is configured.
                return False
        except requests.Timeout:
            # Timeout could mean server exists but is slow
            # Treat timeout as inconclusive and assume available if no other signs
            pass
        except requests.RequestException:
            # Connection errors are expected for truly available domains.
            pass

    # If we reached here, DNS lookup failed, and HTTP requests failed, it's *likely* available.
    return True


def check_domain(domain):
    """Check a single domain's availability using WHOIS and double-checking."""
    whois_info = None
    whois_error = None
    details_suffix = "" # To add info about double check method

    try:
        whois_info = whois.whois(domain)
    except whois.exceptions.WhoisCommandTimeout:
        whois_error = "WHOIS Timeout"
    except Exception as e:
        whois_error = f"WHOIS Error: {str(e).splitlines()[0][:70]}..."

    # --- Initial WHOIS Interpretation ---
    is_registered_via_whois = False
    if whois_info and not whois_error:
        # Check for common indicators of registration
        if whois_info.domain_name or whois_info.creation_date or whois_info.registrar or whois_info.status:
            is_registered_via_whois = True

    # --- Decision Logic ---
    if is_registered_via_whois:
        # WHOIS indicates registered, assume taken.
        expiration = whois_info.expiration_date
        expiry_str = ""
        if expiration:
            expiry_date = expiration[0] if isinstance(expiration, list) else expiration
            try:
                expiry_str = f" (Expires: {expiry_date.strftime('%Y-%m-%d')})"
            except AttributeError:
                expiry_str = f" (Expires: {expiry_date})"
        registrar = whois_info.registrar if whois_info.registrar else "Unknown"
        return {
            "domain": domain,
            "available": False,
            "message": f"{Fore.RED}❌ {domain} - Taken (WHOIS){Style.RESET_ALL}",
            "details": f"   Registrar: {registrar}{expiry_str}",
            "purchase_links": {}
        }
    else:
        # WHOIS is inconclusive (error or no registration data found).
        # Perform the double check.
        is_truly_available = double_check_availability(domain)
        details_suffix = " (Checked via DNS/HTTP)"

        if is_truly_available:
            purchase_links = get_purchase_links(domain)
            links_text = [f"   → {name}: {url}" for name, url in purchase_links.items()]
            prefix = f"{Fore.GREEN}✅ {domain} - Available"
            if whois_error:
                 prefix = f"{Fore.GREEN}✅ {domain} - Likely Available"
                 details_prefix = f"   ({whois_error}){details_suffix}\n"
            else:
                 prefix = f"{Fore.GREEN}✅ {domain} - Available"
                 details_prefix = f"   (WHOIS empty){details_suffix}\n"

            return {
                "domain": domain,
                "available": True,
                "message": f"{prefix}{Style.RESET_ALL}",
                "details": details_prefix + "\n".join(links_text),
                "purchase_links": purchase_links
            }
        else:
            # Double check indicates taken
            details_prefix = ""
            if whois_error:
                prefix = f"{Fore.RED}❌ {domain} - Likely Taken"
                details_prefix = f"   ({whois_error}){details_suffix}"
            else:
                 prefix = f"{Fore.RED}❌ {domain} - Taken"
                 details_prefix = f"   (WHOIS empty, but double-check indicates taken){details_suffix}"

            return {
                "domain": domain,
                "available": False,
                "message": f"{prefix}{Style.RESET_ALL}",
                "details": details_prefix,
                "purchase_links": {}
            }


def check_domain_availability(base_domain, tlds=None, max_workers=10):
    """Check domain availability across multiple TLDs using parallel processing."""
    if tlds is None:
        tlds = TOP_20_TLDS

    print(f"\n{Fore.CYAN}Checking availability for '{base_domain}' across {len(tlds)} TLDs...{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Using up to {max_workers} parallel checks.{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Note: Results rely on WHOIS and DNS/HTTP checks. Availability not guaranteed until registration.{Style.RESET_ALL}")
    print("=" * 60)

    results = []
    domains_to_check = [f"{base_domain}.{tld}" for tld in tlds]
    available_domains_list = [] # Store available domain data for later interaction

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_domain = {executor.submit(check_domain, domain): domain for domain in domains_to_check}

            for future in concurrent.futures.as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    result = future.result()
                    results.append(result)
                    print(result["message"])
                    if result["details"]:
                        print(result["details"])
                    if result["available"]:
                        available_domains_list.append(result)
                except Exception as exc:
                    print(f"{Fore.RED}❌ {domain} generated an exception during future processing: {exc}{Style.RESET_ALL}")
                    results.append({
                        "domain": domain, "available": False,
                        "message": f"{Fore.RED}❌ {domain} - Error during check processing{Style.RESET_ALL}",
                        "details": f"   Error: {str(exc)[:100]}...", "purchase_links": {}
                    })

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Ctrl+C detected. Shutting down gracefully...{Style.RESET_ALL}")
        # executor.shutdown(wait=False, cancel_futures=True) # Use in Python 3.9+ if needed
        sys.exit(1)


    # Summary
    available_count = sum(1 for r in results if r["available"])
    taken_count = sum(1 for r in results if not r["available"] and "Error" not in r["message"]) # Simplified count
    uncertain_count = len(results) - available_count - taken_count

    print("=" * 60)
    print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"Total domains checked: {len(results)}")
    print(f"{Fore.GREEN}Available: {available_count}{Style.RESET_ALL}")
    print(f"{Fore.RED}Taken/Unavailable: {taken_count + uncertain_count}{Style.RESET_ALL}") # Combine uncertain/error with taken for simplicity

    # Interactive part: Offer to open purchase links
    if available_domains_list:
        print(f"\n{Fore.CYAN}Available Domains Found:{Style.RESET_ALL}")
        
        first_registrar = next(iter(REGISTRARS))
        for i, domain_data in enumerate(available_domains_list, 1):
            print(f"{i}. {domain_data['domain']}")
            if first_registrar in domain_data['purchase_links']:
                 print(f"   {Fore.CYAN}Buy at {first_registrar}:{Style.RESET_ALL} {domain_data['purchase_links'][first_registrar]}")

        print(f"\n{Fore.YELLOW}Open a purchase link in browser?{Style.RESET_ALL}")
        while True:
            choice = input(f"Enter number (1-{len(available_domains_list)}) to open the '{first_registrar}' link, or just press Enter to skip: ").strip()
            if not choice:
                print("Skipping browser open.")
                break

            if choice.isdigit():
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(available_domains_list):
                    selected_domain_data = available_domains_list[choice_idx]
                    if first_registrar in selected_domain_data['purchase_links']:
                        link_to_open = selected_domain_data['purchase_links'][first_registrar]
                        print(f"\n{Fore.GREEN}Opening {first_registrar} link for {selected_domain_data['domain']}...{Style.RESET_ALL}")
                        opened = open_purchase_link(link_to_open)
                        if opened:
                            print(f"{Fore.GREEN}Browser should have opened. Good luck!{Style.RESET_ALL}")
                        else:
                            print(f"{Fore.YELLOW}If the browser didn't open, you can manually visit:{Style.RESET_ALL}")
                            print(link_to_open)
                        break
                    else:
                        print(f"{Fore.RED}Error: Could not find '{first_registrar}' link for the selected domain.{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}Invalid number. Please enter a number between 1 and {len(available_domains_list)}.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Invalid input. Please enter a number or press Enter.{Style.RESET_ALL}")

    return results

def validate_domain_name(name):
    """Validate if the input is a plausible base domain name part."""
    if not name:
        return False
    if " " in name or "." in name or "/" in name or "\\" in name:
         print(f"{Fore.RED}Invalid characters (space, dot, slashes) found.{Style.RESET_ALL}")
         return False
    if name.startswith('-') or name.endswith('-'):
        print(f"{Fore.RED}Domain part cannot start or end with a hyphen.{Style.RESET_ALL}")
        return False
    if not all(c.isalnum() or c == '-' for c in name):
        print(f"{Fore.RED}Invalid characters. Use only letters, numbers, and hyphens.{Style.RESET_ALL}")
        return False
    return True

def main():
    """Main function to run the domain checker tool."""
    print(f"{Fore.YELLOW}--- Domain Availability Checker ---{Style.RESET_ALL}")
    print("Checks availability using WHOIS and secondary DNS/HTTP checks.")
    print(f"TLDs checked: {', '.join(TOP_20_TLDS)}")
    print("-" * 30)

    while True:
        base_domain = input("Enter the base domain name (e.g., 'mydomain'): ").strip().lower()
        if validate_domain_name(base_domain):
            break

    check_domain_availability(base_domain)
    print(f"\n{Fore.YELLOW}--- Check Complete ---{Style.RESET_ALL}")


if __name__ == "__main__":
    main()