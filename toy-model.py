from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple
import random


ALPHABET = "ABCDE"
TARGET = "ABCDEABCDE"
RNG = random.Random(7)


@dataclass
class Structure:
    """
    A toy lineage-bearing structure for demonstrating nested recursive/
    recombinant generativity.

    - genome: symbolic substrate
    - lineage: ancestry trail showing recursive carry-forward
    - history: compact log of operations performed
    """

    genome: str
    lineage: Tuple[str, ...] = field(default_factory=tuple)
    history: Tuple[str, ...] = field(default_factory=tuple)

    def with_update(self, genome: str, event: str) -> "Structure":
        return Structure(
            genome=genome,
            lineage=self.lineage + (self.genome,),
            history=self.history + (event,),
        )


# -----------------------------
# Metrics / constraints
# -----------------------------

def coherence(s: Structure) -> float:
    """
    Coherence rewards local repetition and partial target order.
    This acts as a stabilization pressure.
    """
    score = 0.0
    for i, ch in enumerate(s.genome):
        if i > 0 and s.genome[i - 1] == ch:
            score += 0.4
        if i < len(TARGET) and ch == TARGET[i]:
            score += 1.0
    return score / max(len(s.genome), 1)


def novelty(s: Structure, pool: List[Structure]) -> float:
    """
    Novelty is measured as average Hamming distance from the current pool.
    Higher = more different from peers.
    """
    if not pool:
        return 0.0

    def distance(a: str, b: str) -> int:
        return sum(x != y for x, y in zip(a, b))

    return sum(distance(s.genome, other.genome) for other in pool) / (len(pool) * len(s.genome))


def fitness(s: Structure, pool: List[Structure]) -> float:
    """
    A simple viability score balancing recursive stabilization and
    recombinant exploration.
    """
    c = coherence(s)
    n = novelty(s, pool)
    # Balanced systems do best: enough coherence to survive, enough novelty to matter.
    return (0.65 * c) + (0.35 * n)


# -----------------------------
# Recursive operator
# -----------------------------

def recursive_refine(s: Structure) -> Structure:
    """
    Recursive generativity:
    reapply local self-return and inherited target pressure.

    This operator uses the current structure as the basis for its next state.
    """
    chars = list(s.genome)
    i = RNG.randrange(len(chars))

    # 50% chance: move toward target at the chosen position.
    if RNG.random() < 0.5:
        chars[i] = TARGET[i]
        return s.with_update("".join(chars), f"recursive:align@{i}")

    # 50% chance: reinforce a neighboring local pattern.
    if i > 0:
        chars[i] = chars[i - 1]
    elif i < len(chars) - 1:
        chars[i] = chars[i + 1]
    return s.with_update("".join(chars), f"recursive:repeat@{i}")


# -----------------------------
# Recombinant operator
# -----------------------------

def recombine(a: Structure, b: Structure) -> Structure:
    """
    Recombinant generativity:
    compose two independently specifiable sources into a new hybrid.
    """
    cut1 = RNG.randrange(1, len(a.genome) - 1)
    cut2 = RNG.randrange(cut1, len(a.genome) - 1)
    child = a.genome[:cut1] + b.genome[cut1:cut2] + a.genome[cut2:]

    # Small optional twist to avoid sterile copy-paste.
    if RNG.random() < 0.25:
        j = RNG.randrange(len(child))
        child = child[:j] + RNG.choice(ALPHABET) + child[j + 1 :]
        event = f"recombine:{cut1}-{cut2}+mut@{j}"
    else:
        event = f"recombine:{cut1}-{cut2}"

    return Structure(
        genome=child,
        lineage=(a.genome, b.genome),
        history=(event,),
    )


# -----------------------------
# Modulation layer (toy MEA-like governor)
# -----------------------------

def choose_mode(pool: List[Structure]) -> str:
    """
    A toy governor that decides whether the population needs more:
    - recursive stabilization (when coherence is too low)
    - recombinant diversification (when novelty is too low)

    This is a very small sketch of the kind of balancing layer needed
    to keep nested generativity from collapsing into either lock or noise.
    """
    avg_coh = sum(coherence(s) for s in pool) / len(pool)
    avg_nov = sum(novelty(s, pool) for s in pool) / len(pool)

    if avg_coh < 0.48:
        return "recursive"
    if avg_nov < 0.42:
        return "recombinant"
    return "nested"


# -----------------------------
# Population cycle
# -----------------------------

def seed_population(size: int = 8, width: int = 10) -> List[Structure]:
    return [
        Structure("".join(RNG.choice(ALPHABET) for _ in range(width)))
        for _ in range(size)
    ]


def select_top(pool: List[Structure], size: int) -> List[Structure]:
    ranked = sorted(pool, key=lambda s: fitness(s, pool), reverse=True)
    return ranked[:size]


def generation_step(pool: List[Structure]) -> Tuple[List[Structure], str]:
    mode = choose_mode(pool)
    candidates: List[Structure] = []

    if mode == "recursive":
        # Deepen existing lineages.
        for s in pool:
            candidates.append(recursive_refine(s))
            candidates.append(recursive_refine(recursive_refine(s)))

    elif mode == "recombinant":
        # Hybridize across distinct sources.
        for _ in range(len(pool) * 2):
            a, b = RNG.sample(pool, 2)
            candidates.append(recombine(a, b))

    else:
        # Nested mode:
        # 1) recursively mature structures,
        # 2) recombine matured structures,
        # 3) recursively stabilize the hybrids.
        matured = [recursive_refine(s) for s in pool]
        candidates.extend(matured)
        for _ in range(len(pool)):
            a, b = RNG.sample(matured, 2)
            hybrid = recombine(a, b)
            stabilized = recursive_refine(hybrid)
            candidates.append(stabilized)

    next_pool = select_top(pool + candidates, len(pool))
    return next_pool, mode


# -----------------------------
# Demo runner
# -----------------------------

def summarize(pool: List[Structure], generation: int, mode: str) -> None:
    best = max(pool, key=lambda s: fitness(s, pool))
    avg_coh = sum(coherence(s) for s in pool) / len(pool)
    avg_nov = sum(novelty(s, pool) for s in pool) / len(pool)

    print(f"Generation {generation:02d} | mode={mode}")
    print(f"  best genome   : {best.genome}")
    print(f"  best fitness  : {fitness(best, pool):.3f}")
    print(f"  avg coherence : {avg_coh:.3f}")
    print(f"  avg novelty   : {avg_nov:.3f}")
    print(f"  best history  : {list(best.history[-4:])}")
    print()


def run_demo(generations: int = 12) -> None:
    pool = seed_population()
    summarize(pool, 0, "seed")

    for gen in range(1, generations + 1):
        pool, mode = generation_step(pool)
        summarize(pool, gen, mode)

    best = max(pool, key=lambda s: fitness(s, pool))
    print("Final best structure")
    print("--------------------")
    print(f"Genome : {best.genome}")
    print(f"Lineage: {best.lineage[-5:] if len(best.lineage) > 5 else best.lineage}")
    print(f"History: {best.history}")


if __name__ == "__main__":
    run_demo()
