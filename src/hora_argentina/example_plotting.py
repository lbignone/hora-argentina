#!/usr/bin/env python3
"""
Example script demonstrating how to plot yearly sun times data.
"""

from hora_argentina.noaa_plotly import plot_yearly_sun_times
from hora_argentina.noaa_solar_calculations import yearly_sun_times_dataframe


def main():
    """Example of plotting yearly sun times for multiple locations."""

    # Define locations with coordinates
    locations = [
        {
            "name": "Buenos Aires, Argentina",
            "latitude": -34.6118,
            "longitude": -58.3960,
            "timezone_offset": -3,  # Argentina standard time (UTC-3)
        },
        # Arctic locations
        {
            "name": "Barrow (Utqiagvik), Alaska",  # Close to North Pole
            "latitude": 71.2906,
            "longitude": -156.7886,
            "timezone_offset": -9,  # Alaska Standard Time (UTC-9)
        },
        {
            "name": "Longyearbyen, Svalbard",  # Arctic settlement
            "latitude": 78.2232,
            "longitude": 15.6267,
            "timezone_offset": 1,  # Central European Time (UTC+1)
        },
        # Antarctic locations
        {
            "name": "McMurdo Station, Antarctica",  # Close to South Pole
            "latitude": -77.8419,
            "longitude": 166.6863,
            "timezone_offset": 12,  # New Zealand Time (UTC+12)
        },
        {
            "name": "Rothera Research Station, Antarctica",  # Antarctic Peninsula
            "latitude": -67.5681,
            "longitude": -68.1281,
            "timezone_offset": -3,  # Argentina Time (UTC-3)
        },
    ]

    for location in locations:
        print(f"\n{'=' * 60}")
        print(f"Processing: {location['name']}")
        print(f"Coordinates: {location['latitude']:.4f}°, {location['longitude']:.4f}°")
        print(f"Timezone: UTC{location['timezone_offset']:+d}")

        # Generate the dataframe for current year
        print("Generating yearly sun times data...")
        try:
            df = yearly_sun_times_dataframe(
                location["latitude"], location["longitude"], location["timezone_offset"]
            )

            print(f"Data for {df.iloc[0]['date'].year}: {len(df)} days")

            # Create and display the plot
            print("Creating plot...")
            fig = plot_yearly_sun_times(
                df,
                title=f"{location['name']} - Sunrise and Sunset Times Throughout the Year",
                show_figure=True,  # This will open the plot in your browser
            )
            # Figure is created and displayed automatically
            del fig  # Clean up reference

            print("Plot created successfully!")

        except Exception as e:
            print(f"Error processing {location['name']}: {e}")

    print(f"\n{'=' * 60}")
    print("All plots created!")
    print("The plots show:")
    print("- Solid lines: Sunrise times")
    print("- Dashed lines: Sunset times")
    print("- Different colors for different twilight definitions:")
    print("  • Red: Official (sun visible)")
    print("  • Medium gray: Civil twilight")
    print("  • Dark gray: Nautical twilight")
    print("  • Very dark gray: Astronomical twilight")
    print("\nNote: Polar regions may show polar day/night phenomena where")
    print("the sun doesn't rise or set for extended periods.")


if __name__ == "__main__":
    main()
