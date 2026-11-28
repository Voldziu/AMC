# Recenzja preprintu „Ile polskich serwisów newsowych publikuje masowo teksty generowane przez AI?”

*Przedmiot:* `docs/paper/overleaf/preprint.tex` (+ `tabela_serwisow.tex`, `figures/fig01–fig09`), stan z commita `b297877`.
*Data:* 2026-11-21.
*Tryb:* pięciu niezależnych recenzentów (metodologia, statystyka, spójność, grafika, język) i adwersaryjny weryfikator dla każdej osi. Weryfikatorzy przeliczali liczby na danych w repo i odtworzyli pipeline w scratchpadzie (seed 42). Repozytorium nie było modyfikowane.
*Bilans:* 67 zarzutów, 0 obalonych, 26 skorygowanych co do treści lub wagi, 18 dodatkowych przeoczeń wskazanych przez weryfikatorów.

---

## 0. Werdykt w skrócie

**Projekt badania jest dobry, a liczby się odtwarzają.** Recenzent statystyczny odtworzył od zera kluczowe wyniki: zmianynaziemi.pl π_min 34,5 [29,8; 39,3], goniec.pl π_gold 50,1 [31,4; 77,0], wynik zbiorczy 4,0% [2,4; 6,1] i 18,1% [9,7; 32,2], δ = 2,9 pp oraz TPR 26% [18,4; 35,4]. Zgadzają się też sumy we wszystkich tabelach. Porównanie każdego serwisu z nim samym, placebo, reguła ustalona przed obejrzeniem wyników i siatka wariantów to staranność rzadka w preprintach.

**Interpretacja wyprzedza jednak dane w trzech miejscach, które zmieniają wnioski:**

1. **Trzy z pięciu serwisów „masowych” mają konkretne, sprawdzalne wyjaśnienie alternatywne, którego praca nie sprawdziła.**
   - **zmianynaziemi.pl:** skok w 2024 r. pokrywa się ze zmianą szablonu. Tekst zaczyna się od `Image |` w 121 ze 125 tekstów z 2024 r. i w 0 tekstach wcześniej, a oznaczonych jest 78,5% tekstów z prefiksem i 0 z 4 bez niego. Ten sam serwis ma jednak bardzo mocny sygnał przy wysokim progu: wynik > 0,8 ma 47 ze 125 tekstów, a w latach 2020–2022 tylko 4 z 20 814 w całej próbie. Najmocniejszy wynik da się więc prawdopodobnie *wzmocnić*, ale trzeba przeliczyć Pangrama po usunięciu prefiksu.
   - **nczas.com:** wszystkie 21 oznaczonych tekstów z 2024 r. to treści SEO i sponsorowane („kalkulator akcyzy”, „darmowy VPN”, „pralka AbsoluteCare”…), n = 41. Mierzymy tu dział partnerski, nie redakcję.
   - **pap.pl:** przed 2022 r. i po nim badane są inne subdomeny (kurier/fakehunter wobec scienceinpoland/zdrowie, TV = 0,92), a `www.pap.pl` nie ma w próbie wcale. Poziom bazowy b jest więc nieporównywalny.
2. **Instrument mierzy coś innego, niż deklaruje definicja.** EditLens to model *stopnia edycji AI*, a l. 48 twierdzi, że teksty tylko poprawione są poza jego zasięgiem. Tego nie sprawdzono, choć `rewrite.py` ma gotowy tryb `light`.
3. **Wynik zbiorczy „4–18%” nie ma spójnej interpretacji.** π_gold maleje monotonicznie z progiem (21,5 → 11,3%), czyli model G2 nie przechodzi testu niezmienniczości. Zakres miesza dwa szacunki punktowe. Wynik zależy też od celowo dobranej próby: bez pięciu serwisów masowych wynosi 2,5/11,3%, dla samego S1 1,8/8,1%, a l. 56 obiecuje wyniki osobno dla warstw, których nigdzie nie ma.

**Statystyka jest poprawna w mechanice, ale opis niepewności jest mylący.** δ przy FPR 5% to czysty szum dwumianowy (φ = 1,02), a nie „margines dryfu”, i w regule masowości nigdy nie jest wiążący. Przy FPR 10% i 20%, użytych jako argument stabilności, dane mają nadmierną dyspersję (φ = 1,42 i 2,62), więc te warianty są antykonserwatywne. Klasyfikacja globalna.info zależy od ziarna Monte Carlo: w 84,5% ziaren serwis przechodzi do grupy „prawdopodobnie”, więc w analizie głównej masowych może być 6, a nie 5.

**Rysunki trzeba zrobić od nowa, a najpierw napisać kod, który je generuje.** W repo nie ma kodu tworzącego `fig01–fig09` (zero `savefig`, notebook rysuje inne wersje). Wszystkie rysunki to rastry PNG z bezszeryfowym fontem na złamanym białym tle, a w druku mają 4,7–7 pt. Rys. 7 łączy linią lata bez danych, a rys. 6 pokazuje obcięte 100% jak zwykłą wartość.

**Rekomendacja:** *major revision*. Żaden zarzut nie podważa samej metody, ale przed publikacją trzeba poprawić dwie rzeczy: listę serwisów „masowych” i jej sformułowania (punkty 1–3) oraz rysunki.

---

## 1. Lista priorytetów (co poprawić, w jakiej kolejności)

Identyfikatory odsyłają do szczegółów w sekcjach A–E. Zarzuty zgłoszone niezależnie przez kilku recenzentów są zgrupowane.

### P1 – Muszą być poprawione przed publikacją (zmieniają wnioski)

| # | Problem | ID | Nakład |
|---|---|---|---|
| 1 | **zmianynaziemi.pl:** usunąć prefiks `Image \|`, przeliczyć Pangrama (125 tekstów) i dodać analizę wysokiej pewności (próg 0,8, empiryczny FPR ≈ 0,02%) dla zmianynaziemi.pl i neon24.pl | M2, przeoczenie A | GPU, ok. 1 h |
| 2 | **Ręczna ślepa ocena** po ok. 30 oznaczonych i 30 nieoznaczonych tekstów po 2022 r. dla 5 serwisów masowych i neon24.pl, oznaczenie treści sponsorowanych; nczas.com przekwalifikować | M6 | kilka godzin pracy ludzi |
| 3 | **Diagnostyka składu sekcji i subdomen** (TV host/ścieżka przed i po) dla wszystkich serwisów; pap.pl wyłączyć lub stratyfikować; zmianynaziemi.pl i nczas.com mają TV = 0, co warto napisać | M1 | ~1 h kodu |
| 4 | **Konstrukt:** uruchomić G2 w trybie `light` i podać TPR na lekkiej korekcie; zależnie od wyniku zmienić definicję na „generowane lub istotnie redagowane” | M3 | API, ~1 h |
| 5 | **Sformułowania pewności:** „co najmniej 29,8% tekstów *musi* pochodzić z AI”, „niezależnie od założeń o czułości” → granica warunkowa względem stacjonarności b i niezależności artykułów (l. 36, 256, 403) | M2, W7, przeoczenie B | tekst |
| 6 | **Wynik zbiorczy:** podać osobno dla S1/S2/S3 (obiecane w l. 56) i bez serwisów masowych; „4–18%” zastąpić dolną granicą warunkową i jawnym „górnej granicy nie identyfikujemy”; zależność π_gold od progu opisać jako niezaliczony test specyfikacji | M4, STAT-3, STAT-4 | ~1 h |
| 7 | **Monte Carlo:** N_BOOT ≥ 100 000, osobne ziarno dla serwisu, wszystkie tabele z jednego przebiegu, rozstrzygnąć globalna.info (5 czy 6 masowych) | STAT-2, C4, W9 | <1 h |
| 8 | **δ i dyspersja:** przestać nazywać δ „marginesem dryfu”, wbudować φ̂ z placebo w losowania dla FPR 10/20%, usunąć fałszywe zdanie z l. 360; dla każdego serwisu masowego podać „dryf krytyczny” | STAT-1, STAT-5 | ~2 h |

### P2 – Recenzent zażąda (wiarygodność i odbiór)

| # | Problem | ID |
|---|---|---|
| 9 | „Niezależne potwierdzenie” przez Bielika → „zgodność”; dodać tabelę krzyżową oznaczeń (elblag.net: wspólne 4 z 39, goniec.pl: 3) i usunąć „częściowe potwierdzenie” elblag.net | M5 |
| 10 | neon24.pl: „dolna granica ~38%” to szacunek punktowy; przy dolnym końcu r wychodzi ok. 30% | C2, STAT-7, W6 |
| 11 | Teza „żaden serwis S1 nie jest masowy”: w wariantach masowe są cztery serwisy S1 (o2, interia, money, dziennik), a tekst zastrzega tylko o2.pl (l. 262 vs 308, 336) | C1, przeoczenia C |
| 12 | Zdanie o „spadku π_gold przy niskim FPR” odwraca kierunek z tab. FPR (l. 310) | C3, W5 |
| 13 | Sekcja „Prace pokrewne”: Adjusted Classify-and-Count / kwantyfikacja (Forman; González i in. 2017), Liang i in. 2024 (ICML, *Monitoring AI-Modified Content at Scale*), Hanley i Durumeric 2024 (ICWSM, *Machine-Made Media*), DetectGPT, przedziały Wilsona i Jeffreysa | W1, M11 |
| 14 | Oświadczenia: URL repo i commit, dostępność danych, licencja EditLens (CC BY-NC-SA 4.0 + Llama 3.2), nota etyczna przy imiennym wskazywaniu serwisów (zwłaszcza PAP) | W3, W4 |
| 15 | Odwołania do nieistniejących plików: `figures/fig01b_coverage_heatmap`, `figures/fig02b_roc`, `docs/preprint/tables/domains.csv` | C5, W4, M12 |
| 16 | Opis warstw: S3 to w danych warstwa rezydualna „poza Tranco” (np. echodnia.eu), a nie wyłącznie serwisy „podejrzane” | M9, C10 |
| 17 | Estymand „udział 2023–2025” zależy od dostępności lat w crawlu (zmianynaziemi.pl i nczas.com nie mają 2025 r.); podawać π_min per rok jako główną liczbę | M7, STAT-8 |
| 18 | Winner's curse: szacunki punktowe 5 serwisów wybranych z 37 są przeszacowane; wspomnieć lub skorygować | przeoczenie B |

### P3 – Rysunki (osobny blok pracy, patrz sekcja D)

Najpierw **G2**: jeden skrypt `src/paper_figures.py` (albo sekcja notebooka) ze wspólnym stylem, który zapisuje wektorowe PDF do `docs/paper/overleaf/figures/`. Potem poprawki per rysunek. Za *major* uznano: G1 (raster, font, tło, rozmiar), F6 (forest plot: obcięte 100%, jedna oś dla π_min i π_gold), F7 (interpolacja przez lata bez danych), F9 (4,7 pt). Rys. 1 i 2 dublują tabele 1 i 3. Proponujemy rys. 1 usunąć, a rys. 2 zastąpić krzywymi ROC z `fig02b`. Wspólny blok `rcParams` jest w G5.

### P4 – Redakcja i drobiazgi

Myślniki zakresów (`2020-2025` → `2020--2025`), definicje skrótów przed pierwszym użyciem (FPR, TPR, AUC, pp, CI), składnia l. 337 i 403, „w wnioskach” → „we wnioskach”, bibliografia ręczna → BibTeX, overfull boxes (l. 403–404: 28 pt; l. 438–439: 110 pt; tab. 7 i 11), wyrównanie liczb w tabelach (`siunitx`), aneks: „100,0 [100,0; 100,0]” dla zmianynaziemi.pl zastąpić „>100 (obcięte)”. Szczegóły: W8–W16, T1, C6–C13.

---

## 2. Odpowiedź na pytanie „czy to ma sens naukowo i statystycznie?”

- **Tak, co do architektury.** Estymacja nadwyżki na poziomie serwisu z poziomem bazowym serwisu, Rogan-Gladen (= Adjusted Classify-and-Count) oraz para π_min/π_gold jako ograniczenie z dwóch stron to rozsądny i uczciwy projekt dla problemu bez etykiet. Losowanie Beta-Jeffreys jest poprawne, a symulacja pokrycia potwierdza nominalne 95% dla dolnej granicy przy niezależnych artykułach.
- **Najsłabszym ogniwem jest założenie identyfikujące (stacjonarność b), a nie statystyka.** Placebo testuje wyłącznie lata 2020–2022 i nie wykryje zmiany składu crawla po 2022 r. Dane pozwalają ją jednak zmierzyć (TV subdomen, prefiksy szablonów, markery treści sponsorowanych) i dla 3 z 5 serwisów masowych ta zmiana jest faktycznie widoczna. To główny merytoryczny dług pracy.
- **H2 jest prawie spełniona z konstrukcji:** S3 dobrano jako podejrzane, a wystarczy jeden serwis. Warto to przyznać albo przeformułować H2 na liczbę lub odsetek serwisów, z korektą na wielokrotne porównania (STAT-6, M10).
- **Wniosek metodologiczny o wyborze detektora (Śmigiel vs gold) jest mocny i wart wyeksponowania jako osobny wkład.** Zastrzeżenie: ślepotę wykazano dla Bielika 1,5B, a pomiar robiono na 4,5B (M5, F9).

---

## 3. Szczegóły według osi

Każdy zarzut ma wagę po weryfikacji (w nawiasie waga pierwotna, jeśli się zmieniła), werdykt weryfikatora, lokalizację, dowód i proponowaną poprawkę. Weryfikator nie obalił żadnego zarzutu. Treść „skorygowana” ma pierwszeństwo przed pierwotną.

## A. Metodologia i trafność naukowa

**Ocena ogólna.** Projekt badania jest przemyślany. Porównanie każdego serwisu z nim samym, kontrola placebo, reguła klasyfikacji ustalona z góry, symulacja pokrycia i rozbudowana siatka wariantów to mocne strony. Główne twierdzenia są jednak sformułowane mocniej, niż pozwalają dane. Założenie identyfikujące (b się nie zmienia) da się w danych sprawdzić i dla części serwisów wyraźnie nie zachodzi. W pap.pl przed 2022 r. i po nim badane są zupełnie inne subdomeny (TV = 0,92). Teksty oznaczone w nczas.com w 2024 r. to sponsorowane artykuły SEO, a w zmianynaziemi.pl skok zbiega się ze zmianą szablonu (prefiks „Image” w 97% tekstów z 2024 r., w 0% wcześniej). π_gold nie jest stały względem progu, choć model tego wymaga, więc zakres „4–18%” w abstrakcie nie ma spójnej interpretacji. Najlepszą dostępną dolną granicą jest π_min przy FPR 20% (8,2%). „Niezależne potwierdzenie” przez Bielika rozumuje asymetrycznie: zgodność traktuje jako dowód, a brak zgodności tłumaczy ślepotą detektora. Dla elblag.net Pangram i Binoculars oznaczają w dużej mierze różne teksty (wspólne są tylko 4 z 39). Brakuje ręcznej weryfikacji oznaczonych tekstów, przeglądu literatury i diagnostyki składu sekcji. Wszystko to da się naprawić bez nowych pomiarów detektorem, a analiza wysokiej pewności (wynik > 0,8 ma tylko 4 z 20 814 tekstów sprzed 2023 r.) może znacząco wzmocnić najmocniejszy wynik (zmianynaziemi.pl).

**Mocne strony:**
- Porównanie każdego serwisu z nim samym (poziom bazowy b liczony osobno dla serwisu) i wynik zbiorczy z poprawką na skład poprawnie chronią przed zmianą składu serwisów w crawlu (preprint.tex:81).
- Zbiór gold ze sparowanymi tekstami G1/G2 (ten sam temat i podobna długość) to dobry pomysł walidacyjny. Pokazanie, że Śmigiel i gold prowadzą do różnych wyborów detektora, jest wartościowym wnioskiem metodologicznym (preprint.tex:114, 399).
- Placebo na latach 2020–2022, symulacja pokrycia przy zależnych artykułach (tab. pokrycie_sym) i siatka wariantów (FPR, długość, definicja, δ) to rzadko spotykana w preprintach staranność. Do tego otwarcie przyznajecie, że pap.pl, elblag.net i nczas.com są kruche.
- Daty publikacji są w praktyce poprawne. W 5025 tekstach z datą w URL (np. nczas.com/2024/12/09/, goniec.pl ...-091225) rok z trafilatury różni się od roku z URL tylko w 2 przypadkach (0,04%). To można dopisać do pracy jako walidację.
- Pipeline da się odtworzyć: `python -m news_detector.pipeline` z data/clean daje dokładnie 35 628 artykułów po deduplikacji, zgodnie z tab. 1. Losowanie z indeksu CC jest losowe (md5(url||seed)), a nie alfabetyczne.

### [M1] Założenie stacjonarności b nie zachodzi wprost dla pap.pl (zmiana subdomen) i brakuje diagnostyki składu sekcji

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:166, 197, 260, 266, 409; src/news_detector/fetch/cc_index.py (QUERY: ends_with(url_host_name, '.'||domain))`

**Problem.** Estymator zakłada, że bez AI odsetek oznaczonych by się nie zmienił. Placebo sprawdza tylko dryf wewnątrz lat 2020–2022, więc nie wykryje zmiany, którą crawl wprowadza po 2022 r. Pobieranie obejmuje wszystkie subdomeny (zapytanie dopasowuje '.domain'), a skład subdomen i sekcji w crawlu mocno zmienia się z roku na rok. Praca pisze o tym tylko jako o ograniczeniu teoretycznym (pkt 3) i nigdzie tego nie mierzy, choć dane pozwalają to zrobić.

**Dowód.** Mój rozkład URL-i według hosta. pap.pl przed 2023: fakehunter (49), kurier.pap.pl (33), zdrowie (1). Po 2022: scienceinpoland.pap.pl (222), zdrowie.pap.pl (89), kurier (0). Odległość TV między rozkładami hostów wynosi 0,92, a www.pap.pl nie występuje w ogóle. Oznaczone teksty pap.pl z 2024 r. to m.in. wywiad PAP z prof. Nowakowskim o HPV (wynik 0,59). Podobnie duże przesunięcia mają lelum.pl (TV 0,87), naszemiasto.pl (0,61), interia.pl (0,44) i tvmalbork.pl (0,28), czyli właśnie serwisy, które w analizach odporności wchodzą do grup „masowych” albo z nich wypadają. W elblag.net teksty oznaczone w 2024 r. skupiają się w biznes/dom/kobieta.elblag.net (55–67% oznaczonych), a w 2022 r. serwis ma tylko 42 teksty.

**Poprawka.** Dodać do metody diagnostykę składu: dla każdego serwisu odległość TV rozkładu host/pierwszy segment ścieżki przed i po 2022 r. Dla serwisów z TV > np. 0,3 liczyć b w sekcjach (stratyfikacja post-hoc albo reważenie b do składu sekcji po 2022 r.) albo wyłączyć je z reguły. pap.pl przenieść z „kandydatów” do „wyniku niewiarygodnego z powodu zmiany składu” i wprost napisać, że „pap.pl” w próbie to subserwisy Science in Poland i Zdrowie, a nie serwis agencyjny. W ograniczeniu nr 3 podać zmierzone TV zamiast ogólnego „inne działy w crawlu”.

> **Weryfikator:** Sprawdziłem zapytanie w cc_index.py:49. Zawiera `ends_with(p.url_host_name, '.' || w.domain)`, więc subdomeny faktycznie wchodzą do próby. Policzyłem TV rozkładu hostów przed i po 2022 r. Wyniki: pap.pl 0,92, lelum.pl 0,87, naszemiasto.pl 0,61, interia.pl 0,44, tvmalbork.pl 0,28. Wszystkie zgadzają się z referentem. Dla pap.pl przed 2023 r. mam (app.)fakehunter 49, kurier 33, zdrowie 1. Po 2022 r. mam scienceinpoland 222 (13,5% oznaczonych), zdrowie 89 (21,3%), fakehunter 24, niepodlegla 4. www.pap.pl nie występuje. Dla elblag.net TV wynosi 0,32, a w 2022 r. jest 42 teksty. Szczegół o elblag.net jest jednak nieprecyzyjny. Po 2022 r. biznes ma 4/7 oznaczonych (57%), kobieta 5/9 (56%), a dom tylko 21% (6/28). Zakres „55–67%” dla biznes/dom/kobieta nie zgadza się więc z danymi, a liczności są bardzo małe. Praca wspomina o „innych działach w crawlu” tylko w ograniczeniu 3 i w l. 266, bez żadnego pomiaru, więc zarzut jest trafny. Warto dodać to, czego referent nie napisał: dla dwóch najmocniejszych serwisów, zmianynaziemi.pl i nczas.com, TV hostów wynosi 0. Ten mechanizm nie podważa więc głównego wyniku, tylko kandydatów (pap.pl, elblag.net) i serwisy na granicach grup.
>
> **Wersja skorygowana:** Jak u referenta, z poprawką dla elblag.net. Po 2022 r. oznaczone teksty mają wysoki odsetek w biznes.elblag.net (4/7) i kobieta.elblag.net (5/9), ale dom.elblag.net ma tylko 21% (6/28). Liczności są za małe na wniosek o „skupieniu”. TV hostów elblag.net wynosi 0,32. Należy też dopisać, że zmianynaziemi.pl i nczas.com mają TV = 0, więc problem składu dotyczy kandydatów i serwisów granicznych, a nie głównego wyniku.

### [M2] „Co najmniej 29,8% tekstów musi pochodzić z AI” to sformułowanie zbyt mocne; skok w zmianynaziemi.pl zbiega się ze zmianą szablonu

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:36, 256, 403`

**Problem.** Abstrakt i dyskusja przedstawiają 29,8% jako dolną granicę „niezależnie od założeń o czułości”. Ta granica zależy jednak od (a) stacjonarności b, (b) niezależności artykułów (przy zgrupowaniu pokrycie spada do 85–87%, tab. pokrycie_sym, a przejście serwisu w jednym roku na inny reżim produkcji to właśnie zgrupowanie), (c) konstruktu, bo EditLens liczy też redakcję AI (M3), oraz (d) definicji estymandu. zmianynaziemi.pl nie ma danych z 2025 r., więc „udział z lat 2023–2025” to średnia ważona liczbą przechwyceń CC: 187 tekstów z 2023 r. (π_min 7%) i 125 z 2024 r. (75%). Do tego w roku skoku zmienił się szablon strony.

**Dowód.** W zmianynaziemi.pl tekst zaczyna się od 'Image |' w 0% tekstów z lat 2020–2023 i w 96,8% tekstów z 2024 r. Jest to ta sama sekcja /wiadomosc/, a mediana długości rośnie z 282 do 347 słów. Jednocześnie dane bardzo mocno wspierają ten serwis, mocniej niż sam próg 5%. Wynik > 0,8 ma tylko 4 z 20 814 tekstów z lat 2020–2022 (0,02%) i 0 z 551 tekstów zmianynaziemi sprzed 2023 r., a w 2024 r. 37,6% tekstów tego serwisu (47 ze 125). Maksimum wśród przeróbek G2 to 0,83. Trzy losowe oznaczone teksty z 2024 r. (Sora/OpenAI, Asad w Moskwie, 100 dni wojny w Gazie; wyniki 0,94–0,99) mają typową dla LLM strukturę leadu.

**Poprawka.** (1) Zamienić „musi pochodzić z AI” i „niezależnie od założeń o czułości” na „przy założeniu niezmienionego poziomu fałszywych alarmów i niezależności artykułów detektor wskazuje nadwyżkę odpowiadającą ≥29,8% tekstów”. (2) Usunąć prefiks 'Image' i przeliczyć Pangrama dla tego serwisu (to 125 tekstów), żeby wykluczyć artefakt szablonu. (3) Dodać analizę wysokiej pewności (próg 0,8, empiryczny FPR około 0,02%). Przy takim FPR π_min ≈ r jest prawie wolne od założenia o b i daje dla zmianynaziemi.pl (2024) oraz neon24.pl (28,5% w 2023 r.) dowód znacznie odporniejszy niż próg 5%. (4) Podawać π_min per rok (tab. rok) jako główną liczbę dla serwisów z niepełnym pokryciem lat.

> **Weryfikator:** Cytaty są w tekście: l. 256 „co najmniej 29,8% tekstów musi pochodzić z AI” i l. 403 „niezależnie od założeń o czułości”. Sformułowanie jest zbyt mocne. Sama praca w l. 162 warunkuje π_min („o ile poziom bazowy się nie zmienił”), a w ograniczeniu 4 pisze o „korelacji, nie przyczynowości”. Wyliczenia referenta potwierdziłem. Prefiks 'Image' ma 0% tekstów w latach 2020–2023 i 96,8% (121/125) w 2024 r. Wśród tekstów z prefiksem oznaczonych jest 78,5%, wśród 4 bez prefiksu 0/4. Wynik >0,8 mają 4 z 20 811 tekstów z lat 2020–2022, a w zmianynaziemi.pl w 2024 r. 47 tekstów. Maksimum G2 wynosi 0,827. Argument o długości jest jednak chybiony. Mediana długości wzrosła już w 2023 r. (351 słów, a w 2024 r. 347), kiedy odsetek oznaczonych wynosił tylko 9,6%. Wzrost długości nie zbiega się więc ze skokiem i go nie tłumaczy. Pozostaje zbieżność zmiany szablonu (crawl CC-MAIN-2025-05) ze skokiem. Pojedynczy token 'Image' raczej nie podnosi wyniku z około 0,3 do 0,9, ale trzeba to sprawdzić, bo przeliczenie 125 tekstów jest tanie. Poprawki proponowane przez referenta są sensowne. Ważność major jest uzasadniona, bo chodzi o sformułowanie w abstrakcie i dyskusji.
>
> **Wersja skorygowana:** Jak u referenta, ale bez argumentu o długości. Mediana długości wzrosła już w 2023 r. (351 słów), rok przed skokiem, więc długość nie jest wyjaśnieniem. Zbieżna ze skokiem jest tylko zmiana szablonu: prefiks 'Image' ma 121/125 tekstów z 2024 r. (78,5% z nich jest oznaczonych), a 0 tekstów wcześniej. Poprawki: (1) osłabić sformułowania w l. 36, 256 i 403, (2) przeliczyć wynik po usunięciu prefiksu, (3) dodać analizę przy wysokim progu (>0,8: 4/20 811 tekstów sprzed 2023 r. wobec 47/125 w zmianynaziemi.pl w 2024 r.).

