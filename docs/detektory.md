# Detektory zero-shot: Binoculars i Fast-DetectGPT

Instrukcja krok po kroku: jak przepuścić nasze artykuły przez detektory tekstu generowanego przez AI, najpierw lokalnie na Macu, potem większym modelem na GPU w Google Colab.

## 1. Co liczymy

Oba detektory działają *zero-shot*, czyli nie trzeba ich niczego uczyć.
Biorą gotowy model językowy i sprawdzają, jak bardzo tekst jest dla niego przewidywalny.
Tekst z LLM-a jest zwykle przewidywalny w specyficzny sposób.

Używamy pary polskich modeli Bielik:

- **observer**: model bazowy, np. `Bielik-4.5B-v3`,
- **performer**: jego wersja instrukcyjna, np. `Bielik-4.5B-v3.0-Instruct`.

Oba modele muszą mieć ten sam tokenizer.
Kod sprawdza to sam i przerywa pracę, jeśli tokenizery się różnią.

Każdy tekst jest przycinany do pierwszych 512 tokenów (`--max-tokens`).
Za jednym razem z tych samych obliczeń powstają te kolumny w `data/detect/<preset>.csv`:

| kolumna | co to jest | AI, gdy wartość jest |
|---|---|---|
| `binoculars` | **Binoculars** (Hans i in., 2024): perplexity performera / cross-perplexity observer→performer | **niska** |
| `fastdetectgpt_observer` | **Fast-DetectGPT** (Bao i in., 2024) liczony modelem bazowym | **wysoka** |
| `fastdetectgpt_performer` | Fast-DetectGPT liczony modelem instrukcyjnym | **wysoka** |
| `logppl_observer` | zwykła log-perplexity modelu bazowego, najsłabszy punkt odniesienia | **niska** |
| `logppl_performer`, `xppl` | składniki Binoculars, zapisane do analizy | |
| `n_tokens` | ile tokenów faktycznie policzono | |

Raport (punkt 6) zamienia te liczby na decyzję „AI / nie AI” za pomocą progu.

Presety par modeli są w [src/news_detector/detect/models.py](../src/news_detector/detect/models.py):

| preset | modele | pamięć na wagi | gdzie uruchomić |
|---|---|---|---|
| `bielik-1.5b` | Bielik-1.5B-v3 + 1.5B-v3.0-Instruct | ok. 7 GB | Mac M1 Pro 16 GB |
| `bielik-4.5b` | Bielik-4.5B-v3 + 4.5B-v3.0-Instruct | ok. 19 GB, w 8 bitach ok. 9 GB | Google Colab (T4 z `--quantize 8bit`) |

W PolEval 2025 para `bielik-4.5b` dała 79,6% accuracy i była najlepsza z trzech sprawdzonych par.

### Pangram EditLens

Ta sama komenda `score` liczy też trzeci detektor: **Pangram EditLens** (Thai i in., ICLR 2026).
To nie zero-shot, tylko klasyfikator: Llama-3.2-3B z adapterem LoRA i głową o kilku klasach od 0 (człowiek) do n-1 (AI).
Wynik to oczekiwana klasa przeskalowana do [0, 1].

| kolumna w `data/detect/pangram.csv` | co to jest | AI, gdy wartość jest |
|---|---|---|
| `pangram_score` | oczekiwana klasa, 0 = człowiek, 1 = AI | **wysoka** |
| `pangram_bucket` | najbardziej prawdopodobna klasa | **wysoka** |

- Plik nie zależy od presetu, więc nie jest liczony drugi raz przy zmianie pary Bielika. `--no-pangram` pomija ten przebieg, `--pangram-output` zmienia ścieżkę.
- Teksty są przycinane do 1024 tokenów, zapisywane małymi literami i z pojedynczymi spacjami, jak w kodzie autorów.
- Model był uczony tylko na angielskim, więc na polskich artykułach wynik może być słaby. Sprawdź to na Śmigielu (punkt 4.3).
- Wymaga zaakceptowania licencji `meta-llama/Llama-3.2-3B` i `pangram/editlens_Llama-3.2-3B` na Hugging Face (punkt 3.1). Licencja adaptera to CC BY-NC-SA 4.0, tylko do użytku niekomercyjnego.
- `report` i `smigiel-eval` przyjmują kilka plików w `--scores` i łączą je po `text_key`; `make detect-report` i `make smigiel` podają oba.

