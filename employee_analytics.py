import os
import sqlite3
from datetime import datetime
from typing import List, Optional

import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak
)


# ============================================================
# OOP MODEL
# ============================================================

class Person:
    """Base class for common person information."""

    def __init__(self, name: str = "", age: int = 0):
        self.name = name
        self.age = age

    def display(self):
        print("\nPerson Details")
        print("Name:", self.name)
        print("Age:", self.age)


class Employee(Person):
    """Base employee class with encapsulated employee data."""

    employee_count = 0

    def __init__(
        self,
        name: str = "",
        age: int = 0,
        employee_id: str = "",
        salary: float = 0,
        department: str = "General",
        experience: int = 0,
        job_role: str = "Employee",
    ):
        super().__init__(name, age)
        self.__employee_id = employee_id
        self.__salary = float(salary)
        self.department = department
        self.experience = int(experience)
        self.job_role = job_role
        Employee.employee_count += 1

    def __del__(self):
        # Avoid noisy output during interpreter shutdown.
        pass

    def get_employee_id(self):
        return self.__employee_id

    def get_salary(self):
        return self.__salary

    def set_employee_id(self, employee_id):
        self.__employee_id = employee_id

    def set_salary(self, salary):
        self.__salary = float(salary)

    def to_dict(self):
        return {
            "employee_id": self.get_employee_id(),
            "name": self.name,
            "age": self.age,
            "department": self.department,
            "salary": self.get_salary(),
            "experience": self.experience,
            "job_role": self.job_role,
        }

    def display(self):
        super().display()
        print("Employee ID:", self.__employee_id)
        print("Salary:", self.__salary)
        print("Department:", self.department)
        print("Experience:", self.experience, "years")
        print("Job Role:", self.job_role)


class Manager(Employee):
    """Manager specialization demonstrating inheritance."""

    def __init__(self, name, age, employee_id, salary, department, experience=0):
        super().__init__(
            name, age, employee_id, salary,
            department, experience, "Manager"
        )

    def display(self):
        super().display()
        print("Employee Type: Manager")


class Developer(Employee):
    """Developer specialization demonstrating inheritance."""

    def __init__(
        self, name, age, employee_id, salary,
        department, language, experience=0
    ):
        super().__init__(
            name, age, employee_id, salary,
            department, experience, "Developer"
        )
        self.language = language

    def to_dict(self):
        data = super().to_dict()
        data["programming_language"] = self.language
        return data

    def display(self):
        super().display()
        print("Programming Language:", self.language)


# ============================================================
# DATA / DATABASE LAYER
# ============================================================

