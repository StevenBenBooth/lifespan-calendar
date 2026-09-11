from typing import Annotated

from pydantic import Field, TypeAdapter

Probability = Annotated[float, Field(ge=0, le=1, strict=True)]  # preferred in v2
Probabilities = TypeAdapter(list[Probability])


WEEKS_PER_YEAR = 52


def bubble_coords(num_years, grid_step, weeks=WEEKS_PER_YEAR):
    for y in range(1, num_years + 1):
        for x in range(1, weeks + 1):
            yield (x * grid_step, y * grid_step)


class SurvivalCalendar:
    """
    Generates a calendar showing probabilty of survival and current lifespan, in weeks.

    Params
    ------
    num_weeks_survived: int
        How many full weeks survived, which determines how many bubbles to fill

    survival_probabilities: list[float]
        The i-th element is the probability of surviving through week i, conditioned on having survived `num_weeks_survived` already

    Raises
    ------

    """

    def __init__(self, num_weeks_survived: int, survival_probabilities: list[float]):
        pass


def generate_calendar(outname, radius, stroke_width, num_years=90, grid_step=25):
    width = (WEEKS_PER_YEAR + 1) * grid_step
    height = (num_years + 1) * grid_step

    prefix = (
        '<?xml version="1.0" encoding="utf-8" ?>'
        f'<svg baseProfile="full" version="1.1" width="{width}" height="{height}" '
        'xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink">'
        f'<defs><circle id="bubble" cx="0" cy="0" r="{radius}" '
        f'fill="white" stroke="black" stroke-width="{stroke_width}" /></defs>'
    )

    body = "".join(
        f'<use x="{x}" y="{y}" xlink:href="#bubble" />'
        for x, y in bubble_coords(num_years, grid_step)
    )

    with open(f"{outname}.svg", "w") as file:
        file.write(prefix + body + "</svg>")
