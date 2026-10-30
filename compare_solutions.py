#!/usr/bin/env python3
"""
Compare three solutions for own‑data validation (Section8.5 lab manual):
1) Your python SPP: GXX_owndata.csv
2) RTKLIB .pos file
3) Receiver NAV‑HPPOSECEF.csv
Output ENU mean/std/2D‑RMS for lab report
"""
import csv
import re
from pathlib import Path
import numpy as np
from tools.legacy_solver import ecef_to_lla, ecef_to_enu


def read_my_spp_csv(csv_path: Path):
    """Read our submission‑format csv: gps_week,gps_tow_s,x_ecef_m,y_ecef_m,z_ecef_m"""
    data = {}
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            tow = round(float(r["gps_tow_s"]), 1)
            xyz = np.array([float(r["x_ecef_m"]), float(r["y_ecef_m"]), float(r["z_ecef_m"])])
            data[tow] = xyz
    return data


def read_rtklib_pos(pos_path: Path):
    """Parse RTKLIB .pos file, skip # comment lines.
    Return dict: key=round(tow,1), value=np.array([x,y,z]) ECEF meters
    """
    data = {}
    # RTKLIB pos列：week, tow, lat, lon, alt, x, y, z ...
    pattern = re.compile(r"^\s*(\d+)\s+(\S+)\s+\S+\s+\S+\s+\S+\s+(\S+)\s+(\S+)\s+(\S+)")
    with open(pos_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("#"):
                continue
            m = pattern.match(line.strip())
            if not m:
                continue
            week = int(m.group(1))
            tow = float(m.group(2))
            x = float(m.group(3))
            y = float(m.group(4))
            z = float(m.group(5))
            key = round(tow, 1)
            data[key] = np.array([x, y, z])
    return data


def read_receiver_navhpp(csv_path: Path):
    """Read NAV‑HPPOSECEF.csv from pyubx2 export
    iTOW is millisecond → convert to second, round 0.1s
    ecefX/Y/Z unit: centimetre → convert to meter (/100)
    """
    data = {}
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            itow_ms = int(r["iTOW"])
            tow = itow_ms / 1000.0
            key = round(tow, 1)
            x = float(r["ecefX"]) / 100.0
            y = float(r["ecefY"]) / 100.0
            z = float(r["ecefZ"]) / 100.0
            data[key] = np.array([x, y, z])
    return data


def calc_diff_stats(xyz_a_dict, xyz_b_dict):
    """
    两组解时间对齐，以b的平均位置做局部ENU坐标系
    返回：E,N,U mean, std, 2D rms, 匹配历元数量
    """
    common_tows = sorted(set(xyz_a_dict.keys()) & set(xyz_b_dict.keys()))
    if len(common_tows) == 0:
        raise RuntimeError("No common epoch! Check your time rounding(0.1s)")

    a_list = np.array([xyz_a_dict[t] for t in common_tows])
    b_list = np.array([xyz_b_dict[t] for t in common_tows])

    b_mean = np.mean(b_list, axis=0)
    lat0, lon0, _ = ecef_to_lla(*b_mean)

    enu_diff = []
    for a_xyz, b_xyz in zip(a_list, b_list):
        dxyz = a_xyz - b_xyz
        e, n, u = ecef_to_enu(*dxyz, lat0, lon0, 0.0)
        enu_diff.append([e, n, u])
    enu_diff = np.array(enu_diff)

    mean_e, mean_n, mean_u = np.mean(enu_diff, axis=0)
    std_e, std_n, std_u = np.std(enu_diff, axis=0, ddof=1)
    err_2d = np.sqrt(enu_diff[:, 0]**2 + enu_diff[:, 1]**2)
    rms_2d = np.sqrt(np.mean(err_2d**2))

    return {
        "N_epoch": len(common_tows),
        "mean_E": mean_e,
        "mean_N": mean_n,
        "mean_U": mean_u,
        "std_E": std_e,
        "std_N": std_n,
        "std_U": std_u,
        "RMSE_2D": rms_2d
    }


if __name__ == "__main__":
    # ===================== 修改这里文件路径！！=====================
    MY_SPP_CSV = Path("./outputs/own_data_out/G05_owndata.csv")
    RTKLIB_POS = Path("./2026_data.pos")
    RECV_CSV = Path("./NAV‑HPPOSECEF.csv")

    my_spp = read_my_spp_csv(MY_SPP_CSV)
    rtklib_sol = read_rtklib_pos(RTKLIB_POS)
    recv_sol = read_receiver_navhpp(RECV_CSV)

    print("===== SPP vs RTKLIB =====")
    res1 = calc_diff_stats(my_spp, rtklib_sol)
    for k, v in res1.items():
        print(f"{k}: {v:.3f}")

    print("\n===== SPP vs Receiver NAV‑HPPOSECEF =====")
    res2 = calc_diff_stats(my_spp, recv_sol)
    for k, v in res2.items():
        print(f"{k}: {v:.3f}")
