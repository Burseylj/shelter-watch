from PIL import Image, ImageDraw, ImageFont

def render_occupancy(stats, latest_date, output_path="occupancy.png"):
    width, height = 1080, 1080
    img = Image.new("RGB", (width, height), color="white")
    draw = ImageDraw.Draw(img)

    try:
        font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 48)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 36)
    except OSError:
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
    return output_path