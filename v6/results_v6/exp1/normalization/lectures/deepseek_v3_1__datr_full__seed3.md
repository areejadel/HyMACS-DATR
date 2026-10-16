# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** – State the definitions of 1NF, 2NF, 3NF, and BCNF, and identify the key property each form enforces.
2. **Understand** – Explain why partial dependencies, transitive dependencies, and non-superkey determinants cause update anomalies.
3. **Apply** – Given a relation schema and a set of functional dependencies, determine its normal form and decompose it to the next higher form.
4. **Analyze** – Diagnose a real-world schema for normalization violations and predict the specific anomalies that will occur.
5. **Evaluate** – Decide when to stop at 3NF versus BCNF based on dependency preservation and performance trade-offs.

---

## Prerequisites Check

We assume you can:

- Read a relation schema written as `R(attr1, attr2, ...)` with a primary key underlined.
- Write a basic SQL `SELECT` statement and recognize that a table is a set of tuples.
- Understand the idea of a constraint: a rule that limits what data is valid.

If the term "tuple" is unfamiliar: a tuple is a row in a table. We use "tuple" and "row" interchangeably.

---

## Intuition First: The Problem Normalization Solves

Before we define any concepts formally, consider a concrete problem. Imagine a company spreadsheet that tracks employees and their projects:

| EmpID | EmpName | Dept | DeptPhone | ProjectID | ProjName |
|-------|---------|------|-----------|-----------|-----------|
| 101   | Alice   | Sales | 555-0100 | P1        | WidgetX  |
| 101   | Alice   | Sales | 555-0100 | P2        | WidgetY  |
| 102   | Bob     | Sales | 555-0100 | P1        | WidgetX  |
| 103   | Carol   | HR    | 555-0200 | P3        | Onboard  |

**What can go wrong?**

- *Update anomaly:* If the Sales department's phone number changes, we must update three rows. Miss one, and Sales now has two phone numbers.
- *Insertion anomaly:* We cannot record a new department (e.g., "Legal") with its phone number until an employee is assigned to it. The `EmpID` part of the key forces us to invent an employee.
- *Deletion anomaly:* If we remove Carol (the only HR employee), we lose the fact that HR's phone number is 555-0200. The department's phone number vanishes with the employee.

Normalization restructures the schema so each fact lives in exactly one place. The process is mechanical: we use functional dependencies to detect these problems and decomposition to fix them.

---

## 1. Foundational Concepts: Keys and Functional Dependencies

### 1.1 Learning Objective for This Section

Given a relation schema and a set of business rules, you will identify candidate keys, classify attributes as prime or nonprime, and express the rules as functional dependencies.

---

### 1.2 Functional Dependencies: The Detective's Tool

**Intuition.** A functional dependency (FD) captures a statement of the form: "If I know X, then I know exactly one Y." It is a business rule, not a property of the current data.

**Formal Definition.** Given a relation schema $R$, an FD $X \rightarrow Y$ holds if, for every allowable instance $r(R)$, whenever two tuples agree on all attributes in $X$, they must also agree on all attributes in $Y$. $X$ and $Y$ are sets of attributes from $R$.

We write $X \rightarrow Y$ and read it as "$X$ functionally determines $Y$."

**Example.** In a university database, the rule "each instructor belongs to exactly one department" becomes:

$$\text{Instructor} \rightarrow \text{Department}$$

If two rows show `Instructor = 'Dr. Chen'`, they must both show the same `Department` value. If they do not, the business rule is violated.

**Important:** An FD is a constraint on *all possible future states* of the database, not just the current snapshot. You cannot verify an FD by looking at today's data alone; you must know the business rule.

---

### 1.3 Superkeys and Candidate Keys

**Superkey (Intuition).** A set of attributes that, taken together, uniquely identifies every row. No two rows can have the same combination of values for a superkey.

**Formal Definition.** A set of attributes $SK \subseteq R$ is a superkey of relation schema $R$ if, for any two tuples $t_1, t_2$ in any valid instance $r(R)$, whenever $t_1[SK] = t_2[SK]$, then $t_1 = t_2$.

**Worked Example.** In a table `Employee(EmpID, SSN, Name, Dept)`:

- $\{\text{EmpID}\}$ is a superkey: no two employees share the same EmpID.
- $\{\text{SSN}\}$ is a superkey: SSN is unique per person.
- $\{\text{EmpID}, \text{Name}\}$ is a superkey, but it is *redundant*—we do not need `Name` to guarantee uniqueness.

**Candidate Key.** A candidate key is a *minimal* superkey. Remove any attribute from it, and it stops being a superkey.

In the example above:

- $\{\text{EmpID}\}$ is a candidate key (minimal).
- $\{\text{SSN}\}$ is a candidate key (minimal).
- $\{\text{EmpID}, \text{Name}\}$ is *not* a candidate key because we can drop `Name` and still have a superkey.

A schema may have multiple candidate keys. We designate one as the *primary key* for physical implementation; the others are *alternate keys*.

---

### 1.4 Prime vs. Nonprime Attributes

