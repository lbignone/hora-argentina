from math import acos, asin, cos, degrees, radians, sin, tan


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
    O = sun_true_long(julian_century)
    omega = 125.04 - 1934.136 * julian_century
    return O - 0.00569 - 0.00478 * sin(radians(omega))


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
    lat_rad = radians(latitude)
    sd = radians(sun_declination(julian_century))
    se = radians(solar_elevation)

    HAarg = (sin(se) - sin(lat_rad) * sin(sd)) / (cos(lat_rad) * cos(sd))
    if HAarg > 1:
        HAarg = 1
    elif HAarg < -1:
        HAarg = -1

    return degrees(acos(HAarg))  # in degrees


def solar_noon(longitude, timezone_offset, julian_day):
    """Calculate Solar Noon (in local time)."""
    jc = julian_century(julian_day)
    eq_time = equation_of_time(jc)
    return (720 - 4.0 * longitude - eq_time + timezone_offset * 60) / 60


def sunrise(latitude, longitude, timezone_offset, julian_day, solar_elevation=-0.833):
    """Calculate Sunrise time (in local time)."""
    jc = julian_century(julian_day)
    ha = hour_angle(latitude, jc, solar_elevation)
    solar_noon_time = solar_noon(longitude, timezone_offset, julian_day)
    return (solar_noon_time * 1440 - ha * 4.0) / 1440  # in hours


def sunset(latitude, longitude, timezone_offset, julian_day, solar_elevation=-0.833):
    """Calculate Sunset time (in local time)."""
    jc = julian_century(julian_day)
    ha = hour_angle(latitude, jc, solar_elevation)
    solar_noon_time = solar_noon(longitude, timezone_offset, julian_day)
    return solar_noon_time + ha / 15.0  # in hours
