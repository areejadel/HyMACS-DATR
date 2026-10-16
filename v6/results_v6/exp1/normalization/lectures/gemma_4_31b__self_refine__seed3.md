# Lecture: Normalization Forms and Database Schema Design (1NF–BCNF)

## Learning Objectives
By the end of this lecture, you will be able to:
1. **Identify** update, insertion, and deletion anomalies in a given relation.
2. **Determine** functional dependencies (FDs) and identify candidate keys within a schema.
3. **Apply** the rules of 1NF, 2NF, 3NF, and BCNF to detect normalization violations.
4. **Decompose** a non-normalized relation into a set of normalized relations that preserve data integrity.

---

## 0. Prerequisites and Intuition

### The Cost of Redundancy: Why Normalize?
Imagine you are designing a database for a global logistics firm. You decide to store everything in one giant "Master Table" to make querying easier. You have a column for `ProfessorName` and `ProfessorOffice`. 

Now, imagine that professor moves offices. In a table with 10,000 students, that professor might appear in 500 rows. If your update query misses even one row, your database now claims the professor is in two places at once. This is not just a "bug"—it is a loss of **data integrity**.

Storing the same fact in multiple places creates three structural failures:
*   **Update Anomaly:** Changing a single fact (e.g., an office number) requires searching and updating every single row where that fact appears.
*   **Insertion Anomaly:** You cannot record a new course and its professor until at least one student enrolls, because the primary key requires a `StudentID`. The existence of the course is "held hostage" by the enrollment of a student.
*   **Deletion Anomaly:** If the only student in a niche course drops out and you delete that row, you accidentally wipe out the record of who teaches the course and where their office is.

**The Goal:** Normalization is the process of ensuring that every "fact" is stored exactly once. We move from a "spreadsheet mindset" (flat files) to a "relational mindset" (interconnected facts).

### Functional Dependencies (FD)
Normalization is the formal analysis of the "gravity" between attributes.

**Intuition:** If knowing the value of $X$ always tells you exactly one value of $Y$, then $X$ functionally determines $Y$. 

**Cross-Domain Connection:** Think of an FD as a **mathematical function** $f(x) = y$. In the function $y = x^2$, if you know $x$ is 2, $y$ *must* be 4. Similarly, if `EmployeeID` $\to$ `EmployeeName`, knowing the ID "locks" the name. If the same ID could lead to two different names, the dependency is broken.

**Formal Definition:** Let $R$ be a relation schema and $X, Y$ be sets of attributes. We say $X \to Y$ if, for every pair of tuples $t_1, t_2$ in $R$, $t_1[X] = t_2[X]$ implies $t_1[Y] = t_2[Y]$.

**Key Terminology:**
*   **Superkey:** A set of attributes $S$ that uniquely identifies a tuple.
*   **Candidate Key:** A minimal superkey; the "leanest" possible unique identifier.
*   **Prime Attribute:** An attribute that is part of *any* candidate key.
*   **Non-prime Attribute:** An attribute that is not part of any candidate key.

> **Try This Yourself 0.1:** In a table $\text{STUDENTS}(\text{SSN, Email, Name})$, if both $\text{SSN}$ and $\text{Email}$ are unique, identify the candidate keys. Which attributes are prime?
> *(Pause and solve before checking: Candidate keys are $\{\text{SSN}\}$ and $\{\text{Email}\}$. Prime attributes: $\text{SSN, Email}$. Non-prime: $\text{Name}$.)*

---

## 1. First Normal Form (1NF): Atomicity

### The "List" Problem
A relation violates 1NF if a single cell contains a "hidden table" or a list of values. 

**The Tension:** It is tempting to put multiple phone numbers in one `Phone` column separated by commas. However, this forces the database to treat the data as a "blob" of text. To find a specific number, the system cannot use an index; it must perform a slow, full-string scan of every row.

**Formal Definition:** A relation $R$ is in **1NF** if and only if the domain of each attribute contains only **atomic** (indivisible) values.

### Worked Example: Healthcare Records
**Scenario:** $\text{PATIENTS}(\underline{\text{PatientID}}, \text{Name, Medications}})$

