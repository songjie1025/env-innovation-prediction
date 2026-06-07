# =============================================================================
# SDG PROJECT — Statistical evaluation
# =============================================================================
# Prerequisites (one-time installation)
#   pip install pandas numpy scipy openpyxl matplotlib seaborn statsmodels
#
# Instructions:
#   1. INPUT_PATH  → Path to the cleaned Excel file
#   2. SHEET_NAME  → Name of the sheet containing the data
#   3. OUTPUT_EXCEL and OUTPUT_PLOTS → Adjust the desired outputlocation.
#   4. Execute skript using F5
# =============================================================================

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf_backend
import seaborn as sns
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.api import OLS, add_constant
import warnings
warnings.filterwarnings("ignore")

# =============================================================================
# Configuration
# ToDo: Adjust Paths
# Names Columns in Excel File
# creates short lables for plots
# =============================================================================
INPUT_PATH   = "/Users/nicla/Library/Mobile Documents/com~apple~CloudDocs/Studium/Master/2. Semester/Advanced AI Seminar/SDG_Panel_Dataset_clean_final.xlsx"
SHEET_NAME   = "Panel_Data"   
OUTPUT_EXCEL = "/Users/nicla/Library/Mobile Documents/com~apple~CloudDocs/Studium/Master/2. Semester/Advanced AI Seminar/SDG_Statistical_Analysis.xlsx"
OUTPUT_PLOTS = "/Users/nicla/Library/Mobile Documents/com~apple~CloudDocs/Studium/Master/2. Semester/Advanced AI Seminar/SDG_Plots.pdf"


COL_COUNTRY_CODE = "country_code"
COL_COUNTRY_NAME = "country_name"
COL_YEAR         = "year"
TARGET_CM        = "child_mortality (deaths per 1000 birth)"
TARGET_ELEC      = "access_electricity (% of population)"

Predictor_COLS = [
    "gdp_per_capita_ppp (constant 2021 intl. $)",
    "uhc_index (coverage in %)",
    "health_expenditure (% of GDP)",
    "urban_population (% of population)",
    "population",
    "sanitation (% of population)",
    "female_school secondary (% of population)",
    "employment (% of population age 15+)",
    "industrialisation (manufactoring in % of GDP)",
    "clean_fuels (% of population with access)",
    "wgi_composite (0-100)",
    "wgi_voice_accountability (0-100)",
    "wgi_political_stability (0-100)",
    "wgi_gov_effectiveness (0-100)",
    "wgi_regulatory_quality (0-100)",
    "wgi_rule_of_law (0-100)",
    "wgi_control_corruption (0-100)",
]


label_map = {
    TARGET_CM:    "Child Mortality",
    TARGET_ELEC:  "Access Electricity",
    "gdp_per_capita_ppp (constant 2021 intl. $)":      "GDP PPP",
    "uhc_index (coverage in %)":                       "UHC Index",
    "health_expenditure (% of GDP)":                   "Health Exp.",
    "urban_population (% of population)":              "Urbanisation",
    "population":                                      "Population",
    "sanitation (% of population)":                    "Sanitation",
    "female_school secondary (% of population)":       "Female School",
    "employment (% of population age 15+)":            "Employment",
    "industrialisation (manufactoring in % of GDP)":   "Industrialisation",
    "clean_fuels (% of population with access)":       "Clean Fuels",
    "wgi_composite (average between -2,5 and +2,5)":   "WGI Composite",
    "wgi_voice_accountability (0-100)":"WGI Voice",
    "wgi_political_stability (0-100)": "WGI Pol.Stab.",
    "wgi_gov_effectiveness (0-100)":   "WGI Gov.Eff.",
    "wgi_regulatory_quality (0-100)":  "WGI Reg.Qual.",
    "wgi_rule_of_law (0-100)":         "WGI RuleOfLaw",
    "wgi_control_corruption (0-100)":  "WGI Corruption",
}

print("=" * 60)
print("SDG PROJECT — Statistical evaluation")
print("=" * 60)

# =============================================================================
# Step 1 — Load data
# Read Excel file and safe as Data Frame (df)
# Check if Column names are correct, important if number or names of 
# predictors change
# Create a working copy for the skript
# =============================================================================
print("\n[1] Load data...")
df = pd.read_excel(INPUT_PATH, sheet_name=SHEET_NAME)
print(f"     {df[COL_COUNTRY_CODE].nunique()} countries, "
      f"{df[COL_YEAR].nunique()} years, {len(df)} rows")

ALL_NUM_COLS  = [TARGET_CM, TARGET_ELEC] + Predictor_COLS
existing_cols = [c for c in ALL_NUM_COLS if c in df.columns]
missing_cols  = [c for c in ALL_NUM_COLS if c not in df.columns]
if missing_cols:
    print(f"Not found (check column names): {missing_cols}")

