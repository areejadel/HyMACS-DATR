# Normalization Forms and Database Schema Design (1NF–BCNF)

## Learning Objectives
By the end of this lecture, you will be able to:
1. **Analyze** a database relation to identify update, insertion, and deletion anomalies.
2. **Apply** the rules of 1NF, 2NF, 3NF, and BCNF to determine the normalization state of a given schema.
3. **Decompose** a non-normalized relation into a set of normalized relations while preserving functional dependencies.
4. **Evaluate** the trade-off between BCNF and dependency preservation in real-world system design.

---

## 0. Prerequisites and Intuition

### The Paradox of Redundancy
Imagine you are designing a global logistics system. At first glance, storing everything in one massive table seems convenient—it's just one "source of truth." 
$\text{Shipments}(\text{ShipmentID, CustomerName, CustomerAddress, WarehouseID, WarehouseLocation})$

But here is the paradox: **the more "complete" a single table looks, the more fragile it becomes.** If a warehouse moves from Memphis to Dallas, you don't just update one cell; you must hunt down every single shipment ever sent from that warehouse and update its location. 

**The Tension:** If you miss even one row during this update, your database now claims the warehouse exists in two different cities simultaneously. This is a "corrupted" state. This fragility manifests as three specific anomalies:
- **Update Anomaly:** Inconsistent data caused by partial updates to redundant values.
- **Insertion Anomaly:** You cannot record a new warehouse's existence until you have a shipment to put in it (the "chicken and egg" problem).
- **Deletion Anomaly:** Deleting the last shipment from a warehouse accidentally wipes the warehouse's address from your corporate memory.

**The Goal:** Normalization is the process of ensuring that every "fact" is stored exactly once.

### Functional Dependencies (FDs)
To fix these anomalies, we need a mathematical way to describe how columns "control" one another.

**Analogy: The Digital Fingerprint.** 
A functional dependency $X \to Y$ is like a fingerprint. If I have the fingerprint ($X$), I can uniquely identify the person ($Y$). If two records have the same fingerprint, they *must* be the same person. If they aren't, the fingerprint is not a valid determinant.

**Formal Definition:** A functional dependency $X \to Y$ exists in relation $R$ if, for every pair of tuples $t_1, t_2 \in R$, whenever $t_1[X] = t_2[X]$, then $t_1[Y] = t_2[Y]$.
- $X$ is the **determinant**.
- $Y$ is the **dependent**.

**Example:** In a university database, $\text{StudentID} \to \text{StudentEmail}$. If two rows share the same $\text{StudentID}$, they must share the same $\text{StudentEmail}$.

### Key Terminology
- **Superkey:** A set of attributes $S$ that uniquely identifies every tuple ($S \to \text{all other attributes}$).
- **Candidate Key:** A minimal superkey. (The "leanest" possible identifier).
- **Prime Attribute:** An attribute that is a member of at least one candidate key.
- **Non-prime Attribute:** An attribute that is not part of any candidate key.

**Try This Yourself:** You have a table $\text{Employee}(\text{EmpID, SSN, Name, Salary})$. If both $\text{EmpID}$ and $\text{SSN}$ are unique, how many candidate keys are there? Which attributes are prime?

---

## 1. First Normal Form (1NF): Atomicity

### The Problem of "Hidden" Data
Consider an e-commerce system storing orders:
$\text{Orders}(\text{OrderID, CustomerID, ProductList})$
Where $\text{ProductList}$ contains values such as `"Laptop, Mouse, Keyboard"`.

**The Tension:** This looks organized to a human, but it is a nightmare for a machine. If you want to find all orders containing a "Mouse," the database cannot use an index. It must perform a "Full Table Scan," reading every single string and performing a partial match (e.g., `LIKE '%Mouse%'`). This is the difference between looking up a word in an index (milliseconds) and reading every page of a book to find a word (minutes).

### Formal Definition
A relation is in **1NF** if and only if every attribute in every tuple contains only **atomic** (indivisible) values from its domain.

### Worked Example: Converting to 1NF
**Non-1NF Table:**
| OrderID | CustomerID | Products |
| :--- | :--- | :--- |
| 101 | C1 | Laptop, Mouse |
| 102 | C2 | Keyboard |

To achieve 1NF, we "flatten" the multi-valued attribute.

**1NF Table ($\text{OrderItems}$):**
| OrderID | ProductID |
| :--- | :--- |
| 101 | Laptop |
| 101 | Mouse |
| 102 | Keyboard |

**Cross-Domain Connection:** This is essentially the difference between a **Scalar** (a single value) and a **Vector/Array** (a collection). 1NF mandates that our schema only uses scalars.

**Quick Check 1:** A table stores $\text{User}(\text{UserID, PhoneNumbers})$ where $\text{PhoneNumbers}$ is a JSON array. Is this in 1NF? *(Answer: No; the JSON array is a composite object, not an atomic value.)*

---

## 2. Second Normal Form (2NF): Full Functional Dependency

### The Problem of "Partial" Truths
2NF focuses on **composite keys** (keys made of more than one column). A violation occurs when a piece of information depends on only *part* of the key.

**Analogy: The Wrong Address.**
Imagine a key is a coordinate $(\text{Latitude, Longitude})$. If a piece of data (like "Country") only depends on the $\text{Latitude}$, you are storing the country name millions of times for every single longitude at that latitude. That is a partial dependency.

**Concrete Example:**
$\text{CourseAssignment}(\underline{\text{StudentID, CourseID}}, \text{InstructorName})$
Assume each course is taught by only one instructor.
Here, $\text{InstructorName}$ is determined by $\text{CourseID}$ alone. The $\text{StudentID}$ is "along for the ride" but doesn't actually determine who the instructor is.

### Formal Definition
A relation is in **2NF** if:
1. It is in 1NF.
2. No non-prime attribute is **partially functionally dependent** on any candidate key.

### Worked Example: Decomposition
**Relation:** $\text{CourseAssignment}(\underline{\text{StudentID, CourseID}}, \text{InstructorName, InstructorOffice})$
1. **Identify Keys:** $\{\text{StudentID, CourseID}\}$.
2. **Identify FDs:**
   - $\{\text{StudentID, CourseID}\} \to \text{InstructorName}$ (Full)
   - $\text{CourseID} \to \text{InstructorName}$ (Partial)
   - $\text{CourseID} \to \text{InstructorOffice}$ (Partial)
3. **Decompose:** Split the "Partial Truth" into its own table.
   - $R_1(\underline{\text{StudentID, CourseID}})$
   - $R_2(\underline{\text{CourseID}}, \text{InstructorName, InstructorOffice})$

**Quick Check 2:** If a table has a single-attribute primary key (e.g., $\text{EmpID}$), can it violate 2NF? *(Answer: No. A single attribute has no "proper subsets," so partial dependency is mathematically impossible.)*

---

## 3. Third Normal Form (3NF): Eliminating Transitive Dependencies

### The "Middleman" Problem
3NF prevents non-prime attributes from depending on other non-prime attributes. This is called a **transitive dependency**.

**Analogy: The Chain of Command.**
In a military hierarchy: $\text{Soldier} \to \text{Captain} \to \text{General}$.
If you store the General's name in the Soldier's record, you have a transitive dependency. If the General changes, you must update every single soldier in that entire chain. To fix this, you store the General's name only in the Captain's record.

**Concrete Example:**
$\text{Employee}(\underline{\text{EmpID}}, \text{DeptID, DeptName})$
- $\text{EmpID} \to \text{DeptID}$ (The employee belongs to a department)
- $\text{DeptID} \to \text{DeptName}$ (The department has a name)
The $\text{DeptName}$ is essentially "piggybacking" on $\text{EmpID}$ via $\text{DeptID}$.

### Formal Definition
A relation is in **3NF** if:
1. It is in 2NF.
2. For every non-trivial functional dependency $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.

