from PIL import Image, ImageDraw, ImageFont

def render_occupancy(stats, latest_date, output_path="occupancy.png"):
    width, height = 800, 400
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    # falls back to default bitmap font if no TTF is found — swap in a real
    # font path for anything you actually want to look good
    try:
        font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 24)
    except OSError:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text((20, 20), f"Shelter Occupancy — {latest_date}", fill="black", font=font_large)

    draw.text(
        (20, 100),
        f"Beds: {stats['bed_occupied']:.0f} / {stats['bed_capacity']:.0f} ({stats['bed_occupancy_rate']}%)",
        fill="black",
        font=font_small,
    )
    draw.text(
        (20, 150),
        f"Rooms: {stats['room_occupied']:.0f} / {stats['room_capacity']:.0f} ({stats['room_occupancy_rate']}%)",
        fill="black",
        font=font_small,
    )

    img.save(output_path)
    img.show()


if __name__ == "__main__":
    # example usage with the calculate_occupancy() output from before
    stats = {
        "bed_occupied": 4200,
        "bed_capacity": 4500,
        "bed_occupancy_rate": 93.33,
        "room_occupied": 300,
        "room_capacity": 320,
        "room_occupancy_rate": 93.75,
    }
    render_occupancy(stats, "2026-09-21")