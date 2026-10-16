## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember:** Define functional dependency, partial dependency, and transitive dependency in your own words.
2.  **Understand:** Explain how update, insertion, and deletion anomalies arise from a single-table design and identify their root cause.
3.  **Apply:** Given a relation schema and a set of functional dependencies, determine whether the schema satisfies 1NF, 2NF, and 3NF, and identify the specific violating dependencies.
4.  **Analyze:** Decompose a non-normalized schema into lossless-join, normalized relations (up to 3NF) by mechanically isolating the violating functional dependencies.
5.  **Create:** Given a textual description of a business domain, derive the functional dependencies, identify candidate keys, and design a normalized relational schema that avoids the three classic anomalies.

---

## 0. Opening: The $10 Million Typo

In 2015, a major financial institution reported a $10 billion asset to regulators as $10 million. The root cause was not a faulty calculation but a data update that propagated incorrectly across a poorly designed database. One fact—the asset's value—was stored in hundreds of rows, and a single missed update cascaded into regulatory filings, internal risk models, and client reports. The error persisted for months before detection.

This is not a story about careless programmers. It is a story about schema design. When the same fact lives in multiple places, inconsistency is not a possibility—it is a statistical inevitability. Normalization is the systematic discipline that prevents this class of failure. By the end of this lecture, you will be able to look at any table design and predict, with mechanical precision, exactly where and how it will break.

---

## 1. Prerequisites

Before we begin, ensure you are comfortable with these foundational concepts. We will use them extensively.

- **Relation / Table:** A set of tuples (rows), each with the same attributes (columns).
- **Attribute:** A named column of a relation, drawn from a domain of atomic values.
- **Tuple:** A single row in a relation, representing one fact or entity instance.
- **Superkey:** A set of one or more attributes that uniquely identifies each tuple in a relation.
- **Candidate Key:** A *minimal* superkey—you cannot remove any attribute from it without destroying its uniqueness property.
- **Primary Key:** The one candidate key chosen by the designer as the main identifier for the relation.
- **Prime Attribute:** An attribute that belongs to *at least one* candidate key.
- **Nonprime Attribute:** An attribute that does *not* belong to *any* candidate key.

The entire normalization ladder is built on the distinction between prime and nonprime attributes. Review these terms if they are unclear.

---

## 2. Why Normalize? The Pathology of a Single Table

### 2.1 Intuition: One Table, Many Headaches

Imagine you are building the database for a logistics company. A trucking manager states, "We need to track drivers, their assigned trucks, and the truck's home depot." A natural starting point is a single spreadsheet. Months later, a truck moves to a new depot, and someone updates only one of the five drivers assigned to it. The system now claims the same truck is in two different cities. Your reporting is corrupted, and you have no easy way to detect which record is correct.

This is not a bug in your application code; it is a structural flaw in your table design. Good database design represents independent facts independently. A schema that conflates multiple facts into a single relation introduces predictable, systematic data pathologies called **anomalies**. Before we introduce formalism, we examine the problems a single table can create.

### 2.2 Concrete Example: The Employee-Department-Building Table

Consider a simple design for a company directory that tracks employees, their departments, and departmental buildings:

```
EMP_DEPT_BUILDING(EmpID, EmpName, DeptID, DeptName, Building)
```

Assume the following business rules:
- Each employee has a unique `EmpID`.
- Each employee belongs to exactly one department, identified by `DeptID`.
- Each department has exactly one `DeptName` and is housed in exactly one `Building`.

We populate this design with sample data to see the problems firsthand.

| EmpID | EmpName | DeptID | DeptName  | Building |
| :---- | :------ | :----- | :-------- | :------- |
| 1     | Alice   | D01    | Sales     | Alpha    |
| 2     | Bob     | D01    | Sales     | Alpha    |
| 3     | Charlie | D02    | Marketing | Beta     |

This single-table design is subject to three classic anomalies:

- **Update Anomaly:** If the Sales department relocates from Building Alpha to Building Gamma, this single fact about the department must be updated in *every* tuple for a Sales employee (Alice and Bob). A partial update leaves the database in a logically inconsistent state, asserting that Sales occupies two buildings simultaneously. The schema provides no mechanism to enforce the integrity of this independent fact.

- **Insertion Anomaly:** Suppose a new department, Engineering, is created but has not yet hired any employees. It is impossible to record the department's existence, name, and building because `EmpID`, as part of the primary key, cannot be null. The schema forces a coupling between the existence of a department and the existence of at least one employee in it.

- **Deletion Anomaly:** If Charlie, the last employee in the Marketing department, resigns and his tuple is deleted, all information about Marketing's name and building is lost. A routine personnel action accidentally destroys information about an organizational entity.

**Try This Yourself:** Before reading further, look at the table above and identify: which columns contain facts about employees, and which contain facts about departments? Draw a line separating them. You have just performed the core intuition behind normalization—recognizing that one table is secretly carrying two separate conceptual entities.

### 2.3 Root Cause: Conflated Facts

The root cause of all three anomalies is the same: the single relation attempts to represent two separate conceptual entities—employee facts (`EmpID` → `EmpName`, `DeptID`) and department facts (`DeptID` → `DeptName`, `Building`).

Think of this like a library catalog that stores both book information and author biographies on the same card. If an author wins a prize, you must update every card for every book they wrote. Miss one, and the catalog contradicts itself. The problem is not the update operation—it is that the author's biography does not belong on the book card at all.

Normalization theory provides a formal framework to detect and repair this conflation. In current industry practice, relational database management systems (RDBMS) such as PostgreSQL, MySQL, and Oracle use these principles when physical schema designs are reviewed: database architects explicitly model functional dependencies to produce normalized logical schemas before any physical tuning such as indexing or partitioning is applied.

> **Quick Check 1:** In the `EMP_DEPT_BUILDING` table, suppose we change Alice's name from "Alice" to "Alicia." Which of the three anomalies would this trigger?
>
> *(Answer: None. An employee's name is a fact about the employee alone. Since `EmpID` is unique, Alice's name appears in only one tuple. Changing it affects no other entity and requires no multi-tuple update. Anomalies arise only when independent facts—like a department's building—are duplicated across multiple tuples.)*

---

## 3. The Diagnostic Instrument: Functional Dependencies

### 3.1 Intuition: "If You Know X, You Know Y"

Normalization is a rigorous, mechanical procedure grounded in the concept of a **functional dependency (FD)**. An FD is a constraint between two sets of attributes that formally captures a real-world business rule.

Here is an analogy from chemistry that makes this precise: the periodic table embodies a functional dependency. Knowing an element's atomic number (`Z`) functionally determines its chemical symbol (`Z → Symbol`). If two samples have atomic number 6, they must both be carbon—there is no ambiguity, no exception. An FD in a database is the same kind of law: given a value for the determinant, the dependent value is forced to be exactly one thing. Just as you cannot have carbon with atomic number 6 and also atomic number 7, you cannot have department D01 located in both Building Alpha and Building Gamma if the FD `DeptID → Building` is enforced.

### 3.2 Formal Definition

Let $R$ be a relation schema with attribute set $U$. A functional dependency, denoted $X \rightarrow Y$ (read as "$X$ functionally determines $Y$"), holds over $R$ if, for any valid relation instance $r$ of $R$, whenever two tuples $t_1, t_2 \in r$ agree on all attributes in $X$, they must also agree on all attributes in $Y$. Formally:
$$\forall t_1, t_2 \in r: t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]$$

An FD is **nontrivial** if $Y \not\subseteq X$. Trivial FDs (e.g., $\{A, B\} \rightarrow B$) always hold but provide no structural information—they tell us nothing about the real-world rules we are modeling.

### 3.3 Worked Example: Spotting an FD

Look at the `EMP_DEPT_BUILDING` table. We suspect the FD $\text{DeptID} \rightarrow \text{Building}$ holds. To verify, we ask: are there any two tuples with the same `DeptID` but different `Building`?
- Alice and Bob both have `DeptID = \text{D01}` and both have `Building = \text{Alpha}`.
- Charlie has `DeptID = \text{D02}` and `Building = \text{Beta}`.

The constraint holds for this instance. If we tried to insert a tuple `(4, Dave, D01, Sales, Gamma)`, the DBMS would reject it if this FD is enforced, because `D01` already determines `Alpha`. In practice, such FDs are often enforced through `UNIQUE` constraints or application-level logic. Systems like PostgreSQL can use triggers to validate functional dependencies not directly backed by key constraints.

In our example, the full set of nontrivial FDs derived from the business rules is:
- $\text{EmpID} \rightarrow \text{EmpName}, \text{DeptID}$: An employee's ID determines their name and department.
- $\text{DeptID} \rightarrow \text{DeptName}, \text{Building}$: A department's ID determines its name and building.

### 3.4 Keys as a Special Case of FDs

The concept of a key is defined directly from FDs.
- A **superkey** $SK$ is a set of attributes such that $SK \rightarrow U$ (it functionally determines *all* attributes in the relation).
- A **candidate key** $K$ is a *minimal* superkey. No proper subset of $K$ is a superkey; removing any attribute from $K$ destroys the property $K \rightarrow U$.

This distinction between prime and nonprime attributes is the fundamental axis on which the higher normal forms turn. It is the precise, formal line that separates 2NF from 3NF and 3NF from BCNF.

> **Quick Check 2:** In a relation `EMP(EmpID, Name, SSN)`, suppose both `EmpID` and `SSN` are unique for each employee. What are the candidate keys? Classify each attribute as prime or nonprime.
>
> *(Answer: Candidate keys are {EmpID} and {SSN}. Both are minimal superkeys. `EmpID` and `SSN` are prime. `Name` is nonprime.)*

---

## 4. First Normal Form (1NF): The Atomicity Foundation

### 4.1 Intuition: No Lists Inside Cells

Before we can apply functional dependencies to diagnose anomalies, we need a flat, regular playing field. 1NF ensures that every attribute in a tuple holds a single, indivisible value. It is the rule that says "no repeating groups, no lists inside a single cell."

Why does this matter so fundamentally? Consider what happens when you try to sort a column where some cells contain "Java, Python" and others contain "Python, Java." Are these equal? Does "Python" come before or after "Java" in a sort order? The relational model's operators—selection, projection, join—all assume they are comparing atomic values. A list inside a cell breaks the algebra the same way that trying to add "apple" to the number 5 breaks arithmetic: the operation is no longer well-defined.

### 4.2 Definition

A relation $R$ is in First Normal Form (1NF) if the domain of every attribute contains only atomic (indivisible) values. No attribute may be relation-valued, set-valued, or contain repeating groups within a single tuple's cell. The value in each cell must be a single logical datum from the attribute's domain.

**Motivation and Rationale.** The relational algebra, the formal query language underpinning SQL, operates on flat, two-dimensional tables. A cell containing a composite structure like a list `{101, 102, 103}` breaks fundamental operators like selection ($\sigma$) and projection ($\pi$), which expect a single value per attribute per tuple. 1NF is a prerequisite for the algebraic machinery of the relational model to function correctly. Modern SQL databases enforce 1NF by design: a standard SQL column cannot hold an array or nested table without using explicit, non-atomic extensions such as PostgreSQL arrays or JSONB, which deliberately step outside the strict relational model.

### 4.3 Worked Example: Flattening a Non-1NF Table

Consider this non-1NF representation of departments and their employees:

```
DEPARTMENT_NON_1NF(DeptID, DeptName, Employees)
```
Here, the `Employees` attribute is a set of employee IDs. A sample row would be:
`(D01, Sales, {E1, E2})`.

To achieve 1NF, we have two decomposition strategies.

**Strategy 1: Flattening.** Expand each set element into its own tuple, repeating the other attributes. The single row `(D01, Sales, {E1, E2})` produces two rows:

```
DEPARTMENT_FLAT(DeptID, DeptName, EmployeeID)
(D01, Sales, E1)
(D01, Sales, E2)
```

Each cell now holds exactly one atomic value. The cost is that `DeptName` "Sales" is repeated—a redundancy that higher normal forms will address.

**Strategy 2: Decomposition.** Split the original relation into two relations, separating the independent facts.

```
DEPARTMENT(DeptID, DeptName)
DEPT_EMP(DeptID, EmployeeID)
```

With data:
- `DEPARTMENT`: `(D01, Sales)`
- `DEPT_EMP`: `(D01, E1)`, `(D01, E2)`

This strategy eliminates the repetition of `DeptName` entirely. The choice between flattening and decomposition is not neutral. Flattening often introduces the redundancy that higher normal forms (2NF, 3NF) are designed to eliminate, while decomposition often anticipates and aligns with those forms.

**Cross-Domain Connection:** This same flattening-versus-decomposition decision appears in data science workflows daily. When a data scientist receives a JSON file with nested objects from a REST API, they face exactly the 1NF normalization problem before any analysis can begin. Pandas' `json_normalize()` function in Python is, at its core, a 1NF flattening operation. The resulting DataFrame often contains the exact kind of redundancy that 2NF and 3NF are designed to eliminate—which is why data engineers build normalized star schemas in data warehouses like Snowflake rather than dumping flattened JSON directly into analytics tables.

**Common Misconception.** 1NF does *not* prohibit duplicate rows. The relational model is based on set theory; a relation is a set of tuples, and duplicates are impossible by definition. 1NF is exclusively concerned with the atomicity of values within a single tuple's attributes.

**Limitation.** A schema in 1NF can still suffer from all three types of anomalies. 1NF is a necessary starting point, not a final destination. It clears the ground so that functional dependencies can operate on flat attributes, but it performs no analysis of the dependencies themselves.

> **Quick Check 3:** A column `Skills` storing comma-separated values like `'Java,Python,SQL'` violates 1NF. Consider a query to "find all employees who have the 'Python' skill." What operation would the query have to perform on the `Skills` column, and why is this a violation of the atomicity principle?
>
> *(Answer: The query would need a substring search or pattern match (e.g., `LIKE '%Python%'`), treating the cell's content as a composite structure rather than an atomic value. This is error-prone—it would also match "Jython" or "PythonScript"—and breaks the principle that each cell holds a single logical datum. The DBMS cannot index or enforce integrity on individual skills because it cannot see them as separate values.)*

---

## 5. Second Normal Form (2NF): Eliminating Partial Dependencies

### 5.1 Intuition: A Fact About Part of the Key

Consider a table with a composite primary key, such as an employee's ID and a project's ID. If an attribute like "employee name" depends only on the employee ID (a *part* of the key) and not on the full key, we have a problem. The employee name is a fact about the employee, not about the employee-project assignment. This is a **partial dependency**, and it means we are mixing facts about two different entities in one table, leading to redundancy.

Here is the tension that 2NF resolves: the composite key {EmpID, ProjID} identifies a specific assignment of an employee to a project. Any fact that depends on only *half* of that key is not a fact about the assignment—it is a fact about the employee or the project alone. The table is secretly trying to be three tables at once. 2NF is the formal procedure for detecting and separating these conflated identities.

### 5.2 Formal Definition

A relation $R$ is in Second Normal Form (2NF) if:
1.  $R$ is in 1NF, and
2.  Every nonprime attribute $A$ in $R$ is **fully functionally dependent** on *every* candidate key of $R$.

"Fully functionally dependent" means there is no functional dependency $K' \rightarrow A$ where $K'$ is a proper subset of a candidate key $K$. In other words, you cannot determine $A$ by knowing only a part of any candidate key. The definition explicitly checks against *all* candidate keys, not just the primary key. A schema can be in 2NF with respect to one key but fail with respect to another, which constitutes a violation.

### 5.3 Worked Example: The EMP_PROJ Relation

Consider a schema tracking employee assignments to projects:
```
EMP_PROJ(EmpID, ProjID, EmpName, ProjLocation, Hours)
```

The functional dependencies derived from the business rules are:
- $\text{EmpID} \rightarrow \text{EmpName}$ (an employee's ID determines their name)
- $\text{ProjID} \rightarrow \text{ProjLocation}$ (a project's ID determines its location)
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$ (the combination determines the hours worked)

**Step 1: Identify candidate keys.** We test attribute sets to see what functionally determines all attributes. `EmpID` alone does not determine `ProjLocation` or `Hours`. `ProjID` alone does not determine `EmpName` or `Hours`. The pair $\{\text{EmpID}, \text{ProjID}\}$ determines `EmpName` (via `EmpID`), `ProjLocation` (via `ProjID`), and `Hours` (directly). It is minimal—removing either attribute loses the superkey property. The sole candidate key is $\{\text{EmpID}, \text{ProjID}\}$.

**Step 2: Classify attributes.**
- Prime attributes: `EmpID`, `ProjID` (members of the candidate key).
- Nonprime attributes: `EmpName`, `ProjLocation`, `Hours`.

**Step 3: Test for partial dependencies.** We check each nonprime attribute: does it depend on a *proper subset* of the candidate key?
- `EmpName`: The FD $\text{EmpID} \rightarrow \text{EmpName}$ holds. The left-hand side $\{\text{EmpID}\}$ is a proper