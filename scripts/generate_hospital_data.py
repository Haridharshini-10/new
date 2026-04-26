"""
Generate realistic synthetic hospital patient data for analysis.
Creates 5,000+ patient records with admissions and treatments.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Configuration
NUM_PATIENTS = 5000
NUM_ADMISSIONS_MULTIPLIER = 1.2  # Some patients admitted multiple times
DATA_START_DATE = datetime(2024, 1, 1)
DATA_END_DATE = datetime(2025, 7, 31)

# Constants
DEPARTMENTS = ['Cardiology', 'Orthopedics', 'Neurology', 'General Medicine', 
               'Emergency', 'Pediatrics', 'ICU', 'Surgery']
GENDERS = ['M', 'F']
ADMISSION_REASONS = [
    'Chest Pain', 'Fracture', 'Severe Headache', 'Fever/Infection', 'Trauma',
    'Post-Operative Care', 'Chronic Disease Management', 'Emergency', 'Routine Check',
    'Acute Illness', 'Surgical Complication', 'Rehabilitation'
]
TREATMENT_TYPES = ['Medication', 'Surgery', 'Physical Therapy', 'Chemotherapy', 
                   'Radiation', 'Cardiac Intervention', 'Joint Replacement', 'Conservative Treatment']
TREATMENT_OUTCOMES = ['Recovered', 'Improved', 'Stable', 'Declined', 'Discharged']
ADMISSION_STATUS = ['Discharged', 'Transferred', 'Left Against Medical Advice', 'Active']

def random_date(start_date, end_date):
    """Generate random date between start and end date."""
    time_delta = end_date - start_date
    random_days = random.randint(0, time_delta.days)
    return start_date + timedelta(days=random_days)

def generate_patients(num_patients):
    """Generate patient records."""
    print(f"Generating {num_patients} patients...")
    
    first_names = ['John', 'Jane', 'Michael', 'Sarah', 'Robert', 'Emma', 'James', 'Olivia', 
                   'David', 'Sophia', 'Richard', 'Isabella', 'Joseph', 'Ava', 'Thomas']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                  'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson']
    
    patients = []
    for i in range(num_patients):
        dob = random_date(datetime(1930, 1, 1), datetime(2010, 12, 31))
        patient = {
            'patient_id': i + 1,
            'first_name': random.choice(first_names),
            'last_name': random.choice(last_names),
            'date_of_birth': dob.date(),
            'gender': random.choice(GENDERS),
            'age': (datetime.now() - dob).days // 365
        }
        patients.append(patient)
    
    return pd.DataFrame(patients)

def generate_admissions(patients_df, num_patients):
    """Generate admission records."""
    print(f"Generating admission records...")
    
    num_admissions = int(num_patients * NUM_ADMISSIONS_MULTIPLIER)
    admissions = []
    
    for i in range(num_admissions):
        patient_id = np.random.randint(1, num_patients + 1)
        admission_date = random_date(DATA_START_DATE, DATA_END_DATE)
        
        # Length of stay between 1 to 30 days (skewed towards shorter stays)
        los = np.random.exponential(scale=3) + 1
        los = int(np.clip(los, 1, 30))
        discharge_date = admission_date + timedelta(days=los)
        
        admission = {
            'admission_id': i + 1,
            'patient_id': patient_id,
            'department': np.random.choice(DEPARTMENTS),
            'admission_date': admission_date.date(),
            'discharge_date': discharge_date.date(),
            'length_of_stay': los,
            'admission_reason': np.random.choice(ADMISSION_REASONS),
            'status': np.random.choice(ADMISSION_STATUS, p=[0.60, 0.15, 0.10, 0.15])
        }
        admissions.append(admission)
    
    return pd.DataFrame(admissions)

def generate_treatments(admissions_df):
    """Generate treatment records for each admission."""
    print(f"Generating treatment records...")
    
    treatments = []
    treatment_id = 1
    
    for idx, admission in admissions_df.iterrows():
        # Number of treatments per admission (1-5)
        num_treatments = np.random.randint(1, 6)
        
        admission_start = admission['admission_date']
        admission_end = admission['discharge_date']
        
        for _ in range(num_treatments):
            treatment_date = random_date(
                datetime.combine(admission_start, datetime.min.time()),
                datetime.combine(admission_end, datetime.min.time())
            )
            
            treatment_type = np.random.choice(TREATMENT_TYPES)
            
            # Cost varies by treatment type
            cost_map = {
                'Medication': np.random.uniform(100, 1000),
                'Surgery': np.random.uniform(5000, 50000),
                'Physical Therapy': np.random.uniform(200, 500),
                'Chemotherapy': np.random.uniform(2000, 10000),
                'Radiation': np.random.uniform(3000, 15000),
                'Cardiac Intervention': np.random.uniform(10000, 50000),
                'Joint Replacement': np.random.uniform(20000, 80000),
                'Conservative Treatment': np.random.uniform(500, 2000)
            }
            cost = cost_map.get(treatment_type, np.random.uniform(500, 5000))
            
            # Effectiveness score (0.0 to 1.0)
            effectiveness = np.random.uniform(0.5, 1.0)
            
            treatment = {
                'treatment_id': treatment_id,
                'admission_id': admission['admission_id'],
                'treatment_type': treatment_type,
                'treatment_date': treatment_date.date(),
                'treatment_cost': round(cost, 2),
                'outcome': np.random.choice(TREATMENT_OUTCOMES),
                'effectiveness_score': round(effectiveness, 2)
            }
            treatments.append(treatment)
            treatment_id += 1
    
    return pd.DataFrame(treatments)

def main():
    """Main function to generate all data."""
    print("=" * 60)
    print("Hospital Patient Insights - Data Generation")
    print("=" * 60)
    
    # Create data directory if not exists
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate data
    patients_df = generate_patients(NUM_PATIENTS)
    admissions_df = generate_admissions(patients_df, NUM_PATIENTS)
    treatments_df = generate_treatments(admissions_df)
    
    # Save to CSV
    patients_file = os.path.join(data_dir, 'patients.csv')
    admissions_file = os.path.join(data_dir, 'admissions.csv')
    treatments_file = os.path.join(data_dir, 'treatments.csv')
    
    patients_df.to_csv(patients_file, index=False)
    admissions_df.to_csv(admissions_file, index=False)
    treatments_df.to_csv(treatments_file, index=False)
    
    print("\n✓ Data generation completed!")
    print(f"\nGenerated files:")
    print(f"  - {patients_file}: {len(patients_df):,} patients")
    print(f"  - {admissions_file}: {len(admissions_df):,} admissions")
    print(f"  - {treatments_file}: {len(treatments_df):,} treatments")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("Data Summary")
    print("=" * 60)
    print(f"Total patients: {len(patients_df):,}")
    print(f"Total admissions: {len(admissions_df):,}")
    print(f"Total treatments: {len(treatments_df):,}")
    print(f"Average treatments per admission: {len(treatments_df) / len(admissions_df):.2f}")
    print(f"Average length of stay: {admissions_df['length_of_stay'].mean():.2f} days")
    print(f"Total treatment cost: ${treatments_df['treatment_cost'].sum():,.2f}")
    
    return patients_df, admissions_df, treatments_df

if __name__ == "__main__":
    patients_df, admissions_df, treatments_df = main()
