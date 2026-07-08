"""Κλιματικά δεδομένα Θεσσαλονίκης — ωριαίο τυπικό μετεωρολογικό έτος (TMY).

Δύο πηγές:
1. load_pvgis_tmy(path): φορτώνει πραγματικό TMY από το PVGIS
   (https://re.jrc.ec.europa.eu/pvg_tools/en/ → TMY → CSV). ΠΡΟΤΙΜΩΜΕΝΟ
   για την τελική διπλωματική.
2. synthetic_tmy(): συνθετικό έτος από τα μηνιαία κλιματικά δεδομένα της
   ΤΟΤΕΕ 20701-3/2010 για τη Θεσσαλονίκη, ώστε το μοντέλο να τρέχει χωρίς
   εξωτερικά αρχεία. Οι ωριαίες κατανομές παράγονται ντετερμινιστικά
   (ημερήσιο ημιτονοειδές θερμοκρασίας, προφίλ ακτινοβολίας αίθριας ημέρας
   κλιμακωμένο στο μηνιαίο σύνολο).

Κλιματική αλλαγή 2040: μέθοδος "morphing" (Belcher et al., 2005) — μηνιαίες
μεταβολές ΔΤ/ΔRH από προβολές EURO-CORDEX/Copernicus εφαρμόζονται στο TMY.
Οι προεπιλεγμένες τιμές ΔΤ είναι ενδεικτικές· αντικαθίστανται με ακριβείς
τιμές από το Copernicus CDS για το κελί της Θεσσαλονίκης.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

DAYS_IN_MONTH = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])

# ΤΟΤΕΕ 20701-3/2010, Θεσσαλονίκη (σταθμός Μίκρα) — μηνιαίες μέσες τιμές
TOTEE_THESSALONIKI = pd.DataFrame({
    "t_mean_c":  [5.2, 6.7, 9.7, 14.2, 19.6, 24.6, 27.0, 26.4, 22.0, 16.2, 11.0, 6.9],
    "rh_mean":   [0.76, 0.72, 0.71, 0.68, 0.64, 0.55, 0.51, 0.53, 0.60, 0.70, 0.77, 0.78],
    "ghi_kwh_m2": [55, 70, 110, 150, 190, 210, 220, 195, 150, 100, 60, 45],
    "t_ground_c": [10.5, 10.0, 11.5, 14.0, 17.5, 20.5, 22.5, 22.5, 21.0, 18.0, 14.5, 12.0],
}, index=range(1, 13))

# Ενδεικτικές μηνιαίες αποκλίσεις 2040 vs σήμερα (EURO-CORDEX ensemble mean,
# Θεσσαλονίκη) — ΝΑ ΑΝΤΙΚΑΤΑΣΤΑΘΟΥΝ με τιμές από Copernicus CDS.
MORPHING_2040 = {
    "rcp45": {"dt_c": [0.9, 0.9, 0.8, 0.8, 0.9, 1.0, 1.1, 1.2, 1.0, 0.9, 0.9, 0.9],
              "drh":  -0.01},
    "rcp85": {"dt_c": [1.2, 1.2, 1.1, 1.1, 1.3, 1.5, 1.7, 1.8, 1.5, 1.3, 1.2, 1.2],
              "drh":  -0.02},
}


def _solar_geometry(lat_deg: float, doy: np.ndarray, hour: np.ndarray):
    """Επιστρέφει cos(ζενίθιας γωνίας) και εξωγήινη ακτινοβολία G0 (W/m²)."""
    lat = np.radians(lat_deg)
    decl = np.radians(23.45) * np.sin(2 * np.pi * (284 + doy) / 365)
    ha = np.radians(15.0 * (hour + 0.5 - 12.0))  # ωριαία γωνία στο μέσο της ώρας
    cos_z = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(ha)
    cos_z = np.clip(cos_z, 0.0, 1.0)
    g0 = 1367.0 * (1 + 0.033 * np.cos(2 * np.pi * doy / 365)) * cos_z
    return cos_z, g0, decl


def synthetic_tmy(latitude: float = 40.579) -> pd.DataFrame:
    """Ωριαίο DataFrame 8760 γραμμών: t_air_c, rh, ghi_w_m2, t_ground_c."""
    idx = pd.date_range("2023-01-01", periods=8760, freq="h")
    doy = idx.dayofyear.to_numpy().astype(float)
    hour = idx.hour.to_numpy().astype(float)
    month = idx.month.to_numpy()

    clim = TOTEE_THESSALONIKI
    t_month = clim["t_mean_c"].to_numpy()[month - 1]
    rh_month = clim["rh_mean"].to_numpy()[month - 1]

    # Ημερήσιο εύρος θερμοκρασίας ~8 °C, ελάχιστο στις 05:00, μέγιστο στις 14:00
    t_air = t_month + 4.0 * np.sin(2 * np.pi * (hour - 9.5) / 24)
    # Η RH κινείται αντίθετα από τη θερμοκρασία μέσα στην ημέρα
    rh = np.clip(rh_month - 0.10 * np.sin(2 * np.pi * (hour - 9.5) / 24), 0.15, 0.98)

    # Ακτινοβολία: προφίλ αίθριας ημέρας κλιμακωμένο στο μηνιαίο σύνολο ΤΟΤΕΕ
    cos_z, g0, _ = _solar_geometry(latitude, doy, hour)
    ghi_clear = 0.75 * g0
    df = pd.DataFrame({"t_air_c": t_air, "rh": rh, "ghi_w_m2": ghi_clear,
                       "month": month}, index=idx)
    target = clim["ghi_kwh_m2"].to_numpy() * 1000.0  # Wh/m²/μήνα
    month_sum = df.groupby("month")["ghi_w_m2"].transform("sum").to_numpy()
    df["ghi_w_m2"] = df["ghi_w_m2"] * target[month - 1] / np.where(month_sum > 0, month_sum, 1)
    df["t_ground_c"] = clim["t_ground_c"].to_numpy()[month - 1]
    df["cos_zenith"] = cos_z
    df["g0_w_m2"] = g0
    return df.drop(columns="month")


def load_pvgis_tmy(path: str, latitude: float = 40.579) -> pd.DataFrame:
    """Φορτώνει PVGIS TMY CSV (v5) στο ίδιο σχήμα με το synthetic_tmy()."""
    raw = pd.read_csv(path, skiprows=16, skipfooter=12, engine="python")
    raw.columns = [c.strip() for c in raw.columns]
    idx = pd.date_range("2023-01-01", periods=8760, freq="h")
    df = pd.DataFrame({
        "t_air_c": raw["T2m"].to_numpy()[:8760],
        "rh": raw["RH"].to_numpy()[:8760] / 100.0,
        "ghi_w_m2": raw["G(h)"].to_numpy()[:8760],
    }, index=idx)
    month = idx.month.to_numpy()
    df["t_ground_c"] = TOTEE_THESSALONIKI["t_ground_c"].to_numpy()[month - 1]
    doy = idx.dayofyear.to_numpy().astype(float)
    hour = idx.hour.to_numpy().astype(float)
    cos_z, g0, _ = _solar_geometry(latitude, doy, hour)
    df["cos_zenith"] = cos_z
    df["g0_w_m2"] = g0
    return df


def morph_to_2040(tmy: pd.DataFrame, scenario: str) -> pd.DataFrame:
    """Εφαρμόζει μηνιαία ΔΤ/ΔRH (morphing) στο TMY για το σενάριο RCP."""
    spec = MORPHING_2040[scenario]
    out = tmy.copy()
    month = out.index.month.to_numpy()
    out["t_air_c"] = out["t_air_c"] + np.asarray(spec["dt_c"])[month - 1]
    out["rh"] = np.clip(out["rh"] + spec["drh"], 0.10, 0.98)
    out["t_ground_c"] = out["t_ground_c"] + 0.7 * np.asarray(spec["dt_c"])[month - 1]
    return out


def saturation_pressure_kpa(t_c: np.ndarray) -> np.ndarray:
    """Πίεση κορεσμού υδρατμών (kPa), τύπος Magnus."""
    t_c = np.asarray(t_c, dtype=float)
    return 0.61094 * np.exp(17.625 * t_c / (t_c + 243.04))


def humidity_ratio(t_c: np.ndarray, rh: np.ndarray, p_atm_kpa: float = 101.325) -> np.ndarray:
    """Ειδική υγρασία w (kg υδρατμών / kg ξηρού αέρα)."""
    pv = rh * saturation_pressure_kpa(t_c)
    return 0.622 * pv / (p_atm_kpa - pv)
