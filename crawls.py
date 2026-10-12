# pip install requests warcio trafilatura py3langid pandas
import requests
crawls = requests.get("https://index.commoncrawl.org/collinfo.json", timeout=30).json()
for c in crawls[:15]:
    print(c["id"], "|", c["name"])   # wybierzcie crawle VII-IX 2026 i jeden/dwa z 2021