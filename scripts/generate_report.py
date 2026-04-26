import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import json

DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'hospital.db')
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'output', 'hospital_report.html')

def generate_report():
    print("Generating comprehensive visual dashboard...")
    
    if not os.path.exists(DATABASE_PATH):
        print(f"Error: Database not found at {DATABASE_PATH}")
        return

    conn = sqlite3.connect(DATABASE_PATH)
    
    # Load data
    try:
        kpis = pd.read_sql_query("SELECT * FROM kpis", conn)
        admissions = pd.read_sql_query("SELECT * FROM admissions_cleaned", conn)
        treatments = pd.read_sql_query("SELECT * FROM treatments_cleaned", conn)
        patients = pd.read_sql_query("SELECT * FROM patients_cleaned", conn)
    except Exception as e:
        print(f"Error reading data: {e}")
        return
    finally:
        conn.close()

    # Convert KPIs to dict
    kpi_dict = dict(zip(kpis['metric'], kpis['value']))
    
    # Pre-process data
    admissions['admission_date'] = pd.to_datetime(admissions['admission_date'])
    treatments['treatment_date'] = pd.to_datetime(treatments['treatment_date'])
    
    # Generate Charts
    # 1. Recovery Rates by Department
    df_merged = treatments.merge(admissions, on='admission_id', how='left')
    
    def calc_recovery(group):
        recov = group['outcome'].isin(['Recovered', 'Improved']).sum()
        return (recov / len(group)) * 100 if len(group) > 0 else 0
        
    dept_recovery = df_merged.groupby('department_name').apply(calc_recovery).reset_index(name='Recovery Rate')
    dept_recovery = dept_recovery.sort_values('Recovery Rate', ascending=True)
    
    fig1 = px.bar(dept_recovery, x='Recovery Rate', y='department_name', orientation='h',
                  title='Recovery Rate by Department',
                  color='Recovery Rate', color_continuous_scale='Viridis')
    fig1.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       margin=dict(l=20, r=20, t=40, b=20), font=dict(family="Inter", color="#f8fafc"))
    fig1_html = fig1.to_html(full_html=False, include_plotlyjs=False)

    # 2. LOS Trends by Month
    los_trend = admissions.groupby(admissions['admission_date'].dt.to_period('M'))['length_of_stay'].mean().reset_index()
    los_trend['admission_date'] = los_trend['admission_date'].dt.to_timestamp()
    
    fig2 = px.line(los_trend, x='admission_date', y='length_of_stay', markers=True,
                   title='Average Length of Stay Trend', line_shape='spline')
    fig2.update_traces(line=dict(color='#8b5cf6', width=3), marker=dict(size=8, color='#3b82f6'))
    fig2.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       margin=dict(l=20, r=20, t=40, b=20), font=dict(family="Inter", color="#f8fafc"),
                       yaxis_title="Days", xaxis_title="Month")
    fig2_html = fig2.to_html(full_html=False, include_plotlyjs=False)

    # 3. Admission Volume over time
    vol_trend = admissions.groupby(admissions['admission_date'].dt.to_period('M')).size().reset_index(name='Admissions')
    vol_trend['admission_date'] = vol_trend['admission_date'].dt.to_timestamp()
    
    fig3 = px.area(vol_trend, x='admission_date', y='Admissions', title='Admission Volume (Monthly)',
                   color_discrete_sequence=['#10b981'])
    fig3.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       margin=dict(l=20, r=20, t=40, b=20), font=dict(family="Inter", color="#f8fafc"),
                       yaxis_title="Total Admissions", xaxis_title="Month")
    fig3_html = fig3.to_html(full_html=False, include_plotlyjs=False)

    # 4. Treatment Effectiveness vs Cost
    treatment_stats = treatments.groupby('treatment_type').agg(
        avg_eff=('effectiveness_score', 'mean'),
        avg_cost=('treatment_cost', 'mean'),
        count=('treatment_id', 'count')
    ).reset_index()
    
    fig4 = px.scatter(treatment_stats, x='avg_cost', y='avg_eff', size='count', color='treatment_type',
                      hover_name='treatment_type', title='Effectiveness vs Cost per Treatment',
                      labels={'avg_cost': 'Average Cost ($)', 'avg_eff': 'Effectiveness Score'})
    fig4.update_layout(template='plotly_dark', plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                       margin=dict(l=20, r=20, t=40, b=20), font=dict(family="Inter", color="#f8fafc"))
    fig4_html = fig4.to_html(full_html=False, include_plotlyjs=False)

    # Combine into HTML
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hospital Patient Insights Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-2.24.1.min.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-color: #0f172a;
                --card-bg: #1e293b;
                --text-main: #f8fafc;
                --text-muted: #94a3b8;
                --accent-1: #3b82f6;
                --accent-2: #8b5cf6;
                --accent-3: #10b981;
                --border-color: #334155;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Inter', sans-serif;
                background-color: var(--bg-color);
                color: var(--text-main);
                padding: 2rem;
                line-height: 1.6;
            }}
            header {{
                text-align: center;
                margin-bottom: 3rem;
                animation: fadeInDown 1s ease-out;
            }}
            h1 {{
                font-size: 3rem;
                font-weight: 700;
                background: linear-gradient(135deg, var(--accent-1), var(--accent-2));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }}
            .subtitle {{
                color: var(--text-muted);
                font-size: 1.2rem;
            }}
            .kpi-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 1.5rem;
                margin-bottom: 3rem;
                animation: fadeInUp 1s ease-out 0.2s both;
            }}
            .kpi-card {{
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 1.5rem;
                text-align: center;
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                position: relative;
                overflow: hidden;
            }}
            .kpi-card::before {{
                content: '';
                position: absolute;
                top: 0; left: 0; right: 0; height: 4px;
                background: linear-gradient(90deg, var(--accent-1), var(--accent-2));
                opacity: 0;
                transition: opacity 0.3s ease;
            }}
            .kpi-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 10px 15px rgba(0,0,0,0.2);
            }}
            .kpi-card:hover::before {{
                opacity: 1;
            }}
            .kpi-title {{
                color: var(--text-muted);
                font-size: 0.9rem;
                text-transform: uppercase;
                letter-spacing: 1px;
                margin-bottom: 0.5rem;
            }}
            .kpi-value {{
                font-size: 2.5rem;
                font-weight: 700;
                color: var(--text-main);
            }}
            .charts-container {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 2rem;
                animation: fadeInUp 1s ease-out 0.4s both;
            }}
            @media (max-width: 1024px) {{
                .charts-container {{
                    grid-template-columns: 1fr;
                }}
            }}
            .chart-card {{
                background: var(--card-bg);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 1rem;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: box-shadow 0.3s ease;
            }}
            .chart-card:hover {{
                box-shadow: 0 8px 24px rgba(0,0,0,0.3);
            }}
            @keyframes fadeInDown {{
                from {{ opacity: 0; transform: translateY(-20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes fadeInUp {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            .footer {{
                text-align: center;
                margin-top: 3rem;
                color: var(--text-muted);
                font-size: 0.9rem;
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>Hospital Performance Dashboard</h1>
            <p class="subtitle">Comprehensive Insights into Patient Admissions, Treatments, and Outcomes</p>
        </header>

        <div class="kpi-container">
            <div class="kpi-card">
                <div class="kpi-title">Total Patients</div>
                <div class="kpi-value">{{int(kpi_dict.get('Total Patients', 0)):,}}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Total Admissions</div>
                <div class="kpi-value">{{int(kpi_dict.get('Total Admissions', 0)):,}}</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Overall Recovery Rate</div>
                <div class="kpi-value" style="color: var(--accent-3)">{{kpi_dict.get('Overall Recovery Rate (%)', 0)}}%</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Avg Length of Stay</div>
                <div class="kpi-value">{{kpi_dict.get('Average Length of Stay (days)', 0)}}d</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-title">Readmission Rate</div>
                <div class="kpi-value">{{kpi_dict.get('Readmission Rate (%)', 0)}}%</div>
            </div>
        </div>

        <div class="charts-container">
            <div class="chart-card">
                {{fig3_html}}
            </div>
            <div class="chart-card">
                {{fig1_html}}
            </div>
            <div class="chart-card">
                {{fig2_html}}
            </div>
            <div class="chart-card">
                {{fig4_html}}
            </div>
        </div>
        
        <div class="footer">
            Generated automatically by hospital data analysis pipeline.
        </div>
    </body>
    </html>
    """

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html_template)
        
    print(f"Dashboard successfully generated at {OUTPUT_PATH}")

if __name__ == "__main__":
    generate_report()
