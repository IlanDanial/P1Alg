/-!
# Capped map search: machine-checked correctness of `Collect`

Formalizes Lemma 1 (the four quadrants partition a window) and Theorem 1
(partial correctness of `Collect`) from the report. Coordinates are integers:
any fixed-precision latitude/longitude scales to one. Only Lean's core library
is used; every arithmetic step is discharged by `omega`.

`Collect` is given a fuel budget (a bound on the recursion depth) so that Lean
accepts the definition. `collect_correct` is Theorem 1: *whenever* `collect`
returns, its answer is exactly the listings in the window, every leaf is under
the cap, and the leaves cover the window. `collect_terminates` is Lemma 2 on
the grid: if no location holds more than `k` listings, depth `⌈log₂ W⌉`
suffices, where `W` bounds the window's width and height. `collect_total`
combines the two.
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

/-- The four quadrants of `w`, split at its midpoint. -/
def q1 (w : Window) : Window := ⟨w.x0, (w.x0 + w.x1) / 2, w.y0, (w.y0 + w.y1) / 2⟩
def q2 (w : Window) : Window := ⟨(w.x0 + w.x1) / 2, w.x1, w.y0, (w.y0 + w.y1) / 2⟩
def q3 (w : Window) : Window := ⟨w.x0, (w.x0 + w.x1) / 2, (w.y0 + w.y1) / 2, w.y1⟩
def q4 (w : Window) : Window := ⟨(w.x0 + w.x1) / 2, w.x1, (w.y0 + w.y1) / 2, w.y1⟩

/-! ## Lemma 1: the quadrants partition the window -/

/-- Every location in `w` lies in one of its quadrants, and conversely. -/
theorem quadrants_cover (p : Int × Int) (w : Window) :
    inWin p w ↔ inWin p (q1 w) ∨ inWin p (q2 w) ∨ inWin p (q3 w) ∨ inWin p (q4 w) := by
  simp only [inWin, q1, q2, q3, q4]
  omega

/-- No location lies in two different quadrants. -/
theorem quadrants_disjoint (p : Int × Int) (w : Window) :
    (inWin p (q1 w) → ¬ inWin p (q2 w)) ∧ (inWin p (q1 w) → ¬ inWin p (q3 w)) ∧
    (inWin p (q1 w) → ¬ inWin p (q4 w)) ∧ (inWin p (q2 w) → ¬ inWin p (q3 w)) ∧
    (inWin p (q2 w) → ¬ inWin p (q4 w)) ∧ (inWin p (q3 w) → ¬ inWin p (q4 w)) := by
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

/-- `Collect` from the report, with a fuel budget on the recursion depth.
Returns the listings found and the leaf windows, or `none` if fuel runs out. -/
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

/-! ## Theorem 1: partial correctness -/

theorem mem_listingsIn (a : α) (w : Window) :
    a ∈ listingsIn P loc w ↔ a ∈ P ∧ inWin (loc a) w := by
  simp [listingsIn, List.mem_filter]

/-- What a non-overflowing oracle answer tells us. -/
theorem oracle_some {w : Window} {A : List α} (h : oracle P loc k w = some A) :
    A = listingsIn P loc w ∧ (listingsIn P loc w).length ≤ k := by
  unfold oracle at h
  split at h
  · cases h; exact ⟨rfl, by assumption⟩
  · cases h

/-- Correctness of a leaf: the oracle's answer is `P_w`, `w` is under the cap,
and `[w]` trivially covers `w`. -/
theorem leaf_correct {w : Window} {A : List α} (h : oracle P loc k w = some A) :
    (∀ a, a ∈ A ↔ a ∈ P ∧ inWin (loc a) w) ∧
    (∀ l ∈ [w], (listingsIn P loc l).length ≤ k) ∧
    (∀ p, inWin p w ↔ ∃ l ∈ [w], inWin p l) := by
  obtain ⟨rfl, hk⟩ := oracle_some P loc k h
  refine ⟨fun a => mem_listingsIn P loc a w, ?_, ?_⟩
  · intro l hl
    simp only [List.mem_singleton] at hl
    subst hl; exact hk
  · intro p; simp