pred_existing = [c for c in Predictor_COLS if c in df.columns]
df_clean      = df.copy() 

# =============================================================================
# Step 2 — Overview of missing values ​​in the dataset
# =============================================================================
print("\n[2] Missing values ​​in the dataset...")
missing_overview = pd.DataFrame({
    "variable":        existing_cols,
    "missing_total": [df_clean[c].isna().sum() for c in existing_cols],
    "missing _%":       [round(df_clean[c].isna().mean() * 100, 2)
                        for c in existing_cols],
})
print(missing_overview.to_string(index=False))

# =============================================================================
# step 3 — Descriptive statistics
# Drops all missing values for calculation
# =============================================================================
print("\n[3] Calculate descriptive statistics...")

desc_rows = []
for col in existing_cols:
    s = df_clean[col].dropna()
    if len(s) == 0:
        continue
    desc_rows.append({
        "variable":  col,
        "N":         len(s),
        "Mean":      round(s.mean(), 3),
        "Median":    round(s.median(), 3),
        "Std":       round(s.std(), 3),
        "Min":       round(s.min(), 3),
        "Max":       round(s.max(), 3),
        "Skew":      round(stats.skew(s), 3),
        "Kurtosis":  round(stats.kurtosis(s), 3),
        "Q25":       round(s.quantile(0.25), 3),
        "Q75":       round(s.quantile(0.75), 3),
        "IQR":       round(s.quantile(0.75) - s.quantile(0.25), 3),
    })

df_desc = pd.DataFrame(desc_rows)
print("Descriptive statistics calculated")

# =============================================================================
# Step 4 — Correlation matrices (Spearman)
# Drops empty rows
# calculates correlations matrix based on the spearman method 
# =============================================================================
print("\n[4] Calculate correlation matrices...")

df_corr_data  = df_clean[existing_cols].dropna(how="all") 
corr_spearman = df_corr_data.corr(method="spearman").round(3)

short_labels          = [label_map.get(c, c) for c in existing_cols]
corr_spearman.index   = corr_spearman.columns = short_labels
print("Correlation matrix calculated")

# =============================================================================
# Step 5 — VIF (Variance Inflation Factors - Multicollinearity) 
# Drop rows with empty values
# Convert df to arry (variance_inflation_factor dose not work with df)
# Loop over predictors, enumerate to map colum name to number for output
# try/except to avoid code braking in case of failed calculation e.g. perfect
# multicolinearity -> infinity
# =============================================================================
print("\n[5] Calculate VIF...")

df_vif_data = df_clean[pred_existing].dropna()
vif_rows = []
X_vif = df_vif_data.values 

for i, col in enumerate(pred_existing):
    try: 
        vif_val = variance_inflation_factor(X_vif, i)
        flag    = ("high"   if vif_val > 10 else
                   "medium" if vif_val > 5  else "OK")
        vif_rows.append({"variable": col,
                         "VIF":      round(vif_val, 2),
                         "assessment":flag})
    except Exception:
        vif_rows.append({"Variable": col, "VIF": None, "assessment": "Error"})

df_vif = pd.DataFrame(vif_rows)
print(df_vif.to_string(index=False))

# =============================================================================
# Step 6 — Regressions
# Drops missong values
# loop calculates regression for every target - predictor combination
# calculation only if more than 30 data points exist
# =============================================================================
print("\n[6] Calculate bivariate regressions...")

reg_rows = []
for target in [TARGET_CM, TARGET_ELEC]:
    for pred in pred_existing:
        tmp = df_clean[[target, pred]].dropna()
        if len(tmp) < 30:
            continue
        slope, intercept, r, p, se = stats.linregress(tmp[pred], tmp[target])
        reg_rows.append({
            "Target Variable": target,
            "Predictor":    pred,
            "R²":           round(r**2, 4),
            "Slope":        round(slope, 6),
            "Intercept":    round(intercept, 4),
            "p-value":       round(p, 6),
            "Significant":  "Yes" if p < 0.05 else "No",
            "N":            len(tmp),
        })

multivariate_results = []

for target in [TARGET_CM, TARGET_ELEC]:
    
    tmp = df_clean[[target]+pred_existing].dropna()
    
    x = add_constant(tmp[pred_existing])
    y = tmp[target]
    
    model = OLS(y, x).fit()
    
    for pred in pred_existing:
        multivariate_results.append({
            "Target Variable":  target,
            "Predictor":        pred,
            "Coefficient":      round(model.params[pred], 6),
            "p-Value":          round(model.pvalues[pred], 6),
            "Significant":      "Yes" if p < 0.05 else "No",
            "R²_total":         round(model.rsquared, 4),
            "R²_adj_total":     round(model.rsquared_adj, 4),
            "N":                int(model.nobs),
            })


