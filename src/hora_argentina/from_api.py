"""
Functions to fetch sunrise and sunset data from APIs.
"""

from datetime import date, datetime
from typing import Optional, Union

import pandas as pd
import requests


def get_sunrise_sunset_data(
    latitude: float,
    longitude: float,
    timezone: Optional[str] = None,
    date_value: Optional[Union[str, date, datetime]] = None,
    date_start: Optional[Union[str, date, datetime]] = None,
    date_end: Optional[Union[str, date, datetime]] = None,
    time_format: str = "24",
) -> pd.DataFrame:
    """
    Get sunrise and sunset times for a given latitude, longitude and timezone using SunriseSunset.io API.

    Args:
        latitude (float): Latitude of the location in decimal degrees
        longitude (float): Longitude of the location in decimal degrees
        timezone (str, optional): Timezone of the returned times (e.g., 'UTC', 'America/New_York').
                                 If not set, defaults to location's timezone.
        date_value (str/date/datetime, optional): Date in YYYY-MM-DD format, or date/datetime object.
                                                 Can also be "today" or "tomorrow". Defaults to today.
        date_start (str/date/datetime, optional): Start date for date range queries
        date_end (str/date/datetime, optional): End date for date range queries
        time_format (str): Format for times - "24" for 24-hour, "12" for 12-hour, "military", or "unix"

    Returns:
        pd.DataFrame: DataFrame containing sunrise/sunset data with columns:
                     - date: Date of the data
                     - sunrise: Sunrise time
                     - sunset: Sunset time
                     - first_light: First light time
                     - last_light: Last light time
                     - dawn: Dawn time
                     - dusk: Dusk time
                     - solar_noon: Solar noon time
                     - golden_hour: Golden hour start time
                     - day_length: Length of the day
                     - timezone: Timezone used
                     - utc_offset: UTC offset in minutes

    Raises:
        ValueError: If the API request fails or returns an error
        requests.RequestException: If there's a network error

    Example:
        >>> df = get_sunrise_sunset_data(40.7128, -74.0060, timezone="America/New_York")
        >>> print(df.head())
    """

    # Build the API URL
    base_url = "https://api.sunrisesunset.io/json"
    params = {"lat": latitude, "lng": longitude, "time_format": time_format}

    # Add optional parameters
    if timezone:
        params["timezone"] = timezone

    # Handle date parameters
    if date_value is not None:
        if isinstance(date_value, (date, datetime)):
            params["date"] = date_value.strftime("%Y-%m-%d")
        else:
            params["date"] = str(date_value)

    if date_start is not None:
        if isinstance(date_start, (date, datetime)):
            params["date_start"] = date_start.strftime("%Y-%m-%d")
        else:
            params["date_start"] = str(date_start)

    if date_end is not None:
        if isinstance(date_end, (date, datetime)):
            params["date_end"] = date_end.strftime("%Y-%m-%d")
        else:
            params["date_end"] = str(date_end)

    try:
        # Make the API request
        response = requests.get(base_url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Check if the API returned an error
        if data.get("status") != "OK":
            raise ValueError(
                f"API returned error status: {data.get('status', 'Unknown error')}"
            )

        results = data.get("results")
        if not results:
            raise ValueError("No results returned from API")

        # Handle single date response vs date range response
        if isinstance(results, dict):
            # Single date response
            df_data = [results]
        elif isinstance(results, list):
            # Date range response
            df_data = results
        else:
            raise ValueError("Unexpected response format from API")

        # Create DataFrame
        df = pd.DataFrame(df_data)

        # Ensure date column is datetime
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])

        # Reorder columns for better readability
        desired_columns = [
            "date",
            "sunrise",
            "sunset",
            "first_light",
            "last_light",
            "dawn",
            "dusk",
            "solar_noon",
            "golden_hour",
            "day_length",
            "timezone",
            "utc_offset",
        ]

        # Only include columns that exist in the response
        available_columns = [col for col in desired_columns if col in df.columns]
        df = df[available_columns]

        return df

    except requests.RequestException as e:
        raise requests.RequestException(
            f"Failed to fetch data from SunriseSunset.io API: {str(e)}"
        )
    except Exception as e:
        raise ValueError(f"Error processing API response: {str(e)}")


def get_sunrise_sunset_today(
    latitude: float, longitude: float, timezone: Optional[str] = None
) -> pd.DataFrame:
    """
    Convenience function to get today's sunrise and sunset times.

    Args:
        latitude (float): Latitude of the location in decimal degrees
        longitude (float): Longitude of the location in decimal degrees
        timezone (str, optional): Timezone of the returned times

    Returns:
        pd.DataFrame: DataFrame containing today's sunrise/sunset data

    Example:
        >>> df = get_sunrise_sunset_today(40.7128, -74.0060, timezone="America/New_York")
        >>> print(f"Sunrise: {df.iloc[0]['sunrise']}, Sunset: {df.iloc[0]['sunset']}")
    """
    return get_sunrise_sunset_data(
        latitude, longitude, timezone=timezone, date_value="today"
    )