### [M3] EditLens wykrywa redakcję AI, a praca deklaruje, że teksty tylko poprawione są poza zasięgiem instrumentu

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:48, 108, 110, 162`

**Problem.** Definicja (l. 48) liczy tylko teksty „w całości lub w przeważającej części” napisane przez model i stwierdza, że teksty poprawione przez model są poza zasięgiem instrumentu. EditLens (Thai i in. 2026) jest jednak uczony właśnie do mierzenia stopnia redakcji AI. Wynik to oczekiwana klasa na 4-stopniowej skali edycji (komórka 1 notebooka main-results). Próg 0,47 odpowiada w przybliżeniu klasie „umiarkowanie redagowany przez AI”. Nadwyżka może więc zawierać teksty ludzkie wygładzone przez LLM, a wtedy π przeszacowuje udział tekstów wygenerowanych w rozumieniu definicji. Sam G2 jest częściowo ludzki, bo polecenie każe zostawić cytaty bez zmian, więc TPR=26% to czułość na mocno zredagowane teksty ludzkie, a nie na tekst wygenerowany.

**Dowód.** src/news_detector/gold/rewrite.py: USER_PROMPTS['strong'] zawiera „cytaty wypowiedzi osób zostaw bez zmian”. W kodzie jest też tryb 'light' (korekta językowa), którego nie uruchomiono, więc twierdzenia z l. 48 nikt nie sprawdził. Mediana wyniku G2 wynosi 0,37 (maksimum 0,83). Oznaczone teksty goniec.pl, nczas.com i pap.pl po 2022 r. mają medianę 0,54–0,60, czyli tyle samo co fałszywe alarmy sprzed 2023 r. (mediana 0,54) i daleko od zmianynaziemi.pl (0,75).

**Poprawka.** Uruchomić tryb 'light' na 100 tekstach G1 i podać TPR Pangrama na lekkiej korekcie przy progu 0,472. Jeśli jest wyraźnie powyżej 5%, zmienić definicję konstruktu na „teksty wygenerowane lub istotnie zredagowane przez AI” i odpowiednio przeformułować tytuł, abstrakt i l. 48. Jeśli jest około 5%, podać tę liczbę jako dowód twierdzenia z l. 48. W obu przypadkach opisać G2 jako „przeróbki z zachowanymi cytatami” i dodać to do ograniczenia nr 1.

> **Weryfikator:** L. 48 rzeczywiście twierdzi, że „teksty tylko poprawione przez model są poza zasięgiem naszego instrumentu”. EditLens (tytuł w bibliografii: „Quantifying the Extent of AI Editing in Text”) służy do mierzenia stopnia edycji. Komórka 1 notebooka potwierdza, że wynik to oczekiwana klasa z rozkładu na cztery klasy (kolumna pangram_bucket w pangram.csv). rewrite.py ma tryb 'light' („Zachowaj wszystkie fakty, nazwiska, liczby i cytaty”). Uruchomiono tylko tryb 'strong' (DEFAULT_MODE='strong'), a ten zostawia cytaty bez zmian. Twierdzenie z l. 48 nie ma więc żadnego testu. Mediana G2 wynosi 0,366, maksimum 0,827. Mediany oznaczonych tekstów po 2022 r.: goniec 0,58, nczas 0,60, pap 0,54, fałszywe alarmy sprzed 2023 r. 0,54, zmianynaziemi.pl 0,76. Wszystko zgadza się z referentem. Proponowana poprawka (uruchomić tryb 'light' na G1) jest tania i rozstrzyga sprawę.

### [M4] π_gold zależy od progu, co oznacza błędną specyfikację, więc zakres „4–18%” w abstrakcie nie ma spójnej interpretacji

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:36, 162, 228, 310, 403; tab. fpr (l. 319–322)`

**Problem.** Przy poprawnym modelu (teksty AI w serwisach mają rozkład wyniku jak G2) π_gold powinien być w przybliżeniu niezależny od progu. Tymczasem monotonicznie spada z 21,5% do 11,3%, a π_min rośnie z 2,0% do 8,2%. To test specyfikacji, który model oblewa: rzeczywiste teksty z nadwyżki mają inny rozkład wyniku niż G2. Abstrakt podaje „4–18%” jak przedział od dolnej do górnej granicy, ale 18% nie jest górną granicą (sami piszecie, że π_gold przy niskim FPR jest „raczej górną granicą”, a 18% pochodzi z FPR 5%), a 4% nie jest najlepszą dostępną dolną granicą. π_min przy każdym progu jest prawomocną dolną granicą przy tym samym założeniu stacjonarności, więc najostrzejsza wynosi 8,2% [4,8; 12,2] (FPR 20%). Analogicznie interpretacja π_gold > 100% jako „teksty łatwiejsze do wykrycia” (l. 162, 256) jest tylko jednym z wyjaśnień. Równie dobrze może to oznaczać naruszenie stacjonarności b albo inną mieszaninę typów tekstów, a obcięcie do 100% ukrywa tę informację.

**Dowód.** Tab. fpr: π_min 2,0 → 4,0 → 5,6 → 8,2%; π_gold 21,5 → 18,1 → 14,3 → 11,3%. Notebook main-results, komórka 39: „Jeśli model jest poprawny, szacunek udziału AI w serwisie nie powinien zależeć od progu”. To zdanie jest w notebooku, ale nie trafiło do pracy. Przy zmianynaziemi.pl r = 36,5% > TPR = 26%, czyli dane są niezgodne z modelem G2 dla każdego π ∈ [0,1].

**Poprawka.** W abstrakcie i dyskusji podawać dolną granicę jako maksimum π_min po progach (z poprawką na wielokrotny wybór progu albo z jednym progiem wybranym z góry) i wprost napisać, że górnej granicy nie identyfikujemy. π_gold opisywać jako „szacunek warunkowy, przy założeniu tekstów typu G2”, a nie jako koniec zakresu. Dodać zdanie o teście niezmienniczości względem progu i jego wyniku. Dla π_gold > 100% raportować wartość nieobciętą (r−b)/(TPR−b) i opisać ją jako niezgodność z modelem G2, a nie dowód, że teksty pisano od zera.

> **Weryfikator:** Liczby w tab. fpr się zgadzają. Komórka 39 notebooka zawiera zdanie „szacunek udziału AI w serwisie nie powinien zależeć od progu”, a w pracy go nie ma. Dla zmianynaziemi.pl r = 36,5% > TPR = 26%, więc model G2 jest tam niewykonalny. Praca częściowo to adresuje: w l. 310 przyznaje „nie ma jednej stabilnej liczby” i wyjaśnia spadek π_gold różnicą czułości, więc zarzut nie dotyczy zupełnego przemilczenia. Słabsza jest propozycja referenta, by za dolną granicę przyjąć maksimum π_min po progach (8,2% przy FPR 20%). Przy FPR 20% margines dryfu rośnie do 9,6 pp, czyli założenie stacjonarności b jest tam najmniej wiarygodne, a wybór maksimum po progach jest wyborem post hoc. Główne jądro zarzutu jest trafne: „4–18%” nie jest przedziałem od dolnej do górnej granicy, a obcięcie π_gold do 100% ukrywa niezgodność z modelem.
>
> **Wersja skorygowana:** π_gold zależy monotonicznie od progu (21,5 → 11,3%), co jest testem specyfikacji, którego model nie przechodzi. Dla zmianynaziemi.pl r > TPR, więc model G2 jest niewykonalny. Praca to częściowo zauważa (l. 310), ale abstrakt nadal podaje „4–18%” jak przedział. Poprawka: przedstawić π_min przy z góry wybranym progu jako dolną granicę warunkową względem stacjonarności b. Wprost napisać, że górnej granicy nie identyfikujemy. Raportować nieobcięte π_gold jako diagnostykę niezgodności. Nie należy brać maksimum π_min po progach, bo przy FPR 20% dryf wynosi 9,6 pp i założenie o b jest najsłabsze.

### [M5] „Niezależne potwierdzenie” przez detektory Bielika: rozumowanie asymetryczne, a dla elblag.net detektory oznaczają różne teksty

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:114–116, 368, 397`

**Problem.** Ta sama obserwacja jest interpretowana w obie strony. Brak sygnału Bielika w goniec/pap/nczas „nie jest dowodem przeciw”, bo detektor jest ślepy, a sygnał w zmianynaziemi.pl to „niezależne potwierdzenie”. Takiej interpretacji nie da się sfalsyfikować. Ślepota jest przy tym wykazana tylko dla Bielika 1,5B przy 1024 tokenach, a w pomiarze używacie 4,5B przy 512 tokenach (l. 116, 368). Zgodność dwóch detektorów nie odróżnia AI od wspólnego czynnika zakłócającego (np. zmiany szablonu z M2, wzrostu długości), który przesuwa oba wyniki. Korelacja rang 0,02–0,08 w całej próbie oznacza, że detektory mierzą coś innego, więc zbieżność w 1 z 37 serwisów jest słabym dowodem.

**Dowód.** Moje przeliczenie (Binoculars 4,5B, próg przy FPR 5% na train+dev 2020–22). zmianynaziemi.pl po 2022: Binoculars oznacza 53 teksty, z czego 37 (70%) oznacza też Pangram. Korelacja rang wewnątrz serwisu wynosi 0,44 po 2022 r. wobec 0,14 przed, czyli w tym serwisie zgodność jest realna na poziomie tekstów i to lepszy argument niż globalne 0,02–0,08. elblag.net: Binoculars oznacza 39 tekstów, Pangram 28, wspólne są tylko 4. Detektory widzą więc nadwyżkę w różnych tekstach, a „częściowe potwierdzenie” (l. 397) opiera się na zbieżności liczb, nie tekstów. nczas.com: 30 oznaczeń Binoculars, 5 wspólnych.

**Poprawka.** (1) Zastąpić „niezależne potwierdzenie” określeniem „zgodność”. Dodać analizę na poziomie tekstów (tabela krzyżowa oznaczeń i korelacja rang wewnątrz serwisu przed i po 2022 r.) i wprost napisać, że wspólny czynnik niezwiązany z AI (szablon, długość) daje tę samą przewidywaną zgodność. (2) Usunąć „częściowe potwierdzenie” elblag.net albo podać, że oznaczone teksty prawie się nie pokrywają. (3) Przeliczyć Bielika 4,5B na gold (100 + 100 tekstów, 512 tokenów). Bez tego nie twierdzić, że 4,5B jest „ślepy”. (4) Wprost przyznać asymetrię interpretacji w l. 397.

> **Weryfikator:** Asymetria w l. 397 jest w tekście dosłownie: „niezależnym potwierdzeniem” obok „nie jest to dowód przeciw”. L. 116 przyznaje, że ślepoty 4,5B nie sprawdzono bezpośrednio. Gold liczono przy 1024 tokenach dla Pangrama, a Bielika 4,5B przy 512 tokenach (meta.json). Przeliczyłem to sam (próg przy 5. percentylu Binoculars na latach 2020–2022). zmianynaziemi.pl po 2022 r.: Binoculars 53, Pangram 113, wspólne 37. Korelacja rang wewnątrz serwisu 0,44 po 2022 r. i 0,14 przed. To potwierdza tezę referenta. Dla innych serwisów referent zamienił liczby. W elblag.net Binoculars oznacza 28 tekstów, a Pangram 39 (nie odwrotnie), wspólne są 4. W nczas.com Binoculars oznacza 26, Pangram 30, wspólne 5. W goniec.pl wspólne są tylko 3 teksty (Binoculars 28, Pangram 94). Wniosek, że w elblag.net detektory wskazują różne teksty, pozostaje prawdziwy. Globalna korelacja rang wynosi 0,024, zgodnie z pracą.
>
> **Wersja skorygowana:** Jak u referenta, z poprawionymi liczbami. elblag.net: Binoculars 28 oznaczeń, Pangram 39, wspólne 4. nczas.com: Binoculars 26, Pangram 30, wspólne 5. goniec.pl: wspólne tylko 3 przy 28 i 94 oznaczeniach. zmianynaziemi.pl: 37 z 53 oznaczeń Binoculars to także oznaczenia Pangrama, korelacja rang wewnątrz serwisu 0,44 po 2022 r. wobec 0,14 przed.

### [M6] Brak ręcznej weryfikacji oznaczonych tekstów, choć szybki przegląd zmienia interpretację nczas.com i pap.pl

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:110, 260, 266, 410`

**Problem.** Praca dwukrotnie przyznaje, że bez ręcznego przejrzenia nie odróżni skoku od zmiany szablonu albo działu, a mimo to podaje te serwisy jako „masowe”. Przegląd kilkudziesięciu tekstów kosztuje godziny. W G1 sami odrzuciliście artykuły sponsorowane i reklamy jako nienadające się na teksty ludzkie, a w serwisach po 2022 r. nikt nie sprawdził, czy nadwyżki nie tworzą właśnie takie teksty.

**Dowód.** Losowe oznaczone teksty nczas.com z 2024 r. to sponsorowane artykuły SEO: „kalkulator akcyzy za samochód”, „darmowy VPN do ochrony sieci Wi-Fi”, „rozwój sklepów online na Mazowszu” (wyniki 0,53–0,57). Mediana długości w 2024 r. to 530 słów wobec około 300 wcześniej, a tekstów jest tylko 41. Nadwyżka może więc być AI w treściach partnerów, a nie w redakcji, i jest skorelowana z długością (stąd wypadnięcie po poprawce na długość). pap.pl: oznaczone teksty to materiały Science in Poland i wywiad z ekspertem (M1). goniec.pl 2025: teksty o strukturze SEO z śródtytułami („Wypadki z udziałem dzieci nie są rzadkością”), wyniki 0,50–0,56, czyli tuż przy progu.

**Poprawka.** Dla każdego z 5 serwisów „masowych” i neon24.pl wylosować np. 30 oznaczonych i 30 nieoznaczonych tekstów po 2022 r. (oraz 30 sprzed 2023 r.) i dać je do ślepej oceny dwóm osobom (AI/ludzki/niepewne, sponsorowany/redakcyjny, zgodność kappa). Raportować to jako walidację zewnętrzną. Oddzielnie oznaczyć treści sponsorowane (markery URL/HTML, np. „partner”, „materiał sponsorowany”) i powtórzyć analizę bez nich.

> **Weryfikator:** Przejrzałem wszystkie 21 oznaczonych tekstów nczas.com z 2024 r. To niemal wyłącznie treści SEO lub sponsorowane: „kalkulator akcyzy za samochód”, „darmowy VPN”, „zmywarki Electrolux z funkcją QuickSelect”, „pralka AbsoluteCare”, „usługi wtryskowe – dlaczego warto”, „jaki domofon wybrać”. Mediana długości wynosi 530 słów w 2024 r. wobec 290–318 wcześniej, a liczba tekstów 41. Praca w l. 266 i 410 przyznaje, że nikt nie przejrzał tekstów ręcznie. Wynik dla nczas.com mierzy więc najpewniej sekcję partnerską, a nie redakcję. Dla rozstrzygnięcia „masowo” to istotne, bo sponsorowane teksty AI publikowane przez serwis mogą liczyć się do definicji, ale trzeba to powiedzieć wprost. Fix jest konkretny i tani.

### [M7] Estymand „udział tekstów z lat 2023–2025” zależy od struktury przechwyceń CC i różni się między serwisami

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:48, 58, 223, 268; tab. pokrycie`

**Problem.** Jeden crawl na rok, wykonywany w styczniu–marcu następnego roku, z kwotą 200 tekstów. Próba składa się więc głównie z artykułów z listopada–grudnia, a lata wchodzą do średniej z wagą równą liczbie przechwyceń, nie liczbie publikacji. Dla serwisów bez 2025 r. (zmianynaziemi.pl, nczas.com) „2023–2025” oznacza w praktyce 2023–2024 z dowolnymi wagami. Wynik zbiorczy waży serwisy liczbą tekstów w crawlu, a nie produkcją czy ruchem.

**Dowód.** Rozkład miesięcy pub_date: listopad+grudzień to 37% tekstów w 2020 r., 54% w 2021, 52% w 2022, 53% w 2023, 47% w 2024 i 43% w 2025 r. Grudzień to 38% tekstów z 2024 r. i 35% z 2025 r. wobec 26% w 2022 r. nczas.com: 200 tekstów z 2023 r. i 41 z 2024 r., π_min z 2024 r. wynosi 49,5%, a pooled tylko 9,3%.

**Poprawka.** Zdefiniować estymand wprost jako „udział wśród artykułów przechwyconych przez CC w crawlu następującym po danym roku” i dodać wariant z równymi wagami lat (średnia π_rok po dostępnych latach). Dla serwisów bez części lat stosować regułę per rok albo tylko na wspólnych latach. Opisać sezonowość próby i zaznaczyć, że wnioski dotyczą głównie publikacji z końca roku.

> **Weryfikator:** Odsetek tekstów z listopada i grudnia: 0,38 / 0,54 / 0,52 / 0,53 / 0,47 / 0,43 w latach 2020–2025, sam grudzień 0,38 w 2024 r. i 0,35 w 2025 r. Wszystko zgadza się z referentem. nczas.com ma 200 tekstów z 2023 r. i 41 z 2024 r., a w tab. rok π_min z 2024 r. wynosi 49,5% wobec 9,3% dla lat łącznie. zmianynaziemi.pl nie ma tekstów z 2025 r. Ważność minor jest odpowiednia.

### [M9] Warstwy ramy próby opisane niezgodnie z danymi: S3 to warstwa rezydualna „poza Tranco”, a nie serwisy wybrane jako podejrzane

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:56, 83, 262, 411; data/frame/domains.csv; src/news_detector/scripts/build_csv_domains.py`

**Problem.** Praca opisuje S3 jako 14 serwisów dodanych ręcznie, „alternatywnych i konspiracyjnych”, wybranych jako podejrzane, a S1 jako 12 największych serwisów informacyjnych. W kodzie S3 to każda domena spoza tabeli Tranco (OTHER_STRATUM='S3'), więc trafiają tam też serwisy głównego nurtu. Z kolei serwisy „alternatywne” obecne w Tranco są w S2. To zmienia znaczenie tabeli grup według warstw i zdania „Żaden z największych serwisów (S1)”.

**Dowód.** domains.csv: tvp.info, oko.press i echodnia.eu (regionalny Polska Press) mają S3 bez rangi Tranco. zmianynaziemi.pl (ranga 356 224), goniec.pl (250 444) i demagog.org.pl mają S2. Z 5 serwisów „masowych” 3 są w S2, w tym zmianynaziemi.pl, który merytorycznie należałby do grupy „alternatywnej”.

**Poprawka.** Opisać warstwy zgodnie z procedurą (S1/S2 według rangi Tranco z ręcznym filtrem „czy to serwis informacyjny”, S3 = spoza Tranco). Dodać osobną, merytoryczną zmienną „typ serwisu” (główny nurt / regionalny / alternatywny) przypisaną przed analizą i według niej raportować wyniki. Opisać kryterium ręcznego filtra S2 (review_S2.csv zawiera też domeny nienewsowe, np. dhosting.pl).

> **Weryfikator:** build_csv_domains.py:20 OTHER_STRATUM='S3' (domena spoza Tranco). domains.csv: tvp.info, oko.press, echodnia.eu mają S3 bez rangi, zmianynaziemi.pl (356224), goniec.pl (250444), demagog.org.pl S2. L. 56 łagodzi to sformułowaniem „między innymi”, ale l. 411 („S3 wybrano jako podejrzane”) i interpretacje tabeli grup według warstw są niezgodne z procedurą.

### [M10] H2 jest prawie pewna z konstrukcji, a dla H1 nie ma formalnego kryterium

*Waga:* **minor** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:50, 174, 228`

**Problem.** H2 („co najmniej jeden serwis spełnia definicję”) przy 37 serwisach, celowo dobranej podejrzanej warstwie i jednostronnym 5% na serwis ma wysokie a priori prawdopodobieństwo potwierdzenia, więc słabo testuje cokolwiek. H1 jest uznana za potwierdzoną na podstawie przedziału π_min dla wyniku zbiorczego, bez porównania z marginesem dryfu, którego używacie dla serwisów. Deklaracje „reguła ustalona przed obejrzeniem wyników” i „5% przyjęliśmy przed obejrzeniem” nie są niczym udokumentowane.

**Dowód.** Nadwyżka zbiorcza wynosi +3,8 pp, a δ dla serwisów 2,9 pp. Placebo dla poziomu zbiorczego nie zostało policzone. Sami szacujecie około 2 fałszywych przekroczeń w najgorszym przypadku (l. 412).

**Poprawka.** Przeformułować H2 na pytanie ilościowe (ile serwisów i które, z kontrolą FDR, np. Benjamini–Hochberg na jednostronnych p-wartościach P(π_min < 20%)). Dla H1 policzyć placebo na poziomie zbiorczym (rok vs pozostałe dwa, ze zmianą składu) i porównać z nim +3,8 pp. Dla deklaracji o kolejności decyzji podać hash commita z ustawieniami sprzed wyników albo usunąć te deklaracje.

> **Weryfikator:** Teza, że H2 jest „prawie pewna z konstrukcji”, nie ma dowodu. Przy π = 0 serwis zostaje uznany za masowy tylko wtedy, gdy nadwyżka przekracza δ i jednocześnie dolna granica π_gold przekracza 20%. To wymaga nadwyżki rzędu kilku pp na 5. percentylu. Szacunek z l. 412 (około 2 fałszywe przekroczenia) dotyczy najgorszego przypadku π ≈ 20%, a nie hipotezy zerowej. Słuszne są dwa punkty. Wynik zbiorczy +3,8 pp nie jest porównany z żadnym placebo na poziomie zbiorczym, bo δ = 2,9 pp jest marginesem dla pojedynczego serwisu. Deklaracje o regule ustalonej przed obejrzeniem wyników (l. 152, 174) nie są udokumentowane. Historia git nie pokazuje commita z ustawieniami sprzed wyników, a notebook wyników jest w tym samym commicie co preprint.
>
> **Wersja skorygowana:** Dla H1 brakuje placebo na poziomie zbiorczym. +3,8 pp porównano tylko z przedziałem bootstrapowym, a δ dotyczy pojedynczego serwisu. Deklaracje o kolejności decyzji (l. 152, 174) trzeba udokumentować, np. commitem lub prerejestracją, albo usunąć. Zamiast tezy o „pewności H2” lepiej raportować liczbę serwisów masowych z kontrolą FDR.

### [M11] Brak przeglądu literatury i najbliższych prac porównawczych

*Waga:* **minor** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:46`

**Problem.** Wprowadzenie cytuje tylko dwie prace pomiarowe. Brakuje najbliższego odpowiednika metodologicznego: Hanley i Durumeric (ICWSM 2024, „Machine-Made Media”) mierzyli wzrost udziału tekstów syntetycznych przed i po ChatGPT w serwisach głównego nurtu i dezinformacyjnych. Brakuje też prac o kwantyfikacji udziału bez etykiet (Forman 2008; Saerens i in. 2002; Liang i in. 2024, ICML, „Monitoring AI-modified content at scale”, estymacja rozkładowa). Notebook (komórka 1) je omawia, ale do pracy nie trafiły.

**Dowód.** Bibliografia (l. 420–433) ma 12 pozycji i żadnej z literatury o kwantyfikacji. Wybór Rogana-Gladena zamiast metod rozkładowych jest uzasadniony tylko w notebooku.

**Poprawka.** Dodać krótką sekcję „Prace pokrewne” (pomiar AI w mediach, kwantyfikacja/ACC vs. metody rozkładowe, detekcja w językach innych niż angielski) i przenieść do pracy uzasadnienie wyboru ACC/Rogana-Gladena z notebooka. Przy Russell i in. zaznaczyć, że używają komercyjnego Pangrama, a nie EditLens.

> **Weryfikator:** Bibliografia ma 12 pozycji i nie ma w niej literatury o kwantyfikacji. Komórka 1 notebooka cytuje Formana (2008) i Saerensa i in. (2002) oraz uzasadnia wybór ACC. To się zgadza. Nieprawdą jest natomiast, że notebook omawia Hanleya i Durumerica oraz Lianga i in. (2024, ICML). Grep po src/ i docs/ nie znajduje ani „Hanley”, ani „Machine-Made”. Praca cytuje inną pracę Lianga (2025, Nature Human Behaviour).
>
> **Wersja skorygowana:** Brakuje literatury o kwantyfikacji (Forman 2008, Saerens i in. 2002), choć uzasadnienie wyboru ACC jest w komórce 1 notebooka main-results. Brakuje też najbliższej pracy pomiarowej o mediach (Hanley i Durumeric, ICWSM 2024) i metody rozkładowej Lianga i in. (ICML 2024). Tych dwóch prac nie ma ani w pracy, ani w repozytorium. Trzeba dodać krótką sekcję o pracach pokrewnych i przenieść do niej uzasadnienie z notebooka.

### [M12] Odtwarzalność: niezapisana wersja adaptera, prywatne G2, odwołania do nieistniejących plików

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:76, 137, 438; data/detect/pangram.meta.json; docs/results/gold_eval/README.md`

**Problem.** Główna liczba całej pracy (TPR = 26%) pochodzi z prywatnych tekstów G2, których nie da się ponownie ocenić. Wersja adaptera Pangrama nie jest przypięta: meta.json zawiera tylko 'pangram/editlens_Llama-3.2-3B', bez rewizji i hasha. Praca odsyła do plików, których nie ma w repozytorium. Gold dla Bielika liczono przy 1024 tokenach, a dane przy 512.

**Dowód.** Brak docs/preprint/tables/domains.csv (l. 438), figures/fig01b_coverage_heatmap i fig02b_roc (l. 76, 137). data/processed jest w .gitignore i trzeba go odbudować (`make pipeline`, u mnie dało 35 628 tekstów, zgodnie z pracą). W README gold_eval: „cannot be re-run from the repo alone”.

**Poprawka.** Przypiąć rewizję adaptera i modelu bazowego (hash z Hugging Face) i podać ją w pracy. Opublikować G2 (to teksty wygenerowane przez model, więc bez praw autorskich do tekstu ludzkiego) albo przynajmniej wyniki i identyfikatory par z hashami. Uzupełnić brakujące pliki lub usunąć odwołania. Dodać w pracy sekcję „Dostępność danych i kodu” z commitem, listą crawli i komendami odtwarzającymi tabele.

> **Weryfikator:** pangram.meta.json zawiera tylko nazwę adaptera, bez rewizji i hasha. Nie ma w repo docs/preprint/tables/domains.csv, fig01b ani fig02b. data/processed jest w .gitignore (linie 23–24) i u mnie jest pusty. README gold_eval:28 mówi „cannot be re-run from the repo alone”. Teksty G2 nie są w repo (data/derived/gold zawiera tylko g1_2020_review.csv).

### [M8] Grudzień 2022 jest w okresie „ludzkim”, choć abstrakt mówi o tekstach sprzed grudnia 2022

*Waga:* **nit** (referent: minor) · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:36, 142, 409`

**Problem.** Abstrakt: „Przyjmujemy, że artykuły sprzed grudnia 2022 r. napisali ludzie”. W metodzie okres bazowy to jednak całe lata 2020–2022 (GOLD_YEARS = 2020–2022 w pipeline/build.py), a grudzień 2022 r. jest już po premierze ChatGPT. Ze względu na moment crawla (CC-MAIN-2023-06) grudzień stanowi dużą część roku 2022.

**Dowód.** 1700 z 6509 tekstów z 2022 r. (26%) ma datę z grudnia 2022 r. Ich odsetek oznaczonych to 4,7% wobec 5,0% w styczniu–listopadzie 2022 r., więc empirycznie wpływ jest pomijalny, ale tekst pracy jest niespójny z kodem.

**Poprawka.** Albo wyłączyć grudzień 2022 r. z kalibracji i b, albo poprawić abstrakt na „z lat 2020–2022” i dopisać zdanie z liczbami 4,7% / 5,0% jako sprawdzenie, że grudzień 2022 r. nie jest skażony.

> **Weryfikator:** GOLD_YEARS = range(2020, 2023) w build.py:44. Grudzień 2022 r. ma 1701 z 6517 tekstów (26%). Odsetek oznaczonych wynosi w nim 4,6% wobec 4,9% w pozostałych miesiącach 2022 r., więc wpływ jest pomijalny. Abstrakt (l. 36) mówi „sprzed grudnia 2022 r.”, a metoda „z lat 2020–2022”. To niespójność w opisie bez wpływu na wyniki, dlatego obniżam do nit.