## 2. Jak używamy naszych zbiorów

**Czy podział train/dev/test był potrzebny?** Do samego liczenia wyników nie: detektory zero-shot niczego się nie uczą, więc liczymy wynik dla *wszystkich* 5026 tekstów.
Podział przydaje się jednak w jednym miejscu, czyli przy ustawianiu progu.
Przyda się też później, gdybyśmy trenowali własny klasyfikator.

**Teksty sprzed ery LLM (2020–2022, `label = 0`) jako kontrola.** Zakładamy, że są pisane przez ludzi.
Na nich ustawiamy próg tak, żeby detektor oznaczał jako AI tylko np. 1% lub 5% z nich.
Ten odsetek to *false positive rate* (FPR), czyli odsetek fałszywych alarmów.

Raport robi to w trzech krokach:

1. **Kalibracja** na tekstach z lat 2020–2022 ze zbiorów `train` i `dev` (2559 tekstów).
2. **Sprawdzenie** na tekstach z lat 2020–2022 ze zbioru `test` (288 tekstów).
   Tych tekstów nie użyto przy ustawianiu progu, więc FPR wyliczony na nich jest uczciwy.
   Jeśli wyjdzie blisko docelowego 1% czy 5%, próg jest stabilny.
3. **Zastosowanie** tego samego progu do tekstów z lat 2023–2025 ze wszystkich zbiorów (2179 tekstów).

Jak czytać wyniki:

- **Test placebo (lata 2020, 2021, 2022 osobno).** Odsetek oznaczonych powinien być mniej więcej równy FPR w każdym z tych lat.
  Jeśli rośnie z roku na rok już przed ChatGPT, detektor reaguje na coś innego niż AI, np. na zmianę tematów albo na to, że model „zna” dany tekst z treningu.
- **Wynik główny.** O ile odsetek oznaczonych w latach 2023–2025 przekracza poziom z lat 2020–2022, w każdej domenie osobno.
  Raport liczy dla każdej domeny jednostronny test Fishera oraz q-value (poprawka Benjaminiego-Hochberga na 44 domeny).

**Kontrola pozytywna: Śmigiel.** Nie mamy żadnego tekstu, o którym *wiemy*, że jest z AI, więc na naszych danych nie zmierzymy czułości detektora.
Dlatego `make smigiel` bierze 1000 oznaczonych polskich tekstów z PolEval 2025 (pół ludzkich, pół z LLM-ów).
Liczy na nich AUC i czułość przy FPR 1% i 5%.
Accuracy Binoculars na tej próbce powinno wyjść około 0,8, tak jak w PolEval.
Jeśli wyjdzie około 0,5, coś jest źle.

**Zastrzeżenia, o których warto napisać w raporcie:**

- Bielik był trenowany m.in. na polskim Common Crawl, więc część naszych artykułów mógł „widzieć”.
  Teksty znane modelowi wyglądają na bardziej przewidywalne.
  Test placebo i porównanie z latami 2020–2022 częściowo to kontrolują.
- Część tekstów z lat 2020–2022 może być szablonowa (np. komunikaty, wyniki sportowe).
  Nie pochodzi z LLM-a, ale może podnosić FPR w niektórych domenach.
- Na jedną domenę przypada średnio około 114 tekstów, więc przedziały ufności dla pojedynczych domen są szerokie.

## 3. Jednorazowe przygotowanie (Mac)

### 3.1 Konto i token Hugging Face

Modele pobieramy z Hugging Face.

1. Załóż konto na <https://huggingface.co/join>.
2. Wejdź na strony modeli v3 i kliknij **„Agree and access repository”**. Dostęp przyznawany jest od razu:
   - <https://huggingface.co/speakleash/Bielik-1.5B-v3>
   - <https://huggingface.co/speakleash/Bielik-1.5B-v3.0-Instruct>
   - <https://huggingface.co/speakleash/Bielik-4.5B-v3>
   - <https://huggingface.co/speakleash/Bielik-4.5B-v3.0-Instruct>
   - <https://huggingface.co/meta-llama/Llama-3.2-3B> (Pangram; zatwierdzenie może potrwać)
   - <https://huggingface.co/pangram/editlens_Llama-3.2-3B> (Pangram)

