# Employee Analytics & Workforce Insights

A fully functional OOP-based data analytics application that converts employee-management records into workforce and compensation insights.

## Features

- OOP model using `Person`, `Employee`, `Manager`, and `Developer`
- Encapsulation with private employee ID and salary attributes
- Inheritance and method overriding
- CRUD employee management
- CSV data persistence
- Data cleaning and duplicate detection with Pandas
- KPI calculation
- Department and job-role analysis
- Age and experience analysis
- Salary vs experience analysis
- SQLite database integration
- SQL analytics
- Matplotlib visualizations
- Excel report generation
- Automated professional PDF report generation
- Single `EmployeeAnalyticsApp` OOP wrapper for the whole workflow

## Project Structure

```text
Employee_Analytics_Project/
│
├── employee_analytics.py
├── requirements.txt
├── README.md
├── data/
│   ├── employees.csv
│   ├── cleaned_employees.csv
│   └── employees.db
├── sql/
│   └── analytics_queries.sql
├── reports/
│   ├── employee_analysis.xlsx
│   └── employee_analytics_report.pdf
└── visualizations/
    ├── department_analysis.png
    ├── salary_analysis.png
    └── workforce_analysis.png
```

## Installation

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate the environment again.

## Run

```powershell
python employee_analytics.py
```

On the first run, the application creates a sample employee dataset.

## Main Menu

1. Add Employee
2. Add Manager
3. Add Developer
4. Update Employee
5. Delete Employee
6. Display Employees
7. KPI Summary
8. Department Analysis
9. Job Role Analysis
10. Top 10 Highest-Paid Employees
11. Employees Above Average Salary
12. Run SQL Analytics
13. Generate Charts + Excel + PDF Report
14. Check Inheritance
15. Exit

## PDF Report

Choose option **13**. The application automatically:

1. Cleans the dataset.
2. Calculates workforce KPIs.
3. Creates department and salary charts.
4. Creates an Excel workbook.
5. Creates `reports/employee_analytics_report.pdf`.

The PDF contains an executive summary, KPI table, department analysis, visual analytics, and top-paid employee table.

## Analytics Covered

The project follows the supplied project specification:

- Employee count and department analysis
- Average and median salary
- Age and experience distribution
- Job-role and department distribution
- Salary vs experience
- Highest- and lowest-paid employees
- Department-wise salary and headcount
- Employees above overall average salary

## Resume Positioning
