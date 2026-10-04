"""Build index.html from data/*.csv and page_template.html."""
import pandas as pd, json, math
cal = pd.read_csv("data/calendar_year_series.csv", index_col="year")
debt = pd.read_csv("data/debt_fiscal_year.csv")
mw = pd.read_csv("data/minwage_1983_2013_statcan.csv", index_col="year")
mwn = pd.read_csv("data/minwage_bc_nominal.csv")
mwn["dt"] = pd.to_datetime(mwn.effective_date)
def rate_on(y):  # BC general minimum wage in force on July 1 of year y
    r = mwn[mwn.dt <= pd.Timestamp(y, 7, 1)]
    return float(r.wage.iloc[-1]) if len(r) else None
mw_nom = {y: rate_on(y) for y in range(1965, 2027) if rate_on(y) is not None}
gov = pd.read_csv("data/governments.csv").fillna("")

def ser(s, scale=1.0, nd=3):
    return {int(y): round(float(v) * scale, nd) for y, v in s.items() if not (isinstance(v, float) and math.isnan(v))}
c = cal
# derived
for g in ("bc", "ca"):
    c[f"gdp_pc_{g}"] = c[f"gdp_real_m_{g}"] * 1e6 / c[f"pop_{g}"]
    c[f"infl_{g}"] = (c[f"cpi_{g}"] / c[f"cpi_{g}"].shift(1) - 1) * 100
    base = c.loc[2022, f"cpi_{g}"]
    for w in ("avg", "med"):
        c[f"wage_{w}_real_{g}"] = c[f"wage_{w}_{g}"] * base / c[f"cpi_{g}"]

M = {}
def add(key, group, label, desc, fmt, delta, bc, ca=None, basis="calendar", indexable=False, stat="change", zero=True, note="", short=None):
    M[key] = dict(group=group, label=label, short=short or label, desc=desc, fmt=fmt, delta=delta, basis=basis, indexable=indexable, stat=stat, zero=zero, note=note, bc=bc, ca=ca)

add("gdp_real", "Economy", "Real GDP (inflation-adjusted)", "Total value of goods and services produced in the province each year, in chained 2017 dollars, billions.", "b1", "pct",
    ser(c.gdp_real_m_bc, 1/1000), ser(c.gdp_real_m_ca, 1/1000), indexable=True, short="Real GDP", note="Source: Statistics Canada 36-10-0222-01, 1981 to 2024.")
add("gdp_pc", "Economy", "Real GDP per person", "Real GDP divided by the July 1 population estimate, in chained 2017 dollars.", "d0", "pct",
    ser(c.gdp_pc_bc, 1, 0), ser(c.gdp_pc_ca, 1, 0), zero=False, short="Real GDP per person", note="GDP from 36-10-0222-01, population from 17-10-0005-01.")
