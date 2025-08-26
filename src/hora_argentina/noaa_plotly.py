"""
Plotly visualization functions for solar time data.
"""

from datetime import datetime

import plotly.graph_objects as go

# Predefined trace combinations for common use cases
TRACE_COMBINATIONS = {
    "basic": ["official_sunrise", "official_sunset"],
    "basic_with_noon": ["official_sunrise", "official_sunset", "solar_noon"],
    "photography": [
        "civil_sunrise",
        "civil_sunset",
        "official_sunrise",
        "official_sunset",
    ],
    "photography_with_noon": [
        "civil_sunrise",
        "civil_sunset",
        "official_sunrise",
        "official_sunset",
        "solar_noon",
    ],
    "astronomy": ["astronomical_sunrise", "astronomical_sunset"],
    "navigation": ["nautical_sunrise", "nautical_sunset"],
    "all_sunrise": [
        "official_sunrise",
        "civil_sunrise",
        "nautical_sunrise",
        "astronomical_sunrise",
    ],
    "all_sunset": [
        "official_sunset",
        "civil_sunset",
        "nautical_sunset",
        "astronomical_sunset",
    ],
    "solar_noon_only": ["solar_noon"],
    "civil_twilight": ["civil_sunrise", "civil_sunset"],
    "nautical_twilight": ["nautical_sunrise", "nautical_sunset"],
    "astronomical_twilight": ["astronomical_sunrise", "astronomical_sunset"],
}


def decimal_hours_to_time_string(decimal_hours):
    """Convert decimal hours to HH:MM format, rounded to the closest minute."""
    import math

    if decimal_hours is None or math.isnan(decimal_hours):
        return "N/A"

    # Handle negative hours (wrap around midnight)
    while decimal_hours < 0:
        decimal_hours += 24
    while decimal_hours >= 24:
        decimal_hours -= 24

    # Convert to total minutes and round to nearest minute
    total_minutes = round(decimal_hours * 60)

    # Handle edge case where rounding could give us 24:00
    if total_minutes >= 24 * 60:
        total_minutes = 0

    hours = total_minutes // 60
    minutes = total_minutes % 60

    return f"{hours:02d}:{minutes:02d}"