3. Utwórz token na <https://huggingface.co/settings/tokens>: **Create new token**, typ **Read**.
   Skopiuj go (zaczyna się od `hf_`).

### 3.2 Biblioteki do liczenia (opcjonalna grupa `detect`)

```bash
uv add --group detect "torch>=2.9" "transformers>=5.0" "accelerate>=1.10" "peft>=0.18" "bitsandbytes>=0.48; sys_platform == 'linux'"
```

Co robi ta komenda:

- dopisuje do `pyproject.toml` grupę `detect` i aktualizuje `uv.lock`,
- instaluje do `.venv`:
  - `torch`: obliczenia, na Macu przez GPU Apple (MPS),
  - `transformers`: pobieranie i uruchamianie modeli,
  - `accelerate`: rozmieszczanie modeli na GPU,
  - `peft`: wczytanie adaptera LoRA Pangrama,
  - `bitsandbytes`: tylko na Linuksie, do kwantyzacji 8-bitowej w Colabie.
- Na Macu to około 1 GB.
- Grupa jest opcjonalna: zwykłe `uv sync` u reszty zespołu dalej jej nie instaluje.

**Zacommituj zmienione `pyproject.toml` i `uv.lock`.** Colab zainstaluje wtedy dokładnie te same wersje.

### 3.3 Logowanie do Hugging Face

```bash
uv run --group detect hf auth login
```

Wklej token, gdy program o niego poprosi.
Na pytanie o git credential możesz odpowiedzieć `n`.
Token zapisuje się w `~/.cache/huggingface/token`, więc robisz to tylko raz.

### 3.4 Test jednostkowy obliczeń

```bash
uv run --group detect python -m unittest tests.test_detect -v
```

Wszystkie testy powinny pokazać `ok`, w tym `MetricsTest`.
Ten test porównuje zwektoryzowane wzory z prostą pętlą.

## 4. Uruchomienie lokalne na Macu (`bielik-1.5b`)

### 4.1 Próba na 20 tekstach

```bash
uv run --group detect python -m news_detector.detect score --preset bielik-1.5b \
    --limit 20 --output data/detect/proba.csv
```

- Za pierwszym razem pobierze się około 6,5 GB modeli do `~/.cache/huggingface/`. To jednorazowe.
- Na końcu w logu powinno być `Scored 20 texts into data/detect/proba.csv`.
- Zajrzyj do pliku. Wartości `binoculars` powinny wyjść w okolicach 0,7–1,2.
- Potem usuń `data/detect/proba.csv` i `data/detect/proba.meta.json`.

### 4.2 Pełny przebieg

```bash
make detect            # = PRESET=bielik-1.5b
```

- Wyniki trafiają do `data/detect/bielik-1.5b.csv`, a ustawienia przebiegu do `data/detect/bielik-1.5b.meta.json`.
- Szacunkowo potrwa to od kilku do kilkunastu godzin na M1 Pro. To zgrubna ocena: tqdm pokaże prawdziwe tempo po kilku minutach.
- Mac nie może zasnąć. Podłącz zasilanie i uruchom z `caffeinate`:

  ```bash
  caffeinate -i make detect
  ```

- **Przerwanie (Ctrl+C) nic nie psuje.** Wyniki zapisują się na bieżąco, a ponowne `make detect` liczy tylko brakujące teksty.

### 4.3 Kontrola na Śmigielu

```bash
make smigiel           # pobiera ok. 27 MB do data/external/ (poza gitem), liczy 1000 tekstów
```

Na końcu wypisze się tabela z kolumnami `auc`, `accuracy_median` i `recall_at_fpr_0.01/0.05`.

### 4.4 Raport

```bash
make detect-report
```

Tabele trafiają do `data/detect/reports/bielik-1.5b/`, a najważniejsze liczby wypisują się w logu (punkt 6).

## 5. Większy model na GPU w Google Colab

