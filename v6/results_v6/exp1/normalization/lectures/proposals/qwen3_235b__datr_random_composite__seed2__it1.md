### Prerequisites: Functional Dependencies and Keys

Before proceeding, we establish foundational definitions.

A **functional dependency (FD)** $ X \rightarrow Y $ holds in a relation if, for any two tuples that agree on all attributes in $ X $, they also agree on all attributes in $ Y $. For example, $ \text{EmployeeID} \rightarrow \text{Department} $ means no two employees with the same ID can belong to different departments.

An FD expresses a *data constraint*: whenever two rows match on $ X $, they must match on $ Y $. Violating this implies inconsistency.

A **candidate key** is a minimal set of attributes that uniquely identifies each tuple and functionally determines all other attributes in the relation. It satisfies:
- **Uniqueness**: No two distinct tuples have identical values on the key.
- **Minimality**: No proper subset of the key has the uniqueness property.

The candidate key serves as the *anchor* of truth. All other attributes depend on it—directly or indirectly. Losing this anchor results in ambiguous or redundant data.

> **Formative Check 1**: Consider a relation `Enrollment(StudentID, Course, Grade)` with FD $ \text{StudentID} \rightarrow \text{Grade} $. Is this valid?
>
> **Hint**: Can the same student receive different grades in different courses?
>
> **Answer**: No—unless a student always receives the same grade across all courses, this FD is invalid. The correct key is $ \{\text{StudentID}, \text{Course}\} $, so $ \text{Grade} $ depends on both.

We now examine the consequences of poor schema design.

---

### Motivating Example: The Paradox of the Missing Instructor

Consider a single table storing student enrollments and teaching assignments:

```
TeachRecord(Student, Course, Instructor)
```

Sample data:

| Student   | Course     | Instructor    |
|-----------|------------|---------------|
| Alice     | Math101    | Dr. Smith     |
| Bob       | CS101      | Dr. Lee       |
| Charlie   | Math101    | Dr. Smith     |
| Alice     | CS101      | Dr. Lee       |

This schema exhibits three anomalies:

- **Insertion anomaly**: Cannot record that Dr. Lee teaches CS101 unless a student is enrolled.
- **Deletion anomaly**: If all students drop CS101, the fact that Dr. Lee teaches it is lost.
- **Update anomaly**: Renaming Dr. Lee requires updating multiple rows. Missing one introduces inconsistency.

The core issue: the schema conflates *enrollment* with *teaching assignment*. The database claims to store teaching relationships, but that knowledge depends on student enrollment.

This is not a data error—it is a **design flaw**. The cost is fragility and inconsistency.

> **Try this yourself**: Suppose only two of four rows for Dr. Lee are updated after a name change. What inconsistency arises? The database would show both "Dr. Lee" and "Dr. Lopez" teaching CS101, violating the intended FD $ \text{Course} \rightarrow \text{Instructor} $.

We now introduce normalization forms to resolve such flaws.

---

### 1. First Normal Form (1NF): The Atomicity Boundary

Normalization begins with **First Normal Form (1NF)**, which defines the smallest unit of data the database can process.

#### Intuition First: Why Atomicity Matters

Suppose a cell contains `CS101, CS102` as a single string. Can we reliably query which students take CS101? No—because the database treats it as one value. Indexing, searching, and constraint enforcement fail on non-atomic data.

1NF ensures that each attribute contains atomic (indivisible) values.

#### Formal Definition

A relation is in **1NF** if and only if:
- Every attribute contains atomic values.
- There are no repeating groups (e.g., `Course1`, `Course2`, `Course3` columns).

This enables precise querying, indexing, and constraints.

#### Worked Example

Given:

```
StudentCourses(StudentID, Name, Courses)
```

With sample row:

| StudentID | Name   | Courses           |
|-----------|--------|-------------------|
| 1         | Alice  | {CS101, CS102}    |

Here, `Courses` is a set—a non-atomic value—violating 1NF.

To satisfy 1NF, decompose into flat, single-valued tuples:

```
Enrollment(StudentID, CourseID)
```

| StudentID | CourseID |
|-----------|----------|
| 1         | CS101    |
| 1         | CS102    |

Each row represents a single enrollment. All values are atomic. 1NF is satisfied.

> **Common Misconception**: “1NF requires unique rows.”
>
> **Correction**: 1NF does **not** require uniqueness. Duplicate rows are allowed. However, to avoid redundancy, a primary key is typically added later.

> **Formative Check 2**: Is the following table in 1NF?
>
> | ID | Tags        |
> |----|-------------|
> | 1  | "bug, ui"   |
>
> **Answer**: No. `Tags` is a concatenated string—not atomic. To normalize, create:
>
> ```
> IssueTags(ID, Tag)
> ```
>
> | ID | Tag  |
> |----|------|
> | 1  | bug  |
> | 1  | ui   |

Having established atomicity, we now eliminate redundancy from partial dependencies.

---

### 2. Second Normal Form (2NF): The Cost of Partial Truths

After achieving 1NF, we eliminate **partial dependencies**—when a non-prime attribute depends on a proper subset of a composite candidate key.

#### Intuition First: The Library Analogy

Suppose books are identified by $ \{\text{ShelfNumber}, \text{PositionOnShelf}\} $, and $ \text{ShelfNumber} \rightarrow \text{Genre} $. Then `Genre` is repeated for every book on the same shelf—even though it describes the shelf, not the book.

Moving a book requires updating its genre, even though genre is tied to the shelf. This redundancy stems from a **partial dependency**.

The rule: *Partial keys should not determine full truths.*

#### Prerequisite
- The relation is in **1NF**.
- Candidate keys and functional dependencies are known.

#### Formal Definition

A relation is in **Second Normal Form (2NF)** if:
- It is in 1NF, and
- Every **non-prime attribute** is **fully functionally dependent** on every candidate key.

- A **prime attribute** is part of any candidate key.
- A **partial dependency** occurs when a non-prime attribute depends on a proper subset of a candidate key.

#### Worked Example

Consider:

```
OrderDetails(OrderID, ProductID, ProductName, Quantity)
```

Assume:
- FD: $ \text{ProductID} \rightarrow \text{ProductName} $
- Candidate key: $ \{\text{OrderID}, \text{ProductID}\} $

Now examine `ProductName`. It depends only on `ProductID`—a subset of the key. Since `ProductName` is non-prime and partially dependent, the schema violates 2NF.

**Step-by-step fix**:
1. Identify the partial dependency: $ \text{ProductID} \rightarrow \text{ProductName} $.
2. Extract into a new table:
   - `Products(ProductID, ProductName)` — key: $ \{\text{ProductID}\} $
3. Retain:
   - `OrderItems(OrderID, ProductID, Quantity)` — key: $ \{\text{OrderID}, \text{ProductID}\} $

Now:
- In `OrderItems`, all non-prime attributes depend on the full key.
- In `Products`, `ProductName` depends on the full key.

2NF is achieved.

> **Try this yourself**: Suppose `Enrollment(StudentID, CourseID, CourseName)` with key $ \{\text{StudentID}, \text{CourseID}\} $ and FD $ \text{CourseID} \rightarrow \text{CourseName} $.
> - Why does this violate 2NF? Because `CourseName` depends only on `CourseID`, a subset of the key.
> - How many times is `CourseName` repeated if 100 students take CS101? 100 times.
> - After decomposition into `Courses(CourseID, CourseName)` and `Enrollment(StudentID, CourseID)`, can the original data be reconstructed? Yes, via natural join.

> **Formative Check 3**: Does your decomposition preserve all FDs? Can you answer “What is the name of CS101?” without loss?
>
> **Answer**: Yes—the FD $ \text{CourseID} \rightarrow \text{CourseName} $ is preserved in `Courses`.

With partial dependencies resolved, we now address transitive dependencies.

---

### 3. Third Normal Form (3NF): Breaking the Dependency Chain

Even in 2NF, anomalies arise when non-key attributes determine other non-key attributes—**transitive dependencies**.

#### Intuition First: The Game of Telephone

Consider:
$$
\text{EmployeeID} \rightarrow \text{Department} \rightarrow \text{Manager}
$$

When Alice changes departments, her manager changes—not because she chose a new one, but because the department carries that fact.

If the manager of the Data Science department changes, every employee in that department must be updated. Missing one introduces inconsistency.

This is the *data version of telephone*: indirect propagation distorts truth.

3NF breaks the chain by ensuring only superkeys determine non-prime attributes.

#### Prerequisite
- The relation is in **2NF**.
- All FDs and candidate keys are known.

#### Formal Definition

A relation is in **Third Normal Form (3NF)** if:
- It is in 2NF, and
- For every nontrivial FD $ X \rightarrow Y $, at least one holds:
  1. $ X $ is a **superkey**, or
  2. $ Y $ is a **prime attribute** (part of some candidate key).

This prevents non-prime attributes from being determined by non-superkeys.

#### Worked Example

```
Employee(EmployeeID, Department, Manager)
```

FDs:
- $ \text{EmployeeID} \rightarrow \text{Department} $
- $ \text{Department} \rightarrow \text{Manager} $

Candidate key: $ \{\text{EmployeeID}\} $  
Non-prime attributes: `Department`, `Manager`

Examine $ \text{Department} \rightarrow \text{Manager} $:
- $ \text{Department} $ is not a superkey.
- `Manager` is not a prime attribute.

Thus, 3NF is violated.