### Przeoczenia wskazane przez weryfikatora (A)

- preprint.tex:256, 397 (zmianynaziemi.pl): referent nie zauważył, że zmiana szablonu całkowicie pokrywa się z oznaczeniami. W 2024 r. 121 ze 125 tekstów zaczyna się od 'Image' i 78,5% z nich jest oznaczonych, a wszystkie 4 teksty bez prefiksu nie są oznaczone (0/4). Dla tych tekstów crawl to CC-MAIN-2025-05. Na tych danych nie da się więc rozdzielić AI i nowego szablonu. Konieczne jest przeliczenie wyników Pangrama i Binoculars po usunięciu prefiksu, bo prefiks może też tłumaczyć wspólne oznaczenia obu detektorów z M5.
- preprint.tex:162, 166: margines δ to 95. percentyl różnic placebo zebranych ze wszystkich serwisów o bardzo różnych licznościach, więc zawiera głównie szum próbkowy małych serwisów, a nie dryf. Ten sam szum jest drugi raz uwzględniony w przedziale Beta dla serwisu. Kryterium jest więc podwójnie ostrożne dla dużych serwisów i nieostrożne wobec rzeczywistego dryfu, który się nie zmniejsza wraz z n. Poprawka: zestandaryzować różnice placebo przez ich błąd próbkowy (z-score) albo oszacować wariancję dryfu ponad szum dwumianowy (np. model losowych efektów) i dodać ją do przedziału serwisu.
- preprint.tex:166 (pokrycie lat): w części serwisów okres bazowy to w praktyce jeden lub dwa lata, np. elblag.net ma 200/200/42 teksty w latach 2020–2022, a goniec.pl nie ma tekstów z 2020 r. Wtedy placebo „rok vs dwa pozostałe” nie istnieje albo jest zdominowane przez jeden rok. Trzeba podać, dla ilu serwisów z 37 placebo jest w ogóle wykonalne, i oznaczyć serwisy z niepełnym okresem bazowym.


## B. Statystyka

**Ocena ogólna.** Wszystkie kluczowe liczby udało się odtworzyć. Zbudowałem data/processed w scratchpadzie (`news_detector.pipeline`, seed 42) i uruchomiłem kod z main-results.ipynb bez rysunków. Zgadzają się: zmianynaziemi π_min 34,5 [29,8; 39,3], goniec π_gold 50,1 [31,4; 77,0], wynik zbiorczy 4,0% [2,4; 6,1] i 18,1% [9,7; 32,2], δ = 2,9 pp, TPR 26% [18,4; 35,4] oraz tabele odporności. Sam estymator Rogana-Gladena i symulacja Beta-Jeffreys są poprawne, gdy TPR jest dobrze określony. Słabości leżą jednak w miejscach, od których zależą wnioski. Margines δ przy FPR 5% to wyłącznie szum dwumianowy (φ = 1,02), nie zależy od n serwisu i nigdy nie zmienia decyzji „masowo”, więc nie chroni przed dryfem po 2022 r. Do tego goniec.pl wypada przy dryfie 2,75 pp, czyli równym δ. Klasyfikacja globalna.info zależy od ziarna Monte Carlo. Wynik zbiorczy w dużej mierze zależy od celowo dobranych serwisów S2/S3. Symulacja pokrycia nie sprawdza czynników, które naprawdę grożą wnioskom: przeniesienia TPR i nadmiernej dyspersji przy FPR 10-20%. Mocne wyniki (zmianynaziemi.pl, w mniejszym stopniu goniec.pl) przetrwają, ale reguła klasyfikacji i opis niepewności wymagają poprawek.

**Mocne strony:**
- Pełna odtwarzalność: po zbudowaniu data/processed (seed 42) notebook odtwarza co do 0,1 pp wszystkie liczby z tab. zbiorczy, appendix, tab:fpr, tab:pokrycie_sym i tab:rok (np. 18 732 / 2 082 teksty kalibracji/testu, 17 z 37 serwisów > δ).
- Porównanie wewnątrz serwisu (własne b) i poprawka na skład w wyniku zbiorczym poprawnie usuwają zmianę składu crawla; próg zależy tylko od danych sprzed 2023 r., więc nie ma przecieku z okresu 'po' do kontrastu r-b.
- Para π_min / π_gold to uczciwe ograniczenie od dołu i scenariusz realistyczny zamiast jednej liczby zależnej od nieprzenośnego TPR; π_min nie zależy od zbioru gold.
- Test placebo jest dobrze pomyślany; przy FPR 5% wariancja zmian rok do roku w latach 2020-2022 jest dokładnie dwumianowa (φ≈1,02), co samo w sobie jest mocnym (i niewykorzystanym) argumentem za stabilnością detektora.
- Symulacja pokrycia tą samą procedurą co dla serwisów oraz jawne wyjaśnienie 90%/95% to rzadka i cenna praktyka; dolna granica 5. percentyla ma ~95% pokrycia przy poprawnie określonym TPR.
- Ostateczne wnioski (tylko zmianynaziemi.pl i goniec.pl jako stabilne) są zgodne z tym, co daje formalna korekta na wielokrotne porównania (BH), choć artykuł tego nie pokazuje.

### [STAT-1] Margines δ to czysty szum dwumianowy, nie zależy od n serwisu i nie chroni wniosków przed dryfem

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:166, 186, 337, 360, 364, 403; notebook cell 24 (placebo_changes), cell 30 (domain_shares)`

**Problem.** Artykuł przedstawia δ jako 'margines dryfu' i 'kryterium ostrożne'. Twierdzi też, że warunek nadwyżka > δ częściowo chroni przed złamaniem niezależności (l. 360). Obliczenia pokazują trzy problemy. (a) Przy FPR 5% rozkład 110 różnic placebo w całości wyjaśnia losowość dwumianowa, więc δ nie mierzy dryfu. (b) δ to jedna liczba wyznaczona dla porównań n≈200 vs n≈390, a stosuje się ją do serwisów o bardzo różnym n. Dla małych n kryterium jest więc liberalne, a nie ostrożne. (c) Dla grup 'masowych' warunek > δ nigdy nie jest wiążący, bo dolna granica π ≥ 20% sama wymusza nadwyżkę ≫ δ. Nie daje więc żadnej ochrony. Właściwe zagrożenie, czyli dryf zaczynający się po 2022 r., nie trafia do przedziałów. Stąd stwierdzenie, że goniec.pl jest stabilny 'przy każdym marginesie dryfu' (l. 364, 403), jest puste.

**Dowód.** Moje obliczenia na danych notebooka. Σ(różnica²)/Σ(wariancja dwumianowa) = 1,02 (bootstrap po serwisach 95%: 0,66-1,49). Odchylenie standardowe różnic placebo wynosi 2,05 pp, a oczekiwane dwumianowe 2,01 pp. 95. percentyl samego szumu dwumianowego to 3,2 pp, wobec δ = 2,9 pp. Szum dla porównania 3 lata vs 3 lata, liczony dla konkretnego serwisu (1,645·SE): pap.pl (83/339) 7,0 pp, money.pl (115/300) 4,4 pp, o2.pl (600/600) 1,6 pp. δ = 2,9 pp jest więc za niskie dla pap.pl i money.pl i za wysokie dla o2.pl. Z własnym progiem szumu nadwyżkę ma 20 serwisów, z δ 17. Analiza punktu krytycznego (o ile pp trzeba przesunąć r w dół, żeby 5. percentyl π_gold spadł poniżej 20%): goniec.pl 2,75 pp (≈δ), nczas.com 0,75 pp, pap.pl 0,65 pp, elblag.net 0,45 pp, globalna.info 0,10 pp, zmianynaziemi.pl 24 pp (dla π_min 9,6 pp). Po odjęciu δ od r dolne granice π_gold wynoszą: goniec 19,4%, nczas 11,0%, elblag 8,0%, pap 6,4%.

**Poprawka.** Należy przestać nazywać δ marginesem dryfu przy FPR 5% i napisać wprost, że placebo nie wykazuje żadnej wariancji ponad dwumianową (φ≈1,0). To mocny argument za stabilnością detektora. Warunek '> δ' trzeba zastąpić testem uwzględniającym n serwisu albo usunąć jako redundantny wobec dolnej granicy. Zamiast niego proponuję raportować dla każdego serwisu masowego dryf krytyczny: przesunięcie r, przy którym dolna granica spada poniżej 20% (wartości powyżej). Trzeba też wprost napisać, że goniec.pl wypada przy dryfie ≈ δ, a kandydaci przy dryfie < 1 pp. Ograniczenie nr 9 i zdanie z l. 360 o 'ochronie' przez δ należy poprawić.

> **Weryfikator:** Odtworzyłem dane notebooka (próg 0,472, δ = 2,917 pp, tabela serwisów zgodna z aneksem). Dla 110 porównań placebo przy FPR 5% wychodzi φ = Σd²/ΣVar = 1,02, bootstrap po serwisach 0,66–1,50. SD różnic to 2,04 pp, a oczekiwane dwumianowe 2,01 pp. 95. percentyl samego szumu dwumianowego wynosi 3,3 pp (referent podał 3,2). To potwierdza punkt (a). Przesunięcia krytyczne r (siatka co 0,25 pp) też się zgadzają: goniec 2,75 pp, nczas 0,75, pap 0,75, elblag 0,5, globalna 0,25, zmianynaziemi 24 pp (dla π_min 9,75). Po odjęciu δ od r dolne granice π_gold wynoszą: goniec 19,3%, nczas 11,1%, elblag 8,1%, pap 6,5%. Zastrzeżenia do ustalenia: (1) Artykuł sam przyznaje w l. 337, że nadwyżki masowych (8–33 pp) są 'dużo większe niż każde δ' i że δ nie zmienia listy. Punkt (c) jest więc częściowo przyznany. Prawdziwym błędem jest zdanie z l. 360, że warunek > δ 'częściowo chroni' przed zależnością artykułów. (2) φ≈1 nie dowodzi braku dryfu: przy górnej granicy 1,5 dopuszczalne jest ok. 50% dodatkowej wariancji. Lepiej pisać 'placebo nie wykazuje wariancji ponad dwumianową'. (3) Odejmowanie δ od r to test wrażliwości, a nie przedział: δ zawiera szum, który symulacja już uwzględnia, więc podwaja jego liczenie. Ten wariant zawyża kruchość wyniku. Diagnoza i propozycja raportowania dryfu krytycznego są trafne, ważność major jest uzasadniona.
>
> **Wersja skorygowana:** δ (95. percentyl placebo, 2,9 pp) przy FPR 5% niemal w całości wyjaśnia szum dwumianowy porównań 1 rok vs 2 lata: φ = 1,02 [0,66; 1,50], a 95. percentyl samego szumu to 3,3 pp. Nie jest to więc oszacowanie dryfu. δ jest stałe i nie zależy od n serwisu. Dla grup masowych warunek > δ nie jest wiążący, co artykuł przyznaje w l. 337. Zdanie z l. 360, że warunek > δ chroni przed zależnością artykułów, jest jednak fałszywe. Proponowana poprawka: opisać placebo jako brak nadmiernej dyspersji (z zastrzeżeniem, że φ do ~1,5 nie jest wykluczone) i usunąć argument o ochronie. Dla serwisów masowych podać dryf krytyczny, czyli przesunięcie r, przy którym dolna granica π_gold spada poniżej 20%: goniec ≈2,75 pp, nczas i pap ≈0,75 pp, elblag ≈0,5 pp, globalna ≈0,25 pp. Trzeba przy tym zaznaczyć, że to analiza wrażliwości na systematyczny dryf po 2022 r., a nie dodatkowy składnik szumu.

### [STAT-2] Klasyfikacja globalna.info (i dokładność dolnych granic) zależy od ziarna Monte Carlo

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:170, 262 ("dolna granica π_gold 19,5% wobec wymaganych 20%"), tab:grupy l. 239-241, tabela_serwisow.tex (globalna.info), tab:detektory l. 382-383; notebook cell 4 (N_BOOT=5000), cell 30`

**Problem.** Reguła porównuje 5. percentyl z 5000 losowań z progiem 20% z dokładnością do 0,1 pp. Dla serwisów blisko progu błąd Monte Carlo jest większy niż ta różnica. Wynik zależy też od tego, w jakiej kolejności serwisy zużywają wspólny strumień RNG. Dla globalna.info wartość 19,5% zgłoszona w artykule wynika z pechowego ziarna. Przy dokładnej symulacji serwis spełnia warunek 'masowo: prawdopodobnie'. W analizie głównej powinno więc być 6, a nie 5 serwisów masowych, albo trzeba napisać, że granica jest nierozstrzygalna.

**Dowód.** 200 niezależnych ziaren po 5000 losowań: 5. percentyl π_gold dla globalna.info ma średnią 20,38%, SD 0,40, zakres 19,2-21,6. Próg ≥ 20% spełnia w 82% ziaren. Przy 200 000 losowań P(π_gold < 0,2) = 0,047 < 0,05, więc globalna.info spełnia regułę. Dla pap.pl średnia wynosi 23,5% (SD 0,54), a artykuł podaje 22,9. Niespójności między miejscami w samym artykule wynikają z tego samego źródła: goniec π_min [7,5; 14,2] w l. 258 i tab:detektory wobec [7,5; 14,1] w aneksie, pap.pl [4,4; 15,5] w tab:detektory wobec [4,2; 15,6] w aneksie. numpy.beta zużywa zmienną liczbę liczb losowych, więc strumienie się rozjeżdżają.

**Poprawka.** Należy zwiększyć N_BOOT do ≥ 100 000 (to tanie, bo losowania są wektorowe) albo liczyć jednostronne p = P(π < 0,2) i podawać jego błąd MC. Każdy serwis powinien mieć własne ziarno (np. hash domeny), żeby wynik nie zależał od kolejności. Po tej zmianie trzeba przeliczyć tab:grupy i aneks oraz poprawić opis globalna.info w l. 262 i fig06. Wszystkie tabele należy generować z jednego przebiegu.

> **Weryfikator:** Sprawdziłem 200 ziaren po 5000 losowań. Dla globalna.info 5. percentyl π_gold ma średnią 20,43%, SD 0,42, zakres 19,4–21,6, a próg ≥ 20% spełnia 84,5% ziaren. Przy 200 000 losowań P(π_gold < 0,2) = 0,047, a q05 = 20,4%. Dla pap.pl średnia wynosi 23,5% przy wartości 22,9% w artykule. Niespójności w samym tekście są prawdziwe: goniec π_min [7,5; 14,2] w l. 258 i tab:detektory wobec [7,5; 14,1] w aneksie, pap [4,4; 15,5] wobec [4,2; 15,6]. Wynika to z różnej kolejności zużycia RNG (osobne wywołania z SEED=42, rng.beta zużywa zmienną liczbę liczb losowych). Klasyfikacja globalna.info zależy od ziarna, a tab:grupy (5 vs 6 masowych) od błędu MC. Przy dokładnej symulacji serwis formalnie spełnia regułę, ale z marginesem 0,003, więc uczciwie jest napisać, że jest na granicy. Ważność major się utrzymuje, bo zmienia się główna tabela grup.

### [STAT-3] Wynik zbiorczy 4-18% zależy od celowo dobranych serwisów i wag z kwoty crawla; nie jest wielkością populacyjną

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:36 (abstrakt), 170, 223, 228, 403; notebook cell 27 (overall)`

**Problem.** Wynik zbiorczy waży serwisy liczbą ich tekstów z lat 2023-2025 w crawlu, którą wyznacza kwota 200 na rok i dostępność w Common Crawl, a nie wielkość serwisu. Obejmuje też S3, dobrane celowo jako podejrzane. Jedna liczba 'w całej próbie' (abstrakt, dyskusja) nie odpowiada więc żadnej populacji, a w dużej mierze wyznaczają ją serwisy, które i tak są wynikiem osobnym. Abstrakt zestawia też szacunek punktowy π_min (4%) ze szacunkiem punktowym π_gold (18%) jako 'zakres'. Pełna niepewność to 2,4-32,2%.

**Dowód.** Przeliczenie z per-site k1, n1, b (π_min / π_gold). Cała próba: 4,0 / 18,1. Bez zmianynaziemi.pl: 3,3 / 15,0. Bez 5 serwisów 'masowych': 2,5 / 11,3. Tylko S1: 1,8 / 8,1 (n1 = 5566). S2: 5,2 / 23,3. S3: 6,1 / 29,0. Bez S3: 3,6 / 16,1. Sam zmianynaziemi.pl daje 19% całej nadwyżki oznaczonych tekstów, a pięć serwisów masowych 45%.

**Poprawka.** Wynik zbiorczy trzeba podawać osobno dla warstw (co najmniej S1 jako jedyną warstwę zbliżoną do 'głównego nurtu'), a w abstrakcie wyraźnie napisać, że dotyczy próby celowej. Należy dodać wariant bez serwisów masowych, żeby pokazać, czy zjawisko jest rozlane, czy skupione. W abstrakcie zamiast '4-18%' lepiej napisać np. 'od ≥ 2,4% (dolna granica π_min) do ~18% (π_gold, 95% CI 10-32%)'. Trzeba też uzasadnić wagi albo dodać wariant z równymi wagami serwisów.

> **Weryfikator:** Wszystkie liczby potwierdzone: cała próba 4,0/18,1, bez zmianynaziemi 3,3/15,0, bez 5 masowych 2,5/11,3, S1 1,8/8,1 (n1 = 5566), S2 5,2/23,3, S3 6,1/29,0, bez S3 3,6/16,1. Udział zmianynaziemi w nadwyżce wynosi 19,2%, a pięciu masowych 44,9%. Argument o wagach z kwoty crawla jest jednak słaby: przy równych wagach serwisów wychodzi 4,2/18,9, praktycznie to samo. Problemem jest skład próby (S3 i kilka serwisów), a nie sposób ważenia. Artykuł w l. 56 obiecuje 'Podajemy je osobno dla warstw', ale wynik zbiorczy podaje tylko łącznie. W abstrakcie jest 'w całej próbie', bez słowa o próbie celowej. Uwaga o '4–18%' jako zakresie dwóch szacunków punktowych jest trafna.
>
> **Wersja skorygowana:** Wynik zbiorczy (abstrakt, l. 223, 403) obejmuje celowo dobrane S3 i zależy od kilku serwisów. Bez 5 masowych wynosi 2,5/11,3%, dla samego S1 1,8/8,1%, a S3 daje 6,1/29,0%. Zmianynaziemi.pl to 19% całej nadwyżki, a pięć serwisów masowych 45%. Wagi nie są tu problemem, bo przy równych wagach serwisów wychodzi 4,2/18,9%. Problemem jest skład próby i brak wyników osobno dla warstw, choć l. 56 je obiecuje. Poprawka: podać wynik zbiorczy osobno dla S1, S2 i S3 oraz wariant bez serwisów masowych. W abstrakcie trzeba zaznaczyć, że próba jest celowa, i podać niepewność zamiast '4–18%' (π_min ≥ 2,4% jako dolna granica, π_gold ~18% [9,7; 32,2]).

### [STAT-4] Grupa 'prawdopodobnie' opiera się na TPR z G2, którego nieprzenośność pokazują dane samego artykułu; brakuje progu TPR*

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:162, 184, 260, 308-310, 364`

**Problem.** Jeśli model Rogana-Gladena z TPR_gold jest poprawny, π_gold powinno być niezależne od FPR. Tymczasem spada z 21,5% (FPR 1%) do 11,3% (FPR 20%), a dla zmianynaziemi.pl r przekracza TPR. To bezpośredni dowód, że czułość na tekstach z serwisów różni się od czułości na G2, i to w sposób zależny od progu. Symulacja uwzględnia tylko błąd próbkowania TPR (Beta z 26/100), nie błąd przeniesienia. Dolna granica π_gold jest więc warunkowa względem silnego, częściowo obalonego założenia, a artykuł nie pokazuje, jak blisko granicy tego założenia są poszczególne serwisy.

**Dowód.** TPR krytyczny, czyli największa czułość, przy której dolna granica nadal ≥ 20% (TPR* ≈ b + q05(r-b)/0,2): goniec.pl 0,40, nczas.com 0,31, elblag.net 0,29, globalna.info 0,26, pap.pl 0,26, przy TPR_gold = 0,26 (95% CI do 0,354). Dla pap.pl i elblag.net wystarczy, że prawdziwa czułość leży w górnej połowie przedziału TPR z G2. Dla zmianynaziemi r = 0,365 > górna granica TPR 0,354, a P(TPR_gold < r) = 0,987, więc model z TPR_gold jest dla tego serwisu odrzucony.

**Poprawka.** Dla każdego serwisu z grupy 'prawdopodobnie' warto podawać TPR* i porównywać go z przedziałem TPR (np. 'goniec pozostaje masowy, jeśli czułość na jego tekstach AI < 40%'). Zmienność π_gold z FPR (tab:fpr) należy opisać jako test specyfikacji modelu, który model nie przechodzi, a nie jako 'brak sprzeczności, bo przedziały się nakładają' (l. 310). Przedziały się nakładają, bo wszystkie warianty używają tych samych 100 par. Różnicę π_gold(1%) − π_gold(20%) trzeba przetestować sparowanym bootstrapem po parach G2 i serwisach.

> **Weryfikator:** Policzyłem TPR* dokładnie, czyli największe stałe TPR, przy którym q05 ≥ 20% (200 000 losowań): goniec 0,415, nczas 0,31, pap 0,30, elblag 0,295, globalna 0,275. Referent podał dla pap i globalna 0,26, bo użył przybliżenia. Wszystkie wartości dla kandydatów leżą w przedziale TPR [0,18; 0,35], więc główna teza się utrzymuje. Dla zmianynaziemi P(TPR_gold < r = 0,365) = 0,987, potwierdzone. Artykuł sam jednak przyznaje nieprzenośność TPR: w l. 162 ('może być inna'), w l. 310 ('czułość zmierzona na przeróbkach zaniża czułość na tekstach z serwisów') i w ograniczeniu 1. Zarzut 'nie pokazuje' jest więc za mocny. Brakuje natomiast ilościowego TPR* dla poszczególnych serwisów. Dodatkowo zmiana π_gold z FPR nie wynika wyłącznie z nieprzenośności TPR, bo przy 20% rośnie też nadmierna dyspersja i dryf (φ = 2,6). Nie jest to więc czysty test specyfikacji. Zdanie o nakładających się przedziałach (l. 310) rzeczywiście jest w artykule.
>
> **Wersja skorygowana:** Artykuł przyznaje jakościowo, że TPR z G2 może się nie przenosić (l. 162, 310, ogr. 1), ale nie pokazuje, jak blisko granicy założenia są poszczególne serwisy. TPR*, czyli największa czułość, przy której dolna granica π_gold ≥ 20%, wynosi: goniec 0,42, nczas 0,31, pap 0,30, elblag 0,30, globalna 0,28. Przedział TPR z G2 to [0,18; 0,35]. Kandydaci odpadają więc, gdy prawdziwa czułość leży w górnej części tego przedziału. Dla zmianynaziemi P(TPR_gold < r) ≈ 0,99, więc model z TPR_gold jest dla niego niespójny. Poprawka: podać TPR* dla każdego serwisu z grupy 'prawdopodobnie'. Spadek π_gold z 21,5 do 11,3% przy rosnącym FPR trzeba opisać jako sygnał nieprzenośności TPR i/lub nadmiernej dyspersji przy wysokim FPR, a nie zamykać go stwierdzeniem, że przedziały się nakładają (zależą od tych samych 100 par).

### [STAT-5] Symulacja pokrycia nie testuje głównych zagrożeń; scenariusz 'wariancja ×3' jest arbitralny, choć dyspersję da się oszacować z danych

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:341-360, tab:pokrycie_sym l. 343-358, 415; notebook cell 53 (simulate_coverage)`

**Problem.** Symulacja zakłada, że prawdziwe TPR = 0,26 dokładnie (dobra specyfikacja). Sprawdza tylko π_gold przy π ∈ {0,2; 0,4} i nie testuje ścieżki π_min ('mocne dowody'). Wariancję ×3 przyjęto bez uzasadnienia, a dane pozwalają ją zmierzyć. Przy FPR 5% wychodzi φ≈1, więc ostrzeżenie o pokryciu 85-87% jest przesadnie pesymistyczne. Przy FPR 10% i 20%, użytych w analizie odporności, dane pokazują wyraźną nadmierną dyspersję, której przedziały nie uwzględniają. Warianty FPR 20% są więc antykonserwatywne. Dotyczy to dokładnie serwisów, które wchodzą do grupy 'masowe' tylko przy 20% (globalna, interia, lelum, money).

**Dowód.** Dyspersja z placebo (Σd²/ΣVar): FPR 1% 1,00, FPR 5% 1,02 (95% CI bootstrap po serwisach 0,66-1,49), FPR 10% 1,42, FPR 20% 2,61. δ przy 20% (9,6 pp) wobec czystego szumu dwumianowego 5,8 pp. Wzrost δ z 2,9 do 9,6 pp tylko w części jest więc dryfem, bo do ~5,8 pp tłumaczy go sama zmiana p(1−p). W kodzie cell 53 TPR do generowania danych jest równe 0,26, a 'zaobserwowane' k_tpr ~ Bin(100, 0,26). Nie ma scenariusza z TPR_site ≠ TPR_gold.

**Poprawka.** Należy oszacować φ z placebo dla każdego FPR i wbudować je w losowania (np. Beta z wariancją pomnożoną przez φ̂, albo beta-dwumianowy) w regule i w wariantach odporności. Scenariusz ×3 trzeba zastąpić empirycznym φ̂ i jego górną granicą (~1,5). Do symulacji należy dodać scenariusze z TPR_site = 0,4 i 0,6 przy TPR_gold = 0,26 oraz scenariusz dla reguły π_min. Ograniczenie 9 i l. 360 trzeba przeformułować na podstawie φ̂ (przy 5% niezależność na poziomie rok×serwis nie jest odrzucana). Uwaga dla wariantów FPR 10% i 20%: wynikające z nich wejścia serwisów do grupy masowych wymagają szerszych przedziałów.

> **Weryfikator:** Przeliczyłem φ z placebo przy progach odtworzonych z kalibracji (0,612/0,472/0,379/0,251, δ zgodne z tab:fpr: 1,5/2,9/5,4/9,6). Wyniki: FPR 1% φ = 0,99 [0,68; 1,38], 5% 1,02 [0,66; 1,50], 10% 1,42 [1,02; 1,85], 20% 2,62 [1,59; 3,84]. Szum czysto dwumianowy daje δ: 1,5/3,3/4,5/6,0 pp. Kod cell 53 generuje dane z tpr = 0,26 i nie ma scenariusza z TPR_site ≠ TPR_gold ani ścieżki π_min. Wszystkie twierdzenia referenta się potwierdzają. Uwaga łagodząca: serwisy wchodzące tylko przy FPR 20% artykuł i tak pomija jako niestabilne (l. 304). Antykonserwatywność wariantu 20% dotyczy jednak również 'stabilności' gońca i zmianynaziemi przy tym progu.

### [STAT-6] Wielokrotne porównania: arytmetyka poprawna, ale brak formalnej korekty, która by ją rozstrzygnęła

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:412, 174, 298-304, 364`

