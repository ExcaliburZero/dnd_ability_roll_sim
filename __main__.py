from typing import cast, DefaultDict, Dict, List

import argparse
import collections
import enum
import math
import random
import sys

import numpy as np
import pandas as pd
import plotnine as plt9


def main(argv: List[str]) -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument("roll_rule", type=RollRule, choices=list(RollRule))
    parser.add_argument("--num_iterations", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--plot_file", default="ability_roll_distribution.png")

    args = parser.parse_args(argv)

    if args.seed is not None:
        random.seed(args.seed)

    # Run the simulation and process the data
    roll_counts = simulate(args.roll_rule, args.num_iterations)
    data = process_data(roll_counts)

    # Calculate statistics
    mean = sum(data["value"] * data["percent"] / 100.0)
    mode = data.iloc[data["count"].idxmax()]["value"]
    stddev = math.sqrt(sum(data["percent"] / 100.0 * (data["value"] - mean) ** 2.0))
    skewness = pearson_first_skewness(mean, mode, stddev)

    # Print out result information
    print(data)
    print()
    print("Mean:", mean)
    print("Mode:", mode)
    print("Standard deviation:", stddev)
    print("Skewness:", skewness)

    # Plot the data
    plot = (
        plt9.ggplot(data, plt9.aes("value", "percent"))
        + plt9.geom_bar(stat="identity")
        + plt9.geom_vline(xintercept=mean, color="black")
        + plt9.xlim(0, 21)
        + plt9.ylab("Chance (%)")
        + plt9.xlab("Ability Score")
        + plt9.ggtitle(
            "Ability Score Distribution ({} iterations)".format(args.num_iterations)
        )
    )

    plot.save(args.plot_file, dpi=300)
    print("Wrote plot image to:", args.plot_file)


def pearson_first_skewness(mean: float, mode: float, stddev: float) -> float:
    # https://en.wikipedia.org/wiki/Skewness#Pearson's_first_skewness_coefficient_(mode_skewness)
    return (mean - mode) / stddev


def simulate(roll_rule: "RollRule", num_iterations: int) -> Dict[int, int]:
    roll_counts: DefaultDict[int, int] = collections.defaultdict(lambda: 0)
    for _ in range(0, num_iterations):
        roll = roll_ability_scores(roll_rule)
        assert len(roll) == 6

        for value in roll:
            assert 1 <= value <= 20
            roll_counts[value] += 1

    return dict(roll_counts)


def process_data(roll_counts: Dict[int, int]) -> pd.DataFrame:
    data = pd.DataFrame(
        sorted(roll_counts.items(), key=lambda i: i[0]), columns=["value", "count"]
    )

    total_num_rolls = sum(roll_counts.values())

    data["percent"] = (data["count"] / total_num_rolls) * 100.0

    return data


class RollRule(enum.Enum):
    SixDTwenty = "SixDTwenty"
    FourKeepThree = "FourKeepThree"
    ThreeDSix = "ThreeDSix"

    def __str__(self) -> "str":
        return cast(str, self.value)


def roll_ability_scores(roll_rule: RollRule) -> List[int]:
    values: List[int] = []
    if roll_rule == RollRule.SixDTwenty:
        return [random.randint(1, 20) for _ in range(0, 6)]
    elif roll_rule == RollRule.FourKeepThree:
        for _ in range(0, 6):
            four_values = [random.randint(1, 6) for _ in range(0, 4)]
            top_three = sorted(four_values, reverse=True)[:3]
            assert len(top_three) == 3

            value = sum(top_three)
            assert 3 <= value <= 18

            values.append(value)

        return values
    elif roll_rule == RollRule.ThreeDSix:
        for _ in range(0, 6):
            three_values = [random.randint(1, 6) for _ in range(0, 3)]

            value = sum(three_values)
            assert 3 <= value <= 18

            values.append(value)

        return values

    assert False


if __name__ == "__main__":
    main(sys.argv[1:])
