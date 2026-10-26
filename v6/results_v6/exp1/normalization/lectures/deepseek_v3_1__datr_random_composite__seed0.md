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

### 1.1 Starting with a Concrete Example

Imagine you’re building a company directory. You’ve got employees, departments, and buildings. The obvious first instinct is to put everything in one table — after all, each employee *has* a department, and each department *occupies* a building. So you write:

```
EMP_DEPT_BUILDING(EmpID, EmpName, DeptID, DeptName, Building)
```

Assume these real-world constraints:

- Each employee has a unique `EmpID`.
- Each employee belongs to exactly one department, identified by `DeptID`.
- Each department has one name (`DeptName`) and is housed in one building (`Building`).

Let’s populate this table with a small sample so we can see the problems concretely:

| EmpID | EmpName | DeptID | DeptName | Building |
|-------|---------|--------|----------|----------|
| E101  | Alice   | D01    | Sales    | Bldg A   |
| E102  | Bob     | D01    | Sales    | Bldg A   |
| E103  | Carol   | D02    | Marketing| Bldg C   |

Now try three everyday operations against this schema:

- **Update anomaly:** The Sales department moves from Building A to Building B. You must change `Building` in *every* row for every Sales employee (here, rows for Alice and Bob). Miss one row, and your database now asserts that Sales occupies two buildings simultaneously — a logical contradiction that no constraint can catch because the constraint isn’t expressed in the schema itself.
- **Insertion anomaly:** You want to record a brand-new department, Engineering, before any employees are hired into it. You cannot insert that row because `EmpID` is part of the primary key and cannot be null. The database forces you to invent a fake employee just to record a real department.
- **Deletion anomaly:** The last employee in Marketing (Carol) resigns. Deleting her row removes *all* record that Marketing ever existed, including its name and building. A single personnel action accidentally erases organizational structure.

These three anomalies share a single root cause: one table attempts to represent multiple independent facts — facts about employees, facts about departments, facts about buildings — and the schema has no mechanism to enforce their independence. The table is a physical container that conflates three separate logical truths.

> **Quick Check 1:** In the table above, which of the three anomalies would occur if we changed an employee’s name? (Hint: is an employee’s name a fact about the employee alone or about a combination of entities?)
>
> <details>
> <summary>Click for answer</summary>
> None of the three anomalies would occur. An employee's name is a fact about the employee alone — it depends only on `EmpID`. Changing "Alice" to "Alicia" requires updating exactly one row, and no information about departments or buildings is affected. The anomaly only arises when a fact about one entity (like a department's building) is stored redundantly across rows identified by a different entity's key (employee IDs).
> </details>

---

## 2. The Tool That Finds the Problem: Functional Dependencies

### 2.1 Intuition Before Formalism

Before we define anything formally, let’s build intuition. Consider the `EMP_DEPT_BUILDING` table from Section 1. Ask yourself: if I tell you an `EmpID`, can you tell me the employee’s name? Yes — each `EmpID` maps to exactly one name. If I tell you a `DeptID`, can you tell me the building? Yes — each department is in exactly one building.

Now ask: if I tell you a `DeptName`, can you tell me the `EmpID`? No — a department can have many employees, so knowing "Sales" doesn’t give you a unique employee ID.

This "if I know X, I can look up exactly one Y" relationship is what a functional dependency captures. It’s a statement about the real-world rules that the database must enforce.

### 2.2 Formal Definition

Normalization does not rely on intuition. It uses a precise, mechanical tool: the **functional dependency (FD)**. This is the diagnostic instrument that tells you *exactly* which facts are tangled together.

Let $R$ be a relation schema with attribute set $U$. An FD $X \rightarrow Y$ (read “$X$ determines $Y$”) means: in any valid instance of $R$, whenever two tuples agree on all attributes in $X$, they *must* agree on all attributes in $Y$.

**Analogy:** Think of $X \rightarrow Y$ as a mathematical function from $X$ to $Y$. Just as $f(x) = \sin(x)$ gives you exactly one output for each input, an FD says that for each value of $X$, there is exactly one corresponding value of $Y$ in the database. The database is enforcing that the mapping from $X$ to $Y$ is a function, not a relation that could branch.

