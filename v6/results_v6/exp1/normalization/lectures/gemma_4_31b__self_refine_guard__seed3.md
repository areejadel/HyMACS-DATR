# Lecture: Normalization Forms and Database Schema Design (1NF–BCNF)

## Learning Objectives
By the end of this lecture, you will be able to:
1. **Identify** update, insertion, and deletion anomalies in a denormalized table.
2. **Determine** functional dependencies and identify candidate keys within a given relation.
3. **Apply** the rules of 1NF, 2NF, 3NF, and BCNF to evaluate a schema's normalization level.
4. **Decompose** a non-normalized relation into a set of normalized relations while preserving data integrity.

---

## 0. Prerequisites and Intuition

### The "Ghost Data" Paradox
Imagine you are designing a global logistics system. You decide to keep everything in one "master table" for convenience:
$\text{Shipments}(\text{ShipmentID, CustomerName, CustomerAddress, WarehouseID, WarehouseLocation})$

**The Tension:** At first, this seems efficient. But consider this: a warehouse moves from Memphis to Dallas. To reflect this, you must update every single shipment record associated with that warehouse. If you miss just one row, your database now claims the same warehouse exists in two cities simultaneously. Even worse, if you delete the last shipment leaving the Memphis warehouse, the record of that warehouse's existence vanishes from your system entirely. 

This is the **Ghost Data Paradox**: the data is there, but it is fragile, contradictory, or disappears when you don't intend it to.

### Database Anomalies
These failures are categorized as three specific anomalies:
*   **Update Anomaly:** Redundant data requires multiple updates for a single logical change; failure to update all instances leads to inconsistency.
*   **Insertion Anomaly:** A fact cannot be recorded because it depends on the existence of another unrelated fact (e.g., a new warehouse cannot be added until a shipment is assigned to it because $\text{ShipmentID}$ cannot be $\text{NULL}$).
*   **Deletion Anomaly:** Deleting a record to remove one fact accidentally deletes an unrelated fact.

### Functional Dependency (FD)
To resolve these anomalies, we use **Functional Dependencies** to describe the relationships between attributes.

**Analogy: The Digital Fingerprint.** 
Think of an FD as a "fingerprint" or a unique identifier. In a mathematical function $f(x) = y$, the input $x$ uniquely determines $y$. In a database, if knowing the $\text{EmployeeID}$ always leads you to exactly one $\text{EmployeeName}$, then $\text{EmployeeID}$ functionally determines $\text{EmployeeName}$. If you have the "fingerprint" (ID), you have the "identity" (Name).

**Formal Definition:** In a relation $R$, an attribute $X$ (or set of attributes) **functionally determines** attribute $Y$ (denoted $X \to Y$) if, for every pair of tuples $t_1, t_2$ in $R$, the condition $t_1[X] = t_2[X]$ implies $t_1[Y] = t_2[Y]$.

**Core Terminology:**
*   **Candidate Key (CK):** A minimal set of attributes $K$ such that $K \to R$ (it determines every other attribute in the relation).
*   **Superkey:** Any set of attributes that contains a candidate key.
*   **Prime Attribute:** An attribute that is part of at least one candidate key.
*   **Non-prime Attribute:** An attribute that is not part of any candidate key.

> **Worked Example: Identifying Keys**
> Relation: $\text{Students}(\text{StudentID, SSN, Name, Email})$
> Assume: $\text{StudentID} \to \{\text{Name, Email}\}$ and $\text{SSN} \to \{\text{Name, Email}\}$.
> 1. **Find CKs:** Both $\{\text{StudentID}\}$ and $\{\text{SSN}\}$ uniquely identify the row and are minimal. Both are Candidate Keys.
> 2. **Identify Prime Attributes:** $\text{StudentID}$ and $\text{SSN}$ are prime.
> 3. **Identify Non-prime Attributes:** $\text{Name}$ and $\text{Email}$ are non-prime.

**Try This Yourself 1:** You are designing a system for a library. The table is $\text{Books}(\text{ISBN, InternalBarcode, Title, Genre})$. If both $\text{ISBN}$ and $\text{InternalBarcode}$ uniquely identify a book, which attributes are prime? Which are non-prime?
*(Answer: Prime: ISBN, InternalBarcode; Non-prime: Title, Genre)*

---

## 1. First Normal Form (1NF): Atomicity

### Intuition: The Search Problem
Consider a `PhoneNumbers` column containing `"555-1234, 555-5678"`. 

**The Tension:** To find a specific number, the database cannot use a B-Tree index because the index only sees the start of the string. It must perform a "Full Table Scan"—reading every single row and parsing the string. This shifts the time complexity from $\mathcal{O}(\log n)$ to $\mathcal{O}(n)$. For a billion rows, this is the difference between milliseconds and minutes.

**Formal Definition:** A relation is in **1NF** if and only if the domain of each attribute contains only **atomic** (indivisible) values, and there are no repeating groups or multi-valued attributes.