add("pop", "Economy", "Population", "Estimated population on July 1.", "pop", "pct", ser(c.pop_bc, 1, 0), ser(c.pop_ca, 1, 0), indexable=True, note="Source: Statistics Canada 17-10-0005-01.")
add("employment", "Jobs", "Employment", "Average number of employed people aged 15 and over, thousands.", "k0", "pct", ser(c.employment_k_bc, 1, 1), ser(c.employment_k_ca, 1, 1), indexable=True, note="Source: Labour Force Survey, Statistics Canada 14-10-0327-01.")
add("unemp", "Jobs", "Unemployment rate", "Unemployed people as a share of the labour force, annual average, ages 15 and over.", "p1", "abs", ser(c.unemp_rate_bc, 1, 1), ser(c.unemp_rate_ca, 1, 1), stat="avg", short="Unemployment rate", note="Source: Labour Force Survey, Statistics Canada 14-10-0327-01.")
add("emp_rate", "Jobs", "Employment rate", "Employed people as a share of the population aged 15 and over.", "p1", "abs", ser(c.emp_rate_bc, 1, 1), ser(c.emp_rate_ca, 1, 1), zero=False, note="Source: Labour Force Survey, Statistics Canada 14-10-0327-01.")
add("participation", "Jobs", "Labour force participation rate", "Share of the population aged 15 and over that is working or looking for work.", "p1", "abs", ser(c.participation_bc, 1, 1), ser(c.participation_ca, 1, 1), zero=False, note="Source: Labour Force Survey, Statistics Canada 14-10-0327-01.")
add("infl", "Prices and wages", "Inflation (change in consumer prices)", "Year-over-year change in the all-items Consumer Price Index.", "p1", "abs", ser(c.infl_bc, 1, 2), ser(c.infl_ca.loc[1972:], 1, 2), stat="avg", zero=False, short="Inflation (CPI)", note="Source: Statistics Canada 18-10-0005-01. BC series starts in 1980 because the BC CPI starts in 1979.")
add("wage_avg", "Prices and wages", "Average hourly wage, current dollars", "Average hourly wage rate of all employees, as paid in each year, not adjusted for inflation.", "d2", "pct", ser(c.wage_avg_bc, 1, 2), ser(c.wage_avg_ca, 1, 2), zero=False, short="Avg hourly wage (nominal)", note="Source: Labour Force Survey, Statistics Canada 14-10-0340-01, 1997 to 2022.")
add("wage_avg_real", "Prices and wages", "Average hourly wage, inflation-adjusted", "The same average hourly wage restated in 2022 dollars using each region's Consumer Price Index.", "d2", "pct", ser(c.wage_avg_real_bc, 1, 2), ser(c.wage_avg_real_ca, 1, 2), zero=False, short="Avg hourly wage (2022 $)", note="Wages from 14-10-0340-01, adjusted with CPI from 18-10-0005-01.")
add("wage_med_real", "Prices and wages", "Median hourly wage, inflation-adjusted", "The wage of the middle worker, restated in 2022 dollars using each region's Consumer Price Index.", "d2", "pct", ser(c.wage_med_real_bc, 1, 2), ser(c.wage_med_real_ca, 1, 2), zero=False, short="Median hourly wage (2022 $)", note="Wages from 14-10-0340-01, adjusted with CPI from 18-10-0005-01.")
d = debt.set_index("start_year")
d["capital_other_m"] = d.taxpayer_debt_m - d.operating_debt_m
cpi_full = pd.read_csv("data/cpi_canada_annual.csv").set_index("year").cpi_canada_2002_100
BASE = 2025
def fy_cpi(y):  # fiscal year runs April y to March y+1: nine months in year y, three in y+1
    return 0.75 * cpi_full[y] + 0.25 * cpi_full[y + 1] if (y + 1) in cpi_full.index else cpi_full[y]
