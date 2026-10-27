/-!
# Fewest refresh days: machine-checked correctness of `Refresh-Days`

Formalizes Section II-D of the report. Days are integers and a window is a
pair `(a, b)` with `a ≤ b`, meaning the days `a, …, b`. Only Lean's core
library is used; arithmetic steps are discharged by `omega`.

| Report    | Lean                          |
|-----------|-------------------------------|
| Lemma 1   | `refresh_covers`              |
| Lemma 2   | `witnesses_pairwise_disjoint` |
| Theorem 1 | `refresh_optimal`             |

`refresh` is the scan of Fig. 1 on a list already sorted by closing day; it
returns the witnesses, and the refresh days are their closing days. The sort
and the running time (Theorem 2) are not formalized.
-/

namespace Refresh

/-- Day `t` lies in window `p`. -/
def hits (t : Int) (p : Int × Int) : Prop := p.1 ≤ t ∧ t ≤ p.2

/-- The test on line 5: `a > last`, where `none` stands for `last = -∞`. -/
def fresh : Option Int → Int → Bool
  | none, _ => true
  | some l, a => decide (l < a)

/-- The scan of Fig. 1, carrying `last`. Returns the witnesses in order. -/
def refresh : Option Int → List (Int × Int) → List (Int × Int)
  | _, [] => []
  | last, p :: ps => if fresh last p.1 then p :: refresh (some p.2) ps else refresh last ps

/-- The refresh days: one per witness, its closing day. -/
def days (l : List (Int × Int)) : List Int := (refresh none l).map Prod.snd

/-- Every witness is one of the input windows. -/
theorem refresh_sub : ∀ (l : List (Int × Int)) (last : Option Int),
    ∀ w ∈ refresh last l, w ∈ l := by
  intro l
  induction l with
  | nil => intro last w hw; simp [refresh] at hw
  | cons p ps ih =>
    intro last w hw
    simp only [refresh] at hw
    split at hw
    · rcases List.mem_cons.1 hw with rfl | hw
      · exact List.mem_cons_self
      · exact List.mem_cons_of_mem _ (ih _ w hw)
    · exact List.mem_cons_of_mem _ (ih _ w hw)

/-! ## Lemma 1: every window is covered -/

/-- The invariant behind Lemma 1: if `last` is at most every remaining closing
day, every remaining window holds `last` or the closing day of a witness. -/
theorem covers_aux : ∀ (l : List (Int × Int)) (last : Option Int),
    l.Pairwise (fun p q => p.2 ≤ q.2) → (∀ p ∈ l, p.1 ≤ p.2) →
    (∀ L, last = some L → ∀ p ∈ l, L ≤ p.2) →
    ∀ q ∈ l, (∃ L, last = some L ∧ hits L q) ∨ ∃ w ∈ refresh last l, hits w.2 q := by
  intro l
  induction l with
  | nil => intro last _ _ _ q hq; simp at hq
  | cons p ps ih =>
    intro last hs hwf hL q hq
    rw [List.pairwise_cons] at hs
    have hwf' : ∀ r ∈ ps, r.1 ≤ r.2 := fun r hr => hwf r (List.mem_cons_of_mem _ hr)
    have hp : p.1 ≤ p.2 := hwf p List.mem_cons_self
    simp only [refresh]
    split
    · -- `a > last`: the scan adds `p.2` and continues with `last = p.2`.
      rcases List.mem_cons.1 hq with rfl | hq'
      · exact Or.inr ⟨q, List.mem_cons_self, hp, Int.le_refl _⟩
      · have hL' : ∀ L, some p.2 = some L → ∀ r ∈ ps, L ≤ r.2 := by
          intro L h r hr
          cases h
          exact hs.1 r hr
        rcases ih (some p.2) hs.2 hwf' hL' q hq' with ⟨L, h, hq2⟩ | ⟨w, hw, hq2⟩
        · cases h
          exact Or.inr ⟨p, List.mem_cons_self, hq2⟩
        · exact Or.inr ⟨w, List.mem_cons_of_mem _ hw, hq2⟩
    · -- `a ≤ last`: `last` already lies in `p`.
      next hf =>
      rcases List.mem_cons.1 hq with rfl | hq'
      · cases last with
        | none => simp [fresh] at hf
        | some L =>
          simp [fresh] at hf
          exact Or.inl ⟨L, rfl, hf, hL L rfl q List.mem_cons_self⟩
      · exact ih last hs.2 hwf' (fun L h r hr => hL L h r (List.mem_cons_of_mem _ hr)) q hq'

