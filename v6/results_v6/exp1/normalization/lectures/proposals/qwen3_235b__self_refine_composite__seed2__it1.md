### Prerequisites: Functional Dependencies and Keys

Before proceeding, ensure familiarity with the following concepts:

- Define a functional dependency (FD) and interpret $ X \rightarrow Y $ in a relation.
- Compute the closure $ X^+ $ of an attribute set under a set of FDs.
- Identify candidate keys, superkeys, and distinguish prime from non-prime attributes.

These tools are foundational to normalization.

> **Intuition**: A functional dependency $ X \rightarrow Y $ means that if two tuples agree on $ X $, they must agree on $ Y $. This enforces consistency: for example, the same `EmployeeID` implies the same `Department`.

**Functional Dependency**  
Let $ R $ be a relation schema. A functional dependency $ X \rightarrow Y $ holds in $ R $ if for all tuples $ t_1, t_2 $ in any instance of $ R $,  
$ t_1[X] = t_2[X] \Rightarrow t_1[Y] = t_2[Y] $.

**Candidate Key**  
A *candidate key* is a minimal set of attributes $ K \subseteq R $ such that $ K^+ = R $ under the given FDs. It satisfies:
1. **Uniqueness**: No two tuples have identical values on $ K $.
2. **Minimality**: No proper subset of $ K $ determines all attributes.

A *superkey* is any superset of a candidate key. An attribute is *prime* if it belongs to at least one candidate key; otherwise, it is *non-prime*.

**Attribute Closure**  
The closure $ X^+ $ under a set of FDs $ F $ is the set of all attributes functionally determined by $ X $ via $ F $. It is computed by iteratively applying FDs in $ F $ until no new attributes can be added.

> **Worked Example**: Let $ R(A,B,C) $ with FDs $ A \rightarrow B $, $ B \rightarrow C $.  
Compute:
- $ A^+ $: Start with $ \{A\} $, apply $ A \rightarrow B $ → $ \{A,B\} $, then $ B \rightarrow C $ → $ \{A,B,C\} $. So $ A^+ = R $, and $ \{A\} $ is a candidate key.
- $ B^+ = \{B,C\} \neq R $ → not a key.

Thus, the only candidate key is $ \{A\} $. Attributes $ B $ and $ C $ are non-prime.

> **Common Misconception**: “Any unique column is a key.”  
> **Correction**: Uniqueness is necessary but not sufficient. Minimality is required. For example, $ \{\text{Email, SSN}\} $ is not a candidate key if either alone is sufficient.

> **Try This Yourself**:  
Given $ R(X,Y,Z) $ with FDs $ X \rightarrow Y $, $ Y \rightarrow Z $. Is $ \{Y\} $ a candidate key?  
Compute $ Y^+ $, then check whether it equals $ R $.  
**Answer**: $ Y^+ = \{Y,Z\} \neq R $. Only $ \{X\} $ is a candidate key.

---

### Motivating Example: The Paradox of the Missing Instructor

Consider a university tracking enrollments in a single table:

```
TeachRecord(Student, Course, Instructor)
```

| Student   | Course     | Instructor    |
|-----------|------------|---------------|
| Alice     | Math101    | Dr. Smith     |
| Bob       | CS101      | Dr. Lee       |
| Charlie   | Math101    | Dr. Smith     |
| Alice     | CS101      | Dr. Lee       |

Assume:
- $ \text{Course} \rightarrow \text{Instructor} $: Each course has one instructor.
- The key is $ \{\text{Student, Course}\} $: A student takes a course at most once.

Despite correctness, three anomalies arise:

- **Insertion anomaly**: Cannot record that Dr. Lee teaches CS101 without a student.
- **Deletion anomaly**: If all students drop CS101, we lose the instructor assignment.
- **Update anomaly**: Renaming Dr. Lee requires updating multiple rows, risking inconsistency.

> **Tension**: How can a database be logically correct—every row valid—yet fail to represent reality?  
> The schema *permits* truth, but *discourages* completeness. This is not a bug. It’s a design flaw.

