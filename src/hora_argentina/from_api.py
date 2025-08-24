"""
Functions to fetch sunrise and sunset data from APIs.
"""

import hashlib
import pickle
import random
import time
from datetime import date, datetime
from pathlib import Path
from typing import Optional, Union

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def _get_cache_key(
    latitude: float,
    longitude: float,
    timezone: Optional[str],
    date_value: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
    time_format: str,
) -> str:
    """Generate a cache key for the API request."""
    key_data = f"{latitude}_{longitude}_{timezone}_{date_value}_{date_start}_{date_end}_{time_format}"
    return hashlib.md5(key_data.encode()).hexdigest()


def _get_cache_path() -> Path:
    """Get the cache directory path."""
    # Use user's home directory or temp directory if home is not writable
    try:
        cache_dir = Path.home() / ".cache" / "hora_argentina"
    except (OSError, RuntimeError):
        # Fallback to system temp directory for environments like Streamlit Cloud
        import tempfile

        cache_dir = Path(tempfile.gettempdir()) / "hora_argentina_cache"

    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _load_from_cache(cache_key: str, max_age_hours: int = 24) -> Optional[pd.DataFrame]:
    """
    Load data from cache if it exists and is recent.

    Args:
        cache_key: Unique identifier for the cached data
        max_age_hours: Maximum age of cache in hours (default 24)

    Returns:
        Cached DataFrame or None if cache is missing/expired
    """
    try:
        cache_file = _get_cache_path() / f"{cache_key}.pkl"

        if cache_file.exists():
            # Check if cache is within max age
            cache_age_seconds = time.time() - cache_file.stat().st_mtime
            max_age_seconds = max_age_hours * 3600

            if cache_age_seconds < max_age_seconds:
                with open(cache_file, "rb") as f:
                    cached_df = pickle.load(f)
                    print(
                        f"📦 Using cached data (age: {cache_age_seconds / 3600:.1f} hours)"
                    )
                    return cached_df
            else:
                # Cache is too old, remove it
                cache_file.unlink(missing_ok=True)
                print(
                    f"🗑️ Removed expired cache (age: {cache_age_seconds / 3600:.1f} hours)"
                )

        return None
    except Exception as e:
        print(f"⚠️ Cache read error: {e}")
        return None


def _save_to_cache(cache_key: str, df: pd.DataFrame) -> bool:
    """
    Save data to cache.

    Args:
        cache_key: Unique identifier for the cached data
        df: DataFrame to cache

    Returns:
        True if successfully cached, False otherwise
    """
    try:
        cache_file = _get_cache_path() / f"{cache_key}.pkl"
        with open(cache_file, "wb") as f:
            pickle.dump(df, f)
        print("💾 Data cached successfully")
        return True
    except Exception as e:
        print(f"⚠️ Cache write error: {e}")
        return False


def _cleanup_old_cache_files(max_age_days: int = 7):
    """Remove cache files older than specified days."""
    try:
        cache_dir = _get_cache_path()
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 3600

        removed_count = 0
        for cache_file in cache_dir.glob("*.pkl"):
            if current_time - cache_file.stat().st_mtime > max_age_seconds:
                cache_file.unlink()
                removed_count += 1

        if removed_count > 0:
            print(f"🧹 Cleaned up {removed_count} old cache files")

    except Exception as e:
        print(f"⚠️ Cache cleanup error: {e}")