**Problem.** 37·0,05 = 1,85 ≈ 2 jest poprawne jako oczekiwana liczba fałszywych wskazań w najgorszym przypadku. Przy pięciu serwisach 'masowych' w analizie głównej oznacza to jednak, że dwa z trzech kandydatów mogą być fałszywe. Prawdopodobieństwo co najmniej jednego fałszywego wskazania w tym scenariuszu wynosi 1 − 0,95^37 ≈ 85%. Do tego dochodzi 9 wariantów, a lista 'kandydatów' jest sumą po wariantach (ogród rozwidlających się ścieżek). Brakuje q-wartości, które zastąpiłyby opis słowny.

**Dowód.** Jednostronne p = P(π_gold < 0,2) z 200 000 losowań: zmianynaziemi < 1e-5, goniec 0,0017, nczas 0,023, elblag 0,033, pap 0,034, globalna 0,047. Benjamini-Hochberg (37 serwisów) daje q: zmianynaziemi ≈ 0, goniec 0,031, nczas, elblag i pap 0,25, globalna 0,29. Holm: tylko zmianynaziemi < 0,05 (goniec 0,060). Dla H0: nadwyżka ≤ 0 BH przechodzi 16 serwisów, Bonferroni 9.

**Poprawka.** Należy dodać kolumnę q (BH) do aneksu i do tab:grupy. Wynik BH lepiej uzasadnia podział na 'wynik' (zmianynaziemi, goniec) i 'kandydatów' niż liczenie wariantów. W ograniczeniu 6 trzeba podać P(≥ 1 FP) ≈ 85% w najgorszym przypadku. Warto też zaznaczyć, że wariant 'definicja 10%' nie jest testem odporności tej samej hipotezy, bo zmienia pytanie, i nie powinien liczyć się do 'sześciu z dziewięciu' (l. 364).

> **Weryfikator:** Moje wartości P(π_gold < 0,2) z 200 000 losowań: zmianynaziemi 0, goniec 0,0015, nczas 0,023, elblag 0,033, pap 0,034, globalna 0,047, demagog 0,10. BH dla m = 37 daje: goniec ≈0,028, nczas, elblag i pap ≈0,25, globalna ≈0,29. W metodzie Holma goniec ≈0,054 > 0,05. Prawdopodobieństwo co najmniej jednego fałszywego wskazania 1−0,95^37 = 0,85 się zgadza. Zastrzeżenie: te 'p' to częstości z symulacji parametrycznej, a nie ścisłe p-wartości (H0 złożona, wspólne losowanie TPR wprowadza dodatnią zależność, co dla BH jest dopuszczalne). Trzeba to zaznaczyć. Uwaga o wariancie 'definicja 10%' liczonym do wariantów pap.pl (l. 364) jest trafna.

### [STAT-7] neon24.pl: 'dolna granica około 38%' to w rzeczywistości szacunek punktowy

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:294; notebook cell 37`

**Problem.** Liczba 37,7% to share(r̂ = 0,447; b = 0,112; TPR = 1), czyli wartość punktowa przy najgorszym b, a nie dolna granica. Artykuł nazywa ją 'dolną granicą udziału AI', co sugeruje zapas pewności, którego nie ma.

**Dowód.** k = 96, n = 215. Jednostronna 95% dolna granica r (Jeffreys) wynosi 0,391, więc π_min = (0,391 − 0,112)/(1 − 0,112) ≈ 31,5%. Wilson 2,5% daje 0,382 → 30,4%.

**Poprawka.** Należy napisać 'szacunek ~38%, jednostronna 95% dolna granica ~31% przy b = 11,2%'. Trzeba też dodać, że b = 11,2% to maksimum z 37 serwisów, a nie górna granica możliwego b.

> **Weryfikator:** Cell 37 liczy share(post.mean(), B_MAX, 1), czyli wartość punktową. Wynik: (0,447−0,1117)/(1−0,1117) = 37,7%. Jednostronna 95% dolna granica Jeffreysa dla r (96/215) wynosi 0,391, co daje π_min ≈ 31,5%. Tekst w l. 294 nazywa 38% 'dolną granicą udziału AI', więc zarzut jest słuszny.

### [STAT-8] Estymand 'udział 2023-2025' zależy od rocznej dostępności w crawlu (nczas.com, zmianynaziemi.pl)

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:48, 260, 266-268, tab:rok l. 283-287`

**Problem.** r liczy się z sumy tekstów z lat 2023-2025, więc lata ważone są liczbą artykułów w crawlu, a nie czasem. Przy skokowych zmianach estymand zależy od przypadkowej liczby tekstów w danym roku. Artykuł mówi o 'ostrożności' reguły (l. 268), ale nie pokazuje, że wynik zależy od tej arbitralnej wagi.

**Dowód.** nczas.com: 2023 4,5% (n = 200), 2024 51,2% (n = 41), łącznie r = 12,4%. Przy równych wagach lat r = 27,9%, a π_min ≈ 25% (wobec 9,3%). zmianynaziemi.pl: 10,2% (187) i 76% (125), czyli r = 36,5% przy wagach z crawla i 43,1% przy równych wagach lat.

**Poprawka.** Estymand trzeba zdefiniować jawnie (np. średnia z lat albo rok skoku). Należy dodać wariant z równymi wagami lat do analizy odporności, a tab:rok powiązać z regułą, np. 'masowy w co najmniej jednym roku z dolną granicą ≥ 20%'.

> **Weryfikator:** Z tab:rok i b: nczas r2023 ≈ 4,5% (n = 200), r2024 ≈ 51% (n = 41). Średnia z lat daje r ≈ 27,9% i π_min ≈ 25%, wobec 9,3% w artykule. Zmianynaziemi: 10,2% i 76%, czyli 36,5% przy wagach z crawla i 43,1% przy równych wagach lat. Artykuł zauważa w l. 268, że uśrednianie jest 'ostrożne' wobec późnych przejść, i podaje tab:rok. Nie definiuje jednak estymandu jako średniej ważonej liczbą tekstów w crawlu i nie pokazuje, że dla nczas.com wynik reguły zależy od tej wagi. Ważność minor jest właściwa.

### [STAT-9] zmianynaziemi.pl: π_gold '100,0 [100,0; 100,0]' to zdegenerowany przedział przy odrzuconym modelu

*Waga:* **minor** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:256; tabela_serwisow.tex (wiersz zmianynaziemi.pl); fig06`

**Problem.** Gdy r > TPR, Rogan-Gladen daje π > 1 i obcięcie zamienia całą masę na 1. Przedział [100; 100] sugeruje pewność, a w rzeczywistości oznacza, że model z TPR_gold nie pasuje do danych tego serwisu. Ta sama funkcja share() przypisuje π = 1 także wtedy, gdy wylosowane TPR ≤ b, co dla małych TPR (FPR 1%) może zawyżać górne końce.

**Dowód.** r = 0,365, TPR_gold = 0,26 [0,184; 0,354], P(TPR_gold < r) = 0,987 przy rozkładzie Jeffreysa. Wszystkie 5000 losowań π_gold = 1. Przy FPR 1% elblag.net też ma π_gold = 100%.

**Poprawka.** W tabeli trzeba podać 'n/d: r > TPR_gold (model niespójny)' zamiast 100,0 [100,0; 100,0], a na fig06 oznaczyć to osobnym symbolem. W metodach należy opisać regułę TPR ≤ b → π = 1 i podać, w ilu losowaniach wystąpiła (szczególnie dla FPR 1%).

> **Weryfikator:** Wpis 100,0 [100,0; 100,0] dla zmianynaziemi jest w tabela_serwisow.tex:16, a P(TPR_gold < r) = 0,987 się potwierdza. Artykuł interpretuje jednak π_gold > 100% słownie w l. 162 i 256, więc chodzi o sposób prezentacji, a nie ukryty błąd. Druga część zarzutu, że reguła TPR ≤ b → π = 1 może zawyżać górne końce przy FPR 1%, nie potwierdza się liczbowo. Przy FPR 1% P(TPR ≤ b) wynosi 3·10⁻⁵ dla elblag i 1,4·10⁻⁴ dla gońca. Elblag ma π_gold = 100% przy 1% z innego powodu: r = 10,8% > TPR = 10% (punkt), a P(TPR < r) = 0,58. Jest to ten sam objaw niespójności modelu co u zmianynaziemi, a nie artefakt gałęzi TPR ≤ b.
>
> **Wersja skorygowana:** Przy r > TPR_gold obcięcie daje zdegenerowany przedział 100,0 [100,0; 100,0] (zmianynaziemi.pl przy FPR 5%, elblag.net przy FPR 1%, gdzie r = 10,8% > TPR = 10%). Taki przedział sugeruje pewność, a w rzeczywistości oznacza, że model z TPR_gold nie pasuje do danych tego serwisu. Poprawka: w tabeli i na fig06 zamiast 100,0 [100,0; 100,0] podać 'n/d (r > TPR_gold)'. Gałąź TPR ≤ b w share() jest praktycznie nieaktywna (P < 0,0002), więc nie wymaga zmiany.

### [STAT-10] G1 w większości należy do zbioru kalibracyjnego, więc 'FPR na G1 = 6%' nie jest sprawdzeniem poza próbą

*Waga:* **minor** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:110, 142`

**Problem.** Artykuł prezentuje FPR 6% na 100 tekstach G1 obok odłożonego zbioru test jako dowód, że próg przenosi się na nowe teksty. Większość G1 wchodzi jednak do zbioru train, na którym ustawiono próg. Kolumna split w gold_scores.csv (dev/test) nie zgadza się z podziałem w data/processed, co może wprowadzać w błąd przy dalszych analizach. Na TPR (G2) nie ma to wpływu.

**Dowód.** Podział G1 (pair_id) w odbudowanym data/processed: train 74, test 15, dev 11 (wszystkie z 2020 r.). W gold_scores.csv: dev 52, test 48. Kalibracja obejmuje 18 732 teksty, test 2 082, co odpowiada liczbom z artykułu, więc podział jest tożsamy z autorskim.

**Poprawka.** Należy podawać FPR na G1 osobno dla 26 tekstów spoza kalibracji albo usunąć to zdanie jako argument o przenośności. Kolumnę split w pliku gold trzeba wyjaśnić albo przemianować. Opcjonalnie: przeliczyć próg z wyłączeniem G1 (wpływ pomijalny, ale czysty).

> **Weryfikator:** Dopasowałem G1 (pair_id = article_id) do odbudowanego podziału: 74 train, 11 dev, 15 test, wszystkie z 2020 r. Kalibracja obejmuje train+dev (18 732 teksty, zgodnie z artykułem), więc w kalibracji jest 85 tekstów G1, a poza nią 15, a nie 26, jak podaje referent w poprawce. Na tych 15 oznaczony jest 1 tekst (6,7%), w dev 0/11, w train 5/74. Kolumna split w gold_scores.csv (dev 52/test 48) rzeczywiście nie odpowiada podziałowi danych. Wpływu na TPR nie ma. Rdzeń zarzutu jest prawdziwy, liczba w poprawce błędna.
>
> **Wersja skorygowana:** 85 ze 100 tekstów G1 należy do zbioru kalibracyjnego (train 74, dev 11), na którym ustawiono próg. Tylko 15 jest w odłożonym zbiorze test (oznaczony 1 z 15). Wynik 'FPR na G1 = 6%' (l. 142) nie jest więc sprawdzeniem poza próbą. Poprawka: podać FPR na 15 tekstach spoza kalibracji (1/15) albo usunąć ten argument. Kolumnę split w gold_scores.csv (dev/test) trzeba objaśnić lub przemianować, bo nie odpowiada podziałowi data/processed.

### [STAT-11] Opis procedury TPR i przedziałów niespójny z kodem

*Waga:* **nit** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:142, 170`

**Problem.** L. 170 mówi, że symulacja losuje 'TPR (ze 100 par G2)', co sugeruje bootstrap par. Kod losuje TPR z Beta(26,5; 74,5), czyli z rozkładu Jeffreysa. Przedział TPR w tekście (l. 142) to Wilson, a w symulacji Jeffreys. Różnica liczbowa jest mała, ale czytelnik nie odtworzy procedury z opisu. AUC CI pochodzi z bootstrapu par, co jest poprawne, lecz nie jest opisane, a pary są skupione (po 5 z 24 serwisów).

**Dowód.** Wilson [18,4; 35,4], Jeffreys [18,2; 35,2], Clopper-Pearson [17,8; 35,7]. Kod: cell 5 draw_rate, cell 27/30 tpr_draws = draw_rate(k_tpr, n_tpr). AUC: cell 13, 1000 bootstrapów par.

**Poprawka.** Należy napisać 'TPR z rozkładu Beta(k+½, n−k+½) dla k = 26, n = 100' i ujednolicić metodę przedziału TPR w tekście i symulacji. W podpisie tab:auc warto dodać 'bootstrap par, 1000 powtórzeń' i wspomnieć o skupieniu G1 po serwisach.

> **Weryfikator:** L. 170 mówi o 'TPR (ze 100 par G2)', a draw_rate w cell 5 losuje Beta(k+½, n−k+½). Wilson dla 26/100 to [18,4; 35,4], zgodnie z l. 142, więc w tekście użyto innej metody niż w symulacji. Różnica liczbowa jest pomijalna. Ważność nit jest właściwa.

### Przeoczenia wskazane przez weryfikatora (B)

- Przeszacowanie dla wybranych serwisów (winner's curse), preprint.tex:258-260, 403. Pięć serwisów 'masowych' wybrano spośród 37 według tych samych danych, z których potem podaje się ich szacunki punktowe π_gold (50%, 51%, 43%, 40%) i dolne granice. Szacunki serwisów wybranych dlatego, że przekroczyły próg, są systematycznie zawyżone. Dotyczy to zwłaszcza pap.pl, gdzie b pochodzi z 83 tekstów. Warto to zaznaczyć w dyskusji albo pokazać, jak duży jest efekt, np. ściągając szacunki do średniej (shrinkage empiryczny Bayesa na r−b), zanim liczby z l. 258-260 trafią do abstraktu lub wniosków.
- Zbyt kategoryczne sformułowania o dolnej granicy, preprint.tex:36 (abstrakt: 'co najmniej 29,8% tekstów'), 256 ('co najmniej 29,8% tekstów musi pochodzić z AI nawet przy idealnym detektorze'), 403 ('z dolną granicą 31%' dla goniec.pl). 29,8% to jednostronna 95% granica ufności, a nie pewne minimum. Do tego warunkuje ją stałość b, której placebo nie gwarantuje po 2022 r. (sam artykuł przyznaje to w ogr. 3). Z kolei 31% dla gońca zależy od TPR_gold (TPR* = 0,42). Trzeba dopisać '(jednostronna granica 95%, przy założeniu stałego b)' oraz 'przy TPR z G2'.
- Wariant FPR 20% użyty jako argument stabilności, preprint.tex:300, 364, 403. Przy FPR 20% φ z placebo wynosi 2,62 [1,59; 3,84], a przedziały zakładają wariancję dwumianową. Zdanie, że goniec.pl i zmianynaziemi.pl są masowe 'przy każdym progu', opiera się więc w wariancie 20% na zbyt wąskich przedziałach. Pokrycie dolnej granicy z symulacji (tab:pokrycie_sym, wiersz ×3) sugeruje spadek do ok. 85–87%. Wariant 20% trzeba przeliczyć z przedziałami poszerzonymi o φ̂ albo opisać jako słabszy dowód.


## C. Spójność liczb i twierdzeń

**Ocena ogólna.** Liczby w preprincie zgadzają się ze sobą i z danymi lepiej niż zwykle. Odtworzyłem pipeline w scratchpadzie (35 823 → 35 628 artykułów, próg 0,472, 18 732/2 082 teksty, test FPR 4,4% [3,6; 5,3], 110 porównań placebo, δ = 2,3/2,9/4,7 pp). Zgadzają się wszystkie sumy w tab:pokrycie, tab:grupy (11/19/7, 1+4+12+20 = 37, 17 serwisów > δ), liczby w tab:wylaczone, tab:fpr, tab:pokrycie_sym i liczba dziewięciu wariantów. Zgadza się też, ile wariantów przetrwał każdy kandydat (8/9/6/6/4). Są jednak niespójności w treści. Teza „żaden serwis S1 nie jest masowy” jest zastrzeżona tylko dla o2.pl, choć fig08 pokazuje cztery serwisy S1 masowe w co najmniej jednym wariancie. Dla neon24.pl szacunek punktowy jest opisany jako „dolna granica”. Zdanie o „spadku π_gold” odwraca kierunek zmiany z tabeli. Te same π_min mają różne przedziały w tab:detektory i w aneksie. Kilka odwołań do plików w repozytorium prowadzi donikąd, a figur fig01–fig09 nie generuje żaden kod w repozytorium. Pozostałe uwagi to doprecyzowania definicji (panel 16 serwisów, skład placebo, 14 167 vs 14 814 tekstów) i drobne usterki.

**Mocne strony:**
- Sumy i rozkłady są wewnętrznie spójne: tab:pokrycie sumuje się do 35 628. tab:grupy po warstwach (S1 = 11 + gazeta.pl = 12; S2 = 19 + wyborcza.pl + 4 puste domeny = 24; S3 = 7 + 6 + wolnemedia.net = 14) zgadza się z ramą w data/frame/domains.csv i z aneksem wiersz po wierszu.
- Liczby z notebooka main-results.ipynb (komórki 7, 9, 17, 24, 27, 32, 40, 44, 47, 50, 53, 58) są przeniesione do tekstu i tabel bez błędów. Niezależnie odtworzyłem je z data/clean i data/detect/pangram.csv: próg, FPR na teście, roczne odsetki 4,8/5,1/4,9/7,1/11,0/9,8%, 110 porównań placebo, percentyle δ.
- Przeliczenia w aneksie są arytmetycznie poprawne: nadwyżka = r − b (do zaokrąglenia), π_min ≈ e/(1−b), π_gold ≈ e/(0,26−b). Grupy zgadzają się z regułą (np. expressilustrowany.pl 2,8 pp ≤ δ, globalna.info 19,5% < 20%).
- Liczby wariantów w sec:podsumowanie (zmianynaziemi.pl 8+1, nczas.com 6, elblag.net 6, pap.pl 4 z 9) zgadzają się z fig08 i z wynikami notebooka.
- Poziom przedziałów jest konsekwentnie podpisany w podpisach tabel i rysunków (90% dla serwisów, 95% dla wyniku zbiorczego, przedziały Wilsona na fig04/fig07), a wybór jest uzasadniony w sec:niepewnosc.
- Wszystkie \ref i \cite się rozwiązują. Daty crawli zgadzają się z config/crawls.yaml.

### [C2] neon24.pl: szacunek punktowy podany jako „dolna granica”

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:294 (oraz l. 403 „mocną poszlaką”)`

**Problem.** Tekst: „Nawet przy najwyższym poziomie bazowym spośród porównywanych serwisów (11,2%) dolna granica udziału AI wynosi tam około 38%”. Liczba 37,7% (notebook, komórka 37) to π_min policzone z punktowego r = 44,7%, a nie dolna granica przedziału. Przy dolnym końcu podanego w tym samym zdaniu przedziału r [38,2; 51,3] wychodzi znacznie mniej.

**Dowód.** π_min = (0,447 − 0,112)/(1 − 0,112) = 37,7% (szacunek punktowy). Dla r = 0,382: (0,382 − 0,112)/0,888 = 30,4%. Dodatkowo z danych: neon24.pl ma przed 2023 r. tylko 7 tekstów (wszystkie z 2022), a w 2025 r. 6,7% oznaczonych z 15 tekstów. Wzrost dotyczy praktycznie tylko 2023 r. (47,5%, n = 200).

**Poprawka.** Napisać „szacunek punktowy około 38%, a przy dolnej granicy 95% dla r około 30%”. Albo policzyć π_min symulacją z b = 11,2% i podać 5. percentyl. Dodać, że sygnał pochodzi z jednego roku (2023), a w 2025 r. odsetek wraca poniżej FPR (n = 15).

> **Weryfikator:** Komórka 37 notebooka podaje dla neon24.pl „π_min, gdyby poziom bazowy był najwyższy z naszych (11.2%)” = 37,7%. To wartość z punktowego r = 44,7%: (0,447−0,112)/(1−0,112) = 0,377. Dla dolnego końca podanego przedziału r = 38,2% wychodzi (0,382−0,112)/0,888 = 30,4%. Nazwanie tej liczby „dolną granicą” myli szacunek punktowy z granicą ufności, a cała praca opiera regułę właśnie na dolnych granicach. Fig07 potwierdza resztę: neon24.pl ma n = 7 (2022, 0%), 200 (2023, ok. 47%), 15 (2025, ok. 7%). Sygnał pochodzi więc z jednego roku, a w 2025 r. odsetek jest przy FPR. Zdanie z l. 403 („mocną poszlaką”) też warto złagodzić.

### [C1] Teza „żaden serwis S1 nie jest masowy” ma zastrzeżenie tylko dla o2.pl, a w wariantach masowe są cztery serwisy S1

*Waga:* **minor** (referent: major) · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:36 (abstrakt), preprint.tex:262, preprint.tex:403; fig08_robustness.png`

**Problem.** Abstrakt podaje bez zastrzeżeń: „Żaden z największych serwisów nie spełnia kryterium”. W sec:serwisy jedynym wyjątkiem w wariantach jest o2.pl. Według fig08 i notebooka (komórka 40, tabela FPR; komórka 47) w co najmniej jednym z dziewięciu wariantów masowe są cztery z 11 porównywalnych serwisów S1: money.pl (FPR 20% i „masowo” ≥ 10%), interia.pl (FPR 20%), dziennik.pl („masowo” ≥ 10%) i o2.pl (próg wg długości).

**Dowód.** fig08: wiersze money.pl·S1, interia.pl·S1, dziennik.pl·S1 mają „●” w kolumnach FPR 20% i/lub „masowo” ≥ 10%. Aneks: dolna granica π_gold dla money.pl 11,2%, dla dziennik.pl 12,7% (≥ 10%). sec:fpr (l. 308) wymienia interia.pl i money.pl przy 20%, ale bez informacji, że to S1. Zdanie w l. 262 („Przy progu zależnym od długości … wchodzi co prawda o2.pl, więc ten wniosek zależy od wariantu”) pomija pozostałe przypadki.

**Poprawka.** W l. 262 i 403 napisać wprost, że w analizie głównej żaden serwis S1 nie jest masowy, ale cztery z 11 (money.pl, interia.pl, dziennik.pl, o2.pl) stają się „prawdopodobnie masowe” w co najmniej jednym wariancie (money.pl w dwóch). W abstrakcie dodać „w analizie głównej”.

> **Weryfikator:** Sprawdziłem fig08_robustness.png. money.pl·S1 i interia.pl·S1 mają „●” przy FPR 20%, o2.pl·S1 przy progu wg długości, a dziennik.pl·S1 i money.pl przy „masowo ≥ 10%”. Notebook (komórka 40) to potwierdza: money.pl 29%/22% ●, interia.pl 28%/21% ●. Rdzeń zarzutu się zgadza: abstrakt (l. 36) mówi bez zastrzeżeń „Żaden z największych serwisów nie spełnia kryterium”, a l. 262 jako wyjątek podaje tylko o2.pl. Referent przesadza jednak w dwóch punktach. (1) sec:fpr (l. 308) wymienia interia.pl i money.pl przy FPR 20%. Brakuje tylko informacji, że to S1, i powiązania z tezą o S1. (2) dziennik.pl jest masowy wyłącznie przy definicji ≥ 10%, czyli przy innym kryterium niż 20% z abstraktu, więc nie przeczy zdaniu „nie spełnia kryterium”. L. 262 i 403 mają już „w analizie głównej”. Ta sama logika (kandydat = masowy w analizie głównej) rządzi listą kandydatów w całej pracy. Problem jest więc redakcyjny: brak zastrzeżenia w abstrakcie i niepełna lista wyjątków w l. 262. Podważenia głównej tezy tu nie ma, stąd minor, nie major.
>
> **Wersja skorygowana:** Abstrakt (l. 36) twierdzi bez zastrzeżeń, że żaden serwis S1 nie spełnia kryterium, a l. 262 jako wyjątek wymienia tylko o2.pl (próg wg długości). Według fig08 przy kryterium 20% masowe są w jakimś wariancie trzy z 11 serwisów S1: money.pl i interia.pl przy FPR 20% (wspomniane w l. 308, ale bez oznaczenia S1) oraz o2.pl. Przy łagodniejszej definicji ≥ 10% dochodzą money.pl i dziennik.pl (l. 336 podaje tylko liczbę 12, bez nazw). Poprawka: w abstrakcie dopisać „w analizie głównej”, a w l. 262 wymienić wszystkie trzy przypadki S1 przy kryterium 20% (o2.pl, money.pl, interia.pl) i osobno dwa przy definicji 10%.

### [C3] „Spadek π_gold przy niskim FPR” odwraca kierunek z tabeli

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:310`

**Problem.** Dwa zdania wcześniej tekst mówi, że π_gold MALEJE ze wzrostem FPR (21,5% → 11,3%), czyli przy niskim FPR jest NAJWYŻSZE. Zdanie „Spadek π_gold przy niskim FPR pokazuje …” temu przeczy. Wniosek („π_gold z niskiego FPR jest raczej górną granicą”) pasuje do wzrostu, nie do spadku. Ten sam błąd jest w notebooku, komórka 41.

**Dowód.** tab:fpr: π_gold 21,5% (FPR 1%), 18,1% (5%), 14,3% (10%), 11,3% (20%).

**Poprawka.** Zamienić na „Wzrost π_gold przy niskim FPR pokazuje …” albo „To, że π_gold rośnie, gdy FPR maleje, pokazuje …”.

> **Weryfikator:** Wartości w tab:fpr i w komórce 40 notebooka: π_gold 21,5 → 18,1 → 14,3 → 11,3% przy FPR 1 → 20%. Przy niskim FPR π_gold jest więc najwyższe, a zdanie z l. 310 mówi o „spadku przy niskim FPR”. Wniosek, że to „raczej górna granica”, wynika z tego, że π_gold jest wtedy wysokie, nie niskie. Ten sam błąd jest w komórce 41 notebooka.

