By the end of this lecture, you will be able to:  
1. **Identify** candidate keys, prime attributes, and functional dependencies in a given relation schema.  
2. **Explain** the conditions for 1NF, 2NF, 3NF, and BCNF using precise criteria based on functional dependencies and keys.  
3. **Diagnose** normal form violations in a schema by analyzing dependencies and attribute roles.  
4. **Decompose** a relation into higher normal forms using lossless, dependency-preserving strategies where possible.  
5. **Evaluate** trade-offs between normalization levels in real-world design scenarios.

---

### A Puzzle to Start: Why Does Your Database Lie?

Imagine a hospital system flags a patient as allergic to penicillin. But when the doctor checks, the record says “none.” No error log. No rollback. Just… inconsistency.

You dive in. The `Allergies` field stores values like `"penicillin, peanuts"`. A nurse once added “aspirin” by appending it — but missed one record where the string was cut off. Later, a script tried to remove “peanuts” using `REPLACE`, accidentally turning “penicillin” into “penciin.”

No one broke the rules. The system worked exactly as designed.

This isn’t a software bug. It’s a **schema failure** — and normalization is the antidote.

Let’s begin not with definitions, but with **consequences**.

---

### Prerequisites: Functional Dependencies, Keys, and Attribute Classification

Normalization builds on core relational concepts: functional dependencies, keys, and attribute classification. We begin by defining these formally.

Consider a university database with the relation:

```
Enrollment(StudentID, Course, Instructor, Office)
```

Suppose:
- Each course has exactly one instructor.
- Each instructor has exactly one office.

This implies that if two tuples share the same `Course`, they must have the same `Instructor`. Similarly, identical `Instructor` values imply identical `Office` values. These constraints are formalized using **functional dependencies (FDs)**.

#### Functional Dependencies

A **functional dependency** $X \rightarrow Y$ holds in a relation $R$ if, for any two tuples $t_1$ and $t_2$ in $R$,  
$$
t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y].
$$

We say $X$ *determines* $Y$, or $Y$ is *functionally dependent* on $X$.

In our example:
- $Course \rightarrow Instructor$: every course is taught by one instructor.
- $Instructor \rightarrow Office$: each instructor occupies one office.

> **Analogy: Dependency as Causality in Physics**  
Think of FDs like deterministic laws. If mass determines gravitational force (via $F = Gm_1m_2/r^2$), then two objects with the same mass in the same configuration *must* exert the same force. In databases, $Course \rightarrow Instructor$ is just as rigid — it’s a law of the data universe.

#### Superkeys and Candidate Keys

A **superkey** is a set of attributes that functionally determines all other attributes in the relation.  
A **candidate key** is a *minimal* superkey—no proper subset is also a superkey.

Minimality ensures no redundant attributes in the key.

> **Analogy: Candidate Key as a DNA Profile**  
Just as a full genome is a superkey for human identity, but only a minimal set of markers (like in forensic DNA) is needed to uniquely identify someone, a candidate key is the smallest "genetic signature" that distinguishes every tuple.

#### Worked Example: Finding Candidate Keys

Given relation $R(A, B, C)$ with functional dependencies:
- $A \rightarrow B$
- $B \rightarrow C$

We compute the closure of attribute sets to determine superkeys.

**Step 1: Compute $A^+$**  
- $A \rightarrow B$ → $B \in A^+$
- $B \rightarrow C$ → $C \in A^+$
- Thus $A^+ = \{A, B, C\}$ → $A$ determines all attributes → $A$ is a superkey  
- $A$ is single-attribute → minimal → **$A$ is a candidate key**

**Step 2: Is $B$ a candidate key?**  
- $B^+ = \{B, C\}$ (from $B \rightarrow C$), but $A \notin B^+$ → $B$ does not determine $A$ → not a superkey

**Step 3: Is $AB$ a candidate key?**  
- $AB^+ = \{A, B, C\}$ → superkey, but not minimal (since $A$ alone suffices) → not a candidate key

Thus, the only candidate key is $A$.

> **Tension Point**: What if we had $B \rightarrow A$ instead? Would $B$ then be a candidate key?  
Try it: compute $B^+$ under $B \rightarrow A$ and $A \rightarrow C$.  
*(Spoiler: Yes — symmetry matters. Keys aren’t privileged by name, only by function.)*

#### Attribute Classification

- A **prime attribute** is any attribute that is part of *at least one* candidate key.
- A **non-prime attribute** is not part of any candidate key.

In this example:
- $A$ is prime (it is the candidate key)
- $B$ and $C$ are non-prime

> **Clarification**: Being a determinant (left side of an FD) does not imply primeness. Only membership in a candidate key confers this status.

