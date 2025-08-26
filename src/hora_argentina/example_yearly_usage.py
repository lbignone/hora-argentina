#!/usr/bin/env python3
"""
Example usage of the yearly_sun_times_dataframe function

This script demonstrates how to use the function to get a full year of
sunrise and sunset times for all twilight definitions.
"""

from hora_argentina.noaa_solar_calculations import yearly_sun_times_dataframe


def main():
    """Demonstrate the yearly sun times dataframe function."""

    print("🌅 Yearly Sun Times DataFrame Example")
    print("=" * 50)

    # Example coordinates for Buenos Aires, Argentina
    latitude = -34.6118
    longitude = -58.3960
    timezone_offset = -3  # Argentina standard time (UTC-3)

    # Generate the dataframe for current year (default)
    df = yearly_sun_times_dataframe(latitude, longitude, timezone_offset)

    print(f"Coordinates: {latitude}°, {longitude}°")
    print(f"Timezone: UTC{timezone_offset:+d}")
    print(f"Year: {df.iloc[0]['date'].year} (current year)")
    print(f"Total days: {len(df)}")
    print()

    # Show the first few rows
    print("First 5 days of the year:")
    print(df.head().to_string(index=False))
    print()

    # Show summer solstice (Dec 21 in Southern Hemisphere)
    summer_solstice = df[
        df["date"].apply(lambda x: x.strftime("%m-%d") == "12-21")
    ].iloc[0]
    print("Summer Solstice (December 21st):")
    for col in df.columns:
        print(f"  {col}: {summer_solstice[col]}")
    print()

    # Show winter solstice (Jun 21 in Southern Hemisphere)
    winter_solstice = df[
        df["date"].apply(lambda x: x.strftime("%m-%d") == "06-21")
    ].iloc[0]
    print("Winter Solstice (June 21st):")
    for col in df.columns:
        print(f"  {col}: {winter_solstice[col]}")
    print()

    print("Available columns:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")

    print("\nTwilight Definitions:")
    print("  - Official: Sun's center at horizon (-0.833°)")
    print("  - Civil: Sun 6° below horizon (-6°)")
    print("  - Nautical: Sun 12° below horizon (-12°)")
    print("  - Astronomical: Sun 18° below horizon (-18°)")

    print("\nNote: All times are returned as decimal hours (e.g., 5.75 = 5:45 AM)")


if __name__ == "__main__":
    main()