### [C4] Różne przedziały π_min dla tych samych serwisów w tab:detektory, aneksie i tekście

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:258, 382–385 vs tabela_serwisow.tex:17,18,21`

**Problem.** Te same wielkości (Pangram, FPR 5%, 90% CI) mają różne granice. Przyczyna: w notebooku (komórka 58) domain_shares jest wołane z tpr_k = 1, tpr_n = 1. Losowanie Beta dla TPR zużywa wtedy inną liczbę liczb losowych i strumień RNG dla serwisów się przesuwa. Tekst w l. 258 bierze wartość z tab:detektory, a nie z aneksu.

**Dowód.** pap.pl: [4,4; 15,5] (tab:detektory) vs [4,2; 15,6] (aneks); goniec.pl: [7,5; 14,2] (tab:detektory, l. 258) vs [7,5; 14,1] (aneks); nczas.com: [5,7; 13,2] vs [5,7; 13,3].

**Poprawka.** Wpisać do tab:detektory kolumnę Pangram wprost z tabeli `domains` (główna analiza). Albo w domain_shares ustawiać osobny seed per serwis (np. rng = default_rng([SEED, hash(domain)])), żeby wynik nie zależał od kolejności losowań.

> **Weryfikator:** Wyjście komórki 30 (główna tabela domains): pap.pl 10,9% [4,2; 15,6], goniec.pl [7,5; 14,1], nczas.com [5,7; 13,3], tak jak w aneksie. Wyjście komórki 58 (tab:detektory): pap.pl [4,4; 15,5], goniec.pl [7,5; 14,2], nczas.com [5,7; 13,2]. Te właśnie liczby trafiły do tab:detektory i do l. 258. Komórka 56 woła domain_shares(f, 1, 1, ...). rng.beta(1.5, 0.5) używa innej ścieżki próbkowania niż Beta(26.5, 74.5), metodą odrzucania przez gammę o kształcie < 1, i zużywa inną liczbę liczb losowych. Strumień dla serwisów się przesuwa, więc mechanizm opisany przez referenta jest wiarygodny. Różnice są kosmetyczne (0,1–0,2 pp), ale te same wielkości mają w pracy dwie wartości.

### [C5] Odwołania do nieistniejących plików i figury bez kodu generującego

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:76, 137, 438; preprint.tex:18 (\graphicspath ../figures/)`

**Problem.** Tekst odsyła do `figures/fig01b_coverage_heatmap`, `figures/fig02b_roc` i `docs/preprint/tables/domains.csv`, ale żaden z tych plików nie istnieje w repozytorium (katalogu docs/preprint nie ma; jedyny domains.csv to rama próby data/frame/domains.csv). Brak też katalogu ../figures. Ponadto żaden plik w repozytorium nie zawiera nazw fig01_coverage … fig09_detectors_yearly. main-results.ipynb rysuje podobne wykresy, ale w innym stylu i bez heatmapy wariantów z fig08, więc figur z preprintu nie da się odtworzyć z repozytorium.

**Dowód.** `find . -name '*fig01b*' -o -name '*fig02b*'` nic nie zwraca; `ls docs/preprint` zwraca No such file or directory; `grep -r fig08 src docs Makefile` znajduje tylko preprint.tex.

**Poprawka.** Dodać skrypt lub sekcję notebooka, która zapisuje fig01–fig09 (wraz z fig01b, fig02b) i eksportuje tabelę aneksu do CSV, a ścieżki w tekście poprawić na istniejące. Usunąć ../figures z \graphicspath.

> **Weryfikator:** `find` nie znajduje fig01b* ani fig02b*, nie ma katalogów docs/preprint ani docs/paper/figures, a jedyny domains.csv to data/frame/domains.csv. W src, docs, config i Makefile nie ma nazw fig0x ani wywołań savefig, a pliki fig01–fig09 weszły do repozytorium tylko w commicie „add current overleaf”. Uwaga: notebook rysuje heatmapę serwis × rok (komórka 8) i krzywe ROC (komórka 14), czyli odpowiedniki fig01b i fig02b, ale ich nie zapisuje. Fig08 (heatmapa wariantów) nie ma w notebooku wcale, jest tylko jako tabela tekstowa (komórki 40 i 47).

### [C6] Niewyjaśnione różnice w liczebnościach i odsetkach za 2023–2025 (14 167 vs 14 814; 5,7% vs 7,1%)

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:67, 195, 215–223`

**Problem.** tab:pokrycie daje 6 178 + 4 855 + 3 781 = 14 814 tekstów z lat 2023–2025, a tab:zbiorczy 14 167. W l. 195 odsetek oznaczonych w 2023 r. „we wszystkich serwisach” wynosi 7,1%, a w tab:zbiorczy 5,7%. Różnica bierze się z 647 tekstów z ośmiu wyłączonych serwisów (neon24 215 + wpolsce24 358 + gazeta 24 + wyborcza 24 + parezja 10 + pikio 16), ale tekst tego nie mówi.

**Dowód.** 14 814 − 14 167 = 647 = suma n 2023–25 z tab:wylaczone. Odsetek 2023 dla 45 serwisów odtworzony z danych: 7,07%.

**Poprawka.** W podpisie tab:zbiorczy dodać „37 porównywanych serwisów (bez 647 tekstów z serwisów z tab. wylaczone)”. W l. 195 pisać „we wszystkich 45 serwisach”.

> **Weryfikator:** 6 178 + 4 855 + 3 781 = 14 814, a tab:zbiorczy podaje 14 167. Różnica 647 to dokładnie suma n 2023–25 z tab:wylaczone (24 + 24 + 215 + 358 + 10 + 16 + 0 + 0). Komórka 22 i l. 195 podają 7,1% dla 2023 r. dla wszystkich 45 serwisów, a tab:zbiorczy 5,7% dla 37 serwisów. Podpis tabeli mówi tylko „z poprawką na skład” i nie wspomina o ograniczeniu do 37 serwisów. Odsetka 7,07% nie mogłem odtworzyć, bo data/processed jest puste, ale liczba z notebooka i z tekstu się zgadza.

### [C7] „Panel 16 serwisów, które mają dane w każdym roku”: definicja się nie zgadza

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:195; fig04_yearly.png (legenda)`

**Problem.** Dane w każdym roku 2020–2025 ma 25 serwisów. 16 to liczba serwisów z co najmniej 30 tekstami w każdym roku (notebook, komórka 22: `(per_year_n >= 30).all(axis=1)`).

**Dowód.** Z danych: serwisów z > 0 tekstów w każdym roku jest 25, z ≥ 30 w każdym roku 16.

**Poprawka.** Pisać „16 serwisów z co najmniej 30 tekstami w każdym roku” w tekście i w legendzie fig04.

> **Weryfikator:** Kod komórki 22: `balanced = per_year_n.index[(per_year_n >= 30).all(axis=1)]`. Etykieta legendy brzmi „stały skład: serwisy z danymi w każdym roku (16)”, a l. 195 mówi „16 serwisów, które mają dane w każdym roku”. Kryterium ≥ 30 nie jest nigdzie opisane. Liczby 25 serwisów z > 0 tekstami w każdym roku nie mogłem zweryfikować (brak data/processed), ale niezgodność definicji z kodem jest pewna.

### [C8] Skład porównań placebo („dla każdego serwisu … 110 porównań”) nie wynika z opisu

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:166, 197`

**Problem.** Tekst sugeruje, że placebo liczone jest dla 37 porównywanych serwisów (37 × 3 = 111). W rzeczywistości obejmuje 40 serwisów z warunkiem ≥ 50 tekstów w danym roku i ≥ 50 w pozostałych dwóch. Są wśród nich serwisy wyłączone z porównania (gazeta.pl, tvp.info, odkrywamyzakryte.com, pikio.pl), a część porównywanych serwisów ma mniej niż 3 porównania (np. pap.pl, 51/17/15).

**Dowód.** placebo_changes w notebooku (komórka 24) iteruje po wszystkich domenach z danymi 2020–22. Moje odtworzenie: 110 porównań z 40 domen, kwantyle 0,90/0,95/0,99 = 2,34/2,92/4,66 pp.

**Poprawka.** Dopisać: „110 porównań z 40 serwisów, w których dany rok i pozostałe dwa mają po co najmniej 50 tekstów (w tym serwisy wyłączone z porównania przed/po)”.

> **Weryfikator:** placebo_changes iteruje po data[data['human']].groupby('domain'), czyli po wszystkich serwisach z tekstami z lat 2020–22, a nie po ELIGIBLE. Do porównań kwalifikują się więc także tvp.info (600), odkrywamyzakryte.com (400), gazeta.pl (583), pikio.pl (270), a możliwe, że i parezja.pl (167). pap.pl (51/17/15) nie wnosi w ogóle żadnego porównania: dla 2020 pozostałe lata mają 32 < 50, dla pozostałych lat sam rok ma < 50. Referent pisze „mniej niż 3”, a w rzeczywistości jest 0. Dokładnej liczby 40 domen nie mogłem odtworzyć bez danych. Kwantyle 2,3/2,9/4,7 pp z l. 338 zgadzają się z jego 2,34/2,92/4,66. Zdanie „Dla każdego serwisu porównujemy…” w l. 166 nie opisuje więc tego, co liczy kod.

### [C9] Opis skoków („przez kilka lat przy FPR”) nie pasuje do neon24.pl i zmianynaziemi.pl

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:266`

**Problem.** Zdanie „Przez kilka lat odsetek oznaczonych leży przy FPR (3–7%), a potem w ciągu jednego roku skacze do 36–76%” obejmuje neon24.pl, który przed 2023 r. ma tylko 7 tekstów z 2022 r. W zmianynaziemi.pl już w 2023 r. odsetek wynosi 10,2% (π_min 7,3% [3,7; 11,6], tab:rok), czyli wyraźnie powyżej FPR jeszcze przed skokiem w 2024 r.

**Dowód.** Z danych: neon24.pl n = {2022: 7, 2023: 200, 2025: 15}, oznaczone {0%, 47,5%, 6,7%}; zmianynaziemi.pl 2023: 10,2% (n = 187).

**Poprawka.** Ograniczyć zdanie do zmianynaziemi.pl, goniec.pl i nczas.com, a neon24.pl opisać osobno (brak lat bazowych, spadek w 2025 przy n = 15). Odnotować, że zmianynaziemi.pl był podwyższony już w 2023 r.

> **Weryfikator:** Fig07: neon24.pl ma przed 2023 r. tylko 7 tekstów z 2022 r. (0%), czyli nie ma „kilku lat przy FPR”, a w 2025 r. spada do ok. 7% (n = 15). zmianynaziemi.pl ma w 2023 r. ok. 10% (π_min 7,3 [3,7; 11,6] w tab:rok; (0,102 − 0,031)/0,969 = 0,073), więc już przed skokiem jest wyraźnie powyżej FPR. Dla goniec.pl i nczas.com opis pasuje.

### [C10] echodnia.eu w warstwie S3 a opis S3 jako serwisów „podejrzanych”

*Waga:* **nit** (referent: minor) · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:56, 411; tabela_serwisow.tex:40; data/frame/domains.csv`

**Problem.** S3 opisano jako serwisy dodane ręcznie, „alternatywne” i konspiracyjne, wybrane celowo jako podejrzane (l. 56, l. 411: „S3 wybrano jako podejrzane”). Tymczasem echodnia.eu, regionalny serwis tego samego wydawcy co gs24.pl czy dzienniklodzki.pl (S2), jest w S3, podobnie jak oko.press i tvp.info. Wpływa to na kolumnę S3 w tab:grupy (np. 2 z 7 serwisów S3 w „braku nadwyżki” to echodnia.eu i oko.press).

**Dowód.** data/frame/domains.csv: echodnia.eu,S3 (bez rangi Tranco), a gs24.pl, dzienniklodzki.pl, pomorska.pl to S2 z rangami.

**Poprawka.** Opisać kryterium doboru S3 precyzyjnie (np. „serwisy spoza rankingu: alternatywne, publiczne i regionalne, dodane ręcznie”) albo przenieść echodnia.eu do S2. Złagodzić „S3 wybrano jako podejrzane”.

> **Weryfikator:** data/frame/domains.csv: echodnia.eu, oko.press, tvp.info i elblag.net (portal regionalny) mają S3 bez rangi Tranco, a pokrewne regionalne serwisy Polska Press są w S2 z rangami. S3 to więc w praktyce „spoza rankingu Tranco”, a nie zbiór wybrany jako podejrzany. L. 56 jest jednak ostrożna („między innymi «alternatywnych» i konspiracyjnych”). Niezgodne jest tylko uogólnienie w l. 411 („S3 wybrano jako podejrzane”) i w notebooku (komórka 60). Przeniesienie echodnia.eu do S2 byłoby zmianą projektu po fakcie. Lepiej doprecyzować kryterium. Do tego zmianynaziemi.pl, który treściowo pasuje do S3, jest w S2 dzięki randze 356 224. Warto to odnotować, bo tab:grupy przypisuje mu warstwę S2.
>
> **Wersja skorygowana:** L. 411 („S3 wybrano jako podejrzane”) uogólnia opis z l. 56, który jest ostrożniejszy. Według data/frame/domains.csv S3 to serwisy spoza rankingu Tranco dodane ręcznie, w tym publiczne i regionalne (tvp.info, oko.press, echodnia.eu, elblag.net). Z kolei zmianynaziemi.pl jest w S2 tylko dzięki randze Tranco. Poprawka: w l. 56 podać kryterium wprost („serwisy spoza rankingu, dodane ręcznie: alternatywne, a także publiczne i regionalne”), a w l. 411 pisać „S3 dobrano częściowo pod kątem podejrzeń”.

### [C11] tab:detektory: „ten sam próg”, ale różne δ dla detektorów

*Waga:* **nit** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:372, 380`

**Problem.** Wiersz „serwisy z nadwyżką > δ” (17/9/2) używa innego δ dla każdego detektora: 2,9 / 3,3 / 3,5 pp (notebook, komórka 58). Tabela tego nie podaje.

**Dowód.** Notebook, komórka 58, wiersz „δ (pp)”: 2.9, 3.3, 3.5.

**Poprawka.** Dodać wiersz „δ (pp)” albo dopisać w podpisie, że δ wyznaczono osobno dla każdego detektora.

> **Weryfikator:** Komórka 58, wiersz „δ (pp)”: 2.9 / 3.3 / 3.5. W tab:detektory (l. 372–386) tego wiersza nie ma, a podpis mówi „Ten sam próg (FPR 5%)”. L. 368 wspomina „δ z placebo”, ale nie mówi, że jest osobne dla każdego detektora.

### [C12] Niepodpisany poziom przedziałów w tekście i niejednolite nazwy grup

*Waga:* **nit** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:142, 256–260; tabela_serwisow.tex (kolumna grupa)`

**Problem.** W l. 142 przedziały TPR [18,4; 35,4] i FPR [3,6; 5,3] (95% Wilsona) nie mają podanego poziomu. W l. 256–260 przedziały dla serwisów (90%) też nie, choć obok jest tab:zbiorczy z 95%. Aneks skraca nazwy grup do „poniżej progu” i „brak nadwyżki”, a „próg” w pracy oznacza też próg detektora (0,472).

**Dowód.** tab:regula: „nadwyżka poniżej progu”, „brak nadwyżki ponad dryf”; aneks: „poniżej progu”, „brak nadwyżki”.

**Poprawka.** Dodać „(95% CI Wilsona)” w l. 142 i „(90% CI)” przy pierwszym przedziale w sec:serwisy. W aneksie używać pełnych nazw z tab:regula albo zdefiniować skróty w podpisie.

> **Weryfikator:** L. 142 podaje [3,6; 5,3] i [18,4; 35,4] bez poziomu. Przeliczyłem: Wilson 95% dla 26/100 daje [18,4; 35,4], więc to 95%. L. 187 deklaruje: „Przedziały dla serwisów podpisujemy «90% CI»”, a l. 256–260 i 294 tego nie robią. Aneks skraca nazwy grup do „poniżej progu” i „brak nadwyżki”.

### [C13] Stale liczby w notebooku i literówka

*Waga:* **nit** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `src/notebooks/main-results.ipynb komórki 6 i 60; preprint.tex:360`

**Problem.** Notebook mówi o „44 polskich serwisach” (komórka 6) i „44 serwisy” (komórka 60), a preprint i wyjście tego samego notebooka (komórka 7) o 45 serwisach z danymi w ramie 50 domen. W l. 360 jest „w wnioskach”.

**Dowód.** Komórka 7: „Serwisy z co najmniej jednym artykułem: 45.”

**Poprawka.** Ujednolicić na 45 (z ramy 50). Poprawić na „we wnioskach”.

> **Weryfikator:** Komórka 6 podaje dwa razy „44”, komórka 60 „44 serwisy”, a komórka 7 wypisuje „Serwisy z co najmniej jednym artykułem: 45.”. W l. 360 jest „w wnioskach”.

### Przeoczenia wskazane przez weryfikatora (C)

- preprint.tex:336 – „Przy łagodniejszej definicji (co najmniej 10% tekstów) serwisów masowych jest 12” bez nazw. Według fig08 (kolumna „masowo” ≥ 10%) są wśród nich dwa serwisy S1 (money.pl, dziennik.pl) oraz globalna.info, dziennik-polityczny.com, lelum.pl, tvmalbork.pl i demagog.org.pl. Tekst nie łączy tego z tezą o S1 z abstraktu. Poprawka: wymienić te serwisy albo przynajmniej odnotować oba serwisy S1.
- preprint.tex:308 vs 262 – sec:fpr wymienia interia.pl i money.pl jako masowe przy FPR 20%, a sec:serwisy (l. 262) podaje o2.pl jako jedyny przypadek, w którym wniosek o S1 „zależy od wariantu”. Dwie sekcje dają różne obrazy odporności tezy o S1. Ujednolicić (zob. C1).
- preprint.tex:166 – zdanie „Dla każdego serwisu porównujemy jeden rok … z dwoma pozostałymi” jest nieprawdziwe dla pap.pl (n = 51/17/15). Przy MIN_N = 50 serwis ten nie wnosi do placebo ani jednego porównania (dla 2020 pozostałe lata mają 32 teksty), a δ jest potem do niego stosowane. Warto dopisać, że serwisy z małym n bazowym nie mają własnej kontroli placebo. To szczególnie ważne dla pap.pl, którego słaby poziom bazowy praca sama wskazuje (l. 260).
- Notebook main-results.ipynb, komórka 41: „Oba szacunki zbliżają się do siebie w okolicy 8–11%”. Preprint (l. 36, 228) podaje 4–18%. Opis tego samego wyniku w notebooku i w pracy jest niespójny, a autorzy traktują notebook jako źródło liczb do pracy.


## D. Rysunki i tabele

**Ocena ogólna.** Rysunki są czytelne na ekranie i zgadzają się z liczbami w tekście. Sprawdziłem wyrywkowo rys. 4, 6 i 8 względem sekcji 4–5. Nie spełniają jednak standardu publikacyjnego. Wszystkie dziewięć to rastry PNG 200 dpi z bezszeryfowym fontem (Helvetica/Arial) na złamanym białym tle #FCFCFB, które na białej stronie widać jako szary prostokąt. Każdy rysunek ma też gazetowy tytuł-tezę, który dubluje albo wyprzedza podpis. Rysunki są pomniejszane do skali 0,52–0,77, więc etykiety osi mają w druku ok. 4,7–7 pt przy tekście 11 pt i podpisach 10 pt (pomiar wysokości cyfr w PNG). Rys. 9 i 8 są praktycznie nieczytelne na wydruku. Dwa rysunki (1 i 2) powtarzają tabele 1 i 3. Dwa (5 i 7) mają wady, które wprowadzają w błąd: zliczenia z prób różnej wielkości na jednej osi oraz linię interpolowaną przez lata bez danych. Rys. 6 pokazuje obciętą wartość π_gold = 100% bez przedziału i bez wyjaśnienia. Żaden plik w repozytorium (we wszystkich gałęziach) nie generuje plików fig01–fig09. Notebook main-results.ipynb nie ma ani jednego `savefig`, a jego wykresy różnią się od tych w artykule, więc przed poprawkami trzeba odtworzyć skrypt rysunków. Tabele poprawnie używają booktabs i mają podpisy nad tabelą, ale liczby nie są wyrównane (brak siunitx). Trzy tabele wychodzą poza margines (tab. 7: 15 pt, tab. 11: 8 pt w poziomie, tab. 5: 3,6 pt). W tabeli aneksu obcięty wynik zmianynaziemi.pl wygląda jak „100,0 [100,0; 100,0]”. Wiele podpisów nie jest samowystarczalnych.

**Mocne strony:**
- Liczby na rysunkach zgadzają się z tekstem i tabelami: rys. 4 (4,8/5,1/4,9% i 4,6/4,4/5,0/4,0/7,1/8,5%), rys. 6 (pap.pl 51 [23; 83], goniec.pl π_min 11 [7,5; 14]), rys. 8 (warianty, w których wypadają nczas.com i elblag.net, zgodnie z sekcją 5.1).
- Polski przecinek dziesiętny jest konsekwentnie stosowany na osiach i w adnotacjach (0,4; 2,9 pp; 0,47), także w tabelach.
- Paleta niebieski #2a78d6 i pomarańczowy #eb6834 przechodzi test rozróżnialności dla daltonistów (walidator dataviz: najgorsza para ΔE 10,3 protan). Rys. 8 koduje kategorie podwójnie, kolorem i kropkami.
- Dobre typy wykresów: wykres pudełkowy dla 37 serwisów (rys. 6), dumbbell AUC Śmigiel/gold (rys. 2), small multiples z liczbą tekstów pod rokiem (rys. 7), macierz wariantów odporności (rys. 8). Niepewność jest pokazywana prawie wszędzie.
- Tabele używają booktabs (\toprule/\midrule/\bottomrule, bez pionowych linii) i mają podpisy nad tabelą. Długa tabela aneksu to longtable z powtarzanym nagłówkiem.

### [G1] Rysunki to rastry PNG z obcym fontem, złamanym białym tłem i drobnym drukiem

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `docs/paper/overleaf/figures/fig01..fig09 *.png; preprint.tex:75,136,146,201,207,250,272,302,393`

**Problem.** Wszystkie rysunki to PNG 200 dpi z Matplotlib 3.11.2 w kroju bezszeryfowym (Helvetica/Arial-podobnym), podczas gdy tekst jest w Latin Modern. Tło ma kolor #FCFCFB zamiast białego, więc w PDF każdy rysunek wygląda jak szary prostokąt (widać to na skompilowanej stronie 2 i 11). Szerokości natywne to 7–12 cali, a wstawiane są na 0,85–1,0 \linewidth (13,6–16 cm). Skala druku wynosi więc 0,52–0,77 i ten sam font źródłowy ma w każdym rysunku inny rozmiar.

**Dowód.** Odczyt pHYs/tEXt z PNG: 200 dpi, „Software: Matplotlib version3.11.2”, piksel tła (252,252,251). Wysokość cyfr na osiach przeliczona na rozmiar w druku (szacunek ±0,5 pt): fig01 ≈7 pt, fig02 ≈7 pt, fig03 ≈6,7 pt, fig04 ≈6,7 pt, fig05 ≈6,1 pt, fig06 ≈5,7 pt, fig07 ≈6,2 pt, fig08 ≈5,2 pt (legenda), fig09 ≈4,7 pt. Tekst główny ma 11 pt, podpisy \small = 10 pt. Tectonic: PDF 1,33 MB.

**Poprawka.** Zapisywać każdy rysunek jako wektorowy PDF w docelowym rozmiarze: `fig.savefig('figures/fig04_yearly.pdf', bbox_inches='tight', pad_inches=0.02)` i wstawiać `\includegraphics{fig04_yearly}` bez skalowania (albo z width=\linewidth przy figsize szerokości dokładnie 6,3 in). Font szeryfowy Latin Modern przez `text.usetex=True` z preambułą lmodern+babel albo `font.serif=['Latin Modern Roman']` (OTF z CTAN), mathtext 'cm'. Rozmiary: etykiety osi 9 pt, opisy podziałek i legenda 8 pt, nigdy poniżej 7 pt. Białe tło (`figure.facecolor='white'`, `savefig.transparent=False`). Pełny blok rcParams podaję w G5.

> **Weryfikator:** Sprawdziłem nagłówki PNG: wszystkie mają 200 dpi i znacznik „Matplotlib version3.11.2”. Szerokości natywne wynoszą od 6,98 in (fig01) do 12,07 in (fig09). \linewidth to 16 cm = 6,3 in (A4, margin=2.5cm). Skale druku: fig01 0,77, fig06 0,64, fig08 0,55, fig09 0,52. Przy font.size 9 z komórki 4 daje to podziałki ok. 4,7 pt na fig09 i ok. 5,8 pt na fig06, czyli szacunki referenta się zgadzają. Na obrazach widać złamane, niebiałe tło i krój bezszeryfowy. Kompilacja tectonic w scratchpadzie dała PDF 1 397 256 B (ok. 1,33 MB).

### [G2] Brak kodu generującego rysunki z artykułu

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `src/notebooks/main-results.ipynb (komórki 8,14,18,19,22,24,31,34,56,57); docs/paper/overleaf/figures`

**Problem.** Notebook nie zawiera żadnego `savefig`. `git grep fig06_forest` we wszystkich gałęziach trafia tylko w preprint.tex. Wykresy w notebooku różnią się od plików w artykule: komórka 14 rysuje krzywe ROC zamiast dumbbell AUC (fig02), komórka 24 histogram z `density=True` zamiast zliczeń (fig05), komórka 31 ma inny tytuł i legendę („π_gold: TPR z przeróbek G2”). Podpisy odsyłają do plików `figures/fig01b_coverage_heatmap` i `figures/fig02b_roc` (preprint.tex:76,137), a aneks do `docs/preprint/tables/domains.csv` (preprint.tex:439). Żaden z nich nie istnieje w repozytorium.

**Dowód.** `grep -E 'savefig|fig0[1-9]_'` po *.py/*.ipynb: brak trafień. `find . -name '*fig01b*'`: brak. `ls docs/preprint`: No such file or directory.

**Poprawka.** Przed poprawkami graficznymi dodać jeden skrypt `src/paper_figures.py` (albo sekcję notebooka) z funkcją na każdy rysunek, wspólnym `style.py` (rcParams z G5) i `savefig` do docs/paper/overleaf/figures/*.pdf. Tabele LaTeX generować tym samym skryptem (`df.to_latex` albo szablon). Dodać brakujące pliki fig01b/fig02b/domains.csv albo usunąć odwołania do nich.

> **Weryfikator:** `grep -rl 'savefig|fig06_forest'` w src, docs i config trafia tylko w preprint.tex. W historii git katalog figures pojawia się wyłącznie w commicie b297877 („add current overleaf”). Komórka 14 rysuje krzywe ROC, komórka 24 histogram z density=True (na fig05 są zliczenia do 27), a komórka 31 ma legendę „π_gold: TPR z przeróbek G2”, podczas gdy na rysunku jest „czułość z przeróbek GPT (26%)”. Doszła jeszcze jedna rozbieżność: komórka 56 rysuje w każdym panelu również serię „stały skład”, a fig09 ma tylko jedną serię na panel. Plików docs/preprint ani fig01b nie ma w repozytorium.

### [F6] Rys. 6: obcięta wartość π_gold = 100% bez przedziału, π_min ściśnięte, druk ok. 5,7 pt

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:248-252, fig06_forest.png`

**Problem.** (1) Dla zmianynaziemi.pl π_gold to kropka dokładnie przy 100 bez odcinka CI. Czytelnik odczyta „100% tekstów z AI”, a w rzeczywistości to obcięcie wartości > 100% (sekcja 3.4). (2) Dolne końce przedziałów obcięte do 0 wyglądają jak prawdziwe granice. (3) Wspólna oś 0–100 sprowadza wszystkie przedziały π_min do pasa 0–15, więc ich nie widać. (4) Różowe pole 20–100% zajmuje 80% obszaru rysunku, a pomarańczowa linia 20% ma ten sam kolor co inne elementy w innych rysunkach. (5) Nazwy są w trzech odcieniach (czarne pogrubione, ciemnoszare, jasnoszare), a podpis objaśnia tylko dwa. Różnica ciemny/jasny szary ginie w druku. (6) Legenda pisze „π_gold” z podkreślnikiem, a tekst π_{gold}. (7) Podpis nie definiuje S1–S3. (8) Skala druku 0,64, opisy podziałek ok. 5,7 pt.

