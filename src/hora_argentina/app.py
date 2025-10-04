#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2025-present U.N. Owen <void@some.where>
#
# SPDX-License-Identifier: MIT

"""
Minimal Streamlit app for displaying Argentina time with interactive map.
"""

import folium
import streamlit as st
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

from hora_argentina import __version__
from hora_argentina.noaa_plotly import plot_yearly_sun_times
from hora_argentina.noaa_solar_calculations import yearly_sun_times_dataframe


def main():
    """Main Streamlit app function."""
    st.set_page_config(
        page_title="Simulador de horas de amacer/anochecer",
        page_icon="🇦🇷",
        layout="centered",
    )

    st.title("🇦🇷 Simulador de horas de amanecer/anochecer")
    st.write(f"Version: {__version__}")

    st.write("""
    Esta aplicación permite explorar distintos esquemas de huso horario para la Argentina y ver cómo cambian los horarios de amanecer y anochecer en cualquier punto del país, a lo largo del año.

    El 21 de agosto de 2025, la Cámara de Diputados dio media sanción a un [proyecto de ley](https://www4.hcdn.gob.ar/dependencias/dsecretaria/Periodo2024/PDF2024/TP2024/1110-D-2024.pdf) que propone modificar el huso horario del país. La iniciativa plantea retrasar una hora los relojes en todo el territorio nacional, pasando del actual UTC -3 a UTC -4, lo que significaría atrasar una hora respecto de la hora actual (al menos durante el invierno).

    Además, el proyecto contempla la posibilidad de aplicar el **horario de verano**, adelantando una hora los relojes durante los meses estivales (UTC -3). Esta medida quedaría sujeta a la decisión del Poder Ejecutivo.
    """)

    # Add Argentina map with time zones
    st.subheader("🗺️ Ubicación")
    st.write(
        "💡 **Haga click en el mapa para seleccionar una ubicación o ingrese una dirección**"
    )

    # Initialize session state for storing last clicked coordinate and zoom
    if "last_clicked_coordinate" not in st.session_state:
        # Set default location to Mendoza
        st.session_state.last_clicked_coordinate = {
            "lat": -32.8895,
            "lng": -68.8458,
            "address": "Mendoza, Argentina",
        }
    if "map_zoom" not in st.session_state:
        st.session_state.map_zoom = 5

    # Address input section
    col1, col2 = st.columns([3, 1])

    with col1:
        # Use the marker's address if available, otherwise empty
        current_address = ""
        if st.session_state.get(
            "last_clicked_coordinate"
        ) and st.session_state.last_clicked_coordinate.get("address"):
            current_address = st.session_state.last_clicked_coordinate["address"]

        # Initialize session state for tracking address input changes
        if "previous_address_input" not in st.session_state:
            st.session_state.previous_address_input = current_address

        address_input = st.text_input(
            "Enter address or location",
            value=current_address,
            placeholder="e.g., Plaza de Mayo, Buenos Aires or Mendoza, Argentina",
            label_visibility="collapsed",
            key="address_input_field",
        )

    with col2:
        search_button = st.button("🔍 Buscar dirección")

    # Check if address input has changed (Enter was pressed)
    address_changed = (
        address_input != st.session_state.previous_address_input
        and address_input.strip() != ""
    )

    # Update the previous address input for next comparison
    if address_changed:
        st.session_state.previous_address_input = address_input

    # Handle address search (triggered by button click or Enter press)
    if (search_button and address_input.strip()) or address_changed:
        try:
            # Initialize geocoder
            geolocator = Nominatim(user_agent="hora_argentina_app")
            location = geolocator.geocode(address_input, timeout=10, language="es")

            if location:
                # Store the geocoded location
                new_coord = {
                    "lat": location.latitude,
                    "lng": location.longitude,
                    "address": location.address,
                }
                st.session_state.last_clicked_coordinate = new_coord
                st.success(f"📍 Encontramos: {location.address}")
                st.rerun()  # Refresh to show the new marker
            else:
                st.error(
                    "❌ Dirección no encontrada. Por favor intente un término diferente."
                )
        except Exception as e:
            st.error(f"❌ Error buscando dirección: {str(e)}")

    # Determine map center based on last clicked location
    if st.session_state.last_clicked_coordinate:
        map_center = [
            st.session_state.last_clicked_coordinate["lat"],
            st.session_state.last_clicked_coordinate["lng"],
        ]
    else:
        map_center = [-38.4161, -63.6167]  # Default Argentina center

    # Create Argentina map centered on last clicked location

    attr = '&copy; <a href="https://ign-argentina.github.io/argenmap-web/#mapa">ArgenMap</a> '

    m = folium.Map(
        location=map_center,
        zoom_start=st.session_state.map_zoom,
        attr=attr,
        tiles="https://wms.ign.gob.ar/geoserver/gwc/service/tms/1.0.0/capabaseargenmap@EPSG%3A3857@png/{z}/{x}/{-y}.png",
    )

    # Add last clicked marker if it exists
    if st.session_state.last_clicked_coordinate:
        coords = st.session_state.last_clicked_coordinate

        # Create uniform popup content
        popup_content = (
            f"📍 Location<br>Lat: {coords['lat']:.4f}<br>Long: {coords['lng']:.4f}"
        )
        if coords.get("address"):
            popup_content = f"📍 {coords['address']}<br>Lat: {coords['lat']:.4f}<br>Long: {coords['lng']:.4f}"

        folium.Marker(
            [coords["lat"], coords["lng"]],
            popup=popup_content,
            tooltip="Ubicación seleccionada",
            icon=folium.Icon(color="red", icon="map-marker"),
        ).add_to(m)

    # Display the map and capture interactions
    st_data = st_folium(
        m,
        use_container_width=True,
        height=200,
        returned_objects=["last_clicked"],
    )

    # Handle map clicks
    if st_data["last_clicked"] is not None:
        clicked_lat = st_data["last_clicked"]["lat"]
        clicked_lng = st_data["last_clicked"]["lng"]

        # Store the current zoom level if available
        if st_data.get("zoom") is not None:
            st.session_state.map_zoom = st_data["zoom"]

        # Try to get address for clicked location via reverse geocoding
        try:
            geolocator = Nominatim(user_agent="hora_argentina_app")
            location = geolocator.reverse(
                f"{clicked_lat}, {clicked_lng}", timeout=5, language="es"
            )
            address = location.address if location else None
        except Exception:
            address = None

        # Store the clicked coordinate with address if available
        new_coord = {"lat": clicked_lat, "lng": clicked_lng}
        if address:
            new_coord["address"] = address
        else:
            new_coord["address"] = None

        st.session_state.last_clicked_coordinate = new_coord
        st.rerun()  # Refresh to show the new marker

    st.subheader("🌅 Gráfico de amanecer y anochecer")

    # Display last clicked coordinate
    if st.session_state.last_clicked_coordinate:
        coords = st.session_state.last_clicked_coordinate

        with st.spinner("Obteniendo información de amanecer/anochecer..."):
            df_3 = yearly_sun_times_dataframe(
                coords["lat"], coords["lng"], timezone_offset=-3
            )
            df_4 = yearly_sun_times_dataframe(
                coords["lat"], coords["lng"], timezone_offset=-4
            )
            df_dual = yearly_sun_times_dataframe(
                coords["lat"],
                coords["lng"],
                timezone_offset=-4,
                summer_timezone_offset=-3,
                summer_start_date=(9, 7),
                summer_end_date=(4, 6),
            )

        if coords["address"]:
            title = f"📌 {coords['address']}"
        else:
            title = f"📌 Lat: {coords['lat']:.4f}, Long: {coords['lng']:.4f}"

    with st.spinner("Generando gráficos..."):
        st.write(
            "💡 **Elija una opción de esquema de huso horario para ver el correspondiente gráfico**"
        )

        tab1, tab2, tab3 = st.tabs(
            ["UTC -3 (actual)", "UTC -4 (propuesto)", "UTC -4 con horario de verano"]
        )

        traces = ["civil_sunrise", "civil_sunset", "solar_noon"]

        with tab1:
            fig = plot_yearly_sun_times(df_3, title=title + " (UTC -3)", traces=traces)

            st.write(
                "💡 **Deslícese sobre la figura para visualizar fechas y horas en detalle**"
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab2:
            fig = plot_yearly_sun_times(df_4, title=title + " (UTC -4)", traces=traces)

            st.write(
                "💡 **Deslícese sobre la figura para visualizar fechas y horas en detalle**"
            )
            st.plotly_chart(fig, use_container_width=True)

        with tab3:
            fig = plot_yearly_sun_times(
                df_dual, title=title + " (UTC -4 con horario de verano)", traces=traces
            )

            st.write(
                "💡 **Deslícese sobre la figura para visualizar fechas y horas en detalle**"
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("ℹ️ Información adicional")
    st.write("""
    Las figuras muestran, según el huso horario elegido, a qué hora ocurren:

    - el amanecer civil,
    - el anochecer civil,
    - y el mediodía solar.

    Así podés comparar fácilmente cómo cambian las horas de luz solar con cada opción.
    """)

    st.info(
        """El amanecer y el anochecer civil son los momentos en que el Sol se encuentra 6 grados por debajo del horizonte. Si el Sol se encuentra por encima de esa altura, se considera que hay suficiente claridad atmosférica como para ver bien y realizar actividades al aire libre sin necesidad de encender luces.""",
        icon="💡",
    )

    st.info(
        """
        El mediodía solar es el momento del día en que el Sol alcanza su punto más alto en el cielo respecto del horizonte en un lugar determinado.
        No siempre coincide con las 12:00 del reloj porque depende justamente del **huso horario**, la **longitud geográfica** del lugar y la llamada **"ecuación del tiempo"** (pequeñas variaciones en la velocidad aparente del Sol a lo largo del año).
        """,
        icon="☀️",
    )

    st.write("""
    Algunas consideraciones:

    - Hoy en día, Argentina usa UTC -3 todo el año.
    - Con UTC -4, el horario estaría más alineado con la posición geográfica del país (es lo que propone el [proyecto de ley](https://www4.hcdn.gob.ar/dependencias/dsecretaria/Periodo2024/PDF2024/TP2024/1110-D-2024.pdf)).
    - La tercera opción combina UTC -4 en invierno y UTC -3 en verano (horario de verano). El proyecto de ley permitiría al Poder Ejecutivo decidir si se aplica y en qué fechas.
    """)

    st.subheader("Limitaciones")
    st.write("""
    - Los cálculos de amanecer y anochecer se basan en modelos astronómicos y pueden no reflejar condiciones locales exactas.
    - Puede haber ligeras discrepancias en los horarios debido a factores como la altitud y condiciones atmosféricas.
    - Para algunas ubicaciones, particularmente en latitudes extremas, los horarios de amanecer y anochecer pueden no tener sentido durante ciertas épocas del año (por ejemplo, sol de medianoche o noche polar).
    """)

    st.subheader("Créditos")
    st.write("""
    - Datos de mapas por [ArgenMap](https://ign-argentina.github.io/argenmap-web/#mapa)
    - Calculadora de amanecer/anochecer basado en la [calculadora de la NOAA](https://gml.noaa.gov/grad/solcalc/calcdetails.html)
    - Otros recursos utilizados: 
        - [Streamlit](https://streamlit.io/)
        - [astropy](https://www.astropy.org/)
        - [plotly](https://plotly.com/python/)
        - [pandas](https://pandas.pydata.org/)
        - [folium](https://python-visualization.github.io/folium/)
        - 🫣 Un poco de ChatGTP y Sonnet4
    """)

    st.subheader("Desarrollado por:")
    st.write("""
    - [Dr. Lucas A. Bignone](https://lucasbignone.com.ar/) ([Instituto de Astronomía y Física del Espacio, CONICET-UBA](www.iafe.uba.ar))
    - Código fuente disponible en [GitHub](https://github.com/lbignone/hora-argentina)
    - Reporte bugs y sugerencias en [GitHub Issues](https://github.com/lbignone/hora-argentina/issues)
    """)


if __name__ == "__main__":
    main()