> **Analogy**: Imagine a library where the only record of a book’s author is inside student checkout slips. If no one checks it out, the author vanishes.  
> The problem: embedding a fact about *courses* into a table about *enrollments*.

**Insight**: Store facts independently. Separate *who teaches what* from *who is enrolled*.

Normalization aligns schema structure with functional dependencies to eliminate such anomalies.

> **Try This Yourself**:  
Is $ \text{Course} $ a superkey in `TeachRecord`?  
Compute $ \text{Course}^+ $. Does it include `Student`?  
**Answer**: No. $ \text{Course}^+ = \{\text{Course, Instructor}\} \neq R $. It does not determine `Student`.

---

### 1. First Normal Form (1NF): The Atomicity Boundary

**Learning Objective**: Determine whether a relation is in 1NF and convert a non-1NF schema into 1NF.

> **Intuition**: 1NF draws the line between data and structure. A cell must be indivisible—not because of storage, but because meaning breaks if split.

**Definition**  
A relation is in **First Normal Form (1NF)** if:
- Every attribute contains atomic values.
- There are no repeating groups or composite fields.

Atomicity enables indexing, comparison, and constraint enforcement at the attribute level.

> **Analogy**: In chemistry, a compound can be broken down into elements. But in a relational table, each cell is an *element*—you don’t parse it further within the model. If you do, you’re smuggling a nested structure into a flat world.

> **Worked Example**:  
```
StudentCourses(StudentID, Name, Courses)
```

| StudentID | Name   | Courses           |
|-----------|--------|-------------------|
| 1         | Alice  | {CS101, CS102}    |

`Courses` is non-atomic → violates 1NF.

Normalize by creating one row per course:

```
Enrollment(StudentID, CourseID)
```

| StudentID | CourseID |
|-----------|----------|
| 1         | CS101    |
| 1         | CS102    |

Now all values are atomic.

> **Common Misconception**: “1NF forbids duplicate rows.”  
> **Correction**: 1NF does not prohibit duplicates. However, duplicates introduce redundancy. We typically eliminate them via keys, but this is independent of 1NF.

> **Try This Yourself**:  
Is this table in 1NF?  
| ID | Tags        |  
|----|-------------|  
| 1  | "bug, ui"   |  

**Answer**: No. `Tags` contains multiple values. Normalize to:  
```
IssueTags(ID, Tag)
```
with rows (1, "bug"), (1, "ui").

---

### 2. Second Normal Form (2NF): Eliminating Partial Dependencies

**Learning Objective**: Identify partial dependencies and normalize a relation to 2NF.

> **Intuition**: In 2NF, no non-prime attribute depends on only part of a composite key.

> **Analogy**: Imagine a lock with two dials: both must turn to open. If one dial alone unlocks a drawer, the second dial is redundant. In schema terms, a partial dependency means part of the key determines something it shouldn’t.

**Prerequisite**: Recall that a candidate key is a minimal superkey, and a non-prime attribute is not part of any candidate key.

**Definition**  
A relation is in **Second Normal Form (2NF)** if:
1. It is in 1NF.
2. Every non-prime attribute is fully functionally dependent on every candidate key.

A *partial dependency* occurs when a non-prime attribute depends on a proper subset of a candidate key.

> **Worked Example**:  
```
OrderDetails(OrderID, ProductID, ProductName, Quantity)
```
FDs:
- $ \text{ProductID} \rightarrow \text{ProductName} $
- Key: $ \{\text{OrderID, ProductID}\} $

Here, $ \text{ProductName} $ depends only on $ \text{ProductID} $, a subset of the key → partial dependency → violates 2NF.

Decompose:
1. `OrderItems(OrderID, ProductID, Quantity)` — key: $ \{\text{OrderID, ProductID}\} $
2. `Products(ProductID, ProductName)` — key: $ \{\text{ProductID}\} $

Now, `ProductName` depends fully on its key.

> **Why It Matters**: Without decomposition, updating a product name requires modifying multiple rows—introducing update anomalies.

