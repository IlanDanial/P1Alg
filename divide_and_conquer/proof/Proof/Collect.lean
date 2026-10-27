/-!
# Capped map search: machine-checked correctness of `Collect`

Formalizes Section III-D of the report, statement for statement. Coordinates
are integers: reported coordinates have fixed precision, so the plane is a
grid. Only Lean's core library is used; every arithmetic step is discharged by
`omega`.

| Report      | Lean                   |
|-------------|------------------------|
| Lemma 3     | `quadrants_partition`  |
| Theorem 3   | `collect_correct`      |
| Lemma 4     | `unit_window_fits`     |
| Lemma 5     | `quadrants_side`       |
| Theorem 4   | `collect_terminates`   |
| Corollary 1 | `collect_total`        |

`collect` carries its remaining depth budget as an explicit argument and
returns `none` if the budget runs out. Theorem 4 shows that with budget
`⌈log₂ W⌉` this never happens when no location holds more than `k` listings.
-/

namespace Quadtree

/-- A half-open window `[x0, x1) × [y0, y1)`. -/
structure Window where
  x0 : Int
  x1 : Int
  y0 : Int
  y1 : Int

/-- The location `p` lies in window `w`. -/
def inWin (p : Int × Int) (w : Window) : Prop :=
  w.x0 ≤ p.1 ∧ p.1 < w.x1 ∧ w.y0 ≤ p.2 ∧ p.2 < w.y1

instance (p : Int × Int) (w : Window) : Decidable (inWin p w) := by
  unfold inWin; infer_instance

/-- The four quadrants of `w`, split at `⌊(x0+x1)/2⌋` and `⌊(y0+y1)/2⌋`. -/
def q1 (w : Window) : Window := ⟨w.x0, (w.x0 + w.x1) / 2, w.y0, (w.y0 + w.y1) / 2⟩
def q2 (w : Window) : Window := ⟨(w.x0 + w.x1) / 2, w.x1, w.y0, (w.y0 + w.y1) / 2⟩
def q3 (w : Window) : Window := ⟨w.x0, (w.x0 + w.x1) / 2, (w.y0 + w.y1) / 2, w.y1⟩
def q4 (w : Window) : Window := ⟨(w.x0 + w.x1) / 2, w.x1, (w.y0 + w.y1) / 2, w.y1⟩

/-- `1` if `p` lies in `w`, else `0`. -/
def ind (p : Int × Int) (w : Window) : Nat := if inWin p w then 1 else 0

/-! ## Lemma 3: the quadrants partition the window -/

/-- **Lemma 3.** A location in `w` lies in exactly one quadrant; a location
outside `w` lies in none. -/
theorem quadrants_partition (p : Int × Int) (w : Window) :
    ind p (q1 w) + ind p (q2 w) + ind p (q3 w) + ind p (q4 w) = ind p w := by
  -- Decide each of the five memberships, then the remaining goal is linear arithmetic.
  by_cases h0 : inWin p w <;> by_cases h1 : inWin p (q1 w) <;> by_cases h2 : inWin p (q2 w) <;>
    by_cases h3 : inWin p (q3 w) <;> by_cases h4 : inWin p (q4 w) <;>
    simp only [ind, h0, h1, h2, h3, h4, ite_true, ite_false] <;>
    simp only [inWin, q1, q2, q3, q4] at h0 h1 h2 h3 h4 <;> omega

/-- Lemma 3 in its set form: `p` is in `w` iff it is in some quadrant. -/
theorem quadrants_cover (p : Int × Int) (w : Window) :
    inWin p w ↔ inWin p (q1 w) ∨ inWin p (q2 w) ∨ inWin p (q3 w) ∨ inWin p (q4 w) := by
  simp only [inWin, q1, q2, q3, q4]
  omega

/-! ## The algorithm -/

variable {α : Type} (P : List α) (loc : α → Int × Int) (k : Nat)

/-- `P_w`: the listings located in `w`. -/
def listingsIn (w : Window) : List α :=
  P.filter (fun a => decide (inWin (loc a) w))

/-- The capped search: the listings in `w` if there are at most `k`, else overflow. -/
def oracle (w : Window) : Option (List α) :=
  if (listingsIn P loc w).length ≤ k then some (listingsIn P loc w) else none

