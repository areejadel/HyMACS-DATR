### The Core Paradox: The Price of a Single Fact

Imagine architecting a global logistics system. In a "flat" table design, every shipment row contains the `WarehouseAddress`. If 10 million shipments originate from the "North-East Hub," that address is stored 10 million times.

While this design appears efficient for retrieval, it creates a systemic crisis during updates. If the warehouse moves, the system faces two conflicting outcomes:
1. **Read Performance:** Queries to find a package's destination are fast because the address is embedded in the row, eliminating the need for joins.
2. **Write Integrity:** Updating the address requires modifying 10 million rows. If the system crashes mid-update, the database will claim the warehouse exists in two different locations simultaneously.

This is the **Normalization Paradox**: increasing data flattening for read speed increases the risk of data corruption during writes. **Normalization** is the formal process of ensuring every single fact is stored exactly once, transforming a database from a simple storage bucket into a self-enforcing system of logical integrity.

---

### Learning Objectives

By the end of this lecture, you will be able to:
1. **Calculate** candidate keys using attribute closure to identify unique identifiers.
2. **Detect** violations of 1NF, 2NF, 3NF, and BCNF by analyzing functional dependencies.
3. **Decompose** non-normalized relations into a set of normalized relations while preserving dependencies and ensuring lossless joins.
4. **Evaluate** the engineering trade-offs between BCNF and denormalization based on OLTP vs. OLAP workloads.

---

### 1. Prerequisites: Functional Dependencies and Keys

Before decomposing a table, we must define the mathematical rules governing the data.

#### Functional Dependencies
A functional dependency (FD) is a "lookup rule." If a Student ID always maps to exactly one legal name, the ID "determines" the name.

**Analogy:** Think of an FD as a **deterministic function** in programming. If you pass the same input ($X$) into the function, you must always get the same output ($Y$). If `StudentID` 101 returns "Alice" today and "Bob" tomorrow, the functional dependency is broken.

**Formal Definition:** In a relation $R$, a functional dependency $X \to Y$ holds if, for all pairs of tuples $t_1, t_2$ in $R$, $t_1[X] = t_2[X]$ implies $t_1[Y] = t_2[Y]$.
- $X$ is the **determinant**.
- $Y$ is the **dependent**.

#### Attribute Closure and Candidate Keys
A **Candidate Key** is a minimal set of attributes that uniquely identifies every other attribute in a row. To identify candidate keys, we use **Attribute Closure ($K^+$)**: the set of all attributes reachable by following the FDs starting from set $K$.

**Worked Example: Key Calculation**
Consider the relation $\text{Enrollment}(\text{Student, Course, Instructor, Room})$ with the following FDs:
- $FD_1: \{\text{Student, Course}\} \to \text{Instructor}$
- $FD_2: \text{Instructor} \to \text{Course}$
- $FD_3: \text{Instructor} \to \text{Room}$

To determine if $\{\text{Student, Instructor}\}$ is a candidate key:
1. **Initialize the set:** $\{\text{Student, Instructor}\}$
2. **Apply $FD_2$:** Since $\text{Instructor}$ is present, add $\text{Course}$. Set: $\{\text{Student, Instructor, Course}\}$
3. **Apply $FD_3$:** Since $\text{Instructor}$ is present, add $\text{Room}$. Set: $\{\text{Student, Instructor, Course, Room}\}$
4. **Verify Minimality:** 
   - $\{\text{Instructor}\}^+ = \{\text{Instructor, Course, Room}\}$ (Missing $\text{Student}$)
   - $\{\text{Student}\}^+ = \{\text{Student}\}$ (Missing all other attributes)
5. **Conclusion:** Because the closure contains all attributes and no proper subset does, $\{\text{Student, Instructor}\}$ is a **Candidate Key**.

**Try This Yourself:**
Given $\text{Order}(\underline{\text{OrderID, ProductID}}, \text{Quantity, Price})$, where $\text{ProductID} \to \text{Price}$. 
1. Calculate $\{\text{OrderID, ProductID}\}^+$.
2. Is $\{\text{OrderID, ProductID}\}$ a candidate key? Why?
3. Is $\{\text{OrderID}\}$ a candidate key?

---

### 2. First Normal Form (1NF): Atomicity

Having defined keys and dependencies, we address the most basic requirement of relational design: atomicity.

