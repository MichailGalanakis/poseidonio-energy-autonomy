"""Παράμετροι μοντέλου — Ποσειδώνιο Αθλητικό Κέντρο Θεσσαλονίκης.

ΟΛΕΣ οι τιμές εδώ είναι ρητές παραδοχές. Όσες σημειώνονται με [ΑΥΤΟΨΙΑ]
πρέπει να επιβεβαιωθούν/αντικατασταθούν με πραγματικά δεδομένα από την
επιτόπια έρευνα και τους λογαριασμούς κατανάλωσης του Ποσειδωνίου.
"""
from dataclasses import dataclass, field


@dataclass
class Pool:
    """Μία δεξαμενή κολύμβησης."""
    name: str
    length_m: float
    width_m: float
    depth_m: float
    water_temp_c: float          # θερμοκρασία νερού (ΤΟΤΕΕ/FINA: 26–28 °C)
    activity_factor: float       # ASHRAE: 0.5 αδρανής, 0.65 σχολική, 1.0 δημόσια
    hours_open_per_day: float = 15.0

    @property
    def area_m2(self) -> float:
        return self.length_m * self.width_m

    @property
    def volume_m3(self) -> float:
        return self.area_m2 * self.depth_m


@dataclass
class Hall:
    """Ο κλειστός χώρος του κολυμβητηρίου (natatorium)."""
    air_temp_c: float = 29.0        # ASHRAE: 2 °C πάνω από το νερό, όριο ~30
    rh_setpoint: float = 0.60       # σχετική υγρασία 50–60 %
    air_speed_ms: float = 0.10      # ταχύτητα αέρα πάνω από το νερό (<0.15 m/s)
    heat_recovery_eff: float = 0.60 # βαθμός απόδοσης εναλλάκτη ΚΚΜ [ΑΥΤΟΨΙΑ]
    envelope_ua_w_k: float = 12000  # συνολικό UA κελύφους (W/K) [ΑΥΤΟΨΙΑ]


@dataclass
class DomesticHotWater:
    """Ζεστό νερό χρήσης — ντους λουτρών."""
    users_per_day: float = 600      # μέση προσέλευση [ΑΥΤΟΨΙΑ]
    litres_per_user: float = 30.0
    supply_temp_c: float = 40.0


@dataclass
class HeatPump:
    """Αερόψυκτη αντλία θερμότητας αέρα-νερού."""
    carnot_eff: float = 0.45        # λόγος πραγματικού/Carnot COP (τυπικά 0.40–0.50)
    max_cop: float = 6.0
    supply_temp_pool_c: float = 45.0   # χαμηλή θερμοκρασία προσαγωγής → υψηλό COP
    supply_temp_dhw_c: float = 55.0
    capacity_kw_th: float = 1200.0     # ονομαστική θερμική ισχύς — διαστασιολογείται
    backup_gas_eff: float = 0.92       # εφεδρικός λέβητας αιχμής (αν χρειαστεί)


@dataclass
class PVSystem:
    kwp: float = 500.0              # μεταβλητή βελτιστοποίησης (sweep στο run_analysis)
    tilt_deg: float = 30.0
    azimuth_deg: float = 0.0        # 0 = Νότος
    gamma_pmp: float = -0.004       # θερμοκρασιακός συντελεστής ισχύος (/K)
    noct_c: float = 44.0
    pr_other: float = 0.88          # inverter, καλωδιώσεις, ρύπανση, mismatch
    m2_per_kwp: float = 5.0         # απαιτούμενη επιφάνεια ανά kWp
    available_area_m2: float = 4000 # ωφέλιμη στέγη/στέγαστρα [ΑΥΤΟΨΙΑ]


@dataclass
class Economics:
    # Τιμές ενέργειας (2026, προ ΦΠΑ) — τεκμηρίωση στο docs/02-μεθοδολογία.md
    gas_price_eur_kwh: float = 0.085       # φυσικό αέριο ανά kWh καυσίμου [ΛΟΓΑΡΙΑΣΜΟΙ]
    grid_price_eur_kwh: float = 0.165      # προμήθεια+δίκτυο ηλεκτρικής ενέργειας
    injection_price_eur_kwh: float = 0.065 # πίστωση Net Billing (χονδρεμπορική)
    boiler_eff: float = 0.90               # βαθμός απόδοσης υφιστάμενου λέβητα
    # CAPEX
    pv_capex_eur_kwp: float = 750.0
    hp_capex_eur_kwth: float = 320.0
    balance_capex_eur: float = 150_000.0   # δίκτυα, εναλλάκτες, BMS, μελέτες
    # Λειτουργικά & χρηματοοικονομικά
    opex_pct_capex: float = 0.015
    discount_rate: float = 0.05
    lifetime_years: int = 25
    energy_inflation: float = 0.02
    pv_degradation: float = 0.005          # ετήσια απομείωση απόδοσης Φ/Β
    # Συντελεστές εκπομπών (kg CO2 / kWh)
    ef_gas_fuel: float = 0.202             # καύσιμο ΦΑ (ΚΕΝΑΚ/IPCC)
    ef_grid_2026: float = 0.35             # ελληνικό μίγμα 2026 (ΔΑΠΕΕΠ)
    ef_grid_2040: float = 0.12             # προβολή ΕΣΕΚ για το 2040


@dataclass
class Site:
    latitude: float = 40.579     # Ποσειδώνιο, Καλαμαριά
    longitude: float = 22.950
    pools: list = field(default_factory=lambda: [
        Pool("Κύρια δεξαμενή 50 m", 50.0, 25.0, 2.0, 26.5, 0.65),   # [ΑΥΤΟΨΙΑ]
        Pool("Βοηθητική/εκμάθησης", 25.0, 12.5, 1.2, 28.0, 0.65),   # [ΑΥΤΟΨΙΑ]
    ])
    hall: Hall = field(default_factory=Hall)
    dhw: DomesticHotWater = field(default_factory=DomesticHotWater)
    heat_pump: HeatPump = field(default_factory=HeatPump)
    pv: PVSystem = field(default_factory=PVSystem)
    econ: Economics = field(default_factory=Economics)