| PatientID | Name | Medications |
| :--- | :--- | :--- |
| 101 | Alice | Lisinopril, Metformin |
| 102 | Bob | Atorvastatin |

**Violation:** The `Medications` column is a list, not an atom.
**Resolution:** Decompose the multi-valued attribute into its own relation.
1. $\text{PATIENT\_INFO}(\underline{\text{PatientID}}, \text{Name})$
2. $\text{PATIENT\_MEDS}(\underline{\text{PatientID, Medication}})$

**Innovation Note:** Atomicity is relative to the **application's needs**. If you store `FullAddress` as one string but your business requires reporting by `ZipCode`, the `FullAddress` is not atomic for your purpose and must be split.

> **Try This Yourself 1.1:** A table `ORDERS` has a column `Items` containing JSON arrays of products. Is this in 1NF? Why?

---

## 2. Second Normal Form (2NF): Full Dependency

### The "Partial" Problem
2NF is only relevant for tables with **composite keys**. A violation occurs when an attribute is determined by only *part* of the key.

**Analogy:** Imagine a "Passport" for a trip. The passport (the key) consists of $\{\text{TravelerID, Destination}\}$. To know the `TravelerName`, you only need the `TravelerID`; the `Destination` is irrelevant. The `TravelerName` is "partially dependent" on the key.

### Formal Definition
A relation $R$ is in **2NF** if:
1. It is in 1NF.
2. Every non-prime attribute is **fully functionally dependent** on every candidate key (no partial dependencies).

### Worked Example: Logistics
**Scenario:** $\text{INVENTORY}(\underline{\text{WarehouseID, ProductID}}, \text{WarehouseAddress, Quantity})$
*   **Candidate Key:** $\{\text{WarehouseID, ProductID}\}$
*   **FDs:**
    1. $\{\text{WarehouseID, ProductID}\} \to \text{Quantity}$ (Full dependency $\checkmark$)
    2. $\text{WarehouseID} \to \text{WarehouseAddress}$ (Partial dependency $\times$)

**Analysis:** `WarehouseAddress` doesn't care which product is being stored; it only cares about the warehouse. This creates redundancy: the address is repeated for every product in that warehouse.

**Decomposition:**
1. $R_1(\underline{\text{WarehouseID}}, \text{WarehouseAddress})$
2. $R_2(\underline{\text{WarehouseID, ProductID}}, \text{Quantity})$

> **Quick Check 2.1:** If a table has a single-attribute candidate key (e.g., just `UserID`), can it violate 2NF?
> *(Answer: No. With only one attribute, there are no "proper subsets" to depend on. 1NF $\to$ 2NF automatically.)*

---

## 3. Third Normal Form (3NF): Transitive Dependencies

### The "Middleman" Problem
3NF requires that non-prime attributes depend on the key, and *only* the key. A violation occurs when an attribute depends on the key via a "middleman" attribute.

**Analogy:** Think of a chain of command. $\text{Soldier} \to \text{Captain} \to \text{General}$. The Soldier knows who their Captain is, and the Captain knows who the General is. The Soldier "depends" on the General, but only *transitively* through the Captain. In a database, this "chain" creates anomalies.

### Formal Definition
A relation $R$ is in **3NF** if:
1. It is in 2NF.
2. For every non-trivial FD $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.

### Worked Example: Fintech
**Scenario:** $\text{ACCOUNTS}(\underline{\text{AccountID}}, \text{BranchID, BranchCity})$
*   **Candidate Key:** $\{\text{AccountID}\}$
*   **FDs:**
    1. $\text{AccountID} \to \text{BranchID}$ (Determinant is a superkey $\checkmark$)
    2. $\text{BranchID} \to \text{BranchCity}$ (Determinant `BranchID` is not a superkey, and `BranchCity` is not prime $\times$)

**Analysis:** `BranchCity` is determined by `BranchID`, which is determined by `AccountID`. This is a transitive dependency. If you delete the last account in a city, you lose the knowledge that the branch exists in that city.

**Decomposition:**
1. $R_1(\underline{\text{AccountID}}, \text{BranchID})$
2. $R_2(\underline{\text{BranchID}}, \text{BranchCity})$