def get_sunrise_sunset_data(
    latitude: float,
    longitude: float,
    timezone: Optional[str] = None,
    date_value: Optional[Union[str, date, datetime]] = None,
    date_start: Optional[Union[str, date, datetime]] = None,
    date_end: Optional[Union[str, date, datetime]] = None,
    time_format: str = "24",
    max_retries: int = 3,
    retry_delay: float = 15.0,
    use_cache: bool = True,
    cache_max_age_hours: int = 24,
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
        max_retries (int): Maximum number of retry attempts for failed requests
        retry_delay (float): Initial delay between retries in seconds (default 15.0)
        use_cache (bool): Whether to use caching for API responses
        cache_max_age_hours (int): Maximum age of cache in hours (default 24)

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

    # Clean up old cache files periodically
    if use_cache:
        _cleanup_old_cache_files()

    # Convert date parameters to strings for cache key and API params
    date_str = None
    start_str = None
    end_str = None

    if date_value is not None:
        if isinstance(date_value, (date, datetime)):
            date_str = date_value.strftime("%Y-%m-%d")
        else:
            date_str = str(date_value)

    if date_start is not None:
        if isinstance(date_start, (date, datetime)):
            start_str = date_start.strftime("%Y-%m-%d")
        else:
            start_str = str(date_start)

    if date_end is not None:
        if isinstance(date_end, (date, datetime)):
            end_str = date_end.strftime("%Y-%m-%d")
        else:
            end_str = str(date_end)

    # Check cache first
    if use_cache:
        cache_key = _get_cache_key(
            latitude, longitude, timezone, date_str, start_str, end_str, time_format
        )
        cached_data = _load_from_cache(cache_key, cache_max_age_hours)
        if cached_data is not None:
            return cached_data

    # Build the API URL
    base_url = "https://api.sunrisesunset.io/json"
    params = {"lat": latitude, "lng": longitude, "time_format": time_format}

    # Add optional parameters
    if timezone:
        params["timezone"] = timezone

    # Handle date parameters
    if date_str is not None:
        params["date"] = date_str

    if start_str is not None:
        params["date_start"] = start_str

    if end_str is not None:
        params["date_end"] = end_str

    # Create session with retry strategy
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
        backoff_factor=1,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            # Add random jitter to avoid thundering herd
            if attempt > 0:
                delay = retry_delay * (2 ** (attempt - 1)) + random.uniform(0, 1)
                print(
                    f"Retrying API request in {delay:.2f} seconds (attempt {attempt + 1}/{max_retries + 1})"
                )
                time.sleep(delay)

            # Make the API request
            response = session.get(base_url, params=params, timeout=30)
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

            # Save to cache before returning
            if use_cache:
                _save_to_cache(cache_key, df)

            # Add a small delay after successful API calls to be respectful to the API
            # This helps prevent rate limiting, especially important for cloud platforms
            time.sleep(0.5)

            return df

        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < max_retries:
                print(
                    f"API request failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                )
                continue
            else:
                break
        except Exception as e:
            raise ValueError(f"Error processing API response: {str(e)}")

    # If we get here, all retries failed
    if last_exception and "503" in str(last_exception):
        raise requests.RequestException(
            f"SunriseSunset.io API is temporarily unavailable (503 Service Unavailable) after {max_retries + 1} attempts. "
            f"This commonly happens on cloud platforms like Streamlit Cloud. Please try again later or reduce the date range. "
            f"Last error: {str(last_exception)}"
        )
    else:
        raise requests.RequestException(
            f"Failed to fetch data from SunriseSunset.io API after {max_retries + 1} attempts. Last error: {str(last_exception)}"
        )


def get_sunrise_sunset_today(
    latitude: float,
    longitude: float,
    timezone: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 5.0,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Convenience function to get today's sunrise and sunset times.

    Args:
        latitude (float): Latitude of the location in decimal degrees
        longitude (float): Longitude of the location in decimal degrees
        timezone (str, optional): Timezone of the returned times
        max_retries (int): Maximum number of retry attempts for failed requests
        retry_delay (float): Initial delay between retries in seconds (default 5.0)
        use_cache (bool): Whether to use caching for API responses

    Returns:
        pd.DataFrame: DataFrame containing today's sunrise/sunset data

    Example:
        >>> df = get_sunrise_sunset_today(40.7128, -74.0060, timezone="America/New_York")
        >>> print(f"Sunrise: {df.iloc[0]['sunrise']}, Sunset: {df.iloc[0]['sunset']}")
    """
    return get_sunrise_sunset_data(
        latitude,
        longitude,
        timezone=timezone,
        date_value="today",
        max_retries=max_retries,
        retry_delay=retry_delay,
        use_cache=use_cache,
    )


def get_sunrise_sunset_range(
    latitude: float,
    longitude: float,
    start_date: Union[str, date, datetime],
    end_date: Union[str, date, datetime],
    timezone: Optional[str] = None,
    max_retries: int = 3,
    retry_delay: float = 5.0,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Get sunrise and sunset times for a date range (up to 365 days).

    Args:
        latitude (float): Latitude of the location in decimal degrees
        longitude (float): Longitude of the location in decimal degrees
        start_date (str/date/datetime): Start date for the range
        end_date (str/date/datetime): End date for the range
        timezone (str, optional): Timezone of the returned times
        max_retries (int): Maximum number of retry attempts for failed requests
        retry_delay (float): Initial delay between retries in seconds (default 5.0)
        use_cache (bool): Whether to use caching for API responses

    Returns:
        pd.DataFrame: DataFrame containing sunrise/sunset data for the date range

    Example:
        >>> df = get_sunrise_sunset_range(40.7128, -74.0060, "2024-01-01", "2024-01-31")
        >>> print(f"Got {len(df)} days of data")
    """
    return get_sunrise_sunset_data(
        latitude,
        longitude,
        timezone=timezone,
        date_start=start_date,
        date_end=end_date,
        max_retries=max_retries,
        retry_delay=retry_delay,
        use_cache=use_cache,
    )


def get_sunrise_sunset_data_with_stale_cache_fallback(
    latitude: float,
    longitude: float,
    timezone: Optional[str] = None,
    date_value: Optional[Union[str, date, datetime]] = None,
    date_start: Optional[Union[str, date, datetime]] = None,
    date_end: Optional[Union[str, date, datetime]] = None,
    time_format: str = "24",
    max_retries: int = 3,
    retry_delay: float = 15.0,
    stale_cache_max_age_days: int = 30,
) -> pd.DataFrame:
    """
    Get sunrise/sunset data with fallback to stale cache if API is unavailable.

    This function first tries the normal API call with fresh cache. If that fails
    due to 503 errors, it will try to serve data from an older cache (up to 30 days old).
    This is useful for Streamlit Cloud deployments where the API might be intermittently unavailable.

    Args:
        latitude (float): Latitude of the location in decimal degrees
        longitude (float): Longitude of the location in decimal degrees
        timezone (str, optional): Timezone of the returned times
        date_value (str/date/datetime, optional): Date for single day query
        date_start (str/date/datetime, optional): Start date for date range queries
        date_end (str/date/datetime, optional): End date for date range queries
        time_format (str): Format for times - "24" for 24-hour, "12" for 12-hour, etc.
        max_retries (int): Maximum number of retry attempts for failed requests
        retry_delay (float): Initial delay between retries in seconds (default 15.0)
        stale_cache_max_age_days (int): Maximum age of stale cache to accept (default 30 days)

    Returns:
        pd.DataFrame: DataFrame containing sunrise/sunset data

    Raises:
        requests.RequestException: If API fails and no cache is available
    """
    try:
        # First try normal API call with regular cache
        return get_sunrise_sunset_data(
            latitude=latitude,
            longitude=longitude,
            timezone=timezone,
            date_value=date_value,
            date_start=date_start,
            date_end=date_end,
            time_format=time_format,
            max_retries=max_retries,
            retry_delay=retry_delay,
            use_cache=True,
            cache_max_age_hours=24,
        )
    except requests.RequestException as e:
        if "503" in str(e) or "Service Unavailable" in str(e):
            print("🔄 API unavailable, checking for stale cache...")

            # Convert dates to strings for cache key
            date_str = None
            start_str = None
            end_str = None

            if date_value is not None:
                if isinstance(date_value, (date, datetime)):
                    date_str = date_value.strftime("%Y-%m-%d")
                else:
                    date_str = str(date_value)

            if date_start is not None:
                if isinstance(date_start, (date, datetime)):
                    start_str = date_start.strftime("%Y-%m-%d")
                else:
                    start_str = str(date_start)

            if date_end is not None:
                if isinstance(date_end, (date, datetime)):
                    end_str = date_end.strftime("%Y-%m-%d")
                else:
                    end_str = str(date_end)

            # Try to load from stale cache
            cache_key = _get_cache_key(
                latitude, longitude, timezone, date_str, start_str, end_str, time_format
            )
            stale_data = _load_from_cache(cache_key, stale_cache_max_age_days * 24)

            if stale_data is not None:
                print("⚠️ Using stale cache data due to API unavailability")
                return stale_data
            else:
                print("❌ No cache available")
                raise e
        else:
            # Re-raise non-503 errors
            raise e


def clear_cache() -> int:
    """
    Clear all cached data.

    Returns:
        int: Number of cache files removed
    """
    try:
        cache_dir = _get_cache_path()
        removed_count = 0

        for cache_file in cache_dir.glob("*.pkl"):
            cache_file.unlink()
            removed_count += 1

        print(f"🗑️ Cleared {removed_count} cache files")
        return removed_count
    except Exception as e:
        print(f"⚠️ Error clearing cache: {e}")
        return 0


def get_cache_info() -> dict:
    """
    Get information about the current cache.

    Returns:
        dict: Cache information including file count, total size, and oldest/newest files
    """
    try:
        cache_dir = _get_cache_path()
        cache_files = list(cache_dir.glob("*.pkl"))

        if not cache_files:
            return {
                "file_count": 0,
                "total_size_mb": 0,
                "cache_dir": str(cache_dir),
                "oldest_file": None,
                "newest_file": None,
            }

        total_size = sum(f.stat().st_size for f in cache_files)
        file_times = [(f, f.stat().st_mtime) for f in cache_files]
        oldest_file = min(file_times, key=lambda x: x[1])
        newest_file = max(file_times, key=lambda x: x[1])

        return {
            "file_count": len(cache_files),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "cache_dir": str(cache_dir),
            "oldest_file": {
                "name": oldest_file[0].name,
                "age_hours": round((time.time() - oldest_file[1]) / 3600, 1),
            },
            "newest_file": {
                "name": newest_file[0].name,
                "age_hours": round((time.time() - newest_file[1]) / 3600, 1),
            },
        }
    except Exception as e:
        return {"error": str(e)}


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
