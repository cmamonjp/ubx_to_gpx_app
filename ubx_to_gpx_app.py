import streamlit as st
from pyubx2 import UBXReader
import gpxpy
import gpxpy.gpx
import io

def ubx_to_gpx(ubx_data: bytes):
    stream = io.BytesIO(ubx_data)
    ubr = UBXReader(stream, protfilter=2)  # UBX only
    gpx = gpxpy.gpx.GPX()
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    point_count = 0
    try:
        for (_, parsed_data) in ubr:
            if parsed_data.identity == "NAV-PVT":
                try:
                    lat = parsed_data.lat * 1e-7
                    lon = parsed_data.lon * 1e-7
                    if lat == 0.0 and lon == 0.0:
                        continue  # 無効な座標はスキップ
                    ele = parsed_data.height / 1000.0
                    time = parsed_data.dt
                    gpx_segment.points.append(
                        gpxpy.gpx.GPXTrackPoint(lat, lon, elevation=ele, time=time)
                    )
                    point_count += 1
                except Exception:
                    continue
    except Exception as e:
        raise ValueError(f"UBXパースエラー: {e}")

    if point_count == 0:
        raise ValueError("UBXファイルに有効なNAV-PVT位置情報が含まれていません。")

    return gpx.to_xml(), point_count

# --- Streamlit UI ---
st.set_page_config(page_title="UBX→GPX変換ツール", layout="centered")
st.title("📍 UBX → GPX 変換ツール")
st.write("u-blox の UBX バイナリログから GPX ファイルを生成します。")

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
        st.error(f"❌ 予期せぬエラーが発生しました: {e}")
