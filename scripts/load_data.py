"""
Load generated hospital data into SQLite database.
Handles CSV import and data validation.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hospital.db')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
SQL_SCRIPT = os.path.join(os.path.dirname(__file__), 'setup_database.sql')

def setup_database():
    """Create database schema from SQL script."""
    print("Setting up database schema...")
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Read and execute SQL script
    with open(SQL_SCRIPT, 'r') as f:
        sql_script = f.read()
    
    # Execute script (handle multiple statements)
    for statement in sql_script.split(';'):
        if statement.strip():
            cursor.execute(statement)
    
    conn.commit()
    print("✓ Database schema created!")
    return conn

def load_patients(conn):
    """Load patient data into database."""
    print("Loading patient data...")
    
    patients_file = os.path.join(DATA_DIR, 'patients.csv')
    df = pd.read_csv(patients_file)
    
    # Remove age column as it's not in schema
    df = df.drop(columns=['age'], errors='ignore')
    
    df.to_sql('patients', conn, if_exists='append', index=False)
    print(f"✓ Loaded {len(df):,} patients")
    return len(df)

def load_admissions(conn):
    """Load admission data into database."""
    print("Loading admission data...")
    
    admissions_file = os.path.join(DATA_DIR, 'admissions.csv')
    df = pd.read_csv(admissions_file)
    
    # Map department name to department_id
    dept_query = "SELECT department_id, name FROM departments"
    dept_df = pd.read_sql_query(dept_query, conn)
    dept_map = dict(zip(dept_df['name'], dept_df['department_id']))
    
    df['department_id'] = df['department'].map(dept_map)
    
    # Drop unnecessary columns and rename
    df = df.drop(columns=['department', 'length_of_stay'], errors='ignore')
    df = df.rename(columns={'status': 'status'})
    
    # Reorder columns to match schema
    df = df[['patient_id', 'department_id', 'admission_date', 'discharge_date', 
             'admission_reason', 'status']]
    
    df.to_sql('admissions', conn, if_exists='append', index=False)
    print(f"✓ Loaded {len(df):,} admissions")
    return len(df)

def load_treatments(conn):
    """Load treatment data into database."""
    print("Loading treatment data...")
    
    treatments_file = os.path.join(DATA_DIR, 'treatments.csv')
    df = pd.read_csv(treatments_file)
    
    # Reorder columns to match schema
    df = df[['admission_id', 'treatment_type', 'treatment_date', 'treatment_cost', 
             'outcome', 'effectiveness_score']]
    
    df.to_sql('treatments', conn, if_exists='append', index=False)
    print(f"✓ Loaded {len(df):,} treatments")
    return len(df)

def validate_data(conn):
    """Validate loaded data."""
    print("\nValidating data integrity...")
    
    cursor = conn.cursor()
    
    # Check patient count
    cursor.execute("SELECT COUNT(*) FROM patients")
    patient_count = cursor.fetchone()[0]
    print(f"  Patients: {patient_count:,}")
    
    # Check admission count
    cursor.execute("SELECT COUNT(*) FROM admissions")
    admission_count = cursor.fetchone()[0]
    print(f"  Admissions: {admission_count:,}")
    
    # Check treatment count
    cursor.execute("SELECT COUNT(*) FROM treatments")
    treatment_count = cursor.fetchone()[0]
    print(f"  Treatments: {treatment_count:,}")
    
    # Check for orphaned admissions
    cursor.execute("""
        SELECT COUNT(*) FROM admissions a 
        WHERE NOT EXISTS (SELECT 1 FROM patients p WHERE p.patient_id = a.patient_id)
    """)
    orphaned = cursor.fetchone()[0]
    if orphaned > 0:
        print(f"  ⚠ Warning: {orphaned} orphaned admissions found")
    
    # Check for orphaned treatments
    cursor.execute("""
        SELECT COUNT(*) FROM treatments t 
        WHERE NOT EXISTS (SELECT 1 FROM admissions a WHERE a.admission_id = t.admission_id)
    """)
    orphaned = cursor.fetchone()[0]
    if orphaned > 0:
        print(f"  ⚠ Warning: {orphaned} orphaned treatments found")
    
    print("✓ Data validation completed!")
    return patient_count, admission_count, treatment_count

def main():
    """Main function."""
    print("=" * 60)
    print("Hospital Data Loader")
    print("=" * 60)
    
    # Remove existing database
    if os.path.exists(DATABASE_PATH):
        os.remove(DATABASE_PATH)
        print(f"Removed existing database: {DATABASE_PATH}")
    
    # Setup database
    conn = setup_database()
    
    # Load data
    print()
    load_patients(conn)
    load_admissions(conn)
    load_treatments(conn)
    
    # Validate
    print()
    patient_count, admission_count, treatment_count = validate_data(conn)
    
    # Commit and close
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print(f"✓ Data successfully loaded to: {DATABASE_PATH}")
    print("=" * 60)

if __name__ == "__main__":
    main()
