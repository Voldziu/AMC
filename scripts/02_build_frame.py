import io, zipfile
import pandas as pd
import requests

URL = "https://tranco-list.eu/top-1m.csv.zip"   # najnowsza lista; ID zapisz ręcznie ze strony
r = requests.get(URL, timeout=180)
r.raise_for_status()
z = zipfile.ZipFile(io.BytesIO(r.content))
df = pd.read_csv(z.open(z.namelist()[0]), header=None, names=["rank", "domain"])

pl = df[df["domain"].str.endswith(".pl")].copy()
pl["stratum"] = pl["rank"].apply(lambda x: "S1" if x <= 10000 else "S2")
pl.to_csv("data/frame/tranco_pl_all.csv", index=False)

print("Domen .pl w top 1M:", len(pl))
print(pl["stratum"].value_counts())

# Pliki do ręcznego przeglądu (seed=42, żeby wynik był powtarzalny)
pl[pl.stratum == "S1"].sort_values("rank").head(150).to_csv("data/frame/review_S1.csv", index=False)
pl[pl.stratum == "S2"].sample(80, random_state=42).sort_values("rank").to_csv("data/frame/review_S2.csv", index=False)