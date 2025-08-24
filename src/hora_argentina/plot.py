import math
from datetime import datetime

import pytz
from bokeh.models import (
    ColumnDataSource,
    FuncTickFormatter,
    HoverTool,
    Label,
    Legend,
    ResetTool,
    SaveTool,
    Span,
    WheelZoomTool,
)
from bokeh.plotting import figure

from hora_argentina.timeutils import first_sunday


def plot(data_dict, summer_time=False):
    source = ColumnDataSource(data=data_dict)

    wheel_zoom = WheelZoomTool(dimensions="width")
    save_tool = SaveTool(name="hora_solar.png")
    reset_tool = ResetTool()

    p = figure(
        x_axis_type="datetime",
        y_axis_type="datetime",
        tools=[save_tool, reset_tool],
        toolbar_location="above",
    )

    p.add_tools(wheel_zoom)

    p.title.text_font_size = "15px"

    formatter_code = """
        var h = Math.floor(tick);
        var m = Math.floor((tick - h) * 60);
        return ('0' + h).slice(-2) + ":" + ('0' + m).slice(-2);
    """

    p.yaxis.formatter = FuncTickFormatter(code=formatter_code)

    # h_formatter = CustomJSHover(
    #     code="""
    #     var h = Math.floor(value);
    #     var m = Math.floor((value - h) * 60);
    #     return ('0' + h).slice(-2) + ":" + ('0' + m).slice(-2);
    # """
    # )

    # hover = HoverTool(
    #     tooltips=[("Fecha", "@date{%F}"), ("Hora", "$snap_y{custom}")],
    #     formatters={
    #         "@date": "datetime",  # use 'datetime' formatter for date
    #         "$snap_y": h_formatter,
    #     },
    #     mode="vline",
    # )

    hover = HoverTool()
    p.add_tools(hover)

    p.add_layout(Legend(), "right")

    p.yaxis.ticker.desired_num_ticks = 20

    p.xaxis.axis_label = "Fecha"
    p.yaxis.axis_label = "Hora"

    p.line(
        "date",
        "sunrise",
        source=source,
        line_width=2,
        color="blue",
        legend_label="Amanecer civil",
    )
    p.line(
        "date",
        "noon",
        source=source,
        line_width=2,
        color="black",
        line_dash="dashed",
        legend_label="Mediodía solar",
    )
    p.line(
        "date",
        "sunset",
        source=source,
        line_width=2,
        color="orange",
        legend_label="Anochecer civil",
    )

    p.varea(
        x="date",
        y1="sunrise",
        y2="sunset",
        source=source,
        fill_color="lightgoldenrodyellow",
        alpha=0.5,
    )

    if summer_time:
        s = datetime.combine(
            first_sunday(2025, 4), datetime.min.time(), tzinfo=pytz.FixedOffset(-180)
        )
        e = datetime.combine(
            first_sunday(2025, 9), datetime.min.time(), tzinfo=pytz.FixedOffset(-180)
        )

        dst_start = Span(
            location=s, dimension="height", line_color="#009E73", line_width=5
        )

        dst_end = Span(
            location=e, dimension="height", line_color="#009E73", line_width=5
        )

        p.add_layout(dst_start)
        p.add_layout(dst_end)

        label = Label(x=s, y=15, text="UTC -4", angle=math.pi / 2, x_offset=25)
        p.add_layout(label)

        label = Label(x=s, y=15, text="UTC -3", angle=math.pi / 2, x_offset=-10)
        p.add_layout(label)

        label = Label(x=e, y=15, text="UTC -3", angle=math.pi / 2, x_offset=25)
        p.add_layout(label)

        label = Label(x=e, y=15, text="UTC -4", angle=math.pi / 2, x_offset=-10)
        p.add_layout(label)

    return p