def plot_yearly_sun_times(df, title=None, show_figure=False, traces=None):
    """
    Plot sunrise and sunset times for all twilight definitions throughout the year.

    This function creates an interactive Plotly visualization showing:
    - Sunrise times (solid lines) and sunset times (dashed lines)
    - All four twilight definitions: Official, Civil, Nautical, and Astronomical
    - Solar noon times (orange solid line) when available in the data
    - Time axis in both decimal hours and HH:MM format
    - Color-coded lines for easy identification

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame from yearly_sun_times_dataframe() containing date and twilight times
    title : str, optional
        Custom title for the plot. If None, generates automatic title.
    show_figure : bool, optional
        Whether to display the figure (default: False)
    traces : list or str, optional
        List of trace types to include in the plot, or a predefined combination name.

        Available trace types:
        - 'official_sunrise', 'official_sunset'
        - 'civil_sunrise', 'civil_sunset'
        - 'nautical_sunrise', 'nautical_sunset'
        - 'astronomical_sunrise', 'astronomical_sunset'
        - 'solar_noon'

        Predefined combinations (use string name):
        - 'basic': official sunrise/sunset only
        - 'basic_with_noon': official times + solar noon
        - 'photography': civil and official times
        - 'photography_with_noon': civil/official times + solar noon
        - 'astronomy': astronomical twilight only
        - 'navigation': nautical twilight only
        - 'all_sunrise': all sunrise times
        - 'all_sunset': all sunset times
        - 'solar_noon_only': solar noon only
        - 'civil_twilight': civil twilight times
        - 'nautical_twilight': nautical twilight times
        - 'astronomical_twilight': astronomical twilight times

        If None, includes all available traces.

    Returns:
    --------
    plotly.graph_objects.Figure
        The plotly figure object that can be further customized or saved

    Example:
    --------
    >>> from hora_argentina.noaa_solar_calculations import yearly_sun_times_dataframe
    >>> from hora_argentina.noaa_plotly import plot_yearly_sun_times
    >>> df = yearly_sun_times_dataframe(-34.6118, -58.3960, -3)  # Buenos Aires
    >>> # Plot only official times and solar noon
    >>> fig = plot_yearly_sun_times(df, title="Buenos Aires Sun Times", traces='basic_with_noon')
    >>> # Or use custom list
    >>> fig = plot_yearly_sun_times(df, traces=['official_sunrise', 'official_sunset', 'solar_noon'])
    """

    # Create figure
    fig = go.Figure()

    # Define colors for different twilight types
    colors = {
        "astronomical": "#1f1f1f",  # Very dark gray (darkest twilight)
        "nautical": "#4a5568",  # Dark gray
        "civil": "#718096",  # Medium gray
        "official": "#f56565",  # Red (sun visible)
    }

    # Spanish names for twilight types
    twilight_names_es = {
        "official": "Oficial",
        "civil": "Civil",
        "nautical": "Náutico",
        "astronomical": "Astronómico",
    }

    # Determine which traces to include
    if traces is None:
        # Include all available traces
        include_all_traces = True
    else:
        # Check if traces is a predefined combination name
        if isinstance(traces, str) and traces in TRACE_COMBINATIONS:
            traces = TRACE_COMBINATIONS[traces]
        elif isinstance(traces, str):
            raise ValueError(
                f"Unknown predefined trace combination: '{traces}'. "
                f"Available combinations: {list(TRACE_COMBINATIONS.keys())}"
            )

        # Filter traces based on user specification
        include_all_traces = False
        traces_set = set(traces)

    # Add traces for each twilight type, grouping sunrise and sunset together
    twilight_types = ["official", "civil", "nautical", "astronomical"]

    for twilight in twilight_types:
        sunrise_col = f"{twilight}_sunrise"
        sunset_col = f"{twilight}_sunset"

        # Check if we should include this twilight type's traces
        include_sunrise = include_all_traces or sunrise_col in traces_set
        include_sunset = include_all_traces or sunset_col in traces_set

        if sunrise_col in df.columns and include_sunrise:
            # Prepare formatted time strings
            sunrise_times_formatted = [
                decimal_hours_to_time_string(time) for time in df[sunrise_col]
            ]

            # Add sunrise trace
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df[sunrise_col],
                    name=f"Amanecer {twilight_names_es[twilight]}",
                    line=dict(color=colors[twilight]),
                    mode="lines",
                    legendgroup=twilight,
                    customdata=sunrise_times_formatted,
                    hovertemplate=f"<b>Amanecer {twilight_names_es[twilight]}</b><br>"
                    + "Hora: %{customdata}<br>"
                    + "<extra></extra>",
                )
            )

        if sunset_col in df.columns and include_sunset:
            # Prepare formatted time strings
            sunset_times_formatted = [
                decimal_hours_to_time_string(time) for time in df[sunset_col]
            ]

            # Add sunset trace
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df[sunset_col],
                    name=f"Atardecer {twilight_names_es[twilight]}",
                    line=dict(color=colors[twilight], dash="dash"),
                    mode="lines",
                    legendgroup=twilight,
                    customdata=sunset_times_formatted,
                    hovertemplate=f"<b>Atardecer {twilight_names_es[twilight]}</b><br>"
                    + "Hora: %{customdata}<br>"
                    + "<extra></extra>",
                )
            )

    # Add solar noon trace if available and requested
    include_solar_noon = include_all_traces or (
        traces is not None and "solar_noon" in traces_set
    )
    if "solar_noon" in df.columns and include_solar_noon:
        solar_noon_times_formatted = [
            decimal_hours_to_time_string(time) for time in df["solar_noon"]
        ]

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=df["solar_noon"],
                name="Mediodía Solar",
                line=dict(color="#f7931e", width=3),  # Orange color, thicker line
                mode="lines",
                legendgroup="solar_noon",
                customdata=solar_noon_times_formatted,
                hovertemplate="<b>Mediodía Solar</b><br>"
                + "Hora: %{customdata}<br>"
                + "<extra></extra>",
            )
        )

    # Customize layout

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        xaxis=dict(title="Fecha", tickangle=45),
        yaxis=dict(
            title="Hora (horas)", tickmode="linear", tick0=0, dtick=2, range=[0, 24]
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.6,
            xanchor="right",
            x=1.0,
            # bgcolor="rgba(255, 255, 255, 0.8)",
            # bordercolor="rgba(0, 0, 0, 0.2)",
            # borderwidth=1,
        ),
        hovermode="x unified",
        # template="plotly_white",
        # width=1000,
        height=450,
        margin=dict(b=0),  # Extra margin for legend
    )

    # Add secondary y-axis with time labels
    fig.update_layout(
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(0, 25, 2)),
            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
        )
    )

    if show_figure:
        fig.show()

    return fig


