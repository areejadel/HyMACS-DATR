### Lecture: Normalization Forms and Database Schema Design (1NF–BCNF)

#### Learning Objectives
By the end of this lecture, you will be able to:
1. **Identify** update, insertion, and deletion anomalies in a denormalized table.
2. **Compute** the attribute closure of a set of attributes to determine Candidate Keys.
3. **Analyze** a relation to determine its current Normal Form (1NF, 2NF, 3NF, or BCNF).
4. **Decompose** a relation into a higher normal form while preserving data integrity.

---

#### 1. The Motivation: The Cost of Redundancy
Imagine you are designing the backend for a global logistics system. You decide to store everything in one massive "Master Table" for convenience. At first, it seems efficient—one query gets you everything. But as the data grows, you encounter a paradox: **the more data you store in one place, the harder it becomes to keep that data accurate.**

When the same fact is stored in multiple rows, the database no longer represents a single version of truth; it represents a collection of claims that must be manually synchronized. If they fall out of sync, you have "data corruption" not from a disk failure, but from a design failure.

**Example: Healthcare Appointments**
Consider the relation: $\text{Appointments}(\text{PatientID, PatientName, DoctorID, DoctorSpecialty, AppointmentDate})$

| PatientID | PatientName | DoctorID | DoctorSpecialty | AppointmentDate |
| :--- | :--- | :--- | :--- | :--- |
| P1 | Alice | D10 | Cardiology | 2023-10-01 |
| P2 | Bob | D10 | Cardiology | 2023-10-02 |
| P3 | Charlie | D20 | Neurology | 2023-10-01 |

**The Tension:** We want to record an appointment, but the table is forcing us to record the doctor's biography every single time. This creates three critical failures:
*   **Update Anomaly:** If Doctor D10 changes their specialty to "Internal Medicine," you must find every single appointment they've ever had. Miss one row, and your database now claims Doctor D10 is both a Cardiologist and an Internist.
*   **Insertion Anomaly:** You hire a new doctor (D30, Pediatrics). You cannot add them to the system until they have a patient. The system effectively says, "Doctors do not exist unless they are currently seeing a patient."
*   **Deletion Anomaly:** Patient P3 cancels. You delete the row. Suddenly, the system forgets that Doctor D20 specializes in Neurology. The doctor's expertise was "piggybacking" on the patient's appointment.

**Try this yourself:** If `CourseName` and `InstructorEmail` are stored in a `StudentEnrollment` table, what happens to the instructor's contact info if the last student drops the course?

---

#### 2. Prerequisites: Functional Dependencies and Closure
To fix these anomalies, we need a mathematical way to describe "who depends on whom."

**Functional Dependencies (FD)**
A Functional Dependency is a constraint. If we know the value of $X$, we can uniquely determine the value of $Y$. This is denoted as $X \to Y$. 

**The Analogy:** Think of an FD as a **lookup function**. If $\text{SocialSecurityNumber} \to \text{FullName}$, then the SSN is the "input" and the Name is the "output." If you provide the same input twice, you must get the same output. If you get two different names for one SSN, the dependency is violated.

**Attribute Closure ($X^+$)**
The closure of a set of attributes $X$ is the set of all attributes that can be "unlocked" by $X$ using the available FDs.

**Algorithm for Computing $X^+$:**
```text
1. Initialize X+ = X.
2. Repeat until X+ does not grow:
   For each FD (A -> B):
     If A is a subset of X+, then X+ = X+ U B.
3. Return X+.
```

**Worked Example: E-commerce Order System**
Relation: $\text{OrderDetails}(\text{OrderID, ProductID, OrderDate, ProductPrice, Quantity})$
$\text{FDs: } \{ \text{FD}_1: \text{OrderID} \to \text{OrderDate}, \text{FD}_2: \text{ProductID} \to \text{ProductPrice}, \text{FD}_3: \{\text{OrderID, ProductID}\} \to \text{Quantity} \}$

