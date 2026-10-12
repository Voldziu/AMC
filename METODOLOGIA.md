# Farmy treści AI w polskojęzycznych serwisach „newsowych” — plan badawczy

> Pytanie badawcze: **Ile polskojęzycznych serwisów „newsowych” publikuje masowo treści generowane?**
> Dokument = projekt badania + odpowiedzi na pytania zespołu. Jest żywy: zmiany decyzji commitujcie z uzasadnieniem.

---

## 0. Odpowiedzi na Wasze pytania (skrót)

| Pytanie | Odpowiedź |
|---|---|
| Czy pobierać dane sprzed AI? | **Główną próbę — nie** (okno: III kwartał 2026). **Ale** mały korpus z lat 2019–2021 jest Wam potrzebny jako *grupa kontrolna*: to jedyne teksty o pewnej proweniencji „człowiek”, więc jedyny uczciwy sposób zmierzenia fałszywych alarmów detektora na polskich newsach. Skrypt obsługuje oba przez `--corpus target|control`. |
| Ostatnie 3 miesiące czy cały 2026? | Zacznijcie od **1.07–30.09.2026** (`--window-start/--window-end`). Rozszerzenie to zmiana dwóch parametrów, ale mnoży koszt detektora. Trend w czasie ma sens dopiero, gdy okno ≥ 6 miesięcy. |
| Czy lista domen wystarczy? | **Nie.** 26 domen nie pozwala odpowiedzieć na „ile”. Potrzebujecie zdefiniowanej populacji, ramy próby i losowania w warstwach: cel **≥150–300 domen** (sekcja 4). Dopóki ramy nie ma, uczciwa odpowiedź brzmi „wśród N zbadanych serwisów k wykazuje…”. |
| Wszystkie artykuły czy kilka? | **Próba: ok. 25–30 artykułów na domenę** (min. 20; domenę oceniamy od 10). Przy 30 artykułach domena z udziałem AI ≥80% jest rozpoznawana z prawdopodobieństwem ≈100% (tabela w sekcji 5). Przy ograniczonym budżecie **wolcie więcej domen niż więcej artykułów na domenę**. |
| Jakie dane oprócz tekstu? | Datę publikacji i jej źródło, autora (tylko flaga), reklamy, JSON-LD, generator CMS, nagłówki, linki, duplikaty między domenami, a na poziomie domeny ręczny audyt (stopka redakcyjna, wydawca, ujawnienie AI). Pełna lista: sekcja 6. |
| Jak stwierdzić, że artykuł jest generowany? | **Nie da się tego stwierdzić z pewnością z samego tekstu.** Używamy *instrumentu* (detektor — Pangram obsługuje polski), którego rzetelność **mierzymy** na gold standard i **korygujemy** o jego błędy. Dowody niezależne (ślady chatbota, duplikaty, cechy strukturalne) służą do trafności konstruktu i do audytu domen. |
| Mamy robić zbiory treningowe/testowe? | **Zbiór walidacyjny (gold standard) — tak. Trenowanie własnego klasyfikatora jako głównego narzędzia — nie.** Gold dzielicie na *dev* (wybór progu) i *test* (raportowane metryki), po grupach (sekcja 7). Własny model tylko jako opcjonalny dodatek, trenowany wyłącznie na dev. |
| Czy „F1 klasyfikatora” to wynik? | **Nie.** Kurs ocenia wniosek zgodny z dowodami i rzetelną walidację instrumentu. Wynik negatywny („instrument nie nadaje się do pomiaru”, „zjawisko rzadkie”) jest pełnoprawny. |

---

## 1. Operacjonalizacja pytania

**Jednostka analizy: domena (serwis)**, nie artykuł. „Ile serwisów” = liczba domen spełniających definicję.

