import logging
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

from fetch import OccupancyStats

logger = logging.getLogger(__name__)

def render_occupancy(stats: dict, latest_date: str, output_path: str = "occupancy.png") -> str:
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

COLOR_SURFACE = "#fcfcfb"
COLOR_INK_PRIMARY = "#0b0b0b"
COLOR_INK_SECONDARY = "#52514e"
COLOR_INK_MUTED = "#898781"
COLOR_GRIDLINE = "#e1e0d9"
COLOR_BASELINE = "#c3c2b7"
COLOR_SERIES_BED = "#2a78d6"   
COLOR_SERIES_ROOM = "#eb6834"

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

    ax.set_title("Room Occupancy — Last 30 Days", fontsize=28, color="#0b0b0b", pad=30, loc="left")
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