*Goal: Determine if $\{\text{OrderID, ProductID}\}$ is a Candidate Key.*
1. $\{\text{OrderID, ProductID}\}^+ = \{\text{OrderID, ProductID}\}$
2. Apply $\text{FD}_1$ ($\text{OrderID}$ is present) $\to$ $\{\text{OrderID, ProductID, OrderDate}\}$
3. Apply $\text{FD}_2$ ($\text{ProductID}$ is present) $\to$ $\{\text{OrderID, ProductID, OrderDate, ProductPrice}\}$
4. Apply $\text{FD}_3$ ($\text{OrderID, ProductID}$ are present) $\to$ $\{\text{OrderID, ProductID, OrderDate, ProductPrice, Quantity}\}$

**Conclusion:** Since the closure contains all attributes, $\{\text{OrderID, ProductID}\}$ is a Candidate Key.

**Key Terminology:**
*   **Candidate Key (CK):** A minimal set of attributes that uniquely identifies a tuple.
*   **Prime Attribute:** An attribute that is part of any candidate key.
*   **Non-prime Attribute:** An attribute that is not part of any candidate key.

**Formative Check:** Given $\text{R(A, B, C)}$ and $\text{FDs: } \{A \to B, B \to C\}$, what is $A^+$? 
*Answer: $\{A, B, C\}$.*

---

#### 3. First Normal Form (1NF): Atomicity
A relation is in 1NF if every attribute contains only atomic (indivisible) values.

**The Problem: The "Hidden List"**
Storing multiple values in a single cell (e.g., `Tags` as `"Food, Travel, Work"`) seems convenient, but it creates a computational nightmare. To find "Travel" transactions, the DB cannot use a B-Tree index; it must perform a full string scan of every row.

**The Solution**
Decompose the multi-valued attribute into a separate relation.
*   **Before:** $\text{Transactions}(\text{TxID, Tags}) \to (101, \text{"Food, Travel"})$
*   **After:** $\text{TransactionTags}(\underline{\text{TxID, Tag}}) \to (101, \text{"Food"}), (101, \text{"Travel"})$

**Innovation Note:** In modern industry, you will see `JSONB` columns in PostgreSQL. While these allow "lists," they are effectively "denormalization by choice." If you find yourself frequently indexing specific keys inside a JSON blob, you are fighting the database; you should likely be in 1NF.

---

#### 4. Second Normal Form (2NF): Full Dependency
A relation is in 2NF if it is in 1NF and no non-prime attribute is **partially dependent** on a candidate key.

**The Tension:** Partial dependency only exists when you have a **composite key**. The danger is that you are mixing two different "entities" in one table.

**The Analogy:** Imagine a "Student-Course" table. If you store the `StudentName` and the `CourseName` in a table keyed by $\{\text{StudentID, CourseID}\}$, you have a problem. The `StudentName` doesn't care which course is being taken; it only depends on the `StudentID`. It is "half-dependent" on the key.

**Worked Example: Logistics Fleet Management**
$\text{VehicleAssignment}(\underline{\text{VehicleID, DriverID}}, \text{VehicleModel, DriverLicenseNo, TripDate})$
*   **Analysis of FDs:**
    *   $\text{VehicleID} \to \text{VehicleModel}$ (Partial Dependency: $\text{VehicleModel}$ only needs the VehicleID).
    *   $\text{DriverID} \to \text{DriverLicenseNo}$ (Partial Dependency: $\text{DriverLicenseNo}$ only needs the DriverID).
    *   $\{\text{VehicleID, DriverID}\} \to \text{TripDate}$ (Full Dependency: You need both the driver and the truck to know when the trip happened).

**Decomposition:** Split the "half-dependencies" into their own homes:
1. $\text{Vehicle}(\underline{\text{VehicleID}}, \text{VehicleModel})$
2. $\text{Driver}(\underline{\text{DriverID}}, \text{DriverLicenseNo})$
3. $\text{Trip}(\underline{\text{VehicleID, DriverID}}, \text{TripDate})$

---

#### 5. Third Normal Form (3NF): No Transitive Dependencies
A relation is in 3NF if it is in 2NF and, for every non-trivial FD $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.

