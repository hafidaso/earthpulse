"""EarthPulse 3D Earth Evidence Explorer and lightweight 2D DEM fallback."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

import analysis

_FRONTEND_DIR = Path(__file__).parent / 'components' / 'earth_explorer' / 'frontend'
_DEM_PATH = Path(__file__).parent / 'data' / 'morocco_dem_terrarium.json'

if _FRONTEND_DIR.exists():
    _earth_explorer_component = components.declare_component(
        'earth_explorer',
        path=str(_FRONTEND_DIR),
    )
else:
    _earth_explorer_component = None


def load_morocco_dem(dem_path: Path | str | None = None) -> dict[str, Any] | None:
    """Load pre-decoded Mapzen/AWS Terrarium Morocco DEM grid, returning None if unavailable."""
    path = Path(dem_path) if dem_path is not None else _DEM_PATH
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
        required = {'bounds', 'rows', 'cols', 'elevations_m'}
        if not required.issubset(payload.keys()):
            return None
        if len(payload['elevations_m']) != int(payload['rows']):
            return None
        return payload
    except Exception:
        return None


def sample_dem_elevation(dem: dict[str, Any] | None, lat: float, lon: float) -> float | None:
    """Bilinearly sample terrain elevation in meters from DEM metadata if within bounds."""
    if not dem or 'bounds' not in dem:
        return None
    b = dem['bounds']
    if not (b['lat_min'] <= lat <= b['lat_max'] and b['lon_min'] <= lon <= b['lon_max']):
        return None
    rows = int(dem['rows'])
    cols = int(dem['cols'])
    r_f = (b['lat_max'] - lat) / (b['lat_max'] - b['lat_min']) * (rows - 1)
    c_f = (lon - b['lon_min']) / (b['lon_max'] - b['lon_min']) * (cols - 1)
    r0 = max(0, min(rows - 2, int(r_f)))
    c0 = max(0, min(cols - 2, int(c_f)))
    fr = r_f - r0
    fc = c_f - c0
    g = dem['elevations_m']
    val = (
        g[r0][c0] * (1.0 - fr) * (1.0 - fc)
        + g[r0][c0 + 1] * (1.0 - fr) * fc
        + g[r0 + 1][c0] * fr * (1.0 - fc)
        + g[r0 + 1][c0 + 1] * fr * fc
    )
    return round(float(val), 1)


def build_station_payload(
    parameter: str = 'T2M',
    start: int = 1991,
    end: int = 2025,
    interval_mode: str = 'cautious',
) -> list[dict[str, Any]]:
    """Compute non-interpolated station marker summaries directly from unaltered NASA POWER snapshots."""
    spec_unit = analysis.ALL_VARIABLES[parameter][1]
    rate_unit = f'{spec_unit}/dec'
    stations: list[dict[str, Any]] = []
    for city, (lat, lon) in analysis.LOCATIONS.items():
        data = analysis.load_city_dataset(city, parameter=parameter)
        site = analysis.evaluate_site(city, data, parameter, start, end, interval_mode=interval_mode)
        if site['eligible']:
            slope = float(site['result']['slope_decade'])
            ex0 = bool(site['active_excludes_zero'])
            badge = 'Excl. 0' if ex0 else 'Crosses 0'
            metric_text = f"{analysis.format_bound(slope)} {rate_unit} · {badge}"
        else:
            slope = 0.0
            ex0 = False
            metric_text = 'Withheld (<30y)'
        stations.append({
            'name': city,
            'lat': float(lat),
            'lon': float(lon),
            'slope': slope,
            'excludes_zero': ex0,
            'metric_text': metric_text,
            'physiography': analysis.MOROCCO_PHYSIOGRAPHY[city][0],
        })
    return stations


def build_2d_fallback_figure(
    dem: dict[str, Any] | None,
    stations: list[dict[str, Any]],
    selected_city: str = 'Marrakech',
    compare_city: str = 'Casablanca',
) -> go.Figure:
    """Render lightweight 2D Plotly elevation contour map + MERRA-2 grid boxes when 3D WebGL is off/unavailable."""
    fig = go.Figure()
    if dem is not None:
        b = dem['bounds']
        rows = int(dem['rows'])
        cols = int(dem['cols'])
        # Reverse north-to-south rows so y increases northward on Plotly
        lats = [b['lat_min'] + (b['lat_max'] - b['lat_min']) * i / (rows - 1) for i in range(rows)]
        lons = [b['lon_min'] + (b['lon_max'] - b['lon_min']) * j / (cols - 1) for j in range(cols)]
        z_south_north = list(reversed(dem['elevations_m']))
        fig.add_trace(go.Heatmap(
            x=lons,
            y=lats,
            z=z_south_north,
            colorscale=[
                [0.0, '#091f33'],
                [0.44, '#11415e'],
                [0.47, '#355952'],
                [0.58, '#8d8062'],
                [0.78, '#a6623d'],
                [1.0, '#eef3f7'],
            ],
            zmin=-3500,
            zmax=3700,
            colorbar=dict(title='Elev (m)', thickness=12, len=0.72),
            hovertemplate='Lon %{x:.2f}° · Lat %{y:.2f}°<br>Terrain %{z:.0f} m<extra></extra>',
        ))

    shape_map = {
        'Casablanca': 'circle',
        'Rabat': 'triangle-up',
        'Marrakech': 'diamond',
        'Ouarzazate': 'square',
    }
    for item in stations:
        lat, lon = item['lat'], item['lon']
        box = analysis.approximate_grid_footprint(lat, lon)
        is_sel = item['name'] == selected_city
        is_cmp = item['name'] == compare_city
        box_color = '#2dd4bf' if is_sel else ('#f59e0b' if is_cmp else 'rgba(148,179,204,0.55)')
        fig.add_trace(go.Scatter(
            x=box['lons'],
            y=box['lats'],
            mode='lines',
            line=dict(color=box_color, width=2 if (is_sel or is_cmp) else 1, dash='dot'),
            hoverinfo='skip',
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=[lon],
            y=[lat],
            mode='markers+text',
            marker=dict(
                size=14 if is_sel else 11,
                symbol=shape_map.get(item['name'], 'circle'),
                color='#2dd4bf' if is_sel else ('#f59e0b' if item['excludes_zero'] else '#cbd5e1'),
                line=dict(color='#07111a', width=1.6),
            ),
            text=[f"{item['name']} ({item['metric_text']})"],
            textposition='top center',
            textfont=dict(color='#f3f7fa', size=11),
            name=item['name'],
            hovertemplate=(
                f"<b>{item['name']}</b><br>{item['physiography']}<br>"
                f"{item['metric_text']}<br>"
                "MERRA-2 ~0.5° × 0.625° approx box shown<extra></extra>"
            ),
        ))

    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#08121c',
        plot_bgcolor='#08121c',
        height=430,
        margin=dict(l=46, r=18, t=26, b=42),
        xaxis_title='Longitude (°E)',
        yaxis_title='Latitude (°N)',
        yaxis=dict(scaleanchor='x', scaleratio=1.15),
        showlegend=False,
    )
    return fig


def render_earth_explorer(
    selected_city: str = 'Marrakech',
    compare_city: str = 'Casablanca',
    parameter: str = 'T2M',
    start: int = 1991,
    end: int = 2025,
    interval_mode: str = 'cautious',
    key_prefix: str = 'earth_explorer',
    dem_path: Path | str | None = None,
) -> dict[str, Any]:
    """Render the interactive 3D Earth Explorer with bidirectional city selection and clean 2D fallback."""
    dem = load_morocco_dem(dem_path=dem_path)
    stations = build_station_payload(
        parameter=parameter,
        start=start,
        end=end,
        interval_mode=interval_mode,
    )

    mode_key = f'{key_prefix}_use_2d'
    nonce_key = f'{key_prefix}_last_nonce'
    if mode_key not in st.session_state:
        st.session_state[mode_key] = False

    event_result: dict[str, Any] = {
        'selected_city': selected_city,
        'changed': False,
        'dem_loaded': dem is not None,
        'rendered_mode': '3d',
    }

    top_c1, top_c2 = st.columns([3.4, 1.2])
    with top_c1:
        elev_sample = sample_dem_elevation(dem, *analysis.LOCATIONS.get(selected_city, (31.63, -7.98)))
        elev_str = f'~{elev_sample:.0f} m terrain context' if elev_sample is not None else 'terrain metadata active'
        st.caption(
            f"Active focus: **{selected_city}** ({elev_str}) · "
            "Terrain uses Mapzen/AWS Terrarium DEM (NASA SRTM + ETOPO1); MERRA-2 0.5° × 0.625° boxes show cell scale only — trends are never interpolated across relief."
        )
    with top_c2:
        use_2d = st.toggle(
            '2D fallback view',
            key=mode_key,
            help='Switch between the interactive 3D WebGL terrain explorer and lightweight 2D Plotly elevation contours.',
        )

    can_render_3d = (_earth_explorer_component is not None) and (dem is not None) and (not use_2d)

    if can_render_3d:
        comp_val = _earth_explorer_component(
            dem=dem,
            stations=stations,
            selected_city=selected_city,
            compare_city=compare_city,
            parameter=parameter,
            subtitle=(
                f"{analysis.ALL_VARIABLES[parameter][0]} ({start}–{end}) · "
                f"Selected: {selected_city} — click any beacon to load it into the proof below."
            ),
            key=f'{key_prefix}_webgl',
            default=None,
        )
        if isinstance(comp_val, dict) and comp_val.get('nonce') != st.session_state.get(nonce_key):
            st.session_state[nonce_key] = comp_val.get('nonce')
            action = comp_val.get('action')
            if action == 'switch_to_2d':
                st.session_state[mode_key] = True
                st.rerun()
            elif action == 'select_city' and comp_val.get('selected_city') in analysis.LOCATIONS:
                event_result['selected_city'] = comp_val['selected_city']
                event_result['changed'] = True
    else:
        event_result['rendered_mode'] = '2d_fallback'
        if dem is None:
            st.info('Local DEM grid unavailable; showing 2D station & MERRA-2 approximate grid-footprint fallback.')
        fig2d = build_2d_fallback_figure(
            dem=dem,
            stations=stations,
            selected_city=selected_city,
            compare_city=compare_city,
        )
        st.plotly_chart(fig2d, use_container_width=True, key=f'{key_prefix}_2d_chart')
        cols = st.columns(len(stations))
        for col, st_item in zip(cols, stations):
            with col:
                is_sel = st_item['name'] == selected_city
                label = f"{'✓ ' if is_sel else ''}{st_item['name']}"
                if st.button(label, key=f"{key_prefix}_fb_btn_{st_item['name']}", use_container_width=True):
                    event_result['selected_city'] = st_item['name']
                    event_result['changed'] = True

    return event_result
