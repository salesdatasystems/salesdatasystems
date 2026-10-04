"""Build index.html from data/*.csv and page_template.html."""
import pandas as pd, json, math
cal = pd.read_csv("data/calendar_year_series.csv", index_col="year")
debt = pd.read_csv("data/debt_fiscal_year.csv")
mw = pd.read_csv("data/minwage_1983_2013_statcan.csv", index_col="year")
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
add("debt_tp_pct", "Government debt", "Taxpayer-supported debt as a share of GDP", "Debt the province repays from taxes and other government revenue, as a percentage of BC's nominal GDP. Fiscal years ending March 31.", "p1", "abs", ser(d.taxpayer_pct_gdp, 1, 1), None, basis="fiscal", short="Taxpayer-supported debt, % of GDP", note="1969/70 to 2011/12: BC Ministry of Finance Table A2.15. 2012/13 onward: BC Budget and Fiscal Plans. Definitions and GDP revisions differ slightly between publications. 2025/26 is an updated forecast.")
add("debt_tot_pct", "Government debt", "Total provincial debt as a share of GDP", "Taxpayer-supported debt plus self-supported debt (commercial Crown corporations such as BC Hydro), as a percentage of BC's nominal GDP.", "p1", "abs", ser(d.total_pct_gdp, 1, 1), None, basis="fiscal", short="Total provincial debt, % of GDP", note="Same sources and breaks as taxpayer-supported debt. 2025/26 is an updated forecast.")
add("debt_tp_m", "Government debt", "Taxpayer-supported debt in dollars", "Taxpayer-supported debt in current dollars, billions. Not adjusted for inflation or population.", "m", "pct", ser(d.taxpayer_debt_m, 1, 0), None, basis="fiscal", short="Taxpayer-supported debt ($)", note="Same sources and breaks as the percentage series. 2025/26 is an updated forecast.")
add("mw_real", "Minimum wage", "Minimum wage, constant 2013 dollars", "General hourly minimum wage, weighted by employees, restated in 2013 dollars. Covers 1983 to 2013.", "d2", "pct", ser(mw.minwage_real2013_bc, 1, 2), ser(mw.minwage_real2013_ca, 1, 2), zero=False, short="Minimum wage (2013 $)", note="Source: Statistics Canada, Perspectives on Labour and Income 75-006-X, article 14035, Table A.1. Years after 2013 and nominal rates are not loaded yet.")
add("mw_earn", "Minimum wage", "Average hourly earnings, constant 2013 dollars", "Average hourly earnings from the Survey of Employment, Payrolls and Hours, in 2013 dollars. Covers 1983 to 2013.", "d2", "pct", ser(mw.avg_earnings_real2013_bc, 1, 2), ser(mw.avg_earnings_real2013_ca, 1, 2), zero=False, short="Avg hourly earnings (2013 $)", note="Source: Statistics Canada 75-006-X, article 14035, Table A.1.")
add("mw_ratio", "Minimum wage", "Minimum wage as a share of average hourly earnings", "The minimum wage divided by average hourly earnings. A higher figure means the minimum wage is closer to the average wage.", "p1", "abs", ser(mw.minwage_to_avg_earnings_pct_bc, 1, 1), ser(mw.minwage_to_avg_earnings_pct_ca, 1, 1), short="Minimum wage, % of avg earnings", note="Source: Statistics Canada 75-006-X, article 14035, Table A.1.")

sources = [
 "Statistics Canada, Table 14-10-0327-01, Labour force characteristics by province, annual (employment, unemployment, participation).",
 "Statistics Canada, Table 36-10-0222-01, Gross domestic product, expenditure-based, provincial and territorial, annual.",
 "Statistics Canada, Table 17-10-0005-01, Population estimates on July 1, by age and gender.",
 "Statistics Canada, Table 18-10-0005-01, Consumer Price Index, annual average, not seasonally adjusted.",
 "Statistics Canada, Table 14-10-0340-01, Employee wages by occupation, annual.",
 "BC Ministry of Finance, Historical Provincial Debt Summary 1969/70 to 2011/12, Table A2.15 (BC Data Catalogue).",
 "BC Budget and Fiscal Plan 2019/20 to 2021/22 and 2026/27 to 2028/29, Tables A17 and A19 (bcbudget.gov.bc.ca).",
 "Statistics Canada, Perspectives on Labour and Income 75-006-X, 2014, article 14035, Table A.1 (minimum wage and average hourly earnings, constant 2013 dollars).",
 "Premiers and dates of office: List of premiers of British Columbia (Wikipedia), cross-checkable against Elections BC.",
]
D = dict(asof="October 2026", metrics=M, governments=gov.to_dict("records"), sources=sources)
html = open("page_template.html", encoding="utf-8").read().replace("/*DATA*/", json.dumps(D, separators=(",", ":")))
open("index.html", "w", encoding="utf-8").write(html)
print(len(html) // 1024, "KB;", len(M), "metrics")
for k, m in M.items(): print(k, min(m["bc"]) if m["bc"] else None, max(m["bc"]) if m["bc"] else None)
