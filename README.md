# Domain Availability Checker

A command-line tool to quickly check domain name availability across multiple TLDs (Top-Level Domains).

## Features

- Check domain availability across 20 popular TLDs simultaneously
- Verify domain status using multiple methods:
  - WHOIS lookups
  - DNS resolution checks
  - HTTP/HTTPS response validation
- Display expiration dates for registered domains
- Generate purchase links for available domains
- Interactive browser integration to quickly visit registrar sites

## Installation

1. Ensure you have Python 3.6+ installed
2. Clone this repository:
   ```
   git clone https://github.com/mrprohack/testdomainname.git
   cd testdomainname
   ```
3. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the tool with:

```
python domaintest.py
```

The tool will prompt you to enter a base domain name (e.g., "example") and then check its availability across multiple TLDs.

### Supported TLDs

The tool checks availability across these popular TLDs:
- com, net, org, io, co
- ai, app, dev, me, info
- xyz, tech, online, site, store
- blog, shop, biz, edu, ly

## How It Works

The tool uses a multi-step verification process:

1. First checks WHOIS records to determine if a domain is registered
2. For inconclusive WHOIS results, performs secondary verification:
   - Attempts DNS resolution
   - Tries HTTP/HTTPS connections
3. Provides purchase links to popular registrars (Porkbun, GoDaddy) for available domains

## Example

```
--- Domain Availability Checker ---
Checks availability using WHOIS and secondary DNS/HTTP checks.
TLDs checked: com, net, org, io, co, ai, app, dev, me, info, xyz, tech, online, site, store, blog, shop, biz, edu, ly
------------------------------

Enter the base domain name (e.g., 'mydomain'): coolproject

Checking availability for 'coolproject' across 20 TLDs...
Using up to 10 parallel checks.
Note: Results rely on WHOIS and DNS/HTTP checks. Availability not guaranteed until registration.
============================================================
❌ coolproject.com - Taken (WHOIS)
   Registrar: GoDaddy.com, LLC (Expires: 2023-04-12)
✅ coolproject.dev - Available
   (WHOIS empty) (Checked via DNS/HTTP)
   → Porkbun: https://porkbun.com/checkout/search?q=coolproject.dev
   → GoDaddy: https://www.godaddy.com/domainsearch/find?domainToCheck=coolproject.dev
...

============================================================

Summary:
Total domains checked: 20
Available: 8
Taken/Unavailable: 12

Available Domains Found:
1. coolproject.dev
   Buy at Porkbun: https://porkbun.com/checkout/search?q=coolproject.dev
...

Open a purchase link in browser?
Enter number (1-8) to open the 'Porkbun' link, or just press Enter to skip:
```

## Limitations

- Domain availability results are not guaranteed until registration
- WHOIS information may be incomplete or rate-limited for some TLDs
- Some TLDs (especially .ai, .io, .co, .me) may have inconsistent availability reporting

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