**Dowód.** fig06: punkt π_gold zmianynaziemi.pl przy x = 100, bez linii. Aneks (tabela_serwisow.tex:16) podaje „100,0 [100,0; 100,0]”. Tekst (preprint.tex:258): „\pigold{} przekracza 100%”.

**Poprawka.** Dwa panele obok siebie ze wspólną osią Y (serwisy): lewy π_min, oś 0–40%; prawy π_gold, oś 0–100%. W obu pionowa czarna linia przerywana przy 20%. Bez tła i bez pomarańczu. Przedział 90% jako linia 1 pt, punkt jako kółko 3,5 pt. Grupa serwisu kodowana wypełnieniem markera: pełne czarne = masowo, pełne #0072B2 = nadwyżka poniżej progu, puste szare = brak nadwyżki. Do tego mała kolumna tekstowa „grupa” zamiast pogrubień. Wartości obcięte: strzałka „▶ >100%” przy prawej krawędzi, a przedziały obcięte przy 0 zaznaczyć w podpisie. Etykiety w mathtext: `r'$\pi_{\mathrm{gold}}$'`. figsize (6,3, 8,0) in, opisy 8 pt, placement [p] jest tu w porządku. Podpis uzupełnić: „S1–S3: warstwy próby (sekcja 2.1). Wartości π_gold > 100% obcięte (zmianynaziemi.pl).”

> **Weryfikator:** Na fig06 punkt π_gold dla zmianynaziemi.pl leży przy x = 100 bez odcinka, a w aneksie (tabela_serwisow.tex:16) stoi „100,0 [100,0; 100,0]”. Różowe pole 20–100 i pomarańczowa linia są. Nazwy mają trzy odcienie (pogrubione czarne, ciemnoszare np. globalna.info i demagog.org.pl, jasnoszare), a podpis objaśnia dwa. Legenda pisze „π_gold”. Podpis nie definiuje S1–S3. Punkt (3) jest przesadzony: przedziały π_min są widoczne, tylko ściśnięte w zakresie 0–15.
>
> **Wersja skorygowana:** Bez zmian w punktach (1), (2) i (4)–(8). Punkt (3) brzmi: przedziały π_min są ściśnięte w zakresie 0–15% i trudno je porównywać, ale są widoczne. Uzasadnienia dwóch paneli o różnych skalach to nie zmienia.

### [F7] Rys. 7: linia łączy lata bez danych, punkty z n = 7–17 wyglądają jak pełnoprawne

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:270-274, fig07_timelines.png`

**Problem.** W panelu neon24.pl linia i pasmo CI biegną od 2023 (n = 200) do 2025 (n = 15) ponad rokiem 2024 z n = 0. Wygląda to jak spadek przez 2024 rok, którego nie zmierzono. Punkt 2022 (n = 7) leży na 0% z pasmem 0–35% i optycznie dominuje panel. To samo dotyczy pap.pl 2021–2022 (n = 17, 15) i elblag.net 2023 (n = 12). Wspólna oś 0–100 spłaszcza przypadki pap.pl i elblag.net (10–20%), które tekst opisuje jako „umiarkowanie podwyższone”. Tytuł i stopka wewnątrz rysunku powtarzają podpis. Pasma Wilsona 95% różnią się od tab. 7, gdzie jest 90% CI dla π_min, i nie jest to zaznaczone.

**Dowód.** fig07, panel neon24.pl: liczby pod osią „– – 7 200 – 15”, a linia łączy punkty 2023 i 2025. Stopka „Pod rokiem: liczba tekstów. Pasmo: 95% przedział Wilsona…” powtarza podpis z preprint.tex:273.

**Poprawka.** Rysować tylko punkty i pionowe wąsy CI, bez linii łączącej (`ls='none'`). Ewentualnie łączyć linią tylko kolejne lata z danymi. Wielkość lub wypełnienie markera według n: puste kółko dla n < 30. Osobno zaznaczyć poziom bazowy b (pozioma linia przez lata 2020–22) zamiast linii FPR 5%. Oś Y 0–80, wspólna. Usunąć tytuł i stopkę. figsize (6,3, 3,8) in dla siatki 2×3, tytuły paneli 8 pt („zmianynaziemi.pl (S2), mocne dowody”). Podpis ma objaśniać n < 30 i różnicę między poziomem 95% tu a 90% w tab. 7.

> **Weryfikator:** W panelu neon24.pl linia i pasmo biegną z 2023 (n = 200) do 2025 (n = 15) ponad 2024 (n = „–”). Punkt 2022 (n = 7) leży na 0%. pap.pl ma 2021–22 przy n = 17 i 15, elblag.net ma 2023 przy n = 12. Stopka na rysunku powtarza treść podpisu (preprint.tex:273). Interpolacja przez rok bez danych przeinacza dane, więc severity major jest uzasadnione.

### [F9] Rys. 9: nieczytelny w druku (ok. 4,7 pt), panel 1 powtarza rys. 4, podpis szczątkowy

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:391-395, fig09_detectors_yearly.png`

**Problem.** Natywnie 12 × 4,2 in, wstawiony w skali 0,52. Opisy osi wychodzą ok. 4,7 pt, poniżej minimum 6–7 pt dla druku. Panel Pangram to dokładnie niebieska seria z rys. 4. Lata są podpisane „’20” tutaj i „2020” na rys. 4. Podpis („Ten sam próg (FPR 5%) dla trzech detektorów.”) nie objaśnia pasm, linii przerywanej, tła ani tego, że to surowe odsetki dla wszystkich serwisów, a nie wartości z poprawką na skład z tab. 10 (4,7→8,6%). Nie mówi też, że Binoculars i FDGPT to wersje 4,5B, a walidacja gold była na 1,5B.

**Dowód.** Pomiar: wysokość cyfr 18 px × skala 0,52 → ok. 4,7 pt. Kompilacja (strona 14) potwierdza, że podziałki są ledwo widoczne.

**Poprawka.** Jeden panel, trzy serie na wspólnej osi Y (% oznaczonych): Pangram #0072B2 kółko i linia ciągła, Binoculars #D55E00 kwadrat i przerywana, Fast-DetectGPT #009E73 trójkąt i kropkowana. CI jako wąsy, linia 5% czarna kropkowana, etykiety bezpośrednio przy końcach linii. figsize (6,3, 2,6) in, font 8–9 pt, lata w pełnym zapisie. Alternatywnie zostawić trzy panele przy figsize (6,3, 2,2) in z rcParams z G5. Podpis: „Odsetek oznaczonych tekstów (wszystkie serwisy, bez poprawki na skład) przy progu FPR 5% ustawionym osobno dla każdego detektora. Wąsy: 95% CI Wilsona. Binoculars i Fast-DetectGPT na Bieliku 4,5B (walidowane na gold tylko w wersji 1,5B).”

> **Weryfikator:** Skala 0,52 i podziałki ok. 4,7 pt się potwierdzają. Panel Pangram to ta sama niebieska seria co na fig04 (7,1 / 11,0 / 9,8). Podpis (preprint.tex:394) jest szczątkowy. Tytuły paneli podają jednak „Bielik 4.5B”, więc wersja modelu jest na rysunku. Brakuje tylko informacji, że walidacja gold była na 1,5B. Zarzut czytelności częściowo dubluje G1.
>
> **Wersja skorygowana:** Bez zmian, poza jednym: wersja 4,5B jest już w tytułach paneli. Brakuje informacji, że walidację gold przeprowadzono na 1,5B, a także objaśnienia pasm, linii i tła oraz zaznaczenia, że to surowe odsetki.

### [F1] Rys. 1 powtarza tabelę 1 co do liczby

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:60-77 (tab:pokrycie i fig:pokrycie), fig01_coverage.png`

**Problem.** Wykres słupkowy pokazuje dokładnie 12 liczb z tabeli 1 (artykuły i serwisy na rok), a podpis rysunku jest identyczny z podpisem tabeli. Tytuł wewnątrz („Mniej serwisów w latach 2024–2025: część przestała trafiać do crawla”) zawiera interpretację, której nie ma w podpisie. Szara/niebieska legenda zajmuje 15% wysokości. Oś Y ma format „8000”, a etykiety słupków „7 178”, więc separatory tysięcy są niespójne. Na oś Y „artykuły” nie ma jednostki ani informacji, że to liczba po filtrach.

**Dowód.** Tabela 1: 7 178 / 7 127 / 6 509 / 6 178 / 4 855 / 3 781 oraz 41/43/41/42/35/30. Te same liczby stoją na słupkach i pod osią X fig01. Oba podpisy zaczynają się od „Liczba artykułów i serwisów z danymi w kolejnych latach.”

**Poprawka.** Usunąć rys. 1 i zostawić tabelę 1. W miejsce rysunku dać mapę serwis × rok (dziś „fig01b” poza artykułem), która pokazuje to, czego tabela nie pokazuje: znikanie regionalnych serwisów w 2024–25. Specyfikacja: imshow 45×6 komórek, jednobarwna sekwencyjna skala (np. Blues od #f7fbff do #08306b, vmax=200), wiersze pogrupowane według S1/S2/S3 cienkimi liniami, pionowa linia między 2022 a 2023, liczby w komórkach 6 pt. figsize (6,3, 7,5) in, umieszczenie [p] albo w aneksie.

> **Weryfikator:** Obejrzałem fig01. Liczby na słupkach i pod osią X są identyczne z tab. 1 (preprint.tex:66-67). Oś Y ma format „8000”, a etykiety słupków „7 178”. Tytuł-teza o crawlu jest na rysunku, a w podpisie go nie ma. Podpisy obu obiektów zaczynają się tym samym zdaniem.

### [F2] Rys. 2 dubluje tabelę 3 i gubi przedziały ufności

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:118-138, fig02_instrument_auc.png`

**Problem.** Dumbbell pokazuje te same 10 wartości AUC co kolumny „AUC Śmigiel” i „AUC gold” tabeli 3. Tabela podaje 95% CI dla gold ([0,43; 0,56] itd.), a rysunek nie, choć właśnie przedział pokazuje, że Fast-DetectGPT nie odbiega od 0,5. Podpisane są tylko wartości gold, wartości Śmigiela już nie. Oś zaczyna się od 0,4, co optycznie wydłuża różnice, a dla AUC jest to dopuszczalne tylko z wyraźną linią 0,5. Tytuł-teza powtarza podpis.

**Dowód.** Tabela 3: Binoculars 0,84 / 0,56 [0,50; 0,62], FDGPT bazowy 0,79 / 0,49 [0,43; 0,56]. Na fig02 przy gold są tylko liczby „0,56”, „0,49” itd., bez wąsów.

**Poprawka.** Wybrać jedno z dwóch. (a) Zostawić rysunek i usunąć z tabeli 3 kolumny AUC (w tabeli zostają „przeróbka wyżej” i TPR). (b) Usunąć rysunek. Przy (a): dodać poziome wąsy 95% CI dla gold (linewidth 0,8), usunąć tytuł i etykiety liczbowe, oś X 0,4–1,0 z cienką linią przerywaną przy 0,5. Markery: gold = wypełnione kółko #0072B2, Śmigiel = puste kółko #D55E00 (różny kształt wypełnienia działa też w druku czarno-białym). figsize (6,3, 2,2) in, legenda w jednym wierszu nad osią.

> **Weryfikator:** Na fig02 podpisane są wyłącznie wartości gold i brakuje wąsów CI, mimo że tab:auc (preprint.tex:124-128) podaje przedziały. Linia 0,5 jest już narysowana i opisana „brak sygnału (AUC 0,5)”, więc zarzut o osi od 0,4 jest słaby. Rdzeń zarzutu, czyli dublowanie tabeli i brak CI, jest trafny.

### [F3] Rys. 3: histogram gęstości ze 100 obserwacji w 40 przedziałach to szum, a kluczowa informacja leży w ogonie

*Waga:* **minor** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:144-148, fig03_threshold_hist.png`

**Problem.** G1 i G2 to po 100 tekstów rozłożonych na 40 przedziałów (średnio 2,5 obserwacji na przedział), więc schodkowe kontury są poszarpane. Oś „gęstość” 0–12 nic czytelnikowi nie mówi, a skalę wyznacza szczyt przy 0,05, a nie obszar wokół progu 0,47, o który chodzi w tekście. Pionowa linia progu jest w kolorze #eb6834, a ten ma w skali szarości tę samą jasność (≈137/255) co szare wypełnienie #8a8985, więc w druku czarno-białym linia ginie. Podpis nie podaje wartości progu ani liczebności i nie definiuje G1/G2.

**Dowód.** Luminancja Y': #eb6834 → 137, #8a8985 → 137, #2a78d6 → 107. Adnotacja „powyżej progu: 26% przeróbek, 6% oryginałów” jest jedyną ilościową informacją, a jest wpisana tekstem.

**Poprawka.** Zastąpić histogram krzywymi przeżycia 1−F(s), czyli odsetkiem tekstów z wynikiem > s, dla trzech grup: teksty 2020–22 (czarna linia ciągła, n = 20 814), G1 (szara #7f7f7f, przerywana), G2 (#0072B2, ciągła, z pasmem 95% Wilsona). Próg jako czarna pionowa linia kropkowana. Przecięcia z progiem odczytuje się wtedy wprost (5%, 6%, 26%). Oś Y w procentach 0–100, oś X 0–1. figsize (6,3, 2,6) in. Usunąć tytuł. Podpis: „…Próg 0,472 (FPR 5% na 18 732 tekstach train+dev). G1: 100 ludzkich artykułów z 2020 r.; G2: ich przeróbki przez gpt-4.1-mini.”

> **Weryfikator:** Rdzeń się potwierdza: 100 obserwacji na 40 przedziałów daje poszarpane kontury, a oś „gęstość” 0–12 skaluje się do szczytu przy 0,05. Luminancje 137/137 policzyłem poprawnie, ale szare wypełnienie ma alpha 0,35, więc w druku jest dużo jaśniejsze od linii progu i linia nie ginie. G1 ma ciemnoszary kontur, a nie szare wypełnienie. Wartość progu („próg = 0,47 (FPR 5%)”) i liczebności (n = 20 814, 100, 100) są na samym rysunku, brakuje ich tylko w podpisie.
>
> **Wersja skorygowana:** Histogram gęstości ze 100 obserwacji w 40 przedziałach jest poszarpany, a skalę osi wyznacza szczyt przy 0,05 zamiast obszaru wokół progu 0,47. Zalecana zmiana: krzywe 1−F(s) albo szersze przedziały. Podpis (preprint.tex:147) trzeba uzupełnić o wartość progu, liczebności i definicje G1/G2. Zarzut, że linia progu ginie w czerni i bieli, jest nietrafny, bo wypełnienie ma alpha 0,35.

### [F4] Rys. 4: podpis nie objaśnia serii ani oznaczeń, serie różnią się tylko kolorem

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:199-203, fig04_yearly.png`

**Problem.** Podpis nie mówi, czym są dwie serie (wszystkie 45 serwisów i stały skład 16 serwisów), co oznacza szare tło i linia przerywana, ani że odsetki są surowe, bez poprawki na skład z tab. 5. Serie różnią się tylko barwą (te same kółka). W skali szarości kolory mają jasność 107 i 137, a pasma CI się nakładają. Pasmo Wilsona liczone na artykułach połączonych z wielu serwisów zakłada niezależność tekstów, co zaniża niepewność (sekcja 5.5 sama to przyznaje). Oś Y ma etykietę „oznaczone przez Pangram (%)”, a w rys. 9 ta sama wielkość nazywa się „oznaczone przy FPR 5% (%)”.

**Dowód.** fig04: legenda „wszystkie serwisy (45)” i „stały skład: dane w każdym roku (16)”. Podpis: „Odsetek tekstów oznaczonych przez Pangram (FPR 5%) w kolejnych latach. Pasma: 95% przedział Wilsona.” Tab. 5 dla 2023 podaje 5,7%, a fig04 7,1%, i różnicy nie objaśniono.

**Poprawka.** Seria 1: #0072B2, kółko, linia ciągła. Seria 2: #D55E00, kwadrat, linia przerywana (1,2 pt). Dodać podpisy bezpośrednio na końcu linii zamiast legendy. Linia 5% czarna kropkowana 0,6 pt z etykietą „FPR 5%”. Zamiast tła 2023–25 cienka pionowa linia między 2022 a 2023 z opisem „ChatGPT (XI 2022)”. Usunąć tytuł. figsize (6,3, 2,6) in. Podpis uzupełnić o: definicję obu serii, „surowe odsetki, bez poprawki na skład (por. tab. 5)”, „pasma zakładają niezależność artykułów”. Ujednolicić etykietę osi Y we wszystkich rysunkach: „oznaczone przez Pangram [%]”.

> **Weryfikator:** Na fig04 jest 7,1% dla 2023, a w tab:zbiorczy (preprint.tex:219) 5,7% z poprawką na skład. Podpis nie objaśnia serii, tła ani linii. Etykieta osi Y brzmi „oznaczone przez Pangram (%)”, a na fig09 „oznaczone przy FPR 5% (%)”. Sekcja o pokryciu (preprint.tex:360, 415) rzeczywiście przyznaje założenie niezależności. Jest też drobiazg: uchwyty legendy wyglądają na przerywane, choć serie są rysowane linią ciągłą.

### [F5] Rys. 5: zliczenia z prób 110 i 37 na jednej osi zniekształcają porównanie rozkładów

*Waga:* **minor** (referent: major) · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:205-209, fig05_placebo.png`

**Problem.** Na jednej osi Y („liczba porównań / serwisów”) nałożono zliczenia placebo (n = 110) i zmian po 2022 r. (n = 37). Rozkład „po 2022” jest przez to trzy razy niższy i wizualnie przesunięcie w prawo słabnie, choć tę właśnie tezę rysunek ma pokazać. Jednostki osi Y są pomieszane. Notebook (komórka 24) używa `density=True`, czyli wersja w artykule pochodzi z innego, nieobecnego kodu. Schodkowy histogram 37 wartości z przedziałami 1 pp jest nieczytelny. Tytuł „Bez AI zmiany rzadko przekraczają 3 pp” jest tautologiczny, bo δ zdefiniowano jako 95. percentyl. Podpis nie objaśnia linii δ ani liczebności.

**Dowód.** fig05: najwyższy słupek placebo 27, najwyższy schodek „po 2022” 5. Etykieta osi „liczba porównań / serwisów”. preprint.tex:208: „Zmiany odsetka oznaczonych w serwisach bez AI (placebo, 2020--2022) i po 2022 r.”

**Poprawka.** Narysować dwie dystrybuanty empiryczne (ECDF) na wspólnej osi: placebo jako szara #7f7f7f linia schodkowa (n = 110), po 2022 jako #0072B2 (n = 37), z pionową czarną kropkowaną linią δ = 2,9 pp. Odsetek serwisów powyżej δ (17/37 = 46%) odczytuje się wtedy wprost. Alternatywa: oś pozioma w pp, u góry pasek placebo jako jitter strip, u dołu 37 serwisów jako punkty z podpisem zmianynaziemi.pl. Oś Y „odsetek porównań [%]”. figsize (6,3, 2,4) in, bez tytułu. Podpis: „…Szara: 110 porównań jeden rok vs dwa pozostałe w latach 2020–22; niebieska: 37 serwisów, 2023–25 vs 2020–22. Linia kropkowana: margines dryfu δ (95. percentyl placebo).”

> **Weryfikator:** Potwierdzam, że fig05 pokazuje zliczenia (szczyt placebo 27, „po 2022” ok. 5) z mieszaną etykietą „liczba porównań / serwisów”, a komórka 24 używa density=True. Tytuł jest tautologiczny względem definicji δ. Wartość 17/37 = 46% zgadza się z preprint.tex:197. Rysunek jest jednak diagnostyczny, a tekst podaje liczby wprost (mediany, 17 z 37), więc niższy słupek nie podważa żadnej tezy. Severity major jest zawyżone.
>
> **Wersja skorygowana:** Na fig05 nałożono zliczenia z prób n = 110 i n = 37 na jednej osi z mieszaną etykietą, a tytuł jest tautologiczny wobec definicji δ. Lepiej użyć ECDF albo density, tak jak w notebooku, i uzupełnić podpis o liczebności oraz definicję δ. Severity minor, bo liczby kluczowe dla tezy są podane w tekście (preprint.tex:197).

### [F8] Rys. 8: kategorie „poniżej progu” i „brak nadwyżki” prawie nieodróżnialne, druk ok. 5 pt

*Waga:* **minor** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:300-304, fig08_robustness.png`

**Problem.** Kategoria „brak nadwyżki ponad dryf” ma kolor #F0EFEB na tle #FCFCFB, więc te komórki wyglądają jak puste. Jasnoniebieska „nadwyżka poniżej progu” i ten szary w druku czarno-białym prawie się nie różnią (kropki mają tylko dwie kategorie masowe). Dziewięć kolumn to cztery różne rodziny wariantów (FPR, długość, δ, definicja), ale nic ich nie rozdziela. Nagłówki obrócone o 30° z gwiazdką ★ są trudne do czytania. Skala druku 0,55, legenda ok. 5,2 pt. Podpis nie wymienia wariantów, nie objaśnia ●● / ● i nie mówi, dlaczego pokazano 14 serwisów.

**Dowód.** fig08: np. komórki elblag.net × FPR 20% i lelum.pl × długość prawie zlewają się z tłem. Rozmiar PNG 2288×1626 px przy szerokości 16 cm.

