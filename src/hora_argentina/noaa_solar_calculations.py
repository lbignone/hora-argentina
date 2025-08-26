from datetime import date, datetime, timedelta
from math import acos, asin, cos, degrees, radians, sin, tan

import pandas as pd


def julian_century(julian_day):
    """Convert Julian Day to Julian Century."""
    return (julian_day - 2451545.0) / 36525.0


def geom_mean_long_sun(julian_century):
    """Calculate the Geometric Mean Longitude of the Sun (in degrees)."""
    L0 = 280.46646 + julian_century * (36000.76983 + julian_century * 0.0003032)
    return L0 % 360


def geom_mean_anom_sun(julian_century):
    """Calculate the Geometric Mean Anomaly of the Sun (in degrees)."""
    return 357.52911 + julian_century * (35999.05029 - 0.0001537 * julian_century)


def eccent_earth_orbit(julian_century):
    """Calculate the eccentricity of Earth's orbit."""
    return 0.016708634 - julian_century * (0.000042037 + 0.0000001267 * julian_century)


def sun_eq_of_center(julian_century):
    """Calculate the Sun's Equation of Center (in degrees)."""
    m = geom_mean_anom_sun(julian_century)
    m_rad = radians(m)
    sin_m = sin(m_rad)
    sin_2m = sin(2 * m_rad)
    sin_3m = sin(3 * m_rad)

    return (
        sin_m * (1.914602 - julian_century * (0.004817 + 0.000014 * julian_century))
        + sin_2m * (0.019993 - 0.000101 * julian_century)
        + sin_3m * 0.000289
    )


def sun_true_long(julian_century):
    """Calculate the Sun's True Longitude (in degrees)."""
    L0 = geom_mean_long_sun(julian_century)
    C = sun_eq_of_center(julian_century)
    return L0 + C


def sun_apparent_long(julian_century):
    """Calculate the Sun's Apparent Longitude (in degrees)."""
    stl = sun_true_long(julian_century)
    omega = 125.04 - 1934.136 * julian_century
    return stl - 0.00569 - 0.00478 * sin(radians(omega))


def mean_obliq_ecliptic(julian_century):
    """Calculate the Mean Obliquity of the Ecliptic (in degrees)."""
    seconds = 21.448 - julian_century * (
        46.8150 + julian_century * (0.00059 - julian_century * 0.001813)
    )
    return 23.0 + (26.0 + (seconds / 60.0)) / 60.0


def obliq_corr(julian_century):
    """Calculate the corrected Obliquity of the Ecliptic (in degrees)."""
    e0 = mean_obliq_ecliptic(julian_century)
    omega = 125.04 - 1934.136 * julian_century
    return e0 + 0.00256 * cos(radians(omega))


def var_y(julian_century):
    """Calculate the variable Y used in the Equation of Time calculation."""
    e = obliq_corr(julian_century)
    return tan(radians(e) / 2.0) ** 2


def sun_declination(julian_century):
    """Calculate the Sun's Declination (in degrees)."""
    e = obliq_corr(julian_century)
    lambda_sun = sun_apparent_long(julian_century)
    sint = sin(radians(e)) * sin(radians(lambda_sun))
    return degrees(asin(sint))


def equation_of_time(julian_century):
    """Calculate the Equation of Time (in minutes)."""
    y = var_y(julian_century)
    L0 = geom_mean_long_sun(julian_century)
    e = eccent_earth_orbit(julian_century)
    M = geom_mean_anom_sun(julian_century)

    sin_2L0 = sin(2.0 * radians(L0))
    sin_M = sin(radians(M))
    cos_2L0 = cos(2.0 * radians(L0))
    sin_4L0 = sin(4.0 * radians(L0))
    sin_2M = sin(2.0 * radians(M))

    Etime = (
        y * sin_2L0
        - 2.0 * e * sin_M
        + 4.0 * e * y * sin_M * cos_2L0
        - 0.5 * y * y * sin_4L0
        - 1.25 * e * e * sin_2M
    )
    return degrees(Etime) * 4.0  # in minutes


def hour_angle(latitude, julian_century, solar_elevation):
    """Calculate the Hour Angle (in degrees) for given solar elevation."""
    return degrees(
        acos(
            cos(radians(90.0 - solar_elevation))
            / (cos(radians(latitude)) * cos(radians(sun_declination(julian_century))))
            - tan(radians(latitude)) * tan(radians(sun_declination(julian_century)))
        )
    )


