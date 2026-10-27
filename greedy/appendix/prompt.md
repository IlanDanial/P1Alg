Review the concept md file and rough draft plan. Work in the order given, keep each step inside its time box, and when something cannot be finished, mark it clearly rather than silently skipping it. 

## Hard rules
1. **Do not edit Ilan's files** except these four, and only as described: `divide_and_conquer/main.tex`, `divide_and_conquer/refs.bib` (append greedy citations), `divide_and_conquer/main.pdf` (overwritten by rebuilding, never hand-edited), and the top-level `README.md`. Everything else of mine goes under sibling folder `greedy/`.
2. **Self-contained.** `C:\Users\R\Documents\Cruise-Finder` is a read-only reference. Read `cruise_finder/carnival.py` and `cruise_finder/config.py` to double check how the Carnival request is built and paginated (URL, query parameters, headers, month code, pagination), but do not import from that repo, do not copy its database or application code, do not build any app functionality, and do not modify it.
3. Windows machine, PowerShell. Python 3.12 is at `C:\Users\R\AppData\Local\Programs\Python\Python312`. No TeX distribution and no `elan`/`lake` are installed; steps 6 and 9 say what to install.


## The problem

**What is fixed:** the abstraction, the algorithm, and the proofs below. Do not change them.

**What is a modeling choice, and must be presented as one:** the application framing. Do not claim anything about how cruise prices move unless you cite a source for it and ask me. If a source contradicts a claim below, drop the claim and alert me.

**Problem:** Cruise Finder is my self-hosted web app that tracks Carnival Cruise Line sailings from Florida. It gets prices from Carnival's public but undocumented search endpoint `GET https://www.carnival.com/cruisesearch/api/search`, which the app calls once per configured departure month, following pagination, and only on demand; every call is logged in an append-only audit table because the endpoint is unofficial and rate-limited. One **refresh batch** queries every configured month and follows every page, so it observes the current price of every listed sailing. Assumption to state: we treat every batch as having the same cost (pagination can change over time; the objective counts batches, not HTTP requests).

**The feature we propose**: the app accepts **quote requests**. A quote request names a sailing and a date interval [a_i, b_i] during which at least one fresh observation is acceptable. The objective is to satisfy every request with the fewest batches. For the case study, we generate example request windows from sailing dates by an explicitly stated policy: from Carnival's final-payment deadline (76 days before departure for cruises of 5 nights or fewer, 91 days for 6 nights or more; cite Carnival's own page, https://help.carnival.com/app/answers/detail/a_id/481, and verify the numbers there) to booking close, c days before departure. 

**Question.** Given every quote request's window, what is the fewest refresh batches that give every window at least one observation, and on which days?

