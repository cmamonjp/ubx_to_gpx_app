import streamlit as st
from pyubx2 import UBXReader
import gpxpy
import gpxpy.gpx
import io

def ubx_to_gpx(ubx_data):
    stream = io.BytesIO(ubx_data)
    ubr = UBXReader(stream, protfilter=2)  # Only UBX protocol
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    for (raw_data, parsed_data) in ubr:
        if parsed_data.identity == 'NAV-PVT':
            try:
                lat = parsed_data.lat * 1e-7
                lon = parsed_data.lon * 1e-7
                ele = parsed_data.height / 1000.0  # mm to m
                time = parsed_data.dt
                gpx_segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=ele, time=time))
            except Exception:
                continue

    return gpx.to_xml()

# Streamlit UI
st.title("UBX → GPX 変換ツール")
uploaded_file = st.file_uploader("UBXファイルをアップロードしてください", type=["ubx"])

if uploaded_file:
    ubx_bytes = uploaded_file.read()
    try:
        gpx_data = ubx_to_gpx(ubx_bytes)
        st.success("変換成功！以下からダウンロードできます")

        gpx_io = io.BytesIO()
        gpx_io.write(gpx_data.encode('utf-8'))
        gpx_io.seek(0)

        st.download_button(
            label="GPXファイルをダウンロード",
            data=gpx_io,
            file_name="converted.gpx",
            mime="application/gpx+xml"
        )
    except Exception as e:
        st.error(f"変換中にエラーが発生しました: {e}")
