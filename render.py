import logging
from datetime import datetime

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from fetch import OccupancyStats  # noqa: E402
from monthly_fetch import MonthReport  # noqa: E402

logger = logging.getLogger(__name__)

COLOR_SURFACE = "#fcfcfb"
COLOR_INK_PRIMARY = "#0b0b0b"
COLOR_INK_SECONDARY = "#52514e"
COLOR_INK_MUTED = "#898781"
COLOR_GRIDLINE = "#e1e0d9"
COLOR_BASELINE = "#c3c2b7"
COLOR_SERIES_BED = "#2a78d6"
COLOR_SERIES_ROOM = "#eb6834"
COLOR_SERIES_UNMATCHED = "#2a78d6"


# ---------------------------------------------------------------------------
# Daily occupancy post
# ---------------------------------------------------------------------------

def render_occupancy(stats: OccupancyStats, latest_date: str, output_path: str = "occupancy.png") -> str:
    logger.info(f"Rendering occupancy image for {latest_date}")

    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 36)
    except OSError:
        logger.warning("DejaVu fonts not found, falling back to default bitmap font")
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((40, 60), f"Shelter Occupancy — {latest_date}", fill="black", font=font_large)

    draw.text(
        (40, 300),
        f"Beds: {stats['bed_occupied']:.0f} / {stats['bed_capacity']:.0f} ({stats['bed_occupancy_rate']}%)",
        fill="black",
        font=font_small,
    )
    draw.text(
        (40, 400),
        f"Rooms: {stats['room_occupied']:.0f} / {stats['room_capacity']:.0f} ({stats['room_occupancy_rate']}%)",
        fill="black",
        font=font_small,
    )

    img.save(output_path)
    logger.info(f"Saved occupancy image to {output_path}")
    return output_path


def render_trend_graph(history: list[tuple[str, OccupancyStats]], output_path: str = "trend.png") -> str:
    logger.info(f"Rendering trend graph with {len(history)} data points")

    if not history:
        raise ValueError("Cannot render trend graph with no history data")

    history = sorted(history, key=lambda h: h[0])

    dates = [datetime.strptime(date, "%Y-%m-%d") for date, _ in history]
    rates = [stats["room_occupancy_rate"] for _, stats in history]

    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100)
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")

    ax.fill_between(dates, rates, color="#2a78d6", alpha=0.25, linewidth=0)
    ax.plot(dates, rates, color="#2a78d6", linewidth=2, solid_capstyle="round")

    ax.axhline(100, color="#898781", linewidth=1)
    ax.text(dates[0], 101, "Capacity", color="#898781", fontsize=14, va="bottom")

    ax.set_ylim(90, max(100, max(rates) * 1.01))

    ax.set_title(
        f"Room Occupancy — Last {len(history)} Days",
        fontsize=28,
        color="#0b0b0b",
        pad=30,
        loc="left",
    )
    ax.grid(axis="y", color="#e1e0d9", linewidth=1)
    ax.set_axisbelow(True)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#c3c2b7")

    ax.tick_params(axis="both", colors="#898781", labelsize=16)
    ax.yaxis.set_major_formatter(lambda y, _: f"{y:.0f}%")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=6))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

    plt.tight_layout()
    fig.savefig(output_path, facecolor=fig.get_facecolor())
    plt.close(fig)

    logger.info(f"Saved trend graph to {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# Monthly unmatched-callers post
# ---------------------------------------------------------------------------

def month_label(month: str) -> str:
    return datetime.strptime(month, "%Y-%m").strftime("%B %Y")


def percent_change(new: float, old: float) -> float | None:
    if not old:
        return None
    return round((new - old) / old * 100, 1)


def change_text(pct: float) -> str:
    if pct > 0:
        return f"▲ {pct:.1f}%"
    if pct < 0:
        return f"▼ {abs(pct):.1f}%"
    return "— 0.0%"


def render_month_card(report: MonthReport, output_path: str = "monthly-card.png") -> str:
    stats = report["stats"]
    logger.info(f"Rendering monthly card for {stats['month']}")

    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 36)
    except OSError:
        logger.warning("DejaVu fonts not found, falling back to default bitmap font")
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text(
        (40, 60), f"Central Intake — {month_label(stats['month'])}", fill="black", font=font_large
    )
    draw.text(
        (40, 300),
        f"Unmatched callers per day (average): {stats['avg_per_day']:.0f}",
        fill="black",
        font=font_small,
    )

    y = 400
    for other in (report["previous"], report["year_ago"]):
        if other is None:
            continue
        pct = percent_change(stats["avg_per_day"], other["avg_per_day"])
        if pct is None:
            continue
        draw.text(
            (40, y),
            f"vs {month_label(other['month'])}: {pct:+.1f}% ({other['avg_per_day']:.1f} per day)",
            fill="black",
            font=font_small,
        )
        y += 100

    draw.text(
        (40, 650),
        f"{stats['unmatched']:,} unmatched callers over {stats['days']} days",
        fill="black",
        font=font_small,
    )
    draw.text(
        (40, 950), "Source: City of Toronto Open Data", fill="black", font=font_small
    )

    img.save(output_path)
    logger.info(f"Saved monthly card to {output_path}")
    return output_path


def render_month_daily_chart(report: MonthReport, output_path: str = "monthly-daily.png") -> str:
    stats = report["stats"]
    logger.info(f"Rendering daily chart for {stats['month']} with {len(report['daily'])} days")

    dates = [datetime.strptime(d, "%Y-%m-%d") for d, _ in report["daily"]]
    values = [v for _, v in report["daily"]]

    fig, ax = plt.subplots(figsize=(10.8, 10.8), dpi=100)
    fig.patch.set_facecolor(COLOR_SURFACE)
    ax.set_facecolor(COLOR_SURFACE)

    ax.bar(dates, values, width=0.8, color=COLOR_SERIES_UNMATCHED)

    avg = stats["avg_per_day"]
    ax.axhline(avg, color=COLOR_INK_PRIMARY, linewidth=1.2)
    ax.annotate(
        f"Average {avg:.0f}",
        (dates[-1], avg),
        xytext=(0, 6),
        textcoords="offset points",
        ha="right",
        fontsize=16,
        color=COLOR_INK_PRIMARY,
        bbox={"facecolor": COLOR_SURFACE, "edgecolor": "none", "pad": 2},
    )

    peak = values.index(max(values))
    ax.annotate(
        str(values[peak]),
        (dates[peak], values[peak]),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        fontsize=16,
        color=COLOR_INK_PRIMARY,
    )

    ax.set_ylim(0, max(values) * 1.15)
    ax.set_title(
        f"Unmatched callers per day\n{month_label(stats['month'])}",
        fontsize=28,
        color=COLOR_INK_PRIMARY,
        pad=30,
        loc="left",
    )
    ax.grid(axis="y", color=COLOR_GRIDLINE, linewidth=1)
    ax.set_axisbelow(True)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color(COLOR_BASELINE)

    ax.tick_params(axis="both", colors=COLOR_INK_MUTED, labelsize=16)
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 8, 15, 22, 29]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))

    plt.tight_layout()
    fig.savefig(output_path, facecolor=fig.get_facecolor())
    plt.close(fig)

    logger.info(f"Saved daily chart to {output_path}")
    return output_path