✅ **Try This Yourself**  
Given $R(X,Y,Z)$ with FDs $Y \rightarrow Z$, $Z \rightarrow X$, and candidate key $\{Y\}$:  
- Is $Z$ prime?  
- Is $Y$ non-prime?  
*(Answer: $Z$ is non-prime; $Y$ is prime)*

> **Cross-Domain Insight: Prime Attributes as "Protected Variables" in APIs**  
In software engineering, certain fields (like `userID`) are treated as immutable anchors. Prime attributes are like those — they’re part of the identity contract. You don’t derive them; you *rely* on them.

---

### First Normal Form (1NF): Atomicity as a Foundation

We now introduce **First Normal Form (1NF)**, the baseline requirement for relational tables.

A relation is in **1NF** if and only if:
1. All attribute values are **atomic** (indivisible).
2. Each attribute is drawn from a single domain.
3. The order of rows and columns is irrelevant.

> **Intuition**: 1NF ensures one fact per cell. Without it, queries become ambiguous or inefficient.

#### Motivating Example: Patient Allergies

Consider an unnormalized table:

| PatientID | Name   | Allergies               |
|----------|--------|--------------------------|
| P01      | Alice  | penicillin, peanuts      |
| P02      | Bob    | shellfish                |

The `Allergies` column contains multivalued entries, violating atomicity.

**Problems**:
- Cannot index `Allergies` effectively.
- Querying for penicillin allergies requires pattern matching (`LIKE '%penicillin%'`), which is error-prone.
- Cannot enforce referential integrity with a drug database.

> **Analogy: 1NF as the Periodic Table of Data**  
Just as chemistry relies on indivisible elements, databases rely on atomic facts. You can’t build reliable compounds (queries, constraints) from ambiguous mixtures.

#### Decomposition to 1NF

We split the relation into two:

```
Patient(PatientID, Name)
Allergy(PatientID, Allergen)
```

Resulting data:

| PatientID | Allergen    |
|----------|-------------|
| P01      | penicillin  |
| P01      | peanuts     |
| P02      | shellfish   |

Each cell contains a single value → atomic → satisfies 1NF.

> **Why Atomicity Matters**  
Atomic values enable exact matching, indexing, and referential constraints. For example:
```sql
SELECT PatientID FROM Allergy WHERE Allergen = 'penicillin';
```
This query is now efficient and reliable.

✅ **Try This Yourself**  
Is the following schema in 1NF?  
`Book(ISBN, Title, Authors)` where `Authors` stores "Smith, Jones, Lee"  
*(Answer: No—`Authors` is not atomic. Normalize by creating `BookAuthor(ISBN, Author)`)*

> **Innovation: 1NF in Version Control**  
Git doesn’t store diffs as strings like “added line 5, removed line 12.” It breaks changes into atomic commits. Similarly, 1NF ensures each data change is isolated, auditable, and composable.

---

### Second Normal Form (2NF): Eliminating Partial Dependencies

With atomic values established, we address redundancy from **partial dependencies**.

A relation is in **2NF** if:
1. It is in 1NF.
2. Every non-prime attribute is **fully functionally dependent** on every candidate key.

> **Intuition**: If a non-key attribute depends on only part of a composite key, it should be moved to a separate relation.

#### When 2NF Applies

Partial dependencies can only occur when a candidate key has multiple attributes.

Let $K = \{X, Y\}$ be a composite candidate key. A non-prime attribute $Z$ exhibits a **partial dependency** if $X \rightarrow Z$, where $X \subset K$.

> **Analogy: 2NF as Microservices Decomposition**  
Imagine a monolithic service handling both order processing and product catalog. If product name depends only on `ProductID`, not the full `(OrderID, ProductID)` key, it’s like a service endpoint that doesn’t need the full request context. Extract it — that’s 2NF.

#### Worked Example: E-Commerce Order Lines

Schema:  
`OrderLine(OrderID, ProductID, ProductName, Quantity)`  
Candidate key: $\{OrderID, ProductID\}$  
FD: $ProductID \rightarrow ProductName$

Now evaluate $ProductName$:  
- It depends on $ProductID$, a proper subset of the key → **partial dependency**  
- $ProductName$ is non-prime → violates 2NF

**Consequences**:
- **Redundancy**: `ProductName` repeats across orders.
- **Update anomaly**: Renaming a product requires updating multiple rows.
- **Insertion anomaly**: Cannot add a product not yet ordered.
- **Deletion anomaly**: Canceling all orders for a product deletes its name.

#### Decomposition to 2NF

We separate product data from order data:

```
OrderLine(OrderID, ProductID, Quantity)
Product(ProductID, ProductName)
```

