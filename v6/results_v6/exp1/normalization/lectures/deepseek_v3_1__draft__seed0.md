# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** the definitions of 1NF, 2NF, 3NF, and BCNF and state the anomaly each form eliminates.
2. **Understand** why update, insertion, and deletion anomalies arise from poor schema design and how functional dependencies capture the root cause.
3. **Apply** the step-by-step decomposition algorithm to a given relation, using its functional dependencies and candidate keys, to produce schemas in 3NF or BCNF.
4. **Analyze** a real-world schema to identify which normal form it satisfies and pinpoint exactly which functional dependency violates the next higher form.
5. **Evaluate** when to stop normalizing (3NF vs. BCNF) and when deliberate denormalization is a defensible performance trade-off.

---

## 1. Why Normalize? The Problem in One Table

Imagine you’re building a company directory. You’ve got employees, departments, and buildings. The obvious first instinct is to put everything in one table — after all, each employee *has* a department, and each department *occupies* a building. So you write:

```
EMP_DEPT_BUILDING(EmpID, EmpName, DeptID, DeptName, Building)
```

Assume these real-world constraints:

- Each employee has a unique `EmpID`.
- Each employee belongs to exactly one department, identified by `DeptID`.
- Each department has one name (`DeptName`) and is housed in one building (`Building`).

Now try three everyday operations against this schema:

- **Update anomaly:** The Sales department moves from Building A to Building B. You must change `Building` in *every* row for every Sales employee. Miss one row, and your database now asserts that Sales occupies two buildings simultaneously — a logical contradiction that no constraint can catch because the constraint isn’t expressed in the schema itself.
- **Insertion anomaly:** You want to record a brand-new department, Engineering, before any employees are hired into it. You cannot insert that row because `EmpID` is part of the primary key and cannot be null. The database forces you to invent a fake employee just to record a real department.
- **Deletion anomaly:** The last employee in Marketing resigns. Deleting her row removes *all* record that Marketing ever existed, including its name and building. A single personnel action accidentally erases organizational structure.

These three anomalies share a single root cause: one table attempts to represent multiple independent facts — facts about employees, facts about departments, facts about buildings — and the schema has no mechanism to enforce their independence. The table is a physical container that conflates three separate logical truths.

> **Quick Check 1:** In the table above, which of the three anomalies would occur if we changed an employee’s name? (Hint: is an employee’s name a fact about the employee alone or about a combination of entities?)

---

## 2. The Tool That Finds the Problem: Functional Dependencies

Normalization does not rely on intuition. It uses a precise, mechanical tool: the **functional dependency (FD)**. This is the diagnostic instrument that tells you *exactly* which facts are tangled together.

Let $R$ be a relation schema with attribute set $U$. An FD $X \rightarrow Y$ (read “$X$ determines $Y$”) means: in any valid instance of $R$, whenever two tuples agree on all attributes in $X$, they *must* agree on all attributes in $Y$.

**Analogy:** Think of $X \rightarrow Y$ as a mathematical function from $X$ to $Y$. Just as $f(x) = \sin(x)$ gives you exactly one output for each input, an FD says that for each value of $X$, there is exactly one corresponding value of $Y$ in the database. The database is enforcing that the mapping from $X$ to $Y$ is a function, not a relation that could branch.

**Intuition rephrased:** “If I know $X$, I can look up exactly one value for $Y$.” In the employee example:

- $\text{EmpID} \rightarrow \text{EmpName}$ — given an employee’s ID, there is exactly one name.
- $\text{DeptID} \rightarrow \text{DeptName}, \text{Building}$ — given a department ID, there is exactly one department name and exactly one building.

**Formal definition:** For any two tuples $t_1, t_2$ in $r(R)$, if $t_1[X] = t_2[X]$ then $t_1[Y] = t_2[Y]$. An FD is *nontrivial* when $Y \not\subseteq X$; otherwise it conveys no useful constraint (saying “knowing X determines X” is tautologically true but tells you nothing about structure).

**Keys via FDs — the critical bridge:** A **superkey** is any set of attributes $SK$ such that $SK \rightarrow U$ — knowing $SK$ determines the entire tuple. A **candidate key** $K$ is a *minimal* superkey: no attribute can be removed from $K$ while preserving the property $K \rightarrow U$. An attribute is **prime** if it belongs to at least one candidate key; otherwise it is **nonprime**.

