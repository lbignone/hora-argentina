# 🇦🇷 Hora Argentina - Simulador de Husos Horarios

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://simulador-husos-horarios-argentina.streamlit.app)

Una aplicación web interactiva desarrollada con Streamlit para explorar los efectos de diferentes esquemas de huso horario en Argentina, visualizando cómo cambian los horarios de amanecer y anochecer en cualquier punto del país a lo largo del año.

## 📖 Contexto

El 21 de agosto de 2025, la Cámara de Diputados dio media sanción a un [proyecto de ley](https://www4.hcdn.gob.ar/dependencias/dsecretaria/Periodo2024/PDF2024/TP2024/1110-D-2024.pdf) que propone modificar el huso horario del país, pasando del actual UTC-3 a UTC-4, con la posibilidad de implementar horario de verano (UTC-3) durante los meses estivales.

Esta herramienta permite visualizar y comparar los efectos de estos cambios propuestos.

## ✨ Características

- **Mapa interactivo**: Selecciona cualquier ubicación en Argentina haciendo clic en el mapa
- **Comparación de husos horarios**: Visualiza las diferencias entre UTC-3, UTC-4 y horario de verano
- **Gráficos anuales**: Curvas de amanecer y anochecer para todo el año
- **Datos astronómicos precisos**: Cálculos basados en librerías astronómicas especializadas

## 🚀 Instalación

### Requisitos

- Python >= 3.8

### Instalar desde el código fuente

```bash
git clone https://github.com/tu-usuario/hora-argentina.git
cd hora-argentina
pip install -e .
```

## 🎯 Uso

### Ejecutar la aplicación web

```bash
streamlit run src/hora_argentina/app.py
```

## 🛠️ Dependencias principales

- **Streamlit**: Interfaz web interactiva
- **Folium**: Mapas interactivos
- **Plotly**: Visualizaciones interactivas
- **GeoPy**: Geocodificación y servicios geográficos

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE.txt` para más detalles.

## 🔗 Enlaces útiles

- [Proyecto de ley sobre cambio de huso horario](https://www4.hcdn.gob.ar/dependencias/dsecretaria/Periodo2024/PDF2024/TP2024/1110-D-2024.pdf)
- [Documentación de Streamlit](https://docs.streamlit.io/)

---

Desarrollado con ❤️ para entender mejor los efectos del cambio de huso horario en Argentina.
