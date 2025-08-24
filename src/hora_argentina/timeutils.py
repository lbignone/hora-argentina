from datetime import date, datetime, timedelta

import astropy.units as u
import pytz
from astroplan import Observer
from astropy.coordinates import EarthLocation
from astropy.time import Time

horizons = {
    "official": -0.833 * u.deg,
    "civil": -6 * u.deg,
    "nautical": -12 * u.deg,
    "astronomical": -18 * u.deg,
}


def first_sunday(year, month):
    d = date(year, month, 1)
    days_to_sunday = (6 - d.weekday()) % 7
    return d + timedelta(days=days_to_sunday)


def is_winter_time(dt):
    """Check if datetime/date is between first Sunday of April and first Sunday of September."""
    if isinstance(dt, datetime):
        d = dt.date()
    else:
        d = dt

    start = first_sunday(d.year, 4)  # first Sunday of April
    end = first_sunday(d.year, 9)  # first Sunday of September

    return start <= d < end


def datetime_to_decimal_hour(dt):
    return dt.hour + dt.minute / 60 + dt.second / 3600


def sun_times(
    observer,
    horizon=-0.833 * u.deg,
    start_date=date(2025, 1, 1),
    end_date=date(2025, 12, 31),
):
    times = []
    rise_times = []
    set_times = []
    noon_times = []

    current_date = start_date
    while current_date <= end_date:
        dt = datetime(current_date.year, current_date.month, current_date.day, 15, 00)
        time = Time(dt)
        rise_time = observer.sun_rise_time(
            time, which="previous", horizon=horizon, n_grid_points=10
        )
        set_time = observer.sun_set_time(
            time, which="next", horizon=horizon, n_grid_points=10
        )
        noon_time = observer.noon(time, which="nearest", n_grid_points=10)

        times.append(time.to_datetime(timezone=observer.timezone))
        try:
            rise_times.append(
                datetime_to_decimal_hour(
                    rise_time.to_datetime(timezone=observer.timezone)
                )
            )
        except Exception:
            print(time)
            print(observer)
            rise_times.append(None)

        set_times.append(
            datetime_to_decimal_hour(set_time.to_datetime(timezone=observer.timezone))
        )

        noon_times.append(
            datetime_to_decimal_hour(noon_time.to_datetime(timezone=observer.timezone))
        )

        current_date += timedelta(days=1)

    return times, rise_times, set_times, noon_times


def get_results(latitude, longitude, horizon="civil", UTC_offset=-3):
    eloc = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=0 * u.m)

    observer = Observer(location=eloc, timezone=pytz.FixedOffset(UTC_offset * 60))
    times, rise_times, set_times, noon_times = sun_times(
        observer, horizon=horizons[horizon]
    )

    return dict(date=times, sunrise=rise_times, sunset=set_times, noon=noon_times)


def get_summertime_results(off_3_dict, off_4_dict):
    rise_times = []
    set_times = []
    noon_times = []

    for i, time in enumerate(off_3_dict["date"]):
        if is_winter_time(time):
            d = off_3_dict
        else:
            d = off_4_dict

        rise_times.append(d["sunrise"][i])
        set_times.append(d["sunset"][i])
        noon_times.append(d["noon"][i])

    return dict(
        date=off_3_dict["date"], sunrise=rise_times, sunset=set_times, noon=noon_times
    )


def offset_results(results, offset):
    rise_times = []
    set_times = []
    noon_times = []

    for i, time in enumerate(results["date"]):
        rise_times.append(results["sunrise"][i] + offset)
        set_times.append(results["sunset"][i] + offset)
        noon_times.append(results["noon"][i] + offset)

    return dict(
        date=results["date"], sunrise=rise_times, sunset=set_times, noon=noon_times
    )