/-- **Lemma 1.** On input sorted by closing day, every window contains a
refresh day. -/
theorem refresh_covers (l : List (Int × Int))
    (hs : l.Pairwise (fun p q => p.2 ≤ q.2)) (hwf : ∀ p ∈ l, p.1 ≤ p.2) :
    ∀ q ∈ l, ∃ t ∈ days l, hits t q := by
  intro q hq
  rcases covers_aux l none hs hwf (by simp) q hq with ⟨L, h, _⟩ | ⟨w, hw, h⟩
  · cases h
  · exact ⟨w.2, List.mem_map.2 ⟨w, hw, rfl⟩, h⟩

/-! ## Lemma 2: the witnesses are pairwise disjoint -/

/-- Each witness opens after the previous one closes, and after `last`. -/
theorem refresh_separated : ∀ (l : List (Int × Int)) (last : Option Int),
    (∀ p ∈ l, p.1 ≤ p.2) →
    (refresh last l).Pairwise (fun w v => w.2 < v.1) ∧
      ∀ L, last = some L → ∀ w ∈ refresh last l, L < w.1 := by
  intro l
  induction l with
  | nil => intro last _; simp [refresh]
  | cons p ps ih =>
    intro last hwf
    have hwf' : ∀ r ∈ ps, r.1 ≤ r.2 := fun r hr => hwf r (List.mem_cons_of_mem _ hr)
    have hp : p.1 ≤ p.2 := hwf p List.mem_cons_self
    simp only [refresh]
    split
    · next hf =>
      obtain ⟨hpw, hlt⟩ := ih (some p.2) hwf'
      refine ⟨List.pairwise_cons.2 ⟨fun v hv => hlt p.2 rfl v hv, hpw⟩, ?_⟩
      intro L h w hw
      cases h
      simp [fresh] at hf
      rcases List.mem_cons.1 hw with rfl | hw
      · exact hf
      · have := hlt p.2 rfl w hw
        omega
    · exact ih last hwf'

/-- **Lemma 2.** No day lies in two witnesses. -/
theorem witnesses_pairwise_disjoint (l : List (Int × Int)) (hwf : ∀ p ∈ l, p.1 ≤ p.2) :
    (refresh none l).Pairwise (fun w v => ∀ t, ¬ (hits t w ∧ hits t v)) :=
  (refresh_separated l none hwf).1.imp fun h t ⟨⟨_, h1⟩, ⟨h2, _⟩⟩ => by omega

/-! ## Theorem 1: no set of days that hits every window is smaller -/

/-- Pairwise disjoint windows that are all hit by `T` need `|T|` at least
their number: each needs a day of its own. -/
theorem disjoint_le (W : List (Int × Int)) :
    W.Pairwise (fun w v => ∀ t, ¬ (hits t w ∧ hits t v)) →
    ∀ T : List Int, (∀ w ∈ W, ∃ t ∈ T, hits t w) → W.length ≤ T.length := by
  induction W with
  | nil => intros; simp
  | cons w ws ih =>
    intro hd T hT
    rw [List.pairwise_cons] at hd
    obtain ⟨t, ht, htw⟩ := hT w List.mem_cons_self
    -- The day `t` serves `w` only, so the rest are hit by `T` without `t`.
    have hrest : ∀ v ∈ ws, ∃ s ∈ T.erase t, hits s v := by
      intro v hv
      obtain ⟨s, hs, hsv⟩ := hT v (List.mem_cons_of_mem _ hv)
      have hne : s ≠ t := by
        rintro rfl
        exact hd.1 v hv s ⟨htw, hsv⟩
      exact ⟨s, (List.mem_erase_of_ne hne).2 hs, hsv⟩
    have := ih hd.2 (T.erase t) hrest
    rw [List.length_erase_of_mem ht] at this
    have := List.length_pos_of_mem ht
    simp only [List.length_cons]
    omega

/-- **Theorem 1.** Every list of days that hits every window is at least as
long as the list `refresh` returns. -/
theorem refresh_optimal (l : List (Int × Int))
    (hwf : ∀ p ∈ l, p.1 ≤ p.2) (T : List Int) (hT : ∀ p ∈ l, ∃ t ∈ T, hits t p) :
    (days l).length ≤ T.length := by
  rw [days, List.length_map]
  exact disjoint_le _ (witnesses_pairwise_disjoint l hwf) T
    (fun w hw => hT w (refresh_sub l none w hw))

end Refresh
