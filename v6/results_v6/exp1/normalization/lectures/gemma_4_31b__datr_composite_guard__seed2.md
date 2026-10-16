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

#### Worked Example: Fixing 1NF
**Scenario: E-commerce Product Tags**
A product table stores tags as a comma-separated string to simplify the UI.
**Violation:**
| ProductID | Name | Tags |
| :--- | :--- | :--- |
| P1 | Smartphone | Electronics, Mobile, 5G |
| P2 | Laptop | Electronics, Computing |

If a marketing manager asks for "all products tagged with 'Mobile'", the database must perform a slow `LIKE '%Mobile%'` scan, which cannot use standard indexes and may accidentally return "MobileHome" as a match.

**The Fix:** Decompose the multi-valued attribute into its own relation.
**Table: Product** ($\underline{\text{ProductID}}$, $\text{Name}$)
**Table: ProductTags** ($\underline{\text{ProductID, Tag}}$)

**Innovation Note:** 1NF is about the *granularity of access*. If your business logic never needs to search by a specific phone number, a string is fine. But the moment you need to "Find all students with area code 555," you have a 1NF violation.

---

### 3. Second Normal Form (2NF): Partial Dependencies

**The Tension:** If your primary key is "composite" (made of multiple columns), you might accidentally store information that only relates to *part* of that key. This leads to redundancy.

#### Formal Definition
A relation is in **2NF** if:
1. It is in 1NF.
2. Every non-prime attribute is **fully functionally dependent** on every candidate key.

**The "Partial Dependency" Trap:** $X \to A$, where $X$ is only a *piece* of the key $K$.

#### Worked Example: Fixing 2NF
**Scenario: Healthcare Clinic Appointments**
A table tracks appointments where the key is the combination of Patient and Date.
$\text{Appointment}(\underline{\text{PatientID, Date}}, \text{PatientName, Date, ClinicRoom, RoomCapacity})$
- **Candidate Key:** $\{\text{PatientID, Date}\}$
- $\text{FD1: } \text{PatientID} \to \text{PatientName}$ (Partial Dependency: $\text{PatientName}$ depends only on the patient, not the date).
- $\text{FD2: } \text{ClinicRoom} \to \text{RoomCapacity}$ (Partial Dependency: $\text{RoomCapacity}$ depends on the room, not the patient).

**The Anomaly:** If a patient cancels their appointment, we might delete the only record of a specific room's capacity, leading to a **Deletion Anomaly**.

**The Fix:** Separate the entities.
1. $\text{Patient}(\underline{\text{PatientID}}, \text{PatientName})$
2. $\text{Room}(\underline{\text{ClinicRoom}}, \text{RoomCapacity})$
3. $\text{Appointment}(\underline{\text{PatientID, Date}}, \text{ClinicRoom})$

**Cross-Domain Link:** This is like **Separation of Concerns** in software engineering. Don't put "Employee" logic and "Project" logic in the same "class" (table) if they can exist independently.

---

### 4. Third Normal Form (3NF): Transitive Dependencies

**The Tension:** Even if an attribute depends on the *whole* key, it might be doing so "through" another attribute. This creates a hidden chain of dependency.

#### Formal Definition
A relation is in **3NF** if:
1. It is in 2NF.
2. No non-prime attribute is **transitively dependent** on any candidate key.

**The "Chain" Analogy:** $\text{Key} \to \text{Attribute A} \to \text{Attribute B}$. 
$\text{Attribute B}$ is transitively dependent on the key. It's like a game of telephone; if $\text{Attribute A}$ disappears, the link to $\text{Attribute B}$ is severed.

#### Worked Example: Fixing 3NF
**Scenario: Corporate Asset Management**
A table tracks company laptops and the technical support lead for the department owning the laptop.
$\text{Asset}(\underline{\text{AssetID}}, \text{Model, DeptID, DeptSupportLead})$
- $\text{AssetID} \to \text{DeptID} \to \text{DeptSupportLead}$

**The Anomaly:** If the company replaces all laptops in the "Accounting" department, and the last laptop is deleted, we lose the information about who the `DeptSupportLead` for Accounting is. This is a **Deletion Anomaly**. Conversely, if we want to assign a lead to a new department that hasn't bought laptops yet, we cannot do so without inventing a fake `AssetID` (**Insertion Anomaly**).

**The Fix:**
1. $\text{ASSET}(\underline{\text{AssetID}}, \text{Model, DeptID})$
2. $\text{DEPARTMENT}(\underline{\text{DeptID}}, \text{DeptSupportLead})$

**Try this yourself:** In $\text{R}(\text{A, B, C})$ with $\text{FDs: } A \to B, B \to C$, is this in 3NF? Why?

---

### 5. Boyce-Codd Normal Form (BCNF)

**The Tension:** 3NF is usually enough, but it has a loophole: it allows a determinant to be a non-key, as long as the dependent attribute is "prime." BCNF closes this loophole.

#### Formal Definition
A relation is in **BCNF** if for every non-trivial functional dependency $X \to Y$, $X$ **must** be a superkey. 

**The "No Exceptions" Rule:** BCNF says: "If you are determining something, you must be a key. Period."

#### Worked Example: 3NF vs. BCNF
**Scenario: Specialized Consulting Firm**
A firm assigns consultants to clients for specific services. Each consultant specializes in only one service, but a service can have many consultants.
$\text{CONSULTING}(\underline{\text{Client, Service}}, \text{Consultant})$
- $\text{FD1: } \{\text{Client, Service}\} \to \text{Consultant}$
- $\text{FD2: } \text{Consultant} \to \text{Service}$
- **Keys:** $\{\text{Client, Service}\}$ and $\{\text{Client, Consultant}\}$.
- **Prime Attributes:** All three.

**The Analysis:**
- **Is it 3NF?** Yes. In FD2, $\text{Consultant}$ is not a key, but $\text{Service}$ is prime. 3NF allows this.
- **Is it BCNF?** No. In FD2, $\text{Consultant}$ is the determinant but is not a superkey.

**The Anomaly:** If we want to record that "Consultant Sarah" specializes in "Tax Law" before she is assigned to a client, we cannot (Insertion Anomaly). If we remove the only client Sarah has, we lose the knowledge that Sarah specializes in Tax Law (Deletion Anomaly).

**The Fix:**
1. $\text{CONSULTANT\_SPECIALTY}(\underline{\text{Consultant}}, \text{Service})$
2. $\text{CLIENT\_ASSIGNMENT}(\underline{\text{Client, Consultant}})$

**Final Trade-off:** BCNF is the "purest" form, but it can sometimes make it impossible to preserve all functional dependencies in a single join. In the real world, we balance BCNF against **Join Overhead**—the more we decompose, the more `JOIN` operations we need, which can slow down reads.