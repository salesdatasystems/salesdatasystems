import openpyxl, csv, re

rows=[]
ws=openpyxl.load_workbook(f"{RAW}/debt_hist.xlsx",data_only=True).active
for r in ws.iter_rows(values_only=True):
    m=re.match(r"(\d{4})/(\d{2,4})",str(r[1] or ""))
    if m and isinstance(r[10],(int,float)):
        rows.append(dict(fiscal_year=f"{m.group(1)}/{str(int(m.group(1))+1)[-2:]}",start_year=int(m.group(1)),taxpayer_debt_m=r[10],taxpayer_pct_gdp=round(r[15],1),total_debt_m=r[13],total_pct_gdp=round(r[14],1),
          source="BC Ministry of Finance, Historical Provincial Debt Summary 1969/70-2011/12 (Table A2.15)"))
b19=dict(tp=[38182,41068,41880,42719,41499,43607,43957],tpp=[17.2,17.9,17.3,17.2,15.7,15.5,14.9],tot=[55816,60693,62920,65251,65837,64919,67916],totp=[25.2,26.5,26.0,26.2,24.9,23.0,23.0])
for i,y in enumerate(range(2012,2019)):
    rows.append(dict(fiscal_year=f"{y}/{str(y+1)[-2:]}",start_year=y,taxpayer_debt_m=b19["tp"][i],taxpayer_pct_gdp=b19["tpp"][i],total_debt_m=b19["tot"][i],total_pct_gdp=b19["totp"][i],
      source="BC Budget and Fiscal Plan 2019/20-2021/22, Tables A17 & A19" + (" (updated forecast, not final actual)" if y==2018 else "")))
b26=dict(tp=[46229,59750,62341,59888,75402,99089,116540],tpp=[15.0,19.4,17.5,15.0,18.2,23.1,26.1],tot=[72161,87100,90666,89380,107462,133877,154059],totp=[23.4,28.3,25.4,22.3,25.9,31.2,34.5])
for i,y in enumerate(range(2019,2026)):
    rows.append(dict(fiscal_year=f"{y}/{str(y+1)[-2:]}",start_year=y,taxpayer_debt_m=b26["tp"][i],taxpayer_pct_gdp=b26["tpp"][i],total_debt_m=b26["tot"][i],total_pct_gdp=b26["totp"][i],
      source="BC Budget and Fiscal Plan 2026/27-2028/29, Tables A17 & A19" + (" (updated forecast, not final actual)" if y==2025 else "")))
with open("data/debt_fiscal_year.csv","w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
print(len(rows),rows[0]["fiscal_year"],rows[-1]["fiscal_year"])
gov=[("W.A.C. Bennett","Social Credit","1952-08-01","1972-09-15"),("Dave Barrett","NDP","1972-09-15","1975-12-22"),("Bill Bennett","Social Credit","1975-12-22","1986-08-06"),
("Bill Vander Zalm","Social Credit","1986-08-06","1991-04-02"),("Rita Johnston","Social Credit","1991-04-02","1991-11-05"),("Mike Harcourt","NDP","1991-11-05","1996-02-22"),
("Glen Clark","NDP","1996-02-22","1999-08-25"),("Dan Miller","NDP","1999-08-25","2000-02-24"),("Ujjal Dosanjh","NDP","2000-02-24","2001-06-05"),
("Gordon Campbell","BC Liberal","2001-06-05","2011-03-14"),("Christy Clark","BC Liberal","2011-03-14","2017-07-18"),("John Horgan","NDP","2017-07-18","2022-11-18"),("David Eby","NDP","2022-11-18","")]
with open("data/governments.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["premier","party","start","end"]); w.writerows(gov)
