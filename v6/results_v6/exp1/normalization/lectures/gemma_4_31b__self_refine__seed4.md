# Lecture: Normalization Forms and Database Schema Design (1NF–BCNF)

## The "Single Source of Truth" Paradox
Imagine you are designing a database for a global airline. A passenger changes their phone number. In a poorly designed system, that number might be stored in the `Bookings` table, the `FrequentFlyer` table, and the `EmergencyContact` table. If you update it in two places but miss the third, you have created a "schism" in your data. Which one is the truth? 

This is the fundamental problem of **Data Redundancy**. Normalization is not about making tables "neat"; it is a rigorous mathematical process to ensure that every single fact is stored in exactly one place. If a fact is stored twice, you don't have two copies of the data—you have two opportunities for the data to disagree.

## Learning Objectives
By the end of this lecture, you will be able to:
1. **Analyze** a set of attributes to identify Functional Dependencies (FDs) and determine Candidate Keys.
2. **Detect** insertion, update, and deletion anomalies in unnormalized tables and explain their causes.
3. **Apply** the rules of 1NF, 2NF, 3NF, and BCNF to decompose a "fat" table into a normalized schema.
4. **Evaluate** the trade-off between normalization (integrity) and denormalization (performance) for OLTP versus OLAP use cases.

---

## 1. Prerequisites: Functional Dependencies and Keys
Before normalizing, we must define the constraints that govern how data attributes relate to one another.

### The Deterministic Function
A functional dependency mirrors a programming function: `getEmail(employeeID)`. If the input `employeeID` "101" always maps to "alice@company.com", then the ID determines the email. In database theory, this is a **Functional Dependency**.

**Analogy:** Think of an FD as a "lookup key." If I give you a Social Security Number, you can find exactly one person. The SSN *determines* the person. However, if I give you a "First Name," you cannot find exactly one person. Therefore, `FirstName` does not functionally determine `PersonID`.

### Formal Definition: Functional Dependency (FD)
We say $X \to Y$ ($X$ functionally determines $Y$) if, for every pair of tuples $t_1$ and $t_2$ in a relation $R$, whenever $t_1[X] = t_2[X]$, then $t_1[Y] = t_2[Y]$.

### Key Terminology
*   **Superkey:** A set of attributes $S$ such that no two distinct rows in a relation have the same values for $S$.
*   **Candidate Key:** A minimal superkey; if any attribute is removed from $S$, it is no longer a superkey.
*   **Prime Attribute:** An attribute that is part of at least one candidate key.
*   **Non-prime Attribute:** An attribute that is not part of any candidate key.

### Worked Example: Dependency Analysis
Consider the relation $\text{TRADING\_ACCOUNT}(\text{AccountID, ClientEmail, ClientName, PortfolioID, PortfolioRiskLevel})$.

**Given FDs:**
1. $\text{AccountID} \to \{\text{ClientEmail, ClientName, PortfolioID}\}$
2. $\text{ClientEmail} \to \text{ClientName}$
3. $\text{PortfolioID} \to \text{PortfolioRiskLevel}$

**Analysis Steps:**
1. **Determine the Key:** $\text{AccountID}$ determines $\text{ClientEmail, ClientName, and PortfolioID}$ directly. Because $\text{PortfolioID} \to \text{PortfolioRiskLevel}$, $\text{AccountID}$ determines the risk level transitively. Thus, $\text{AccountID}$ is the **Candidate Key**.
2. **Identify Prime Attributes:** Only $\text{AccountID}$ is prime.
3. **Identify Non-prime Attributes:** $\{\text{ClientEmail, ClientName, PortfolioID, PortfolioRiskLevel}\}$.

> **Try This Yourself:** If the rule $\text{ClientEmail} \to \text{AccountID}$ were added, would $\text{ClientEmail}$ become a candidate key? Why? (Hint: Check if it can determine all other attributes in the table).

---

## 2. The Motivation for Normalization: The "Fat" Table
Normalization prevents "data decay"—the gradual introduction of contradictions into your system.

### The Anatomy of an Anomaly
Consider a logistics table: $\text{Shipments}(\text{ShipmentID, DriverName, LicenseNumber, TruckID, TruckModel})$. This table attempts to track three distinct entities: the **Shipment** (event), the **Driver** (person), and the **Truck** (machine).