#### The Problem of Non-Atomic Values
If a column `Tags` contains a comma-separated string such as `"Electronics, Sale, Refurbished"`, the database cannot use standard indexing to find "Sale" items. It must perform a full table scan using string searches (e.g., `LIKE '%Sale%'`), significantly degrading performance.

**Cross-Domain Link:** This is essentially a **type mismatch**. A relational column is intended to be a "scalar" (a single value), but a comma-separated list is an "array." Using a string to simulate an array forces the database to treat structured data as unstructured text.

#### Formal Definition
A relation is in **1NF** if the domain of each attribute contains only **atomic** (indivisible) values and contains no repeating groups.

**Worked Example: E-commerce Product Tags**
- **Violation:** $\text{Products}(\underline{\text{ProductID}}, \text{ProductName, Tags})$ where $\text{Tags}$ is a multi-valued list.
- **Decomposition:** Move the multi-valued attribute into a separate relation.
  1. $\text{Product}(\underline{\text{ProductID}}, \text{ProductName})$
  2. $\text{ProductTags}(\underline{\text{ProductID, Tag}})$

**Note on Atomicity:** Atomicity is defined by the application's requirements. A `FullAddress` string is atomic if the application only prints labels; it becomes non-atomic if the application must generate reports based on `ZipCode`.

**Try This Yourself:**
Imagine a table `UserProfiles` with columns `UserID`, `Username`, and `PhoneNumbers` (where `PhoneNumbers` is a list). 
1. Explain why this violates 1NF.
2. Propose a 1NF-compliant schema.
3. **Challenge:** If you add columns `Phone1`, `Phone2`, and `Phone3` instead of a list, is it technically in 1NF? Why is this still a "repeating group" in spirit?

---

### 3. Second Normal Form (2NF): Partial Dependencies

Once atomicity is ensured, we address dependencies within composite keys.

#### The "Half-Key" Problem
2NF is relevant only when a relation has a **composite key**. A violation occurs when a non-prime attribute depends on only a subset of that key. 

**Analogy:** Imagine a **Joint Venture Agreement** signed by two partners (the composite key). If a clause in the agreement describes the "Home Address of Partner A," that clause doesn't depend on the *partnership*—it depends only on *Partner A*. If the partnership dissolves, the information about Partner A's address is unnecessarily deleted or duplicated across every other venture Partner A joins.

#### Formal Definition
A relation is in **2NF** if it is in 1NF and **no non-prime attribute is partially dependent on any candidate key**. A prime attribute is any attribute that is part of at least one candidate key.

**Worked Example: Logistics Management**
Consider $\text{Shipment}(\underline{\text{ShipmentID, ItemID}}, \text{Quantity, ItemDescription})$.
1. **Identify the Key:** $\{\text{ShipmentID, ItemID}\}$
2. **Analyze Dependencies:**
   - $\{\text{ShipmentID, ItemID}\} \to \text{Quantity}$ (Full dependency: $\checkmark$)
   - $\text{ItemID} \to \text{ItemDescription}$ (Partial dependency: $\text{ItemDescription}$ depends only on $\text{ItemID}$, not the whole key: $\times$)
3. **Decomposition:**
   - $\text{ShipmentDetails}(\underline{\text{ShipmentID, ItemID}}, \text{Quantity})$
   - $\text{Items}(\underline{\text{ItemID}}, \text{ItemDescription})$

**Check Your Understanding:**
In $\text{CourseRegistration}(\underline{\text{StudentID, CourseID}}, \text{Grade, CourseName})$, which attribute causes a 2NF violation? What happens to `CourseName` if we delete all students from a specific course?

---

### 4. Third Normal Form (3NF): Transitive Dependencies

After eliminating partial dependencies, we must remove indirect dependencies between non-prime attributes.

#### The "Hidden" Chain
3NF prevents transitive dependencies, where the Key determines Attribute A, and Attribute A determines Attribute B ($\text{Key} \to A \to B$). 

**Tension:** If we only stop at 2NF, we have a "hidden" dependency. If we delete the last employee in a department, we don't just lose the employee record—we accidentally delete the fact that the department exists and who its head is. This is a **Deletion Anomaly**.

#### Formal Definition
A relation is in **3NF** if it is in 2NF and every non-prime attribute is **non-transitively dependent** on every candidate key.
**The Golden Rule:** For every non-trivial FD $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.

