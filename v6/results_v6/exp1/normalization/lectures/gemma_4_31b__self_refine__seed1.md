### The Theoretical Foundation of Database Schema Design: Normalization (1NF–BCNF)

#### Learning Objectives
By the end of this lecture, you will be able to:
1. **Identify** update, insertion, and deletion anomalies in an unnormalized relation.
2. **Determine** candidate keys and functional dependencies for a given relation.
3. **Evaluate** whether a relation satisfies 1NF, 2NF, 3NF, and BCNF.
4. **Decompose** a non-normalized relation into a set of normalized relations that are lossless and dependency-preserving.

---

#### 1. The Problem: The Cost of "Flat" Data
Imagine you are designing a system for a global logistics firm. You decide to keep everything in one giant "Master Table" for convenience. At first, it seems efficient—everything is in one place. But then, a single piece of data changes.

If a customer moves house, you must find and update 5,000 rows of historical order data. If you miss one row, your database now claims the customer lives in two different cities simultaneously. This is not a storage problem; it is a **truth problem**.

Normalization is the process of ensuring that every "fact" is stored in exactly one place. When we fail to do this, we encounter **anomalies**:

**Case Study: The Healthcare Appointment Table**
$\text{APPOINTMENTS}(\underline{\text{ApptID}}, \text{PatientID}, \text{PatientName}, \text{DoctorID}, \text{DoctorSpecialty}, \text{Date})$

| ApptID | PatientID | PatientName | DoctorID | DoctorSpecialty | Date |
| :--- | :--- | :--- | :--- | :--- | :--- |
| A1 | P10 | Alice | D99 | Cardiology | 2023-10-01 |
| A2 | P10 | Alice | D88 | Neurology | 2023-10-05 |
| A3 | P20 | Bob | D99 | Cardiology | 2023-10-10 |

*   **Update Anomaly:** Alice changes her name to "Alice Smith." If the system updates row A1 but crashes before A2, the database is now logically inconsistent.
*   **Insertion Anomaly:** You hire Dr. Zee (Oncology). You cannot add them to the system because the primary key `ApptID` cannot be null; Dr. Zee "doesn't exist" until they have their first patient.
*   **Deletion Anomaly:** Deleting appointment A2 doesn't just remove a meeting; it deletes the only record in the system that Patient P10 ever saw a Neurologist.

**The Solution:** Decomposition. We split the "fat" table into "lean" tables so that a doctor's specialty is a property of the *doctor*, not a property of the *appointment*.

> **Try this yourself:** Imagine a `COURSE_REGISTRATION` table with `StudentName`, `CourseName`, and `ProfessorEmail`. If a professor leaves the university, what happens to the record of the students who took that course? Which anomaly is this?

---

#### 2. Prerequisites: Functional Dependencies and Keys
Before we can "fix" a table, we need a mathematical way to describe the relationships between columns.

**The Concept: Functional Dependency (FD)**
Think of an FD as a **lookup function**. If I know the value of $X$, can I definitively find the value of $Y$ every single time?
*   **Formal Definition:** $X \to Y$ if, for any two tuples $t_1$ and $t_2$, $t_1[X] = t_2[X]$ implies $t_1[Y] = t_2[Y]$.
*   **Analogy:** A Social Security Number (SSN) $\to$ Legal Name. The SSN "determines" the name. However, Legal Name $\not\to$ SSN, because two people can be named "John Smith."

**Key Definitions:**
*   **Superkey:** Any set of attributes that uniquely identifies a row.
*   **Candidate Key:** The "leanest" possible superkey (no unnecessary attributes).
*   **Prime Attribute:** An attribute that is part of any candidate key.

**Worked Example: E-Commerce Order System**
$\text{ORDER\_DETAILS}(\text{OrderID, ProductID, OrderDate, ProductPrice, Quantity})$

1.  **Identify FDs:**
    *   $\text{OrderID} \to \text{OrderDate}$ (An order happens on one specific day).
    *   $\text{ProductID} \to \text{ProductPrice}$ (A product has one standard price).
    *   $\{\text{OrderID, ProductID}\} \to \text{Quantity}$ (The amount of *this* item in *this* order).
2.  **Determine the Candidate Key:** Neither $\text{OrderID}$ nor $\text{ProductID}$ alone can determine everything. Only the combination $\{\text{OrderID, ProductID}\}$ identifies the specific line item.
    *   **Candidate Key:** $\{\text{OrderID, ProductID}\}$.
    *   **Prime Attributes:** $\text{OrderID, ProductID}$.

---

