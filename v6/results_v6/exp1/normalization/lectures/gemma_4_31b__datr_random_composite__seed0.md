### Lecture: Normalization and Database Schema Design (1NF to BCNF)

#### The Cost of Redundancy: Why Normalize?
Imagine you are designing a database for a global logistics company. You store the `WarehouseAddress` every time a `Package` is assigned to a warehouse. If a warehouse moves across the street, you must update 10,000 package records. If you miss one, your data is now contradictory: the warehouse exists in two places at once. 

This is the **Update Anomaly**. It is not just a storage waste; it is a systemic risk where the database ceases to be a "source of truth" and becomes a collection of conflicting claims. Normalization is the process of surgically removing these redundancies to ensure that **every piece of data is stored in exactly one place**.

---

#### 1. Prerequisites: The Logic of Dependencies
Before we can fix a schema, we need a mathematical way to describe how attributes "cling" to one another.

**Functional Dependency (FD)**
A functional dependency $X \to Y$ exists if, for any two tuples $t_1$ and $t_2$ in a relation $R$, $t_1[X] = t_2[X]$ implies $t_1[Y] = t_2[Y]$. This means the value of $X$ uniquely determines the value of $Y$.

**The Analogy: The Digital Fingerprint**
Think of a Functional Dependency as a "lookup guarantee." If $X \to Y$, then $X$ acts like a fingerprint; once you identify the fingerprint ($X$), the identity ($Y$) is locked in. There is no ambiguity.

**Core Terminology**
*   **Determinant:** The attribute set $X$ on the left side of the dependency.
*   **Dependent:** The attribute set $Y$ on the right side of the dependency.
*   **Superkey:** A set of attributes $S$ such that for every attribute $A$ in the relation, $S \to A$.
*   **Candidate Key:** A minimal superkey; a set of attributes such that no proper subset of it is also a superkey.
*   **Prime Attribute:** An attribute that is a member of at least one candidate key.
*   **Non-prime Attribute:** An attribute that is not part of any candidate key.

**Worked Example: Finding the Candidate Key**
Consider $\text{Enrollment}(\text{StudentID, CourseID, Grade, StudentName})$.
1. $\text{StudentID} \to \text{StudentName}$
2. $\{\text{StudentID, CourseID}\} \to \text{Grade}$

**The Tension:** Can $\text{StudentID}$ alone be the key? No, because it cannot determine the $\text{Grade}$ (a student has different grades for different courses). Can $\text{CourseID}$ be the key? No, it doesn't determine the $\text{StudentName}$. 
**Resolution:** The minimal set that unlocks all data is $\{\text{StudentID, CourseID}\}$. This is the **Candidate Key**.
*   **Prime:** $\text{StudentID, CourseID}$.
*   **Non-prime:** $\text{Grade, StudentName}$.

**Try This Yourself:** In a relation $\text{Books}(\text{ISBN, Title, Author})$, if $\text{ISBN} \to \{\text{Title, Author}\}$, is $\text{Title}$ a prime attribute? 
*(Answer: No, because $\text{Title}$ is not part of the candidate key $\text{ISBN}$.)*

---

#### 2. First Normal Form (1NF): Atomicity
**The Problem: The "List" Trap**
Consider a table where a `Courses` column contains: `CS101, MATH202, PHYS101`. To find every student in `CS101`, the database cannot use a high-speed index; it must perform a "string search" (like `LIKE '%CS101%'`) across every single row. This turns a millisecond operation into a multi-second crawl.

**Formal Definition**
A relation is in **1NF** if and only if the domain of each attribute contains only **atomic** (indivisible) values, and there are no repeating groups. In the relational model, this implies that every attribute value is a single value from the domain, not a set or a list.

**Worked Example: Normalizing to 1NF**
*Non-1NF Table:*
| StudentID | Courses |
| :--- | :--- |
| 101 | {CS101, MATH202} |

*1NF Table:*
| StudentID | CourseID |
| :--- | :--- |
| 101 | CS101 |
| 101 | MATH202 |

**Quick Check:** A table stores "Full Name" as one column. Is this a violation of 1NF? 
*(Answer: Generally no, unless the business logic requires searching/sorting by First Name and Last Name independently, rendering the combined value non-atomic for that specific use case.)*

---

#### 3. Second Normal Form (2NF): No Partial Dependencies
**The Problem: The "Half-Key" Dependency**
2NF only applies to tables with **composite keys**. A partial dependency occurs when a non-prime attribute is determined by only *part* of the key.

**The Analogy: The Bad Roommate**
Imagine a lease signed by two roommates (the Composite Key). The `RentAmount` depends on both people signing (Full Dependency). However, the `Roommate1_PhoneNumber` depends only on Roommate 1, regardless of who the second roommate is. Storing the phone number on the joint lease is a "partial dependency."

**Formal Definition**
A relation is in **2NF** if it is in 1NF and no non-prime attribute is functionally dependent on a proper subset of any candidate key. Every non-prime attribute must be **fully functionally dependent** on every candidate key.

**Worked Example: Fixing Partial Dependency**
$\text{ProjectAssignments}(\text{EmpID, ProjID, EmpName, HoursWorked})$.
*   **Candidate Key:** $\{\text{EmpID, ProjID}\}$
*   $\text{FD}_1: \{\text{EmpID, ProjID}\} \to \text{HoursWorked}$ (Full Dependency)
*   $\text{FD}_2: \text{EmpID} \to \text{EmpName}$ (**Partial Dependency**—$\text{EmpName}$ is determined by a subset of the key, $\{\text{EmpID}\}$).