def plot_twilight_comparison(df, date_range=None, title=None, show_figure=True):
    """
    Plot a comparison of different twilight definitions for a specific date range.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame from yearly_sun_times_dataframe()
    date_range : tuple, optional
        (start_date, end_date) as strings 'YYYY-MM-DD' or datetime objects
    title : str, optional
        Custom title for the plot
    show_figure : bool, optional
        Whether to display the figure (default: True)

    Returns:
    --------
    plotly.graph_objects.Figure
        The plotly figure object
    """

    # Filter data by date range if specified
    plot_df = df.copy()
    if date_range:
        start_date, end_date = date_range
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        plot_df = plot_df[
            (plot_df["date"] >= start_date) & (plot_df["date"] <= end_date)
        ]

    # Create subplots for sunrise and sunset
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=2,
        cols=1,
        subplot_titles=("Horarios de Amanecer", "Horarios de Atardecer"),
        vertical_spacing=0.1,
        shared_xaxes=True,
    )

    # Colors for twilight types
    colors = {
        "astronomical": "#1f1f1f",
        "nautical": "#4a5568",
        "civil": "#718096",
        "official": "#f56565",
    }

    # Spanish names for twilight types
    twilight_names_es = {
        "official": "Oficial",
        "civil": "Civil",
        "nautical": "Náutico",
        "astronomical": "Astronómico",
    }

    twilight_types = ["official", "civil", "nautical", "astronomical"]

    # Add traces grouped by twilight type (sunrise and sunset together)
    for twilight in twilight_types:
        sunrise_col = f"{twilight}_sunrise"
        sunset_col = f"{twilight}_sunset"

        # Add sunrise trace
        if sunrise_col in plot_df.columns:
            # Prepare formatted time strings
            sunrise_times_formatted = [
                decimal_hours_to_time_string(time) for time in plot_df[sunrise_col]
            ]

            fig.add_trace(
                go.Scatter(
                    x=plot_df["date"],
                    y=plot_df[sunrise_col],
                    name=f"Amanecer {twilight_names_es[twilight]}",
                    line=dict(color=colors[twilight]),
                    mode="lines+markers",
                    marker=dict(size=4),
                    legendgroup=twilight,
                    customdata=sunrise_times_formatted,
                    hovertemplate=f"<b>Amanecer {twilight_names_es[twilight]}</b><br>"
                    + "Fecha: %{x}<br>"
                    + "Hora: %{customdata}<br>"
                    + "<extra></extra>",
                ),
                row=1,
                col=1,
            )

        # Add sunset trace
        if sunset_col in plot_df.columns:
            # Prepare formatted time strings
            sunset_times_formatted = [
                decimal_hours_to_time_string(time) for time in plot_df[sunset_col]
            ]

            fig.add_trace(
                go.Scatter(
                    x=plot_df["date"],
                    y=plot_df[sunset_col],
                    name=f"Atardecer {twilight_names_es[twilight]}",
                    line=dict(color=colors[twilight], dash="dash"),
                    mode="lines+markers",
                    marker=dict(size=4),
                    legendgroup=twilight,
                    customdata=sunset_times_formatted,
                    hovertemplate=f"<b>Atardecer {twilight_names_es[twilight]}</b><br>"
                    + "Fecha: %{x}<br>"
                    + "Hora: %{customdata}<br>"
                    + "<extra></extra>",
                ),
                row=2,
                col=1,
            )

    # Add solar noon trace if available (shown on both subplots for reference)
    if "solar_noon" in plot_df.columns:
        solar_noon_times_formatted = [
            decimal_hours_to_time_string(time) for time in plot_df["solar_noon"]
        ]

        # Add to sunrise subplot
        fig.add_trace(
            go.Scatter(
                x=plot_df["date"],
                y=plot_df["solar_noon"],
                name="Mediodía Solar",
                line=dict(color="#f7931e", width=2, dash="dot"),  # Orange dotted line
                mode="lines",
                legendgroup="solar_noon",
                customdata=solar_noon_times_formatted,
                hovertemplate="<b>Mediodía Solar</b><br>"
                + "Fecha: %{x}<br>"
                + "Hora: %{customdata}<br>"
                + "<extra></extra>",
                showlegend=True,
            ),
            row=1,
            col=1,
        )

        # Add to sunset subplot (same trace, no legend)
        fig.add_trace(
            go.Scatter(
                x=plot_df["date"],
                y=plot_df["solar_noon"],
                name="Mediodía Solar",
                line=dict(color="#f7931e", width=2, dash="dot"),
                mode="lines",
                legendgroup="solar_noon",
                customdata=solar_noon_times_formatted,
                hovertemplate="<b>Mediodía Solar</b><br>"
                + "Fecha: %{x}<br>"
                + "Hora: %{customdata}<br>"
                + "<extra></extra>",
                showlegend=False,  # Don't duplicate in legend
            ),
            row=2,
            col=1,
        )

    # Update layout
    if title is None:
        if date_range:
            title = f"Twilight Comparison: {date_range[0]} to {date_range[1]}"
        else:
            year = (
                plot_df.iloc[0]["date"].year
                if not plot_df.empty
                else datetime.now().year
            )
            title = f"Twilight Comparison for {year}"

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        height=450,
        margin=dict(l=30, r=30, t=50, b=50),
        hovermode="x unified",
    )

    # Update y-axes
    for row in [1, 2]:
        fig.update_yaxes(
            title="Time (hours)",
            tickmode="array",
            tickvals=list(range(0, 25, 2)),
            ticktext=[f"{h:02d}:00" for h in range(0, 25, 2)],
            row=row,
            col=1,
        )

    fig.update_xaxes(title="Fecha", row=2, col=1)

    if show_figure:
        fig.show()

    return fig


