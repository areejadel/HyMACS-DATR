### The Core Paradox: The Cost of Storage vs. The Cost of Truth
Imagine you are designing a system for a global logistics company. You store the `WarehouseAddress` every time a `Package` is listed. It seems efficient—one table, one query. But then, the warehouse moves. You must update 10 million package rows. If the system crashes halfway through, your database now claims the same warehouse exists in two different cities. 

This is the fundamental tension of database design: **Redundancy is a performance shortcut that creates "data lies" (anomalies).** Normalization is the mathematical process of ensuring that every single fact is stored exactly once.

### Learning Objectives
By the end of this lecture, you will be able to:
1. **Identify** functional dependencies and calculate candidate keys for a given relation.
2. **Detect** violations of 1NF, 2NF, 3NF, and BCNF in a database schema.
3. **Decompose** a non-normalized relation into a set of normalized relations to eliminate redundancy and anomalies.
4. **Evaluate** the trade-offs between high normalization (BCNF) and denormalization regarding system performance.

---

### 1. Prerequisites: Functional Dependencies and Keys

Before we can "clean" a table, we need a formal way to describe how data elements are tethered to one another.

#### Functional Dependencies (FDs)
A **Functional Dependency** $X \to Y$ is a constraint on the data. It means that if two rows have the same value for $X$, they *must* have the same value for $Y$.

**The "Lookup Table" Analogy:** 
Think of an FD as a specialized lookup function. If $\text{StudentID} \to \text{Name}$, then $\text{StudentID}$ is the "input" and $\text{Name}$ is the "output." If you input `ID 101` and get `Alice` in one row, but input `ID 101` and get `Bob` in another, the FD is violated. The "function" has broken.

**Formal Definition:**
A functional dependency $X \to Y$ exists in a relation $R$ if, for every pair of tuples $t_1$ and $t_2$ in $R$, whenever $t_1[X] = t_2[X]$, it must also be the case that $t_1[Y] = t_2[Y]$.

#### Candidate Keys and Prime Attributes
To find redundancy, we must find the "minimal anchors" of the table.

**Candidate Key:**
A set of attributes $K$ is a candidate key if it satisfies:
1. **Uniqueness:** $K \to R$ (The closure of $K$ contains all attributes).
2. **Minimality:** No proper subset of $K$ can determine all attributes.

**Prime Attribute:** An attribute is **prime** if it is a member of *any* candidate key.

#### Worked Example: Finding Keys
Consider $\text{TEACH}(\text{Student, Course, Instructor})$ with:
- $\text{FD1: } \{\text{Student, Course}\} \to \text{Instructor}$
- $\text{FD2: } \text{Instructor} \to \text{Course}$

**The Search:**
1. **Test $\{\text{Student, Course}\}$:** Via FD1, we get $\text{Instructor}$. Result: $\{\text{Student, Course, Instructor}\}$. This is a candidate key.
2. **Test $\{\text{Student, Instructor}\}$:** Via FD2, $\text{Instructor}$ gives us $\text{Course}$. Result: $\{\text{Student, Instructor, Course}\}$. This is also a candidate key.
3. **Identify Prime Attributes:** Since all three attributes appear in at least one key, all are prime.

**Try this yourself:** In $\text{Relation}(\text{A, B, C})$ with $\text{FDs: } A \to B, B \to C$, what is the candidate key? (Answer: $\{A\}$).

---

### 2. First Normal Form (1NF): Atomicity

**The Tension:** We often want to store "lists" in a cell (e.g., tags, phone numbers) because it feels intuitive. However, SQL cannot efficiently query *inside* a comma-separated string.

#### Formal Definition
A relation is in **1NF** if every attribute in every tuple contains only **atomic** (indivisible) values. No multi-valued attributes; no nested tables.

#### Worked Example: Fixing 1NF in E-Commerce
**Violation:** An e-commerce `Order` table where `Products` is a comma-separated string.
| OrderID | Customer | Products |
| :--- | :--- | :--- |
| 5001 | Alice | Laptop, Mouse, Keyboard |

**The Problem:** To calculate total sales for "Mouse," the database must perform a costly `LIKE '%Mouse%'` string scan on every row, which bypasses indexing and slows down as the dataset grows. Furthermore, updating a single product (e.g., changing "Mouse" to "Wireless Mouse") requires complex string manipulation rather than a simple update.

**The Fix:** Decompose into a many-to-many relationship.
**Table: Order** ($\underline{\text{OrderID}}$, $\text{Customer}$)
**Table: OrderItems** ($\underline{\text{OrderID, ProductID}}$)

**Innovation Note:** 1NF is about the *granularity of access*. If your business logic never needs to search by a specific phone number, a string is fine. But the moment you need to "Find all students with area code 555," you have a 1NF violation.

---

### 3. Second Normal Form (2NF): Partial Dependencies

**The Tension:** If your primary key is "composite" (made of multiple columns), you might accidentally store information that only relates to *part* of that key. This creates a scenario where the table is trying to describe two different things at once.

#### Formal Definition
A relation is in **2NF** if:
1. It is in 1NF.
2. Every non-prime attribute is **fully functionally dependent** on every candidate key.