| Pojęcie | Definicja robocza | Uwagi |
|---|---|---|
| Serwis „newsowy” | Polskojęzyczna strona, która publikuje bieżące wiadomości/informacje w formie artykułów i wygląda jak serwis informacyjny; aktywna w oknie badania (≥ 10 artykułów ≥150 słów w próbie). | Kryteria `is_news` w `CODEBOOK.md`. Decyzję podejmuje się ze strony głównej, dwóch oceniających. |
| Tekst „generowany” | Tekst, którego istotną część wytworzył model językowy bez znaczącej redakcji ludzkiej. | Detektor mierzy *podobieństwo do tekstu AI*, nie proweniencję. Pangram rozróżnia: człowiek / AI-assisted / AI. Główna miara: `fraction_ai`; wariant szeroki `ai_any = fraction_ai + fraction_ai_assisted`. |
| Artykuł oznaczony | Wynik detektora ≥ próg wybrany **na dev** tak, by FPR(dev) ≤ 1%. | Próg zamrażacie przed oglądaniem wyników na danych docelowych. |
| „Masowo” | Skorygowany udział artykułów AI w domenie **≥ τ**. Główne τ = **0,5**; analiza odporności τ ∈ {0,2; 0,3; 0,5; 0,8}. | Wolumen (ile/dzień) jest poza zasięgiem próby z CC; opcjonalnie z map witryn (sekcja 6). |
| Farma treści AI (poziom jakościowy) | Cztery kryteria NewsGuard: (1) znaczna część treści z AI, (2) brak istotnego nadzoru człowieka, (3) wygląda jak serwis redakcyjny, (4) brak ujawnienia AI. | NewsGuard nie obejmuje polskiego (16 języków bez PL) → to realna luka badawcza, ale też brak gotowej listy do porównania. |

**Hipotezy** (przykład; lead je zamraża na M1):

- **H1 (gradient):** odsetek domen „masowo AI” rośnie od S1 (czołówka rankingu) przez S2 do S3 (długi ogon).
- **H2 (konwergencja):** domeny oznaczone przez detektor różnią się od reszty niezależnymi cechami (brak podpisów autorów, więcej reklam, duplikaty między domenami, ślady chatbota) — to sprawdzian, że instrument mierzy coś realnego.
- **H0/wynik negatywny:** w badanych warstwach jest ≈0 takich domen **albo** detektor nie przechodzi walidacji na polskich newsach. Oba wyniki są pełnoprawne — pod warunkiem uczciwej walidacji.

---

## 2. Co było nie tak w skrypcie `v0.1` (i co zmieniono w `v0.2`)

| # | Problem | Skutek | Poprawka w `collect.py` |
|---|---|---|---|
| 1 | Brak filtra po **dacie publikacji**; crawl z IX 2026 zawiera strony archiwalne (np. z 2015 r.) | Stare artykuły w próbie — to Wasz główny problem | `--window-start/--window-end`; filtr po `pub_date` z JSON-LD/meta/`<time>`/URL; kolumna `pub_date_source`; odrzucenia `out_of_window` / `no_date` liczone w podsumowaniu |
| 2 | Jeden crawl | Okno 3 miesięcy to kilka crawlów | `--crawls auto` wybiera crawle pokrywające okno (z `collinfo.json`); `--max-crawls` |
| 3 | `kobieta.onet.pl` jest poddomeną `onet.pl` | Podwójne liczenie / niejasna jednostka | Poddomeny wymienione na liście są wykluczane z domeny nadrzędnej; `frame.py check` je zgłasza |
| 4 | Regex `og:type` zależny od kolejności atrybutów; JSON-LD szukany tylko w pierwszych 300 kB | Fałszywe odrzucenia „not_article” | Parser meta niezależny od kolejności; pełny JSON-LD (`@graph`, listy typów) |
| 5 | `Range` zignorowany → serwer zwraca 200 + cały WARC | Pobranie gigabajtów | `stream=True`, przerwanie przy 200 |
| 6 | Wszystkie kody ≠200/404 ponawiane 5× | Zbędny ruch, wolne | Ponawiamy tylko 429/5xx (z `Retry-After`) |
| 7 | Odrzucanie adresów z `?` | Gubi `?p=123` (WordPress) | `QUERY_OK` dla `?p=`/`?id=` |
| 8 | Pusty wynik zapisywany jako „pobrane” | Domena nigdy nie zostaje ponowiona | Zapis atomowy `.tmp → .jsonl`; `--force` |
| 9 | Dedup tylko wewnątrz domeny, bez zapisu duplikatów między domenami | Gubicie sygnał farm (kopiowanie) | `features.py`: MinHash/LSH wewnątrz i **między** domenami |
| 10 | 20 art./domenę, 3 strony indeksu | Za mało, mocno obciążone alfabetycznie | Domyślnie 30 art., 5 stron/crawl, `--max-fetch 400`; ograniczenie opisane w sekcji 10 |
| 11 | Brak cech do analizy (reklamy, autor, generator CMS…) | Brak dowodów zbieżnych | `html_features()` + flagi |
| 12 | Brak korpusu kontrolnego | Nie zmierzycie FPR detektora | `--corpus control` + okno 2019–2021 |

