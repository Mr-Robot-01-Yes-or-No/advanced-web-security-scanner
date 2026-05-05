import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import json

visited = set()
results = []

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# 🔗 Get links (simple crawler)
def get_links(url):
    links = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")

        for a in soup.find_all("a", href=True):
            link = urljoin(url, a["href"])
            if link.startswith(url):
                links.append(link)
    except:
        pass

    return list(set(links))


# 🛡️ Security headers check
def check_headers(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        headers = r.headers

        issues = []
        if "X-Frame-Options" not in headers:
            issues.append("Missing X-Frame-Options")
        if "Content-Security-Policy" not in headers:
            issues.append("Missing CSP")
        if "Strict-Transport-Security" not in headers:
            issues.append("Missing HSTS")

        return issues
    except:
        return []


# ⚠️ XSS check (multiple payloads)
def check_xss(url):
    payloads = [
        "<script>alert(1)</script>",
        "\"><script>alert(1)</script>"
    ]

    for payload in payloads:
        test_url = f"{url}?q={payload}"
        try:
            r = requests.get(test_url, headers=HEADERS, timeout=5)
            if payload in r.text:
                return True
        except:
            pass

    return False


# ⚠️ SQLi check (multiple payloads)
def check_sqli(url):
    payloads = [
        "' OR '1'='1",
        "' OR 1=1--",
        "\" OR \"1\"=\"1"
    ]

    for payload in payloads:
        test_url = f"{url}?id={payload}"
        try:
            r = requests.get(test_url, headers=HEADERS, timeout=5)
            if any(err in r.text.lower() for err in ["sql", "syntax", "mysql", "error"]):
                return True
        except:
            pass

    return False


# 🔍 Scan function
def scan(url):
    if url in visited:
        return

    print(f"\n🔍 Scanning: {url}")
    visited.add(url)

    data = {
        "url": url,
        "xss": check_xss(url),
        "sqli": check_sqli(url),
        "header_issues": check_headers(url)
    }

    # 📢 Live output
    print(f"   XSS: {'⚠️ Possible' if data['xss'] else '✔ Safe'}")
    print(f"   SQLi: {'⚠️ Possible' if data['sqli'] else '✔ Safe'}")

    if data["header_issues"]:
        print(f"   Header Issues: {data['header_issues']}")
    else:
        print("   Headers: ✔ Good")

    results.append(data)

    # 🔁 Crawl limited links
    links = get_links(url)
    for link in links[:5]:
        scan(link)


# 💾 Save report
def save_report():
    with open("report.json", "w") as f:
        json.dump(results, f, indent=4)

    print("\n📁 Report saved as report.json")


# ▶️ Main
if __name__ == "__main__":
    target = input("Enter target URL (with http/https): ")
    scan(target)
    save_report()