> **Try This Yourself**:  
In `Enrollment(StudentID, CourseID, CourseName, Credits)` with key $ \{\text{StudentID, CourseID}\} $ and $ \text{CourseID} \rightarrow \text{CourseName, Credits} $, is the schema in 2NF?  
Compute $ \text{CourseID}^+ $. Does it include `StudentID`?  
**Answer**: No. `CourseName` and `Credits` depend only on `CourseID` → partial dependency. Normalize.

---

### 3. Third Normal Form (3NF): Eliminating Transitive Dependencies

**Learning Objective**: Detect transitive dependencies and decompose a relation into 3NF.

> **Intuition**: 3NF prevents indirect dependencies. For example, if $ \text{Employee} \rightarrow \text{Department} $ and $ \text{Department} \rightarrow \text{Manager} $, then `Manager` is transitively determined by `Employee`.

> **Analogy**: In a game of telephone, whispering through intermediaries distorts the message. In databases, transitive dependencies mean facts are relayed through unnecessary links—each a point of failure.

**Definition**  
A relation is in **Third Normal Form (3NF)** if:
1. It is in 2NF.
2. For every nontrivial FD $ X \rightarrow Y $, at least one holds:
   - $ X $ is a superkey, or
   - $ Y $ is a prime attribute.

This blocks transitive dependencies where $ A \rightarrow B $, $ B \rightarrow C $, $ B $ is not a superkey, and $ C $ is non-prime.

> **Worked Example**:  
```
Employee(EmployeeID, Department, Manager)
```
FDs:
- $ \text{EmployeeID} \rightarrow \text{Department} $
- $ \text{Department} \rightarrow \text{Manager} $

Key: $ \{\text{EmployeeID}\} $ → `Manager` is non-prime.

Check $ \text{Department} \rightarrow \text{Manager} $:
- $ \text{Department} $ is not a superkey.
- `Manager` is not prime.
→ Violates 3NF.

Decompose:
1. `EmployeeDept(EmployeeID, Department)` — key: $ \{\text{EmployeeID}\} $
2. `DeptManager(Department, Manager)` — key: $ \{\text{Department}\} $

Now, `Manager` is determined directly by a superkey.

> **Common Misconception**: “3NF eliminates all anomalies.”  
> **Correction**: 3NF eliminates anomalies from functional dependencies, but not from multivalued dependencies (addressed in 4NF).

> **Try This Yourself**:  
In `Book(ISBN, Author, Publisher)` with $ \text{ISBN} \rightarrow \text{Publisher} $, $ \text{Author} \rightarrow \text{Publisher} $, and key $ \{\text{ISBN, Author}\} $, is the schema in 3NF?  
Check $ \text{Author} \rightarrow \text{Publisher} $. Is `Author` a superkey? Is `Publisher` prime?  
**Answer**: $ \text{Author} $ is not a superkey, and `Publisher` is non-prime → violates 3NF.

---

### 4. Boyce-Codd Normal Form (BCNF): The Superkey Principle

**Learning Objective**: Distinguish BCNF from 3NF and decompose a relation into BCNF.

> **Intuition**: BCNF is stricter than 3NF. It requires that *only* superkeys can determine other attributes.

> **Analogy**: In a well-governed society, only elected officials (superkeys) can issue binding decrees (determine attributes). If a random citizen (non-superkey) can pass a law, the system is vulnerable to inconsistency.

**Definition**  
A relation is in **Boyce-Codd Normal Form (BCNF)** if for every nontrivial FD $ X \rightarrow Y $, $ X $ is a superkey.

BCNF implies 3NF, but not vice versa. Unlike 3NF, BCNF has no exception for prime attributes.

> **Worked Example**:  
```
CourseInstructor(Course, Instructor, Department)
```
FDs:
- $ \text{Course} \rightarrow \text{Instructor} $
- $ \text{Instructor} \rightarrow \text{Department} $

Find keys:
- $ \text{Course}^+ = \{\text{Course, Instructor, Department}\} $ → $ \{\text{Course}\} $ is a candidate key.
- $ \text{Instructor}^+ = \{\text{Instructor, Department}\} \neq R $ → not a key.