> **Ważne:** skrypt zbierający nie mógł być uruchomiony na prawdziwym Common Crawl w środowisku, w którym powstał (brak dostępu do sieci CC). Przetestowany jest na **atrapie serwera CC** z prawdziwymi plikami WARC (`tests/`). Pierwszy krok u Was: `--only onet.pl --n 5` i obejrzenie wyników. Najbardziej prawdopodobne miejsca na korektę: pola `from/to` w `collinfo.json` (jest zapas: parsowanie z numeru tygodnia) oraz wydajność (ile kandydatów faktycznie mieści się w oknie).

---

## 3. Okno czasowe i crawle

- Okno domyślne: **1.07–30.09.2026** (kwartał kalendarzowy → łatwy do powtórzenia). Crawle: `--crawls auto` bierze te, które kończą się po początku okna i zaczynają nie później niż 30 dni po jego końcu (artykuł z września mógł być zebrany w październiku).
- Filtr egzekwujemy **po dacie publikacji artykułu**, nie po dacie crawla.
- Artykuły bez daty domyślnie odrzucamy (`no_date`), **ale uwaga:** farmy mogą nie podawać dat, więc to ryzyko obciążenia *w dół*. Raportujcie liczbę `no_date` per domena (jest w `collect_summary_target.csv`) i zróbcie analizę z `--accept-undated`.
- Ulepszenie wydajności (opcjonalne): `--prefer-dated` najpierw bierze adresy z datą w URL w oknie. Szybsze, ale obciążone ku sekcjom z datą w adresie — używajcie świadomie i odnotujcie.
- Rozszerzenie na cały 2026: `--window-start 2026-01-01`. Jeśli chcecie analizę miesięczną, potrzebujecie ≥ 10 artykułów/domenę/miesiąc, więc próba rośnie kilkukrotnie.

---

## 4. Populacja, rama próby i schemat losowania (najważniejsze dla „ile”)

**Problem z obecną listą.** To nie jest próba populacji: dominuje czołówka rankingu (S1), a S3 wygląda na ręcznie dobrane serwisy polityczne/alternatywne. Farmy AI to zwykle anonimowe, młode domeny o „neutralnych” nazwach — **rzadko ma je ranking Tranco**. Jeśli ramę zbudujecie z rankingów, farm w niej nie będzie, a wynik „0” byłby artefaktem ramy.

**Zasada:** odpowiedź na „ile” wymaga (a) populacji, (b) ramy, (c) losowania w warstwach, (d) wag. Gdy któregoś brakuje, zmieniamy *zakres twierdzenia*, nie metodę.

| Warstwa | Opis | Cel | Co wolno twierdzić |
|---|---|---|---|
| **S1** | Czołówka (np. rank Tranco < 10 000), serwisy informacyjne | **Spis** (wszystkie, ~30–50) | „Z N największych serwisów k…” — bez błędu doboru |
| **S2** | Środek rankingu (np. 10 000–1 000 000), `.pl` + klasyfikacja `is_news` | **~100, losowanie** z jawnej ramy | Ekstrapolacja na całą warstwę z przedziałem ufności (`--frame-sizes`, `--extrapolate`) |
| **S3** | Długi ogon, poza rankingiem — tu są farmy | **≥100–150**, z ≥3 niezależnych źródeł | Jeśli nie ma ramy: **tylko „wśród N zbadanych”** (dolne ograniczenie), bez ekstrapolacji |

**Jak budować S3** (źródła do zweryfikowania pod kątem dostępności i licencji):

1. **Metoda wspólnych tematów:** weźcie 10–20 głównych newsów danego dnia, wyszukajcie ich nagłówków/zdań w wyszukiwarce/Google News i zbierzcie domeny spoza S1/S2 — farmy przepisują popularne newsy, więc wypłyną. Powtórzcie w kilku dniach okna.
2. Domeny z list organizacji fact-checkingowych i badaczy dezinformacji (sprawdźcie, czy publikują listy domen) — to jednak populacja o innym profilu (dezinformacja ≠ farma AI), zaznaczcie w `source_note`.
3. Z samego Common Crawl: hosty `.pl` o dużej liczbie stron z `og:type=article`, spoza Tranco (graf hostów CC — duże pliki, pobierać z sieci o dobrym łączu).
4. Linki wychodzące z agregatorów i stron-rejestrów mediów.
5. Rejestry formalne (np. rejestr dzienników i czasopism) — dają domeny *legalnych* tytułów, nie farm; potrzebne jako punkt odniesienia.