Now:
- In `Product`, $ProductID \rightarrow ProductName$: full dependency on key.
- `OrderLine` contains only attributes fully dependent on its key.

2NF is satisfied.

✅ **Try This Yourself**  
Given `Enrollment(StudentID, CourseID, CourseName, Grade)`  
Key: $\{StudentID, CourseID\}$, FD: $CourseID \rightarrow CourseName$  
- Is this in 2NF?  
- If not, how would you fix it?  
*(Answer: No—partial dependency. Decompose into `Enrollment(StudentID, CourseID, Grade)` and `Course(CourseID, CourseName)`)*

> **Design Tension**: Could we instead make `CourseName` part of the key?  
Try it: would `(StudentID, CourseName)` be unique? What if two courses have the same name?  
*(Spoiler: Keys must be stable and minimal. Name changes break referential integrity.)*

---

### Third Normal Form (3NF): Eliminating Transitive Dependencies

We now address **transitive dependencies**, where a non-key attribute determines another non-key attribute.

A relation is in **3NF** if:
1. It is in 2NF.
2. For every non-trivial FD $X \rightarrow Y$, at least one of the following holds:
   - $X$ is a superkey.
   - $Y$ is a prime attribute.

> **Intuition**: If $A \rightarrow B$ and $B \rightarrow C$, then $C$ depends indirectly on $A$. If $B$ is not a key, storing $C$ with $A$ creates redundancy.

> **Analogy: 3NF as Causal Chains in Epidemiology**  
If smoking → tar buildup → lung cancer, and you only control smoking, you’re relying on an indirect link. In databases, if $StudentID \rightarrow Advisor \rightarrow Office$, storing `Office` with `StudentID` means you’re trusting a chain — and chains break.

#### Real-World Example: Student Advisors

Schema:  
`Student(StudentID, Advisor, AdvisorOffice)`  
FDs:
- $StudentID \rightarrow Advisor$
- $Advisor \rightarrow AdvisorOffice$

Candidate key: $\{StudentID\}$ → $Advisor$ and $AdvisorOffice$ are non-prime.

Check $Advisor \rightarrow AdvisorOffice$:
- $Advisor$ is not a superkey (does not determine $StudentID$)
- $AdvisorOffice$ is non-prime
→ Violates 3NF.

**Anomalies**:
- Changing an advisor’s office requires updating all their students.
- Deleting the last student of an advisor may lose office information.
- Cannot record a new advisor’s office before assigning a student.

#### Decomposition to 3NF

```
Student(StudentID, Advisor)
Advisor(Advisor, AdvisorOffice)
```

Now:
- $Advisor \rightarrow AdvisorOffice$: $Advisor$ is key in `Advisor` → FD preserved.
- No transitive dependency in `Student`.

3NF is satisfied.

✅ **Try This Yourself**  
Given `Employee(EmpID, Dept, DeptPhone)`  
Key: $\{EmpID\}$, FD: $Dept \rightarrow DeptPhone$  
- Is this in 3NF?  
- If not, decompose it.  
*(Answer: No—transitive dependency. Split into `Employee(EmpID, Dept)` and `Department(Dept, DeptPhone)`)*

> **Innovation: 3NF and Machine Learning Pipelines**  
In ML, feature leakage occurs when a variable indirectly encodes the target. Transitive dependencies are data leakage: `AdvisorOffice` indirectly reveals `Advisor`, which is already determined by `StudentID`. 3NF prevents such hidden couplings.

---

### Boyce-Codd Normal Form (BCNF): The Strictest FD-Based Normal Form

BCNF closes the loophole in 3NF by disallowing any non-trivial FD where the determinant is not a superkey.

A relation is in **BCNF** if and only if:  
For every non-trivial FD $X \rightarrow Y$, $X$ is a **superkey**.

> **Intuition**: In BCNF, *only keys can determine other attributes*. There are no exceptions.

BCNF is **strictly stronger** than 3NF: every BCNF schema is in 3NF, but not vice versa.

> **Analogy: BCNF as Constitutional Law**  
In a democracy, laws must be passed by authorized bodies (superkeys). If a random citizen (non-superkey) could pass a law (determine an attribute), chaos ensues. BCNF enforces rule of law: only keys legislate.

#### Worked Example: Airline Gate Assignment

Schema:  
`Flight(AirlineCode, FlightNum, Gate)`  
Candidate key: $\{AirlineCode, FlightNum\}$  
FD: $AirlineCode \rightarrow Gate$ (each airline uses one gate)

Check $AirlineCode \rightarrow Gate$:
- $AirlineCode$ is not a superkey (does not determine $FlightNum$)
→ Violates BCNF.

