"""Παράμετροι μοντέλου — Ποσειδώνιο Αθλητικό Κέντρο Θεσσαλονίκης.

ΟΛΕΣ οι τιμές εδώ είναι ρητές παραδοχές. Πηγές:
  [ΣΗΘΥΑ]  Η/Μ Μελέτη Συστήματος Τριπαραγωγής, ΓΓΑ/ΤΕΑΑΕ 07/2024
  [ΕΞΕ]    Μελέτη Η/Μ Παρεμβάσεων Εξοικονόμησης Ενέργειας, ΓΓΑ/ΤΕΑΑΕ 07/2024
  [ΑΥΤΟΨΙΑ] εκκρεμεί επιβεβαίωση επιτόπου
  [ΒΑΘΜΟΝΟΜΗΣΗ] τιμή ρυθμισμένη ώστε το S0 να αναπαράγει τον PTZ μετρητή ΕΔΑ
Αναλυτική τεκμηρίωση: docs/05-πραγματικά-δεδομένα.md
"""
from dataclasses import dataclass, field


@dataclass
class Pool:
    """Μία δεξαμενή κολύμβησης."""
    name: str
    length_m: float
    width_m: float
    depth_m: float
    water_temp_c: float          # [ΣΗΘΥΑ]: 24 °C πισίνες 50×21, 31 °C εκμάθησης
    activity_factor: float       # ASHRAE: 0.5 αδρανής, 0.65 σχολική, 1.0 δημόσια
    hours_open_per_day: float = 15.0
    indoor: bool = True
    air_speed_ms: float | None = None  # επιβολή για εξωτερική δεξαμενή (άνεμος)
    heated_months: tuple | None = None  # None → site.heating_months, () → αθέρμαντη

    @property
    def area_m2(self) -> float:
        return self.length_m * self.width_m

    @property
    def volume_m3(self) -> float:
        return self.area_m2 * self.depth_m


@dataclass
class Hall:
    """Ο κλειστός χώρος του κολυμβητηρίου (natatorium).

    Το [ΣΗΘΥΑ σ.19] ορίζει ελάχιστη θερμοκρασία 18 °C χειμώνα / 25 °C θέρος
    μέσω ΚΚΜ. Η πραγματική θερμοκρασία αίθουσας πάνω από το νερό λαμβάνεται
    κατά ASHRAE ≈ 2 °C πάνω από το νερό (26 °C) — καθοριστική για την
    εξάτμιση· επιβεβαίωση [ΑΥΤΟΨΙΑ].
    """
    air_temp_winter_c: float = 26.0  # [ΒΑΘΜΟΝΟΜΗΣΗ· ASHRAE νερό+2 °C]
    air_temp_summer_c: float = 25.0  # θερινή περίοδος [ΣΗΘΥΑ σ.19]
    rh_setpoint: float = 0.65        # σχετική υγρασία [ΒΑΘΜΟΝΟΜΗΣΗ· ΑΥΤΟΨΙΑ]
    air_speed_ms: float = 0.10       # ταχύτητα αέρα πάνω από το νερό (<0.15 m/s)
    heat_recovery_eff: float = 0.60  # βαθμός απόδοσης εναλλάκτη ΚΚΜ [ΑΥΤΟΨΙΑ]
    envelope_ua_w_k: float = 14000   # συνολικό UA κελύφους (W/K) [ΒΑΘΜΟΝΟΜΗΣΗ]


@dataclass
class DomesticHotWater:
    """Ζεστό νερό χρήσης — ντους λουτρών.

    Στόχος βαθμονόμησης: οι θερινοί μήνες (Ιουν–Σεπ, όπου το ΦΑ είναι
    αποκλειστικά ΖΝΧ) καταναλώνουν ~90–100 MWh πρωτογενή/μήνα, δηλ.
    ~3.000 kWh/ημέρα [Πίν.1 ΣΗΘΥΑ]. Ο όγκος πιθανόν συμπεριλαμβάνει και
    απώλειες αναμονής/διανομής των λεβήτων — επιμερισμός με [ΑΥΤΟΨΙΑ].
    """
    users_per_day: float = 2600     # [ΒΑΘΜΟΝΟΜΗΣΗ έναντι Ιουν–Σεπ· ΑΥΤΟΨΙΑ]
    litres_per_user: float = 40.0
    supply_temp_c: float = 43.0