W kolumnie `source_note` zapisujcie źródło każdej domeny — dzięki temu można liczyć wyniki per źródło i pokazać, jak wynik zależy od sposobu doboru.

**Decyzje do podjęcia na M1:** (i) czy `kobieta.onet.pl` to osobna jednostka czy część `onet.pl` (rekomendacja: portal wielotematyczny = jedna domena, o ile nie stosuje innej polityki redakcyjnej; tak czy inaczej opiszcie); (ii) kto i według jakich kryteriów przypisuje `is_news` (dwóch oceniających, kappa); (iii) czy `S3` to losowanie czy zbiór celowy.

`python src/frame.py check` wykrywa duplikaty, poddomeny i drukuje przypomnienia. `frame.py audit` tworzy szablony audytu.

---

## 5. Ile danych — liczby

**Niepewność odsetka domen w warstwie** (przedział Wilsona 95%; `python src/frame.py ci-table`):

| n domen | p=5% | p=10% | p=25% | p=50% |
|---:|---|---|---|---|
| 30 | 1,8–21,3% | 3,5–25,6% | 14,2–44,4% | 33,2–66,8% |
| 50 | 1,1–13,5% | 4,3–21,4% | 14,3–37,4% | 36,6–63,4% |
| 100 | 2,2–11,2% | 5,5–17,4% | 17,5–34,3% | 40,4–59,6% |
| 150 | 2,7–10,2% | 6,2–15,8% | 19,0–32,8% | 42,1–57,9% |
| 300 | 3,1–8,1% | 7,1–13,9% | 20,4–30,2% | 44,4–55,6% |

→ Przy 100–150 domenach w warstwie możecie wskazać rząd wielkości (np. „5–15%”), przy 30 tylko, że „nie jest to zjawisko dominujące”. Przy rzadkim zjawisku (p≈5%) nawet 300 domen daje szeroki przedział — zaplanujcie sformułowania z góry.

**Klasyfikacja pojedynczej domeny przy m artykułach** (założenie: czułość 0,9, swoistość 0,99; prawdopodobieństwo uznania za „masowo AI”, τ=0,5):

| m | udział AI w domenie 0% | 20% | 40% | 60% | 80% | 100% |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0% | 2% | 29% | 72% | 97% | 100% |
| 20 | 0% | 0% | 15% | 74% | 99% | 100% |
| 30 | 0% | 0% | 16% | 84% | 100% | 100% |
| 50 | 0% | 0% | 11% | 91% | 100% | 100% |

→ **Domeny „czyste” i „farmy” są rozpoznawane niezawodnie już przy m=20–30.** Niepewne są domeny „mieszane” (40–60%) — i tam nic nie zdziała wiele więcej artykułów, bo problemem jest definicja progu, nie próbkowanie. Dlatego raportujemy **trzy klasy** (tak / niepewne / nie), nie sztuczną dychotomię.

**Rekomendowana próba:** 150–300 domen × 25–30 artykułów ≈ 4–9 tys. artykułów.

**Koszt detektora — policzcie przed startem:** `python src/detect.py --corpora target control synthetic --dry-run`. Przykład: 150 domen × 25 art. × ~350 słów ≈ 1,3 mln słów; przy cenie orientacyjnej z dokumentacji Pangram (~0,05 USD/100 słów, ceny mogą się zmienić) to ok. 650 USD **plus** gold standard (ok. 600 tekstów ≈ 200 tys. słów ≈ 100 USD). Dlatego:

1. **Zapytajcie prowadzącego** o dostęp do Pangrama (kurs sam go używa) i **napiszcie do Pangram o dostęp akademicki** — strona API wspomina o darmowym dostępie dla badaczy. Nie zakładajcie, że go dostaniecie.
2. Redukcja kosztu: `--max-words 400` (pierwsze 400 słów), pilotaż 10 art./domenę, a resztę dopiero dla domen niepewnych (dwuetapowo; opiszcie jako sequential design).
3. Plan B: otwarty detektor zero-shot (np. Binoculars / Fast-DetectGPT z polskojęzycznym modelem otwartym) — słabszy, wymaga GPU, **ale przechodzi tę samą walidację** i ten sam potok (adapter zapisuje `scores_*.jsonl` z `article_id`, `fraction_ai`).

---

## 6. Co zbierać — pola i po co