/-- **Theorem 1.** If `collect` returns `(out, leaves)` then `out` is exactly the
listings in `w`, every leaf holds at most `k` listings, and the leaves cover `w`. -/
theorem collect_correct (fuel : Nat) :
    ∀ (w : Window) (out : List α) (leaves : List Window),
      collect P loc k fuel w = some (out, leaves) →
        (∀ a, a ∈ out ↔ a ∈ P ∧ inWin (loc a) w) ∧
        (∀ l ∈ leaves, (listingsIn P loc l).length ≤ k) ∧
        (∀ p, inWin p w ↔ ∃ l ∈ leaves, inWin p l) := by
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
        · intro a
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
          rw [quadrants_cover, v1, v2, v3, v4]
          simp only [List.mem_append, or_and_right, exists_or, or_assoc]
      · cases h

/-! ## Lemma 2 (on the grid): depth `⌈log₂ W⌉` suffices -/

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

/-- A window of side at most 1 contains at most one location, so under `CapOK`
the oracle never overflows on it. -/
theorem unit_window_fits (hcap : CapOK P loc k) (w : Window)
    (hx : w.x1 - w.x0 ≤ 1) (hy : w.y1 - w.y0 ≤ 1) :
    (listingsIn P loc w).length ≤ k := by
  refine Nat.le_trans (length_filter_le_of_imp P _ _ ?_) (hcap (w.x0, w.y0))
  intro a ha
  simp only [decide_eq_true_eq, inWin, Prod.ext_iff] at ha ⊢
  omega

/-- If the window's sides are at most `2^fuel`, `collect` with that much fuel
returns an answer. The quadrants of a window of side `≤ 2B` have side `≤ B`. -/
theorem collect_terminates (hcap : CapOK P loc k) (fuel : Nat) :
    ∀ w : Window, w.x1 - w.x0 ≤ (2 : Int) ^ fuel → w.y1 - w.y0 ≤ (2 : Int) ^ fuel →
      ∃ r, collect P loc k fuel w = some r := by
  induction fuel with
  | zero =>
    intro w hx hy
    simp only [Int.pow_zero] at hx hy
    have hfits := unit_window_fits P loc k hcap w hx hy
    refine ⟨(listingsIn P loc w, [w]), ?_⟩
    simp [collect, oracle, hfits]
  | succ fuel ih =>
    intro w hx hy
    rw [Int.pow_succ] at hx hy
    unfold collect
    split
    · exact ⟨_, rfl⟩
    · -- Each quadrant's sides are at most half the parent's, i.e. at most 2^fuel.
      obtain ⟨⟨o1, l1⟩, h1⟩ := ih (q1 w) (by simp only [q1]; omega) (by simp only [q1]; omega)
      obtain ⟨⟨o2, l2⟩, h2⟩ := ih (q2 w) (by simp only [q2]; omega) (by simp only [q2]; omega)
      obtain ⟨⟨o3, l3⟩, h3⟩ := ih (q3 w) (by simp only [q3]; omega) (by simp only [q3]; omega)
      obtain ⟨⟨o4, l4⟩, h4⟩ := ih (q4 w) (by simp only [q4]; omega) (by simp only [q4]; omega)
      rw [h1, h2, h3, h4]
      exact ⟨_, rfl⟩

/-- **Total correctness.** Under `m ≤ k`, on a window of side at most `2^D`,
`collect` with depth bound `D` returns the listings in the window, every leaf
is under the cap, and the leaves cover the window. -/
theorem collect_total (hcap : CapOK P loc k) (D : Nat) (w : Window)
    (hx : w.x1 - w.x0 ≤ (2 : Int) ^ D) (hy : w.y1 - w.y0 ≤ (2 : Int) ^ D) :
    ∃ out leaves, collect P loc k D w = some (out, leaves) ∧
      (∀ a, a ∈ out ↔ a ∈ P ∧ inWin (loc a) w) ∧
      (∀ l ∈ leaves, (listingsIn P loc l).length ≤ k) ∧
      (∀ p, inWin p w ↔ ∃ l ∈ leaves, inWin p l) := by
  obtain ⟨⟨out, leaves⟩, h⟩ := collect_terminates P loc k hcap D w hx hy
  exact ⟨out, leaves, h, collect_correct P loc k D w out leaves h⟩

end Quadtree
