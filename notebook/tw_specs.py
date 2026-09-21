"""Time-window table specs for notebook 09 (see cri_utils.build_table).

T0 is default_time_windows.csv with exclusive ends. T1 and T2 are candidates.
Windows are (day_group, start, end, vi); ends are exclusive.
"""

T0 = {
    "attraction": [("weekday", "09:00", "17:00", 0.5), ("weekend", "09:00", "17:00", 0.7)],
    "bus_station": [
        ("weekday", "07:00", "09:00", 0.5),
        ("weekday", "12:00", "14:00", 0.2),
        ("weekday", "17:00", "19:00", 0.5),
    ],
    "hospital": [
        ("weekday", "07:00", "10:00", 0.8),
        ("weekday", "10:00", "16:00", 0.4),
        ("weekday", "16:00", "19:00", 0.8),
        ("weekend", "00:00", "24:00", 0.2),
    ],
    "industrial": [
        ("weekday", "07:00", "09:00", 0.6),
        ("weekday", "12:00", "13:00", 0.2),
        ("weekday", "17:00", "19:00", 0.6),
    ],
    "mall": [
        ("weekday", "12:00", "14:00", 0.6),
        ("weekday", "17:00", "20:00", 0.7),
        ("weekend", "09:00", "20:00", 0.2),
    ],
    "school": [("weekday", "08:00", "10:00", 0.4), ("weekday", "16:00", "18:00", 0.4)],
    "station": [
        ("weekday", "07:00", "09:00", 0.7),
        ("weekday", "12:00", "14:00", 0.3),
        ("weekday", "17:00", "19:00", 0.7),
        ("weekend", "09:00", "20:00", 0.3),
    ],
    "university": [
        ("weekday", "07:00", "09:00", 0.8),
        ("weekday", "12:00", "13:00", 0.6),
        ("weekday", "17:00", "19:00", 0.8),
    ],
}

# T1: coherence gap-fills that reuse vi values already present in T0.
# - hospital: continuous occupancy; weekday nights get the weekend base (0.2).
# - station / bus_station: off-peak service between peaks and in the evening,
#   at their existing off-peak values (0.3 / 0.2).
# - industrial / university: occupied between peaks, at their lowest existing
#   daytime value (0.2 / 0.6), so the peaks remain the maxima.
# - school: occupied during class, at the gate value (0.4).
# - attraction, mall: unchanged.
T1 = {
    "attraction": T0["attraction"],
    "bus_station": [
        ("weekday", "07:00", "09:00", 0.5),
        ("weekday", "09:00", "17:00", 0.2),
        ("weekday", "17:00", "19:00", 0.5),
        ("weekday", "19:00", "22:00", 0.2),
    ],
    "hospital": [
        ("weekday", "00:00", "07:00", 0.2),
        ("weekday", "07:00", "10:00", 0.8),
        ("weekday", "10:00", "16:00", 0.4),
        ("weekday", "16:00", "19:00", 0.8),
        ("weekday", "19:00", "24:00", 0.2),
        ("weekend", "00:00", "24:00", 0.2),
    ],
    "industrial": [
        ("weekday", "07:00", "09:00", 0.6),
        ("weekday", "09:00", "17:00", 0.2),
        ("weekday", "17:00", "19:00", 0.6),
    ],
    "mall": T0["mall"],
    "school": [("weekday", "08:00", "17:00", 0.4)],
    "station": [
        ("weekday", "07:00", "09:00", 0.7),
        ("weekday", "09:00", "17:00", 0.3),
        ("weekday", "17:00", "19:00", 0.7),
        ("weekday", "19:00", "24:00", 0.3),
        ("weekend", "09:00", "24:00", 0.3),
    ],
    "university": [
        ("weekday", "07:00", "09:00", 0.8),
        ("weekday", "09:00", "17:00", 0.6),
        ("weekday", "17:00", "19:00", 0.8),
    ],
}

# T2: T1 plus changes that need a domain judgement (new vi values).
# - mall: open 10-23 every day; weekend daytime is the busiest period (0.7),
#   weekday off-peak 0.2, evening 0.4 (T0 had weekend at 0.2 < weekday 0.6).
# - attraction: evening tail 17-20 at 0.3.
# - school: gates (08-09, 16-17) keep 0.4 as crowd peaks; class hours 0.6,
#   because children are present and less able to self-evacuate.
T2 = dict(
    T1,
    mall=[
        ("weekday", "10:00", "12:00", 0.2),
        ("weekday", "12:00", "14:00", 0.6),
        ("weekday", "14:00", "17:00", 0.2),
        ("weekday", "17:00", "20:00", 0.7),
        ("weekday", "20:00", "23:00", 0.4),
        ("weekend", "10:00", "20:00", 0.7),
        ("weekend", "20:00", "23:00", 0.4),
    ],
    attraction=[
        ("weekday", "09:00", "17:00", 0.5),
        ("weekday", "17:00", "20:00", 0.3),
        ("weekend", "09:00", "17:00", 0.7),
        ("weekend", "17:00", "20:00", 0.3),
    ],
    school=[
        ("weekday", "08:00", "09:00", 0.4),
        ("weekday", "09:00", "16:00", 0.6),
        ("weekday", "16:00", "17:00", 0.4),
    ],
)

# Variants with schools active only at the gates, as in T0 (crowds on the
# street rather than occupancy), to isolate the effect of all-day schools.
T1g = dict(T1, school=T0["school"])
T2g = dict(T2, school=T0["school"])

SPECS = {"T0": T0, "T1": T1, "T1g": T1g, "T2": T2, "T2g": T2g}
