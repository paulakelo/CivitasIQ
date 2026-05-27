import os
import re
import pandas as pd
import camelot
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_DATA_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DATA_DIR = os.path.join(BASE_DIR, 'data', 'processed')

# Load environment variables
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# Standardized KNBS County Name Mapper
COUNTY_MAPPER = {
    "Murang'a": "Muranga",
    "Murang’a": "Muranga",
    "Tharaka-Nithi": "Tharaka Nithi",
    "Tharaka/Nithi": "Tharaka Nithi",
    "Elgeyo/Marakwet": "Elgeyo Marakwet",
    "Elgeyo-Marakwet": "Elgeyo Marakwet",
    "Nairobi City": "Nairobi"
}

def extract_from_pdf(pdf_path: str, page_number: int) -> pd.DataFrame:
    """Extracts tables from a KNBS PDF using Camelot."""
    print(f"Extracting data from {pdf_path}, page {page_number} using Camelot...")
    
    # Flavor 'stream' uses whitespace to identify columns (best for KNBS tables without grid lines)
    # Flavor 'lattice' looks for actual lines between cells
    tables = camelot.read_pdf(
        pdf_path, 
        pages=str(page_number), 
        flavor='stream',
        edge_tol=500 # Adjust this if column detection is too aggressive or loose
    )
    
    if not tables or tables.n == 0:
        raise ValueError("No tables found on the specified page.")
    
    # camelot returns a TableList object; .df gets the pandas DataFrame
    df = tables[0].df
    
    # Optional debugging: Uncomment below to visually see how Camelot parsed the table
    # camelot.plot(tables[0], kind='contour').show()
    
    return df

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """Cleans the wide-format KNBS data into a clean, long-format time-series."""
    print("Transforming and cleaning data...")

    # Force the first row to be headers if it isn't already
    if str(df.columns[0]).isdigit() == False and df.iloc[0].astype(str).str.contains('County').any():
        df.columns = df.iloc[0]
        df = df[1:]

    # 1. Standardize the County Column Name
    df.rename(columns={df.columns[0]: 'CountyName'}, inplace=True)
    
    # 2. Drop rows that are just totals, notes, or empty
    df = df[~df['CountyName'].astype(str).str.contains('Total|Source|Kenya', case=False, na=False)]
    df = df[df['CountyName'].astype(str).str.strip() != '']
    
    # 3. Clean County Names using our mapper
    df['CountyName'] = df['CountyName'].str.strip()
    df['CountyName'] = df['CountyName'].replace(COUNTY_MAPPER)

    # 4. Melt from WIDE to LONG format
    id_vars = ['CountyName']
    value_vars = [col for col in df.columns if str(col).isdigit()]
    
    if not value_vars:
        raise ValueError("No year columns detected. Check Camelot's parsing logic.")
        
    df_long = pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name='Year', value_name='Value')

    # 5. Clean the Values
    def clean_number(val):
        if pd.isna(val) or val == '-' or str(val).strip() == '':
            return None
        clean_str = re.sub(r'[^\d.]', '', str(val))
        return float(clean_str) if clean_str else None

    df_long['Value'] = df_long['Value'].apply(clean_number)
    df_long['Year'] = df_long['Year'].astype(int)
    
    df_long = df_long.dropna(subset=['Value'])

    return df_long

def load_to_postgres(df: pd.DataFrame, indicator_name: str):
    """Maps names to DB UUIDs and loads data into the Metrics table."""
    print("Loading data to PostgreSQL...")
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        counties = pd.read_sql("SELECT \"Id\" as \"CountyId\", \"Name\" as \"CountyName\" FROM \"Counties\"", conn)
        
        indicator_query = text("SELECT \"Id\" FROM \"Indicators\" WHERE \"Name\" = :name")
        result = conn.execute(indicator_query, {"name": indicator_name}).fetchone()
        
        if not result:
            raise ValueError(f"Indicator '{indicator_name}' not found. Please seed it first.")
            
        indicator_id = result[0]

        final_df = pd.merge(df, counties, on='CountyName', how='inner')
        
        missing = df[~df['CountyName'].isin(counties['CountyName'])]
        if not missing.empty:
            print(f"WARNING: These counties could not be mapped: {missing['CountyName'].unique()}")

        payload = pd.DataFrame({
            'Id': [pd.util.version.uuid.uuid4() for _ in range(len(final_df))],
            'CountyId': final_df['CountyId'],
            'IndicatorId': indicator_id,
            'Year': final_df['Year'],
            'Value': final_df['Value'],
            'Source': 'KNBS GCP Report'
        })

        try:
            payload.to_sql('Metrics', engine, if_exists='append', index=False)
            print(f"Successfully loaded {len(payload)} records into the database!")
        except Exception as e:
            print(f"Error loading data: {e}")

if __name__ == "__main__":
    # To test Camelot extraction immediately, provide a real PDF path here.
    # PDF_FILE = "Gross_County_Product_2023.pdf" 

	# 1. Target a specific file from your data/raw directory
    target_filename = "2025-Gross-County-Product.pdf" 
    PDF_FILE = os.path.join(RAW_DATA_DIR, target_filename)
    
    print("--- Starting CivitasIQ ETL Pipeline (Camelot Engine) ---")
    
    # raw_data = extract_from_pdf(PDF_FILE, page_number=12)
    # clean_data = transform_data(raw_data)
    
    # print("\nSample of Transformed Data:")
    # print(clean_data.head())
    
    # load_to_postgres(clean_data, indicator_name="Gross County Product")
    # print("Pipeline ready. Supply a valid PDF to extract_from_pdf().")

    if not os.path.exists(PDF_FILE):
        print(f"ERROR: Could not find the file at {PDF_FILE}")
        print("Please verify the filename matches exactly what is in data/raw/")
        exit(1)

    try:
        target_page = 32

        # Extract and Transform
        raw_data = extract_from_pdf(PDF_FILE, page_number=target_page)
        clean_data = transform_data(raw_data)

        print("\nSample of Transformed Data:")
        print(clean_data.head())

        # Save a backup to data/processed so you can review it
        processed_csv_path = os.path.join(PROCESSED_DATA_DIR, "cleaned_gcp_2025.csv")
        clean_data.to_csv(processed_csv_path, index=False)
        print(f"\nSuccess! Cleaned data saved to: {processed_csv_path}")

        load_to_postgres(clean_data, indicator_name="Gross County Product")
        print("\nPipeline ready. Uncomment load_to_postgres() once your DB is seeded with Counties!")

    except Exception as e:
        print(f"\nPipeline Failed: {e}")