These definitions form the lens through which every normal form is judged. The distinction between prime and nonprime is the fault line that separates 2NF from 3NF, and 3NF from BCNF.

> **Quick Check 2:** In the relation `EMP(EmpID, Name, SSN)`, suppose both `EmpID` and `SSN` are unique per employee. What are the candidate keys? Which attributes are prime, which are nonprime?

---

## 3. First Normal Form (1NF): The Flat-Table Foundation

**Definition.** A relation is in 1NF if every attribute domain contains only atomic (indivisible) values. No attribute may be relation-valued, set-valued, or contain repeating groups within a single cell.

**Why it matters.** The relational algebra operates on flat tables. A cell containing a list `{101, 102, 103}` breaks operators like selection and join because they expect a single value per column per row. It’s not a cosmetic preference — it’s a requirement for the algebraic machinery to function.

**Worked example.**

Start with this non-1NF table:

```
DEPARTMENT(DeptID, DeptName, Employees)
```

Here `Employees` is a set of employee IDs, e.g., `{E1, E2}`. A single cell contains multiple values.

To reach 1NF, we have two choices:

1. **Flatten:** Expand each set element into its own row:
   ```
   DEPARTMENT(DeptID, DeptName, EmployeeID)
   ```
   Now `D01, Sales, E1` and `D01, Sales, E2` are two separate tuples. The department name is repeated, but every cell holds exactly one atomic value.

2. **Decompose:** Split into two relations:
   ```
   DEPARTMENT(DeptID, DeptName)
   DEPT_EMP(DeptID, EmployeeID)
   ```
   This eliminates the repetition entirely by separating the facts.

In both results, every cell holds exactly one atomic value. The choice between flattening and decomposing is not neutral — decomposition often anticipates further normalization, while flattening can introduce the very redundancy that higher normal forms aim to eliminate.

**Misconception alert:** 1NF does *not* mean “no duplicate rows.” Duplicate rows are a separate issue handled by the relational model’s set semantics (a relation is a set of tuples, so duplicates are impossible by definition). 1NF only prohibits non-atomic cell contents.

**Limitation:** A schema in 1NF can still suffer from all three anomalies. 1NF is a starting point, not a destination. It clears the ground so that functional dependencies can operate on flat attributes, but it does nothing to untangle the dependencies themselves.

> **Quick Check 3:** Why would a column storing comma-separated values like `'Math,Physics'` violate 1NF? (Consider: what would a query asking “find all employees enrolled in Physics” have to do to that column?)

---

## 4. Second Normal Form (2NF): Eliminating Partial Dependencies

### 4.1 Motivation

2NF targets a specific situation that 1NF leaves untouched: the primary key is composite (made of multiple attributes), yet some non-key attribute depends on only *part* of that key. When that happens, the attribute is really describing one of the key parts, not the whole combination. The attribute is, in a sense, in the wrong table — it belongs with its determining subset, not with the full composite.

### 4.2 Definition

A relation $R$ is in 2NF if:

1. $R$ is in 1NF, and
2. Every nonprime attribute is *fully* functionally dependent on every candidate key. That means no nonprime attribute $A$ satisfies $K' \rightarrow A$ where $K'$ is a proper subset of a candidate key $K$.

**Tension:** Notice what this definition *doesn’t* say. It doesn’t say “no nonprime attribute depends on part of the primary key.” It says “every candidate key.” If a relation has multiple candidate keys, 2NF checks all of them. A schema can satisfy 2NF with respect to one key and still fail with respect to another — but the definition requires satisfaction for every candidate key.

### 4.3 Worked Example: The Classic EMP_PROJ

Consider a schema that tracks which employees work on which projects and for how many hours:

```
EMP_PROJ(EmpID, ProjID, EmpName, ProjLocation, Hours)
```

We identify the FDs from the real-world rules:

- $\text{EmpID} \rightarrow \text{EmpName}$ (an employee’s ID determines their name)
- $\text{ProjID} \rightarrow \text{ProjLocation}$ (a project’s ID determines its location)
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$ (the combination determines hours worked)

Candidate key: $\{\text{EmpID}, \text{ProjID}\}$. Prime attributes: `EmpID`, `ProjID`. Nonprime: `EmpName`, `ProjLocation`, `Hours`.

