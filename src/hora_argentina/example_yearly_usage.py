#!/usr/bin/env python3
"""
Example usage of the yearly sunrise/sunset API function.
"""

from datetime import date

from hora_argentina import get_sunrise_sunset_year


def main():
    """Demonstrate the yearly sunrise/sunset API function."""

    print("🌅 Yearly Sunrise/Sunset API Demo")
    print("=" * 50)

    # New York coordinates
    ny_lat, ny_lng = 40.7128, -74.0060
    ny_timezone = "America/New_York"

    # Buenos Aires coordinates
    ba_lat, ba_lng = -34.6037, -58.3816
    ba_timezone = "America/Argentina/Buenos_Aires"

    # Get current year
    current_year = date.today().year

    print(f"\n1. Getting full year data for NYC ({current_year}):")
    df_ny = get_sunrise_sunset_year(ny_lat, ny_lng, current_year, ny_timezone)
    print(f"   📊 Dataset: {len(df_ny)} days ({df_ny.shape[1]} columns)")

    # Find extremes
    longest = df_ny.loc[df_ny["day_length_seconds"].idxmax()]
    shortest = df_ny.loc[df_ny["day_length_seconds"].idxmin()]

    print(
        f"   🌞 Longest day: {longest['date'].strftime('%B %d')} ({longest['day_length']})"
    )
    print(
        f"   🌚 Shortest day: {shortest['date'].strftime('%B %d')} ({shortest['day_length']})"
    )
    print(
        f"   📏 Difference: {(longest['day_length_seconds'] - shortest['day_length_seconds']) / 3600:.1f} hours"
    )

    print(f"\n2. Comparing NYC vs Buenos Aires ({current_year}):")
    df_ba = get_sunrise_sunset_year(ba_lat, ba_lng, current_year, ba_timezone)

    # Compare winter solstice (opposite hemispheres)
    ny_winter = df_ny.loc[df_ny["day_length_seconds"].idxmin()]
    ba_summer = df_ba.loc[df_ba["day_length_seconds"].idxmax()]

    print(
        f"   NYC winter solstice: {ny_winter['date'].strftime('%Y-%m-%d')} - {ny_winter['day_length']}"
    )
    print(
        f"   BA summer solstice:  {ba_summer['date'].strftime('%Y-%m-%d')} - {ba_summer['day_length']}"
    )

    print("\n3. Seasonal analysis (NYC):")
    seasonal_stats = (
        df_ny.groupby("season")
        .agg({"day_length_seconds": ["mean", "min", "max"], "date": "count"})
        .round(1)
    )

    for season in ["Winter", "Spring", "Summer", "Autumn"]:
        if season in seasonal_stats.index:
            stats = seasonal_stats.loc[season]
            avg_hours = stats[("day_length_seconds", "mean")] / 3600
            min_hours = stats[("day_length_seconds", "min")] / 3600
            max_hours = stats[("day_length_seconds", "max")] / 3600
            days = stats[("date", "count")]
            print(
                f"   {season:>6}: {days:>2} days, avg {avg_hours:4.1f}h (range: {min_hours:4.1f}h - {max_hours:4.1f}h)"
            )

    print("\n4. Testing leap year handling (2024):")
    if current_year != 2024:
        df_leap = get_sunrise_sunset_year(ny_lat, ny_lng, 2024, ny_timezone)
        feb_29 = df_leap[df_leap["date"].dt.strftime("%m-%d") == "02-29"]
        print(f"   2024 has {len(df_leap)} days")
        if not feb_29.empty:
            print(
                f"   ✅ Feb 29 included: {feb_29.iloc[0]['date'].strftime('%Y-%m-%d')}"
            )
            print(
                f"      Sunrise: {feb_29.iloc[0]['sunrise']}, Sunset: {feb_29.iloc[0]['sunset']}"
            )
        else:
            print("   ❌ Feb 29 missing")
    else:
        print(f"   Current year {current_year} is a leap year!")
        feb_29 = df_ny[df_ny["date"].dt.strftime("%m-%d") == "02-29"]
        if not feb_29.empty:
            print(
                f"   ✅ Feb 29 data: Sunrise {feb_29.iloc[0]['sunrise']}, Sunset {feb_29.iloc[0]['sunset']}"
            )

    print(f"\n5. Monthly daylight progression (NYC {current_year}):")
    monthly_avg = (
        df_ny.groupby(df_ny["date"].dt.month)["day_length_seconds"].mean() / 3600
    )
    months = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]

    print("   Month | Avg Hours | Visual")
    print("   ------|-----------|" + "-" * 20)
    max_hours = monthly_avg.max()
    for i, hours in enumerate(monthly_avg, 1):
        bar_length = int((hours / max_hours) * 20)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"   {months[i - 1]:>5} | {hours:7.1f}h | {bar}")

    print("\n6. Data structure information:")
    print(f"   Columns: {list(df_ny.columns)}")
    print("   Extra analysis columns added:")
    print("   - day_length_seconds: Numeric day length for calculations")
    print("   - day_of_year: Day number (1-365/366)")
    print("   - season: Calculated season based on hemisphere")

    print("\n✅ Yearly demo completed successfully!")
    print("💡 Use the returned DataFrame for your own analysis and visualizations!")
    print("\nPowered by SunriseSunset.io - https://sunrisesunset.io/")


if __name__ == "__main__":
    main()