df_multivar = pd.DataFrame(multivariate_results)
print("Multivariate regressions calculated")


df_reg = pd.DataFrame(reg_rows).sort_values(
    ["Target Variable", "R²"], ascending=[True, False])
print("Regressionen calculated")

# =============================================================================
# Step 7 — Temporal trends
# Calculates the mean for every year and predictor over all countries
# =============================================================================
print("\n[7] Calculate temporal trends...")
df_trends = df_clean.groupby(COL_YEAR)[existing_cols].mean().round(3)
df_trends.index.name = "Year"
print("Temporal trends calculated")

# =============================================================================
# Step 8 — Outliers (IQR-Method)
# Drops all mising values
# Uses Tukey Method to identy outliers
# =============================================================================
print("\n[8] Identify Outliers...")

outlier_rows = []
for col in existing_cols:
    s          = df_clean[col].dropna()
    Q1, Q3     = s.quantile(0.25), s.quantile(0.75)
    IQR        = Q3 - Q1
    lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR
    n_out      = ((df_clean[col] < lower) | (df_clean[col] > upper)).sum()
    outlier_rows.append({
        "variable":         col,
        "Lower_limit":    round(lower, 3),
        "upper_limit":     round(upper, 3),
        "Number_of_outliers": n_out,
        "outliers_%":      round(n_out / len(df_clean) * 100, 2),
    })

df_outliers = pd.DataFrame(outlier_rows)
print("Outliers identified")

# =============================================================================
# Step 9 — Create plots and save them as PDFs
# =============================================================================
print("\n[9] Create plots...")