Now inspect the nonprime attributes against the key. This is where the tension resolves — we’ve identified the FDs, now we check each one:

- `EmpName` depends on `EmpID` alone — a proper subset of the key. This is a partial dependency. **Violation.**
- `ProjLocation` depends on `ProjID` alone — another partial dependency. **Violation.**
- `Hours` depends on the full key $\{\text{EmpID}, \text{ProjID}\}$ — no violation. `Hours` is the only attribute that genuinely describes the *intersection* of an employee and a project.

**Anomalies caused:**

- Update: Changing an employee’s name requires updating every row for that employee across all projects. If they’re on 20 projects, that’s 20 updates.
- Insertion: Cannot record a new employee’s name until they are assigned to at least one project. The schema holds the employee’s identity hostage to project participation.
- Deletion: If an employee finishes their last project and that row is deleted, we lose their name entirely. The employee ceases to exist in the database.

### 4.4 Decomposition to 2NF

We split along the violating FDs, ensuring each resulting relation has a key that fully determines its nonprime attributes:

- $R_1(\text{EmpID}, \text{EmpName})$ with key $\text{EmpID}$. Single-attribute key: trivially full dependence — no subset to depend on partially.
- $R_2(\text{ProjID}, \text{ProjLocation})$ with key $\text{ProjID}$. Single-attribute key: trivially full dependence.
- $R_3(\text{EmpID}, \text{ProjID}, \text{Hours})$ with key $\{\text{EmpID}, \text{ProjID}\}$. Here `Hours` depends on the full key — no partial dependency remains.

**Try this yourself:** Before reading on, write down the FDs for each of $R_1$, $R_2$, and $R_3$. Verify that in each relation, every nonprime attribute depends on the *entire* candidate key, not on any subset. This is the litmus test for 2NF.

---

## 5. Third Normal Form (3NF): Eliminating Transitive Dependencies

### 5.1 The Gap 2NF Leaves

A schema in 2NF can still harbor anomalies. The problem shifts: now a nonprime attribute depends on another nonprime attribute, which in turn depends on the key. This is a **transitive dependency** — a chain of determination that routes through a non-key attribute.

**Cross-domain analogy:** Think of a transitive dependency like a supply chain with an unnecessary middleman. The key should determine everything directly. But if Key $\rightarrow$ Middleman $\rightarrow$ FinalAttribute, then the FinalAttribute is really about the Middleman, not about the Key. When the Middleman changes, you must update all the FinalAttribute references — even though the Key didn’t change. The middleman introduces a spurious coupling.

### 5.2 Definition

A relation $R$ is in 3NF if:

1. $R$ is in 2NF, and
2. For every nontrivial FD $X \rightarrow A$ (where $A$ is a single attribute), at least one of the following holds:
   - $X$ is a superkey of $R$, or
   - $A$ is a prime attribute (belongs to some candidate key).

**Why the "or $A$ is prime" escape clause?** This is the subtlety that distinguishes 3NF from BCNF. 3NF permits a non-superkey to determine a prime attribute. The intuition: prime attributes are part of some key, so they’re already “under the protection” of the identification mechanism. A dependency on a non-superkey that leads to a prime attribute doesn’t create the same redundancy because the prime attribute is, by definition, part of how we identify tuples.

### 5.3 Worked Example: EMP_DEPT with a Transitive Chain

Returning to our original table, now in 1NF but not yet 2NF:

```
EMP_DEPT(EmpID, EmpName, DeptID, DeptName, Building)
```

FDs:
- $\text{EmpID} \rightarrow \text{EmpName}, \text{DeptID}$
- $\text{DeptID} \rightarrow \text{DeptName}, \text{Building}$

Candidate key: $\text{EmpID}$. Prime: `EmpID`. Nonprime: `EmpName`, `DeptID`, `DeptName`, `Building`.

First, check 2NF: the key is a single attribute, so no partial dependencies are possible. The schema is in 2NF.

Now check for transitive dependencies. Look at the nonprime attributes: `DeptID` is nonprime, and it determines `DeptName` and `Building`. So we have:

$\text{EmpID} \rightarrow \text{DeptID} \rightarrow \text{DeptName}, \text{Building}$

