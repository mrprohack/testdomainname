import socket

# List of IP addresses
ips = [
    "37.209.192.9",
    "2001:dcd:1:0:0:0:0:9",
    "37.209.194.9",
    "2001:dcd:2:0:0:0:0:9",
    "37.209.196.9",
    "2001:dcd:3:0:0:0:0:9",
    "156.154.172.82",
    "2610:a1:1074:0:0:0:1:82",
    "156.154.173.82",
    "2610:a1:1075:0:0:0:1:82",
    "156.154.174.82",
    "2610:a1:1076:0:0:0:1:82"
]

def reverse_dns_lookup(ip_list):
    for ip in ip_list:
        try:
            host = socket.gethostbyaddr(ip)
            print(f"✅ {ip} → {host[0]}")
        except socket.herror:
            print(f"❌ {ip} → No PTR record found")

# Perform reverse DNS lookup
reverse_dns_lookup(ips)