class EmployeeDataManager:
    """Handles CSV persistence and SQLite database operations."""

    COLUMNS = [
        "employee_id", "name", "age", "department",
        "salary", "experience", "job_role"
    ]

    def __init__(self, data_dir="data", db_name="employees.db"):
        self.data_dir = data_dir
        self.csv_path = os.path.join(data_dir, "employees.csv")
        self.cleaned_csv_path = os.path.join(data_dir, "cleaned_employees.csv")
        self.db_path = os.path.join(data_dir, db_name)
        os.makedirs(self.data_dir, exist_ok=True)

    def employees_to_dataframe(self, employees: List[Employee]) -> pd.DataFrame:
        rows = [emp.to_dict() for emp in employees]
        return pd.DataFrame(rows, columns=self.COLUMNS)

    def save_csv(self, employees: List[Employee], path=None):
        path = path or self.csv_path
        df = self.employees_to_dataframe(employees)
        df.to_csv(path, index=False)
        return path

    def load_csv(self, path=None) -> pd.DataFrame:
        path = path or self.csv_path
        if not os.path.exists(path):
            return pd.DataFrame(columns=self.COLUMNS)
        return pd.read_csv(path)

    def clean_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        cleaned = df.copy()

        for col in self.COLUMNS:
            if col not in cleaned.columns:
                cleaned[col] = None

        cleaned = cleaned[self.COLUMNS]
        cleaned["employee_id"] = cleaned["employee_id"].astype(str).str.strip()
        cleaned["name"] = cleaned["name"].astype(str).str.strip()
        cleaned["department"] = cleaned["department"].astype(str).str.strip()
        cleaned["job_role"] = cleaned["job_role"].astype(str).str.strip()

        for col in ["age", "salary", "experience"]:
            cleaned[col] = pd.to_numeric(cleaned[col], errors="coerce")

        cleaned = cleaned.drop_duplicates(subset=["employee_id"])
        cleaned = cleaned.dropna(subset=["employee_id", "name"])
        cleaned["age"] = cleaned["age"].fillna(cleaned["age"].median() if not cleaned["age"].dropna().empty else 0)
        cleaned["salary"] = cleaned["salary"].fillna(cleaned["salary"].median() if not cleaned["salary"].dropna().empty else 0)
        cleaned["experience"] = cleaned["experience"].fillna(0)

        cleaned["age"] = cleaned["age"].clip(lower=0)
        cleaned["salary"] = cleaned["salary"].clip(lower=0)
        cleaned["experience"] = cleaned["experience"].clip(lower=0)

        cleaned["age"] = cleaned["age"].astype(int)
        cleaned["experience"] = cleaned["experience"].astype(int)

        cleaned.to_csv(self.cleaned_csv_path, index=False)
        return cleaned

    def initialize_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                department TEXT,
                salary REAL,
                experience INTEGER,
                job_role TEXT
            )
        """)
        conn.commit()
        conn.close()

    def load_dataframe_to_database(self, df: pd.DataFrame):
        self.initialize_database()
        conn = sqlite3.connect(self.db_path)

        df[self.COLUMNS].to_sql(
            "employees", conn, if_exists="replace", index=False
        )

        conn.close()

    def run_query(self, query: str) -> pd.DataFrame:
        self.initialize_database()
        conn = sqlite3.connect(self.db_path)
        try:
            return pd.read_sql_query(query, conn)
        finally:
            conn.close()


# ============================================================
# ANALYTICS LAYER
# ============================================================

class EmployeeAnalytics:
    """
    OOP wrapper around the complete analytics workflow.

    This class provides one interface for:
    - data cleaning
    - KPIs
    - EDA
    - SQL analytics
    - charts
    - Excel export
    - PDF reporting
    """

    def __init__(self, data_manager: EmployeeDataManager):
        self.data_manager = data_manager
        self.df = pd.DataFrame(columns=EmployeeDataManager.COLUMNS)
        self.visualization_dir = "visualizations"
        self.report_dir = "reports"
        os.makedirs(self.visualization_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)

    def load_and_prepare_data(self):
        self.df = self.data_manager.load_csv()
        self.df = self.data_manager.clean_dataframe(self.df)
        self.data_manager.load_dataframe_to_database(self.df)
        return self.df

    def set_dataframe(self, df: pd.DataFrame):
        self.df = self.data_manager.clean_dataframe(df)
        self.data_manager.load_dataframe_to_database(self.df)

    def kpis(self):
        if self.df.empty:
            return {
                "Total Employees": 0,
                "Average Salary": 0,
                "Median Salary": 0,
                "Number of Departments": 0,
                "Average Experience": 0,
            }

        return {
            "Total Employees": int(len(self.df)),
            "Average Salary": float(self.df["salary"].mean()),
            "Median Salary": float(self.df["salary"].median()),
            "Number of Departments": int(self.df["department"].nunique()),
            "Average Experience": float(self.df["experience"].mean()),
        }

    def department_analysis(self):
        return (
            self.df.groupby("department", dropna=False)
            .agg(
                employee_count=("employee_id", "count"),
                average_salary=("salary", "mean"),
                average_experience=("experience", "mean"),
            )
            .reset_index()
            .sort_values("average_salary", ascending=False)
        )

    def role_analysis(self):
        return (
            self.df.groupby("job_role", dropna=False)
            .agg(
                employee_count=("employee_id", "count"),
                average_salary=("salary", "mean"),
                average_experience=("experience", "mean"),
            )
            .reset_index()
            .sort_values("average_salary", ascending=False)
        )

    def age_distribution(self):
        result = self.df.copy()
        result["age_group"] = pd.cut(
            result["age"],
            bins=[0, 25, 35, 45, 55, 100],
            labels=["18-25", "26-35", "36-45", "46-55", "56+"],
            include_lowest=True,
        )
        return result.groupby("age_group", observed=False).size().reset_index(name="employee_count")

    def salary_vs_experience(self):
        return self.df[["employee_id", "salary", "experience", "department", "job_role"]].sort_values(
            "experience"
        )

    def highest_paid(self, n=10):
        return self.df.nlargest(n, "salary")

    def lowest_paid(self, n=10):
        return self.df.nsmallest(n, "salary")

    def above_average_salary(self):
        if self.df.empty:
            return self.df.copy()
        avg = self.df["salary"].mean()
        return self.df[self.df["salary"] > avg].sort_values("salary", ascending=False)

    def summary_text(self):
        if self.df.empty:
            return "No employee data is available."

        kpi = self.kpis()
        dept = self.department_analysis()
        top_department = dept.iloc[0]["department"] if not dept.empty else "N/A"
        top_salary = self.df.loc[self.df["salary"].idxmax(), "name"]
        return (
            f"The dataset contains {kpi['Total Employees']} employees across "
            f"{kpi['Number of Departments']} departments. Average salary is "
            f"{kpi['Average Salary']:,.2f}, median salary is "
            f"{kpi['Median Salary']:,.2f}, and average experience is "
            f"{kpi['Average Experience']:.2f} years. "
            f"The highest average-salary department is {top_department}, "
            f"while the highest-paid employee is {top_salary}."
        )

    # -------------------- SQL analytics --------------------

    def sql_department_summary(self):
        return self.data_manager.run_query("""
            SELECT
                department,
                COUNT(*) AS employee_count,
                ROUND(AVG(salary), 2) AS average_salary
            FROM employees
            GROUP BY department
            ORDER BY average_salary DESC
        """)

    def sql_top_10_highest_paid(self):
        return self.data_manager.run_query("""
            SELECT employee_id, name, department, job_role, salary
            FROM employees
            ORDER BY salary DESC
            LIMIT 10
        """)

    def sql_average_salary_by_role(self):
        return self.data_manager.run_query("""
            SELECT
                job_role,
                COUNT(*) AS employee_count,
                ROUND(AVG(salary), 2) AS average_salary
            FROM employees
            GROUP BY job_role
            ORDER BY average_salary DESC
        """)

    def sql_average_experience_by_department(self):
        return self.data_manager.run_query("""
            SELECT
                department,
                ROUND(AVG(experience), 2) AS average_experience
            FROM employees
            GROUP BY department
            ORDER BY average_experience DESC
        """)

    def sql_employees_above_average(self):
        return self.data_manager.run_query("""
            SELECT employee_id, name, department, salary
            FROM employees
            WHERE salary > (SELECT AVG(salary) FROM employees)
            ORDER BY salary DESC
        """)

    # -------------------- visualization --------------------

    def create_visualizations(self):
        if self.df.empty:
            return []

        paths = []

        plt.figure(figsize=(9, 5))
        dept_counts = self.df["department"].value_counts()
        dept_counts.plot(kind="bar")
        plt.title("Employees by Department")
        plt.xlabel("Department")
        plt.ylabel("Employee Count")
        plt.tight_layout()
        p = os.path.join(self.visualization_dir, "department_analysis.png")
        plt.savefig(p, dpi=160)
        plt.close()
        paths.append(p)

        plt.figure(figsize=(9, 5))
        self.df.groupby("department")["salary"].mean().sort_values(ascending=False).plot(kind="bar")
        plt.title("Average Salary by Department")
        plt.xlabel("Department")
        plt.ylabel("Average Salary")
        plt.tight_layout()
        p = os.path.join(self.visualization_dir, "salary_analysis.png")
        plt.savefig(p, dpi=160)
        plt.close()
        paths.append(p)

        plt.figure(figsize=(9, 5))
        plt.scatter(self.df["experience"], self.df["salary"])
        plt.title("Salary vs Experience")
        plt.xlabel("Experience (Years)")
        plt.ylabel("Salary")
        plt.tight_layout()
        p = os.path.join(self.visualization_dir, "workforce_analysis.png")
        plt.savefig(p, dpi=160)
        plt.close()
        paths.append(p)

        return paths

    def export_excel(self, path="reports/employee_analysis.xlsx"):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            self.df.to_excel(writer, sheet_name="Cleaned Data", index=False)
            self.department_analysis().to_excel(writer, sheet_name="Department Analysis", index=False)
            self.role_analysis().to_excel(writer, sheet_name="Role Analysis", index=False)
            self.age_distribution().to_excel(writer, sheet_name="Age Distribution", index=False)
            self.highest_paid().to_excel(writer, sheet_name="Top Paid", index=False)
            pd.DataFrame([self.kpis()]).T.rename(columns={0: "Value"}).to_excel(
                writer, sheet_name="KPIs"
            )

        return path


# ============================================================
# PDF REPORT LAYER
# ============================================================

class PDFReportGenerator:
    """Creates a professional PDF analytics report with KPIs, tables and charts."""

    def __init__(self, analytics: EmployeeAnalytics):
        self.analytics = analytics
        self.styles = getSampleStyleSheet()

        self.title_style = ParagraphStyle(
            "ReportTitle",
            parent=self.styles["Title"],
            alignment=TA_CENTER,
            fontSize=20,
            leading=24,
            spaceAfter=14,
        )

        self.heading_style = ParagraphStyle(
            "ReportHeading",
            parent=self.styles["Heading2"],
            fontSize=14,
            leading=18,
            spaceBefore=10,
            spaceAfter=8,
        )

    @staticmethod
    def _table(data, widths=None):
        table = Table(data, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24527A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#EEF3F7")]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
        ]))
        return table

    def generate(self, path="reports/employee_analytics_report.pdf"):
        os.makedirs(os.path.dirname(path), exist_ok=True)

        if self.analytics.df.empty:
            raise ValueError("Cannot create a report because the dataset is empty.")

        chart_paths = self.analytics.create_visualizations()
        kpis = self.analytics.kpis()
        dept = self.analytics.department_analysis()
        top_paid = self.analytics.highest_paid(10)

        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        story = []
        story.append(Paragraph("Employee Analytics & Workforce Insights", self.title_style))
        story.append(Paragraph(
            "Data Analytics Report — Python • Pandas • SQL • Excel • OOP",
            self.styles["Normal"]
        ))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Executive Summary", self.heading_style))
        story.append(Paragraph(self.analytics.summary_text(), self.styles["BodyText"]))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Key Performance Indicators", self.heading_style))
        kpi_rows = [["KPI", "Value"]]
        for key, value in kpis.items():
            if "Salary" in key:
                formatted = f"{value:,.2f}"
            elif "Experience" in key:
                formatted = f"{value:.2f} years"
            else:
                formatted = f"{value:,}"
            kpi_rows.append([key, formatted])
        story.append(self._table(kpi_rows, widths=[3.3 * inch, 2.3 * inch]))

        story.append(Paragraph("Department Analysis", self.heading_style))
        dept_rows = [["Department", "Employees", "Avg Salary", "Avg Experience"]]
        for _, row in dept.iterrows():
            dept_rows.append([
                str(row["department"]),
                str(int(row["employee_count"])),
                f"{row['average_salary']:,.2f}",
                f"{row['average_experience']:.2f}",
            ])
        story.append(self._table(dept_rows, widths=[1.6*inch, 1.0*inch, 1.4*inch, 1.4*inch]))

        story.append(PageBreak())
        story.append(Paragraph("Visual Analytics", self.heading_style))

        for chart in chart_paths:
            if os.path.exists(chart):
                story.append(Image(chart, width=6.6*inch, height=3.65*inch))
                story.append(Spacer(1, 8))

        story.append(PageBreak())
        story.append(Paragraph("Top 10 Highest-Paid Employees", self.heading_style))

        top_rows = [["Employee ID", "Name", "Department", "Role", "Salary"]]
        for _, row in top_paid.iterrows():
            top_rows.append([
                str(row["employee_id"]),
                str(row["name"]),
                str(row["department"]),
                str(row["job_role"]),
                f"{row['salary']:,.2f}",
            ])
        story.append(self._table(
            top_rows,
            widths=[0.85*inch, 1.25*inch, 1.2*inch, 1.3*inch, 1.2*inch]
        ))

        story.append(Spacer(1, 14))
        story.append(Paragraph(
            "Generated automatically by the OOP Employee Analytics application on "
            + datetime.now().strftime("%d-%m-%Y %H:%M"),
            self.styles["Normal"]
        ))

        doc.build(story)
        return path


# ============================================================
# APPLICATION / OOP WRAPPER
# ============================================================

class EmployeeAnalyticsApp:
    """Complete application wrapper combining CRUD + analytics + reporting."""

    def __init__(self):
        self.data_manager = EmployeeDataManager()
        self.analytics = EmployeeAnalytics(self.data_manager)
        self.pdf = PDFReportGenerator(self.analytics)
        self.employees: List[Employee] = []

    # -------------------- CRUD --------------------

    def _employee_exists(self, employee_id):
        return any(emp.get_employee_id() == employee_id for emp in self.employees)

    def add_employee(self):
        print("\n--- Add Employee ---")
        emp_id = input("Enter Employee ID: ").strip()

        if self._employee_exists(emp_id):
            print("Employee ID already exists.")
            return

        name = input("Enter Name: ").strip()
        age = self._get_int("Enter Age: ", 0)
        salary = self._get_float("Enter Salary: ", 0)
        department = input("Enter Department: ").strip() or "General"
        experience = self._get_int("Enter Experience (years): ", 0)
        role = input("Enter Job Role: ").strip() or "Employee"

        self.employees.append(
            Employee(name, age, emp_id, salary, department, experience, role)
        )
        self.save()
        print("Employee added successfully.")

    def add_manager(self):
        print("\n--- Add Manager ---")
        emp_id = input("Enter Employee ID: ").strip()
        if self._employee_exists(emp_id):
            print("Employee ID already exists.")
            return

        name = input("Enter Name: ").strip()
        age = self._get_int("Enter Age: ", 0)
        salary = self._get_float("Enter Salary: ", 0)
        department = input("Enter Department: ").strip() or "Management"
        experience = self._get_int("Enter Experience (years): ", 0)

        self.employees.append(
            Manager(name, age, emp_id, salary, department, experience)
        )
        self.save()
        print("Manager added successfully.")

    def add_developer(self):
        print("\n--- Add Developer ---")
        emp_id = input("Enter Employee ID: ").strip()
        if self._employee_exists(emp_id):
            print("Employee ID already exists.")
            return

        name = input("Enter Name: ").strip()
        age = self._get_int("Enter Age: ", 0)
        salary = self._get_float("Enter Salary: ", 0)
        department = input("Enter Department: ").strip() or "IT"
        experience = self._get_int("Enter Experience (years): ", 0)
        language = input("Enter Programming Language: ").strip() or "Python"

        self.employees.append(
            Developer(
                name, age, emp_id, salary,
                department, language, experience
            )
        )
        self.save()
        print("Developer added successfully.")

    def update_employee(self):
        emp_id = input("Enter Employee ID to update: ").strip()

        for emp in self.employees:
            if emp.get_employee_id() == emp_id:
                print("Press Enter to keep the current value.")

                name = input(f"Name [{emp.name}]: ").strip()
                age = input(f"Age [{emp.age}]: ").strip()
                salary = input(f"Salary [{emp.get_salary()}]: ").strip()
                department = input(f"Department [{emp.department}]: ").strip()
                experience = input(f"Experience [{emp.experience}]: ").strip()
                role = input(f"Job Role [{emp.job_role}]: ").strip()

                if name:
                    emp.name = name
                if age:
                    emp.age = int(age)
                if salary:
                    emp.set_salary(float(salary))
                if department:
                    emp.department = department
                if experience:
                    emp.experience = int(experience)
                if role:
                    emp.job_role = role

                self.save()
                print("Employee updated successfully.")
                return

        print("Employee not found.")

    def delete_employee(self):
        emp_id = input("Enter Employee ID to delete: ").strip()

        for emp in self.employees:
            if emp.get_employee_id() == emp_id:
                self.employees.remove(emp)
                self.save()
                print("Employee deleted successfully.")
                return

        print("Employee not found.")

    def display_employees(self):
        if not self.employees:
            print("No employees found.")
            return

        for emp in self.employees:
            print("-" * 45)
            emp.display()

    # -------------------- persistence --------------------

    def save(self):
        self.data_manager.save_csv(self.employees)
        df = self.data_manager.clean_dataframe(
            self.data_manager.employees_to_dataframe(self.employees)
        )
        self.analytics.set_dataframe(df)

    def load(self):
        df = self.data_manager.load_csv()
        if df.empty:
            return

        self.analytics.set_dataframe(df)
        self.employees = []

        for _, row in self.analytics.df.iterrows():
            role = str(row["job_role"]).lower()

            if role == "manager":
                emp = Manager(
                    row["name"], int(row["age"]), row["employee_id"],
                    float(row["salary"]), row["department"],
                    int(row["experience"])
                )
            else:
                emp = Employee(
                    row["name"], int(row["age"]), row["employee_id"],
                    float(row["salary"]), row["department"],
                    int(row["experience"]), row["job_role"]
                )

            self.employees.append(emp)

    # -------------------- analytics menu --------------------

    def show_kpis(self):
        print("\n========== KPI SUMMARY ==========")
        for key, value in self.analytics.kpis().items():
            if "Salary" in key:
                print(f"{key}: {value:,.2f}")
            elif "Experience" in key:
                print(f"{key}: {value:.2f} years")
            else:
                print(f"{key}: {value:,}")

    def show_department_analysis(self):
        print("\n========== DEPARTMENT ANALYSIS ==========")
        print(self.analytics.department_analysis().to_string(index=False))

    def show_role_analysis(self):
        print("\n========== JOB ROLE ANALYSIS ==========")
        print(self.analytics.role_analysis().to_string(index=False))

    def show_top_paid(self):
        print("\n========== TOP 10 HIGHEST PAID ==========")
        print(self.analytics.highest_paid().to_string(index=False))

    def show_above_average(self):
        print("\n========== ABOVE AVERAGE SALARY ==========")
        print(self.analytics.above_average_salary().to_string(index=False))

    def run_sql_analytics(self):
        print("\n========== SQL DEPARTMENT SUMMARY ==========")
        print(self.analytics.sql_department_summary().to_string(index=False))

        print("\n========== SQL TOP 10 HIGHEST PAID ==========")
        print(self.analytics.sql_top_10_highest_paid().to_string(index=False))

        print("\n========== SQL AVERAGE SALARY BY ROLE ==========")
        print(self.analytics.sql_average_salary_by_role().to_string(index=False))

        print("\n========== SQL AVERAGE EXPERIENCE BY DEPARTMENT ==========")
        print(self.analytics.sql_average_experience_by_department().to_string(index=False))

        print("\n========== SQL EMPLOYEES ABOVE AVERAGE ==========")
        print(self.analytics.sql_employees_above_average().to_string(index=False))

    def generate_reports(self):
        if self.analytics.df.empty:
            print("No data available for reporting.")
            return

        charts = self.analytics.create_visualizations()
        excel = self.analytics.export_excel()
        pdf = self.pdf.generate()

        print("\nReports generated successfully:")
        print("PDF:", pdf)
        print("Excel:", excel)
        print("Charts:")
        for chart in charts:
            print(" -", chart)

    def show_subclass_check(self):
        print("Manager subclass of Employee:", issubclass(Manager, Employee))
        print("Developer subclass of Employee:", issubclass(Developer, Employee))

    # -------------------- utilities --------------------

    @staticmethod
    def _get_int(prompt, minimum=0):
        while True:
            try:
                value = int(input(prompt))
                if value < minimum:
                    raise ValueError
                return value
            except ValueError:
                print(f"Enter a valid integer >= {minimum}.")

    @staticmethod
    def _get_float(prompt, minimum=0):
        while True:
            try:
                value = float(input(prompt))
                if value < minimum:
                    raise ValueError
                return value
            except ValueError:
                print(f"Enter a valid number >= {minimum}.")

    def menu(self):
        self.load()

        while True:
            print("\n" + "=" * 60)
            print(" EMPLOYEE ANALYTICS & WORKFORCE INSIGHTS SYSTEM")
            print("=" * 60)
            print("1. Add Employee")
            print("2. Add Manager")
            print("3. Add Developer")
            print("4. Update Employee")
            print("5. Delete Employee")
            print("6. Display Employees")
            print("7. KPI Summary")
            print("8. Department Analysis")
            print("9. Job Role Analysis")
            print("10. Top 10 Highest-Paid Employees")
            print("11. Employees Above Average Salary")
            print("12. Run SQL Analytics")
            print("13. Generate Charts + Excel + PDF Report")
            print("14. Check Inheritance")
            print("15. Exit")

            choice = input("\nEnter your choice: ").strip()

            try:
                if choice == "1":
                    self.add_employee()
                elif choice == "2":
                    self.add_manager()
                elif choice == "3":
                    self.add_developer()
                elif choice == "4":
                    self.update_employee()
                elif choice == "5":
                    self.delete_employee()
                elif choice == "6":
                    self.display_employees()
                elif choice == "7":
                    self.show_kpis()
                elif choice == "8":
                    self.show_department_analysis()
                elif choice == "9":
                    self.show_role_analysis()
                elif choice == "10":
                    self.show_top_paid()
                elif choice == "11":
                    self.show_above_average()
                elif choice == "12":
                    self.run_sql_analytics()
                elif choice == "13":
                    self.generate_reports()
                elif choice == "14":
                    self.show_subclass_check()
                elif choice == "15":
                    print("Exiting Program...")
                    break
                else:
                    print("Invalid choice. Please select 1-15.")
            except Exception as exc:
                print("Operation failed:", exc)


def create_sample_dataset():
    """Creates the initial sample dataset from the project specification."""
    manager = EmployeeDataManager()
    if os.path.exists(manager.csv_path):
        return

    sample = pd.DataFrame([
        ["EMP001", "Alice", 28, "HR", 45000, 3, "HR Executive"],
        ["EMP002", "Rahul", 32, "IT", 72000, 6, "Developer"],
        ["EMP003", "Priya", 26, "Finance", 52000, 2, "Analyst"],
        ["EMP004", "Arjun", 35, "IT", 85000, 9, "Senior Developer"],
        ["EMP005", "Neha", 30, "Marketing", 58000, 5, "Marketing Executive"],
        ["EMP006", "Karan", 41, "Finance", 92000, 14, "Finance Manager"],
        ["EMP007", "Meera", 29, "HR", 49000, 4, "Recruiter"],
        ["EMP008", "Dev", 38, "IT", 98000, 12, "Tech Lead"],
        ["EMP009", "Riya", 25, "Marketing", 50000, 2, "Content Analyst"],
        ["EMP010", "Vikram", 45, "Management", 110000, 18, "Manager"],
    ], columns=EmployeeDataManager.COLUMNS)

    manager.save_csv(
        [Employee(
            row["name"], int(row["age"]), row["employee_id"],
            float(row["salary"]), row["department"],
            int(row["experience"]), row["job_role"]
        ) for _, row in sample.iterrows()]
    )


if __name__ == "__main__":
    create_sample_dataset()
    app = EmployeeAnalyticsApp()
    app.menu()