`DeptID` is not a superkey (it doesn’t determine the whole tuple — it doesn’t determine `EmpID` or `EmpName`), and `DeptName` and `Building` are nonprime. This is a transitive dependency. **Violation of 3NF.**

**Anomaly:** If the Sales department moves buildings, we must update `Building` in every employee row belonging to Sales. The update touches rows identified by `EmpID` — the key hasn’t changed — but the fact we’re changing is about the department, not about the employee.

### 5.4 Decomposition to 3NF

We split along the transitive chain, isolating the middleman:

- $R_1(\text{EmpID}, \text{EmpName}, \text{DeptID})$ with key $\text{EmpID}$ and FD $\text{EmpID} \rightarrow \text{EmpName}, \text{DeptID}$. Here `DeptID` is nonprime, but it doesn’t determine anything else in this relation — it’s just an attribute, not a determinant of nonprime attributes. No transitive dependency.
- $R_2(\text{DeptID}, \text{DeptName}, \text{Building})$ with key $\text{DeptID}$ and FD $\text{DeptID} \rightarrow \text{DeptName}, \text{Building}$. `DeptID` is now a superkey in its own relation, so the FD’s left-hand side is a superkey. No violation.

**Try this yourself:** Write out the FDs for $R_1$ and $R_2$. Verify that in $R_1$, the only nontrivial FD with a single-attribute right-hand side is $\text{EmpID} \rightarrow \text{EmpName}$ (left side is a superkey) and $\text{EmpID} \rightarrow \text{DeptID}$ (left side is a superkey). In $R_2$, $\text{DeptID} \rightarrow \text{DeptName}$ and $\text{DeptID} \rightarrow \text{Building}$ both have a superkey on the left. No transitive dependencies remain.

---

## 6. Boyce-Codd Normal Form (BCNF): When 3NF Isn’t Enough

### 6.1 The 3NF Escape Clause in Action

3NF’s “or $A$ is prime” clause is a deliberate compromise. It allows certain schemas that still contain redundancy — but the redundancy is confined to prime attributes, which are part of some key. For many practical schemas, this is acceptable. But when it isn’t, BCNF closes the loophole.

**Intellectual tension:** 3NF guarantees that every nonprime attribute depends directly on a key. But what if a *prime* attribute depends on something that isn’t a superkey? That’s the scenario 3NF permits and BCNF forbids. The question is: does that scenario actually cause anomalies, or is it a theoretical curiosity? The answer: it causes anomalies — just more subtle ones.

### 6.2 Definition

A relation $R$ is in BCNF if for every nontrivial FD $X \rightarrow Y$, $X$ is a superkey of $R$.

Notice: no escape clause. No “unless $Y$ is prime.” Every determinant must be a superkey, period.

### 6.3 The Classic BCNF-Violating Example: TEACHES

Consider:

```
TEACHES(Student, Course, Instructor)
```

Rules:
- Each course is taught by exactly one instructor: $\text{Course} \rightarrow \text{Instructor}$.
- Each instructor teaches exactly one course (in this hypothetical school): $\text{Instructor} \rightarrow \text{Course}$.
- A student can take multiple courses with different instructors; the combination $\{\text{Student}, \text{Course}\}$ uniquely identifies a row; likewise $\{\text{Student}, \text{Instructor}\}$ uniquely identifies a row.

Candidate keys: $\{\text{Student}, \text{Course}\}$ and $\{\text{Student}, \text{Instructor}\}$. Prime attributes: `Student`, `Course`, `Instructor` — all three are prime because each belongs to at least one candidate key.

Check 3NF: The FD $\text{Course} \rightarrow \text{Instructor}$ has a left-hand side `Course` that is not a superkey (it doesn’t determine `Student`). But `Instructor` is a prime attribute. So 3NF’s escape clause applies: the right-hand side is prime, therefore no violation. The schema is in 3NF.

**But anomalies still occur:** Suppose we want to update the instructor for a course. We must update every row for every student enrolled in that course. If a course has 30 students, that’s 30 updates. The redundancy is in the prime attribute `Instructor`, but it’s still redundancy — and it still causes update anomalies.

**Check BCNF:** $\text{Course} \rightarrow \text{Instructor}$. `Course` is not a superkey. **Violation.** BCNF catches what 3NF lets pass.

### 6.4 Decomposition to BCNF

We split on the violating FD $\text{Course} \rightarrow \text{Instructor}$: