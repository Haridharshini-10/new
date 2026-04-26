-- Hospital Patient Insights Database Schema
-- SQLite version

-- Departments table
CREATE TABLE IF NOT EXISTS departments (
    department_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    bed_count INTEGER NOT NULL,
    staff_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Patients table
CREATE TABLE IF NOT EXISTS patients (
    patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth DATE NOT NULL,
    gender TEXT NOT NULL,
    contact_number TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admissions table
CREATE TABLE IF NOT EXISTS admissions (
    admission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    department_id INTEGER NOT NULL,
    admission_date DATE NOT NULL,
    discharge_date DATE,
    admission_reason TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
    FOREIGN KEY (department_id) REFERENCES departments(department_id)
);

-- Treatments table
CREATE TABLE IF NOT EXISTS treatments (
    treatment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    admission_id INTEGER NOT NULL,
    treatment_type TEXT NOT NULL,
    treatment_date DATE NOT NULL,
    treatment_cost DECIMAL(10, 2) NOT NULL,
    outcome TEXT NOT NULL,
    effectiveness_score DECIMAL(3, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admission_id) REFERENCES admissions(admission_id)
);

-- Treatment effectiveness lookup
CREATE TABLE IF NOT EXISTS treatment_effectiveness (
    treatment_type TEXT PRIMARY KEY,
    recovery_rate DECIMAL(5, 2),
    average_duration_days INTEGER,
    success_count INTEGER,
    total_count INTEGER
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_patients_dob ON patients(date_of_birth);
CREATE INDEX IF NOT EXISTS idx_admissions_patient ON admissions(patient_id);
CREATE INDEX IF NOT EXISTS idx_admissions_department ON admissions(department_id);
CREATE INDEX IF NOT EXISTS idx_admissions_date ON admissions(admission_date);
CREATE INDEX IF NOT EXISTS idx_treatments_admission ON treatments(admission_id);
CREATE INDEX IF NOT EXISTS idx_treatments_date ON treatments(treatment_date);

-- Insert sample departments
INSERT OR IGNORE INTO departments (name, bed_count, staff_count) VALUES
('Cardiology', 25, 12),
('Orthopedics', 30, 15),
('Neurology', 20, 10),
('General Medicine', 50, 25),
('Emergency', 40, 20),
('Pediatrics', 35, 18),
('ICU', 15, 20),
('Surgery', 20, 12);

-- Insert sample treatment effectiveness data
INSERT OR IGNORE INTO treatment_effectiveness (treatment_type, recovery_rate, average_duration_days, success_count, total_count) VALUES
('Medication', 78.5, 5, 157, 200),
('Surgery', 85.0, 10, 170, 200),
('Physical Therapy', 82.3, 14, 165, 200),
('Chemotherapy', 72.5, 21, 145, 200),
('Radiation', 75.8, 30, 152, 200),
('Cardiac Intervention', 88.5, 3, 177, 200),
('Joint Replacement', 90.2, 7, 181, 200),
('Conservative Treatment', 70.0, 8, 140, 200);