**The Anomaly:** If an employee is on 10 projects, we store their name 10 times. If they change their name, we must update 10 rows. This is an **Update Anomaly**.

**Decomposition:**
1. $\text{Employee}(\underline{\text{EmpID}}, \text{EmpName})$
2. $\text{Assignments}(\underline{\text{EmpID, ProjID}}, \text{HoursWorked})$

**Quick Check:** If a table has a single-attribute primary key, can it violate 2NF? 
*(Answer: No. A single attribute has no proper non-empty subsets, so a partial dependency is mathematically impossible.)*

---

#### 4. Third Normal Form (3NF): No Transitive Dependencies
**The Problem: The "Hidden" Chain**
Even if every attribute depends on the *whole* key, they might depend on the key *via* another attribute. This is a transitive dependency: $\text{Key} \to \text{Attribute B} \to \text{Attribute C}$.

**The Analogy: The Chain of Command**
The CEO ($\text{Key}$) determines who the Manager is ($\text{Attribute B}$). The Manager ($\text{Attribute B}$) determines which Office ($\text{Attribute C}$) is used. While the CEO technically determines the office, they do so *through* the manager. If the manager changes, the office changes, even if the CEO remains the same.

**Formal Definition**
A relation is in **3NF** if it is in 2NF and no non-prime attribute is transitively dependent on a candidate key. 
*Criterion:* For every non-trivial FD $X \to A$, either $X$ is a superkey or $A$ is a prime attribute.

**Worked Example: Fixing Transitive Dependency**
$\text{Employee}(\text{EmpID, DeptID, DeptName})$.
*   **Candidate Key:** $\text{EmpID}$
*   $\text{FD}_1: \text{EmpID} \to \text{DeptID}$
*   $\text{FD}_2: \text{DeptID} \to \text{DeptName}$
$\text{DeptName}$ is transitively dependent on $\text{EmpID}$ via $\text{DeptID}$. Since $\text{DeptID}$ is not a superkey and $\text{DeptName}$ is not prime, this violates 3NF.

**The Anomaly:** If you delete the last employee in the "Research" department, you accidentally delete the fact that the "Research" department exists. This is a **Deletion Anomaly**.

**Decomposition:**
1. $\text{Employee}(\underline{\text{EmpID}}, \text{DeptID})$
2. $\text{Department}(\underline{\text{DeptID}}, \text{DeptName})$

**Try This Yourself:** In $\text{R}(A, B, C)$ with $A$ as the key, $A \to B$ and $B \to C$, which normal form is violated? 
*(Answer: 3NF).*

---

#### 5. Boyce-Codd Normal Form (BCNF): The Strict Standard
**The Problem: The Overlapping Key Paradox**
3NF allows a dependency if the dependent attribute is "prime" (part of *some* candidate key). BCNF removes this loophole to eliminate redundancies that occur when candidate keys overlap.

**The Tension:** Is 3NF enough? Consider a scenario where we have multiple overlapping candidate keys. 3NF might allow a non-superkey to determine part of a key, which still creates redundancy.

**Formal Definition**
A relation is in **BCNF** if for every non-trivial FD $X \to A$, $X$ is a superkey. In BCNF, the determinant must always be a superkey.

**Worked Example: 3NF vs. BCNF**
$\text{TEACH}(\text{Student, Course, Instructor})$.
*   **Constraints:** Each instructor teaches only one course; students can have multiple instructors.
*   $\text{FD}_1: \{\text{Student, Course}\} \to \text{Instructor}$
*   $\text{FD}_2: \text{Instructor} \to \text{Course}$
*   **Candidate Keys:** $\{\text{Student, Course}\}$ and $\{\text{Student, Instructor}\}$.

**Evaluation:**
*   **3NF:** Valid. In $\text{Instructor} \to \text{Course}$, $\text{Course}$ is a prime attribute (it's part of the first candidate key $\{\text{Student, Course}\}$).
*   **BCNF:** Invalid. In $\text{Instructor} \to \text{Course}$, the determinant $\text{Instructor}$ is **not** a superkey (it cannot determine the $\text{Student}$).

**Decomposition:**
1. $\text{R1}(\underline{\text{Student, Instructor}})$
2. $\text{R2}(\underline{\text{Instructor}}, \text{Course})$

**Quick Check:** If a relation is in BCNF, is it automatically in 3NF? 
*(Answer: Yes, BCNF is a stricter version of 3NF. Every BCNF relation satisfies the 3NF criteria.)*

---

#### 6. Summary and Practical Trade-offs

**Normalization Comparison Matrix**

| Form | Requirement | Eliminates | Analogy |
| :--- | :--- | :--- | :--- |
| **1NF** | Atomic values | Multi-valued attributes | No "lists" in cells |
| **2NF** | 1NF + No partial dependencies | Redundancy from composite keys | No "half-key" dependencies |
| **3NF** | 2NF + No transitive dependencies | Redundancy from non-key attributes | No "chains of command" |
| **BCNF** | Every determinant is a superkey | Redundancy from overlapping keys | Absolute determinant authority |

**Limitations and Pitfalls**
*   **Over-Normalization:** While higher normal forms reduce redundancy, they increase the number of tables. This requires more $\text{JOIN}$ operations during queries, which can degrade performance. In high-read environments, "denormalization" is sometimes used intentionally.
*   **Dependency Preservation:** Decomposing a relation into BCNF does not always preserve all functional dependencies. A decomposition is "dependency-preserving" if the union of the FDs in the resulting relations is equivalent to the original set of FDs. 3NF always allows for a dependency-preserving decomposition; BCNF does not.