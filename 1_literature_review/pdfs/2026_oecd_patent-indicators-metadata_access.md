# OECD Patent Indicators Metadata Access Note

- Source: OECD Environment Statistics, `Patents - indicators` database documentation.
- URL: https://webfs-env.oecd.org/files/Patent%20indicators%20metadata.pdf
- Local file: `1_literature_review/pdfs/2026_oecd_patent-indicators-metadata.pdf`
- Accessed: 2026-07-06
- OECD dataflow: `OECD.ENV.EPI:DSD_PAT_IND@DF_PAT_IND`
- SDMX data-structure endpoint: https://sdmx.oecd.org/public/rest/v1/datastructure/OECD.ENV.EPI/DSD_PAT_IND/1.0?references=all
- Purpose: Authoritative project reference for interpreting OECD patent indicator combinations such as `PT_INV.DEV.ENV_PAT._Z`, `PT_TECH.DEV.ENV_PAT._Z`, `INV_PS.DEV.ENV_PAT._Z`, and `IX.DEV.ENV_PAT._Z`.

Use this file together with the OECD SDMX codelists. The short `UNIT_MEASURE` labels alone are not sufficient to infer a full series-level denominator.

## Key Schema

OECD API keys for this dataflow use:

`REF_AREA.FREQ.UNIT_MEASURE.TYPE.TECH.PAT`

The database-code shorthand used in project documentation is the final four dimensions:

`UNIT_MEASURE.TYPE.TECH.PAT`

Example: the Australia annual series for the project target is requested as `AUS.A.PT_INV.DEV.ENV_PAT._Z`; the shorthand is `PT_INV.DEV.ENV_PAT._Z`.

## PDF Indicator Entry To Database-Code Map

| PDF metadata entry | OECD database code or pattern | Notes for project interpretation |
|---|---|---|
| Development of environment-related technologies, % all technologies | `PT_TECH.DEV.ENV_PAT._Z` | Environment-related higher-value domestic inventions as a percentage of all domestic inventions. This is a domestic portfolio share, not the project target. |
| Relative advantage in environment-related technologies | `IX.DEV.ENV_PAT._Z` | Relative technological advantage index: domestic environment-related share divided by the world environment-related share. |
| Development of environment-related technologies, % inventions worldwide | `PT_INV.DEV.ENV_PAT._Z` | Country or aggregate contribution to worldwide environment-related inventions. This is the selected project target definition. |
| Development of environment-related technologies, inventions per capita | `INV_PS.DEV.ENV_PAT._Z` | PDF defines the denominator as per million residents; OECD CSV reports `UNIT_MEASURE=INV_PS` and `UNIT_MULT=6`. |
| Development of environment-related technologies, inventions per unit of government R&D | `INV_RD_S13.DEV.ENV_PAT._Z` | Inventions per million USD PPP of environment/energy-related government R&D budget. |
| Development of environment-related technologies, percentage of environment-related technologies. By domain | `PT_TECH_ENV.DEV.<ENV_TECH_DOMAIN>._Z` | Domain shares within environment-related inventions. Example: `PT_TECH_ENV.DEV.ENE._Z`. Do not treat `ENV_PAT` as a domain breakdown; it is the broad environment-related technology total. |
| Diffusion of environment-related technologies, % all technologies | `PT_TECH.DIFF.ENV_PAT._Z` for national jurisdictions; `PT_TECH.DIFF.ENV_PAT.<PAT_OFFICE>` for regional-office breakdowns | Diffusion market-protection share relative to all patent applications deposited in the jurisdiction. For national markets, `REF_AREA` is the country and `PAT=_Z`; for regional offices, `REF_AREA=_Z` and `PAT` carries the office code. |
| Diffusion of environment-related technologies, % inventions worldwide | `PT_INV.DIFF.ENV_PAT._Z` for national jurisdictions; `PT_INV.DIFF.ENV_PAT.<PAT_OFFICE>` for regional-office breakdowns | Percentage of the global green-technology pool seeking protection in a market. OECD notes that sums across markets can exceed 100 because the same invention can seek protection in multiple jurisdictions. |
| Diffusion of environment-related technologies, percentage of environment-related technologies. By domain | `PT_TECH_ENV.DIFF.<ENV_TECH_DOMAIN>._Z` for national jurisdictions; `PT_TECH_ENV.DIFF.<ENV_TECH_DOMAIN>.<PAT_OFFICE>` for regional-office breakdowns | Domain shares within environment-related inventions deposited in a jurisdiction. Example: `PT_TECH_ENV.DIFF.ENE._Z`. |
| International collaboration in development of environment-related technologies, % collaboration in all technologies | `PT_TECH_COL.COL.ENV_PAT._Z` | Environment-related co-inventions as a percentage of all domestic co-inventions. Counts use patent-family size 1 in the PDF metadata. |
| Development of renewable energy technologies, inventions per unit of public RD&D | `INV_RD_S1ZS.RENEW.ENV_PAT._Z` | Renewable-energy inventions per million USD 2010 PPP of public RD&D. Use `S1ZS` for public RD&D; `S13` is the separate government R&D denominator used in the environment-related R&D entry above. |

## Dimension Notes

- `TYPE`: `DEV` = development of environment-related technologies; `DIFF` = diffusion of environment-related technologies; `COL` = international collaboration in development; `RENEW` = development of renewable energy technologies.
- `UNIT_MEASURE`: `PT_TECH` = percentage of technologies; `PT_INV` = percentage of inventions; `INV_PS` = inventions per person; `INV_RD_S13` = inventions per unit of government R&D; `INV_RD_S1ZS` = inventions per unit of public R&D; `IX` = index; `PT_TECH_ENV` = percentage of environment-related technologies; `PT_TECH_COL` = percentage of collaborations in all technologies.
- `TECH`: `ENV_PAT` is the broad environment-related technology group. Domain rows use a specific `CL_TECH_PAT` code such as `ENE`, `MAN`, `ADAPT`, `BUILD`, `GHG`, `GOODS`, `ICT`, `OCEAN`, `TRA`, or `WAT_WASTE`.
- `PAT`: `_Z` means not applicable/no regional patent-office breakdown. Regional patent-office breakdown codes in the SDMX codelist include `WIPO`, `OAPI`, `EAPO`, `ARIPO`, `EPO`, `GCC`, and `PCT`; do not mix these breakdown rows with the main country-year target.