def get_sunrise_sunset_range(
    latitude: float,
    longitude: float,
    start_date: Union[str, date, datetime],
    end_date: Union[str, date, datetime],
    timezone: Optional[str] = None,
) -> pd.DataFrame:
    """
    Get sunrise and sunset times for a date range (up to 365 days).

    Args:
        latitude (float): Latitude of the location in decimal degrees
        longitude (float): Longitude of the location in decimal degrees
        start_date (str/date/datetime): Start date for the range
        end_date (str/date/datetime): End date for the range
        timezone (str, optional): Timezone of the returned times

    Returns:
        pd.DataFrame: DataFrame containing sunrise/sunset data for the date range

    Example:
        >>> df = get_sunrise_sunset_range(40.7128, -74.0060, "2024-01-01", "2024-01-31")
        >>> print(f"Got {len(df)} days of data")
    """
    return get_sunrise_sunset_data(
        latitude, longitude, timezone=timezone, date_start=start_date, date_end=end_date
    )


def get_sunrise_sunset_year(
    latitude: float,
    longitude: float,
    year: int,
    timezone: Optional[str] = None,
) -> pd.DataFrame:
    """
    Get sunrise and sunset times for an entire year.

    This function automatically handles leap years and fetches data in chunks
    to respect API limits (maximum 365 days per request).

    Args:
        latitude (float): Latitude of the location in decimal degrees
        longitude (float): Longitude of the location in decimal degrees
        year (int): The year to get data for (e.g., 2024)
        timezone (str, optional): Timezone of the returned times

    Returns:
        pd.DataFrame: DataFrame containing sunrise/sunset data for the entire year

    Example:
        >>> df = get_sunrise_sunset_year(40.7128, -74.0060, 2024, timezone="America/New_York")
        >>> print(f"Got {len(df)} days of data for year 2024")
        >>> # Find longest and shortest days
        >>> df['day_length_seconds'] = pd.to_timedelta(df['day_length']).dt.total_seconds()
        >>> longest_day = df.loc[df['day_length_seconds'].idxmax()]
        >>> shortest_day = df.loc[df['day_length_seconds'].idxmin()]
        >>> print(f"Longest day: {longest_day['date'].strftime('%Y-%m-%d')} ({longest_day['day_length']})")
        >>> print(f"Shortest day: {shortest_day['date'].strftime('%Y-%m-%d')} ({shortest_day['day_length']})")
    """
    from calendar import isleap

    # Determine if it's a leap year
    is_leap = isleap(year)

    # Create start and end dates for the year
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31)

    # Check if it's a leap year and we need to split the request
    if is_leap:
        # For leap years (366 days), we need to split into two requests
        # since API limit is 365 days per request

        # First request: Jan 1 to Dec 30 (364 days)
        mid_date = date(year, 12, 30)

        df1 = get_sunrise_sunset_data(
            latitude,
            longitude,
            timezone=timezone,
            date_start=start_date,
            date_end=mid_date,
        )

        # Second request: Dec 31 (1 day)
        df2 = get_sunrise_sunset_data(
            latitude, longitude, timezone=timezone, date_value=end_date
        )

        # Combine the dataframes
        df_year = pd.concat([df1, df2], ignore_index=True)

    else:
        # For regular years (365 days), single request is sufficient
        df_year = get_sunrise_sunset_data(
            latitude,
            longitude,
            timezone=timezone,
            date_start=start_date,
            date_end=end_date,
        )

    # Sort by date to ensure proper order
    df_year = df_year.sort_values("date").reset_index(drop=True)

    # Add some useful derived columns
    if "day_length" in df_year.columns:
        # Convert day_length to seconds for easier analysis
        df_year["day_length_seconds"] = pd.to_timedelta(
            df_year["day_length"]
        ).dt.total_seconds()

        # Add day of year
        df_year["day_of_year"] = df_year["date"].dt.dayofyear

        # Add season information (Northern Hemisphere by default)
        def get_season(month, day, latitude):
            """Determine season based on date and hemisphere."""
            # Northern hemisphere seasons
            if latitude >= 0:
                if (
                    (month == 12 and day >= 21)
                    or month in [1, 2]
                    or (month == 3 and day < 20)
                ):
                    return "Winter"
                elif (
                    (month == 3 and day >= 20)
                    or month in [4, 5]
                    or (month == 6 and day < 21)
                ):
                    return "Spring"
                elif (
                    (month == 6 and day >= 21)
                    or month in [7, 8]
                    or (month == 9 and day < 22)
                ):
                    return "Summer"
                else:
                    return "Autumn"
            # Southern hemisphere seasons (opposite)
            else:
                if (
                    (month == 12 and day >= 21)
                    or month in [1, 2]
                    or (month == 3 and day < 20)
                ):
                    return "Summer"
                elif (
                    (month == 3 and day >= 20)
                    or month in [4, 5]
                    or (month == 6 and day < 21)
                ):
                    return "Autumn"
                elif (
                    (month == 6 and day >= 21)
                    or month in [7, 8]
                    or (month == 9 and day < 22)
                ):
                    return "Winter"
                else:
                    return "Spring"

        df_year["season"] = df_year.apply(
            lambda row: get_season(row["date"].month, row["date"].day, latitude), axis=1
        )

    return df_year