---

## 4. Boyce-Codd Normal Form (BCNF): The Determinant Rule

### The "Overlapping Key" Problem
3NF has a "loophole": it allows $X \to A$ if $A$ is a prime attribute. BCNF closes this loophole. BCNF is only necessary when you have **multiple, overlapping candidate keys**.

**The Tension:** Can a table be in 3NF but still have anomalies? Yes. When a prime attribute is determined by something other than a superkey, we still have redundancy.

### Formal Definition
A relation $R$ is in **BCNF** if, for every non-trivial functional dependency $X \to A$, $X$ is a superkey. (Essentially: "The determinant must be a candidate key.")

### Worked Example: Consultant Assignments
**Scenario:** $\text{ASSIGNMENTS}(\underline{\text{Client, Consultant}}, \text{Specialty}})$
**Constraints:**
1. A client has only one consultant per specialty.
2. Each consultant has only one specialty.

**FDs:**
1. $\{\text{Client, Specialty}\} \to \text{Consultant}$
2. $\text{Consultant} \to \text{Specialty}$

**Candidate Keys:** $K_1 = \{\text{Client, Specialty}\}$ and $K_2 = \{\text{Client, Consultant}\}$.
**Analysis:**
*   **3NF Check:** In $\text{Consultant} \to \text{Specialty}$, `Specialty` is prime (it's part of $K_1$). 3NF is satisfied.
*   **BCNF Check:** In $\text{Consultant} \to \text{Specialty}$, the determinant `Consultant` is **not** a superkey. BCNF is violated.

**Decomposition:**
1. $R_1(\underline{\text{Consultant}}, \text{Specialty})$
2. $R_2(\underline{\text{Client, Consultant}})$

---

## 5. Synthesis and Strategy

### The Normalization Trade-off
Normalization is not a "free lunch." It is a trade-off between **Write-Integrity** and **Read-Speed**.

| Strategy | Focus | Structure | Trade-off |
| :--- | :--- | :--- | :--- |
| **Normalization** | Write-Integrity | Many small tables | More `JOINs` $\to$ Slower Reads |
| **Denormalization** | Read-Performance | Few large tables | Redundancy $\to$ Risk of Anomalies |

### Comprehensive Exercise: Step-by-Step
**Task:** Decompose $\text{PROJECTS}(\underline{\text{EmpID, ProjectID}}, \text{EmpName, ProjectName, ProjectManager, ManagerPhone})$
**Given FDs:**
- $\text{EmpID} \to \text{EmpName}$
- $\text{ProjectID} \to \text{ProjectName}$
- $\text{ProjectID} \to \text{ProjectManager}$
- $\text{ProjectManager} \to \text{ManagerPhone}$

**Step 1: 1NF $\to$ 2NF (Remove Partial Dependencies)**
The candidate key is $\{\text{EmpID, ProjectID}\}$.
*   `EmpName` depends only on `EmpID`.
*   `ProjectName` and `ProjectManager` depend only on `ProjectID`.
*   **Decomposition:**
    - $\text{EMPLOYEES}(\underline{\text{EmpID}}, \text{EmpName})$
    - $\text{PROJECT\_BASE}(\underline{\text{ProjectID}}, \text{ProjectName, ProjectManager, ManagerPhone})$
    - $\text{ASSIGNMENTS}(\underline{\text{EmpID, ProjectID}})$

**Step 2: 2NF $\to$ 3NF (Remove Transitive Dependencies)**
Analyze $\text{PROJECT\_BASE}$. We have $\text{ProjectID} \to \text{ProjectManager}$ and $\text{ProjectManager} \to \text{ManagerPhone}$.
*   `ManagerPhone` is determined by `ProjectManager` (the middleman).
*   **Decomposition:**
    - $\text{PROJECTS}(\underline{\text{ProjectID}}, \text{ProjectName, ProjectManager})$
    - $\text{MANAGERS}(\underline{\text{ProjectManager}}, \text{ManagerPhone})$

**Final Schema:** $\{\text{EMPLOYEES, PROJECTS, MANAGERS, ASSIGNMENTS}\}$. All determinants are now superkeys; the schema is in BCNF.