with pdf_backend.PdfPages(OUTPUT_PLOTS) as pdf:


    # --- Plot 1: Correlation matrix Spearman ---
    mask = np.triu(np.ones_like(corr_spearman, dtype=bool))
    fig, ax = plt.subplots(figsize=(16, 13))
    sns.heatmap(corr_spearman, mask=mask, annot=True, fmt=".2f",
                cmap="RdYlGn", center=0, vmin=-1, vmax=1, ax=ax,
                annot_kws={"size": 7}, linewidths=0.5)
    ax.set_title("Correlation matrix (Spearman)",
                 fontsize=14, fontweight="bold", pad=15)
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # --- Plot 2: Temporal trends of the Target Variables ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, target in zip(axes, [TARGET_CM, TARGET_ELEC]):
        if target in df_trends.columns:
            ax.plot(df_trends.index, df_trends[target],
                    marker="o", linewidth=2, markersize=4, color="#2196F3")
            ax.set_title(label_map.get(target, target), fontweight="bold")
            ax.set_xlabel("Year")
            ax.set_ylabel("Global mean")
            ax.grid(True, alpha=0.3)
    fig.suptitle("Global terend of the Target Variables (2000–2022)",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # --- Plot 3: Boxplots of the Target Variables ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, target in zip(axes, [TARGET_CM, TARGET_ELEC]):
        if target in df_clean.columns:
            df_clean.boxplot(column=target, ax=ax,
                             boxprops=dict(color="#2196F3"),
                             medianprops=dict(color="red", linewidth=2))
            ax.set_title(f"Boxplot: {label_map.get(target, target)}",
                         fontweight="bold")
            ax.set_ylabel("value")
    fig.suptitle("Distribution of the Target Variables",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # --- Plot 4: Histograms of the Predictors ---
    ncols  = 4
    nrows  = (len(pred_existing) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(16, nrows * 3.5))
    axes = axes.flatten()
    for i, col in enumerate(pred_existing):
        s = df_clean[col].dropna()
        axes[i].hist(s, bins=30, color="#4CAF50", edgecolor="white", alpha=0.8)
        axes[i].set_title(label_map.get(col, col),
                          fontsize=9, fontweight="bold")
        axes[i].set_xlabel("value", fontsize=8)
        axes[i].tick_params(labelsize=7)
        sk = round(stats.skew(s), 2)
        axes[i].text(0.97, 0.95, f"Skewness: {sk}",
                     transform=axes[i].transAxes,
                     ha="right", va="top", fontsize=7, color="gray")
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)
    fig.suptitle("Histograms of the Predictors",
                 fontsize=13, fontweight="bold")
    plt.tight_layout()
    pdf.savefig(fig); plt.close()

    # --- Plot 5:  Predictors vs. Child Mortality ---
    for pred in pred_existing:
        tmp = df_clean[[TARGET_CM, pred]].dropna()
        if len(tmp) < 30:
            continue
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(tmp[pred], tmp[TARGET_CM],
                   alpha=0.3, s=15, color="#E91E63")
        m, b   = np.polyfit(tmp[pred], tmp[TARGET_CM], 1)
        x_line = np.linspace(tmp[pred].min(), tmp[pred].max(), 100)
        ax.plot(x_line, m * x_line + b, color="black", linewidth=1.5)
        ax.set_xlabel(label_map.get(pred, pred), fontsize=11)
        ax.set_ylabel("Child Mortality", fontsize=11)
        r2 = (df_reg[(df_reg["Target Variable"] == TARGET_CM) &
                     (df_reg["Predictor"] == pred)]["R²"].values)
        p_val = (df_reg[(df_reg["Target Variable"] == TARGET_CM) &
                        (df_reg["Predictor"] == pred)]["p-value"].values)
        title = f"{label_map.get(pred, pred)} vs. Child Mortality"
        subtitle = f"R² = {r2[0]:.3f}   |   p = {p_val[0]:.4f}" if len(r2) else ""
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.text(0.98, 0.98, subtitle, transform=ax.transAxes,
                ha="right", va="top", fontsize=10, color="gray")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        pdf.savefig(fig); plt.close()
 
    # --- Plot 6: Predictors vs. Access to Electricity ---
    for pred in pred_existing:
        tmp = df_clean[[TARGET_ELEC, pred]].dropna()
        if len(tmp) < 30:
            continue
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(tmp[pred], tmp[TARGET_ELEC],
                   alpha=0.3, s=15, color="#FF9800")
        m, b   = np.polyfit(tmp[pred], tmp[TARGET_ELEC], 1)
        x_line = np.linspace(tmp[pred].min(), tmp[pred].max(), 100)
        ax.plot(x_line, m * x_line + b, color="black", linewidth=1.5)
        ax.set_xlabel(label_map.get(pred, pred), fontsize=11)
        ax.set_ylabel("Access to Electricity", fontsize=11)
        r2 = (df_reg[(df_reg["Target Variable"] == TARGET_ELEC) &
                     (df_reg["Predictor"] == pred)]["R²"].values)
        p_val = (df_reg[(df_reg["Target Variable"] == TARGET_ELEC) &
                        (df_reg["Predictor"] == pred)]["p-value"].values)
        title = f"{label_map.get(pred, pred)} vs. Access to Electricity"
        subtitle = f"R² = {r2[0]:.3f}   |   p = {p_val[0]:.4f}" if len(r2) else ""
        ax.set_title(title, fontsize=13, fontweight="bold")
        ax.text(0.98, 0.98, subtitle, transform=ax.transAxes,
                ha="right", va="top", fontsize=10, color="gray")
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        pdf.savefig(fig); plt.close()

    # --- Plot 7: VIF bar chart ---
    if not df_vif.empty and df_vif["VIF"].notna().any():
        fig, ax  = plt.subplots(figsize=(12, 5))
        vif_plot = (df_vif.dropna(subset=["VIF"])
                    .sort_values("VIF", ascending=True))
        colors   = ["#F44336" if v > 10 else
                    "#FF9800" if v > 5  else "#4CAF50"
                    for v in vif_plot["VIF"]]
        short_names = [label_map.get(c, c) for c in vif_plot["variable"]]
        ax.barh(short_names, vif_plot["VIF"], color=colors)
        ax.axvline(x=5,  color="orange", linestyle="--",
                   linewidth=1.5, label="VIF = 5 (Warning)")
        ax.axvline(x=10, color="red",    linestyle="--",
                   linewidth=1.5, label="VIF = 10 (Critical)")
        ax.set_xlabel("VIF")
        ax.set_title("Variance Inflation Factor (Multicollinearity)",
                     fontweight="bold")
        ax.legend()
        plt.tight_layout()
        pdf.savefig(fig); plt.close()

print(f"Plots safed: {OUTPUT_PLOTS}")

# =============================================================================
# Step 10 — Export to Excel
# =============================================================================
print(f"\n[10] Export to Excel: {OUTPUT_EXCEL}")

with pd.ExcelWriter(OUTPUT_EXCEL, engine="openpyxl") as writer:
    missing_overview.to_excel(writer, sheet_name="missing e_values",         index=False)
    df_desc.to_excel(         writer, sheet_name="Descriptive Statistics",  index=False)
    corr_spearman.to_excel(   writer, sheet_name="Correlation_Spearman")
    df_vif.to_excel(          writer, sheet_name="VIF_Multicollinearity",index=False)
    df_reg.to_excel(          writer, sheet_name="Bivariate_Regression", index=False)
    df_multivar.to_excel(     writer, sheet_name="Multivariate_Regression", index=False)
    df_trends.to_excel(       writer, sheet_name="Temporal_trends")
    df_outliers.to_excel(     writer, sheet_name="Outliers",             index=False)

print("\n" + "=" * 60)
print("✅ Done!")
print(f"   Excel:  {OUTPUT_EXCEL}")
print(f"   Plots:  {OUTPUT_PLOTS}")
print("=" * 60)