| Warstwa dowodów | Pola | Po co |
|---|---|---|
| **Identyfikacja/proweniencja** | `url`, `crawl_id`, `warc_filename/offset/length`, `crawl_timestamp`, `article_id` | Odtwarzalność (każdy artykuł można pobrać ponownie z WARC) |
| **Czas** | `pub_date`, `pub_date_source`, `mod_date` | Okno; wiarygodność dat; `mod_date` ≠ `pub_date` — farmy często „odświeżają” |
| **Tekst** (prywatnie) | `text`, `n_words`, `lang`, `lang_conf`, `text_sha1` | Wejście detektora; dedup |
| **Struktura HTML** | `article_signal`, `jsonld_types`, `og_type`, `has_canonical`, `generator`, `n_h2/n_h3/n_li/n_p_html`, `n_img/n_img_alt`, `n_ext_links`, `n_ad_markers`, `html_kb`, `publisher_name` | Dowody zbieżne: monetyzacja (reklamy), szablonowość, CMS |
| **Autorstwo** | `author_present` (nazwisko tylko w danych prywatnych) | Brak podpisów ≠ AI, ale to cecha farm; RODO |
| **Stylometria** (`features.py`) | zmienność długości zdań, TTR, interpunkcja, cytaty, markery źródeł, `llm_phrase_per_1000w` | **Eksploracyjne** — nie są dowodem bez walidacji |
| **Ślady AI** | `leak_flag` (reszty po chatbocie), `disclosure_flag` (samodeklaracja) | Pozytywy „twarde” do gold; trzeba je weryfikować ręcznie |
| **Sieć** | `near_dup_same_domain_max`, `near_dup_cross_domain` | Kopiowanie/parafraza między serwisami; **uwaga:** przedruki agencyjne (PAP) to też duplikaty, ale nie AI |
| **Domena** (ręcznie, `frame.py audit`) | stopka redakcyjna, redaktor naczelny, wydawca, podpisy, ujawnienie AI, gęstość reklam, nazwa „udaje” portal | Kryteria NewsGuard; weryfikacja domen oznaczonych |
| **Opcjonalnie** | Wiek domeny (WHOIS/RDAP — sprawdźcie dostępność dla `.pl`), liczba URL w mapie witryny z `lastmod` (wolumen publikacji) | Operacjonalizacja „masowo” jako *wolumenu*, nie tylko udziału |

**Przedruki agencyjne** (PAP, Reuters) to główne ryzyko fałszywych alarmów i fałszywej „masowości” — oznaczajcie je (`src_marker_count`, `near_dup_cross_domain`) i liczcie wyniki z nimi i bez nich.

---

## 7. Jak ustalić, które artykuły są generowane: instrument, nie intuicja

**Podejście: instrument + pomiar jego błędów + korekta.** Nikt (ani człowiek, ani detektor) nie rozpozna AI w polskim newsie z pewnością; rozpoznawanie „na oko” jest bliskie losowemu. Dlatego:

1. Instrument: Pangram (obsługuje polski; zwraca `fraction_ai`, `fraction_ai_assisted`, `fraction_human`, okna tekstu).
2. **Walidacja na gold standard** (poniżej) → czułość, swoistość, próg, analiza błędów.
3. **Korekta** udziału w domenie o błędy instrumentu (Rogan–Gladen) z propagacją niepewności.
4. **Dowody zbieżne** (sekcja 6) + audyt ręczny domen oznaczonych — nie zmieniają liczby, ale pokazują, czy instrument mierzy to, co chcemy.

### Skład gold standard (zbiór WALIDACYJNY, nie treningowy)

| Zbiór | Etykieta | Źródło | Rozmiar (min.) | Rola |
|---|---|---|---|---|
| **G1** pre-LLM | człowiek | te same domeny, lata 2019–2021 (`collect --corpus control`) | ≥300 z ≥30 domen, z gatunkami „formulaicznymi” (pogoda, horoskop, wyniki sportowe, komunikaty, PAP) | **Swoistość / FPR**. Wynik 0/300 daje górną granicę 95% ≈ 1% (reguła trzech: 3/n) |
| **G2** syntetyczne | AI | `gold.py synth-prompts` → ≥3 modele × 3 typy promptów (nagłówek→news, przeróbka, SEO) → `ingest-synth` | ≥300 (≥100 na model) | **Czułość**, w podziale na model i wariant |
| **G3** udokumentowane | AI | artykuły 2026 ze śladem chatbota / deklaracją AI, **zweryfikowane ręcznie** | ile znajdziecie (może być <30) | Czułość na tekstach „z natury” |
| **G4** miękkie | — | adnotacja stylu (`annotated_soft`) | 100–200 | **Tylko analiza błędów**, nie liczymy z tego czułości |