**The "Partial Dependency" Trap:** $X \to A$, where $X$ is only a *piece* of the key $K$.

#### Worked Example: Fixing 2NF in Healthcare
$\text{PatientVisit}(\text{PatientID, VisitDate, PatientName, ClinicName})$
- **Candidate Key:** $\{\text{PatientID, VisitDate}\}$
- $\text{FD1: } \text{PatientID} \to \text{PatientName}$ (Partial Dependency: $\text{PatientName}$ is determined by the patient, regardless of the date of the visit).
- $\text{FD2: } \{\text{PatientID, VisitDate}\} \to \text{ClinicName}$ (Full Dependency).

**The Anomaly:** If a patient visits the clinic 50 times, their name is stored 50 times. If the patient changes their legal name, you must update 50 rows, risking data inconsistency. If the patient is deleted, you lose the history of the clinic visits.

**The Fix:** Separate the entities.
1. $\text{Patient}(\underline{\text{PatientID}}, \text{PatientName})$
2. $\text{Visit}(\underline{\text{PatientID, VisitDate}}, \text{ClinicName})$

**Cross-Domain Link:** This is like **Separation of Concerns** in software engineering. Don't put "Employee" logic and "Project" logic in the same "class" (table) if they can exist independently.

---

### 4. Third Normal Form (3NF): Transitive Dependencies

**The Tension:** Even if an attribute depends on the *whole* key, it might be doing so "through" another attribute. This creates a hidden chain of dependency where the key doesn't actually "own" the data—it just knows who does.

#### Formal Definition
A relation is in **3NF** if:
1. It is in 2NF.
2. No non-prime attribute is **transitively dependent** on any candidate key.

**The "Chain" Analogy:** $\text{Key} \to \text{Attribute A} \to \text{Attribute B}$. 
$\text{Attribute B}$ is transitively dependent on the key. It's like a game of telephone; if $\text{Attribute A}$ disappears, the link to $\text{Attribute B}$ is severed.

#### Worked Example: Fixing 3NF in HR Systems
$\text{Employee}(\underline{\text{EmpID}}, \text{Name, DeptID, DeptName})$
- $\text{EmpID} \to \text{DeptID} \to \text{DeptName}$

**The Anomaly:** 
- **Deletion Anomaly:** If you delete the only employee in "Research," you accidentally delete the fact that the "Research" department exists. 
- **Insertion Anomaly:** You cannot create a new department (e.g., "AI Ethics") without first hiring an employee to "anchor" it.
- **Update Anomaly:** Changing "Research" to "R&D" requires updating every employee in that department.

**The Fix:**
1. $\text{EMP}(\underline{\text{EmpID}}, \text{Name, DeptID})$
2. $\text{DEPARTMENT}(\underline{\text{DeptID}}, \text{DeptName})$

**Try this yourself:** In $\text{R}(\text{A, B, C})$ with $\text{FDs: } A \to B, B \to C$, is this in 3NF? Why?

---

### 5. Boyce-Codd Normal Form (BCNF)

**The Tension:** 3NF is usually enough, but it has a loophole: it allows a determinant to be a non-key, as long as the dependent attribute is "prime." BCNF closes this loophole by demanding a higher standard of accountability.

#### Formal Definition
A relation is in **BCNF** if for every non-trivial functional dependency $X \to Y$, $X$ **must** be a superkey. 

**The "No Exceptions" Rule:** BCNF says: "If you are determining something, you must be a key. Period."

#### Worked Example: 3NF vs. BCNF in Academic Scheduling
$\text{TEACH}(\text{Student, Course, Instructor})$
- $\text{FD1: } \{\text{Student, Course}\} \to \text{Instructor}$
- $\text{FD2: } \text{Instructor} \to \text{Course}$ (Assumption: Each instructor teaches only one specific course).
- **Keys:** $\{\text{Student, Course}\}$ and $\{\text{Student, Instructor}\}$.
- **Prime Attributes:** All three.

**The Analysis:**
- **Is it 3NF?** Yes. In FD2, $\text{Instructor}$ is not a key, but $\text{Course}$ is prime. 3NF allows this.
- **Is it BCNF?** No. In FD2, $\text{Instructor}$ is the determinant but is not a superkey.

**The Anomaly:** We cannot store the fact that "Dr. Smith teaches Physics" until at least one student enrolls in the course. This is an **Insertion Anomaly**. Similarly, if the only student in the Physics class drops out, we lose the information that Dr. Smith is the Physics instructor.

**The Fix:**
1. $\text{TEACHER}(\underline{\text{Instructor}}, \text{Course})$
2. $\text{STUDENT\_INSTRUCTOR}(\underline{\text{Student, Instructor}})$

**Final Trade-off:** BCNF is the "purest" form, but it can sometimes make it impossible to preserve all functional dependencies in a single join. In the real world, we balance BCNF against **Join Overhead**—the more we decompose, the more `JOIN` operations we need, which can slow down reads. In high-throughput read-heavy systems (like Analytics dashboards), architects often intentionally "denormalize" back to 3NF or 2NF to reduce latency.