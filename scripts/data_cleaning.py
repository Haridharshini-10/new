"""
Data cleaning and transformation for hospital patient data.
Handles missing values, outliers, and creates derived metrics.
"""

import sqlite3
import pandas as pd
import numpy as np
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hospital.db')

def clean_and_transform_data(conn):
    """
    Clean and transform raw data into analysis-ready format.
    """
    print("Cleaning and transforming data...")
    
    # Load data from database
    patients = pd.read_sql_query("SELECT * FROM patients", conn)
    admissions = pd.read_sql_query("SELECT * FROM admissions", conn)
    treatments = pd.read_sql_query("SELECT * FROM treatments", conn)
    departments = pd.read_sql_query("SELECT * FROM departments", conn)
    
    # === Clean Patients ===
    print("\n  Cleaning patients table...")
    
    # Handle missing emails (fill with placeholder)
    patients['email'] = patients['email'].fillna('not_provided@hospital.local')
    
    # Handle missing phone numbers
    patients['contact_number'] = patients['contact_number'].fillna('Not Provided')
    
    # Calculate age
    patients['date_of_birth'] = pd.to_datetime(patients['date_of_birth'])
    patients['age'] = (datetime.now() - patients['date_of_birth']).dt.days // 365
    
    # Create age groups
    patients['age_group'] = pd.cut(patients['age'], 
                                    bins=[0, 18, 35, 50, 65, 100],
                                    labels=['0-18', '19-35', '36-50', '51-65', '65+'])
    
    print(f"    ✓ {len(patients)} patients cleaned")
    print(f"    - Age range: {patients['age'].min()} - {patients['age'].max()} years")
    print(f"    - Gender distribution: M={len(patients[patients['gender']=='M'])}, F={len(patients[patients['gender']=='F'])}")
    
    # === Clean Admissions ===
    print("\n  Cleaning admissions table...")
    
    admissions['admission_date'] = pd.to_datetime(admissions['admission_date'])
    admissions['discharge_date'] = pd.to_datetime(admissions['discharge_date'])
    
    # Calculate length of stay
    admissions['length_of_stay'] = (admissions['discharge_date'] - admissions['admission_date']).dt.days
    
    # Handle potentially invalid lengths of stay
    invalid_los = admissions[admissions['length_of_stay'] < 0]
    if len(invalid_los) > 0:
        print(f"    ⚠ Found {len(invalid_los)} admissions with negative length of stay")
        # Swap dates for invalid records
        mask = admissions['length_of_stay'] < 0
        admissions.loc[mask, ['admission_date', 'discharge_date']] = \
            admissions.loc[mask, ['discharge_date', 'admission_date']].values
        admissions['length_of_stay'] = (admissions['discharge_date'] - admissions['admission_date']).dt.days
    
    # Remove extreme outliers (> 120 days) and set to median
    q99 = admissions['length_of_stay'].quantile(0.99)
    print(f"    - 99th percentile LOS: {q99:.1f} days")
    
    # Create LOS categories
    admissions['los_category'] = pd.cut(admissions['length_of_stay'],
                                         bins=[0, 3, 7, 14, 1000],
                                         labels=['Short (<3d)', 'Medium (3-7d)', 'Long (7-14d)', 'Very Long (>14d)'])
    
    # Extract month and year
    admissions['admission_month'] = admissions['admission_date'].dt.month
    admissions['admission_year'] = admissions['admission_date'].dt.year
    admissions['admission_quarter'] = admissions['admission_date'].dt.quarter
    
    # Merge department names
    admissions = admissions.merge(departments[['department_id', 'name']], 
                                   left_on='department_id', right_on='department_id', how='left')
    admissions = admissions.rename(columns={'name': 'department_name'})
    
    print(f"    ✓ {len(admissions)} admissions cleaned")
    print(f"    - Average LOS: {admissions['length_of_stay'].mean():.2f} days")
    print(f"    - Min LOS: {admissions['length_of_stay'].min()} days")
    print(f"    - Max LOS: {admissions['length_of_stay'].max()} days")
    
    # === Clean Treatments ===
    print("\n  Cleaning treatments table...")
    
    treatments['treatment_date'] = pd.to_datetime(treatments['treatment_date'])
    
    # Handle missing effectiveness scores
    treatments['effectiveness_score'] = treatments['effectiveness_score'].fillna(
        treatments['effectiveness_score'].median()
    )
    
    # Handle missing costs
    treatments['treatment_cost'] = treatments['treatment_cost'].fillna(
        treatments.groupby('treatment_type')['treatment_cost'].transform('median')
    )
    
    # Identify and remove extreme cost outliers (> 99.5th percentile)
    cost_p995 = treatments['treatment_cost'].quantile(0.995)
    outliers = treatments[treatments['treatment_cost'] > cost_p995]
    if len(outliers) > 0:
        print(f"    - Removed {len(outliers)} cost outliers (> ${cost_p995:,.0f})")
        treatments = treatments[treatments['treatment_cost'] <= cost_p995]
    
    print(f"    ✓ {len(treatments)} treatments cleaned")
    print(f"    - Average treatment cost: ${treatments['treatment_cost'].mean():,.2f}")
    print(f"    - Total treatment cost: ${treatments['treatment_cost'].sum():,.2f}")
    
    # === Create aggregated metrics ===
    print("\n  Creating derived metrics...")
    
    # Recovery rate by treatment type
    recovery_by_treatment = treatments.groupby('treatment_type').apply(
        lambda x: (x['outcome'].isin(['Recovered', 'Improved'])).sum() / len(x) * 100
    ).round(2)
    
    # Average effectiveness score by treatment type
    effectiveness_by_treatment = treatments.groupby('treatment_type')['effectiveness_score'].mean().round(3)
    
    # Department performance metrics
    dept_admissions = admissions.groupby('department_name').size()
    dept_avg_los = admissions.groupby('department_name')['length_of_stay'].mean().round(2)
    
    print(f"    ✓ Created metrics for {len(recovery_by_treatment)} treatment types")
    print(f"    ✓ Created metrics for {len(dept_admissions)} departments")
    
    # === Calculate Key Performance Indicators ===
    print("\n  Calculating KPIs...")
    
    # Overall recovery rate
    overall_recovery = (treatments['outcome'].isin(['Recovered', 'Improved'])).sum() / len(treatments) * 100
    
    # Average length of stay
    avg_los = admissions['length_of_stay'].mean()
    
    # Readmission rate (patients with multiple admissions)
    readmission_rate = (admissions.groupby('patient_id').size() > 1).sum() / len(patients) * 100
    
    # Treatment cost efficiency (cost per day of care)
    admission_costs = treatments.groupby('admission_id')['treatment_cost'].sum()
    admission_los = admissions.set_index('admission_id')['length_of_stay']
    cost_per_day = (admission_costs / admission_los).mean()
    
    kpis = {
        'Overall Recovery Rate (%)': round(overall_recovery, 2),
        'Average Length of Stay (days)': round(avg_los, 2),
        'Readmission Rate (%)': round(readmission_rate, 2),
        'Average Cost per Day ($)': round(cost_per_day, 2),
        'Total Patients': len(patients),
        'Total Admissions': len(admissions),
        'Total Treatments': len(treatments),
        'Average Treatments per Admission': round(len(treatments) / len(admissions), 2),
    }
    
    print("\n  KPIs Calculated:")
    for key, value in kpis.items():
        print(f"    - {key}: {value}")
    
    # === Save cleaned data ===
    print("\n  Saving cleaned data to database...")
    
    # Create cleaned data tables
    patients.to_sql('patients_cleaned', conn, if_exists='replace', index=False)
    admissions.to_sql('admissions_cleaned', conn, if_exists='replace', index=False)
    treatments.to_sql('treatments_cleaned', conn, if_exists='replace', index=False)
    
    # Save KPIs as reference table
    kpi_df = pd.DataFrame(list(kpis.items()), columns=['metric', 'value'])
    kpi_df.to_sql('kpis', conn, if_exists='replace', index=False)
    
    print("    ✓ Cleaned tables created: patients_cleaned, admissions_cleaned, treatments_cleaned")
    
    conn.commit()
    print("\n✓ Data cleaning and transformation completed!")
    
    return kpis

def main():
    """Main function."""
    print("=" * 60)
    print("Hospital Data Cleaning & Transformation")
    print("=" * 60)
    
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database not found at {DATABASE_PATH}")
        print("Please run load_data.py first!")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    kpis = clean_and_transform_data(conn)
    conn.close()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    for key, value in kpis.items():
        print(f"{key}: {value}")

if __name__ == "__main__":
    main()
