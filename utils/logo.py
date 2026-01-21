from dataclasses import dataclass
from typing import Tuple, Literal
from rich.text import Text

GradientMode = Literal["horizontal", "vertical", "none"]
PresetMode = Literal["orion", "sunset", "matrix", "ice"]

PRESETS = {
    "orion": ((138, 43, 226), (0, 255, 255)),
    "sunset": ((255, 94, 77), (255, 195, 113)),
    "matrix": ((0, 255, 0), (0, 128, 0)),
    "ice": ((180, 240, 255), (80, 180, 255)),
}


@dataclass
class ColorConfig:
    start: Tuple[int, int, int] = PRESETS["orion"][0]
    end: Tuple[int, int, int] = PRESETS["orion"][1]
    mode: GradientMode = "horizontal"
    enabled: bool = True


def color_char(ch, rgb):
    r, g, b = rgb
    return f"\033[38;2;{r};{g};{b}m{ch}"


def _lerp(a, b, t):
    return a + (b - a) * t


def _interpolate(c1, c2, t):
    return tuple(int(_lerp(c1[i], c2[i], t)) for i in range(3))


def _make_logo(lines: list[str], cfg: ColorConfig):
    if not cfg.enabled or cfg.mode == "none":
        return "\n".join(lines)

    match cfg.mode:
        case "vertical":
            h = max(len(lines) - 1, 1)
            out = ""
            for i, line in enumerate(lines):
                t = i / h
                color = _interpolate(cfg.start, cfg.end, t)
                out += "".join(color_char(c, color) for c in line) + "\033[0m"
            return out
        case "horizontal":
            out = []
            for line in lines:
                w = max(len(line) - 1, 1)
                _line = []
                for i, ch in enumerate(line):
                    t = i / w
                    color = _interpolate(cfg.start, cfg.end, t)
                    _line.append(color_char(ch, color))
                out.append("".join(_line))
            return "\n".join(out) + "\033[0m"


def _make_logo_text(lines: list[str], cfg: ColorConfig) -> Text:
    text = Text()
    if not cfg.enabled or cfg.mode == "none":
        return Text("\n".join(lines))

    if cfg.mode == "vertical":
        h = max(len(lines) - 1, 1)
        for i, line in enumerate(lines):
            t = i / h
            color = _interpolate(cfg.start, cfg.end, t)
            text.append(line + "\n", style=f"rgb({color[0]},{color[1]},{color[2]})")

    else:  # horizontal
        for line in lines:
            w = max(len(line) - 1, 1)
            for i, ch in enumerate(line):
                t = i / w
                color = _interpolate(cfg.start, cfg.end, t)
                text.append(ch, style=f"rgb({color[0]},{color[1]},{color[2]})")
            text.append("\n")

    return text


def preset(name: PresetMode, mode: GradientMode = "horizontal"):
    s, e = PRESETS[name]
    return ColorConfig(start=s, end=e, mode=mode)


orion_logo = [
    "██████╗ ██████╗ ██╗ ██████╗ ███╗   ██╗",
    "██╔═══██╗██╔══██╗██║██╔═══██╗████╗  ██║",
    "██║   ██║██████╔╝██║██║   ██║██╔██╗ ██║",
    "██║   ██║██╔══██╗██║██║   ██║██║╚██╗██║",
    "╚██████╔╝██║  ██║██║╚██████╔╝██║ ╚████║",
    " ╚═════╝ ╚═╝  ╚═╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝",
    "               O R I O N",
]


_preset: PresetMode = "sunset"
logo = _make_logo(
    orion_logo,
    preset(_preset),
)

rich_logo_text = _make_logo_text(
    orion_logo,
    preset(_preset),
)