**Abstraction.** Days are integers. Window W_i = [a_i, b_i] with a_i = d_i − F(L_i), b_i = d_i − c, F(L) = 76 if L ≤ 5 else 91, c a parameter (default 2; use Carnival's published cutoff if you find one). Drop windows with b_i < today; clip a_i to today. A refresh batch on day t observes every window with t ∈ W_i. Input: n integer intervals with a_i ≤ b_i. Output: a set T of days hitting every interval, |T| minimum. This is the minimum point cover of intervals (interval stabbing). It is **not** interval scheduling; say so in one sentence.

**Algorithm REFRESH-DAYS.** Sort windows by b ascending. T ← ∅, last ← −∞. For each window in order: if a_i > last, add b_i to T and set last ← b_i. Return T and the windows that triggered an addition (the "witnesses").

**Proofs** (typeset as Lemma 1, Lemma 2, Theorem 1, Theorem 2 in the style of `sec_dc.tex`):
- Lemma 1 (every window is covered). At window i, either a_i > last and b_i ∈ W_i is added, or a_i ≤ last = b_j for an earlier j with b_j ≤ b_i, so a_i ≤ b_j ≤ b_i and b_j ∈ T lies in W_i.
- Lemma 2 (witnesses are pairwise disjoint). Let i_1 < … < i_m be the triggering indices. For r < s, when i_s is processed, last = b_{i_{s−1}} ≥ b_{i_r} (last only increases, b's are sorted) and a_{i_s} > last ≥ b_{i_r}, so every day of W_{i_s} exceeds every day of W_{i_r}.
- Theorem 1 (optimality). Feasibility is Lemma 1. Any feasible T′ needs a day in each of the m pairwise-disjoint witness windows, and one day lies in at most one of them, so |T′| ≥ m = |T|.
- Theorem 2 (running time). O(n log n) time with a comparison sort and O(n) extra space; O(n) if the windows arrive sorted by closing day.

**Worked example:** windows [1,10], [4,12], [8,20], [15,25], [22,30] → days 10 and 25; one day is impossible because [1,10] and [22,30] share no day.

**Domain translation** (adapt, keep the voice): look at whichever sailing's quote window closes soonest among those not yet observed and refresh on that day; that batch also observes every other sailing whose window is open that day; cross them off and repeat. No schedule with fewer batches exists because the sailings you refreshed *for* have windows that never overlap, so each needed its own day. Finish with the real numbers from step 3, and say in the same breath that each sailing is observed once in its window, not nightly.

## Deliverables (exact paths)

```
greedy/
  README.md                 # same shape as divide_and_conquer/README.md
  .gitignore                # __pycache__/, .lake/, LaTeX build files (copy the root .gitignore patterns)
  refresh_days.py           # windows(sailings, today, c) and refresh_days(intervals) -> (days, witnesses)
  test_refresh_days.py
  fetch_sailings.py         # writes data/sailings.csv
  experiments.py            # writes results/*.csv
  plots.py                  # writes figures/*.pdf and *.png
  sec_greedy.tex
  app_greedy.tex            # created as a stub in step 5, filled in step 7
  appendix/transcript.md    # one-line placeholder; I export the transcripts myself
  data/sailings.csv
  results/scaling.csv, results/scan_only.csv
  figures/scaling.pdf/.png, figures/ratio.pdf/.png, figures/scan.pdf/.png, figures/windows.pdf/.png
  proof/                    # step 9 only, mirrors divide_and_conquer/proof
```

## Steps, in order

**Step 1 Algorithm.** `refresh_days.py` with a module docstring like `quadtree.py`'s. `refresh_days(intervals)` takes a list of `(a, b)` integer pairs and returns `(days, witnesses)`. `windows(sailings, today, c)` takes rows with `departure` (date) and `nights` (int) and returns clipped intervals as day offsets from `today`, dropping windows already closed. Raise `ValueError` on a > b.

**Step 2 Tests.** `test_refresh_days.py`, unittest, run as `python -m unittest test_refresh_days` from `greedy/`:
1. every input interval contains a returned day (Lemma 1);
2. witnesses are pairwise disjoint (Lemma 2);
3. brute force on 300 random instances with n ≤ 10 and endpoints in [0, 20]: enumerate subsets of days 0..20 and assert no feasible subset is smaller than the greedy's. This checks the implementation on small cases; it is not the proof, and the report must not call it one;
4. the worked example returns {10, 25};
5. `windows()` gives 76- and 91-day windows ending c days before departure for a 4-night and an 8-night sailing, and drops a sailing whose window closed yesterday.
All tests must pass before you continue.

**Step 3 Real data.** `fetch_sailings.py`: for each month November 2026 through April 2027, request page 1 with ports `MIA,PCV,TPA,JAX` and page size 200, using the same query shape, headers, and `MMYYYY` month code as Cruise-Finder's `carnival.py`, then **follow every page the response reports** (`lastPage`), exactly as the reference does. Sleep 3 seconds between requests. Write `data/sailings.csv` with columns `sailing_id, ship, port, itinerary, departure, nights` (nights from `dur`; confirm against arrival − departure). Then build windows with today = 2026-10-26 and c = 2, run the greedy, and print n, m, the chosen dates, and the horizon length in days. Those numbers go in the domain paragraph and the README. **If the endpoint errors, returns a block page, or returns zero itineraries for every month, stop and ask me.** Do not fabricate data.

**Step 4 Experiments.** `experiments.py`: n = 2^10 … 2^22. Generate windows by drawing departure days uniformly over a horizon of **2n days** (so closing days are mostly distinct; a fixed 730-day horizon would give millions of ties and measure something else) and lengths from the empirical length mix in `data/sailings.csv`, c = 2. Five runs per n on fresh inputs, fastest kept, gc disabled, Ilan's protocol. Also time the scan alone on pre-sorted input. Assert feasibility (Lemma 1) and witness count = output size on every run. Write `results/scaling.csv` and `results/scan_only.csv`. `plots.py`: (a) time vs n with an n log n least-squares fit; (b) time/(n log n); (c) scan-only time vs n with a linear fit; (d) `windows.pdf`: the real sailings as horizontal bars sorted by closing day, chosen refresh days as vertical lines, witnesses highlighted. In the report, describe what the plots show; Theorem 2 is an upper bound, so say whether the ratio is flat rather than asserting it must be. Record the CPU (`Get-CimInstance Win32_Processor | Select Name`) and Python version.

**Step 5 The section and main.tex.** `sec_greedy.tex`, structured like `sec_dc.tex` (problem, abstraction, algorithm with an `algorithmic` figure, running time, correctness with lemma/theorem/IEEEproof environments, explanation in the problem domain, experiments with Setup and Running-time paragraphs and the figures). Section title `Greedy: Fewest Price Refreshes Under a Request Budget`, label `sec:greedy`. State the modeling choices and the limitation from "The problem" above. Citations, appended to `divide_and_conquer/refs.bib`: Carnival's final-payment page (above); Carnival's booking cutoff only if you find Carnival's own page, otherwise c stays an assumption; an industry source on cabins returning to inventory / repricing after final payment only if found; the Cruise-Finder repository (read the remote from that folder's `.git/config`; if private, cite as "private repository, available on request"); Kleinberg & Tardos chapter 4 for the greedy paradigm. No rambling. 

Create `app_greedy.tex` now as a stub containing the two appendix section headings and labels (`app:greedy-code`, `app:greedy-llm`) so main.tex compiles in step 6; fill it in step 7.

Edit `divide_and_conquer/main.tex`: replace **every** `\partnertodo{...}`: author block (Ryan Rodriguez, rrodriguez7@ufl.edu, same affiliation lines as Ilan), abstract sentences, keywords (`greedy algorithm, interval point cover, web scraping, rate limiting, cruise fares`), the introduction paragraph (both halves scrape travel marketplaces under a platform limit: the divide-and-conquer half asks *where* to look when a map caps results per window; this half asks *when* to look when an API caps how often you may ask), the greedy section (replace the placeholder with `\input{../greedy/sec_greedy}`, keep `\input{sec_dc}` after it), and the conclusion paragraph. Reference greedy figures and listings with `../greedy/` paths. Add `\input{../greedy/app_greedy}` after the existing divide-and-conquer appendix inputs. Do not restructure anything else.

**Step 6 Compile.** Install Tectonic: `winget install --id Tectonic.Tectonic`; if that id fails, `winget search tectonic`; if winget is unavailable, install MiKTeX basic via winget and use `pdflatex` + `bibtex` + `pdflatex` ×2. Compile from `divide_and_conquer/` with `tectonic main.tex`. Fix every error and every undefined reference or citation warning. Verify: `rg -n "partnertodo" divide_and_conquer/main.tex divide_and_conquer/sec_dc.tex greedy/*.tex` returns only the `\newcommand` line; `rg -n "\?\?" divide_and_conquer/main.log` is empty (if Tectonic keeps no log, grep its console output). Overwrite the tracked `divide_and_conquer/main.pdf` and report its page count. Confirm no absolute paths appear in any `.tex` so the folder still builds on Overleaf.

**Step 7 Appendix and README.** Fill `app_greedy.tex`: Appendix "Greedy Code" with `\lstinputlisting` of `refresh_days.py` and `experiments.py` (tests, plotting script, data, and raw results referenced as in the repository, like `app_dc.tex`), then Appendix "Greedy LLM Prompts and Results" in the format of `app_dc.tex`: tools and models (Claude Code with the model you are running as, for implementation; an earlier Claude Code planning session and a Codex session that researched the course requirements and reviewed the plan, whose transcripts I will add), this entire prompt verbatim, then per step a short record of what you produced, what you checked, and every correction (failed test, compile error, proof attempt that did not close). 

**Step 8. Verification and report.** From `greedy/`: `python -m unittest test_refresh_days`; confirm the CSVs and figures exist; `python plots.py`. From the repo root: `git status --short`; it must list only `greedy/**`, `divide_and_conquer/main.tex`, `divide_and_conquer/main.pdf`, `divide_and_conquer/refs.bib`, and `README.md`. Then report: real-data numbers (n, m, dates); page count; citations found vs left as assumptions; anything unfinished or unverified.

**Step 9  Lean formalization.** Install elan with the official Windows installer from https://github.com/leanprover/elan, confirm `cd divide_and_conquer/proof; lake build` succeeds so toolchain `leanprover/lean4:v4.35.0` is present, then create `greedy/proof/` mirroring Ilan's layout (`lakefile.toml`, same `lean-toolchain`, `Proof.lean`, `Proof/Refresh.lean`, `.gitignore` for `.lake/`). Core Lean only, no Mathlib. Model intervals as `Int × Int`, the input as `List (Int × Int)` with hypotheses `List.Pairwise (fun p q => p.2 ≤ q.2)` and `∀ p ∈ l, p.1 ≤ p.2`. Define `refresh` by structural recursion carrying `last`. Prove in order: (1) `refresh_covers`; (2) `witnesses_pairwise_disjoint`; (3) `refresh_optimal` (any covering list of days is at least as long). Add a Lean table and listing to `sec_greedy.tex` / `app_greedy.tex` the way Ilan's half does, saying exactly which statements are machine-checked. **Recompile `main.pdf`, rerun the step 8 checks, and update the report.**

## Stop and ask (only these)

- Carnival's endpoint blocks or returns nothing for every month in step 3.
- Tectonic and MiKTeX both fail to install.
- Anything that would require editing one of Ilan's files beyond the three allowed.
