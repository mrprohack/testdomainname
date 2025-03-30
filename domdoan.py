import requests

def get_all_tlds():
    url = "https://data.iana.org/TLD/tlds-alpha-by-domain.txt"
    
    try:
        response = requests.get(url)
        response.raise_for_status()

        # Parse and clean the list
        tlds = response.text.splitlines()[1:]  # Skip the first line (header)
        tlds = [tld.lower() for tld in tlds]   # Convert to lowercase

        # Save to txt file
        with open("tlds_list.txt", "w") as file:
            file.write("\n".join(tlds))

        print(f"✅ Saved {len(tlds)} TLDs to 'tlds_list.txt'")
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching TLDs: {e}")

# Fetch and save TLDs
get_all_tlds()