**Podział dev/test:** po *grupach* (domena dla G1, tekst-źródło dla G2), deterministycznie przez hash — ten sam tekst-źródło nie trafi do obu zbiorów. **Próg wybieracie na dev, metryki raportujecie na test**, a test odsłaniacie raz, po zamrożeniu potoku.

**Dlaczego nie trenować własnego klasyfikatora:**
1. Wyuczylibyście separację *epoki* (2020 vs 2026: tematy, formatowanie, CMS), nie AI.
2. Pozytywy syntetyczne ≠ farmy (parafrazy, post-edycja, tłumaczenia) — model nauczy się artefaktów generatorów z promptów.
3. Kurs ocenia walidację instrumentu i wniosek, nie F1.
4. Gotowe narzędzie z polskim istnieje; Wasza wartość to walidacja i pomiar.
Jeśli mimo to chcecie model pomocniczy: tylko cechy z `features.py`, trening wyłącznie na dev, walidacja krzyżowa po domenach, raport jako uzupełnienie.

**Testy odporności instrumentu** (opcjonalne, wysoka wartość dla red teamingu): (a) teksty G2 po parafrazie/„humanizerze”, (b) przycięte do 150 słów, (c) człowiek → tłumaczenie maszynowe z angielskiego (farmy tłumaczą!), (d) tekst ludzki zredagowany przez LLM (AI-assisted).

**Adnotacja ręczna** (G3/G4): `gold.py sample` tworzy próbkę (równo po warstwach, max 2 art./domenę, opcjonalnie nadpróbkowana wokół progu detektora); dwóch oceniających, ≥30% wspólnych → kappa; reguły w `CODEBOOK.md`: **bez twardego dowodu nie wpisujemy „AI”**.

---

## 8. Walidacja i korekta (jak to działa w kodzie)

- `validate.py`: wybór progu na dev (FPR ≤ `--fpr-target`), metryki na test z Wilsonem **i** bootstrapem po grupach (artykuły z jednej domeny nie są niezależne), rozbicia (model, wariant, długość tekstu), listy FP/FN do ręcznej analizy błędów, `validation_boot.npz`.
- `estimate.py`: dla każdej domeny `p_obs` → `p_corr = (p_obs + swoistość − 1) / (czułość + swoistość − 1)`. W każdym z B powtórzeń losujemy parę (czułość, swoistość) z bootstrapu walidacji i artykuły w domenie → rozkład `p_corr`. Z niego: prawdopodobieństwo „masowo AI” per domena, przedziały dla liczby domen per warstwa, klasy tak/niepewne/nie.
- **Reguła stopu:** jeśli czułość+swoistość−1 < 0,2, detektor jest praktycznie nieodróżnialny od losowego na Waszych danych → `estimate.py` przerywa, a Wy raportujecie to jako wynik.
- **Założenie, które musicie nazwać w raporcie:** czułość i swoistość z gold przenoszą się na domeny docelowe (to nieprawda dla np. nowych modeli, tekstów po edycji, innych gatunków). Dlatego raportujemy **obie liczby: naiwną i skorygowaną** i traktujemy przedział jako optymistyczny.

---

## 9. Analiza i odporność — lista do wykonania

Jedno polecenie na wariant (`--tag`), porównujecie `stratum_summary_<tag>.csv`:

| Wariant | Jak |
|---|---|
| Próg domeny τ | `--taus 0.2,0.3,0.5,0.8` (jest w jednym przebiegu) |
| Próg detektora | `validate.py --fixed-threshold 0.3 / 0.5 / 0.8`, potem `estimate.py --tag t03` |
| Miara AI | `--score-col ai_any` vs `fraction_ai` |
| Minimalna liczba artykułów | `estimate.py --min-articles 5/10/20` |
| Bez przedruków | wykluczcie artykuły z `near_dup_cross_domain` lub `src_marker_count>0` |
| Daty | `collect --accept-undated` vs domyślnie |
| Długość tekstu | `collect --min-words 300` |
| Poddomeny | portal jako jedna / wiele jednostek |
| Per model z G2 | czułość podzielona; „najgorszy przypadek” czułości |
| Okno czasowe | miesiące osobno (jeśli rozszerzycie okno) |