adj = pd.Series({y: cpi_full[BASE] / fy_cpi(y) for y in d.index})
popbc = pd.read_csv("data/calendar_year_series.csv", index_col="year").pop_bc
d["tp_real_m"] = d.taxpayer_debt_m * adj
d["op_real_m"] = d.operating_debt_m * adj
d["cap_real_m"] = d.capital_other_m * adj
d["tp_real_pc"] = d.tp_real_m * 1e6 / popbc.reindex(d.index)
add("debt_tp_pct", "Government debt", "Taxpayer-supported debt as a share of GDP", "Debt the province repays from taxes and other government revenue, as a percentage of BC's nominal GDP. Fiscal years ending March 31.", "p1", "abs", ser(d.taxpayer_pct_gdp, 1, 1), None, basis="fiscal", short="Taxpayer-supported debt, % of GDP", note="1969/70 to 2011/12: BC Ministry of Finance Table A2.15. 2012/13 onward: BC Budget and Fiscal Plans. Definitions and GDP revisions differ slightly between publications. 2025/26 is an updated forecast.")
add("debt_tot_pct", "Government debt", "Total provincial debt as a share of GDP", "Taxpayer-supported debt plus self-supported debt (commercial Crown corporations such as BC Hydro), as a percentage of BC's nominal GDP.", "p1", "abs", ser(d.total_pct_gdp, 1, 1), None, basis="fiscal", short="Total provincial debt, % of GDP", note="Same sources and breaks as taxpayer-supported debt. 2025/26 is an updated forecast.")
add("debt_tp_m", "Government debt", "Taxpayer-supported debt in dollars", "Taxpayer-supported debt in current dollars, billions. Not adjusted for inflation or population.", "m", "pct", ser(d.taxpayer_debt_m, 1, 0), None, basis="fiscal", short="Taxpayer-supported debt ($)", note="Same sources and breaks as the percentage series. 2025/26 is an updated forecast.")
add("debt_op_m", "Government debt", "Operating debt (borrowing for day-to-day spending)", "Provincial government direct operating debt: money borrowed to cover deficits in everyday spending, as distinct from debt that finances buildings and infrastructure. Current dollars, billions.", "m", "abs", ser(d.operating_debt_m, 1, 0), None, basis="fiscal", short="Operating debt ($)", note="1969/70 to 2011/12: BC Ministry of Finance Table A2.15. 2012/13 onward: BC Budget and Fiscal Plans, Table A17. Definitions differ slightly between publications. 2025/26 is an updated forecast.")
add("debt_cap_m", "Government debt", "Capital and other taxpayer-supported debt in dollars", "Taxpayer-supported debt other than operating debt: borrowing for schools, hospitals, roads, transit, housing and similar assets. Total taxpayer-supported debt minus operating debt, in current dollars, billions.", "m", "abs", ser(d.capital_other_m, 1, 0), None, basis="fiscal", short="Capital and other debt ($)", note="Calculated as taxpayer-supported debt minus operating debt. Same sources and breaks as the other debt series. 2025/26 is an updated forecast.")
add("debt_tp_real", "Government debt", "Taxpayer-supported debt, inflation-adjusted", "Taxpayer-supported debt restated in 2025 dollars using the Consumer Price Index (Canada), billions. Removes the effect of rising prices so different decades can be compared.", "m", "pct", ser(d.tp_real_m, 1, 0), None, basis="fiscal", short="Taxpayer-supported debt (2025 $)", note="Each fiscal year is converted with a CPI weighted 9 months to the starting calendar year and 3 months to the next. One index (Canada, Statistics Canada 18-10-0005-01) is used for the whole 1969 to 2025 series. 2025/26 is an updated forecast.")
add("debt_pc_real", "Government debt", "Taxpayer-supported debt per person, inflation-adjusted", "Taxpayer-supported debt divided by BC's July 1 population, in 2025 dollars. Adjusts for both inflation and population growth.", "d0", "pct", ser(d.tp_real_pc.dropna(), 1, 0), None, basis="fiscal", zero=True, short="Debt per person (2025 $)", note="Debt from BC budget documents, population from Statistics Canada 17-10-0005-01 (from 1971), CPI from 18-10-0005-01. 2025/26 is an updated forecast.")
add("debt_op_real", "Government debt", "Operating debt, inflation-adjusted", "Operating debt restated in 2025 dollars, billions.", "m", "abs", ser(d.op_real_m, 1, 0), None, basis="fiscal", short="Operating debt (2025 $)", note="Same conversion as taxpayer-supported debt in 2025 dollars. 2025/26 is an updated forecast.")
add("debt_cap_real", "Government debt", "Capital and other debt, inflation-adjusted", "Taxpayer-supported debt other than operating debt, restated in 2025 dollars, billions.", "m", "abs", ser(d.cap_real_m, 1, 0), None, basis="fiscal", short="Capital and other debt (2025 $)", note="Same conversion as taxpayer-supported debt in 2025 dollars. 2025/26 is an updated forecast.")
add("debt_int", "Government debt", "Interest cost per dollar of revenue", "Cents of every provincial revenue dollar spent on interest on taxpayer-supported debt (the interest bite).", "c1", "abs", ser(d.interest_bite_cents.dropna(), 1, 1), None, basis="fiscal", short="Interest bite (cents per revenue $)", note="Source: BC Budget and Fiscal Plan 2019/20 to 2021/22 and 2026/27 to 2028/29, Table A19. Earlier years are not loaded. 2025/26 is an updated forecast.")
_cpi = pd.read_csv("data/cpi_canada_annual.csv").set_index("year").cpi_canada_2002_100
mw_nom_real = {y: round(v * _cpi[2025] / _cpi[y], 2) for y, v in mw_nom.items() if y in _cpi.index}
_wavg = c.wage_avg_bc.dropna()
mw_ratio_avg = {int(y): round(mw_nom[int(y)] / v * 100, 1) for y, v in _wavg.items() if int(y) in mw_nom}
add("mw_nom", "Minimum wage", "BC minimum wage, as set (current dollars)", "The general hourly minimum wage in force on July 1 of each year, 1965 to 2026, not adjusted for inflation.", "d2", "pct", {int(k): v for k, v in mw_nom.items()}, None, short="Minimum wage (current $)", note="Source: Employment and Social Development Canada, Historical Minimum Wage Rates in Canada (open.canada.ca). The source dates the $17.85 rate 2026-06-01, a duplicate of the $18.25 row; it is treated here as June 1, 2025. Rates that changed on other dates in a year appear in the year they were in force on July 1.")
add("mw_nom_real", "Minimum wage", "BC minimum wage, inflation-adjusted", "The same minimum wage restated in 2025 dollars using the Consumer Price Index (Canada), so a 1970s rate and a 2020s rate buy the same basket of goods.", "d2", "pct", mw_nom_real, None, short="Minimum wage (2025 $)", note="Rate from ESDC historical minimum wage table; CPI from Statistics Canada 18-10-0005-01 (Canada all-items). One index is used for the whole series.")
add("mw_ratio_avg", "Minimum wage", "BC minimum wage as a share of the average hourly wage", "The July 1 minimum wage divided by the average hourly wage of all BC employees, 1997 to 2022. A higher figure means the minimum wage is closer to the average wage.", "p1", "abs", mw_ratio_avg, None, short="Minimum wage, % of avg wage (1997-2022)", zero=False, note="Minimum wage from ESDC; average hourly wage from Statistics Canada 14-10-0340-01. Different survey and method from the 1983 to 2013 series below, so the two ratios are not directly comparable.")
add("mw_real", "Minimum wage", "Minimum wage, constant 2013 dollars", "General hourly minimum wage, weighted by employees, restated in 2013 dollars. Covers 1983 to 2013.", "d2", "pct", ser(mw.minwage_real2013_bc, 1, 2), ser(mw.minwage_real2013_ca, 1, 2), zero=False, short="Minimum wage (2013 $)", note="Source: Statistics Canada, Perspectives on Labour and Income 75-006-X, article 14035, Table A.1. It ends in 2013; the series above cover the years since.")
add("mw_earn", "Minimum wage", "Average hourly earnings, constant 2013 dollars", "Average hourly earnings from the Survey of Employment, Payrolls and Hours, in 2013 dollars. Covers 1983 to 2013.", "d2", "pct", ser(mw.avg_earnings_real2013_bc, 1, 2), ser(mw.avg_earnings_real2013_ca, 1, 2), zero=False, short="Avg hourly earnings (2013 $)", note="Source: Statistics Canada 75-006-X, article 14035, Table A.1.")
add("mw_ratio", "Minimum wage", "Minimum wage as a share of average hourly earnings", "The minimum wage divided by average hourly earnings. A higher figure means the minimum wage is closer to the average wage.", "p1", "abs", ser(mw.minwage_to_avg_earnings_pct_bc, 1, 1), ser(mw.minwage_to_avg_earnings_pct_ca, 1, 1), short="Minimum wage, % of avg earnings", note="Source: Statistics Canada 75-006-X, article 14035, Table A.1.")