### Worked Example: Decomposition
**Relation:** $\text{Employee}(\underline{\text{EmpID}}, \text{DeptID, DeptName, DeptManager})$
1. **Identify Keys:** $\{\text{EmpID}\}$.
2. **Identify FDs:** $\text{EmpID} \to \text{DeptID}$ and $\text{DeptID} \to \{\text{DeptName, DeptManager}\}$.
3. **Analysis:** $\text{DeptID}$ is not a superkey, and $\text{DeptName}$ is not prime. Violation!
4. **Decompose:**
   - $R_1(\underline{\text{EmpID}}, \text{DeptID})$
   - $R_2(\underline{\text{DeptID}}, \text{DeptName, DeptManager})$

**Quick Check 3:** In $R(\underline{A, B}, C, D)$, we have $A \to C$ and $C \to D$. Is this in 3NF? *(Answer: No. $C \to D$ is a transitive dependency; $C$ is not a superkey and $D$ is not prime.)*

---

## 4. Boyce-Codd Normal Form (BCNF): The Determinant Rule

### The "Overlapping Key" Edge Case
BCNF is a stricter version of 3NF. It handles cases where candidate keys "overlap" (share attributes). In 3NF, we allow a dependency if the dependent is a prime attribute. BCNF says: **"I don't care if the dependent is prime; the determinant must be a superkey."**

**Concrete Example:**
$\text{Appointment}(\underline{\text{Patient, Time}}, \text{Doctor})$
- **Rule 1:** A patient can see only one doctor at a time: $\{\text{Patient, Time}\} \to \text{Doctor}$.
- **Rule 2:** Each doctor works only one specific time slot: $\text{Doctor} \to \text{Time}$.

**The Tension:** 
Candidate Keys: $\{\text{Patient, Time}\}$ and $\{\text{Patient, Doctor}\}$.
Look at $\text{Doctor} \to \text{Time}$. 
- Is it 3NF? **Yes.** $\text{Time}$ is a prime attribute (it's part of a candidate key).
- Is it BCNF? **No.** The determinant $\text{Doctor}$ is NOT a superkey.

**Why does this matter?** Because we can now enter a doctor and their time slot into the table without a patient, but if we do, we might create redundancy or anomalies regarding which doctor is available when.

### Formal Definition
A relation is in **BCNF** if, for every non-trivial functional dependency $X \to A$, $X$ is a superkey.

### Worked Example: Decomposition
1. **Identify FDs:** $\{\text{Patient, Time}\} \to \text{Doctor}$ and $\text{Doctor} \to \text{Time}$.
2. **Analyze:** $\text{Doctor} \to \text{Time}$ violates BCNF.
3. **Decompose:**
   - $R_1(\underline{\text{Doctor}}, \text{Time})$
   - $R_2(\underline{\text{Patient, Doctor}})$

---

## 5. Limitations, Pitfalls, and Trade-offs

### The BCNF Dilemma: Dependency Preservation
Decomposing to BCNF can be a "pyrrhic victory." In the $\text{Appointment}$ example, the constraint $\{\text{Patient, Time}\} \to \text{Doctor}$ is now split across two tables. 
To check if a patient is double-booked, the database can no longer just look at one row; it must **JOIN** the tables. 

**The Trade-off:** If your system is "Write-Heavy," go to BCNF to prevent anomalies. If your system is "Read-Heavy" and the join is too expensive, you may choose to stop at 3NF.

### Common Pitfalls
1. **Join Explosion:** Over-normalization turns a simple query into a 10-table join, which can kill performance.
2. **The "Email" Trap:** Never assume an attribute is a key because it "looks" unique. Always ask the business: "Can one user have two emails?" If yes, $\text{Email}$ is not a key.

### OLTP vs. OLAP: When to Break the Rules
- **OLTP (Online Transaction Processing):** High-frequency writes (e.g., Banking). **Strict BCNF/3NF** is mandatory to prevent data corruption.
- **OLAP (Online Analytical Processing):** Massive reads (e.g., Data Warehousing). **Denormalization** is the goal. We intentionally introduce redundancy (Star Schemas) to eliminate joins and accelerate aggregation.

**Try This Yourself:** Think of a social media "Like" system. Would you normalize the "Total Like Count" for a post, or store it as a redundant value in the Post table? Why?