**Korelacja ≠ przyczynowość:** warstwa (S1–S3) nie „powoduje” udziału AI — to opis; nie wyciągajcie wniosków o intencjach wydawców ani o szkodliwości z samego udziału AI. `convergent_<tag>.csv` pokazuje, czy udział AI koreluje z niezależnymi cechami (rho Spearmana na poziomie domen).

**Pre-rejestracja (tanio, mocno):** przed odsłonięciem wyników docelowych zacommitujcie plik `docs/PLAN_ANALIZY.md` z: τ główne, regułą progu detektora, `min-articles`, listą wariantów odporności i tym, co uznacie za wynik negatywny. Tag git `plan-v1`.

---

## 10. Zagrożenia dla trafności

| Zagrożenie | Skutek | Łagodzenie |
|---|---|---|
| Pokrycie Common Crawl (paywalle, JS, robots.txt, losowość crawla) | Obciążenie próby; mało artykułów z małych serwisów | Raport `collect_summary` (kandydaci, odrzucenia) per domena; domeny z <10 artykułami raportowane osobno |
| Losowanie *stron indeksu* = przedziały alfabetyczne URL | Dla ogromnych portali próba z wąskiego wycinka | `--n-pages` ↑; dla S1 rozważyć losowanie po poddomenach/sekcjach; opisać |
| Brak daty / zła data | Stare treści w oknie lub brak farm bez dat | `pub_date_source`, `no_date` per domena, analiza z `--accept-undated` |
| Detektor myli się na polskim, tłumaczeniach, szablonowych gatunkach, przedrukach | Fałszywa „masowość” | G1 z gatunkami formulaicznymi, FPR per gatunek, analiza FP, wariant bez przedruków |
| Czułość z syntetyków zawyżona (łatwiejsze niż farmy) | Niedoszacowanie udziału AI | Raport czułości jako *górnego ograniczenia*; testy odporności (parafraza, tłumaczenie) |
| Dryf modeli (nowe LLM) | Czułość spada w czasie | Generatory G2 z 2026 r.; zapis daty i wersji modelu |
| AI-assisted vs AI | Granica rozmyta | Dwa warianty miary (`fraction_ai` / `ai_any`), jawna definicja |
| Ekstrapolacja z S3 | Fałszywe „ile” | Tylko „wśród zbadanych”; opis źródeł `source_note` |
| Mała liczba domen z zjawiskiem | Szerokie przedziały | Plan sformułowań z góry (sekcja 5) |
| Wielokrotne porównania (wiele τ, progów) | Fałszywie „znaczące” | Jedno wariant główny zamrożony; reszta to odporność |
| Etykietowanie domen jako „farm” | Szkoda reputacyjna | Mówimy „wykazuje cechy…”, podajemy niepewność; kodowanie nazw w publikacji (decyzja z prowadzącym) |

---

## 11. Etyka, prawo, dane

- **Źródło danych:** Common Crawl (publiczne archiwum, szanuje `robots.txt` w momencie zbierania). Nie scrapujemy serwisów na żywo bez osobnej decyzji; gdyby było trzeba — `robots.txt`, regulamin, limit zapytań, identyfikujący `User-Agent` (`AMC_UA`).
- **Prawo autorskie / TDM:** teksty służą wyłącznie do analizy (eksploracja tekstu i danych w badaniach); **nie republikujemy tekstów**. `data/raw_private/` jest w `.gitignore`; publikujemy tylko metadane i wyniki (`PRIVATE_FIELDS` w `common.py` odcina tekst, tytuł i nazwisko autora z plików publicznych). Interpretację (wyjątki dla badań) potwierdźcie z prowadzącym.
- **RODO:** nazwiska autorów to dane osobowe — w danych prywatnych tylko do deduplikacji, w publicznych wyłącznie flaga `author_present`.
- **Data statement** (obowiązek roli *Inżynier danych*): skąd dane, jak próbkowane, co odrzucone (`collect_summary`), okres, język, znane obciążenia, licencje, kto ma dostęp. Szablon w `docs/DATA_STATEMENT.md`.
- **Ujawnienie użycia AI:** kurs ocenia logi sesji agentów i sprawdza preprint Pangramem. Wpiszcie w raporcie, co i jak zrobił agent (kod, burza mózgów, redakcja) i trzymajcie logi. Każdy z Was musi umieć obronić każdą decyzję — obrony są indywidualne.

---

## 12. Mapowanie na etapy kursu i role

