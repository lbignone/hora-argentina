#!/usr/bin/env python3
"""
Example usage of the sunrise/sunset API functions.
"""

from datetime import date, timedelta

from src.hora_argentina.from_api import (
    get_sunrise_sunset_data,
    get_sunrise_sunset_range,
    get_sunrise_sunset_today,
)


def main():
    """Demonstrate the sunrise/sunset API functions."""

    print("🌅 Sunrise/Sunset API Demo")
    print("=" * 50)

    # Buenos Aires coordinates
    ba_lat, ba_lng = -34.6037, -58.3816
    ba_timezone = "America/Argentina/Buenos_Aires"

    # New York coordinates
    ny_lat, ny_lng = 40.7128, -74.0060
    ny_timezone = "America/New_York"

    # 1. Get today's data for Buenos Aires
    print("\n1. Today's sunrise/sunset in Buenos Aires:")
    df_ba_today = get_sunrise_sunset_today(ba_lat, ba_lng, ba_timezone)
    print(f"   Sunrise: {df_ba_today.iloc[0]['sunrise']}")
    print(f"   Sunset:  {df_ba_today.iloc[0]['sunset']}")
    print(f"   Day length: {df_ba_today.iloc[0]['day_length']}")

    # 2. Compare with New York
    print("\n2. Today's sunrise/sunset in New York:")
    df_ny_today = get_sunrise_sunset_today(ny_lat, ny_lng, ny_timezone)
    print(f"   Sunrise: {df_ny_today.iloc[0]['sunrise']}")
    print(f"   Sunset:  {df_ny_today.iloc[0]['sunset']}")
    print(f"   Day length: {df_ny_today.iloc[0]['day_length']}")

    # 3. Get a week of data
    print("\n3. Next 7 days for Buenos Aires:")
    today = date.today()
    week_later = today + timedelta(days=6)

    df_week = get_sunrise_sunset_range(
        ba_lat, ba_lng, start_date=today, end_date=week_later, timezone=ba_timezone
    )

    for _, row in df_week.iterrows():
        print(
            f"   {row['date'].strftime('%Y-%m-%d')}: "
            f"Sunrise {row['sunrise']}, Sunset {row['sunset']}"
        )

    # 4. Show different time formats
    print("\n4. Different time formats (UTC):")

    # 12-hour format
    df_12h = get_sunrise_sunset_data(ba_lat, ba_lng, "UTC", time_format="12")
    print(
        f"   12-hour: Sunrise {df_12h.iloc[0]['sunrise']}, "
        f"Sunset {df_12h.iloc[0]['sunset']}"
    )

    # 24-hour format
    df_24h = get_sunrise_sunset_data(ba_lat, ba_lng, "UTC", time_format="24")
    print(
        f"   24-hour: Sunrise {df_24h.iloc[0]['sunrise']}, "
        f"Sunset {df_24h.iloc[0]['sunset']}"
    )

    # Unix timestamp
    df_unix = get_sunrise_sunset_data(ba_lat, ba_lng, "UTC", time_format="unix")
    print(
        f"   Unix:    Sunrise {df_unix.iloc[0]['sunrise']}, "
        f"Sunset {df_unix.iloc[0]['sunset']}"
    )

    # 5. Show full DataFrame info
    print("\n5. Full DataFrame structure:")
    print(f"   Columns: {list(df_ba_today.columns)}")
    print("   Data types:")
    for col in df_ba_today.columns:
        print(f"     {col}: {df_ba_today[col].dtype}")

    print("\n✅ Demo completed successfully!")
    print("\nPowered by SunriseSunset.io - https://sunrisesunset.io/")


if __name__ == "__main__":
    main()
