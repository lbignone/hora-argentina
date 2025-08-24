"""
Simple Plotly plotting functions for sunrise/sunset data.
"""

import locale
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go

# Try to set Spanish locale
try:
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_TIME, "es_ES")
    except locale.Error:
        # Fallback to default if Spanish locale not available
        pass


def plot_sunrise_sunset_curves(
    df: pd.DataFrame, title: str = "Horarios de Amanecer y Anochecer"
) -> tuple:
    """
    Create a simple Plotly chart showing sunrise and sunset curves.

    Args:
        df (pd.DataFrame): DataFrame with columns 'date', 'sunrise', 'sunset'
        title (str): Title for the chart

    Returns:
        tuple: (df_plot, fig, config) - DataFrame, Plotly figure object, and config dict
    """
    # Ensure we have the required columns
    required_columns = ["date", "sunrise", "sunset"]
    if not all(col in df.columns for col in required_columns):
        raise ValueError(
            "DataFrame must contain 'date', 'sunrise', and 'sunset' columns"
        )

    # Check if dawn and dusk data is available for twilight areas
    has_twilight = all(col in df.columns for col in ["dawn", "dusk"])

    # Check if first_light and last_light data is available for astronomical twilight
    has_astronomical_twilight = all(
        col in df.columns for col in ["first_light", "last_light"]
    )

    # Check if solar_noon data is available
    has_solar_noon = "solar_noon" in df.columns

    if df.empty:
        raise ValueError("DataFrame is empty")

    # Create a copy to avoid modifying the original
    df_plot = df.copy()

    # Convert time strings to datetime objects for plotting (using dummy date)
    dummy_date = datetime(2024, 1, 1)  # Same date for all rows to focus on time only

    def parse_time(time_str):
        """Convert time string to datetime object using dummy date"""
        if pd.isna(time_str):
            return None
        try:
            # Parse the time string
            if isinstance(time_str, (pd.Timestamp, datetime)):
                time_obj = time_str.time()
            else:
                time_obj = pd.to_datetime(time_str).time()

            # Combine with dummy date to create datetime for plotting
            return datetime.combine(dummy_date.date(), time_obj)
        except Exception:
            return None

    df_plot["sunrise_time"] = df_plot["sunrise"].apply(parse_time)
    df_plot["sunset_time"] = df_plot["sunset"].apply(parse_time)

    # Parse dawn and dusk times if available
    if has_twilight:
        df_plot["dawn_time"] = df_plot["dawn"].apply(parse_time)
        df_plot["dusk_time"] = df_plot["dusk"].apply(parse_time)

    # Parse first_light and last_light times if available
    if has_astronomical_twilight:
        df_plot["first_light_time"] = df_plot["first_light"].apply(parse_time)
        df_plot["last_light_time"] = df_plot["last_light"].apply(parse_time)

    # Parse solar_noon time if available
    if has_solar_noon:
        df_plot["solar_noon_time"] = df_plot["solar_noon"].apply(parse_time)

    def adjust_dusk_times_for_midnight_crossing(dt):
        """
        Adjust dusk-related times that cross midnight to be represented as 24+ hours.
        For example, 1 AM becomes 25:00, 2 AM becomes 26:00, etc.
        """
        if pd.isna(dt) or dt is None:
            return dt

        # If the time is in the early morning hours (midnight to 6 AM),
        # assume it's a dusk time that crossed midnight
        if dt.hour < 6:  # Times from 00:00 to 05:59
            # Add 24 hours worth of seconds to represent as 24+ hour
            from datetime import timedelta

            adjusted_dt = dt + timedelta(days=1)
            return adjusted_dt
        return dt

    def adjust_dawn_times_for_before_midnight(dt):
        """
        Adjust dawn-related times that occur before midnight to be represented as negative hours.
        For example, 23:00 becomes -1:00, 22:00 becomes -2:00, etc.
        """
        if pd.isna(dt) or dt is None:
            return dt

        # If the time is in the late evening hours (18:00 to 23:59),
        # assume it's a dawn time that occurs before midnight
        if dt.hour >= 18:  # Times from 18:00 to 23:59
            # Subtract 24 hours to represent as negative hour
            from datetime import timedelta

            adjusted_dt = dt - timedelta(days=1)
            return adjusted_dt
        return dt

    # Adjust dusk-related times that might cross midnight
    if has_twilight:
        df_plot["dusk_time"] = df_plot["dusk_time"].apply(
            adjust_dusk_times_for_midnight_crossing
        )
        # Adjust dawn-related times that might occur before midnight
        df_plot["dawn_time"] = df_plot["dawn_time"].apply(
            adjust_dawn_times_for_before_midnight
        )

    if has_astronomical_twilight:
        df_plot["last_light_time"] = df_plot["last_light_time"].apply(
            adjust_dusk_times_for_midnight_crossing
        )
        # Adjust first_light times that might occur before midnight
        df_plot["first_light_time"] = df_plot["first_light_time"].apply(
            adjust_dawn_times_for_before_midnight
        )

    # Filter out any rows with invalid times
    required_time_columns = ["sunrise_time", "sunset_time"]
    if has_twilight:
        required_time_columns.extend(["dawn_time", "dusk_time"])
    if has_astronomical_twilight:
        required_time_columns.extend(["first_light_time", "last_light_time"])

    df_plot = df_plot.dropna(subset=required_time_columns)

    if df_plot.empty:
        raise ValueError("No valid sunrise/sunset times found in the data")

    # Create Spanish month names mapping
    spanish_months = {
        1: "Ene",
        2: "Feb",
        3: "Mar",
        4: "Abr",
        5: "May",
        6: "Jun",
        7: "Jul",
        8: "Ago",
        9: "Sep",
        10: "Oct",
        11: "Nov",
        12: "Dic",
    }

    # Add Spanish formatted date column
    df_plot["fecha_es"] = df_plot["date"].apply(
        lambda x: f"{x.day} {spanish_months[x.month]}"
    )

    # Create the figure
    fig = go.Figure()

    # Add night time background areas
    # We'll create night areas that extend beyond the twilight periods
    # Night time is considered the time before first_light and after last_light
    if has_astronomical_twilight:
        # Create times for midnight and end of day for night background
        midnight_time = datetime.combine(dummy_date.date(), datetime.min.time())

        # Calculate the maximum and minimum time range considering adjusted times
        max_time_in_data = max(
            [
                df_plot["last_light_time"].max()
                if not df_plot["last_light_time"].isna().all()
                else midnight_time,
                datetime.combine(
                    dummy_date.date(), datetime.max.time().replace(microsecond=0)
                ),
            ]
        )

        min_time_in_data = min(
            [
                df_plot["first_light_time"].min()
                if not df_plot["first_light_time"].isna().all()
                else midnight_time,
                midnight_time,
            ]
        )

        # Early night (last_light to max time in data or end of day)
        fig.add_trace(
            go.Scatter(
                x=df_plot["date"].tolist() + df_plot["date"].tolist()[::-1],
                y=df_plot["last_light_time"].tolist()
                + [max_time_in_data] * len(df_plot),
                fill="toself",
                # fillcolor="#2f454d",
                fillcolor="rgba(47, 69, 77, 0.8)",
                line=dict(width=0),
                mode="lines",
                name="Noche",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # Late night (min time in data to first_light)
        fig.add_trace(
            go.Scatter(
                x=df_plot["date"].tolist() + df_plot["date"].tolist()[::-1],
                y=[min_time_in_data] * len(df_plot)
                + df_plot["first_light_time"].tolist()[::-1],
                fill="toself",
                # fillcolor="#2f454d",
                fillcolor="rgba(47, 69, 77, 0.8)",
                line=dict(width=0),
                mode="lines",
                name="Noche",
                showlegend=False,  # Don't duplicate legend entry
                hoverinfo="skip",
            )
        )

    # Add astronomical twilight areas if data is available (first_light to dawn and dusk to last_light)
    if has_astronomical_twilight:
        # Morning astronomical twilight (first_light to dawn)
        if has_twilight:  # Only add if we also have dawn data
            fig.add_trace(
                go.Scatter(
                    x=df_plot["date"].tolist() + df_plot["date"].tolist()[::-1],
                    y=df_plot["first_light_time"].tolist()
                    + df_plot["dawn_time"].tolist()[::-1],
                    fill="toself",
                    # fillcolor="#586a70",
                    fillcolor="rgba(88, 106, 112, 0.8)",
                    line=dict(width=0),
                    mode="lines",
                    name="Crepúsculo astronómico matutino",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        # Evening astronomical twilight (dusk to last_light)
        if has_twilight:  # Only add if we also have dusk data
            fig.add_trace(
                go.Scatter(
                    x=df_plot["date"].tolist() + df_plot["date"].tolist()[::-1],
                    y=df_plot["dusk_time"].tolist()
                    + df_plot["last_light_time"].tolist()[::-1],
                    fill="toself",
                    # fillcolor="#586a70",
                    fillcolor="rgba(88, 106, 112, 0.8)",
                    line=dict(width=0),
                    mode="lines",
                    name="Crepúsculo astronómico vespertino",
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

    # Add twilight areas if data is available (dawn to sunrise and sunset to dusk)
    if has_twilight:
        # Morning twilight (dawn to sunrise)
        fig.add_trace(
            go.Scatter(
                x=df_plot["date"].tolist() + df_plot["date"].tolist()[::-1],
                y=df_plot["dawn_time"].tolist()
                + df_plot["sunrise_time"].tolist()[::-1],
                fill="toself",
                # fillcolor="#96bbc8",
                fillcolor="rgba(150, 187, 200, 0.8)",
                line=dict(width=0),
                mode="lines",
                name="Crepúsculo matutino",
                showlegend=False,
                hoverinfo="skip",
            )
        )

        # Evening twilight (sunset to dusk)
        fig.add_trace(
            go.Scatter(
                x=df_plot["date"].tolist() + df_plot["date"].tolist()[::-1],
                y=df_plot["sunset_time"].tolist() + df_plot["dusk_time"].tolist()[::-1],
                fill="toself",
                # fillcolor="#96bbc8",
                fillcolor="rgba(150, 187, 200, 0.8)",
                line=dict(width=0),
                mode="lines",
                name="Crepúsculo vespertino",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Add filled area between sunrise and sunset (daylight hours)
    fig.add_trace(
        go.Scatter(
            x=df_plot["date"].tolist() + df_plot["date"].tolist()[::-1],
            y=df_plot["sunrise_time"].tolist() + df_plot["sunset_time"].tolist()[::-1],
            fill="toself",
            # fillcolor="#b0dae7",
            fillcolor="rgba(176, 218, 231, 0.8)",
            line=dict(width=0),
            mode="lines",
            name="Día",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Add sunrise curve
    fig.add_trace(
        go.Scatter(
            x=df_plot["date"],
            y=df_plot["dawn_time"],
            mode="lines",
            name="Amanecer civil",
            line=dict(color="orange", width=3),
            hovertemplate="<b>%{fullData.name}</b><br>Hora: %{y}<extra></extra>",
        )
    )

    # Add solar noon curve if available
    if has_solar_noon:
        fig.add_trace(
            go.Scatter(
                x=df_plot["date"],
                y=df_plot["solar_noon_time"],
                mode="lines",
                name="Mediodía solar",
                line=dict(color="gold", width=2),
                hovertemplate="<b>%{fullData.name}</b><br>Hora: %{y}<extra></extra>",
            )
        )

    # Add sunset curve
    fig.add_trace(
        go.Scatter(
            x=df_plot["date"],
            y=df_plot["dusk_time"],
            mode="lines",
            name="Anochecer civil",
            line=dict(color="darkred", width=3),
            hovertemplate="<b>%{fullData.name}</b><br>Hora: %{y}<extra></extra>",
        )
    )

    # Update layout with Spanish locale
    fig.update_layout(
        # title=dict(text=title, x=0, font=dict(size=12)),
        title=title,
        xaxis_title="Fecha",
        yaxis_title="Hora del Día",
        xaxis=dict(
            tickformat="%d %b",
            tickmode="auto",
            # Spanish month names
            ticktext=None,
            # Set range to show full date range
            range=[df_plot["date"].min(), df_plot["date"].max()],
        ),
        yaxis=dict(
            tickformat="%H:%M",
            dtick=3600000,  # 1 hour in milliseconds
            # Set range to accommodate times that might go beyond 24 hours or be negative
            range=[
                # Calculate min time from all time columns, allowing for negative times
                min(
                    [
                        df_plot["sunrise_time"].min()
                        if not df_plot["sunrise_time"].isna().all()
                        else datetime.combine(dummy_date.date(), datetime.min.time()),
                        df_plot["sunset_time"].min()
                        if not df_plot["sunset_time"].isna().all()
                        else datetime.combine(dummy_date.date(), datetime.min.time()),
                        df_plot["dawn_time"].min()
                        if has_twilight and not df_plot["dawn_time"].isna().all()
                        else datetime.combine(dummy_date.date(), datetime.min.time()),
                        df_plot["first_light_time"].min()
                        if has_astronomical_twilight
                        and not df_plot["first_light_time"].isna().all()
                        else datetime.combine(dummy_date.date(), datetime.min.time()),
                        datetime.combine(
                            dummy_date.date(), datetime.min.time()
                        ),  # fallback to start of day
                    ]
                ),
                # Calculate max time from all time columns, defaulting to end of day
                max(
                    [
                        df_plot["sunrise_time"].max()
                        if not df_plot["sunrise_time"].isna().all()
                        else datetime.combine(dummy_date.date(), datetime.min.time()),
                        df_plot["sunset_time"].max()
                        if not df_plot["sunset_time"].isna().all()
                        else datetime.combine(dummy_date.date(), datetime.min.time()),
                        df_plot["dusk_time"].max()
                        if has_twilight and not df_plot["dusk_time"].isna().all()
                        else datetime.combine(dummy_date.date(), datetime.min.time()),
                        df_plot["last_light_time"].max()
                        if has_astronomical_twilight
                        and not df_plot["last_light_time"].isna().all()
                        else datetime.combine(dummy_date.date(), datetime.min.time()),
                        datetime.combine(
                            dummy_date.date(),
                            datetime.max.time().replace(microsecond=0),
                        ),  # fallback to end of day
                    ]
                ),
            ],
        ),
        hovermode="x unified",
        template="plotly_white",
        # width=800,
        height=700,
        margin=dict(l=30, r=30, t=50, b=50),
        showlegend=False,
        # Set locale to Spanish
        font=dict(family="Arial, sans-serif"),
        xaxis_fixedrange=True,
        yaxis_fixedrange=True,
        dragmode=False,
    )

    # Configuration to hide the toolbar
    config = {
        "displayModeBar": True,  # This completely hides the toolbar
        "staticPlot": False,  # Keep interactivity but hide toolbar,
        "locale": "es",
    }

    return df_plot, fig, config