Colab to notebook w przeglądarce, który działa na tymczasowym komputerze Google z kartą graficzną.
Ten komputer jest pusty i znika po zakończeniu sesji, więc w każdej sesji pobieramy kod z GitHuba i modele z Hugging Face, a wyniki zapisujemy na Google Drive.
Nie trzeba niczego wgrywać ręcznie.

### 5.1 Raz: wypchnij kod na GitHuba

Zmiany mogą zostać na gałęzi `detectors-w`. Nie trzeba ich łączyć z `main`, bo notebook pobiera właśnie tę gałąź (`git clone -b detectors-w`).
Muszą być jednak **wypchnięte na GitHuba**, bo Colab nie widzi plików na Twoim dysku.

```bash
git add .gitignore Makefile README.md pyproject.toml uv.lock docs src/news_detector/detect tests/test_detect.py
git commit -m "Add zero-shot detectors"
git push -u origin detectors-w
```

Nie dodajemy katalogu `scripts/`, bo jest niezwiązany z detektorami.
Po każdej późniejszej poprawce kodu trzeba zrobić `git push`, a w Colabie uruchomić od nowa komórkę 1 (świeży `git clone`).

### 5.2 Wybór GPU

W Colabie: **Runtime → Change runtime type → Hardware accelerator**.

| GPU | pamięć | co uruchomić |
|---|---|---|
| **T4** (wystarcza) | 15 GB | `bielik-4.5b` z `--quantize 8bit` |
| L4 / A100 (jeśli dostępne w planie studenckim) | 24 / 40 GB | `bielik-4.5b` bez kwantyzacji, szybciej |

Para 4.5B ma w 16 bitach około 19 GB wag, więc na T4 się nie zmieści.
Opcja `--quantize 8bit` zmniejsza ją do około 9 GB i wyniki zmieniają się tylko nieznacznie.
Zapisz w opisie projektu, jaki wariant uruchomiono: ustawienia są zapisywane w pliku `.meta.json` obok wyników.

### 5.3 Komórki notebooka

