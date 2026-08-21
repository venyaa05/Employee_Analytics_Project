-- Employee Analytics SQL Queries

CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER,
    department TEXT,
    salary REAL,
    experience INTEGER,
    job_role TEXT
);

-- Department-wise employee count and average salary
SELECT
    department,
    COUNT(*) AS employee_count,
    AVG(salary) AS average_salary
FROM employees
GROUP BY department
ORDER BY average_salary DESC;

-- Top 10 highest-paid employees
SELECT employee_id, name, department, job_role, salary
FROM employees
ORDER BY salary DESC
LIMIT 10;

-- Average salary by job role
SELECT
    job_role,
    COUNT(*) AS employee_count,
    AVG(salary) AS average_salary
FROM employees
GROUP BY job_role
ORDER BY average_salary DESC;

-- Average experience by department
SELECT
    department,
    AVG(experience) AS average_experience
FROM employees
GROUP BY department
ORDER BY average_experience DESC;

-- Employees above overall average salary
SELECT employee_id, name, department, salary
FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees)
ORDER BY salary DESC;
