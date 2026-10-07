from pathlib import Path
from typing import Annotated, NamedTuple

from PIL import Image, ImageDraw
from PIL.Image import Resampling
from pydantic import Field, NonNegativeInt, dataclass

WEEKS_PER_YEAR = 52
UNITS_PER_INCH = 96  # CSS reference pixel

Probability = Annotated[float, Field(ge=0, le=1)]


@dataclass(frozen=True)
class Week:
    index: int
    p_alive: Probability
    survived: bool


@dataclass(frozen=True)
class GridSpec:
    cols: int = WEEKS_PER_YEAR
    step: int = 25
    radius: int = 10
    stroke_width: int = 2

    def center(self, i: int) -> tuple[int, int]:
        row, col = divmod(i, self.cols)
        return (col + 1) * self.step, (row + 1) * self.step


@dataclass(frozen=True)
class SurvivalRepresentation:
    weeks: list[Week]

    # TODO: what is the decorator again?
    def validate(self):
        was_alive = True
        last_p = 1
        for week in self.weeks:
            # survival probability should decrease
            assert week.p_alive <= last_p

            # jesus disallowed
            if not was_alive:
                assert not week.survived

            was_alive = week.survived
            last_p = week.p_alive


def _to_lstar(c: int) -> float:
    u: float = c / 255
    y = u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
    return 116 * y ** (1 / 3) - 16 if y > 0.008856 else 903.3 * y


def _from_lstar(lstar: float) -> int:
    y = ((lstar + 16) / 116) ** 3 if lstar > 8 else lstar / 903.3
    c = 12.92 * y if y <= 0.0031308 else 1.055 * y ** (1 / 2.4) - 0.055
    return round(min(max(c, 0.0), 1.0) * 255)


def cmap(t: , lightest: int = 0xFF, darkest: int = 0x00) -> str:
    """Perceptually uniform grey ramp: equal steps in `t` are equal steps in L*."""
    lo, hi = _to_lstar(lightest), _to_lstar(darkest)
    v: int = _from_lstar(lo + (hi - lo) * t)
    return f"#{v:02x}{v:02x}{v:02x}"


def write_svg(xml: str, path: str | Path) -> None:
    Path(path).write_text(xml, encoding="utf-8")


class Bubble(NamedTuple):
    x: int
    y: int
    color: str
    filled: bool


class SurvivalCalendar:
    """
    Generates a calendar showing probability of survival and current lifespan, in weeks.

    Parameters
    ----------
    num_weeks_survived: NonNegativeInt
        How many full weeks survived, which determines how many bubbles to fill

    survival_probabilities: list[float]
        The i-th element is the probability of surviving through week i.
        Must be 1 for the first `num_weeks_survived` elements, which were survived.

    Raises
    ------
    pydantic.ValidationError
        If any probability falls outside [0, 1].
    """

    def __init__(
        self, num_weeks_survived: NonNegativeInt, survival_probabilities: list[float]
    ):
        self.calendar_info = [
            Week(i, p_alive, i < num_weeks_survived)
            for i, p_alive in enumerate(survival_probabilities)
        ]

    @staticmethod
    def _xml_bubble(x: int, y: int, color: str, filled: bool) -> str:
        return (
            f'<use href="#{"x" if filled else "o"}" x="{x}" y="{y}" color="{color}"/>'
        )

    @staticmethod
    def _defs(radius: int, stroke_width: int) -> str:
        return (
            "<defs>"
            f'<circle id="o" r="{radius}" stroke-width="{stroke_width}" '
            'fill="none" stroke="currentColor"/>'
            f'<circle id="x" r="{radius}" stroke-width="{stroke_width}" '
            'fill="currentColor" stroke="currentColor"/>'
            "</defs>"
        )
        

    def generate_calendar(self, output_format = 'svg', **kwargs):
        assert output_format in ('web_svg', 'print_svg', 'png', 'csv')
        
        grid = GridSpec(**kwargs)

        xml_body = []
        for week in self.calendar_info:
            x, y = grid.center(week.index)
            color = cmap(week.p_alive)
            filled = week.survived

            xml_body.append(self._xml_bubble(x, y, color, filled))
        xml_body = "".join(xml_body)

        # now what?



    def _to_web_svg(
        self,
        xml_body,
        grid
    ) -> str:
        """Responsive, transparent SVG for embedding in a page."""
        width: int = ( + 1) * grid_step
        height: int = (num_rows + 1) * grid_step

        # TODO: this probably isn't the cleanest way to render it...
        # can we just grab the biggest y value based on teh number of bubbles (?)
        xml_body
        grid.cols

        return (
            f'<svg version="1.1" viewBox="0 0 {width} {height}" '
            'xmlns="http://www.w3.org/2000/svg">'
            f"{self._defs(radius, stroke_width)}"
            f"{self._body(num_rows, num_cols, grid_step)}"
            "</svg>"
        )

    def to_print_svg(
        self,
        radius: int,
        stroke_width: int,
        paper_width_in: float,
        paper_height_in: float,
        margin_in: float = 0.5,
        num_rows: int = 90,
        num_cols: int = WEEKS_PER_YEAR,
        grid_step: int = 25,
    ) -> str:
        """Fixed paper-size SVG with a white background and centred content."""
        content_w: int = (num_cols + 1) * grid_step
        content_h: int = (num_rows + 1) * grid_step

        page_w: float = paper_width_in * UNITS_PER_INCH
        page_h: float = paper_height_in * UNITS_PER_INCH
        m: float = margin_in * UNITS_PER_INCH

        return (
            '<?xml version="1.0" encoding="utf-8"?>'
            f'<svg version="1.1" width="{paper_width_in}in" height="{paper_height_in}in" '
            f'viewBox="0 0 {page_w:g} {page_h:g}" '
            'xmlns="http://www.w3.org/2000/svg">'
            '<rect width="100%" height="100%" fill="white"/>'
            f"{self._defs(radius, stroke_width)}"
            f'<svg x="{m:g}" y="{m:g}" '
            f'width="{page_w - 2 * m:g}" height="{page_h - 2 * m:g}" '
            f'viewBox="0 0 {content_w} {content_h}" preserveAspectRatio="xMidYMid meet">'
            f"{self._body(num_rows, num_cols, grid_step)}"
            "</svg></svg>"
        )

    def to_png(
        self,
        path: str | Path,
        radius: int,
        stroke_width: int,
        dpi: int = 300,
        supersample: int = 2,
        num_rows: int = 90,
        num_cols: int = WEEKS_PER_YEAR,
        grid_step: int = 25,
    ) -> None:
        """Rasterise the grid directly. `supersample` buys antialiasing."""
        width: int = (num_cols + 1) * grid_step
        height: int = (num_rows + 1) * grid_step
        s: float = (dpi / UNITS_PER_INCH) * supersample

        img = Image.new("RGB", (round(width * s), round(height * s)), "white")
        draw = ImageDraw.Draw(img)
        line_w: int = max(1, round(stroke_width * s))

        for b in self._bubbles(num_rows, num_cols, grid_step):
            draw.ellipse(
                (
                    (b.x - radius) * s,
                    (b.y - radius) * s,
                    (b.x + radius) * s,
                    (b.y + radius) * s,
                ),
                fill=b.color if b.filled else None,
                outline=b.color,
                width=line_w,
            )

        if supersample > 1:
            img = img.resize(
                (
                    round(width * s / supersample),
                    round(height * s / supersample),
                ),
                resample=Resampling.LANCZOS,
            )

        img.save(path, dpi=(dpi, dpi))
