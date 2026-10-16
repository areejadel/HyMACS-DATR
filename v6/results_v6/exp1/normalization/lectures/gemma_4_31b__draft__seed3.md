# Lecture: Normalization and Database Schema Design (1NF to BCNF)

## Learning Objectives
By the end of this lecture, you will be able to:
1. **Identify** functional dependencies and candidate keys within a given relation.
2. **Detect** violations of 1NF, 2NF, 3NF, and BCNF in a database schema.
3. **Decompose** a non-normalized relation into a set of normalized relations to eliminate redundancy and anomalies.
4. **Evaluate** the trade-off between normalization (data integrity) and denormalization (query performance) for specific use cases.

---

## 0. Prerequisites and Intuition

### The Hook: The Cost of "Just Adding a Column"
Imagine you are designing a system for a global logistics company. You decide to store everything in one large `Shipments` table: `ShipmentID`, `CustomerName`, `CustomerAddress`, `WarehouseID`, and `WarehouseLocation`. It seems efficient—one query gets all the data. 

But then, a warehouse moves to a new city. To reflect this, you must update 10,000 shipment records. If the system crashes halfway through, your database now claims the same warehouse is in two different cities simultaneously. You haven't just encountered a bug; you've encountered a structural failure of the schema. This "data corruption by design" is exactly what normalization prevents.

### The Core Problem: Anomalies
Redundancy occurs when the same fact is stored in multiple rows. This creates three structural traps:

*   **Update Anomaly:** Changing a single fact (e.g., an instructor's office) requires updating every row where that fact appears. Partial updates lead to "schizophrenic" data.
*   **Insertion Anomaly:** You cannot record a fact about an entity (e.g., a new instructor's office) until that entity is linked to another entity (e.g., a student) because the primary key requires both.
*   **Deletion Anomaly:** Deleting a relationship (e.g., the last student in a course) accidentally wipes out a fundamental fact (e.g., the existence of the instructor and their office).

**Normalization** is the process of decomposing relations to ensure that every single fact is stored in exactly one place.

### The Tool: Functional Dependency (FD)
To normalize, we need a mathematical way to describe "what determines what."

**Intuition:** Think of a Functional Dependency as a **lookup function**. If $X \to Y$, then $X$ is the input and $Y$ is the output. If I give you a specific `StudentID`, the "function" of the database should return exactly one `StudentEmail`. If it could return two different emails for the same ID, the dependency is broken.

**Formal Definition:** A functional dependency $X \to Y$ exists in relation $R$ if, for every pair of tuples $t_1$ and $t_2$ in $R$, whenever $t_1[X] = t_2[X]$, then $t_1[Y] = t_2[Y]$.

### Key Terminology
*   **Candidate Key:** A minimal set of attributes that functionally determines all other attributes in the relation. (The "Unique Identifier").
*   **Prime Attribute:** An attribute that is a member of at least one candidate key.
*   **Non-prime Attribute:** An attribute that is not part of any candidate key.

---

## 1. First Normal Form (1NF): Atomicity

### The Tension: The "List" Temptation
It is tempting to store a list of values in a single cell (e.g., `Courses: "CS101, CS102, MATH201"`). While this looks clean to a human, it is a nightmare for a machine. How do you write a SQL query to find all students taking "CS101" without using slow, error-prone string searching (like `LIKE '%CS101%'`)?

### Formal Definition
A relation is in **1NF** if every attribute in every tuple contains only **atomic** (indivisible) values from its domain.

### Worked Example
**Scenario:** $\text{STUDENT\_COURSES}(\text{StudentID, CourseName})$

| StudentID | CourseName |
| :--- | :--- |
| 101 | {Physics, Calculus} |

**The Problem:** The $\text{CourseName}$ cell contains a set. This forces the application layer to parse strings rather than allowing the database engine to use its relational algebra.

**The Solution:** Decompose the multi-valued attribute into separate rows.

| StudentID | CourseName |
| :--- | :--- |
| 101 | Physics |
| 101 | Calculus |

**Try this yourself:** Consider a `User` table with a `PhoneNumbers` column containing multiple numbers separated by commas. How does this violate 1NF, and what happens if you need to update only one of those phone numbers?

---

## 2. Second Normal Form (2NF): No Partial Dependencies

### The Tension: The "Half-Key" Problem
Once we have 1NF, we often use **composite keys** (keys made of multiple columns). But what happens if a column only cares about *part* of that key? 

**Analogy:** Imagine a badge that grants access to a building. The badge ID is the key. If the badge also lists the "Building Color," the color depends on the building, not the specific badge. Storing the building color on every single badge is redundant.

### Formal Definition
A relation is in **2NF** if:
1. It is in 1NF.
2. Every non-prime attribute is **fully functionally dependent** on every candidate key.

A violation occurs if a non-prime attribute depends on a proper subset of a candidate key (a **Partial Dependency**).

### Worked Example
**Scenario:** $\text{TEACH}(\text{Student, Course, Instructor, InstructorOffice})$
*   **Candidate Key:** $\{\text{Student, Course}\}$
*   **Functional Dependencies:**
    1. $\{\text{Student, Course}\} \to \text{Instructor}$
    2. $\text{Instructor} \to \text{InstructorOffice}$

**The Problem:** $\text{InstructorOffice}$ is determined by $\text{Instructor}$. But $\text{Instructor}$ is only *part* of the logic that identifies the row. We don't need to know which $\text{Student}$ is in the class to know where the $\text{Instructor}$'s office is. This is a partial dependency.

**The Solution:** Split the table so that the "Office" fact lives only with the "Instructor" fact.
1. $R_1(\underline{\text{Instructor}}, \text{InstructorOffice})$
2. $R_2(\underline{\text{Student, Course}}, \text{Instructor})$

---

## 3. Third Normal Form (3NF): No Transitive Dependencies

### The Tension: The "Middleman" Dependency
Even if every column depends on the *whole* key, they might be depending on it through a "middleman." 

**Analogy:** Think of a chain of command. The CEO $\to$ Manager $\to$ Employee. If you store the Manager's phone number in the Employee's record, the phone number depends on the Employee *only because* the Employee depends on the Manager. If the employee quits, you lose the manager's phone number.

### Formal Definition
A relation is in **3NF** if:
1. It is in 2NF.
2. No non-prime attribute is **transitively dependent** on a candidate key.

**Formal Condition:** For every non-trivial FD $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.

### Worked Example
**Scenario:** $\text{EMPLOYEE}(\text{EmpID, DeptID, DeptName})$
*   **Candidate Key:** $\{\text{EmpID}\}$
*   **Functional Dependencies:**
    1. $\text{EmpID} \to \text{DeptID}$
    2. $\text{DeptID} \to \text{DeptName}$

**The Problem:** $\text{EmpID} \to \text{DeptID} \to \text{DeptName}$. The $\text{DeptName}$ is a "passenger" riding on $\text{DeptID}$. This creates a deletion anomaly: if you fire the only employee in "Research," the "Research" department itself vanishes from your database.

**The Solution:** Remove the middleman.
1. $R_1(\underline{\text{EmpID}}, \text{DeptID})$
2. $R_2(\underline{\text{DeptID}}, \text{DeptName})$

---

## 4. Boyce-Codd Normal Form (BCNF): The Strictest Standard

### The Tension: The "Prime" Loophole
3NF has a loophole: it allows a dependency if the dependent attribute is "prime" (part of a key). This is rare, but it allows redundancy to sneak back in when you have overlapping candidate keys. BCNF closes this loophole.

### Formal Definition
A relation is in **BCNF** if, for every non-trivial functional dependency $X \to A$, $X$ is a superkey. 
*Simplified: "Every determinant must be a candidate key."*

### Worked Example
**Scenario:** $\text{TEACH}(\text{Student, Course, Instructor})$
*   **Constraints:** Each instructor teaches only one course; multiple instructors may teach the same course.
*   **Functional Dependencies:**
    1. $\{\text{Student, Course}\} \to \text{Instructor}$
    2. $\text{Instructor} \to \text{Course}$
*   **Candidate Keys:** $\{\text{Student, Course}\}$ and $\{\text{Student, Instructor}\}$

**Analysis:**
*   **3NF Check:** It *is* in 3NF. In $\text{Instructor} \to \text{Course}$, $\text{Course}$ is a prime attribute. 3NF says "That's fine."
*   **BCNF Check:** It is **not** in BCNF. In $\text{Instructor} \to \text{Course}$, the determinant ($\text{Instructor}$) is **not** a superkey (it can't tell us which student is in the class).

**The Solution:** Decompose to ensure the determinant is the key.
1. $R_1(\underline{\text{Instructor}}, \text{Course})$
2. $R_2(\underline{\text{Student, Instructor}})$

**Try this yourself:** Look at the BCNF solution. If we add a new instructor who hasn't been assigned any students yet, can we do it now? Could we do it in the original table?

---

## 5. Practical Application and Trade-offs

**The Normalization Paradox:** As you move from 1NF $\to$ BCNF, you increase **Data Integrity** (no anomalies) but you increase **Join Complexity**. 

To retrieve a student's instructor's office in a BCNF schema, you might need to join three tables. In a non-normalized table, it's one row. In high-read environments (like a product catalog), engineers often **denormalize**—intentionally introducing redundancy to trade write-integrity for read-speed. 

**Rule of Thumb:** Normalize for the "Source of Truth" (OLTP); denormalize for the "Analysis/View" (OLAP).