**Worked Example: Human Resources**
$\text{Employee}(\underline{\text{EmpID}}, \text{Name, DeptID, DeptHead})$
1. **Detection:** $\text{EmpID} \to \text{DeptID}$ and $\text{DeptID} \to \text{DeptHead}$.
2. **Analysis:** $\text{DeptHead}$ is determined by $\text{DeptID}$, which is not a superkey. This is a transitive chain.
3. **Decomposition:**
   - $\text{Employee}(\underline{\text{EmpID}}, \text{Name, DeptID})$
   - $\text{Department}(\underline{\text{DeptID}}, \text{DeptHead})$

**Try This Yourself:**
Given $\text{Store}(\underline{\text{StoreID}}, \text{City, ZipCode})$ and the FD $\text{ZipCode} \to \text{City}$. 
1. Is this in 3NF? 
2. If you change the city name for a specific ZipCode, how many rows must you update in a non-3NF table? How many in a 3NF table?

---

### 5. Boyce-Codd Normal Form (BCNF)

BCNF is a stricter version of 3NF that addresses anomalies arising from overlapping candidate keys.

#### The Overlapping Key Loophole
3NF allows a dependency $X \to A$ if $A$ is a prime attribute (part of *some* candidate key). BCNF removes this exception. 

**The Framing:** While 3NF handles dependencies where "non-keys depend on keys," BCNF handles the rare case where "parts of keys depend on other parts of keys." It is the "final polish" that ensures the determinant is **always** a superkey, leaving no room for ambiguity.

#### Formal Definition
A relation is in **BCNF** if for every non-trivial functional dependency $X \to Y$, $X$ must be a superkey.

**Worked Example: Academic Scheduling**
$\text{Class}(\underline{\text{Student, Course}}, \text{Instructor})$
- **Constraints:** Each instructor teaches only one course; students can take multiple courses.
- **FDs:**
  1. $\{\text{Student, Course}\} \to \text{Instructor}$ (Determinant is a superkey: $\checkmark$)
  2. $\text{Instructor} \to \text{Course}$ (Determinant is **not** a superkey: $\times$)
- **Analysis:** This is in 3NF because $\text{Course}$ is prime. It violates BCNF because $\text{Instructor}$ is a determinant but not a superkey.
- **Decomposition:**
  - $\text{InstructorCourse}(\underline{\text{Instructor}}, \text{Course})$
  - $\text{StudentInstructor}(\underline{\text{Student, Instructor}})$

**Check Your Understanding:**
Why is BCNF considered "stronger" than 3NF? Can a table be in BCNF but not in 3NF? (Hint: Look at the definitions).

---

### 6. Summary and Engineering Trade-offs

#### Normalization Summary Table

| Normal Form | Target | Key Rule | Typical Fix |
| :--- | :--- | :--- | :--- |
| **1NF** | Atomicity | No lists or repeating groups | Create a bridge table |
| **2NF** | Partial Dependencies | Non-prime $\to$ Whole Key | Isolate partial dependencies |
| **3NF** | Transitive Dependencies | No non-prime $\to$ non-prime | Isolate transitive chains |
| **BCNF** | Overlapping Keys | Every determinant must be a superkey | Separate overlapping attributes |

#### OLTP vs. OLAP Workloads
Normalization is not a "perfect state" to be reached, but a slider between **Write Integrity** and **Read Latency**.

**1. OLTP (Online Transactional Processing)**
- **Scenario:** A banking app processing 10,000 balance updates per second.
- **Priority:** Write speed and data integrity.
- **Strategy:** **Target BCNF/3NF.** Ensuring a fact is stored in exactly one place avoids update anomalies and minimizes the locking overhead of updating redundant rows.

**2. OLAP (Online Analytical Processing)**
- **Scenario:** A data warehouse analyzing 5 years of sales trends across 1 billion rows.
- **Priority:** Read speed and throughput.
- **Strategy:** **Denormalization (e.g., Star Schema).** At this scale, joining 10 normalized tables is computationally expensive. Data is deliberately duplicated into "Wide Tables" to eliminate joins.

#### Limitations and Edge Cases
- **Dependency Preservation:** Decomposing to BCNF can sometimes "lose" a functional dependency. If a dependency cannot be checked without joining two tables, designers may choose to remain in 3NF to ensure constraints can be enforced efficiently.
- **Join Explosion:** Over-normalization can lead to a "Join Explosion," where a simple query requires numerous joins, degrading performance.
- **Nulls:** Normalization increases the number of tables, which may increase `NULL` values in optional relationships, necessitating the use of `OUTER JOINs`.