#!/usr/bin/env python3
"""
Solar Times Calculator

Reads configuration from config.json and outputs sunrise, sunset, and noon times
in HH:MM:SS format for the specified date, location, and timezone.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the src directory to Python path to import our modules
sys.path.append(str(Path(__file__).parent / "src"))

from hora_argentina.noaa_solar_calculations import (
    eccent_earth_orbit,
    equation_of_time,
    geom_mean_anom_sun,
    geom_mean_long_sun,
    hour_angle,
    julian_century,
    mean_obliq_ecliptic,
    obliq_corr,
    solar_noon,
    sun_apparent_long,
    sun_declination,
    sun_eq_of_center,
    sun_true_long,
    sunrise,
    sunset,
    var_y,
)


def date_to_julian_day(target_date, utc_offset=0):
    """Convert a date to Julian Day Number, considering local time."""
    if isinstance(target_date, str):
        # If it's just a date string (YYYY-MM-DD), assume noon local time
        if len(target_date) == 10:
            target_datetime = datetime.fromisoformat(target_date + "T12:00:00")
        else:
            target_datetime = datetime.fromisoformat(target_date)
    elif isinstance(target_date, datetime):
        target_datetime = target_date
    else:
        # If it's a date object, assume noon local time
        target_datetime = datetime.combine(
            target_date, datetime.min.time().replace(hour=12)
        )

    # Convert to UTC by subtracting the UTC offset
    utc_datetime = target_datetime - timedelta(hours=utc_offset)

    # Extract date and time components
    year = utc_datetime.year
    month = utc_datetime.month
    day = utc_datetime.day
    hour = utc_datetime.hour
    minute = utc_datetime.minute
    second = utc_datetime.second

    # Julian Day calculation for the date part
    a = (14 - month) // 12
    y = year + 4800 - a
    m = month + 12 * a - 3

    jd_date = day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045

    # Add the time fraction (convert time to fraction of a day)
    time_fraction = (hour + minute / 60.0 + second / 3600.0) / 24.0

    return jd_date + time_fraction - 0.5  # Subtract 0.5 because JD starts at noon


def decimal_hours_to_time_string(decimal_hours):
    """Convert decimal hours to HH:MM:SS format."""
    if decimal_hours is None:
        return "N/A"

    # Handle negative hours (previous day) or hours >= 24 (next day)
    hours = int(decimal_hours) % 24
    minutes = int((decimal_hours - int(decimal_hours)) * 60)
    seconds = int(((decimal_hours - int(decimal_hours)) * 60 - minutes) * 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def load_config(config_file="config.txt"):
    """Load configuration from JSON file."""
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in configuration file: {e}")
        sys.exit(1)


def validate_config(config):
    """Validate the configuration parameters."""
    required_fields = ["date", "utc_offset", "latitude", "longitude"]

    for field in required_fields:
        if field not in config:
            print(f"Error: Missing required field '{field}' in configuration.")
            sys.exit(1)

    # Validate ranges
    if not -90 <= config["latitude"] <= 90:
        print("Error: Latitude must be between -90 and 90 degrees.")
        sys.exit(1)

    if not -180 <= config["longitude"] <= 180:
        print("Error: Longitude must be between -180 and 180 degrees.")
        sys.exit(1)

    if not -12 <= config["utc_offset"] <= 14:
        print("Error: UTC offset must be between -12 and +14 hours.")
        sys.exit(1)

    # Validate date format
    try:
        datetime.fromisoformat(config["date"])
    except ValueError:
        print("Error: Date must be in YYYY-MM-DD format.")
        sys.exit(1)

    # Validate time format if provided
    if "time" in config:
        try:
            datetime.strptime(config["time"], "%H:%M:%S")
        except ValueError:
            try:
                datetime.strptime(config["time"], "%H:%M")
            except ValueError:
                print("Error: Time must be in HH:MM:SS or HH:MM format.")
                sys.exit(1)


def main():
    """Main function to calculate and display solar times."""
    # Check for command line argument for config file
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.txt"

    # Load and validate configuration
    config = load_config(config_file)
    validate_config(config)

    # Extract configuration values
    target_date = config["date"]
    target_time = config.get("time", "12:00:00")  # Default to noon if no time specified
    utc_offset = config["utc_offset"]
    latitude = config["latitude"]
    longitude = config["longitude"]

    # Combine date and time
    if "time" in config:
        datetime_str = f"{target_date}T{target_time}"
    else:
        datetime_str = f"{target_date}T{target_time}"

    # Convert date to Julian Day (considering local time)
    julian_day = date_to_julian_day(datetime_str, utc_offset)

    # Calculate Julian Century
    jc = julian_century(julian_day)

    # Calculate geometric mean longitude of the sun
    geom_mean_long = geom_mean_long_sun(jc)

    # Calculate additional astronomical parameters
    geom_mean_anom = geom_mean_anom_sun(jc)
    eccent_orbit = eccent_earth_orbit(jc)
    sun_eq_center = sun_eq_of_center(jc)
    sun_true_longitude = sun_true_long(jc)
    sun_apparent_longitude = sun_apparent_long(jc)
    mean_obliq = mean_obliq_ecliptic(jc)
    obliq_correction = obliq_corr(jc)
    var_y_value = var_y(jc)
    sun_decl = sun_declination(jc)

    # Calculate hour angle (using standard solar elevation of -0.833°)
    hour_angle_value = hour_angle(latitude, jc, -0.833)

    # Calculate equation of time
    eq_time = equation_of_time(jc)

    # Calculate solar times
    sunrise_time = sunrise(latitude, longitude, utc_offset, julian_day)
    sunset_time = sunset(latitude, longitude, utc_offset, julian_day)
    noon_time = solar_noon(longitude, utc_offset, julian_day)

    # Format times as HH:MM:SS
    sunrise_str = decimal_hours_to_time_string(sunrise_time)
    sunset_str = decimal_hours_to_time_string(sunset_time)
    noon_str = decimal_hours_to_time_string(noon_time)

    # Display results
    print("Solar Times Calculator")
    print("=" * 50)
    print(f"Date: {target_date}")
    print(f"Time: {target_time}")
    print(f"Location: {latitude:.4f}°, {longitude:.4f}°")
    print(f"UTC Offset: {utc_offset:+.1f} hours")
    print()
    print("Astronomical Calculations:")
    print(f"Julian Day:              {julian_day:.6f}")
    print(f"Julian Century:          {jc:.8f}")
    print(f"Geom Mean Long Sun:      {geom_mean_long:.6f}°")
    print(f"Geom Mean Anom Sun:      {geom_mean_anom:.6f}°")
    print(f"Eccent Earth Orbit:      {eccent_orbit:.8f}")
    print(f"Sun Eq of Center:        {sun_eq_center:.6f}°")
    print(f"Sun True Long:           {sun_true_longitude:.6f}°")
    print(f"Sun Apparent Long:       {sun_apparent_longitude:.6f}°")
    print(f"Mean Obliq Ecliptic:     {mean_obliq:.6f}°")
    print(f"Obliq Corr:              {obliq_correction:.6f}°")
    print(f"Var Y:                   {var_y_value:.8f}")
    print(f"Sun Declination:         {sun_decl:.6f}°")
    print(f"Hour Angle:              {hour_angle_value:.6f}°")
    print(f"Equation of Time:        {eq_time:.6f} minutes")
    print()
    print("Solar Times:")
    print(f"Sunrise:    {sunrise_str}")
    print(f"Solar Noon: {noon_str}")
    print(f"Sunset:     {sunset_str}")


if __name__ == "__main__":
    main()