**Problem**: If Delta changes gates, every Delta flight record must be updated.

#### Decomposition to BCNF

```
Flight(AirlineCode, FlightNum)
AirlineGate(AirlineCode, Gate)
```

Now:
- In `AirlineGate`, $AirlineCode \rightarrow Gate$: $AirlineCode$ is a key → BCNF satisfied.
- In `Flight`, no non-trivial FDs → trivially in BCNF.

✅ **Try This Yourself**  
Given $R(A,B,C)$ with FDs:
- $A \rightarrow B$
- $B \rightarrow C$
- Key: $\{A\}$

Is this in BCNF?  
*(Answer: No—$B \rightarrow C$, but $B$ is not a superkey. Although $A \rightarrow B$ is valid ($A$ is a superkey), one violation suffices to fail BCNF.)*

> **Critical Insight**: BCNF decomposition **does not guarantee dependency preservation**.

#### Case Where Dependency Is Lost

Let $R(A,B,C)$ with FDs:
- $A \rightarrow B$
- $C \rightarrow B$
- Candidate key: $\{A,C\}$

Check $A \rightarrow B$: $A$ is not a superkey → violates BCNF.

Decompose using $A \rightarrow B$:
- $R1(A,B)$
- $R2(A,C)$

Now $C \rightarrow B$ cannot be enforced—$C$ and $B$ are in different relations.

> **Tension Point**: Can we instead decompose on $C \rightarrow B$?  
Try it: create $R1(C,B)$, $R2(C,A)$.  
Now $A \rightarrow B$ is lost. **No decomposition preserves both.**

> **Consequence**: The FD $C \rightarrow B$ is **lost**. Enforcing it requires joins or application logic.

✅ **Try This Yourself**  
After decomposition, can we detect a violation of $C \rightarrow B$ without joining $R1$ and $R2$?  
*(Answer: No—checking $C \rightarrow B$ requires data from both tables. The constraint is not locally enforceable.)*

> **Innovation: BCNF vs. Eventual Consistency in Distributed Systems**  
In distributed databases, enforcing global constraints (like $C \rightarrow B$) across partitions is costly. BCNF’s loss of dependency preservation mirrors the CAP theorem: you can’t always have full consistency, availability, and partition tolerance. Sometimes 3NF is the pragmatic compromise.

---

### Trade-Offs and Design Strategy

Normalization is a design tool, not an absolute goal. Practical schema design balances data integrity, performance, and maintainability.

#### Comparison of 3NF and BCNF

| Criterion               | 3NF                              | BCNF                              |
|-------------------------|----------------------------------|-----------------------------------|
| Redundancy              | Minimal; some transitive chains allowed if $Y$ is prime | Eliminated for all FDs |
| Dependency Preservation | **Guaranteed** possible          | **Not guaranteed**                |
| Lossless Join           | Guaranteed                       | Guaranteed                        |
| Update Anomaly Safety   | High                             | Maximum                           |
| Query Complexity        | Lower (fewer joins)              | Higher (more decomposed)          |

#### Case Study: Hospital Lab Testing

Schema:  
`PatientTest(PatientID, TestType, LabTechnician, LabLocation)`  
FDs:
- $TestType \rightarrow LabTechnician$
- $LabTechnician \rightarrow LabLocation$
- Key: $\{PatientID, TestType\}$

Non-prime attributes: $LabTechnician$, $LabLocation$

Check $LabTechnician \rightarrow LabLocation$:  
- $LabTechnician$ not a superkey, $LabLocation$ non-prime → violates 3NF

Decompose to BCNF:

```
PatientTest(PatientID, TestType)
TestAssign(TestType, LabTechnician)
LabTeam(LabTechnician, LabLocation)
```

All FDs are preserved, and each relation is in BCNF.

But suppose $LabTechnician \rightarrow TestType$ also holds. Then $\{LabTechnician\}$ is a candidate key. In this case, $LabTechnician \rightarrow LabLocation$ is valid in BCNF (determinant is a key).

> **Design Insight**: Normalization depends on *current business rules*. If rules change (e.g., technicians begin handling multiple test types), the schema may no longer be in BCNF. Reassess regularly.

> **Cross-Domain Link: Schema Evolution as API Versioning**  
Just as APIs version when contracts change, database schemas should evolve when functional dependencies shift. Treat FDs as part of your API contract.

> **Emerging Practice**: Apply **domain-driven design**—identify bounded contexts (e.g., “Billing”, “Lab”) and normalize *within* each. This supports both data integrity and modular development.

---

### Summary and Synthesis

We have defined a hierarchy of normal forms, each eliminating a class of redundancy and anomalies.

#### Normal