def get_sunrise_sunset_year_dual_timezone(
    latitude: float,
    longitude: float,
    year: int,
    summer_timezone: str,
    winter_timezone: str,
    summer_start_date: Union[str, date, datetime],
    winter_start_date: Union[str, date, datetime],
) -> pd.DataFrame:
    """
    Get sunrise and sunset times for an entire year using different timezones for summer and winter periods.

    This function is useful for locations that observe daylight saving time or seasonal timezone changes.
    It fetches complete year data using both timezones and combines them based on the specified switch dates.

    Args:
        latitude (float): Latitude of the location in decimal degrees
        longitude (float): Longitude of the location in decimal degrees
        year (int): The year to get data for (e.g., 2024)
        summer_timezone (str): Timezone to use during summer period (e.g., "America/Argentina/Buenos_Aires")
        winter_timezone (str): Timezone to use during winter period (e.g., "America/Argentina/Buenos_Aires")
        summer_start_date (str/date/datetime): Date when summer timezone begins (e.g., "2024-10-06" for Argentina)
        winter_start_date (str/date/datetime): Date when winter timezone begins (e.g., "2024-03-03" for Argentina)

    Returns:
        pd.DataFrame: DataFrame containing sunrise/sunset data for the entire year with mixed timezones.
                     Includes an additional column 'active_timezone' indicating which timezone was used for each date.

    Example:
        >>> # Example for Argentina (UTC-3 in summer, UTC-3 in winter, but with DST transitions)
        >>> df = get_sunrise_sunset_year_dual_timezone(
        ...     latitude=-34.6118,
        ...     longitude=-58.3960,
        ...     year=2024,
        ...     summer_timezone="America/Argentina/Buenos_Aires",
        ...     winter_timezone="America/Argentina/Buenos_Aires",
        ...     summer_start_date="2024-10-06",  # Argentina DST starts
        ...     winter_start_date="2024-03-03"   # Argentina DST ends
        ... )
        >>> print(f"Got {len(df)} days of data with mixed timezones")
        >>> print(df[df['active_timezone'] == summer_timezone].shape[0], "days with summer timezone")
        >>> print(df[df['active_timezone'] == winter_timezone].shape[0], "days with winter timezone")
    """

    # Convert date inputs to date objects
    if isinstance(summer_start_date, str):
        summer_start = datetime.strptime(summer_start_date, "%Y-%m-%d").date()
    elif isinstance(summer_start_date, datetime):
        summer_start = summer_start_date.date()
    else:
        summer_start = summer_start_date

    if isinstance(winter_start_date, str):
        winter_start = datetime.strptime(winter_start_date, "%Y-%m-%d").date()
    elif isinstance(winter_start_date, datetime):
        winter_start = winter_start_date.date()
    else:
        winter_start = winter_start_date

    # Ensure dates are for the correct year
    summer_start = summer_start.replace(year=year)
    winter_start = winter_start.replace(year=year)

    # Fetch complete year data for both timezones
    df_summer = get_sunrise_sunset_year(latitude, longitude, year, summer_timezone)
    df_winter = get_sunrise_sunset_year(latitude, longitude, year, winter_timezone)

    # Create a combined dataframe using the appropriate timezone for each date
    df_combined = df_summer.copy()  # Start with summer data as base

    # Add active_timezone column to track which timezone is being used
    df_combined["active_timezone"] = summer_timezone

    # Add date_only columns for easier matching
    df_combined["date_only"] = pd.to_datetime(df_combined["date"]).dt.date
    df_winter["date_only"] = pd.to_datetime(df_winter["date"]).dt.date

    # Determine which dates should use winter timezone
    if winter_start < summer_start:
        # Winter period: winter_start to summer_start (exclusive)
        winter_mask = (df_combined["date_only"] >= winter_start) & (
            df_combined["date_only"] < summer_start
        )
    else:
        # Winter period: winter_start to end of year AND start of year to summer_start
        winter_mask = (df_combined["date_only"] >= winter_start) | (
            df_combined["date_only"] < summer_start
        )

    # Replace data with winter timezone data for winter period dates
    winter_indices = df_combined[winter_mask].index
    if len(winter_indices) > 0:
        # Update the combined dataframe with winter data
        for idx in winter_indices:
            date_val = df_combined.loc[idx, "date_only"]
            winter_row = df_winter[df_winter["date_only"] == date_val]
            if not winter_row.empty:
                # Replace all columns except 'active_timezone' and 'date_only'
                for col in df_combined.columns:
                    if (
                        col not in ["active_timezone", "date_only"]
                        and col in winter_row.columns
                    ):
                        df_combined.loc[idx, col] = winter_row.iloc[0][col]
                # Set active timezone
                df_combined.loc[idx, "active_timezone"] = winter_timezone

    # Remove the temporary date_only column
    df_combined = df_combined.drop("date_only", axis=1)

    # Sort by date to ensure proper order
    df_combined = df_combined.sort_values("date").reset_index(drop=True)

    return df_combined
