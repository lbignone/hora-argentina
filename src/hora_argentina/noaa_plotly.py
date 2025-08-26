"""
Plotly visualization functions for solar time data.
"""

from datetime import datetime

import plotly.graph_objects as go


def decimal_hours_to_time_string(decimal_hours):
    """Convert decimal hours to HH:MM format, rounded to the closest minute."""
    if decimal_hours is None:
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


def plot_yearly_sun_times(df, title=None, show_figure=True):
    """
    Plot sunrise and sunset times for all twilight definitions throughout the year.

    This function creates an interactive Plotly visualization showing:
    - Sunrise times (solid lines) and sunset times (dashed lines)
    - All four twilight definitions: Official, Civil, Nautical, and Astronomical
    - Time axis in both decimal hours and HH:MM format
    - Color-coded lines for easy identification

    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame from yearly_sun_times_dataframe() containing date and twilight times
    title : str, optional
        Custom title for the plot. If None, generates automatic title.
    show_figure : bool, optional
        Whether to display the figure (default: True)

    Returns:
    --------
    plotly.graph_objects.Figure
        The plotly figure object that can be further customized or saved

    Example:
    --------
    >>> from hora_argentina.noaa_solar_calculations import yearly_sun_times_dataframe
    >>> from hora_argentina.noaa_plotly import plot_yearly_sun_times
    >>> df = yearly_sun_times_dataframe(-34.6118, -58.3960, -3)  # Buenos Aires
    >>> fig = plot_yearly_sun_times(df, title="Buenos Aires Sun Times")
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

    # Add traces for each twilight type
    twilight_types = ["astronomical", "nautical", "civil", "official"]

    for twilight in twilight_types:
        sunrise_col = f"{twilight}_sunrise"
        sunset_col = f"{twilight}_sunset"

        if sunrise_col in df.columns and sunset_col in df.columns:
            # Prepare formatted time strings
            sunrise_times_formatted = [
                decimal_hours_to_time_string(time) for time in df[sunrise_col]
            ]
            sunset_times_formatted = [
                decimal_hours_to_time_string(time) for time in df[sunset_col]
            ]

            # Add sunrise trace
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df[sunrise_col],
                    name=f"{twilight.title()} Sunrise",
                    line=dict(color=colors[twilight]),
                    mode="lines",
                    customdata=sunrise_times_formatted,
                    hovertemplate=f"<b>{twilight.title()} Sunrise</b><br>"
                    + "Date: %{x}<br>"
                    + "Time: %{customdata}<br>"
                    + "<extra></extra>",
                )
            )

            # Add sunset trace
            fig.add_trace(
                go.Scatter(
                    x=df["date"],
                    y=df[sunset_col],
                    name=f"{twilight.title()} Sunset",
                    line=dict(color=colors[twilight], dash="dash"),
                    mode="lines",
                    customdata=sunset_times_formatted,
                    hovertemplate=f"<b>{twilight.title()} Sunset</b><br>"
                    + "Date: %{x}<br>"
                    + "Time: %{customdata}<br>"
                    + "<extra></extra>",
                )
            )

    # Customize layout

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=18)),
        xaxis=dict(title="Date", tickangle=45),
        yaxis=dict(
            title="Time (hours)", tickmode="linear", tick0=0, dtick=2, range=[0, 24]
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.01,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.2)",
            borderwidth=1,
        ),
        hovermode="x unified",
        template="plotly_white",
        width=1000,
        height=600,
        margin=dict(r=150),  # Extra margin for legend
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
        subplot_titles=("Sunrise Times", "Sunset Times"),
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

    twilight_types = ["astronomical", "nautical", "civil", "official"]

    # Add sunrise traces
    for twilight in twilight_types:
        sunrise_col = f"{twilight}_sunrise"
        if sunrise_col in plot_df.columns:
            # Prepare formatted time strings
            sunrise_times_formatted = [
                decimal_hours_to_time_string(time) for time in plot_df[sunrise_col]
            ]

            fig.add_trace(
                go.Scatter(
                    x=plot_df["date"],
                    y=plot_df[sunrise_col],
                    name=f"{twilight.title()}",
                    line=dict(color=colors[twilight]),
                    mode="lines+markers",
                    marker=dict(size=4),
                    legendgroup=twilight,
                    customdata=sunrise_times_formatted,
                    hovertemplate=f"<b>{twilight.title()} Sunrise</b><br>"
                    + "Date: %{x}<br>"
                    + "Time: %{customdata}<br>"
                    + "<extra></extra>",
                ),
                row=1,
                col=1,
            )

    # Add sunset traces
    for twilight in twilight_types:
        sunset_col = f"{twilight}_sunset"
        if sunset_col in plot_df.columns:
            # Prepare formatted time strings
            sunset_times_formatted = [
                decimal_hours_to_time_string(time) for time in plot_df[sunset_col]
            ]

            fig.add_trace(
                go.Scatter(
                    x=plot_df["date"],
                    y=plot_df[sunset_col],
                    name=f"{twilight.title()}",
                    line=dict(color=colors[twilight]),
                    mode="lines+markers",
                    marker=dict(size=4),
                    legendgroup=twilight,
                    showlegend=False,  # Don't duplicate legend
                    customdata=sunset_times_formatted,
                    hovertemplate=f"<b>{twilight.title()} Sunset</b><br>"
                    + "Date: %{x}<br>"
                    + "Time: %{customdata}<br>"
                    + "<extra></extra>",
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
        template="plotly_white",
        width=1000,
        height=800,
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

    fig.update_xaxes(title="Date", row=2, col=1)

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
                name="Day Length",
                line=dict(color="#f56565", width=2),
                fill="tonexty",
                fillcolor="rgba(245, 101, 101, 0.1)",
                hovertemplate="<b>Day Length</b><br>"
                + "Date: %{x}<br>"
                + "Length: %{y:.2f} hours<br>"
                + "<extra></extra>",
            )
        )

        if title is None:
            year = df.iloc[0]["date"].year if not df.empty else datetime.now().year
            title = f"Day Length Variation Throughout {year}"

        fig.update_layout(
            title=dict(text=title, x=0.5, font=dict(size=18)),
            xaxis=dict(title="Date"),
            yaxis=dict(title="Day Length (hours)", tickmode="linear", tick0=8, dtick=1),
            template="plotly_white",
            width=1000,
            height=500,
            hovermode="x",
        )

        if show_figure:
            fig.show()

        return fig
    else:
        raise ValueError(
            "DataFrame must contain 'official_sunrise' and 'official_sunset' columns"
        )