**Definition.** An attribute is **prime** if it belongs to at least one candidate key. Otherwise it is **nonprime**.

**Worked Example.** Consider `Enrollment(StudentID, CourseID, Grade)`. Candidate key: $\{\text{StudentID}, \text{CourseID}\}$.

- `StudentID` is prime (it is in the key).
- `CourseID` is prime (it is in the key).
- `Grade` is nonprime (it is not in any candidate key).

This distinction is central to 3NF. Prime means "part of some key"; nonprime means "not part of any key."

---

### 1.5 Full vs. Partial Functional Dependencies

**Intuition.** A full dependency means the entire left-hand side is needed to determine the right-hand side. A partial dependency means a piece of the left-hand side already does the job.

**Formal Definition.** An FD $X \rightarrow Y$ is **full** if removing any attribute $A$ from $X$ causes the dependency to fail. That is, there is no proper subset $X' \subset X$ such that $X' \rightarrow Y$ holds.

If such an $X'$ does exist, the dependency is **partial**.

**Worked Example.** In `EMP_PROJ(EmpID, ProjID, Hours, EmpName)` with candidate key $\{\text{EmpID}, \text{ProjID}\}$:

- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$ is full: you need both the employee and the project to know the hours worked.
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{EmpName}$ is partial: $\text{EmpID} \rightarrow \text{EmpName}$ already holds. `EmpName` depends on only part of the key.

Partial dependencies are the defect that 2NF eliminates. Notice the pattern: a nonprime attribute depending on a proper subset of a candidate key.

---

### Quick Check 1

Given `Order(OrderID, ProductID, CustomerID, CustomerName)` with candidate key $\{\text{OrderID}, \text{ProductID}\}$ and the FD $\text{CustomerID} \rightarrow \text{CustomerName}$:

1. Is `CustomerName` prime or nonprime?
2. Is $\{\text{OrderID}, \text{ProductID}\} \rightarrow \text{CustomerName}$ full or partial?

*(Answers: `CustomerName` is nonprime—it is not in the key. The FD is partial because `CustomerName` depends on `CustomerID` alone, which is a proper subset of the key.)*

---

## 2. First Normal Form (1NF)

### 2.1 Learning Objective for This Section

Determine whether a schema satisfies 1NF, and if not, transform it into 1NF by eliminating multi-valued attributes and nested relations.

---

### 2.2 Intuition

1NF is the starting line. It states: "Every cell in the table holds exactly one atomic value." No lists, no sets, no tables inside tables. The relational model cannot operate on a column that contains a comma-separated list—`WHERE` clauses, joins, and aggregates all assume atomicity.

---

### 2.3 Formal Definition

A relation schema $R$ is in 1NF if the domain of each attribute contains only *atomic* (indivisible) values, and the value of each attribute in any tuple is a single element from that domain.

---

### 2.4 Violations and Remedies

**Typical Violation.** A column stores multiple values, such as a comma-separated list of phone numbers or a nested table of line items.

**Remedy.** Decompose the multi-valued attribute into a separate relation linked by a foreign key, or expand the list into multiple rows, one per value.

**Example.** Transform `Employee(EmpID, Name, PhoneNumbers)` where `PhoneNumbers` holds a set of values into:

```sql
Employee(EmpID, Name)
EmployeePhone(EmpID, PhoneNumber)
```

Each phone number occupies its own row in `EmployeePhone`. The schema is now in 1NF.

---

## 3. Second Normal Form (2NF)

### 3.1 Learning Objective for This Section

Given a 1NF schema, identify partial dependencies on candidate keys and decompose the schema to eliminate them, achieving 2NF.

---

### 3.2 Intuition

2NF targets the problem: "A nonprime attribute depends on only part of a candidate key." When that happens, the attribute describes a subset of the key's components, not the whole key. This duplication leads to update anomalies.

---

### 3.3 Formal Definition

A relation schema $R$ is in 2NF if it is in 1NF and every nonprime attribute is fully functionally dependent on every candidate key of $R$.

---

### 3.4 Detection and Decomposition

**Detection.** Find a candidate key $K$ and a nonprime attribute $A$ such that a proper subset $K' \subset K$ determines $A$ ($K' \rightarrow A$).

**Decomposition.** Split $R$ into:

- $R_1(K', \text{attributes depending on } K')$
- $R_2(K, \text{remaining attributes})$

**Worked Example.** Consider `EMP_PROJ(EmpID, ProjID, Hours, EmpName, ProjName)` with candidate key $\{\text{EmpID}, \text{ProjID}\}$ and FDs:

- $\text{EmpID} \rightarrow \text{EmpName}$
- $\text{ProjID} \rightarrow \text{ProjName}$
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$

`EmpName` and `ProjName` are nonprime and depend on parts of the key. Decompose into:

```sql
Employee(EmpID, EmpName)
Project(ProjID, ProjName)
Assignment(EmpID, ProjID, Hours)
```

Each nonprime attribute now depends on the full key of its own relation. The schema is in 2NF.

---

