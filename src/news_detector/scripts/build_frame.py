import io
import zipfile

import pandas as pd
import requests

from news_detector.config import settings

FRAME_DIR = settings.domains_csv.parent
FRAME_DIR.mkdir(parents=True, exist_ok=True)

URL = "https://tranco-list.eu/top-1m.csv.zip"  # najnowsza lista; ID zapisz ręcznie ze strony
r = requests.get(URL, timeout=180)
r.raise_for_status()
z = zipfile.ZipFile(io.BytesIO(r.content))
df = pd.read_csv(z.open(z.namelist()[0]), header=None, names=["rank", "domain"])

pl = df[df["domain"].str.endswith(".pl")].copy()
pl["stratum"] = pl["rank"].apply(lambda x: "S1" if x <= 10000 else "S2")
pl.to_csv(FRAME_DIR / "tranco_pl_all.csv", index=False)

print("Domen .pl w top 1M:", len(pl))
print(pl["stratum"].value_counts())

pl[pl.stratum == "S1"].sort_values("rank").head(150).to_csv(
    FRAME_DIR / "review_S1.csv",
    index=False,
)
pl[pl.stratum == "S2"].sample(80, random_state=42).sort_values("rank").to_csv(
    FRAME_DIR / "review_S2.csv",
    index=False,
)