Now, $ \text{Instructor} \rightarrow \text{Department} $: $ \text{Instructor} $ is not a superkey → violates BCNF.

Decompose:
1. `CourseInstructor(Course, Instructor)` — key: $ \{\text{Course}\} $
2. `InstructorDept(Instructor, Department)` — key: $ \{\text{Instructor}\} $

Now all FDs have superkey determinants.

> **Why BCNF Matters**: It eliminates redundancy even in cases allowed by 3NF.

> **Try This Yourself**:  
Is every 3NF schema also in BCNF?  
Construct a counterexample: a relation in 3NF but not BCNF.  
**Answer**: Yes. A 3NF schema with a non-superkey determinant that determines a prime attribute may not be in BCNF.

---

### 5. Decomposition: Lossless Join and Dependency Preservation

**Learning Objective**: Perform lossless-join decomposition and verify dependency preservation.

> **Intuition**: When splitting a table, we must ensure:
1. The original data can be reconstructed → **lossless join**.
2. All functional dependencies are enforceable → **dependency preservation**.

> **Analogy**: Like splitting a jigsaw puzzle, decomposition must allow perfect reassembly (lossless join), and every rule about piece placement (FDs) must still be enforceable somewhere.

**Lossless-Join Decomposition**  
A decomposition of $ R $ into $ R_1 $ and $ R_2 $ is *lossless* if $ R_1 \cap R_2 \rightarrow R_1 $ or $ R_1 \cap R_2 \rightarrow R_2 $.  
That is, the intersection must be a superkey in at least one of the decomposed relations.

**Dependency Preservation**  
A decomposition *preserves* FDs if the union of FDs in the new schemas logically implies all original FDs.

> **Worked Example**:  
Decompose `Employee(EmployeeID, Department, Manager)` into:
- $ R_1 = \{\text{EmployeeID, Department}\} $
- $ R_2 = \{\text{Department, Manager}\} $

Intersection: `Department`.  
Given $ \text{Department} \rightarrow \text{Manager} $, `Department` is a superkey in $ R_2 $ → decomposition is lossless.

FDs:
- $ \text{EmployeeID} \rightarrow \text{Department} $ is in $ R_1 $
- $ \text{Department} \rightarrow \text{Manager} $ is in $ R_2 $
→ Both FDs are preserved.

> **Common Pitfall**: Some BCNF decompositions fail to preserve FDs.  
Example: $ R(A,B,C) $ with $ A \rightarrow B $, $ B \rightarrow C $.  
Decompose into $ R_1(A,B) $, $ R_2(B,C) $.  
Now $ A \rightarrow B $ is in $ R_1 $, $ B \rightarrow C $ in $ R_2 $, but $ A \rightarrow C $ is not directly enforced. Worse, if $ B \rightarrow C $ is not contained in any single relation, it cannot be enforced.

> **Try This Yourself**:  
Decompose $ R(A,B,C) $ with $ A \rightarrow B $, $ B \rightarrow C $ into $ R_1(A,B) $, $ R_2(A,C) $.  
Is it lossless?  
Compute $ R_1 \cap R_2 = \{A\} $. Is $ A $ a superkey in $ R_1 $?  
**Answer**: $ A \rightarrow B $, so $ A $ is a superkey in $ R_1 $ → yes, lossless.  
But $ B \rightarrow C $ is not in either schema → not preserved.

---

### 6. Trade-offs, Limitations, and Denormalization

**Learning Objective**: Evaluate when to normalize and when to denormalize based on application needs.

> **Intuition**: Normalization reduces redundancy but increases join complexity. Real systems balance correctness and performance.

> **Cross-Domain Insight**: In distributed systems, normalization resembles microservices—each fact owned by one service. Denormalization is like caching: faster access, but consistency requires coordination.

**Limitations of Normalization**:
- **Performance**: Joins are expensive. In analytics, denormalization improves read speed.
- **Dependency Loss**: Some BCNF decompositions cannot preserve all FDs.
- **Beyond FDs**: Normalization based on FDs does not address multivalued dependencies (4NF) or temporal data.

**When to Denormalize**: