import os
import re
import uuid
import pandas as pd
import camelot
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# Comprehensive County Name Mapper (Handles title casing quirks with apostrophes)
COUNTY_MAPPER = {
    "Murang'a": "Muranga",
    "Murang'A": "Muranga",
    "Murang’a": "Muranga",
    "Murang’A": "Muranga",
    "Tharaka-Nithi": "Tharaka Nithi",
    "Tharaka/Nithi": "Tharaka Nithi",
    "Elgeyo/Marakwet": "Elgeyo Marakwet",
    "Elgeyo-Marakwet": "Elgeyo Marakwet",
    "Taita/Taveta": "Taita Taveta",
    "Taita-Taveta": "Taita Taveta",
    "Nairobi City": "Nairobi"
}

def extract_from_pdf(pdf_path: str, page_number: int) -> pd.DataFrame:
    print(f"Extracting data from {pdf_path}, page {page_number} using Camelot...")
    
    tables = camelot.read_pdf(
        pdf_path, 
        pages=str(page_number), 
        flavor='stream',
        edge_tol=500 
    )
    
    if not tables or tables.n == 0:
        raise ValueError(f"No tables found on page {page_number}.")
    
    df = tables[0].df
    
    # Debug raw dump
    raw_debug_path = os.path.join(PROCESSED_DATA_DIR, f"debug_raw_page_{page_number}.csv")
    df.to_csv(raw_debug_path, index=False)
    print(f"-> Raw Camelot extraction saved to {raw_debug_path}")
    
    return df

def transform_data(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """
    Dynamically transforms data based on table structural signature.
    Returns: (Cleaned Long DataFrame, Indicator Name)
    """
    print("Transforming and cleaning data...")

    # Look for a signature text snippet to determine if this is the Population Table
    # Row 0 or 1 usually contains descriptive text in the raw extraction
    is_population_table = df.astype(str).apply(lambda x: x.str.contains('Population|Density|KPHC', case=False)).any().any()

    if is_population_table:
        print("-> Detected Table Signature: Projected Population (Page 18)")
        
        # Based on your debug file, the first column is the County. 
        # Columns 1 is 2019 baseline. Columns 4, 5, 6, 7, 8 correspond to 2020, 2021, 2022, 2023, 2024 projections.
        # We explicitly drop structural meta rows before naming the columns
        df.rename(columns={df.columns[0]: 'CountyName'}, inplace=True)
        
        # Drop rows that don't represent clear county data
        df = df[~df['CountyName'].astype(str).str.contains('Total|Source|Kenya|County|Projections', case=False, na=False)]
        df = df[df['CountyName'].astype(str).str.strip() != '']
        
        # Re-assign semantic column names matching the exact layout of Page 18
        # Format: County, 2019, Area, Density, 2020, 2021, 2022, 2023, 2024
        df.columns = ['CountyName', '2019', 'AreaSqKm', 'Density', '2020', '2021', '2022', '2023', '2024']
        
        indicator_name = "Population"
        # Melt only the explicit time-series columns (ignoring Area and Density for this Metric payload)
        value_vars = ['2019', '2020', '2021', '2022', '2023', '2024']
        id_vars = ['CountyName']

    else:
        print("-> Detected Table Signature: Gross County Product (Page 32)")
        if str(df.columns[0]).isdigit() == False and df.iloc[0].astype(str).str.contains('County', case=False).any():
            df.columns = df.iloc[0]
            df = df[1:]

        df.rename(columns={df.columns[0]: 'CountyName'}, inplace=True)
        df.columns = [str(col).replace('*', '').strip() for col in df.columns]
        
        df = df[~df['CountyName'].astype(str).str.contains('Total|Source|Kenya', case=False, na=False)]
        df = df[df['CountyName'].astype(str).str.strip() != '']
        
        indicator_name = "Gross County Product"
        id_vars = ['CountyName']
        value_vars = [col for col in df.columns if str(col).isdigit()]

    # Global transformations across both formats
    df['CountyName'] = df['CountyName'].str.strip().str.title().replace(COUNTY_MAPPER)
    
    if not value_vars:
        raise ValueError("No year columns detected during structural profiling.")
        
    df_long = pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name='Year', value_name='Value')

    def clean_number(val):
        if pd.isna(val) or str(val).strip() in ['-', '']:
            return None
        clean_str = re.sub(r'[^\d.]', '', str(val))
        return float(clean_str) if clean_str else None

    df_long['Value'] = df_long['Value'].apply(clean_number)
    df_long['Year'] = df_long['Year'].astype(int)
    df_long = df_long.dropna(subset=['Value'])

    return df_long, indicator_name

def load_to_postgres(df: pd.DataFrame, indicator_name: str):
    print(f"Loading '{indicator_name}' metrics to PostgreSQL...")
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        counties = pd.read_sql("SELECT \"Id\" as \"CountyId\", \"Name\" as \"CountyName\" FROM \"Counties\"", conn)
        
        indicator_query = text("SELECT \"Id\" FROM \"Indicators\" WHERE \"Name\" = :name")
        result = conn.execute(indicator_query, {"name": indicator_name}).fetchone()
        
        if not result:
            raise ValueError(f"Indicator '{indicator_name}' not found. Please seed your database via the C# project first.")
            
        indicator_id = result[0]
        final_df = pd.merge(df, counties, on='CountyName', how='inner')
        
        missing = df[~df['CountyName'].isin(counties['CountyName'])]
        if not missing.empty:
            print(f"WARNING: These counties could not be mapped: {missing['CountyName'].unique()}")

        payload = pd.DataFrame({
            'Id': [uuid.uuid4() for _ in range(len(final_df))],
            'CountyId': final_df['CountyId'],
            'IndicatorId': indicator_id,
            'Year': final_df['Year'],
            'Value': final_df['Value'],
            'Source': 'KNBS GCP Report 2025'
        })

        try:
            payload.to_sql('Metrics', engine, if_exists='append', index=False)
            print(f"Successfully loaded {len(payload)} rows into the Metrics table!")
        except Exception as e:
            print(f"Database write failure: {e}")

if __name__ == "__main__":
    target_filename = "2025-Gross-County-Product.pdf" 
    PDF_FILE = os.path.join(RAW_DATA_DIR, target_filename)
    
    print("--- Starting CivitasIQ Multitask Ingestion Engine ---")

    if not os.path.exists(PDF_FILE):
        print(f"ERROR: Could not find raw target file at {PDF_FILE}")
        exit(1)

    # Change this configuration array to ingest whatever pages you want!
    PAGES_TO_PROCESS = [18, 33] 

    for page in PAGES_TO_PROCESS:
        try:
            print(f"\n--- Processing Queue Item: Page {page} ---")
            raw_data = extract_from_pdf(PDF_FILE, page_number=page)
            clean_data, extracted_indicator = transform_data(raw_data)

            print(f"Sample of processed data for '{extracted_indicator}':")
            print(clean_data.head(5))

            # Export storage backup
            processed_csv_path = os.path.join(PROCESSED_DATA_DIR, f"cleaned_{extracted_indicator.lower().replace(' ', '_')}.csv")
            clean_data.to_csv(processed_csv_path, index=False)
            
            # Load straight to PostgreSQL database
            load_to_postgres(clean_data, indicator_name=extracted_indicator)
            
        except Exception as e:
            print(f"Processing failed for Page {page}: {e}")