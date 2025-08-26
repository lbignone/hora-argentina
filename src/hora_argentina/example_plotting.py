#!/usr/bin/env python3
"""
Example script demonstrating how to plot yearly sun times data.
"""

from hora_argentina.noaa_plotly import plot_yearly_sun_times
from hora_argentina.noaa_solar_calculations import yearly_sun_times_dataframe


def main():
    """Example of plotting yearly sun times."""

    # Buenos Aires coordinates
    latitude = -34.6118
    longitude = -58.3960
    timezone_offset = -3  # Argentina standard time (UTC-3)

    # Generate the dataframe for current year
    print("Generating yearly sun times data...")
    df = yearly_sun_times_dataframe(latitude, longitude, timezone_offset)

    print(f"Data for {df.iloc[0]['date'].year}: {len(df)} days")

    # Create and display the plot
    print("Creating plot...")
    fig = plot_yearly_sun_times(
        df,
        title="Buenos Aires - Sunrise and Sunset Times Throughout the Year",
        show_figure=True,  # This will open the plot in your browser
    )

    print("Plot created successfully!")
    print("The plot shows:")
    print("- Solid lines: Sunrise times")
    print("- Dashed lines: Sunset times")
    print("- Different colors for different twilight definitions:")
    print("  • Red: Official (sun visible)")
    print("  • Medium gray: Civil twilight")
    print("  • Dark gray: Nautical twilight")
    print("  • Very dark gray: Astronomical twilight")


if __name__ == "__main__":
    main()