@dataclass
class HeatPump:
    """Αερόψυκτη αντλία θερμότητας αέρα-νερού."""
    carnot_eff: float = 0.45        # λόγος πραγματικού/Carnot COP (τυπικά 0.40–0.50)
    max_cop: float = 6.0
    supply_temp_pool_c: float = 45.0   # χαμηλή θερμοκρασία προσαγωγής → υψηλό COP
    supply_temp_dhw_c: float = 55.0
    capacity_kw_th: float = 1600.0     # διαστασιολόγηση ~ αιχμή φορτίου (βλ. καμπύλη
                                       # διάρκειας [ΣΗΘΥΑ Διάγρ.9]: αιχμή ~1.100 kW)
    backup_gas_eff: float = 0.90       # εφεδρικοί λέβητες Buderus [ΣΗΘΥΑ σ.41]


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
    # Τιμές ενέργειας (προ ΦΠΑ) — τεκμηρίωση στο docs/05-πραγματικά-δεδομένα.md
    gas_price_eur_kwh: float = 0.064       # από ειδικό κόστος λέβητα 71,2 €/MWh_th
                                           # × β.α. 0,90 [ΣΗΘΥΑ Διάγρ.10]
    grid_price_eur_kwh: float = 0.156      # συνεπαγόμενη από κόστος φωτισμού
                                           # 53.670 €/343 MWh [ΕΞΕ §2.3]
    injection_price_eur_kwh: float = 0.065 # πίστωση Net Billing (χονδρεμπορική)
    boiler_eff: float = 0.90               # μέσος β.α. λεβήτων Buderus [ΣΗΘΥΑ σ.41]
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
    # Συντελεστές εκπομπών (kg CO2 / kWh) — μεθοδολογία ΙΕΑ κατά τις
    # σημειώσεις επιβλέποντα «Κεφ. 5: Αποτύπωμα άνθρακα» (μίγμα 2020: 0,406)
    ef_gas_fuel: float = 0.202             # καύσιμο ΦΑ (ΚΕΝΑΚ/IPCC)
    ef_grid_2026: float = 0.35             # ελληνικό μίγμα 2026 (ΔΑΠΕΕΠ)
    ef_grid_2040: float = 0.12             # προβολή ΕΣΕΚ για το 2040


@dataclass
class Site:
    latitude: float = 40.579     # Ποσειδώνιο, Μ. Κάλλας & 25ης Μαρτίου
    longitude: float = 22.950
    # Πραγματική γεωμετρία δεξαμενών [ΣΗΘΥΑ σ.5]· βάθη [ΑΥΤΟΨΙΑ].
    # Συντελεστής δραστηριότητας 0,5: αγωνιστική/προπονητική χρήση με
    # διαδρομές — όχι δημόσια αναψυχή (ASHRAE) [ΒΑΘΜΟΝΟΜΗΣΗ].
    # Η εξωτερική 50 m διαθέτει εναλλάκτες, αλλά η βαθμονόμηση με τον PTZ
    # μετρητή αποκλείει θέρμανσή της από λέβητες τον χειμώνα (θα υπερέβαινε
    # μόνη της όλη την καταγεγραμμένη κατανάλωση) → αθέρμαντη στη βάση·
    # επιβεβαίωση λειτουργίας [ΑΥΤΟΨΙΑ].
    pools: list = field(default_factory=lambda: [
        Pool("Εσωτερική 50 m (Α)", 50.0, 21.0, 2.0, 24.0, 0.5),
        Pool("Εσωτερική 50 m (Β)", 50.0, 21.0, 2.0, 24.0, 0.5),
        Pool("Πισίνα εκμάθησης 10×12", 10.0, 12.0, 0.9, 31.0, 0.5),
        Pool("Εξωτερική 50 m", 50.0, 21.0, 2.0, 24.0, 0.5,
             indoor=False, air_speed_ms=1.0,    # U = Uap·Z, Z=0,25 [ΣΗΘΥΑ σ.18]
             heated_months=()),
    ])
    # Θερινή διακοπή: Ιουν–Σεπ ΔΕΝ λειτουργεί θέρμανση χώρων/πισινών — μόνο ΖΝΧ.
    # Ο Μάιος περιλαμβάνει μόνο θέρμανση πισινών (όχι χώρων). [ΣΗΘΥΑ σ.9, σ.17]
    heating_months: tuple = (1, 2, 3, 4, 5, 10, 11, 12)
    # Θέρμανση χώρων έως Μάρτιο: η χαμηλή πραγματική κατανάλωση Απριλίου
    # (262 MWh) δεν χωράει φορτίο κελύφους/αερισμού [ΒΑΘΜΟΝΟΜΗΣΗ].
    space_heating_months: tuple = (1, 2, 3, 10, 11, 12)
    hall: Hall = field(default_factory=Hall)
    dhw: DomesticHotWater = field(default_factory=DomesticHotWater)
    heat_pump: HeatPump = field(default_factory=HeatPump)
    pv: PVSystem = field(default_factory=PVSystem)
    econ: Economics = field(default_factory=Economics)