**Cross-Domain Link: The "Single Responsibility" Principle.** 
Just as in software engineering where a class should have one reason to change, 1NF mandates that a cell should hold one piece of information. Storing a list in a cell is essentially treating a database table like a text file.

> **Worked Example: Healthcare Records**
> **Non-1NF State:** $\text{PATIENTS}(\text{PatientID, Name, Medications})$
> | PatientID | Name | Medications |
> | :--- | :--- | :--- |
> | P001 | Alice | {Lisinopril, Metformin} |
> 
> **Decomposition:** To achieve 1NF, we split the multi-valued attribute into two relations:
> 1. $\text{PATIENTS}(\underline{\text{PatientID}}, \text{Name})$
> 2. $\text{PATIENT\_MEDS}(\underline{\text{PatientID, Medication}})$

**Note on Atomicity:** Atomicity is defined by how the application uses the data. A `Date` (Year-Month-Day) is atomic if the application never queries the "Month" independently.

**Quick Check 2:** A table $\text{Orders}$ has a column $\text{Items}$ containing comma-separated product IDs. Is this in 1NF?
*(Answer: No, it contains non-atomic, multi-valued attributes.)*

---

## 2. Second Normal Form (2NF): Partial Dependencies

Having ensured atomicity, we now address dependencies within composite keys.

### Intuition: The "Half-Key" Problem
**The Tension:** Imagine a table where the primary key is a combination of $\text{OrderID}$ and $\text{ProductID}$. If you store the `ProductDescription` in this table, that description depends *only* on the $\text{ProductID}$, not the $\text{OrderID}$. 

This creates a "half-dependency." If 1,000 orders contain an "iPhone 15", the description is stored 1,000 times. If you want to fix a typo in the description, you must update 1,000 rows. This is a waste of storage and a risk to integrity.

**Formal Definition:** A relation is in **2NF** if:
1. It is in 1NF.
2. Every non-prime attribute is **fully functionally dependent** on every candidate key.

**Analogy: The "Wrong Address" Error.** 
A partial dependency is like sending a package to a "City" but not a "Street Address." The city tells you the general area (Partial Key), but you need the specific street (Full Key) to find the exact house (Non-prime attribute). If the attribute only needs the city to be identified, it doesn't belong in a table indexed by street address.

> **Worked Example: E-commerce Order Items**
> **Scenario:** $\text{ORDER\_ITEMS}(\text{OrderID, ProductID, Quantity, UnitPrice, ProductDescription})$
> *   **Candidate Key:** $\{\text{OrderID, ProductID}\}$
> *   **Dependencies:**
>     *   $\{\text{OrderID, ProductID}\} \to \text{Quantity}$ (Full dependency).
>     *   $\text{ProductID} \to \text{UnitPrice}$ (**Partial dependency**).
>     *   $\text{ProductID} \to \text{ProductDescription}$ (**Partial dependency**).
> 
> **Decomposition:**
> 1. $\text{ORDER\_LINE}(\underline{\text{OrderID, ProductID}}, \text{Quantity})$
> 2. $\text{PRODUCT}(\underline{\text{ProductID}}, \text{UnitPrice, ProductDescription})$

**Quick Check 3:** If a table has a single-attribute primary key (e.g., $\text{UserID}$), can it violate 2NF?
*(Answer: No. A single attribute has no proper subsets, making partial dependency impossible.)*

---

## 3. Third Normal Form (3NF): Transitive Dependencies

With partial dependencies removed, we must now eliminate dependencies between non-prime attributes.

### Intuition: Eliminating the "Middleman"
**The Tension:** You have a table where $\text{EmpID} \to \text{DeptID}$ and $\text{DeptID} \to \text{DeptManager}$. 
The $\text{EmpID}$ (the key) technically determines the $\text{DeptManager}$, but it does so *indirectly*. This is a transitive dependency. 

The danger here is "hidden" data. If you delete the last employee in the "Quantum Physics" department, you don't just lose an employee record—you lose the fact that Dr. Smith manages the Quantum Physics department. The manager's identity is "piggybacking" on the employee's existence.

**Formal Definition:** A relation is in **3NF** if:
1. It is in 2NF.
2. For every non-trivial FD $X \to A$, either $X$ is a superkey OR $A$ is a prime attribute.

**Analogy: The Game of Telephone.** 
Transitive dependency is like a game of telephone: $\text{Key} \to \text{Attribute A} \to \text{Attribute B}$. To ensure stability, we "cut the line" and give $\text{Attribute A}$ and $\text{Attribute B}$ their own separate table, removing the middleman.

> **Worked Example: Corporate HR System**
> **Scenario:** $\text{EMPLOYEE}(\text{EmpID, DeptID, DeptManager})$
> *   **Candidate Key:** $\{\text{EmpID}\}$
> *   **FDs:** $\text{EmpID} \to \text{DeptID}$ and $\text{DeptID} \to \text{DeptManager}$.
> *   **Analysis:** $\text{DeptManager}$ is non-prime and depends on $\text{DeptID}$ (also non-prime).
> *   **Chain:** $\text{EmpID} \to \text{DeptID} \to \text{DeptManager}$.
> 
> **Decomposition:**
> 1. $\text{EMP\_DEPT}(\underline{\text{EmpID}}, \text{DeptID})$
> 2. $\text{DEPARTMENT}(\underline{\text{DeptID}}, \text{DeptManager})$

