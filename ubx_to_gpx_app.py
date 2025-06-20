import streamlit as st
from pyubx2 import UBXReader, UBX_PROTOCOL
import gpxpy
import gpxpy.gpx
import io

def ubx_to_gpx(ubx_data: bytes):
    stream = io.BytesIO(ubx_data)
    ubr = UBXReader(stream, protfilter=UBX_PROTOCOL)

    gpx = gpxpy.gpx.GPX()
    track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(track)
    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    point_count = 0

    for _, parsed_data in ubr:
        if hasattr(parsed_data, 'lat') and hasattr(parsed_data, 'lon'):
            try:
                lat = parsed_data.lat / 1e7
                lon = parsed_data.lon / 1e7
                if lat == 0.0 and lon == 0.0:
                    continue

                ele = getattr(parsed_data, 'height', 0) / 1000.0  # mm → m
                time = getattr(parsed_data, 'dt', None)

                point = gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=ele, time=time)
                segment.points.append(point)
                point_count += 1
            except Exception:
                continue

    if point_count == 0:
        raise ValueError("有効な位置情報が見つかりませんでした（lat/lon ≠ 0 のものがない）")

    return gpx.to_xml(), point_count

# --- Streamlit UI ---
st.set_page_config(page_title="UBX→GPX変換ツール", layout="centered")
st.title("📍 UBX → GPX 変換ツール")
st.write("u-blox の UBX ログファイルから GPX に変換します。")

uploaded_file = st.file_uploader("🔼 UBXファイルをアップロード", type=["ubx"])

if uploaded_file:
    ubx_bytes = uploaded_file.read()

    try:
        gpx_text, point_count = ubx_to_gpx(ubx_bytes)

        st.success(f"✅ 変換成功！トラックポイント数: {point_count}")

        gpx_io = io.BytesIO()
        gpx_io.write(gpx_text.encode("utf-8"))
        gpx_io.seek(0)

        st.download_button(
            label="⬇️ GPXファイルをダウンロード",
            data=gpx_io,
            file_name="converted.gpx",
            mime="application/gpx+xml"
        )

    except ValueError as ve:
        st.error(f"⚠️ 変換失敗: {ve}")
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {e}")
