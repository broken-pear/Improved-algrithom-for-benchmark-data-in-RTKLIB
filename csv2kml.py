#!/usr/bin/env python3
"""
Convert submission format CSV (gps_week,gps_tow_s,x_ecef_m,y_ecef_m,z_ecef_m)
to Google Earth KML for report visualization
"""
import csv
from pathlib import Path
from tools.legacy_solver import ecef_to_lla


def spp_csv_to_kml(csv_in: Path, kml_out: Path):
    coords = []
    with open(csv_in, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            x = float(row["x_ecef_m"])
            y = float(row["y_ecef_m"])
            z = float(row["z_ecef_m"])
            lat_deg, lon_deg, alt_m = ecef_to_lla(x, y, z)
            # KML order: longitude,latitude,altitude
            coords.append(f"{lon_deg:.8f},{lat_deg:.8f},{alt_m:.2f}")

    kml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
    <Placemark>
        <name>Our Multi‑Constellation SPP Solution</name>
        <Style>
            <LineStyle>
                <color>ff00ffff</color>
                <width>3</width>
            </LineStyle>
        </Style>
        <LineString>
            <tessellate>1</tessellate>
            <coordinates>
{"\n".join(coords)}
            </coordinates>
        </LineString>
    </Placemark>
</Document>
</kml>
"""
    kml_out.write_text(kml_content, encoding="utf‑8")
    print(f"Generated KML: {kml_out.resolve()}")


if __name__ == "__main__":
    # ========= 修改这里指向你的输出csv =========
    INPUT_CSV = Path("./outputs/own_data_out/G05_owndata.csv")
    OUT_KML = Path("./our_owndata_spp.kml")
    spp_csv_to_kml(INPUT_CSV, OUT_KML)