**Try This Yourself 2:** You have a table $\text{Store}(\text{StoreID, StoreZip, StoreCity})$. Assume $\text{StoreID} \to \text{StoreZip}$ and $\text{StoreZip} \to \text{StoreCity}$. Is this in 3NF? Why or why not?
*(Answer: No. It is in 2NF, but there is a transitive dependency: $\text{StoreID} \to \text{StoreZip} \to \text{StoreCity}$.)*

---

## 4. Boyce-Codd Normal Form (BCNF): The Strict Standard

BCNF addresses a specific loophole in 3NF regarding overlapping candidate keys.

### Intuition: Overlapping Keys
**The Tension:** 3NF is "lenient." It allows a dependency if the attribute being determined is "prime" (part of *any* candidate key). BCNF is "strict." It says: "I don't care if the attribute is prime; if the determinant isn't a superkey, it's a violation."

This usually happens when you have multiple composite keys that share an attribute.

**Formal Definition:** A relation is in **BCNF** if, for every non-trivial FD $X \to A$, $X$ must be a superkey.

**Analogy: The Exclusive Club.** 
In 3NF, an attribute can get into the "dependency club" if it's a prime attribute, even if its determinant isn't a superkey. BCNF is like a strict bouncer who only lets you in if the determinant is a Superkey. No exceptions.

> **Worked Example: University Tutoring**
> **Scenario:** $\text{TUTORING}(\text{Student, Subject, Tutor})$
> *   **Constraints:** 
>     1. A student has one tutor per subject.
>     2. A tutor teaches only one subject.
> *   **FDs:** $\{\text{Student, Subject}\} \to \text{Tutor}$ and $\text{Tutor} \to \text{Subject}$.
> *   **Candidate Keys:** $\{\text{Student, Subject}\}$ and $\{\text{Student, Tutor}\}$.
> 
> **Analysis:** 
> Consider $\text{Tutor} \to \text{Subject}$.
> *   Is $\text{Tutor}$ a superkey? **No**.
> *   Is $\text{Subject}$ a prime attribute? **Yes** (it is part of $\{\text{Student, Subject}\}$).
> *   **Result:** This is valid in 3NF but **invalid in BCNF**.
> 
> **Anomaly:** We cannot record that "Professor X teaches Calculus" until at least one student signs up for it.
> 
> **Decomposition:**
> 1. $\text{TUTOR\_SPECIALTY}(\underline{\text{Tutor}}, \text{Subject})$
> 2. $\text{STUDENT\_TUTOR}(\underline{\text{Student, Tutor}})$

---

## 5. Advanced Dependencies: Multi-Valued Dependencies (MVD)

### Intuition: Orthogonal Data
Multi-valued dependencies occur when a table contains two independent sets of values related to the same entity. 

**The Tension:** This isn't a functional dependency (where one value leads to one other value), but a "combinatorial explosion." If a consultant has 3 skills and speaks 3 languages, and those two things are unrelated, a single table must store $3 \times 3 = 9$ rows to represent all combinations. If you add one more language, you must add 3 more rows (one for each skill).

**Cross-Domain Link: Cartesian Products.** 
MVD is essentially a Cartesian Product living inside a table. When two independent one-to-many relationships are forced into one table, the table grows quadratically rather than linearly.

**Decomposition (4NF):**
1. $\text{CONSULTANT\_SKILLS}(\underline{\text{ConsultantID, Skill}})$
2. $\text{CONSULTANT\_LANGS}(\underline{\text{ConsultantID, Language}})$

---

## 6. Limitations and Trade-offs

### The Normalization Paradox: Integrity vs. Performance
Normalization is a trade-off between **Write Integrity** and **Read Speed**.

*   **OLTP (Online Transaction Processing):** High normalization (3NF/BCNF). Optimized for "Writes." When you change a user's address, you change it in *one* place. This is critical for banking and e-commerce.
*   **OLAP (Online Analytical Processing):** Intentional denormalization. Optimized for "Reads." In a data warehouse, we use "Fact Tables" to avoid joining 20 tables together, which would destroy query performance.

### Common Pitfalls
1.  **Join Explosion:** Decomposing to BCNF can increase the CPU cost of queries because the database must "stitch" the data back together using joins.
2.  **Dependency Loss:** Some BCNF decompositions are not "dependency-preserving." You might split a table such that a specific business rule (FD) can no longer be enforced by a primary key and requires a complex trigger.
3.  **The "Atomic" Fallacy:** Atomicity is relative. A `Date` field is atomic for a "Sales by Year" report but non-atomic for a "Sales by Hour" report. Always define atomicity based on the **access pattern**, not the data type.