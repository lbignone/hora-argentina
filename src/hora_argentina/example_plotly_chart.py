#!/usr/bin/env python3
"""
Example of creating a simple Plotly chart with sunrise/sunset curves.
"""

from datetime import date

from src.hora_argentina.from_api import get_sunrise_sunset_year_dual_timezone


def main():
    """Create and display a simple sunrise/sunset chart."""

    # Buenos Aires coordinates
    ba_lat, ba_lng = -34.6037, -58.3816
    ba_timezone = "America/Argentina/Buenos_Aires"

    # Get data for the next 30 days
    today = date.today()

    print("Fetching sunrise/sunset data...")
    df = get_sunrise_sunset_year_dual_timezone(
        latitude=ba_lat,
        longitude=ba_lng,
        year=today.year,
        summer_timezone="Etc/GMT+3",
        winter_timezone="Etc/GMT+4",
        summer_start_date="2025-9-07",
        winter_start_date="2025-04-06",
    )

    # df = get_sunrise_sunset_year(ba_lat, ba_lng, year=today.year, timezone=ba_timezone)

    # df_4 = get_sunrise_sunset_year(
    #     ba_lat, ba_lng, year=today.year, timezone="Etc/GMT-4"
    # )

    print(f"Got data for {len(df)} days")
    print("\nFirst few rows:")
    print(df[["date", "sunrise", "sunset"]].head())

    # Create the plot
    try:
        from src.hora_argentina.plot_plotly import plot_sunrise_sunset_curves

        df_plot, fig, config = plot_sunrise_sunset_curves(
            df, title=f"Buenos Aires - Sunrise and Sunset Times ({today.year})"
        )

        print(f"Got data for {len(df)} days")
        print("\nFirst few rows:")
        print(df_plot[["date", "sunrise_time", "sunset_time"]].head())

        # Show the plot in browser
        fig.show(config=config)

        # Save to HTML file
        fig.write_html("sunrise_sunset_chart.html")
        print("\n✅ Chart created successfully!")
        print("📊 Interactive chart saved to: sunrise_sunset_chart.html")
        print("🌐 Chart should open automatically in your browser")

    except ImportError as e:
        print(f"\n❌ Plotly not installed: {e}")
        print("To use the plotting function, install plotly with:")
        print("pip install plotly")
    except Exception as e:
        print(f"\n❌ Error creating chart: {e}")


if __name__ == "__main__":
    main()
