import requests

crawls = requests.get("https://index.commoncrawl.org/collinfo.json", timeout=30).json()
for c in crawls:
    print(c["id"], "|", c["name"], "|", c.get("from", ""), "->", c.get("to", ""))