/-- `Collect` from the report, with an explicit depth budget. Returns the
listings found and the leaf windows, or `none` if the budget runs out. -/
def collect : Nat → Window → Option (List α × List Window)
  | 0, w =>
    match oracle P loc k w with
    | some A => some (A, [w])
    | none => none
  | fuel + 1, w =>
    match oracle P loc k w with
    | some A => some (A, [w])
    | none =>
      match collect fuel (q1 w), collect fuel (q2 w),
            collect fuel (q3 w), collect fuel (q4 w) with
      | some (o1, l1), some (o2, l2), some (o3, l3), some (o4, l4) =>
        some (o1 ++ o2 ++ o3 ++ o4, l1 ++ l2 ++ l3 ++ l4)
      | _, _, _, _ => none

/-- Number of leaves in `leaves` containing `p`. -/
def leafCount (p : Int × Int) (leaves : List Window) : Nat :=
  leaves.countP (fun l => decide (inWin p l))

/-- The three properties Theorem 3 asserts of an answer `(out, leaves)` for `w`:
`out` is exactly `P_w`; every leaf is under the cap; every location in `w` lies
in exactly one leaf and every location outside `w` in none. -/
def Correct (w : Window) (out : List α) (leaves : List Window) : Prop :=
  (∀ a, a ∈ out ↔ a ∈ P ∧ inWin (loc a) w) ∧
  (∀ l ∈ leaves, (listingsIn P loc l).length ≤ k) ∧
  (∀ p, leafCount p leaves = ind p w)

/-! ## Theorem 3: partial correctness -/

theorem mem_listingsIn (a : α) (w : Window) :
    a ∈ listingsIn P loc w ↔ a ∈ P ∧ inWin (loc a) w := by
  simp [listingsIn, List.mem_filter]

theorem oracle_some {w : Window} {A : List α} (h : oracle P loc k w = some A) :
    A = listingsIn P loc w ∧ (listingsIn P loc w).length ≤ k := by
  unfold oracle at h
  split at h
  · cases h; exact ⟨rfl, by assumption⟩
  · cases h

theorem leafCount_singleton (p : Int × Int) (w : Window) : leafCount p [w] = ind p w := by
  simp only [leafCount, ind, List.countP_cons, List.countP_nil, decide_eq_true_eq]
  split <;> rfl

theorem leafCount_append (p : Int × Int) (l₁ l₂ : List Window) :
    leafCount p (l₁ ++ l₂) = leafCount p l₁ + leafCount p l₂ := by
  simp [leafCount, List.countP_append]

/-- A non-overflowing window is a correct leaf. -/
theorem leaf_correct {w : Window} {A : List α} (h : oracle P loc k w = some A) :
    Correct P loc k w A [w] := by
  obtain ⟨rfl, hk⟩ := oracle_some P loc k h
  refine ⟨fun a => mem_listingsIn P loc a w, ?_, fun p => leafCount_singleton p w⟩
  intro l hl
  simp only [List.mem_singleton] at hl
  subst hl; exact hk

/-- **Theorem 3.** Whenever `collect` returns an answer, the answer is correct. -/
theorem collect_correct (fuel : Nat) :
    ∀ (w : Window) (out : List α) (leaves : List Window),
      collect P loc k fuel w = some (out, leaves) → Correct P loc k w out leaves := by
  induction fuel with
  | zero =>
    intro w out leaves h
    unfold collect at h
    split at h
    · cases h; exact leaf_correct P loc k (by assumption)
    · cases h
  | succ fuel ih =>
    intro w out leaves h
    unfold collect at h
    split at h
    · cases h; exact leaf_correct P loc k (by assumption)
    · split at h
      · rename_i o1 l1 o2 l2 o3 l3 o4 l4 h1 h2 h3 h4
        cases h
        obtain ⟨m1, c1, v1⟩ := ih _ _ _ h1
        obtain ⟨m2, c2, v2⟩ := ih _ _ _ h2
        obtain ⟨m3, c3, v3⟩ := ih _ _ _ h3
        obtain ⟨m4, c4, v4⟩ := ih _ _ _ h4
        refine ⟨?_, ?_, ?_⟩
        · -- out = P_w: a listing is in some quadrant's output iff it is in w (Lemma 3).
          intro a
          rw [quadrants_cover]
          simp only [List.mem_append, m1, m2, m3, m4, and_or_left, or_assoc]
        · intro l hl
          simp only [List.mem_append] at hl
          rcases hl with ((hl | hl) | hl) | hl
          · exact c1 l hl
          · exact c2 l hl
          · exact c3 l hl
          · exact c4 l hl
        · intro p
          rw [leafCount_append, leafCount_append, leafCount_append, v1, v2, v3, v4]
          exact quadrants_partition p w
      · cases h

/-! ## Lemma 4, Lemma 5, Theorem 4: the depth budget `⌈log₂ W⌉` suffices -/

/-- `m ≤ k`: no single location holds more than `k` listings. -/
def CapOK : Prop := ∀ p : Int × Int, (P.filter (fun a => decide (loc a = p))).length ≤ k