When we mix entities in one table, we create three specific failures:
1.  **Update Anomaly:** If a driver changes their license number, every shipment row associated with that driver must be updated. If you have 10,000 shipments, one typo in the 500th row creates a data contradiction.
2.  **Deletion Anomaly:** If you delete the only shipment associated with "Truck-X", you inadvertently delete the knowledge that "Truck-X" is a "Volvo FH16". You've lost a piece of equipment data because you deleted a transaction.
3.  **Insertion Anomaly:** You cannot record a new truck's model in the system until that truck is assigned to a specific `ShipmentID`. You cannot have a truck without a trip.

**The Golden Rule:** Normalization ensures that **every fact is stored in exactly one place**.

---

## 3. First Normal Form (1NF): Atomicity

### The Tension: Searchability vs. Storage
If a cell contains a list such as `"Refrigerated, Fragile"`, the database cannot use a standard index to find "Fragile" shipments. It must perform a "full-table scan" using pattern matching (e.g., `LIKE %Fragile%`), which is computationally expensive.

### Formal Definition
A relation is in **1NF** if the domain of every attribute contains only **atomic (indivisible) values**, and there are no repeating groups.

**Analogy:** Think of 1NF as the "No Lists" rule. A spreadsheet cell should be a single value, not a comma-separated string or a nested table.

### Worked Example: Logistics Tags
**Violation:** $\text{SHIPMENT}(\underline{\text{ShipmentID}}, \text{Destination, SpecialHandling})$
*   Row: $(\text{S101, Tokyo, "Refrigerated, Fragile"})$ $\leftarrow$ *Non-atomic value.*

**Decomposition:**
The multi-valued attribute is moved to a separate relation:
1. $\text{SHIPMENT}(\underline{\text{ShipmentID}}, \text{Destination})$
2. $\text{SHIPMENT\_REQUIREMENTS}(\underline{\text{ShipmentID, HandlingTag}})$
   *   $(\text{S101, Refrigerated})$
   *   $(\text{S101, Fragile})$

> **Misconception Alert:** 1NF does not mean "one column per attribute." It means "one value per cell." Using columns like `Phone1`, `Phone2`, and `Phone3` still violates the spirit of 1NF because these are "repeating groups"—you are simulating a list using columns.

---

## 4. Second Normal Form (2NF): Partial Dependencies

### The Tension: Composite Keys
When a primary key consists of two or more columns (a composite key), we risk storing information that only relates to *part* of that key.

### Formal Definition
A relation is in **2NF** if it is in 1NF and no non-prime attribute is **partially dependent** on a candidate key. A partial dependency occurs if $X \to Y$, where $X$ is a proper subset of a candidate key.

**Analogy:** Imagine a "Course-Student" grade book. The key is $\{\text{Student, Course}\}$. The `Grade` depends on both. But if you add `CourseName` to this table, `CourseName` only depends on the `Course` part of the key. It doesn't care which student is taking it.

### Worked Example: Healthcare Staffing
Consider $\text{ASSIGNMENT}(\text{DoctorID, PatientID, DoctorSpecialty})$.
*   **Candidate Key:** $\{\text{DoctorID, PatientID}\}$ (Composite).
*   **Dependency:** $\text{DoctorID} \to \text{DoctorSpecialty}$.

**Analysis:**
`DoctorSpecialty` is non-prime and depends only on `DoctorID`, not the entire composite key. This is a **Partial Dependency**. This creates an anomaly: a doctor's specialty cannot be stored until they are assigned to a patient.

**Decomposition:**
1. $\text{DOCTOR}(\underline{\text{DoctorID}}, \text{DoctorSpecialty})$
2. $\text{PATIENT\_VISIT}(\underline{\text{DoctorID, PatientID}})$

---

## 5. Third Normal Form (3NF): Transitive Dependencies

### The Tension: The "Hidden" Relationship
3NF addresses the "friend-of-a-friend" problem. If the key determines attribute A, and A determines attribute B, then the key determines B *transitively*. B is actually a fact about A, not the key.

### Formal Definition
A relation is in **3NF** if it is in 2NF and no non-prime attribute is **transitively dependent** on a candidate key.
*Simplified Rule:* For every FD $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.