**Intuition rephrased:** “If I know $X$, I can look up exactly one value for $Y$.” In the employee example:

- $\text{EmpID} \rightarrow \text{EmpName}$ — given an employee’s ID, there is exactly one name.
- $\text{DeptID} \rightarrow \text{DeptName}, \text{Building}$ — given a department ID, there is exactly one department name and exactly one building.

**Formal definition:** For any two tuples $t_1, t_2$ in $r(R)$, if $t_1[X] = t_2[X]$ then $t_1[Y] = t_2[Y]$. An FD is *nontrivial* when $Y \not\subseteq X$; otherwise it conveys no useful constraint (saying “knowing X determines X” is tautologically true but tells you nothing about structure).

### 2.3 Keys via FDs — The Critical Bridge

A **superkey** is any set of attributes $SK$ such that $SK \rightarrow U$ — knowing $SK$ determines the entire tuple. A **candidate key** $K$ is a *minimal* superkey: no attribute can be removed from $K$ while preserving the property $K \rightarrow U$. An attribute is **prime** if it belongs to at least one candidate key; otherwise it is **nonprime**.

These definitions form the lens through which every normal form is judged. The distinction between prime and nonprime is the fault line that separates 2NF from 3NF, and 3NF from BCNF.

### 2.4 Worked Example: Finding Keys from FDs

Let’s practice deriving candidate keys from a set of FDs. Consider:

```
R(A, B, C, D)
FDs: A → B,  B → C,  {A, D} → everything
```

We start with the closure of attribute sets. The closure of $X$, written $X^+$, is everything $X$ determines through the given FDs.

- $\{A\}^+ = \{A, B, C\}$ (A determines B; B determines C; so A determines A, B, and C)
- $\{B\}^+ = \{B, C\}$
- $\{A, D\}^+ = \{A, B, C, D\}$ — this is all attributes, so $\{A, D\}$ is a superkey.

Is $\{A, D\}$ minimal? Check subsets:
- $\{A\}^+ = \{A, B, C\}$ — does not include D, so not a superkey.
- $\{D\}^+ = \{D\}$ — does not include A, B, or C, so not a superkey.

Therefore $\{A, D\}$ is a candidate key. Prime attributes: A, D. Nonprime: B, C.

> **Quick Check 2:** In the relation `EMP(EmpID, Name, SSN)`, suppose both `EmpID` and `SSN` are unique per employee. What are the candidate keys? Which attributes are prime, which are nonprime?
>
> <details>
> <summary>Click for answer</summary>
> FDs: `EmpID → Name, SSN` and `SSN → EmpID, Name`. Candidate keys: `{EmpID}` and `{SSN}`. Prime attributes: `EmpID`, `SSN` (both appear in at least one candidate key). Nonprime: `Name` (appears in neither candidate key).
> </details>

---

## 3. First Normal Form (1NF): The Flat-Table Foundation

### 3.1 Intuition

Before we can apply the machinery of functional dependencies, we need a flat playing field. Every cell must contain exactly one value — not a list, not a nested table, not a set. Think of it as the requirement that each row–column intersection holds a single, indivisible piece of data. Without this, the relational operators (selection, projection, join) cannot work predictably.

### 3.2 Definition

A relation is in 1NF if every attribute domain contains only atomic (indivisible) values. No attribute may be relation-valued, set-valued, or contain repeating groups within a single cell.

### 3.3 Worked Example: Flattening a Non-1NF Table

Start with this non-1NF table:

```
DEPARTMENT(DeptID, DeptName, Employees)
```

Here `Employees` is a set of employee IDs. A sample row might be:

| DeptID | DeptName | Employees |
|--------|----------|-----------|
| D01    | Sales    | {E1, E2}  |

A single cell contains multiple values. This breaks even simple queries — to find all employees in Sales, we can’t just write `SELECT Employees FROM DEPARTMENT WHERE DeptID = 'D01'` and get a usable result; we’d have to parse the set.

To reach 1NF, we have two choices:

1. **Flatten:** Expand each set element into its own row:
   ```
   DEPARTMENT(DeptID, DeptName, EmployeeID)
   ```
   | DeptID | DeptName | EmployeeID |
   |--------|----------|------------|
   | D01    | Sales    | E1         |
   | D01    | Sales    | E2         |

   Now every cell holds exactly one atomic value. The department name is repeated, but that’s a redundancy problem for higher normal forms to solve — 1NF only cares about atomicity.

2. **Decompose:** Split into two relations:
   ```
   DEPARTMENT(DeptID, DeptName)
   DEPT_EMP(DeptID, EmployeeID)
   ```
   This eliminates the repetition entirely by separating the facts.

In both results, every cell holds exactly one atomic value. The choice between flattening and decomposing is not neutral — decomposition often anticipates further normalization, while flattening can introduce the very redundancy that higher normal forms aim to eliminate.

### 3.4 Common Misconception

**Misconception:** "1NF means no duplicate rows."

**Correction:** 1NF does *not* mean “no duplicate rows.” Duplicate rows are a separate issue handled by the relational model’s set semantics (a relation is a set of tuples, so duplicates are impossible by definition — though SQL implementations may permit them). 1NF only prohibits non-atomic cell contents.

### 3.5 Limitation

A schema in 1NF can still suffer from all three anomalies. 1NF is a starting point, not a destination. It clears the ground so that functional dependencies can operate on flat attributes, but it does nothing to untangle the dependencies themselves.

> **Quick Check 3:** Why would a column storing comma-separated values like `'Math,Physics'` violate 1NF? (Consider: what would a query asking “find all employees enrolled in Physics” have to do to that column?)
>
> <details>
> <summary>Click for answer</summary>
> The value `'Math,Physics'` is not atomic — it encodes two separate facts in one cell. A query looking for Physics students would need to parse the string, search for the substring "Physics", and handle edge cases (what if a course name contains a comma? what about partial matches like "PhysicsLab"?). The relational model assumes each cell holds one value so that operators like `=` and `JOIN` work directly. With comma-separated values, you lose the ability to use standard relational operations and must resort to error-prone string manipulation.
> </details>

---

## 4. Second Normal Form (2NF): Eliminating Partial Dependencies

### 4.1 Motivation and Intuition

2NF targets a specific situation that 1NF leaves untouched: the primary key is composite (made of multiple attributes), yet some non-key attribute depends on only *part* of that key. When that happens, the attribute is really describing one of the key parts, not the whole combination.

**Analogy:** Imagine a library catalog where each row represents a book–borrower pair, and the key is `{BookID, BorrowerID}`. If you store the book’s title in this table, the title depends only on `BookID` — it has nothing to do with who borrowed it. The title is "along for the ride" on every row, repeated for every borrower of that book. It belongs in a separate `Books` table where `BookID` alone is the key.

### 4.2 Definition

A relation $R$ is in 2NF if:

1. $R$ is in 1NF, and
2. Every nonprime attribute is *fully* functionally dependent on every candidate key. That means no nonprime attribute $A$ satisfies $K' \rightarrow A$ where $K'$ is a proper subset of a candidate key $K$.

**Important nuance:** Notice what this definition *doesn’t* say. It doesn’t say “no nonprime attribute depends on part of the primary key.” It says “every candidate key.” If a relation has multiple candidate keys, 2NF checks all of them. A schema can satisfy 2NF with respect to one key and still fail with respect to another — but the definition requires satisfaction for every candidate key.

### 4.3 Worked Example: The Classic EMP_PROJ

Consider a schema that tracks which employees work on which projects and for how many hours:

```
EMP_PROJ(EmpID, ProjID, EmpName, ProjLocation, Hours)
```

Let’s populate a small instance to make the dependencies concrete:

| EmpID | ProjID | EmpName | ProjLocation | Hours |
|-------|--------|---------|--------------|-------|
| E1    | P10    | Alice   | New York     | 20    |
| E1    | P20    | Alice   | Boston       | 15    |
| E2    | P10    | Bob     | New York     | 30    |

We identify the FDs from the real-world rules:

- $\text{EmpID} \rightarrow \text{EmpName}$ (an employee’s ID determines their name)
- $\text{ProjID} \rightarrow \text{ProjLocation}$ (a project’s ID determines its location)
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$ (the combination determines hours worked)

Candidate key: $\{\text{EmpID}, \text{ProjID}\}$. Prime attributes: `EmpID`, `ProjID`. Nonprime: `EmpName`, `ProjLocation`, `Hours`.

Now inspect the nonprime attributes against the key. This is where the definition applies — we’ve identified the FDs, now we check each one:

- `EmpName` depends on `EmpID` alone — a proper subset of the key. This is a partial dependency. **Violation.**
- `ProjLocation` depends on `ProjID` alone — another partial dependency. **Violation.**
- `Hours` depends on the full key $\{\text{EmpID}, \text{ProjID}\}$ — no violation. `Hours` is the only attribute that genuinely describes the *intersection* of an employee and a project. Notice in the table: Alice works 20 hours on P10 and 15 hours on P20 — hours vary with both employee and project.

**Anomalies caused:**

- Update: Changing Alice’s name requires updating every row for Alice across all projects. If she’s on 20 projects, that’s 20 updates.
- Insertion: Cannot record a new employee’s name until they are assigned to at least one project. The schema holds the employee’s identity hostage to project participation.
- Deletion: If an employee finishes their last project and that row is deleted, we lose their name entirely. The employee ceases to exist in the database.

### 4.4 Decomposition to 2NF

We split along the violating FDs, ensuring each resulting relation has a key that fully determines its nonprime attributes:

- $R_1(\text{EmpID}, \text{EmpName})$ with key $\text{EmpID}$. Single-attribute key: trivially full dependence — no subset to depend on partially.
- $R_2(\text{ProjID}, \text{ProjLocation})$ with key $\text{ProjID}$. Single-attribute key: trivially full dependence.
- $R_3(\text{EmpID}, \text{ProjID}, \text{Hours})$ with key $\{\text{EmpID}, \text{ProjID}\}$. Here `Hours` depends on the full key — no partial dependency remains.

> **Test Yourself — 2NF:** Before reading on, write down the FDs for each of $R_1$, $R_2$, and $R_3$. Verify that in each relation, every nonprime attribute depends on the *entire* candidate key, not on any subset.
>
> <details>
> <summary>Click for verification</summary>
> - $R_1$: FD is `EmpID → EmpName`. Candidate key is `{EmpID}` (single attribute, so no proper subset exists). Nonprime attribute `EmpName` depends on the full key. ✓
> - $R_2$: FD is `ProjID → ProjLocation`. Candidate key is `{ProjID}`. Nonprime attribute `ProjLocation` depends on the full key. ✓
> - $R_3$: FD is `{EmpID, ProjID} → Hours`. Candidate key is `{EmpID, ProjID}`. Nonprime attribute `Hours` depends on the full key (check: does `EmpID` alone determine `Hours`? No — Alice has different hours on different projects. Does `ProjID` alone determine `Hours`? No — P10 has different hours for Alice and Bob). ✓
>
> All three are in 2NF.
> </details>

### 4.5 Common Pitfall: Relations with Only Single-Attribute or All-Prime Keys

A relation whose every candidate key consists of a single attribute is automatically in 2NF. Why? Because a proper subset of a single-attribute key is the empty set, and the empty set cannot functionally determine any nonprime attribute (unless that attribute is constant across all tuples, which is a degenerate case). There is simply no partial dependency possible — there is no "part" of the key to depend on.

Similarly, a relation where *every* attribute is prime (an all-key relation) is automatically in 2NF. The definition of 2NF only constrains nonprime attributes. If there are no nonprime attributes, there are no partial dependencies to violate the condition. This observation will become important when we distinguish 3NF from BCNF in Section 6.

---

## 5. Third Normal Form (3NF): Eliminating Transitive Dependencies

### 5.1 The Gap 2NF