sources = [
 "Statistics Canada, Table 14-10-0327-01, Labour force characteristics by province, annual (employment, unemployment, participation).",
 "Statistics Canada, Table 36-10-0222-01, Gross domestic product, expenditure-based, provincial and territorial, annual.",
 "Statistics Canada, Table 17-10-0005-01, Population estimates on July 1, by age and gender.",
 "Statistics Canada, Table 18-10-0005-01, Consumer Price Index, annual average, not seasonally adjusted (used for every inflation adjustment on this page).",
 "Statistics Canada, Table 14-10-0340-01, Employee wages by occupation, annual.",
 "BC Ministry of Finance, Historical Provincial Debt Summary 1969/70 to 2011/12, Table A2.15 (BC Data Catalogue).",
 "BC Budget and Fiscal Plan 2019/20 to 2021/22 and 2026/27 to 2028/29, Tables A17 and A19 (bcbudget.gov.bc.ca).",
 "Employment and Social Development Canada, Historical Minimum Wage Rates in Canada (open.canada.ca), BC general hourly rates since 1965.",
 "Statistics Canada, Perspectives on Labour and Income 75-006-X, 2014, article 14035, Table A.1 (minimum wage and average hourly earnings, constant 2013 dollars).",
 "Premiers and dates of office: List of premiers of British Columbia (Wikipedia), cross-checkable against Elections BC.",
]
D = dict(asof="October 2026", metrics=M, governments=gov.to_dict("records"), sources=sources)
html = open("page_template.html", encoding="utf-8").read().replace("/*DATA*/", json.dumps(D, separators=(",", ":")))
open("index.html", "w", encoding="utf-8").write(html)
print(len(html) // 1024, "KB;", len(M), "metrics")
for k, m in M.items(): print(k, min(m["bc"]) if m["bc"] else None, max(m["bc"]) if m["bc"] else None)