#### 3. First Normal Form (1NF): Atomicity
**The Tension:** We often want to store "lists" (e.g., a user's phone numbers) in a single cell for convenience. But databases are designed to operate on scalars, not arrays.

**Formal Definition:** A relation is in **1NF** if every attribute contains only atomic (indivisible) values.

**The Innovation: The Computational Cost of Non-Atomicity**
If you store `TransactionIDs` as a comma-separated string `"T1, T4, T9"`, the database cannot use a B-Tree index to find `T4`. It must perform a **Full Table Scan** and execute string parsing on every single row—transforming an $O(\log N)$ search into an $O(N)$ disaster.

**Resolution:** Move the list to a new table where each transaction gets its own row.
$\text{USER\_TRANSACTIONS}(\underline{\text{UserID, TransactionID}})$

> **Quick Check:** If a table uses columns `Skill1`, `Skill2`, and `Skill3`, is it in 1NF?
> *(Answer: Technically yes, but it creates "Repeating Groups," which is a structural smell that usually leads to 2NF/3NF violations.)*

---

#### 4. Second Normal Form (2NF): Partial Dependencies
**The Tension:** 2NF only matters when you have a **composite key**. If your key is a "team" of attributes, does every other column depend on the *whole team*, or just *one member* of the team?

**Formal Definition:** A relation is in **2NF** if it is in 1NF and no non-prime attribute is **partially dependent** on a candidate key.

**Analogy: The "Wrong Address" Problem**
Imagine a key $\{\text{BuildingID, RoomNumber}\}$. If you store the `BuildingAddress` in this table, you have a partial dependency. The address depends on the `BuildingID`, but it doesn't care which `RoomNumber` you are in. You are effectively storing the building's address thousands of times (once for every room).

**Worked Example: Logistics Fleet Management**
$\text{TRUCK\_ASSIGNMENT}(\underline{\text{TruckID, RouteID}}, \text{DriverID}, \text{DriverLicenseNum})$
*   **Violation:** $\text{DriverLicenseNum}$ depends on $\text{DriverID}$, which is determined by the key. But if we consider the dependency $\text{DriverID} \to \text{DriverLicenseNum}$, we see that the license is tied to the person, not the specific truck/route combination.

**Resolution:**
1.  $\text{DRIVER}(\underline{\text{DriverID}}, \text{DriverLicenseNum})$
2.  $\text{ASSIGNMENT}(\underline{\text{TruckID, RouteID}}, \text{DriverID})$

---

#### 5. Third Normal Form (3NF): Transitive Dependencies
**The Tension:** 2NF stopped attributes from depending on *part* of the key. But what if a non-key attribute depends on *another non-key attribute*?

**Formal Definition:** A relation is in **3NF** if it is in 2NF and no non-prime attribute is **transitively dependent** on a candidate key ($Key \to Y \to Z$).

**Cross-Domain Link: Data Science & Feature Leakage**
In Machine Learning, a transitive dependency in a database is similar to "feature leakage." If $\text{EmpID} \to \text{DeptID} \to \text{DeptHead}$, then `DeptHead` is not a property of the employee; it is a property of the department. Treating it as an employee attribute in a model creates redundant signals that can mislead an algorithm.

**Worked Example: Corporate Payroll**
$\text{EMPLOYEE}(\underline{\text{EmpID}}, \text{EmpName}, \text{DeptID}, \text{DeptHead})$
*   **The Chain:** $\text{EmpID} \to \text{DeptID}$ and $\text{DeptID} \to \text{DeptHead}$.
*   **The Anomaly:** If you fire the last employee in the "Research" department, you accidentally delete the fact that "Dr. Aris" is the head of Research.

**Resolution:**
1.  $\text{EMPLOYEE}(\underline{\text{EmpID}}, \text{EmpName}, \text{DeptID})$
2.  $\text{DEPARTMENT}(\underline{\text{DeptID}}, \text{DeptHead})$

---

#### 6. Boyce-Codd Normal Form (BCNF): The Determinant Standard
**The Tension:** 3NF handles non-prime attributes. But what if a **prime attribute** (part of a key) depends on a non-key attribute? 3NF allows this; BCNF does not.

**Formal Definition:** A relation is in **BCNF** if, for every non-trivial FD $X \to Y$, $X$ must be a superkey. (Essentially: "The key, the whole key, and nothing but the key, so help me Codd.")

**Worked Example: Specialized Clinic Scheduling**
$\text{SCHEDULE}(\underline{\text{Patient, Time}}, \text{Doctor, Specialty})$
*   **Constraints:** $\{\text{Patient, Time}\} \to \text{Doctor}$ AND $\text{Doctor} \to \text{Specialty}$.
*   **The Violation:** $\text{Doctor}$ determines $\text{Specialty}$, but $\text{Doctor}$ is not a superkey (a doctor has many patients/times).
*   **The Problem:** You cannot record that "Dr. House is a Diagnostician" until he has a patient scheduled.

**Resolution:**
1.  $\text{DOCTOR\_INFO}(\underline{\text{Doctor}}, \text{Specialty})$
2.  $\text{APPOINTMENT}(\underline{\text{Patient, Time}}, \text{Doctor})$

---

#### 7. Practical Trade-offs: Normalization vs. Performance

Normalization is a quest for **Write Integrity**. However, it creates **Read Overhead**. Every time you decompose a table, you add a `JOIN` operation to get the data back.

**1. Denormalization (The OLAP Approach)**
In Big Data/Data Warehousing (OLAP), we often intentionally revert to lower normal forms to maximize read speed.
*   **Star Schema:** We use a central **Fact Table** (metrics) surrounded by **Dimension Tables** (descriptions). This mimics a "semi-normalized" state to avoid 10-way joins on billion-row tables.

**2. Materialized Views**
The "best of both worlds" strategy: Store the data in BCNF to ensure no anomalies occur during updates, but maintain a physically stored "snapshot" (Materialized View) that is pre-joined for lightning-fast reads.

**Summary of Normalization Forms**

| Form | Requirement | Eliminates... | Analogy |
| :--- | :--- | :--- | :--- |
| **1NF** | Atomic values | Multi-valued attributes | No "lists" in cells |
| **2NF** | 1NF + No partial FDs | Composite key redundancy | No "half-key" dependencies |
| **3NF** | 2NF + No transitive FDs | Non-key redundancy | No "indirect" dependencies |
| **BCNF** | Every determinant is a superkey | All FD anomalies | Only keys can be determinants |