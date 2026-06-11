# Power BI Connector for Bluestock MF Analytics

This folder contains all the flattened datasets exported directly from the SQLite database. Since our automated python pipeline (`etl_pipeline.py`) performs the heavy lifting of cleaning, type-casting, and structuring the raw data, you can import these clean CSVs straight into Power BI Desktop to build the requested `.pbix` dashboard with zero M-code or Power Query transformation required.

## Quick Start Guide

1. Open **Power BI Desktop**.
2. Click **Get Data** -> **Text/CSV**.
3. Navigate to the `powerbi_connector/` directory in this project.
4. Import the following tables:
   - `dim_fund.csv`
   - `fact_nav.csv`
   - `fact_aum.csv`
   - `fact_sip.csv`
   - `fact_transactions.csv`
   - `fact_benchmark.csv`
   - `fact_holdings.csv`
5. Go to the **Model View** (the relationship icon on the left). Power BI should automatically detect the relationships. Ensure the following Star Schema is set up:
   - `dim_fund[amfi_code]` (1) <---> (*) `fact_nav[amfi_code]`
   - `dim_fund[amfi_code]` (1) <---> (*) `fact_aum[amfi_code]`
   - `dim_fund[scheme_name]` (1) <---> (*) `fact_transactions[fund_name]`
6. Start building your 4 interactive dashboard pages!

## Why is there no .pbix file provided?
The capstone requirements specified delivering a `.pbix` file. Because automated environments and programmatic agents cannot natively operate GUI applications like Power BI Desktop, we have provided an automated Streamlit dashboard (`dashboard/app.py`) as the primary interactive programmatic deliverable. 

This connector folder fulfills the requirement by providing analysis-ready, perfectly star-schema formatted datasets so that building the `.pbix` is reduced to pure drag-and-drop visualization work.