def solar_noon(longitude, timezone_offset, julian_day):
    """Calculate Solar Noon time (in local time)."""
    jc = julian_century(julian_day)
    eq_time = equation_of_time(jc)
    solar_noon_utc = (720 - 4.0 * longitude - eq_time) / 60.0  # in hours
    return solar_noon_utc + timezone_offset  # in local time


def sunrise(latitude, longitude, timezone_offset, julian_day, solar_elevation=-0.833):
    """Calculate Sunrise time (in local time)."""
    jc = julian_century(julian_day)
    ha = hour_angle(latitude, jc, solar_elevation)
    solar_noon_time = solar_noon(longitude, timezone_offset, julian_day)
    return solar_noon_time - ha / 15.0  # in hours


def sunset(latitude, longitude, timezone_offset, julian_day, solar_elevation=-0.833):
    """Calculate Sunset time (in local time)."""
    jc = julian_century(julian_day)
    ha = hour_angle(latitude, jc, solar_elevation)
    solar_noon_time = solar_noon(longitude, timezone_offset, julian_day)
    return solar_noon_time + ha / 15.0  # in hours


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
    if decimal_hours is None or pd.isna(decimal_hours):
        return None

    # Handle negative hours (wrap around midnight)
    while decimal_hours < 0:
        decimal_hours += 24
    while decimal_hours >= 24:
        decimal_hours -= 24

    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    seconds = int(((decimal_hours - hours) * 60 - minutes) * 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def yearly_sun_times_dataframe(latitude, longitude, timezone_offset, year=None):
    """
    Calculate sunrise and sunset times for all twilight definitions for a full year.

    Parameters:
    -----------
    latitude : float
        Latitude in degrees (positive for North, negative for South)
    longitude : float
        Longitude in degrees (positive for East, negative for West)
    timezone_offset : float
        Timezone offset from UTC in hours (e.g., -3 for Argentina standard time)
    year : int, optional
        Year for calculations (default: current year)

    Returns:
    --------
    pandas.DataFrame
        DataFrame with columns:
        - date: Date for each day of the year
        - official_sunrise: Official sunrise time (decimal hours)
        - official_sunset: Official sunset time (decimal hours)
        - civil_sunrise: Civil twilight sunrise time (decimal hours)
        - civil_sunset: Civil twilight sunset time (decimal hours)
        - nautical_sunrise: Nautical twilight sunrise time (decimal hours)
        - nautical_sunset: Nautical twilight sunset time (decimal hours)
        - astronomical_sunrise: Astronomical twilight sunrise time (decimal hours)
        - astronomical_sunset: Astronomical twilight sunset time (decimal hours)
    """

    # Use current year if none specified
    if year is None:
        year = date.today().year

    # Twilight definitions (solar elevation angles in degrees)
    twilight_angles = {
        "official": -0.833,  # Sun's center at horizon, accounting for refraction
        "civil": -6.0,  # Civil twilight
        "nautical": -12.0,  # Nautical twilight
        "astronomical": -18.0,  # Astronomical twilight
    }

    # Create date range for the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Initialize lists to store results
    dates = []
    results = {f"{twilight}_sunrise": [] for twilight in twilight_angles.keys()}
    results.update({f"{twilight}_sunset": [] for twilight in twilight_angles.keys()})

    # Calculate for each day of the year
    current_date = start_date
    while current_date <= end_date:
        dates.append(current_date)
        julian_day = date_to_julian_day(current_date, timezone_offset)

        # Calculate sunrise and sunset for each twilight definition
        for twilight, elevation in twilight_angles.items():
            try:
                sunrise_time = sunrise(
                    latitude, longitude, timezone_offset, julian_day, elevation
                )
                sunset_time = sunset(
                    latitude, longitude, timezone_offset, julian_day, elevation
                )

                results[f"{twilight}_sunrise"].append(sunrise_time)
                results[f"{twilight}_sunset"].append(sunset_time)

            except (ValueError, ZeroDivisionError):
                # Handle cases where sun doesn't rise/set (polar regions)
                results[f"{twilight}_sunrise"].append(None)
                results[f"{twilight}_sunset"].append(None)

        current_date += timedelta(days=1)

    # Create DataFrame
    data = {"date": dates}
    data.update(results)

    return pd.DataFrame(data)