**Analogy:** In a table of `Employees`, the `EmployeeID` determines the `DepartmentID`, and the `DepartmentID` determines the `DepartmentBudget`. The budget is a property of the *department*, not the *employee*. Storing it in the employee table is like listing the building's address on every single employee's badge.

### Worked Example: E-commerce Orders
Consider $\text{ORDER}(\text{OrderID, CustomerID, CustomerZip, City})$.
*   **Candidate Key:** $\{\text{OrderID}\}$.
*   **Dependencies:** $\text{OrderID} \to \text{CustomerZip}$ and $\text{CustomerZip} \to \text{City}$.

**Analysis:**
`City` is non-prime. While $\text{OrderID} \to \text{City}$ holds, it is only true because of the intermediate attribute `CustomerZip`. This is a **Transitive Dependency**. If the only order from zip `90210` is deleted, the knowledge that `90210` is "Beverly Hills" is lost.

**Decomposition:**
1. $\text{ORDER}(\underline{\text{OrderID}}, \text{CustomerID, CustomerZip})$
2. $\text{LOCATION}(\underline{\text{CustomerZip}}, \text{City})$

---

## 6. Boyce-Codd Normal Form (BCNF)

### The Tension: The Prime Attribute Loophole
3NF has a loophole: it allows $X \to Y$ if $Y$ is a prime attribute, even if $X$ is not a key. BCNF closes this loophole. It is a stricter version of 3NF where *every* determinant must be a candidate key.

### Formal Definition
A relation is in **BCNF** if, for every non-trivial functional dependency $X \to Y$, $X$ is a superkey.

**Analogy:** BCNF is like a strict security checkpoint. In 3NF, some "prime" attributes can get through without a key. BCNF says, "I don't care if you're prime; if you're determining something, you must be a superkey."

### Worked Example: Consultant Scheduling
Consider $\text{CONSULTING}(\text{Client, Consultant, Specialization})$.
*   **Rule 1:** $\text{Consultant} \to \text{Specialization}$ (Each consultant has one specialty).
*   **Rule 2:** $\{\text{Client, Specialization}\} \to \text{Consultant}$ (A client uses one consultant per specialty).

**Analysis:**
1. **Candidate Keys:** $\{\text{Client, Consultant}\}$ and $\{\text{Client, Specialization}\}$.
2. **Prime Attributes:** All attributes are prime.
3. **3NF Check:** Because there are no non-prime attributes, the relation is automatically in 3NF.
4. **BCNF Check:** In the FD $\text{Consultant} \to \text{Specialization}$, `Consultant` is not a superkey. This is a **BCNF violation**.

**Decomposition:**
1. $\text{CONSULTANT\_SKILL}(\underline{\text{Consultant}}, \text{Specialization})$
2. $\text{CLIENT\_ASSIGNMENT}(\underline{\text{Client, Consultant}})$

---

## 7. Engineering Trade-offs and Pitfalls

### The Cost: The "Join Tax"
Normalization decomposes a single table into multiple relations. Retrieving a complete record now requires `JOIN` operations. In high-traffic systems, joining ten tables can be significantly slower than reading one "fat" table. This is the "Join Tax."

### Strategic Denormalization: Read vs. Write
The choice of normalization level depends on the system's workload:

| System Type | Primary Concern | Strategy | Rationale |
| :--- | :--- | :--- | :--- |
| **OLTP** (Banking, Apps) | Write Integrity | High Normalization | Prevents inconsistency; ensures atomic, fast updates. |
| **OLAP** (Data Warehouse) | Read Speed | Denormalization | Optimizes aggregation; avoids expensive joins on billions of rows. |

### Common Pitfalls
1.  **Over-Normalization:** Creating tables for trivial data (e.g., a separate table for "Gender" or "Yes/No" flags), resulting in excessive joins for no integrity gain.
2.  **Misidentifying Keys:** Assuming a single-column ID is always the key, which leads to missed 2NF violations in composite-key tables.
3.  **Ignoring Multi-Valued Dependencies (MVDs):** Overlooking attributes that are multi-valued and independent (e.g., a Teacher having multiple Degrees AND multiple Hobbies), which can lead to exponential row growth (4NF violations).

> **Final Challenge:** Look at a common app you use (e.g., Instagram or Spotify). Can you identify one "fat table" they might use in their analytics (OLAP) side that would be a nightmare for their production (OLTP) database?