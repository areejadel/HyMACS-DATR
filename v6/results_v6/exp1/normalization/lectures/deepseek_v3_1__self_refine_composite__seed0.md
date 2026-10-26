# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember** the precise definitions of 1NF, 2NF, 3NF, and BCNF, and state which class of anomaly each form eliminates.
2.  **Understand** how update, insertion, and deletion anomalies arise from poor schema design, and how functional dependencies provide the formal mechanism to detect them.
3.  **Apply** a step-by-step decomposition algorithm to a given relation, using its functional dependencies and candidate keys, to produce a lossless-join decomposition in 3NF or BCNF.
4.  **Analyze** a real-world schema to identify its current normal form and pinpoint the exact functional dependency that violates the next higher form.
5.  **Evaluate** when to stop normalization (3NF vs. BCNF), when deliberate denormalization is a defensible performance trade-off, and what dependency-preservation guarantees are sacrificed at each step.

---

## 1. Why Normalize? The Problem in One Table

### 1.1 Prerequisites

We build on the following concepts. You should be comfortable with:

- The relational model: a relation is a table with rows (tuples) and columns (attributes).
- The concept of a primary key: a minimal set of attributes that uniquely identifies each row.
- Basic SQL: `SELECT`, `INSERT`, `UPDATE`, `DELETE`, and simple `JOIN` operations.
- The idea that a database schema is a blueprint for the structure of data, independent of the data currently stored.

If any of these feel unfamiliar, pause and review them—every concept that follows depends on this foundation.

### 1.2 The Hook: The Database That Cannot Contradict Itself—Yet Does

Here is a puzzle that has cost organizations millions of dollars and that your DBMS will not save you from.

You declare a `UNIQUE` constraint on employee ID. You declare a `CHECK` constraint that building codes must match a valid list. You declare foreign keys. Every constraint you explicitly wrote is enforced perfectly. Yet your database now asserts, with complete confidence, that the Sales department occupies Building A in row 17 and Building B in row 42.

No alarm sounds. No constraint fires. The DBMS is not broken—it is doing exactly what you told it to do. The problem is what you *did not* tell it: that a department can only be in one building. You never codified that rule because the schema gave you no natural place to put it. The structure itself—one table mixing facts about employees, departments, and buildings—permits the contradiction by storing the same real-world fact in multiple rows.

Normalization is the systematic process of restructuring the schema so that the structure itself enforces these hidden rules. In a normalized database, every fact about the world lives in exactly one place. You cannot accidentally create two versions of the truth because there is only one place to store it. This is not about saving disk space or making queries faster—it is about the difference between a database that *might* be consistent and one that *cannot be otherwise*.

**The core tension of this entire lecture:** Every normal form we study is a response to a specific, diagnosable way that a schema can permit logical contradictions. By the end, you will be able to look at any table design and say: "This schema can lie to me about X, because of functional dependency Y, and the fix is decomposition Z."

### 1.3 Intuition: One Table, Too Many Stories

Imagine a filing cabinet where each folder contains an employee's information, their department's information, and the building that department occupies—all stapled together. When the Sales department moves to a new building, you must open every Sales employee's folder and update the building address. Missing one folder creates a contradiction: the cabinet now claims Sales is in two buildings simultaneously. If you want to create a folder for a brand-new department that has no employees yet, you cannot—every folder requires an employee name on the tab. And if the last employee in Marketing leaves, shredding their folder destroys all record that Marketing ever existed.

This is exactly what happens when a database stores unrelated facts in a single relation. Normalization is the systematic process of separating these facts so that each lives in its own place, updated once and referenced everywhere.

> **Analogy: The Library Catalog**
>
> Think of a relation as a library catalog card. A well-designed catalog has one card per book, with author name, title, and ISBN. If you also store the author's biography on every card for every book they wrote, you have a problem: when the author wins a prize, you must update hundreds of cards. Worse, if you want to add a new author who hasn't published yet, you cannot create a card because every card requires a book. The catalog is trying to be both a book index and an author directory simultaneously. Normalization separates these into two catalogs, each responsible for one kind of fact.
>
> **Why this analogy is precise:** The catalog card is a *tuple*; the author's biography is a *non-key attribute functionally dependent on author, not on the book*. The inability to add an author without a book is an *insertion anomaly* caused by a partial dependency—the very definition of a 2NF violation. We will make this formal soon.

### 1.4 A Concrete Example

Consider a company directory tracking employees, departments, and buildings. A naive design places all facts in a single relation:

```
EMP_DEPT_BUILDING(EmpID, EmpName, DeptID, DeptName, Building)
```

Assume these real-world constraints:

- Each employee has a unique `EmpID`.
- Each employee belongs to exactly one department, identified by `DeptID`.
- Each department has one name (`DeptName`) and is housed in exactly one building (`Building`).

Sample data reveals the problems concretely:

| EmpID | EmpName | DeptID | DeptName | Building |
|-------|---------|--------|----------|----------|
| E1    | Alice   | D01    | Sales    | A        |
| E2    | Bob     | D01    | Sales    | A        |
| E3    | Carol   | D02    | Marketing| B        |

Three anomalies are evident:

- **Update anomaly:** If Sales relocates from Building A to Building B, the `Building` attribute must be updated in *every* tuple for Sales employees (E1 and E2). Updating E1 but missing E2 leaves the database asserting that Sales occupies both Building A and Building B—a logical contradiction. No declarative constraint can prevent this because the dependency is not structurally enforced.

- **Insertion anomaly:** We wish to record a newly created department, Engineering (D03, Building C), before any employees are hired. We cannot insert this tuple because `EmpID` is part of the primary key and cannot be null. The schema forces us to fabricate a dummy employee solely to record a legitimate organizational fact.

- **Deletion anomaly:** Carol (E3), the last employee in Marketing, resigns. Deleting her tuple removes *all* evidence that Marketing ever existed—its name, its building assignment, everything. A routine personnel action accidentally destroys organizational data.

These anomalies share a single root cause: one relation attempts to represent multiple independent entity types (employees, departments, buildings) without any mechanism to enforce their independence. The schema conflates distinct logical truths into a single physical container.

> **Try this yourself:** Before reading further, look at the sample data above. Can you identify which specific fact is stored redundantly? (Hint: it is not the employee names.) What would you need to change in the schema to store that fact exactly once?
>
> <details>
> <summary>Reveal answer</summary>
> The fact "Department D01 is named Sales and is in Building A" is stored twice—once in Alice's row and once in Bob's row. The employee names are not redundant because each employee appears only once. To store the department fact exactly once, we would need to separate employees and departments into two different relations. This is exactly what normalization does.
> </details>

**Practical context across industries:** The cost of redundant storage manifests in diverse domains. In healthcare, a hospital information system stored patient insurance provider details redundantly within every visit record; when a provider changed its billing address, a partial update caused claim rejections for three months, delaying millions in revenue. In e-commerce, a major retailer stored product category tax rates alongside every line item in orders; a mid-year tax regulation change required updating hundreds of millions of historical rows, and a batch job failure left 2% of records with the old rate, triggering a regulatory audit. In logistics, a shipping company stored warehouse location data redundantly across shipment manifests; a warehouse relocation created conflicting routing instructions that sent trucks to both the old and new addresses for the same facility. In each case, the root cause was identical: a fact about one entity (provider, product category, warehouse) was stored alongside facts about a different entity (visit, order line, shipment). Normalization would have prevented each of these failures by ensuring each fact resides in exactly one place.

> **Quick Check 1:** In the relation above, which of the three anomalies would occur if we changed an employee's name? Is an employee's name a fact about the employee alone or about a combination of entities?
>
> <details>
> <summary>Reveal answer</summary>
> Changing an employee's name would cause an <strong>update anomaly</strong> only if the name were stored redundantly. Here, each employee appears exactly once (`EmpID` is the key), so a name change touches only one row—no anomaly. An employee's name is a fact about the employee alone. The anomalies arise from facts about <em>departments</em> (`DeptName`, `Building`) being stored redundantly alongside employee facts. This observation is the seed of normalization: separate facts about different things into different relations.
> </details>

---

## 2. The Diagnostic Instrument: Functional Dependencies

### 2.1 Intuition: "If You Know X, You Know Y"

Normalization does not rely on intuition. It uses a precise, mechanical tool: the **functional dependency (FD)**. An FD is a statement of the form: "If I tell you the value of X, there is exactly one possible value for Y." In our example: if I tell you an employee's ID, there is exactly one name that employee can have. If I tell you a department's ID, there is exactly one building that department can occupy.

The power of FDs is that they make the hidden rules *visible and machine-checkable*. When we said earlier that "a department can only be in one building," we were stating an FD: $\text{DeptID} \rightarrow \text{Building}$. Once we write that down, we can algorithmically detect whether a schema permits contradictions—and algorithmically fix it.

> **Cross-domain connection: Functions in Mathematics**
>
> A functional dependency is literally a function in the mathematical sense. In $f(x) = y$, each $x$ maps to exactly one $y$. The FD $X \rightarrow Y$ asserts the same thing: each value of $X$ maps to exactly one value of $Y$. The difference is that in databases, this function is not computed by a formula—it is enforced as a constraint on stored data. If you have taken discrete mathematics, you already understand FDs: they are functions from the domain of $X$ to the domain of $Y$, embedded in your schema. And just as mathematical functions can be composed ($f(g(x))$), FDs can be chained via transitivity—a property that will prove essential for detecting hidden violations.

These are not guesses from looking at the current data. They are business rules—truths about the domain that hold regardless of what data happens to be stored right now. This distinction is critical: you cannot discover FDs by inspecting a table; you must learn them from the domain expert who knows what the data means.

### 2.2 Definition and Notation

Let $R$ be a relation schema with attribute set $U$. A functional dependency $X \rightarrow Y$ (read "$X$ functionally determines $Y$") is a constraint stating: in any valid relation instance $r$ of $R$, whenever two tuples $t_1, t_2 \in r$ agree on all attributes in $X$, they *must* agree on all attributes in $Y$.

Formally:

$$\forall t_1, t_2 \in r(R): t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]$$

**Worked example:** In our sample data, does $\text{DeptID} \rightarrow \text{Building}$ hold? We check every pair of tuples with the same `DeptID`:

- E1 and E2 both have `DeptID` = D01. Do they agree on `Building`? Yes—both have `Building` = A.
- E3 has `DeptID` = D02. No other tuple shares this `DeptID`, so the condition is vacuously satisfied.

The FD holds in this instance. More importantly, the *business rule* says it must hold in every possible instance—a department cannot be split across two buildings. If someone later tries to insert a tuple with `DeptID` = D01 and `Building` = C, the DBMS should reject it. But without normalization, the DBMS has no mechanism to enforce this rule—it does not know the rule exists.

An FD is **nontrivial** if $Y \not\subseteq X$. Trivial FDs (where $Y \subseteq X$) are tautologically true and convey no structural constraint. For example, $\{\text{EmpID}, \text{DeptID}\} \rightarrow \text{EmpID}$ is trivial—knowing both already means you know `EmpID`. Normalization theory concerns itself exclusively with nontrivial FDs.

> **Common Misconception #1: "FDs can be discovered by looking at data."**
>
> This is dangerously wrong. The current data might happen to satisfy an FD by coincidence. For example, if all employees currently have unique names, the data satisfies $\text{EmpName} \rightarrow \text{EmpID}$—but this is not a business rule; tomorrow we could hire a second "Alice" and the FD would fail. FDs are constraints that must hold in *all possible valid states* of the database, not just the current one. Always obtain FDs from domain experts and business rules, never from data inspection alone.

### 2.3 FDs from Domain Knowledge: A Second Concrete Example

Let us practice identifying FDs from a different domain. Consider a university registration system with this naive relation:

```
ENROLLMENT(StudentID, StudentName, CourseID, CourseName, InstructorID, InstructorName, Grade)
```

Assume these business rules:

- A student has a unique ID and exactly one name.
- A course has a unique ID, exactly one name, and exactly one instructor.
- An instructor has a unique ID and exactly one name.
- A student receives exactly one grade per course.

We can now state the FDs explicitly:

- $\text{StudentID} \rightarrow \text{StudentName}$
- $\text{CourseID} \rightarrow \text{CourseName}, \text{InstructorID}$
- $\text{InstructorID} \rightarrow \text{InstructorName}$
- $\{\text{StudentID}, \text{CourseID}\} \rightarrow \text{Grade}$

Notice the last FD has a composite left-hand side. Knowing only `StudentID` does not determine `Grade` (a student takes many courses), and knowing only `CourseID` does not determine `Grade` (many students take the same course). Only the combination determines the grade. This is a **full functional dependency**—no subset of the left-hand side determines the right-hand side—and it will be central to understanding 2NF.

> **Try this yourself:** In the `ENROLLMENT` relation, what anomalies do you predict? If an instructor changes their name, how many rows must be updated? If a new course is designed but no students have enrolled yet, can we record it? If the last student drops a course, do we lose the course's information?
>
> <details>
> <summary>Reveal answer</summary>
> Instructor name changes require updating every enrollment row for that instructor's course—an update anomaly. A new course with no students cannot be inserted because `StudentID` is part of the key—an insertion anomaly. If the last student drops a course, deleting their row destroys the course's name and instructor information—a deletion anomaly. These are the same three anomaly types we saw in the employee-department example, arising from the same root cause: facts about courses and instructors are stored redundantly alongside facts about student enrollments.
> </details>

### 2.4 Keys Defined via FDs

The concept of a key is entirely definable through functional dependencies:

- A **superkey** is any set of attributes $SK \subseteq U$ such that $SK \rightarrow U$. Knowing $SK$ determines the entire tuple.
- A **candidate key** $K$ is a *minimal* superkey: no proper subset $K' \subset K$ satisfies $K' \rightarrow U$. Remove any attribute from $K$, and the determination of the whole tuple is lost.
- A **prime attribute** is any attribute that belongs to at least one candidate key. A **nonprime attribute** belongs to no candidate key.

These definitions form the lens through which every normal form is evaluated. The distinction between prime and nonprime is the fault line separating 2NF from 3NF, and 3NF from BCNF. Every normal form violation can be stated in terms of which kind of attribute depends on what.

> **Why this distinction matters:** Think of prime attributes as the "identity" attributes—they tell you *which thing* a row is about. Nonprime attributes are the "descriptive" attributes—they tell you *something about* that thing. Anomalies occur when a descriptive attribute depends on only part of an identity, or on something other than an identity altogether. Each normal form forbids a specific pattern of such misplaced dependencies.

**Worked example:** In $\text{EMP}(\text{EmpID}, \text{Name}, \text{SSN})$, suppose both `EmpID` and `SSN` uniquely identify an employee. Then:

- $\{\text{EmpID}\}$ is a candidate key (minimal—you cannot remove `EmpID` and still determine everything).
- $\{\text{SSN}\}$ is also a candidate key.
- $\{\text{EmpID}, \text{Name}\}$ is a superkey but *not* a candidate key (`Name` is redundant).
- Prime attributes: `EmpID`, `SSN`.
- Nonprime attribute: `Name`.

**Worked example for the ENROLLMENT relation:** What are the candidate keys?

We compute the closure of various attribute sets using the FDs from Section 2.3. Start with $\{\text{StudentID}, \text{CourseID}\}$:

- We know $\text{StudentID} \rightarrow \text{StudentName}$, so we add `StudentName`.
- We know $\text{CourseID} \rightarrow \text{CourseName}, \text{InstructorID}$, so we add `CourseName` and `InstructorID`.
- We know $\text{InstructorID} \rightarrow \text{InstructorName}$, so we add `InstructorName`.
- We know $\{\text{StudentID}, \text{CourseID}\} \rightarrow \text{Grade}$, so we add `Grade`.

The closure is $\{\text{StudentID}, \text{CourseID}, \text{StudentName}, \text{CourseName}, \text{InstructorID}, \text{InstructorName}, \text{Grade}\}$, which is the entire schema. So $\{\text{StudentID}, \text{CourseID}\}$ is a superkey. Is it minimal? If we remove `CourseID`, can `StudentID` alone determine everything? No—a student takes many courses, so `StudentID` does not determine `CourseID` or `Grade`. If we remove `StudentID`, can `CourseID` alone determine everything? No—many students take the same course, so `CourseID` does not determine `StudentID` or `Grade`. Therefore $\{\text{StudentID}, \text{CourseID}\}$ is the only candidate key. Prime attributes: `StudentID`, `CourseID`. Nonprime attributes: `StudentName`, `CourseName`, `InstructorID`, `InstructorName`, `Grade`.

### 2.5 Closure of FDs: The Armstrong Axioms

Given a set of FDs $F$ on a schema, other FDs are logically implied. The **closure** $F^+$ is the set of all FDs logically implied by $F$. Computing $F^+$ relies on Armstrong's axioms, which are sound and complete:

1.  **Reflex