/-- A filter by a stronger predicate is no longer than a filter by a weaker one. -/
theorem length_filter_le_of_imp (l : List α) (p q : α → Bool) (h : ∀ a, p a = true → q a = true) :
    (l.filter p).length ≤ (l.filter q).length := by
  induction l with
  | nil => simp
  | cons a l ih =>
    simp only [List.filter_cons]
    cases hp : p a with
    | true =>
      have hq := h a hp
      simp only [hq, ite_true, List.length_cons]
      omega
    | false =>
      simp only [Bool.false_eq_true, ite_false]
      split
      · simp only [List.length_cons]; omega
      · exact ih

/-- **Lemma 4.** A window of side at most 1 holds listings of a single
location, so under `m ≤ k` it is never split. -/
theorem unit_window_fits (hcap : CapOK P loc k) (w : Window)
    (hx : w.x1 - w.x0 ≤ 1) (hy : w.y1 - w.y0 ≤ 1) :
    (listingsIn P loc w).length ≤ k := by
  refine Nat.le_trans (length_filter_le_of_imp P _ _ ?_) (hcap (w.x0, w.y0))
  intro a ha
  simp only [decide_eq_true_eq, inWin, Prod.ext_iff] at ha ⊢
  omega

/-- **Lemma 5.** The quadrants of a window of side at most `2B` have side at most `B`. -/
theorem quadrants_side (w : Window) (B : Int)
    (hx : w.x1 - w.x0 ≤ 2 * B) (hy : w.y1 - w.y0 ≤ 2 * B) :
    ((q1 w).x1 - (q1 w).x0 ≤ B ∧ (q1 w).y1 - (q1 w).y0 ≤ B) ∧
    ((q2 w).x1 - (q2 w).x0 ≤ B ∧ (q2 w).y1 - (q2 w).y0 ≤ B) ∧
    ((q3 w).x1 - (q3 w).x0 ≤ B ∧ (q3 w).y1 - (q3 w).y0 ≤ B) ∧
    ((q4 w).x1 - (q4 w).x0 ≤ B ∧ (q4 w).y1 - (q4 w).y0 ≤ B) := by
  simp only [q1, q2, q3, q4]
  omega

/-- **Theorem 4.** Under `m ≤ k`, on a window of side at most `2^D`, `collect`
with depth budget `D` returns an answer. -/
theorem collect_terminates (hcap : CapOK P loc k) (D : Nat) :
    ∀ w : Window, w.x1 - w.x0 ≤ (2 : Int) ^ D → w.y1 - w.y0 ≤ (2 : Int) ^ D →
      ∃ r, collect P loc k D w = some r := by
  induction D with
  | zero =>
    intro w hx hy
    simp only [Int.pow_zero] at hx hy
    have hfits := unit_window_fits P loc k hcap w hx hy
    refine ⟨(listingsIn P loc w, [w]), ?_⟩
    simp [collect, oracle, hfits]
  | succ D ih =>
    intro w hx hy
    rw [Int.pow_succ, Int.mul_comm] at hx hy
    obtain ⟨⟨a1, b1⟩, ⟨a2, b2⟩, ⟨a3, b3⟩, ⟨a4, b4⟩⟩ := quadrants_side w _ hx hy
    unfold collect
    split
    · exact ⟨_, rfl⟩
    · obtain ⟨⟨o1, l1⟩, h1⟩ := ih (q1 w) a1 b1
      obtain ⟨⟨o2, l2⟩, h2⟩ := ih (q2 w) a2 b2
      obtain ⟨⟨o3, l3⟩, h3⟩ := ih (q3 w) a3 b3
      obtain ⟨⟨o4, l4⟩, h4⟩ := ih (q4 w) a4 b4
      rw [h1, h2, h3, h4]
      exact ⟨_, rfl⟩

/-- **Corollary 1 (total correctness).** Under `m ≤ k`, on a window of side at
most `2^D`, `collect` with depth budget `D` returns a correct answer. -/
theorem collect_total (hcap : CapOK P loc k) (D : Nat) (w : Window)
    (hx : w.x1 - w.x0 ≤ (2 : Int) ^ D) (hy : w.y1 - w.y0 ≤ (2 : Int) ^ D) :
    ∃ out leaves, collect P loc k D w = some (out, leaves) ∧ Correct P loc k w out leaves := by
  obtain ⟨⟨out, leaves⟩, h⟩ := collect_terminates P loc k hcap D w hx hy
  exact ⟨out, leaves, h, collect_correct P loc k D w out leaves h⟩

end Quadtree