**The Intuition: "The Middleman"**
3NF forbids "indirect" dependencies. It stops the chain: $\text{Key} \to \text{Attribute A} \to \text{Attribute B}$.

**The Analogy:** Think of this as a **chain of command**. In a well-normalized table, every non-key attribute should report directly to the Primary Key (the boss), not to another non-key attribute (a middle manager).

**Worked Example: Real Estate Listings**
$\text{Property}(\underline{\text{PropertyID}}, \text{ZipCode, City, State})$
*   **FDs:** $\text{PropertyID} \to \text{ZipCode}$ and $\text{ZipCode} \to \text{City, State}$.
*   **The Problem:** $\text{City}$ depends on $\text{ZipCode}$, and $\text{ZipCode}$ depends on $\text{PropertyID}$. If you delete all properties in a specific ZipCode, you accidentally delete the knowledge of which city that ZipCode belongs to.

**Decomposition:**
1. $\text{Location}(\underline{\text{ZipCode}}, \text{City, State})$
2. $\text{Property}(\underline{\text{PropertyID}}, \text{ZipCode})$

**Try this yourself:** In $\text{Employee}(\underline{\text{EmpID}}, \text{DeptID, DeptName})$, where $\text{EmpID} \to \text{DeptID}$ and $\text{DeptID} \to \text{DeptName}$, identify the "middleman" attribute.

---

#### 6. Boyce-Codd Normal Form (BCNF): The Determinant Standard
BCNF is a stricter version of 3NF. It removes the "prime attribute" loophole. In BCNF, **every determinant must be a superkey.**

**The Tension:** 3NF allows a dependency if the dependent attribute is "prime" (part of a key). BCNF says: "I don't care if it's prime; if the determinant isn't a superkey, it's a redundancy risk."

**Worked Example: Consulting Firm**
$\text{Consulting}(\underline{\text{Client, Project}}, \text{Consultant})$
*   **Constraints:** Each project has one consultant; each consultant works on only one project.
*   **FDs:** 
    1. $\{\text{Client, Project}\} \to \text{Consultant}$
    2. $\text{Consultant} \to \text{Project}$
*   **Analysis:** 
    *   Candidate Keys: $\{\text{Client, Project}\}$ and $\{\text{Client, Consultant}\}$.
    *   In $\text{Consultant} \to \text{Project}$, the determinant ($\text{Consultant}$) is **not** a superkey. 
    *   Wait! $\text{Project}$ is a **prime attribute**, so this is allowed in 3NF.
    *   But in BCNF, this is forbidden. Why? Because if a Consultant changes projects, you must update that change across every Client they serve.

**Decomposition:**
1. $\text{ConsultantProject}(\underline{\text{Consultant}}, \text{Project})$
2. $\text{ClientConsultant}(\underline{\text{Client, Consultant}})$

---

#### 7. Summary and Trade-offs

**The "Join Penalty" vs. "Anomaly Tax"**
Normalization is a trade-off between **Write Integrity** and **Read Speed**.
*   **Normalized (BCNF):** Fast writes, no anomalies, but requires multiple `JOIN` operations to reconstruct data.
*   **Denormalized:** Fast reads (no joins), but "expensive" writes because you must update the same fact in ten places.

In modern Big Data (e.g., NoSQL, Snowflake), we often intentionally denormalize. We pay the "Anomaly Tax" (managing consistency in the application layer) to avoid the "Join Penalty" on petabytes of data.

**Normalization Summary Matrix**

| Form | Core Requirement | Target Anomaly | Rule of Thumb |
| :--- | :--- | :--- | :--- |
| **1NF** | Atomic values | Multi-valued fields | No lists in cells |
| **2NF** | Full FD on CK | Partial dependencies | No non-prime $\to$ part of CK |
| **3NF** | No transitive FD | Non-key dependencies | No non-prime $\to$ non-prime |
| **BCNF** | Determinant is Superkey | Overlapping key redundancy | All determinants must be keys |