**Poprawka.** Przenieść do tabeli LaTeX (booktabs) z symbolami: ●● = mocne dowody, ● = prawdopodobnie, ○ = poniżej progu, – = brak nadwyżki. Nagłówki dwupoziomowe przez \cmidrule: „FPR: 1 / 5* / 10 / 20 | długość | δ: P90 / P99 | masowo: ≥10 / ≥30”. Tabela będzie ostrzejsza, przeszukiwalna i ok. 40% niższa. Jeśli ma zostać rysunkiem: 4 kategorie w jednej sekwencyjnej palecie, wszystkie wyraźnie różne od tła (#08519c, #4292c6, #c6dbef, #ffffff z obwódką 0,4 pt #bdbdbd), odstęp 4 pt między rodzinami kolumn, nagłówki poziome w 2 liniach, figsize (6,3, 3,2) in, font 8 pt.

> **Weryfikator:** Szare komórki „brak nadwyżki” rzeczywiście zlewają się z tłem i wyglądają jak puste (np. elblag.net × FPR 20%). Twierdzenie, że „poniżej progu” i „brak nadwyżki” są prawie nieodróżnialne, jest przesadzone. W kolorze wyraźnie się różnią (jasnoniebieski i złamana biel), a w skali szarości kontrast jest mały, ale istnieje. Braki w podpisie (preprint.tex:303) potwierdzam: nie ma listy wariantów, objaśnienia ●●/● ani uzasadnienia, dlaczego pokazano 14 serwisów. Skala druku wynosi 0,55.
>
> **Wersja skorygowana:** Kategoria „brak nadwyżki” (bez obwódki, kolor bliski tłu) wygląda jak pusta komórka. Kontrast „poniżej progu” wobec „brak nadwyżki” jest mały w druku czarno-białym. Brakuje rozdzielenia rodzin wariantów i pełnego podpisu. Poprawka bez zmian.

### [G3] Kolor ma w każdym rysunku inne znaczenie, tytuły dublują podpisy

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `fig02–fig09; preprint.tex podpisy rysunków`

**Problem.** Pomarańcz #eb6834 oznacza Śmigiel (rys. 2), próg (rys. 3), stały skład (rys. 4), δ (rys. 5) i strefę „masowo” (rys. 6). Niebieski oznacza gold, G2, wszystkie serwisy, okres po 2022, π_gold i Pangram. Czytelnik nie może przenieść kodu kolorów z rysunku na rysunek. Każdy rysunek ma pogrubiony tytuł-tezę („Tylko Pangram widzi przeróbki GPT…”, „Płasko w latach 2020–2022…”), który w preprincie powinien być w podpisie albo w tekście. Rys. 7 ma dodatkowo stopkę z treścią podpisu. Szerokości 0,85 / 0,9 / 1,0 \linewidth sprawiają, że rysunki mają różne rozmiary fontów.

**Dowód.** Kod notebooka: `BLUE, ORANGE, GRAY, INK = '#2a78d6', '#eb6834', '#8a8985', '#3d3d3a'` używane bez stałej semantyki. rcParams: `axes.titleweight: bold`, `axes.titlesize: 11`.

**Poprawka.** Ustalić słownik semantyczny i trzymać się go we wszystkich rysunkach: Pangram / okres 2023–25 / π_gold = #0072B2; seria porównawcza (stały skład, Śmigiel, Binoculars) = #D55E00; trzecia seria = #009E73; teksty ludzkie, placebo, 2020–22 = szary #7f7f7f; linie odniesienia (próg, δ, 20%, FPR) zawsze czarne kropkowane 0,6 pt, nie kolorowe. Paleta Okabe-Ito jest bezpieczna dla daltonistów, a odmienne markery i style linii zapewniają czytelność w czerni i bieli. Usunąć wszystkie `set_title`/`suptitle` (tytuły paneli tylko jako identyfikatory, 8 pt, normalna grubość). Wszystkie rysunki wstawiać z width=\linewidth i projektować na 6,3 in.

> **Weryfikator:** Komórka 4 definiuje BLUE, ORANGE, GRAY i INK oraz ustawia axes.titleweight bold i axes.titlesize 11. Pomarańcz oznacza Śmigiela (fig02), próg (fig03), stały skład (fig04), δ (fig05) i strefę „masowo” (fig06). Każdy rysunek ma tytuł-tezę, a fig07 ma dodatkowo stopkę. Szerokości wstawienia to 0,85 / 0,9 / 1,0 \linewidth.

### [T1] Tabele: liczby niewyrównane, wyjście poza margines, obcięta wartość jako precyzyjna

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:276-296 (tab:rok), 213-228 (tab:zbiorczy), 312-325 (tab:fpr), 370-388 (tab:detektory), tabela_serwisow.tex:4,16`

**Problem.** (1) Kompilacja zgłasza Overfull \hbox: tab:rok o 15,3 pt (p{3,9cm}×3 + \dom), tab:zbiorczy o 3,6 pt, longtable aneksu o 8,2 pt mimo układu poziomego, akapit z \texttt ścieżki o 111,7 pt (l. 439). (2) Kolumny z przedziałami (\pimin, \pigold, AUC gold) są typu l/c, więc przecinki dziesiętne nie są wyrównane w pionie, a znak % powtarza się w każdej komórce zamiast stać w nagłówku. (3) W aneksie zmianynaziemi.pl ma „100,0 [100,0; 100,0]” w π_gold. Wynik obcięty wygląda jak precyzyjny pomiar z zerową niepewnością. (4) tab:fpr upycha cztery liczby w jednej komórce „1 / 4 / 12 / 20”. (5) tab:detektory ma w wierszu korelacji „1 / 1” dla Pangrama z samym sobą, mieszaną jednostkę wierszy i dopisek „(1,5B)” w komórkach. (6) Pogrubienie całego wiersza 2023–2025 w tab:zbiorczy i całego wiersza 5% w tab:fpr, plus pogrubienia wewnątrz komórek w tab:auc. Wszystkie te tabele mają poprawnie podpis nad tabelą i booktabs.

**Dowód.** Log tectonic: „preprint.tex:295: Overfull \hbox (15.33354pt too wide)”, „preprint.tex:226: Overfull \hbox (3.58885pt too wide)”, „tabela_serwisow.tex:53: Overfull \hbox (8.18298pt too wide) in alignment”, „preprint.tex:439: Overfull \hbox (111.6742pt too wide)”.

**Poprawka.** Dodać `\usepackage{siunitx}` z `\sisetup{output-decimal-marker={,}, group-separator={\,}, group-minimum-digits=4}`. Wartość i przedział w osobnych kolumnach S, np. `S[table-format=2.1] @{\,[}S[table-format=2.1]@{;\,}S[table-format=2.1]@{]}`, a „[%]” tylko w nagłówku. tab:rok: kolumny l zamiast p{3,9cm} albo `tabularx` z \linewidth, n w osobnej kolumnie. tab:fpr: rozbić „grupy” na 4 kolumny S z \cmidrule „liczba serwisów w grupach”. tab:detektory: zamiast „1 / 1” dać „—”, a „(1,5B)” przenieść do przypisu tabeli (`threeparttable`). Aneks: π_gold zmianynaziemi.pl = „>100\tnote{a}” bez przedziału, nagłówki w 2 liniach (`\makecell`), co pozwoli zmieścić tabelę w pionie przy \scriptsize. Wyróżnienie analizy głównej robić \rowcolor{gray!10} albo gwiazdką zamiast pogrubienia całego wiersza. Ścieżki \texttt łamać przez `\url{}` albo `\path{}`.

> **Weryfikator:** Skompilowałem dokument tectonic w scratchpadzie. Log zawiera Overfull 15,33 pt (l. 294–295), 3,59 pt (l. 216–226), 8,18 pt w longtable aneksu i 110,7 pt (l. 438–439; referent podał 111,7, różnica nieistotna). Do tego dochodzi pominięte 28,4 pt przy l. 403–404 (wnioski). Kolumny tab:rok to p{3.9cm}×3, tab:fpr ma „1 / 4 / 12 / 20”, tab:detektory ma „1 / 1” i „(1,5B)” w komórkach, a aneks ma „100,0 [100,0; 100,0]”. Wszystko się zgadza.

### [C1] Podpisy rysunków nie są samowystarczalne

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:76,137,147,202,208,251,273,303,394`

**Problem.** Podpisy nie definiują skrótów ani oznaczeń, które pojawiają się na rysunkach: S1–S3 (rys. 6, 7, 8), G1/G2 (rys. 3), δ i liczebności (rys. 5), serie i tło (rys. 4, 9), symbole ●●/● i listę wariantów (rys. 8). Nie mówią też, czy odsetki są z poprawką na skład. Rys. 1 i tab. 1 mają identyczne podpisy. Rys. 9 i tab. 10 też mają praktycznie ten sam podpis („Ten sam próg (FPR 5%) dla trzech detektorów.”). Rys. 2 i 3 odsyłają do plików, których nie ma w repozytorium.

**Dowód.** preprint.tex:394: „Ten sam próg (FPR 5\%) dla trzech detektorów.” preprint.tex:303: „Grupa każdego serwisu, który choć raz był „masowy”, w dziewięciu wariantach analizy (główna analiza: FPR 5%).”

**Poprawka.** Każdy podpis według schematu: (1) co jest na osiach i jaka jednostka, (2) co oznacza każdy kolor, marker i linia, (3) poziom i typ przedziału, (4) próba (n, ile serwisów), (5) definicje skrótów albo odsyłacz do sekcji. Konkretne uzupełnienia dla rys. 3, 4, 5, 6, 7 i 9 są w F3–F9. Dla rys. 8 dopisać: „Kolumny: próg FPR 1/5/10/20%, próg zależny od długości, δ z 90. i 99. percentyla placebo, definicja „masowo” ≥10% i ≥30%. ●● mocne dowody, ● prawdopodobnie. Pokazano 14 serwisów, które w co najmniej jednym wariancie były masowe.”

> **Weryfikator:** Sprawdziłem wszystkie podpisy (preprint.tex:76, 137, 147, 202, 208, 251, 273, 303, 394). Żaden nie definiuje S1–S3, G1/G2, δ, ●●/● ani nie mówi, czy odsetki są z poprawką na skład. Podpisy fig01 i tab:pokrycie są identyczne. Podpis tab:detektory to podpis fig09 rozszerzony o jedno zdanie o poziomach przedziałów. Odsyłacze do fig01b i fig02b prowadzą do plików, których nie ma.

### [G5] Wspólny styl: jeden blok rcParams dla wszystkich rysunków

*Waga:* **nit** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `src/notebooks/main-results.ipynb komórka 4 (blok plt.rcParams.update)`

**Problem.** Obecne rcParams (`figure.figsize (9,4)`, `font.size 9`, `axes.titleweight bold`, `axes.grid True`, brak savefig) projektują rysunki na ekran 9-calowy, a nie na kolumnę 16 cm. Różne figsize (6,5–12 in) dają różne rozmiary fontu w druku.

**Dowód.** Komórka 4: `plt.rcParams.update({"figure.dpi": 110, "figure.figsize": (9, 4), ... "font.size": 9})`, figsize w kolejnych komórkach od (6.5, …) do (12, 4.3).

**Poprawka.** Proponowany blok (wspólny moduł style.py):
import matplotlib as mpl
mpl.rcParams.update({
 'text.usetex': True,
 'text.latex.preamble': r'\usepackage[T1]{fontenc}\usepackage{lmodern}\usepackage[polish]{babel}\usepackage{amsmath}\usepackage{icomma}',
 'font.family': 'serif', 'font.size': 9,
 'axes.labelsize': 9, 'axes.titlesize': 9, 'axes.titleweight': 'normal',
 'xtick.labelsize': 8, 'ytick.labelsize': 8, 'legend.fontsize': 8,
 'figure.figsize': (6.3, 2.6),  # 16 cm szerokości
 'figure.facecolor': 'white', 'axes.facecolor': 'white',
 'savefig.format': 'pdf', 'savefig.bbox': 'tight', 'savefig.pad_inches': 0.02,
 'pdf.fonttype': 42,
 'axes.spines.top': False, 'axes.spines.right': False,
 'axes.linewidth': 0.6, 'axes.edgecolor': '#333333', 'axes.labelcolor': 'black',
 'xtick.color': 'black', 'ytick.color': 'black',
 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
 'xtick.major.size': 3, 'ytick.major.size': 3,
 'axes.grid': False,
 'lines.linewidth': 1.2, 'lines.markersize': 4, 'errorbar.capsize': 0,
 'legend.frameon': False, 'legend.handlelength': 1.6,
 'axes.prop_cycle': mpl.cycler(color=['#0072B2', '#D55E00', '#009E73', '#7f7f7f'], marker=['o', 's', '^', 'D'], linestyle=['-', '--', ':', '-.']),
})
Bez LaTeX-a w systemie: 'text.usetex': False, 'font.serif': ['Latin Modern Roman'], 'mathtext.fontset': 'cm' oraz formatter z przecinkiem i spacją tysięcy: `ax.yaxis.set_major_formatter(mpl.ticker.FuncFormatter(lambda v, _: f'{v:,.0f}'.replace(',', ' ')))` (dla ułamków `.replace('.', ',')`). Wysokości: pojedynczy wykres 2,4–2,8 in, trzy panele 2,2 in, siatka 2×3 3,8 in, wykres pudełkowy 37 serwisów 8 in. W LaTeX-u zawsze `\includegraphics[width=\linewidth]{nazwa}` (PDF, bez rozszerzenia).

> **Weryfikator:** Opis obecnych rcParams w komórce 4 się zgadza. Proponowany blok ma domyślnie 'text.usetex': True, a na tej maszynie nie ma pdflatex ani latexmk, jest tylko tectonic, którego matplotlib nie używa. Blok w tej postaci po prostu się wywali. Przy usetex=True ustawienie 'pdf.fonttype': 42 nic nie daje. Domyślną opcją powinien być wariant bez LaTeX-a.
>
> **Wersja skorygowana:** Wspólny moduł stylu jest zasadny. Domyślnie należy jednak ustawić 'text.usetex': False, 'font.family': 'serif', 'font.serif': ['Latin Modern Roman'] (font OTF zainstalowany w systemie), 'mathtext.fontset': 'cm' i 'pdf.fonttype': 42. usetex=True ma sens tylko tam, gdzie jest pdflatex lub latex; na maszynie autorów jest wyłącznie tectonic. Reszta bloku bez zmian.

### Przeoczenia wskazane przez weryfikatora (D)

- preprint.tex:403-404 (pierwszy akapit wniosków): tectonic zgłasza Overfull \hbox (28.4299pt too wide). Ten wpis nie trafił do T1. Akapit wystaje poza margines w najczęściej czytanej części tekstu. Poprawka: przeformułować zdanie albo wstawić \allowbreak lub \- przy długich nazwach domen (\dom{...}).
- fig04_yearly.png: uchwyty legendy pokazują linię przerywaną z kropką („--●--”), a obie serie są rysowane linią ciągłą. To artefakt uchwytu errorbar w legendzie. Czytelnik szuka serii przerywanej, której nie ma. Poprawka: własne uchwyty Line2D albo etykiety bezpośrednio przy końcach linii.
- fig06_forest.png i preprint.tex:250: rysunek ma height=0.86\textheight i placement [t], co w praktyce wymusza osobną stronę i może odsunąć rysunek daleko od odwołania. Poprawka: jawnie dać [p], tak jak proponuje F6.
- fig07_timelines.png, panele pap.pl i neon24.pl: punkty 2022 (n = 15 i n = 7) leżą dokładnie na 0% z pasmem Wilsona do ok. 20–35%. Wraz z liniami łączącymi tworzy to wizualny dołek przed skokiem, który wyolbrzymia „skok” w 2023 r. Uzupełnia to F7: punkty z n < 30 trzeba wyraźnie odróżnić (puste markery) albo pominąć.


## E. Język, struktura, literatura, LaTeX

**Ocena ogólna.** Tekst jest zwięzły, rzeczowy i w większości precyzyjny. Wyniki liczbowe w tabelach są w dużej mierze spójne ze sobą, a float-y kompilują się blisko odwołań (tectonic/XeTeX, 17 stron, brak niezdefiniowanych odwołań). Największe braki dotyczą jednak warstwy „wydawniczej” preprintu. Nie ma przeglądu literatury ani jawnej listy wkładów, nie ma też osobnych wniosków. Hipoteza H2 nie zostaje nigdzie formalnie rozstrzygnięta. Brakuje oświadczeń o danych i kodzie, o licencji modelu EditLens oraz noty etycznej przy wskazywaniu z nazwy serwisów (w tym PAP) jako publikujących treści AI. Odwołania „do repozytorium” prowadzą do plików, które nie istnieją, a sam adres repozytorium nie pada w tekście. Bibliografia pomija prace najbliższe metodycznie: Adjusted Classify-and-Count, Liang i in. 2024 (ICML), Hanley i Durumeric 2024 o tekstach syntetycznych w serwisach newsowych, przedziały Wilsona i Jeffreysa, DetectGPT oraz raport techniczny Pangrama. Kilka zdań ma błędy merytoryczne w samym sformułowaniu: „spadek” \pigold{} przy niskim FPR w miejsce wzrostu oraz „dolna granica ~38%” dla neon24.pl, która jest szacunkiem punktowym. Są też drobne rozbieżności liczb między tabelami, niespójne półpauzy i kolokwializmy do wygładzenia.

**Mocne strony:**
- Klarowna, krótka proza z jasno wyłożonym rozumowaniem (np. uzasadnienie wyboru FPR 5% i układu próg globalny + poziom bazowy serwisu w preprint.tex:150-152).
- Ostrożny język wniosków: rozróżnienie „mocne dowody”/„prawdopodobnie”/„kandydaci”, jawna lista ograniczeń (preprint.tex:405-416) i deklaracja unikania sformułowania „serwis używa AI”.
- Polskie cudzysłowy „…” są użyte konsekwentnie (brak ASCII), liczby tysięczne z \, (35\,628), przecinek dziesiętny konsekwentny w tekście i tabelach.
- Liczby grup w tab. 6 zgadzają się z tabelą aneksu (11/19/7 serwisów S1/S2/S3), a warianty z sekcji 5.6 zgadzają się z rys. 8.
- Dokument kompiluje się bez niezdefiniowanych odwołań i cytowań. Wszystkie float-y lądują na stronie odwołania lub następnej (z pliku .aux: np. tab:auc i fig:auc na s. 4, fig:las na s. 9).
- Sekcja 6 stanowi wartościowy, rzadko spotykany wniosek metodologiczny: walidacja na zbiorze z innej dziedziny wybrałaby zły detektor (preprint.tex:399).

### [W1] Brak przeglądu literatury i pominięte prace najbliższe metodycznie

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:46 (jedyny akapit o pracach pokrewnych), preprint.tex:420-433 (bibliografia)`

**Problem.** Kontekst literaturowy to dwa zdania (Russell i in., Liang i in.). Nie ma sekcji „Prace pokrewne”. Brakuje prac, o które recenzent zapyta wprost. (a) Estymator (r−b)/(TPR−b) to w uczeniu maszynowym znane „Adjusted Classify and Count” (Forman 2005/2008; przegląd: González i in. 2017, ACM CSUR); tekst cytuje tylko epidemiologię (Rogan–Gladen). (b) Liang i in. 2024, „Monitoring AI-Modified Content at Scale” (ICML 2024): rozkładowa estymacja udziału LLM bez klasyfikacji pojedynczych tekstów, czyli bezpośrednia alternatywa metody. Do tego Liang i in. 2024, „Mapping the Increasing Use of LLMs in Scientific Papers” (COLM). (c) Hanley i Durumeric 2024, „Machine-Made Media” (ICWSM): odsetek artykułów syntetycznych w serwisach mainstreamowych i dezinformacyjnych przed i po ChatGPT, czyli najbliższy odpowiednik całego badania. (d) Raporty NewsGuard o „UAINS” (AI content farms). (e) DetectGPT (Mitchell i in. 2023), na którym bazuje Fast-DetectGPT. (f) Raport techniczny Pangrama (Emi i Spero 2024, arXiv:2402.14873). (g) Przedział Wilsona (Wilson 1927) i Jeffreysa (Brown, Cai, DasGupta 2001). Obu przedziałów używacie (podpisy rys. 4 i 7, preprint.tex:170) bez cytowania.

**Dowód.** preprint.tex:46: jedynie „Russell i in.~\cite{russell2025} … Liang i in.~\cite{liang2025} …”. Bibliografia ma 12 pozycji, żadna nie dotyczy kwantyfikacji ani interwałów. Notebook main-results (kod, l. 85-90) nazywa losowanie Beta(k+1/2, n−k+1/2) „wersją bootstrapu”, a to posterior Jeffreysa.

**Poprawka.** Dodać sekcję 2 „Prace pokrewne” (3-4 akapity): (1) pomiar udziału AI w korpusach (Liang 2024/2025, Russell 2025, Hanley i Durumeric 2024, NewsGuard); (2) kwantyfikacja/ACC i Rogan–Gladen jako ten sam estymator; (3) detektory i ich zawodność międzydziedzinowa (DetectGPT, Fast-DetectGPT, Binoculars, RAID, Pangram); (4) polskie zasoby (Śmigiel, Bielik). Zakończyć jednym zdaniem, czym różni się to badanie: wynik per serwis, język polski, brak etykiet, walidacja na przeróbkach. W preprint.tex:170 nazwać rozkład „posteriorem Jeffreysa” i zacytować Brown i in. (2001). W podpisach rys. 4 i 7 zacytować Wilsona.

> **Weryfikator:** Sprawdziłem preprint.tex:46: kontekst literaturowy to faktycznie dwa zdania (Russell, Liang). Nie ma sekcji „Prace pokrewne”. Bibliografia (l. 420-433) ma 12 pozycji i żadna nie dotyczy kwantyfikacji, ACC ani przedziałów. Przedział Wilsona jest nazwany w podpisach rys. 4 i 7 (l. 202, 273), ale bez cytowania. W notebooku main-results.ipynb losowanie Beta(k + 1/2, n - k + 1/2) jest opisane jako odmiana „bootstrapu” (grep potwierdza), a to jest posterior Jeffreysa. Wskazane prace istnieją i są metodycznie najbliższe (Liang i in. ICML 2024, Hanley i Durumeric ICWSM 2024). Jak na preprint metodyczny brak ACC/Forman to luka, o którą recenzent zapyta.

### [W3] Brak oświadczeń wymaganych w preprincie: dane i kod, licencje, etyka wskazywania serwisów, wkład autorów, użycie AI

*Waga:* **major** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `koniec dokumentu (przed bibliografią); preprint.tex:108, 256-262, 403`

**Problem.** Preprint z imiennym wskazaniem serwisów jako publikujących masowo teksty AI (w tym \dom{pap.pl}, czyli Polskiej Agencji Prasowej, jako „kandydata” na podstawie 83 tekstów bazowych) nie ma noty etyczno-prawnej. Brakuje: (a) adresu repozytorium i oświadczenia o dostępności danych i kodu; (b) informacji o licencji EditLens (adapter CC BY-NC-SA 4.0, wymagana akceptacja licencji Llama 3.2; zob. docs/detektory.md) i o warunkach Common Crawl; (c) informacji, czy serwisy proszono o komentarz; (d) wkładu autorów, finansowania, konfliktu interesów; (e) ujawnienia użycia LLM (GPT-4.1-mini do G2 jest opisany, ale nie wiadomo, czy AI wspierało pisanie lub kod). Bez (c) zdania typu „co najmniej 29,8% tekstów musi pochodzić z AI” (l. 256) są ryzykowne prawnie.

**Dowód.** Brak jakiejkolwiek sekcji poza „Dyskusja i ograniczenia” → bibliografia. docs/detektory.md: „Licencja adaptera to CC BY-NC-SA 4.0, tylko do użytku niekomercyjnego”. Słowo „GitHub” ani URL repozytorium nie występują w preprint.tex.

**Poprawka.** Przed bibliografią dodać nienumerowane sekcje: „Dostępność danych i kodu” (URL repozytorium z tagiem lub commitem; które dane są publiczne: wyniki per tekst, listy URL; których nie publikujecie: pełne teksty, ze względu na prawa autorskie), „Licencje” (EditLens: HF id pangram/editlens_Llama-3.2-3B, CC BY-NC-SA 4.0), „Uwagi etyczne” (wynik dotyczy nadwyżki tekstów ocenianych przez detektor jako AI-podobne, nie dowodu autorstwa; ewentualny kontakt z redakcjami; brak danych osobowych), „Wkład autorów”, „Finansowanie”, „Użycie narzędzi AI”.

> **Weryfikator:** Potwierdzam brak: oświadczenia o dostępności danych i kodu, URL repozytorium (grep: brak „github” i brak URL poza commoncrawl.org), informacji o licencji EditLens (docs/detektory.md:56: CC BY-NC-SA 4.0 i licencja Llama), noty etycznej przy wskazywaniu z nazwy serwisów, w tym pap.pl. Nie zgadzam się ze sformułowaniem „wymaganych w preprincie”: arXiv nie wymaga sekcji o wkładzie autorów, finansowaniu ani o użyciu AI. Użycie GPT-4.1-mini jest opisane jako część metody (l. 110). Rdzeniem problemu jest nota etyczna i dostępność danych, nie formalne wymogi.
>
> **Wersja skorygowana:** Brak noty o dostępności danych i kodu (URL i commit), licencjach (EditLens: CC BY-NC-SA 4.0 i licencja Llama 3.2; warunki Common Crawl) oraz krótkiej noty etycznej przy imiennym wskazywaniu serwisów (w tym \dom{pap.pl} na podstawie 83 tekstów bazowych). Nota powinna mówić, że wynik dotyczy nadwyżki tekstów ocenianych przez detektor jako AI-podobne, a nie dowodu autorstwa. Sekcje „wkład autorów”, „finansowanie” i „użycie AI w pisaniu” są opcjonalne w preprincie arXiv, warto je dodać, ale nie są wymagane.

### [W4] Odwołania do nieistniejących plików i brak adresu repozytorium

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:76, 137, 429, 438`

**Problem.** Tekst cztery razy odsyła czytelnika „do repozytorium”, ale nie podaje jego adresu. Trzy z czterech ścieżek nie istnieją w repo. Notebook src/notebooks/main-results.ipynb nie zapisuje rysunków do plików (brak savefig), więc figures/fig0*.png w docs/paper/overleaf nie mają ścieżki reprodukcji z kodu.

**Dowód.** find w repo: brak plików fig01b*, fig02b* i docs/preprint/tables/domains.csv. Istnieją tylko config/crawls.yaml i data/frame/domains.csv (rama próby, nie tabela wyników). Katalog docs/preprint nie istnieje (jest docs/paper). Ścieżka w l. 438 daje też overfull hbox 110,7 pt.

**Poprawka.** Dodać URL repozytorium (np. w przypisie do tytułu i w sekcji „Dostępność danych”). Wygenerować i zacommitować fig01b_coverage_heatmap, fig02b_roc i tabelę domains.csv (eksport z main-results.ipynb) albo usunąć te odwołania. Poprawić ścieżkę w l. 438 na rzeczywistą. Dodać do notebooka fig.savefig(...) dla fig01-fig09, żeby rysunki w preprincie były reprodukowalne.

> **Weryfikator:** find w repo: nie ma fig01b*, fig02b* ani docs/preprint/tables/domains.csv. Katalog docs/preprint nie istnieje, jest docs/paper. Istnieją tylko config/crawls.yaml i data/frame/domains.csv (rama próby). grep -c savefig w src/notebooks/main-results.ipynb daje 0. Nazwy fig06_forest i fig02_instrument występują w repo wyłącznie w preprint.tex, więc żaden kod w repo nie zapisuje rysunków z preprintu. Tectonic potwierdza overfull 110,7 pt w l. 438-439.

### [W7] Sformułowania sugerujące pewność autorstwa AI, sprzeczne z deklarowaną ostrożnością

*Waga:* **major** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:256, 403 (vs 162 i 410)`

**Problem.** W l. 410 autorzy deklarują, że unikają stwierdzenia, że serwis „używa AI”. Mimo to l. 256 mówi, że „co najmniej 29,8% tekstów musi pochodzić z AI nawet przy idealnym detektorze”, a l. 403 łączy w jednym zdaniu „treści, które detektor ocenia jako generowane przez AI” z „pochodzi z AI niezależnie od założeń o czułości”. To dolna granica jednostronnego 95% przedziału, warunkowa względem założenia o braku zmiany poziomu bazowego (l. 162: „o ile poziom bazowy się nie zmienił”). Przy wskazywaniu konkretnych serwisów z nazwy to także kwestia prawna.

**Dowód.** l. 256: „czyli co najmniej 29,8\% tekstów musi pochodzić z AI”; l. 403: „bo co najmniej 29,8\% jego tekstów z lat 2023--2025 pochodzi z AI niezależnie od założeń o czułości”.

**Poprawka.** l. 256: „Jeśli poziom bazowy serwisu się nie zmienił, z 95-procentową pewnością co najmniej 29,8% jego tekstów z lat 2023–2025 to teksty AI, niezależnie od czułości detektora.” l. 403: „…jeden serwis (\dom{zmianynaziemi.pl}, S2) ma nadwyżkę tekstów ocenianych przez detektor jako generowane przez AI, odpowiadającą co najmniej 29,8% jego artykułów z lat 2023–2025 (jednostronna granica 95%, przy założeniu stałego poziomu bazowego)…”

> **Weryfikator:** Cytaty są w tekście. l. 256: „co najmniej 29,8\% tekstów musi pochodzić z AI nawet przy idealnym detektorze”. l. 403: „pochodzi z AI niezależnie od założeń o czułości”. To przeczy deklaracji z l. 410 („unikamy sformułowania, że serwis »używa AI«”) i warunkowi z l. 162 („o ile poziom bazowy się nie zmienił”). Jest to też jednostronna granica 95%, a nie pewność. Serwis jest wskazany z nazwy, więc severity major jest zasadne.

### [W2] Brak jawnych wkładów, brak rozstrzygnięcia H2 i brak sekcji wniosków

*Waga:* **minor** (referent: major) · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:50, 228, 401-416`

**Problem.** Wprowadzenie stawia H1 i H2 (główną), ale H2 nie pada już nigdzie w tekście. Rozstrzygnięta jest tylko H1 („H1 się potwierdza”, l. 228). Odpowiedź na H2 trzeba wyczytać z Dyskusji. Brakuje listy wkładów, a „Dyskusja i ograniczenia” łączy podsumowanie, interpretację i ograniczenia. Dokument kończy się listą ograniczeń bez akapitu zamykającego (wnioski, rekomendacje, dalsze prace). Sekcja 6 (porównanie z Bielikiem) stoi po analizach odporności, a w istocie jest częścią walidacji instrumentu (3.2) albo kolejnym wariantem odporności.

**Dowód.** grep „H2” zwraca tylko preprint.tex:50. Sekcja 7 kończy się na enumerate (l. 416), po której od razu następuje bibliografia.

**Poprawka.** (1) Na końcu Wprowadzenia dodać akapit „Nasz wkład:” z 3-4 punktami: metoda bez etykiet per serwis z marginesem dryfu z placebo; zbiór gold G1/G2 dla polskich newsów; pokazanie, że walidacja na Śmigielu wybiera zły detektor; wynik dla 37 serwisów. (2) W 4.2 lub 4.3 dodać zdanie: „H2 się potwierdza: co najmniej jeden serwis (\dom{zmianynaziemi.pl}) spełnia definicję we wszystkich wariantach z definicją 20%”. (3) Podzielić sekcję 7 na „7 Dyskusja”, „8 Ograniczenia” i krótkie „9 Wnioski”. (4) Przenieść sekcję 6 do 5.x („Inny detektor”) albo skrócić ją i włączyć do 3.2.

> **Weryfikator:** grep potwierdza, że H2 występuje tylko w l. 50, a jawnie rozstrzygnięto tylko H1 (l. 228). Odpowiedź na H2 da się jednak jednoznacznie wyczytać z 4.2 i 7 (l. 256, 403), więc czytelnik nie traci informacji. To kwestia redakcji, nie braku wyniku. Lista wkładów i podział Dyskusji na sekcje to preferencja stylistyczna, nie wymóg. Przeniesienie sekcji 6 jest dyskusyjne, bo sekcja 6 stosuje procedurę do danych serwisów, a nie tylko waliduje instrument.
>
> **Wersja skorygowana:** Hipoteza H2 (główna) jest postawiona w l. 50, ale nigdzie nie pada jawne zdanie, że się potwierdza. H1 ma takie zdanie (l. 228). Dodać w 4.2 lub na początku sekcji 7: „H2 się potwierdza: \dom{zmianynaziemi.pl} spełnia definicję we wszystkich wariantach, \dom{goniec.pl} w wariancie »prawdopodobnie«”. Opcjonalnie: krótki akapit wkładów na końcu Wprowadzenia i 2-3 zdania wniosków po liście ograniczeń, żeby dokument nie kończył się na enumerate.

### [W5] Odwrócony kierunek zmiany w zdaniu o \pigold{} przy niskim FPR

*Waga:* **minor** (referent: major) · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:310`

**Problem.** Zdanie „Spadek \pigold{} przy niskim FPR pokazuje, że…” przeczy tabeli i poprzedniemu zdaniu. \pigold{} jest najwyższe przy najniższym FPR, czyli przy niskim FPR rośnie, a nie spada. Wniosek („raczej górną granicą”) pasuje do wzrostu, więc błąd leży w słowie i dezorientuje czytelnika w kluczowej interpretacji.

**Dowód.** tab:fpr (l. 319-322): \pigold{} 21,5% przy FPR 1% → 18,1% → 14,3% → 11,3% przy 20%. Ta sama linia 310 wyżej: „Wraz z nim \pimin{} rośnie …, a \pigold{} maleje”.

**Poprawka.** Zamienić na: „Wzrost \pigold{} przy niskim FPR pokazuje, że przy surowym progu czułość zmierzona na przeróbkach zaniża czułość na tekstach z serwisów, więc \pigold{} przy niskim FPR należy traktować raczej jako górną granicę.”

> **Weryfikator:** Tab. fpr (l. 319-322) potwierdza: \pigold{} wynosi 21,5% przy FPR 1% i 11,3% przy FPR 20%. Przy niskim FPR \pigold{} jest więc najwyższe, a słowo „Spadek” w l. 310 jest błędne. Wniosek zdania („raczej górną granicą”) odpowiada jednak wzrostowi, a dane z tabeli i zdanie wcześniej są poprawne. To błąd jednego słowa, który czytelnik może sam skorygować, nie błąd merytoryczny. Severity: minor.
>
> **Wersja skorygowana:** W l. 310 słowo „Spadek” zamienić na „Wzrost”, bo \pigold{} przy FPR 1% (21,5%) jest najwyższe w tab. fpr. Reszta zdania jest zgodna z danymi.

### [W6] „Dolna granica ~38%” dla neon24.pl to w rzeczywistości szacunek punktowy

*Waga:* **minor** (referent: major) · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:294`

**Problem.** Tekst nazywa „dolną granicą udziału AI” wartość policzoną z punktowego r = 44,7%. Dolną granicę daje dolny koniec przedziału r (38,2%), a wtedy wynik wynosi ok. 30%. Nazwanie szacunku punktowego dolną granicą zawyża siłę najmocniejszej poszlaki spoza porównania.

**Dowód.** \pimin{} = (r−b)/(1−b) przy b = 11,2%: dla r = 44,7% wychodzi (0,447−0,112)/0,888 = 37,7% (to te „~38%”); dla dolnego końca r = 38,2% wychodzi (0,382−0,112)/0,888 = 30,4%.

**Poprawka.** „Nawet przy najwyższym poziomie bazowym spośród porównywanych serwisów (11,2%) \pimin{} wynosi tam około 38% (dolny koniec 95% przedziału: około 30%).” Najlepiej policzyć to tą samą symulacją co dla innych serwisów i podać 90% CI.

> **Weryfikator:** Rachunek się zgadza: (0,447-0,112)/0,888 = 37,7%, a dla dolnego końca r = 38,2% wychodzi 30,4%. b = 11,2% to faktycznie maksimum w aneksie (oko.press). Tekst używa jednak „dolnej granicy” w sensie, który sam zdefiniował w l. 162: \pimin{} jako dolna granica względem czułości (TPR = 100%). Nie jest to więc sprzeczne z przyjętą terminologią. Problemem jest dwuznaczność terminu, bo w l. 183, 251, 345 i 360 „dolna granica” oznacza koniec przedziału ufności. Ten sam punktowy „co najmniej” pojawia się w l. 228 („co najmniej 4%” to punktowe \pimin{}, CI [2,4; 6,1]). Wynik dotyczy serwisu bez porównania, opisanego wyłącznie jako poszlaka, więc severity minor.
>
> **Wersja skorygowana:** Termin „dolna granica” ma w tekście dwa znaczenia: \pimin{} jako dolna granica względem czułości (l. 162, 228, 294) oraz dolny koniec przedziału (l. 183, 251, 345, 360, 403). W l. 294 „~38%” to punktowe \pimin{} przy maksymalnym b (11,2%, oko.press). Dolny koniec przedziału r (38,2%) daje około 30%. Napisać „\pimin{} wynosi około 38% (przy dolnym końcu przedziału r: około 30%)”. Analogicznie w l. 228: „\pimin{} = 4%” zamiast „co najmniej 4%”. W całym tekście rozróżnić „dolne oszacowanie (\pimin{})” od „dolnej granicy przedziału”.

### [W8] Terminy i skróty używane przed zdefiniowaniem

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:36, 108, 114, 142, 152, 172`

**Problem.** AUC pojawia się w streszczeniu i w l. 114 bez definicji. TPR jest używane w l. 114 i w tab. 3, zanim zostanie objaśnione (pośrednio dopiero w l. 142 i 156). „pp” pojawia się bez definicji (l. 152). Zbiory \texttt{train}/\texttt{dev}/\texttt{test} wchodzą w l. 142, ale podział danych nie jest nigdzie opisany (ani proporcje, ani zasada: losowo po tekstach czy po serwisach). Skrót „CI” (angielski) wchodzi w l. 172 bez rozwinięcia. „LoRA” i „(1024 tokeny)” w l. 108 bez objaśnienia; nie wiadomo, że dłuższe teksty są obcinane, a docs/detektory.md mówi też o zamianie na małe litery. Nazwa „Pangram” używana samodzielnie myli otwarty model EditLens z komercyjnym detektorem Pangram Labs, którego użyli Russell i in.

**Dowód.** l. 114: „(TPR 1\%)” przed jakąkolwiek definicją. l. 142: „ze zbiorów \texttt{train} i \texttt{dev}” pojawia się po raz pierwszy. docs/detektory.md: „Teksty są przycinane do 1024 tokenów, zapisywane małymi literami”.

**Poprawka.** W 3.1 dodać zdanie definiujące: „FPR (odsetek tekstów ludzkich oznaczonych jako AI), TPR (czułość: odsetek tekstów AI oznaczonych jako AI), AUC (pole pod krzywą ROC; 0,5 = brak rozróżnienia), p.p. (punkty procentowe)”. W 2.1 opisać podział train/dev/test. W l. 108: „…który zwraca wynik od 0 (tekst ludzki) do 1 (tekst AI); teksty dłuższe niż 1024 tokeny obcinamy, a całość sprowadzamy do małych liter, jak w kodzie autorów”. Ujednolicić nazwę: „EditLens (Pangram)” przy pierwszym użyciu, dalej „EditLens” albo jawnie zdefiniowany skrót. Ujednolicić też opis danych uczących: tekst mówi „głównie na tekstach angielskich”, a docs/detektory.md „tylko na angielskim”.

> **Weryfikator:** TPR pojawia się pierwszy raz w l. 114 („TPR 1%”) bez definicji. AUC występuje w streszczeniu bez definicji. „pp” nie jest zdefiniowane. train/dev/test pojawia się tylko w l. 142, a podział danych nie jest nigdzie opisany (grep). „Pangram” użyty samodzielnie, a Russell i in. używali komercyjnego detektora Pangram Labs. docs/detektory.md:54-55 mówi o obcinaniu do 1024 tokenów, zamianie na małe litery i uczeniu „tylko na angielskim”, a l. 108 i 410 piszą „głównie”/„uczono na tekstach angielskich”. Brak opisu podziału train/dev/test jest najważniejszym elementem tego punktu.

### [W9] Rozbieżne liczby tego samego wyniku w różnych tabelach

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:258, 382-383; tabela_serwisow.tex:17-18`

**Problem.** Przedziały \pimin{} dla tych samych serwisów różnią się między tekstem, tab. 10 i aneksem. Prawdopodobnie pochodzą z różnych przebiegów symulacji (inne ziarno albo inny N). Czytelnik nie wie, która wersja jest właściwa.

**Dowód.** goniec.pl \pimin{}: [7,5; 14,1] w aneksie (l. 18), a [7,5; 14,2] w tekście (l. 258) i w tab. 10 (l. 382). pap.pl \pimin{}: [4,2; 15,6] w aneksie (l. 17), a [4,4; 15,5] w tab. 10 (l. 383).

**Poprawka.** Liczyć wszystkie tabele z jednego przebiegu (jedno ziarno RNG, wyniki zapisywane do CSV i wczytywane do tabel). Albo, jeśli tab. 10 to osobny przebieg, ustawić to samo ziarno. Dodać zdanie o liczbie powtórzeń i ziarnie w 3.6.

> **Weryfikator:** Potwierdzam. goniec.pl \pimin{}: aneks [7,5; 14,1], tab. detektory i l. 258 [7,5; 14,2]. pap.pl: aneks [4,2; 15,6], tab. detektory [4,4; 15,5]. Recenzent pominął też nczas.com: aneks [5,7; 13,3], tab. detektory [5,7; 13,2]. W tekście (l. 258) goniec ma „\pimin{} = 11%”, a w tabelach 10,9.

### [W10] Niejednoznaczne i niedokładne streszczenie oraz tytuł

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:27-28, 36`

**Problem.** (a) „Trzy kolejne wypadają w części wariantów analizy”: „wypadają” można odczytać jako „wypadają z listy”, a chodzi o to, że są masowe tylko w części wariantów. (b) Streszczenie nie mówi, że próba jest celowa (S3 dobrano jako podejrzane), a od tego zależy interpretacja zdania „Żaden z największych…”. (c) „W całej próbie” oznacza tu 37 porównywanych serwisów z poprawką na skład, nie 45. (d) Mieszane myślniki w jednym zdaniu: „2023-2025 … 4--18%”. (e) Tytuł „Ile polskich serwisów…” sugeruje odpowiedź dla populacji, a „newsowych” to rejestr potoczny (w streszczeniu: „informacyjne”).

**Dowód.** l. 36: „Trzy kolejne wypadają w części wariantów analizy.” l. 56: „Próba nie jest więc losowa i wnioski dotyczą tylko tych serwisów.”

**Poprawka.** Streszczenie: „Trzy kolejne serwisy spełniają kryterium tylko w części wariantów analizy.”; dodać „Próba (45 serwisów, w tym 14 dobranych jako podejrzane) nie jest losowa.”; „W 37 porównywanych serwisach udział AI w latach 2023–2025 szacujemy na 4–18%.” Tytuł np.: „Masowe publikowanie tekstów generowanych przez AI w polskich serwisach informacyjnych: pomiar bez etykiet w 45 serwisach (2020–2025)”.

> **Weryfikator:** l. 36 zawiera „Trzy kolejne wypadają w części wariantów analizy”, co jest dwuznaczne. Streszczenie nie mówi o celowym doborze S3, choć l. 56 i 412 to podkreślają. „W całej próbie” dotyczy wyniku standaryzowanego dla 37 serwisów. Mieszane myślniki: „2023-2025” obok „4--18\%” w tym samym streszczeniu. Tytuł: „newsowych” w tytule, „informacyjne” w streszczeniu. Wszystko się zgadza.

### [W11] Niespójne myślniki zakresów i jednostka „pp”

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:28, 36, 142, 147, 152, 156, 166, 403, 409, 414, 415; bibliografia l. 424-425`

**Problem.** Zakresy zapisano raz łącznikiem (2020-2022), raz półpauzą (2020--2022), czasem w tym samym akapicie. Polska typografia wymaga półpauzy bez spacji w zakresach. Skrót „pp” jest angielski; po polsku „p.p.” lub „pkt proc.”, a w tekście nie ma jego definicji.

**Dowód.** grep wzorca łącznika w zakresach daje 15 wystąpień: l. 28 „2020-2025”, 36 „0,49-0,56”, „2023-2025”, 142, 147, 152 „10-20\%”, 156 (×2), 166, 403, 409 (×2), 414, 415 „85-87\%”, a w bibliografii „71-76”, „5-15”. W większości pozostałych miejsc stoi „--”.

**Poprawka.** Zamienić wszystkie zakresy na „--” (sed 's/\([0-9]\)-\([0-9]\)/\1--\2/' z ręczną kontrolą nazw typu CC-MAIN-2021-04). Ujednolicić „pp” → „p.p.” (najlepiej makrem \newcommand{\pp}{\,p.p.}) i zdefiniować skrót przy pierwszym użyciu.

> **Weryfikator:** grep wzorca cyfra-cyfra (bez CC-MAIN, nazw modeli i arXiv) daje dokładnie wskazane linie: 28, 36, 142, 147, 152, 156, 166, 403, 409, 414, 415, 424, 425. W pozostałych 26 liniach są „--”. „pp” bez definicji. Severity raczej nit/minor, ale łatwe do poprawy, więc minor jest w porządku.

### [W12] Najsłabiej zredagowane fragmenty: niejasność i składnia

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:44, 110, 116, 170, 172, 360`

**Problem.** Kilka akapitów jest pociętych na zbyt krótkie zdania albo niejasnych: (a) l. 44 to rejestr potoczny („kosztuje ułamek grosza”, „mają powód, żeby z tego korzystać”, „Pytamy, w ilu … da się to zmierzyć”; pytanie badawcze nie dotyczy mierzalności). (b) l. 110: „losowanych kolejno z każdego serwisu” jest niejasne; nie wiadomo, co zrobiono z odpowiedziami oznaczonymi za >25% wspólnych 5-gramów; zdanie o „G1 w zbiorze gold i w naszych danych” jest mylące, bo G1 to podzbiór naszych danych. (c) l. 116: „Zdecydowała walidacja. To, jaki wynik…” jest rwane; „Zbiór gold policzyliśmy” to kolokwializm. (d) l. 170: „poziom bazowy dopasowujemy do serwisów po 2022 r.” jest niezrozumiałe bez kodu. (e) l. 172: akapit o poziomach przedziałów jest zawiły („Dolny koniec przedziału 5.--95.\ percentyl jest…”). (f) l. 360: błąd „w wnioskach” → „we wnioskach”.

**Dowód.** Cytaty jak w opisie problemu.

**Poprawka.** (a) „Od premiery ChatGPT (30 listopada 2022 r.) koszt wygenerowania artykułu po polsku spadł niemal do zera. Serwisy zależne od ruchu z wyszukiwarek i mediów społecznościowych mają zatem ekonomiczną motywację, by z tego korzystać. Pytamy, które polskie serwisy informacyjne publikują teksty generowane przez AI na masową skalę.” (c) „Detektor wybraliśmy wyłącznie na podstawie walidacji, bez wglądu w jego wyniki na badanych danych.” „Na zbiorze gold oceniliśmy tylko Bielika 1,5B.” (d) „Wynik zbiorczy standaryzujemy względem składu: poziom bazowy dla okresu 2023–2025 to średnia poziomów bazowych serwisów ważona liczbą ich tekstów z lat 2023–2025.” (e) „Dla wyników zbiorczych i wielkości opisowych podajemy dwustronne przedziały 95%. Reguła klasyfikacji serwisu pyta jednostronnie, czy udział AI wynosi co najmniej 20%, więc używamy jednostronnej dolnej granicy 95%, czyli 5. percentyla symulacji; jest to spójne z δ, które również jest 95. percentylem. Na rysunkach pokazujemy przedział 5.–95. percentyl i oznaczamy go jako 90% CI.” (b) Doprecyzować: „pierwsze teksty w losowej kolejności z każdego serwisu, aż do 100”, „odpowiedzi oznaczone wygenerowaliśmy ponownie / wykluczyliśmy (n = …)”. (f) Poprawić na „we wnioskach”.

> **Weryfikator:** Wszystkie cytaty są w tekście (l. 44, 110, 116, 170, 172). Błąd „w wnioskach” jest w l. 360 (grep). l. 110: los odpowiedzi oznaczonych za >25% wspólnych 5-gramów nie jest opisany, a zdanie o G1 „w zbiorze gold i w naszych danych” jest mylące. Zgadzam się z oceną.

### [W13] Bibliografia ręczna, niekompletna i niejednolita

*Waga:* **minor** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:420-433`

**Problem.** Bibliografia jest ręczna (thebibliography), bez DOI i URL. Format jest niejednolity: tytuły raz kursywą, raz nie (rogan, liang2025); „i in.” zamiast pełnych list autorów (liang2025, smigiel); brak tomu, stron i DOI dla Liang i in. (Nature Human Behaviour 2025). Pozycja „cc” to w istocie odwołanie do pliku w repo, a nie do źródła. Status „ICLR 2026” dla EditLens oraz lista autorów i strony Śmigiela (PolEval 2025) wymagają weryfikacji z oficjalnym proceedings.

**Dowód.** l. 431: „Liang, W. i in. (2025). Quantifying large language model usage in scientific papers. \emph{Nature Human Behaviour}.” (brak tomu, stron, DOI); l. 425: „Przybyła, P. i in. (2025)”.

**Poprawka.** Przejść na BibTeX/biblatex (plik refs.bib, styl np. biblatex-ieee lub authoryear z babel polish). Pobrać wpisy z DBLP lub ACL Anthology lub Crossref z DOI. Uzupełnić pełne listy autorów, tom, strony i DOI. Dla Common Crawl podać cytowanie zbioru (URL, identyfikatory crawli w tabeli w aneksie), nie tylko ścieżkę w repo.

> **Weryfikator:** l. 420-433: ręczne thebibliography, brak DOI, „i in.” w liang2025 i smigiel, liang2025 bez tomu, stron i DOI, a tytuł liang2025 i rogan nie jest kursywą, w przeciwieństwie do pozostałych. bibitem{cc} odsyła do pliku w repo. Statusu EditLens jako ICLR 2026 nie mogłem zweryfikować offline, więc słusznie oznaczony jako „do weryfikacji”.

### [W15] Rysunki: tytuły wewnątrz grafik, tło i format rastrowy

*Waga:* **minor** · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `figures/fig02_instrument_auc.png, fig08_robustness.png (i pozostałe fig0*); preprint.tex:136, 302`

**Problem.** Rysunki mają wbudowane tytuły-tezy („Tylko Pangram widzi przeróbki GPT; detektory Bielika działają tylko na Śmigielu”, „Stabilne przy każdym progu, długości i δ: …”), które dublują podpisy LaTeX, a czasem mówią mocniej niż tekst. Tło jest złamaną bielą (nie białe), co na wydruku i w PDF daje widoczne prostokąty. Grafiki są rastrowe (PNG), a nie wektorowe, więc tekst nie skaluje się i nie da się go przeszukiwać. W fig02 etykieta „Binoculars” nie mówi, że wartość gold dotyczy Bielika 1,5B. W fig08 nagłówki kolumn obrócone o 30° wychodzą poza siatkę („„masowo” ≥ 30%” obcięte przy prawej krawędzi).

**Dowód.** Podgląd fig02_instrument_auc.png i fig08_robustness.png: tytuł nad wykresem, tło ok. #FAFAF8; rozmiar plików PNG 77-264 KB.

**Poprawka.** Usunąć tytuły z rysunków (teza należy do podpisu). Ustawić facecolor='white' i eksportować do PDF (fig.savefig('figNN.pdf', bbox_inches='tight')). Fonty w rysunkach dopasować do tekstu (rozmiar ≥ 8 pt po skalowaniu do \linewidth = 16 cm). W fig02 dopisać „(Bielik 1,5B)”. W fig08 dać nagłówki poziomo w dwóch liniach albo zwiększyć górny margines.

> **Weryfikator:** Obejrzałem fig02 i fig08. Wbudowane tytuły-tezy są obecne („Tylko Pangram widzi przeróbki GPT…”, „Stabilne przy każdym progu, długości i δ…”) i dublują podpisy, a tło jest złamaną bielą. W fig02 etykiety Bielika („Binoculars”, „Fast-DetectGPT”) nie mówią, że chodzi o 1,5B. Nieprawdą jest, że nagłówek „„masowo” ≥ 30%” w fig08 jest obcięty: jest w całości widoczny, choć sięga krawędzi. PNG mają ok. 2000-2300 px szerokości, co przy 16 cm daje ok. 300 dpi. Użytkownik chce prostego standardu rysunków przy dobrej jakości, więc wymóg eksportu wektorowego to sugestia, nie błąd.
>
> **Wersja skorygowana:** Usunąć tytuły-tezy z rysunków (teza należy do podpisu, a „Tylko Pangram widzi…” mówi mocniej niż tekst). Tło ustawić na białe. W fig02 dopisać „(Bielik 1,5B)” przy detektorach Bielika. Rozdzielczość PNG (~300 dpi przy 16 cm) jest wystarczająca. Eksport do PDF jest opcjonalny. Nagłówki fig08 nie są obcięte, choć ostatni dotyka krawędzi.

### [W14] Preambuła działa tylko z pdfLaTeX; overfull boxes w tekście

*Waga:* **nit** (referent: minor) · *Weryfikacja:* 🟡 częściowo potwierdzone (skorygowane) · *Miejsce:* `preprint.tex:3-6, 25, 294, 403, 438; tabela_serwisow.tex:4`

**Problem.** Kompilacja kopii przez tectonic (silnik XeTeX) daje 1146 ostrzeżeń „Missing character” (ą, ę, ł, ż, „ ” znikają z PDF), bo T1 + inputenc + lmodern to zestaw pod pdfLaTeX; inputenc jest przy tym zbędny („inputenc package ignored with utf8 based engines”). Na Overleaf z pdfLaTeX działa, ale przy zmianie silnika (np. xelatex/lualatex na arXiv lub lokalnie) tekst traci polskie znaki bez błędu kompilacji. Do tego overfull hbox: l. 438 o 110,7 pt (ścieżka w \texttt), l. 403 o 28,4 pt i l. 294 o 15,3 pt (domeny w \dom = \texttt bez możliwości łamania), tabela aneksu o 8,2 pt, tab. 5 o 3,6 pt; underfull w kolumnach p{} tab. 3, 4 i 10 (l. 128, 183, 186, 378, 386).

**Dowód.** Log tectonic: „Missing character: There is no ż ("17C) in font ec-lmr10!” (221×), „Overfull \hbox (110.73141pt too wide) in paragraph at lines 438--439”, „(28.4299pt too wide) … lines 403--404”, „(15.33354pt too wide) … lines 294--295”.

**Poprawka.** Usunąć \usepackage[utf8]{inputenc}, a fontenc i lmodern ładować warunkowo: \usepackage{iftex}\ifPDFTeX\usepackage[T1]{fontenc}\usepackage{lmodern}\else\usepackage{fontspec}\fi. Dodać w README lub w nagłówku pliku „kompilować pdfLaTeX”. \dom i ścieżki zdefiniować przez pakiet url/xurl: \newcommand{\dom}[1]{\nolinkurl{#1}} (umożliwia łamanie po kropce). W kolumnach p{} użyć >{\raggedright\arraybackslash}p{…}. Tabelę aneksu zmieścić przez \setlength{\tabcolsep}{3pt} albo skrócenie nagłówków (np. „ozn.”).

> **Weryfikator:** Kompilacja kopii przez tectonic odtwarza 1146 ostrzeżeń „Missing character” i overfull: 110,7 pt (l. 438), 28,4 pt (l. 403), 15,3 pt (l. 294), 8,2 pt w aneksie, 3,6 pt w l. 216-226. Overleaf i arXiv kompilują jednak domyślnie pdfLaTeX, dla którego T1 + inputenc + lmodern jest poprawną preambułą, więc ryzyko utraty polskich znaków jest hipotetyczne. Wartości overfull zmierzono pod XeTeX z brakującymi glifami, więc pod pdfLaTeX będą inne. Overfull przy \texttt (l. 438, \dom) jest realny niezależnie od silnika, ale l. 438 zniknie po poprawce z W4.
>
> **Wersja skorygowana:** Preambuła jest poprawna dla pdfLaTeX (domyślnego na Overleaf i arXiv). Kompilacja innym silnikiem gubi polskie znaki, więc warto dodać komentarz „kompilować pdfLaTeX” albo warunek iftex. Realny problem to brak łamania w \dom/\texttt: overfull w l. 403 i 294 oraz ścieżka w l. 438. Rozwiązanie: \dom przez \nolinkurl (pakiet xurl). Wartości overfull zmierzone pod XeTeX są tylko przybliżone.

### [W16] Drobne kwestie notacji i rejestru

*Waga:* **nit** · *Weryfikacja:* ✅ potwierdzone · *Miejsce:* `preprint.tex:108, 114, 170, 256, tabela_serwisow.tex:16`

**Problem.** (a) „Beta$(k+\tfrac12,\,n-k+\tfrac12)$”: nazwa rozkładu poza trybem matematycznym; nie wiadomo też, czy r jest losowane z tego samego rozkładu. (b) Anglicyzmy „perplexity”, „crawl/crawla”, „open-source” obok polskich odpowiedników (perpleksja, zrzut Common Crawl). (c) W aneksie \pigold{} zmianynaziemi.pl „100,0 [100,0; 100,0]” to zdegenerowany przedział wynikający z obcięcia; czytelniej byłoby podać wartość nieobciętą albo „>100 (obcięte)”. (d) Makra \pimin/\pigold nie są używane w tabela_serwisow.tex (tam ręcznie $\pi_{\mathrm{min}}$), co psuje jednolitość przy zmianie notacji.

**Dowód.** l. 170; l. 108, 114, 129; tabela_serwisow.tex:5, 7, 16.

**Poprawka.** $r,b\sim\mathrm{Beta}(k+\tfrac12,\,n-k+\tfrac12)$ z jawnym „każde osobno”. „perpleksja” lub „zwykła perpleksja (log-perplexity)” przy pierwszym użyciu. W aneksie „>100 (obc.)”. W tabela_serwisow.tex użyć \pimin{} i \pigold{}.

> **Weryfikator:** l. 170: „Beta$(...)$”; anglicyzmy „perplexity” (l. 108, 114, 129) i „crawl” (l. 58, 414); aneks l. 16: „100,0 [100,0; 100,0]”; tabela_serwisow.tex używa ręcznie $\pi_{\mathrm{min}}$ zamiast makr. Wszystko się zgadza i są to drobiazgi.

### Przeoczenia wskazane przez weryfikatora (E)

- preprint.tex:403: anakolut „W naszej próbie 37 polskich serwisów, które da się porównać przed i po 2022 r., jeden (...) publikuje”. Poprawka: „Spośród 37 serwisów z naszej próby, które da się porównać przed i po 2022 r., jeden (...)”. W tym samym akapicie „z dolną granicą 31%” dla goniec.pl to dolny koniec \pigold{}, a dwa zdania wcześniej „co najmniej 29,8%” dotyczy \pimin{}. Należy jawnie podać, o który szacunek chodzi.
- preprint.tex:337: błąd składniowy „to w każdym wariancie te same pięć serwisów”. Poprawka: „to w każdym wariancie tych samych pięć serwisów”.
- preprint.tex:228: „szacujemy na od co najmniej 4% do około 18%” – „co najmniej 4%” to szacunek punktowy \pimin{} (tab. zbiorczy: 4,0% [2,4; 6,1]), a nie dolna granica przedziału. To ten sam problem dwuznaczności terminu co w l. 294 i 403. Poprawka: „od 4% (\pimin{}) do około 18% (\pigold{})”.
- preprint.tex:258 vs tabele: goniec.pl ma w tekście „\pimin{} = 11%”, a w tab. detektory i w aneksie 10,9%. Do tego niezgodność nczas.com: aneks \pimin{} [5,7; 13,3], tab. detektory [5,7; 13,2]. To uzupełnienie W9.
