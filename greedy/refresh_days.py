"""Fewest price-refresh batches that observe every quote window (greedy).

Carnival's cruise search is an unofficial, rate-limited endpoint, so a fare
tracker should call it as rarely as it can. One refresh batch queries every
configured departure month and follows every page, so it observes the current
price of every listed sailing. A quote request asks for at least one fresh
observation of its sailing somewhere in a window of days; the tracker must
satisfy every request with as few batches as possible.

Abstraction: n integer intervals [a_i, b_i]. Choose a set T of days such that
every interval contains a day of T, with |T| minimum (minimum point cover of
intervals, also called interval stabbing).
"""

FINAL_PAYMENT_SHORT = 76  # days before departure, cruises of 5 nights or fewer
FINAL_PAYMENT_LONG = 91  # days before departure, cruises of 6 nights or more


def final_payment_days(nights):
    """Carnival's final-payment deadline, in days before departure."""
    return FINAL_PAYMENT_SHORT if nights <= 5 else FINAL_PAYMENT_LONG


def windows(sailings, today, c=2):
    """Quote windows for `sailings` as (a, b) day offsets from `today`.

    Each row has `departure` (a date) and `nights` (an int). The window runs
    from the final-payment deadline to booking close, c days before departure.
    Windows that closed before today are dropped; open ones start no earlier
    than today (offset 0), since a refresh cannot happen in the past.
    """
    out = []
    for s in sailings:
        d = (s["departure"] - today).days
        a, b = d - final_payment_days(s["nights"]), d - c
        if a > b:
            raise ValueError(f"empty window for {s}: c={c} is too large")
        if b >= 0:
            out.append((max(a, 0), b))
    return out


def refresh_days(intervals):
    """Return (days, witnesses): a minimum set of days hitting every interval.

    Scan the intervals by closing day. Whenever one is not yet hit, refresh on
    its last day, which hits it and as many later-closing intervals as any
    single day could. The intervals that forced a refresh are the witnesses;
    they are pairwise disjoint, which is why no smaller set of days exists.
    """
    for a, b in intervals:
        if a > b:
            raise ValueError(f"interval ({a}, {b}) has a > b")
    days, witnesses = [], []
    last = None  # most recent refresh day; None plays the role of -infinity
    for a, b in sorted(intervals, key=lambda w: w[1]):
        if last is None or a > last:
            days.append(b)
            witnesses.append((a, b))
            last = b
    return days, witnesses


def refresh_days_sorted(intervals):
    """The scan alone, for intervals already sorted by closing day (O(n))."""
    days, last = [], None
    for a, b in intervals:
        if last is None or a > last:
            days.append(b)
            last = b
    return days