Utwórz nowy notebook (<https://colab.research.google.com> → **New notebook**).
Wklej poniższe komórki, każdą osobno, i uruchamiaj po kolei.

**Przed komórką 1: sekret z Hugging Face.**
Kliknij ikonę **kluczyka** po lewej stronie (zakładka *Secrets*) → **Add new secret**:

- nazwa: `HF_TOKEN`, wartość: token z Hugging Face (punkt 3.1), włącz przełącznik **Notebook access**,
- jeśli repo `Voldziu/AMC` jest prywatne, dodaj też `GH_TOKEN` (token GitHub z uprawnieniem *Contents: Read* do tego repo).

**Komórka 1: sekrety, Google Drive i pobranie kodu.**
Przy montowaniu Drive przeglądarka poprosi o zgodę.

```python
import os
from google.colab import drive, userdata

os.environ["HF_TOKEN"] = userdata.get("HF_TOKEN")
drive.mount("/content/drive")
os.makedirs("/content/drive/MyDrive/amc-detect", exist_ok=True)
repo = "github.com/Voldziu/AMC.git"
try:
    repo = f"x-access-token:{userdata.get('GH_TOKEN')}@{repo}"
except Exception:
    pass  # publiczne repo, token niepotrzebny
!rm -rf /content/AMC
!git clone -q -b detectors-w https://{repo} /content/AMC
```

**Komórka 2: instalacja (kilka minut) i sprawdzenie GPU.**

```python
!pip install -q uv
%cd /content/AMC
!uv sync --group detect
!uv run --group detect python -c "import torch; print(torch.cuda.get_device_name(0))"
```

Ostatnia linia powinna wypisać nazwę karty, np. `Tesla T4`.

**Komórka 3: próba na 20 tekstach.**
Pobierze modele, co trwa kilka minut. Jeśli tu jest błąd, nie ma sensu uruchamiać pełnego przebiegu.

```python
!uv run --group detect python -m news_detector.detect score --preset bielik-4.5b \
    --quantize 8bit --limit 20 --output /content/proba.csv
```

Na T4 zostaw `--quantize 8bit`. Na L4 lub A100 usuń tę opcję i dodaj do komórki 4 `--batch-size 2` (L4) albo zostaw domyślne (A100).

**Komórka 4: pełny przebieg.**
Wynik zapisuje się od razu na Drive. Jeśli sesja się zerwie, uruchom jeszcze raz komórki 1, 2 i 4: policzy tylko brakujące teksty.

```python
!uv run --group detect python -m news_detector.detect score --preset bielik-4.5b \
    --quantize 8bit --output /content/drive/MyDrive/amc-detect/bielik-4.5b.csv
```

**Komórka 5: kontrola na Śmigielu.**

```python
!uv run python -m news_detector.detect smigiel-sample
!uv run --group detect python -m news_detector.detect score --preset bielik-4.5b \
    --quantize 8bit --input data/external/smigiel/sample.csv \
    --output /content/drive/MyDrive/amc-detect/smigiel-bielik-4.5b.csv
!uv run python -m news_detector.detect smigiel-eval \
    --scores /content/drive/MyDrive/amc-detect/smigiel-bielik-4.5b.csv
```

Przez cały czas liczenia **nie zamykaj karty z notebookiem** i nie zostawiaj jej bez aktywności, bo Colab rozłącza nieużywane sesje.

### 5.4 Po powrocie na Maca

Pobierz z Google Drive (`amc-detect/`) pliki `bielik-4.5b.csv` i `bielik-4.5b.meta.json` do `data/detect/` w repo i zrób raport:

```bash
make detect-report PRESET=bielik-4.5b
uv run python -m news_detector.detect smigiel-eval --scores data/detect/smigiel-bielik-4.5b.csv
```

Pliki z wynikami zawierają tylko hashe tekstów i liczby, bez treści artykułów, więc można je commitować.

### 5.5 Inne opcje, gdyby Colab nie wystarczył

- **Kaggle:** darmowe około 30 godzin GPU tygodniowo (2× T4, wymaga weryfikacji telefonu). Komórki wyglądają prawie tak samo jak w Colabie, tylko sekrety bierze się z `kaggle_secrets`, a kod klonuje do `/tmp`.
- **PLGrid:** darmowe superkomputery dla polskich uczelni (konto przez portal PLGrid i dołączenie do grantu).

## 6. Jak czytać raport

`data/detect/reports/<preset>/` zawiera:

- **`calibration.csv`**: próg (`threshold`, a `flag_if` mówi, czy oznaczamy wartości poniżej czy powyżej) oraz FPR na danych kalibracyjnych i na odłożonych (`fpr_heldout` z przedziałem ufności).
  Ważne jest `fpr_heldout`: powinno wyjść blisko `target_fpr`.
- **`by_year.csv`**: odsetek oznaczonych (`rate`, z 95% przedziałem ufności) w każdym roku.
  Lata 2020–2022 to test placebo (powinny być płaskie, blisko FPR).
  Lata 2023–2025 to wynik.
- **`by_domain.csv`**: dla każdej domeny odsetek przed i po 2023 r., `excess` (różnica), `p_value` i `q_value`.
  Kandydaci na „farmy treści” to domeny z dużym `excess` i małym `q_value` przy kilku detektorach jednocześnie.

Porównanie Mac i GPU:

1. Zestaw `smigiel-eval` dla różnych presetów. Który lepiej oddziela znane AI od ludzi?
2. Porównaj `by_year.csv` i `by_domain.csv` między presetami. Czy wskazują te same domeny?

## 7. Najczęstsze problemy

| objaw | co zrobić |
|---|---|
| `401` / `GatedRepoError` przy pobieraniu | nie zaakceptowano modelu na HF (3.1) albo brak logowania (3.3; w Colabie sekret `HF_TOKEN`) |
| `out of memory` / `MPS backend out of memory` | zmniejsz `--batch-size` (np. 2 lub 1) albo `--max-tokens 384` (wtedy zmień też `--output`, bo to inne ustawienia) |
| `Non-finite ... overflowed` | 16-bitowe wagi przepełniły się; na Macu spróbuj `--dtype float16` albo `--dtype float32` (tylko 1.5B), na T4 dodaj `--quantize 8bit` |
| `... was written with different settings` | do tego pliku liczono z innymi ustawieniami; podaj inne `--output` |
| `tokenize text differently` | wybrana para modeli ma różne tokenizery; Binoculars wymaga wspólnego |