def plot_day_length_variation(df, title=None, show_figure=True):
    """
    Plot the variation in day length throughout the year.

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame from yearly_sun_times_dataframe()
    title : str, optional
        Custom title for the plot
    show_figure : bool, optional
        Whether to display the figure (default: True)

    Returns:
    --------
    plotly.graph_objects.Figure
        The plotly figure object
    """

    # Calculate day length for official sunrise/sunset
    if "official_sunrise" in df.columns and "official_sunset" in df.columns:
        day_length = df["official_sunset"] - df["official_sunrise"]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["date"],
                y=day_length,
                mode="lines",
                name="Duración del Día",
                line=dict(color="#f56565", width=2),
                fill="tonexty",
                fillcolor="rgba(245, 101, 101, 0.1)",
                hovertemplate="<b>Duración del Día</b><br>"
                + "Fecha: %{x}<br>"
                + "Duración: %{y:.2f} horas<br>"
                + "<extra></extra>",
            )
        )

        if title is None:
            year = df.iloc[0]["date"].year if not df.empty else datetime.now().year
            title = f"Variación de la Duración del Día Durante {year}"

        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=18)),
            xaxis=dict(title="Fecha"),
            yaxis=dict(
                title="Duración del Día (horas)", tickmode="linear", tick0=8, dtick=1
            ),
            # template="plotly_white",
            # width=1000,
            # height=500,
            hovermode="x",
            height=450,
            margin=dict(l=30, r=30, t=50, b=50),
        )

        if show_figure:
            fig.show()

        return fig
    else:
        raise ValueError(
            "El DataFrame debe contener las columnas 'official_sunrise' y 'official_sunset'"
        )