**Step-by-step fix**:
1. Identify the transitive dependency: $ \text{Department} \rightarrow \text{Manager} $.
2. Extract into:
   - `DeptManager(Department, Manager)` — key: $ \{\text{Department}\} $
3. Retain:
   - `EmployeeDept(EmployeeID, Department)` — key: $ \{\text{EmployeeID}\} $

Now:
- `Manager` is determined directly by `Department`—a superkey in its own table.
- Updates to management affect only one row.

> **Formative Check 4**: In the decomposed schema, can you still determine Alice’s manager?
>
> **Answer**: Yes—join `EmployeeDept` and `DeptManager` on `Department`.

> **Try this yourself**: Design a scenario where deleting the last employee in a department deletes the manager fact. What is lost? Could it have been preserved?
>
> **Answer**: Yes—the `DeptManager` table preserves the manager even if no employees remain.

We now consider the strongest normal form.

---

### 4. Boyce-Codd Normal Form (BCNF): The Gold Standard

3NF resolves most anomalies, but a rare flaw remains: a dependency where the determinant is not a superkey, even if the dependent attribute is prime.

#### Intuition First: The Passport Control Analogy

Suppose:
- $ \text{ConnectingFlight} \rightarrow \text{Gate} $
- $ \text{PassportType} \rightarrow \text{Gate} $

But neither attribute uniquely identifies a passenger. If Gate A closes, every matching row must be updated. Worse: if a passenger has both conditions, the gate is stored redundantly.

BCNF requires that only **superkeys** determine attributes—eliminating overlapping determinants.

#### Prerequisite
- The relation is in **3NF**.
- All FDs and candidate keys are known.

#### Formal Definition

A relation is in **Boyce-Codd Normal Form (BCNF)** if:
For every nontrivial FD $ X \rightarrow Y $, $ X $ is a **superkey**.

BCNF is strictly stronger than 3NF—it removes the “or $ Y $ is prime” clause.

#### Worked Example

```
CourseInstructor(Course, Instructor, Department)
```

FDs:
- $ \text{Instructor} \rightarrow \text{Department} $
- $ \text{Course} \rightarrow \text{Instructor} $

Candidate key: $ \{\text{Course}\} $ (since $ \text{Course} \rightarrow \text{Instructor} \rightarrow \text{Department} $)

Examine $ \text{Instructor} \rightarrow \text{Department} $:
- $ \text{Instructor} $ does not determine $ \text{Course} $, so it is not a superkey.
- Yet the FD holds.

Thus, **BCNF is violated**.

**Step-by-step fix**:
1. Identify the violating FD: $ \text{Instructor} \rightarrow \text{Department} $.
2. Decompose:
   - `InstructorDept(Instructor, Department)` — key: $ \{\text{Instructor}\} $
   - `CourseInstructor(Course, Instructor)` — key: $ \{\text{Course}\} $

Now:
- In `InstructorDept`, $ \text{Instructor} $ is a superkey.
- In `CourseInstructor`, $ \text{Course} $ is a superkey.
- All determinants are superkeys.

BCNF is satisfied.

> **Formative Check 5**: Why didn’t 3NF catch this?
>
> **Answer**: In this case, `Department` is not prime (not part of any candidate key), so 3NF is also violated. But BCNF would catch it even if `Department` were prime—because it requires *all* determinants to be superkeys.

> **Key Insight**: BCNF enforces *determinant authority*. It does not permit exceptions based on attribute type. It is the strongest defense against hidden redundancy.

> **Try this yourself**: Can every 3NF schema be converted to BCNF with lossless join? What about dependency preservation?
>
> **Hint**: Not always. Some BCNF decompositions sacrifice FD preservation. For example, if two FDs conflict, decomposition may lose one. This is a trade-off between consistency and completeness.

---

### Summary: The Normalization Lattice

The normalization hierarchy eliminates classes of anomalies:

| Normal Form | Requirement |
|-------------|-------------|
| **1NF** | All attributes contain atomic values; no repeating groups. |
| **2NF** | No partial dependencies: non-prime attributes must depend on the full candidate key. |
| **3NF** | No transitive dependencies: non-prime attributes must not depend on non-superkeys. |
| **BCNF** | Only superkeys may determine attributes: for every $ X \rightarrow Y $, $ X $ must be a superkey. |

Each step aligns schema structure with logical dependencies.

However, normalization is not dogma. Controlled **denormalization** may improve query performance at the cost of redundancy and potential inconsistency. The key is awareness: knowing when and why to deviate.

> **Final Challenge**: Design a schema for a hospital:
> - Each doctor has one specialty.
> - Each patient is assigned one doctor.
> - Some specialties have multiple doctors.
>
> 1. List FDs and candidate keys.
> 2. Normalize to BCNF.
> 3. Where might you denormalize in practice? Why?

Normalization is not merely a set of rules. It is *design reasoning*—a method to make dependencies visible, manageable, and truthful.