## 4. Third Normal Form (3NF)

### 4.1 Learning Objective for This Section

Given a 2NF schema, identify transitive dependencies where a nonprime attribute determines another nonprime attribute, and decompose to achieve 3NF.

---

### 4.2 Intuition

Even after 2NF, a nonprime attribute may depend on another nonprime attribute, not directly on a key. This indirect dependency still duplicates facts and causes anomalies. 3NF eliminates these transitive dependencies.

---

### 4.3 Formal Definition

A relation schema $R$ is in 3NF if, for every non-trivial FD $X \rightarrow A$ (where $A$ is a single nonprime attribute), either:

- $X$ is a superkey of $R$, or
- $A$ is prime.

Equivalently: no nonprime attribute is transitively dependent on a candidate key through another nonprime attribute.

---

### 4.4 Detection and Decomposition

**Detection.** Find an FD $X \rightarrow Y$ where $X$ is not a superkey and $Y$ is nonprime. Then $Y$ is transitively dependent on the key via $X$.

**Decomposition.** For each such FD, project out the dependent attributes:

- $R_1(X, Y)$
- $R_2(R \setminus \{Y\})$ (keep $X$ as a foreign key in $R_2$)

**Worked Example.** `EmployeeDept(EmpID, DeptID, DeptName, DeptPhone)` with candidate key $\{\text{EmpID}\}$ and FDs:

- $\text{EmpID} \rightarrow \text{DeptID}$
- $\text{DeptID} \rightarrow \text{DeptName}, \text{DeptPhone}$

`DeptName` and `DeptPhone` are nonprime and depend on `DeptID`, which is not a superkey. Decompose into:

```sql
Employee(EmpID, DeptID)
Department(DeptID, DeptName, DeptPhone)
```

Now `DeptName` and `DeptPhone` depend directly on the key `DeptID` of their own relation. The schema is in 3NF.

---

## 5. Boyce-Codd Normal Form (BCNF)

### 5.1 Learning Objective for This Section

Given a 3NF schema, identify FDs where the left-hand side is not a superkey but the right-hand side is prime, and decompose to achieve BCNF when 3NF is insufficient.

---

### 5.2 Intuition

3NF allows a special case: an FD whose left-hand side is not a superkey but whose right-hand side is prime. This can still cause redundancy when multiple candidate keys overlap. BCNF removes that exception: every non-trivial FD must have a superkey as its left-hand side.

---

### 5.3 Formal Definition

A relation schema $R$ is in BCNF if, for every non-trivial FD $X \rightarrow Y$ (where $Y \subseteq R$ and $Y \not\subseteq X$), $X$ is a superkey of $R$.

---

### 5.4 Detection and Decomposition

**Detection.** Find an FD $X \rightarrow Y$ where $X$ is not a superkey. This is a violation regardless of whether $Y$ is prime or nonprime.

**Decomposition.** For each violating FD $X \rightarrow Y$, split:

- $R_1(X, Y)$
- $R_2(R \setminus Y)$ (retaining $X$ as a foreign key)

Repeat until all relations satisfy BCNF.

**Worked Example.** `Enrollment(StudentID, CourseID, InstructorID)` with candidate keys $\{\text{StudentID}, \text{CourseID}\}$ and $\{\text{StudentID}, \text{InstructorID}\}$, and FD:

- $\text{InstructorID} \rightarrow \text{CourseID}$

Here, `InstructorID` is not a superkey, yet it determines `CourseID`. The schema is in 3NF (because `CourseID` is prime) but violates BCNF. Decompose into:

```sql
Teaches(InstructorID, CourseID)
Attends(StudentID, InstructorID)
```

Now `InstructorID` is a superkey in `Teaches`. The schema is in BCNF.

---

## 6. Choosing Between 3NF and BCNF

### 6.1 Learning Objective for This Section

Evaluate the trade-off between dependency preservation and elimination of redundancy when deciding whether to stop at 3NF or proceed to BCNF.

---

### 6.2 The Trade-off

- **BCNF** eliminates all redundancy caused by FDs but may not preserve all original FDs across the decomposed relations. Some constraints must then be enforced procedurally.
- **3NF** guarantees dependency preservation: every original FD is enforced within a single relation. However, it may retain some redundancy involving prime attributes.

### 6.3 Decision Heuristic

- If the lost FD is critical for data integrity and you cannot enforce it via application logic, **stop at 3NF**.
- If redundancy is the primary concern and the lost FD is acceptable, **go to BCNF**.

In practice, most well-designed schemas reach BCNF naturally; the 3NF/BCNF dilemma arises mainly in schemas with multiple overlapping candidate keys.

---

## Summary

- **1NF**: Atomic values only. No repeating groups.
- **2NF**: No partial dependency of a nonprime attribute on a candidate key.
- **3NF**: No transitive dependency of a nonprime attribute on a candidate key.
- **BCNF**: Every non-trivial FD has a superkey on its left-hand side.

Each normal form builds on the previous one, progressively eliminating update, insertion, and deletion anomalies by ensuring each fact is stored exactly once.