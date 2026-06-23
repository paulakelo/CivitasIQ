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

# Comprehensive County Name Mapper
COUNTY_MAPPER = {
    "Murang'a": "Muranga",
    "Murang'A": "Muranga",
    "Murang’a": "Muranga",
    "Murang’A": "Muranga",
    "Tharaka-Nithi": "Tharaka Nithi",
    "Tharaka/Nithi": "Tharaka Nithi",
    "Elgeyo/Marakwet": "Elgeyo Marakwet",
    "Elgeyo-Marakwet": "Elgeyo Marakwet",
    "Elgeyo Marakwet": "Elgeyo Marakwet",
    "Elgeyo": "Elgeyo Marakwet",
    "Taita/Taveta": "Taita Taveta",
    "Taita-Taveta": "Taita Taveta",
    "Nairobi City": "Nairobi"
}

def extract_from_pdf(pdf_path: str, pages: str) -> pd.DataFrame:
    """Extracts tables from a KNBS PDF using Camelot. Accepts page ranges like '32-33'."""
    print(f"Extracting data from {pdf_path}, pages {pages} using Camelot...")
    
    tables = camelot.read_pdf(
        pdf_path, 
        pages=pages, 
        flavor='stream',
        edge_tol=500 
    )
    
    if not tables or tables.n == 0:
        raise ValueError(f"No tables found on pages {pages}.")
    
    # NEW: Concatenate all tables found across the page range into one massive DataFrame
    df = pd.concat([t.df for t in tables], ignore_index=True)
    
    raw_debug_path = os.path.join(PROCESSED_DATA_DIR, f"debug_raw_pages_{pages.replace('-','_')}.csv")
    df.to_csv(raw_debug_path, index=False)
    
    return df

def transform_data(df: pd.DataFrame, indicator_name: str) -> pd.DataFrame:
    """Cleans data based on the requested indicator."""
    print(f"Transforming and cleaning data for '{indicator_name}'...")

    if indicator_name == "Population":
        df.rename(columns={df.columns[0]: 'CountyName'}, inplace=True)
        df = df[~df['CountyName'].astype(str).str.contains('Total|Source|Kenya|County|Projections', case=False, na=False)]
        df = df[df['CountyName'].astype(str).str.strip() != '']
        df.columns = ['CountyName', '2019', 'AreaSqKm', 'Density', '2020', '2021', '2022', '2023', '2024']
        value_vars = ['2019', '2020', '2021', '2022', '2023', '2024']
        id_vars = ['CountyName']

    elif indicator_name == "Gross County Product":
        if str(df.columns[0]).isdigit() == False and df.iloc[0].astype(str).str.contains('County', case=False).any():
            df.columns = df.iloc[0]
            df = df[1:]

        df.rename(columns={df.columns[0]: 'CountyName'}, inplace=True)
        df.columns = [str(col).replace('*', '').strip() for col in df.columns]
        
        df = df[~df['CountyName'].astype(str).str.contains('Total|Source|Kenya|County', case=False, na=False)]
        df = df[df['CountyName'].astype(str).str.strip() != '']
        
        id_vars = ['CountyName']
        value_vars = [col for col in df.columns if str(col).isdigit()]

    # NEW: Fix line breaks like "Elgeyo/\nMarakwet" before mapping
    df['CountyName'] = df['CountyName'].astype(str).str.replace(r'\n', '', regex=True)
    df['CountyName'] = df['CountyName'].str.replace(r'/', ' ', regex=True)
    
    # Global transformations
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

    return df_long

def load_to_postgres(df: pd.DataFrame, indicator_name: str):
    print(f"Loading '{indicator_name}' metrics to PostgreSQL...")
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        counties = pd.read_sql("SELECT \"Id\" as \"CountyId\", \"Name\" as \"CountyName\" FROM \"Counties\"", conn)
        
        indicator_query = text("SELECT \"Id\" FROM \"Indicators\" WHERE \"Name\" = :name")
        result = conn.execute(indicator_query, {"name": indicator_name}).fetchone()
        
        if not result:
            raise ValueError(f"Indicator '{indicator_name}' not found. Seed the DB first.")
            
        indicator_id = result[0]
        
        # --- NEW: Pipeline Idempotency ---
        # Clear existing data for this indicator to prevent UniqueViolation crashes
        print(f"-> Cleaning existing records for {indicator_name} to prevent duplicate conflicts...")
        conn.execute(text('DELETE FROM "Metrics" WHERE "IndicatorId" = :ind_id'), {"ind_id": indicator_id})
        conn.commit() # Important for SQLAlchemy 2.0

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

    # NEW: Define exact tasks and page ranges to process together
    TASKS = [
        {"indicator": "Population", "pages": "18"},
        {"indicator": "Gross County Product", "pages": "32-33"} # Combines both pages seamlessly!
    ]

    for task in TASKS:
        try:
            print(f"\n--- Processing Queue Item: {task['indicator']} ---")
            raw_data = extract_from_pdf(PDF_FILE, pages=task['pages'])
            
            clean_data = transform_data(raw_data, indicator_name=task['indicator'])

            processed_csv_path = os.path.join(PROCESSED_DATA_DIR, f"cleaned_{task['indicator'].lower().replace(' ', '_')}.csv")
            clean_data.to_csv(processed_csv_path, index=False)
            
            load_to_postgres(clean_data, indicator_name=task['indicator'])
            
        except Exception as e:
            print(f"Processing failed for {task['indicator']}: {e}")