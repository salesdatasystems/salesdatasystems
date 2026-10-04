"""Assemble BC-vs-Canada indicator series from raw StatCan / BC Budget downloads.
Run from this folder after placing raw files in RAW (see sources.md)."""
import pandas as pd, sys, os
RAW = sys.argv[1] if len(sys.argv) > 1 else "raw"
def rd(t): return pd.read_csv(f"{RAW}/{t}/{t}.csv", encoding="utf-8-sig", low_memory=False)
GEOS = ["British Columbia", "Canada"]
tag = {"British Columbia": "bc", "Canada": "ca"}
out = {}
def put(name, geo, s):
    for y, v in s.items(): out.setdefault(int(y), {})[f"{name}_{tag[geo]}"] = v

# --- Labour force (14-10-0327-01), annual, both sexes, 15+
l = rd("14100327"); l = l[(l.GEO.isin(GEOS)) & (l.Gender == "Total - Gender") & (l["Age group"] == "15 years and over")]
for lab, nm in [("Employment", "employment_k"), ("Unemployment rate", "unemp_rate"), ("Participation rate", "participation"),
                ("Employment rate", "emp_rate"), ("Labour force", "labour_force_k"), ("Unemployment", "unemployed_k")]:
    for g in GEOS:
        s = l[(l["Labour force characteristics"] == lab) & (l.GEO == g)].set_index("REF_DATE").VALUE; put(nm, g, s)

# --- GDP (36-10-0222-01), expenditure-based
g = rd("36100222"); g = g[(g.GEO.isin(GEOS)) & (g.Estimates == "Gross domestic product at market prices")]
for pr, nm in [("Chained (2017) dollars", "gdp_real_m"), ("Current prices", "gdp_nom_m")]:
    for geo in GEOS:
        put(nm, geo, g[(g.Prices == pr) & (g.GEO == geo)].set_index("REF_DATE").VALUE)

# --- Population July 1 (17-10-0005-01)
p = rd("17100005"); p = p[(p.GEO.isin(GEOS)) & (p["Age group"] == "All ages") & (p.Gender == "Total - gender")]
for geo in GEOS: put("pop", geo, p[p.GEO == geo].set_index("REF_DATE").VALUE)

# --- CPI all-items (18-10-0005-01), 2002=100
c = rd("18100005"); c = c[(c.GEO.isin(GEOS)) & (c["Products and product groups"] == "All-items") & (c.UOM == "2002=100")]
for geo in GEOS: put("cpi", geo, c[c.GEO == geo].set_index("REF_DATE").VALUE)

# --- Hourly wages (14-10-0340-01)
w = rd("14100340"); w = w[(w.GEO.isin(GEOS)) & (w["Type of work"] == "Both full- and part-time employees") &
    (w["National Occupational Classification (NOC)"] == "Total employees, all occupations") & (w.Sex == "Both sexes") & (w["Age group"] == "15 years and over")]
for lab, nm in [("Average hourly wage rate", "wage_avg"), ("Median hourly wage rate", "wage_med")]:
    for geo in GEOS: put(nm, geo, w[(w.Wages == lab) & (w.GEO == geo)].set_index("REF_DATE").VALUE)

df = pd.DataFrame.from_dict(out, orient="index").sort_index(); df.index.name = "year"
df = df[df.index >= 1971]
df.to_csv("data/calendar_year_series.csv")
print(df.shape); print(df.notna().sum().to_string()); print(df.loc[[1981, 1991, 2001, 2017, 2024]].T.to_string())