| Zajęcia | Etap | Co powstaje | Kto prowadzi |
|---|---|---|---|
| 1–2 (**M1**) | Karta eksploracji danych | Pytanie + hipotezy; ramy próby (`frame.py check`); pilotaż `collect` na 5–10 domenach (wydajność, odrzucenia); plan pomiaru; ograniczenia; wykonalność (liczby z sekcji 5) | Lead + Inżynier danych |
| 3 | Codebook i gold standard; walidacja instrumentu | `CODEBOOK.md`, `gold.py`, korpus `control`, `synthetic`, kappa, pierwsza `validate.py` | Inżynier pipelinu |
| 4 | Pierwszy wynik na pełnych danych | `collect` (pełne), `features`, `detect`, `estimate` → pierwsze tabele/wykresy | Inżynier analityk + wszyscy |
| 5 (**M2**) | Red teaming | Raport z metodologią i wynikami; przygotowane odpowiedzi na zarzuty (niżej) | Lead |
| 6 | Konsultacje | Poprawki, analizy odporności | wszyscy |
| 7–8 (**M3**) | Plakat, obrona | `fig_domains_*.png`, `fig_strata_*.png`, notatka dla odbiorcy spoza zespołu | Analityk + Lead |

**Spodziewane zarzuty w turnieju — przygotujcie odpowiedzi z liczbami:**
1. „Detektor nie jest wiarygodny po polsku.” → G1/G2, czułość/swoistość z CI, analiza błędów, reguła stopu.
2. „S3 nie jest losowa.” → tak, i dlatego tylko „wśród zbadanych”; źródła w `source_note`.
3. „Syntetyki to nie farmy.” → traktujemy czułość jako górne ograniczenie; testy odporności; G3.
4. „Przedruki agencyjne to fałszywe alarmy.” → flagi, wariant bez przedruków, FPR per gatunek.
5. „Okno jest krótkie / crawl niepełny.” → raport pokrycia, wrażliwość na okno.
6. „Dlaczego τ=0,5?” → zamrożone a priori, wrażliwość 0,2–0,8.
7. „Korekta Rogana–Gladena zakłada stałą czułość.” → tak; raportujemy też wynik naiwny i najgorszy przypadek.
8. „Kopiowanie tekstów i RODO.” → sekcja 11.

---

## 13. Pierwsze 10 kroków (kolejność)

1. `pip install -r requirements.txt`; `export AMC_UA="AMC-student-research (kontakt: twoj@email)"`; `bash tests/run_e2e.sh` (powinno kończyć się `E2E: OK`).
2. `python src/frame.py check` na prawdziwej liście; decyzja o poddomenach.
3. **Zapytać prowadzącego o dostęp do Pangrama / napisać do Pangram** (od tego zależy budżet).
4. Rozbudować ramę próby (sekcja 4), zapisywać `source_note`.
5. Pilotaż: `python src/collect.py --only pap.pl --n 10 --max-fetch 100` → obejrzeć odrzucenia i daty. Dopiero potem pełny przebieg.
6. `collect --corpus control …` (2019–2021, `--max-crawls 4`).
7. `features.py`, `gold.py synth-prompts`, wygenerowanie tekstów, `ingest-synth`, `gold.py sample` (adnotacja), `assemble`.
8. `detect.py --dry-run` → budżet → `detect.py` na control+synthetic → `validate.py`. **Bramka:** czy instrument przechodzi walidację?
9. Zamrozić `PLAN_ANALIZY.md` (tag `plan-v1`); `detect.py` na target; `estimate.py`.
10. Audyt ręczny domen „tak/niepewne” (`frame.py audit`), analizy odporności, raport.

---

### Źródła użyte do przygotowania planu

- Pangram — obsługiwane języki (polski na liście 24): <https://www.pangram.com/knowledge-hub/what-languages-does-pangram-work-on>
- Pangram — API, SDK i rozliczenia: <https://www.pangram.com/llms.txt>, <https://pangram.readthedocs.io/en/stable/tutorial.html>, <https://www.pangram.com/blog/v3-api-migration-guide>
- NewsGuard — AI Tracking Center (16 języków, bez polskiego; cztery kryteria „AI Content Farm”): <https://www.newsguardtech.com/special-reports/ai-tracking-center/>
- Wymagania kursu: `AMC_1.pdf` (zasady, harmonogram, kryteria oceny).

*Ceny i funkcje Pangrama pochodzą ze stron dostawcy w dniu przygotowania planu — zweryfikujcie je przed budżetowaniem.*
