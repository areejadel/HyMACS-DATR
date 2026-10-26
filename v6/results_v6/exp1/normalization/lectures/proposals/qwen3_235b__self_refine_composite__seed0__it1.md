---

### Learning Objectives

By the end of this lecture, you will be able to:  
1. **Remember** the definitions of 1NF, 2NF, 3NF, and BCNF with their formal conditions.  
2. **Understand** the intuition behind each normal form by identifying redundancy and anomalies in concrete examples.  
3. **Apply** normalization steps to decompose a relation schema into higher normal forms using functional dependencies.  
4. **Analyze** a database schema to detect violations of normal forms and determine appropriate decompositions.  
5. **Evaluate** trade-offs between normalization and denormalization in real-world applications.

---

### Prerequisites: Functional Dependencies and Candidate Keys

Before proceeding, we establish foundational concepts.

A **functional dependency (FD)** $ X \rightarrow Y $ means that the value of attribute set $ X $ uniquely determines the value of attribute set $ Y $. For example, if $ \text{StudentID} \rightarrow \text{StudentName} $, then each student ID corresponds to exactly one name.

A **candidate key** is a minimal set of attributes that functionally determines all other attributes in the relation. It must satisfy two properties:  
- **Uniqueness**: No two tuples may have identical values on the key.  
- **Minimality**: No proper subset of the key is also a superkey.

To test whether a set $ K $ is a candidate key, compute its **closure** $ K^+ $—the set of all attributes logically implied by $ K $ using the given FDs and Armstrong’s axioms (reflexivity, augmentation, transitivity). If $ K^+ $ includes all attributes in the schema and no proper subset of $ K $ has this property, then $ K $ is a candidate key.

Now consider a puzzle:

> Imagine a university where every student-course pair determines a unique instructor and course level—but the same course always has the same instructor and level, and each student has only one name.  
> Can we predict *before seeing any data* that some information will repeat across rows?

Yes—and that’s the power of functional dependencies. They encode *inevitable redundancy*, not just current repetition.

Let’s make it concrete with our running example:

> **Enrollments**(StudentID, StudentName, Course, Instructor, CourseLevel)  
> Functional dependencies:  
> - $ \text{StudentID} \rightarrow \text{StudentName} $  
> - $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $  
> - $ \text{StudentID}, \text{Course} \rightarrow \text{StudentName}, \text{Instructor}, \text{CourseLevel} $

We compute $ \{\text{StudentID}, \text{Course}\}^+ $:  
- Start: $ \{\text{StudentID}, \text{Course}\} $  
- Apply $ \text{StudentID} \rightarrow \text{StudentName} $: add StudentName  
- Apply $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $: add Instructor, CourseLevel  
- Result: all attributes are determined → $ \{\text{StudentID}, \text{Course}\} $ is a superkey  

Check minimality:  
- $ \text{StudentID}^+ = \{\text{StudentID}, \text{StudentName}\} $ → does not determine Course  
- $ \text{Course}^+ = \{\text{Course}, \text{Instructor}, \text{CourseLevel}\} $ → does not determine StudentName  

Thus, $ \{\text{StudentID}, \text{Course}\} $ is minimal and the only candidate key.

> **Misconception Alert**:  
> A primary key ensures uniqueness but **does not eliminate redundancy**. Redundancy arises from functional dependencies involving non-key attributes, even in relations with well-defined keys.

> **Try This Yourself**:  
> Suppose we add Department to Enrollments, with $ \text{Course} \rightarrow \text{Department} $.  
> Compute $ \{\text{StudentID}, \text{Course}\}^+ $ again. Is the key still valid?  
> ✅ Yes—closure now includes Department via Course → still a superkey.

---

### Step 1: First Normal Form (1NF) — Atomic Values and No Repeating Groups

**Learning Objective**: Transform a relation into 1NF by ensuring atomic attribute values and eliminating repeating groups.

> A relation is in **First Normal Form (1NF)** if:  
> - All attribute values are **atomic** (indivisible).  
> - There are **no repeating groups** (e.g., lists or arrays stored within a single cell).

Atomicity is foundational to relational operations such as selection, projection, and join. Non-atomic values violate the relational model and complicate querying and updating.

#### A Real Anomaly: The Ambiguous Allergy

Consider:

| PatientID | Name   | Allergies               |
|-----------|--------|-------------------------|
| P001      | Maria  | Penicillin, Latex       |
| P002      | James  | Peanuts, Bee stings     |

Now, a nurse searches for patients allergic to "Latex".  
- Query: `SELECT * FROM Patients WHERE Allergies LIKE '%Latex%'`  
But what if one record says "latex", another "Latex (severe)", and a third "No known allergies except latex"?  
String parsing fails silently—and in healthcare, silence can be deadly.

This is not just messy data. It’s a **failure of structure**.

Think of it like a **zip code that contains both city and state**. You *could* extract the city by parsing, but you shouldn’t have to. Atomicity means each fact lives in one place, cleanly.

#### Worked Example: Achieving 1NF

Given:

| StudentID | StudentName | Course           | Instructor | CourseLevel |
|-----------|-------------|------------------|------------|-------------|
| S001      | Alice       | CS101, CS102     | Dr. Lee    | Intro       |

The Course attribute contains multiple values → violates 1NF.

We resolve this by **expanding multivalued entries into separate rows**:

| StudentID | StudentName | Course  | Instructor | CourseLevel |
|-----------|-------------|---------|------------|-------------|
| S001      | Alice       | CS101   | Dr. Lee    | Intro       |
| S001      | Alice       | CS102   | Dr. Lee    | Intro       |

All values are now atomic. The candidate key $ \{\text{StudentID}, \text{Course}\} $ ensures tuple uniqueness.

> **Clarification**: While 1NF does not formally require a candidate key, **practical implementations must define one** to prevent duplicates and support referential integrity.

> **Try This Yourself**:  
> Suppose a course can have multiple instructors, stored as “Dr. Lee, Dr. Smith” in one cell.  
> How would you fix this while preserving 1NF?  
> ✅ Create a separate relation: `CourseInstructors(Course, Instructor)`—each row atomic.

---

### Step 2: Second Normal Form (2NF) — Eliminate Partial Dependencies

**Learning Objective**: Identify and eliminate partial dependencies to achieve 2NF.

> A relation is in **Second Normal Form (2NF)** if:  
> - It is in 1NF, and  
> - Every **non-prime attribute** is **fully functionally dependent** on every candidate key.

An attribute is **prime** if it is part of any candidate key; otherwise, it is **non-prime**.  
A **partial dependency** occurs when a non-prime attribute depends on a proper subset of a composite candidate key.

#### The Inventory Paradox

> **Inventory**(StoreID, ProductID, ProductName, Price, Location)  
> Functional dependencies:  
> - $ \text{ProductID} \rightarrow \text{ProductName} $  
> - $ \text{StoreID}, \text{ProductID} \rightarrow \text{Price}, \text{Location} $

Candidate key: $ \{\text{StoreID}, \text{ProductID}\} $  
Non-prime attributes: ProductName, Price, Location  

But $ \text{ProductID} \rightarrow \text{ProductName} $: ProductName depends only on ProductID—a subset of the key → **partial dependency**

Here’s the paradox:  
ProductName repeats across stores. But if you rename a product, you must update every store’s inventory row.  
Why? Because **the product’s identity is scattered across multiple contexts**.

This is like storing a person’s birthdate in every email they’ve ever sent. The data is correct—until it isn’t.

> **Analogy**:  
> Think of a partial dependency as **storing a chapter title inside every paragraph of the chapter**.  
> The title belongs to the chapter, not the paragraph.  
> When the chapter is renamed, every paragraph must be updated.  
> That’s inefficient—and error-prone.

#### Worked Example: Achieving 2NF

Return to **Enrollments**(StudentID, StudentName, Course, Instructor, CourseLevel)  
FDs:  
- $ \text{StudentID} \rightarrow \text{StudentName} $  
- $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $  
- Key: $ \{\text{StudentID}, \text{Course}\} $

Non-prime attributes:  
- StudentName depends only on StudentID → partial dependency  
- Instructor, CourseLevel depend only on Course → partial dependency  

We decompose based on these dependencies:

1. **Students**(StudentID, StudentName)  
   Key: $ \{\text{StudentID}\} $  
2. **Courses**(Course, Instructor, CourseLevel)  
   Key: $ \{\text{Course}\} $  
3. **Enrollments**(StudentID, Course)  
   Key: $ \{\text{StudentID}, \text{Course}\} $

In each new relation, non-prime attributes depend fully on the entire key.

> **Misconception Alert**:  
> 2NF applies **only when the candidate key is composite**. If the key consists of a single attribute, partial dependencies cannot exist.

> **Try This Yourself**:  
> Suppose we add $ \text{Course} \rightarrow \text{Department} $.  
> Is Courses still in 2NF?  
> ✅ Yes—Department depends on the full key Course → no partial dependency.

---

### Step 3: Third Normal Form (3NF) — Eliminate Transitive Dependencies

**Learning Objective**: Identify and eliminate transitive dependencies to achieve 3NF.

> A relation is in **Third Normal Form (3NF)** if:  
> - It is in 2NF, and  
> - For every non-trivial FD $ X \rightarrow Y $, at least one of the following holds:  
>   - $ X $ is a superkey, or  
>   - $ Y $ is a **prime attribute** (part of some candidate key)

Equivalently: **no non-prime attribute should depend on another non-key attribute**.

This prevents **transitive dependencies**, where $ K \rightarrow X $ and $ X \rightarrow Y $ imply $ K \rightarrow Y $ through $ X $, even though $ X $ is not a key.

#### The Doctor’s Dilemma

> **Doctors**(DoctorID, Specialty, DeptHead, DeptPhone)  
> FDs:  
> - $ \text{DoctorID} \rightarrow \text{Specialty} $  
> - $ \text{Specialty} \rightarrow \text{DeptHead} $  
> - $ \text{DeptHead} \rightarrow \text{DeptPhone} $

Candidate key: $ \{\text{DoctorID}\} $  
Non-prime attributes: DeptHead, DeptPhone  

Transitive chain:  
$ \text{DoctorID} \rightarrow \text{Specialty} \rightarrow \text{DeptHead} \rightarrow \text{DeptPhone} $

Changing the department head requires updating every doctor in that specialty.  
But what if two doctors update simultaneously? Race condition. Data corruption.

> **Analogy**:  
> This is like a **chain of command in a military unit**.  
> The captain reports to the major, the major to the colonel.  
> If the colonel changes, every soldier below must update their records.  
> But what if the major doesn’t get the memo?  
> **Transitive dependencies create brittle hierarchies**.

#### Worked Example: Achieving 3NF

Consider **Courses**(Course, Instructor, Office)  
FDs:  
- $ \text{Course} \rightarrow \text{Instructor} $  
- $ \text{Instructor} \rightarrow \text{Office} $

Candidate key: $ \{\text{Course}\} $  
Non-prime attribute: Office  

Now, $ \text{Course} \rightarrow \text{Instructor} \rightarrow \text{Office} $ → transitive dependency  
Also, $ \text{Instructor} \rightarrow \text{Office} $: Instructor is not a superkey, and Office is non-prime → violates 3NF

Decompose using $ \text{Instructor} \rightarrow \text{Office} $:

1. **Courses**(Course, Instructor)  
   Key: $ \{\text{Course}\} $  
2. **Instructors**(Instructor, Office)  
   Key: $ \{\text{Instructor}\} $

Now:  
- In Courses, $ \text{Course} \rightarrow \text{Instructor} $: Course is a superkey → OK  
- In Instructors, $ \text{Instructor} \rightarrow \text{Office} $: Instructor is a superkey → OK  

Both relations satisfy 3NF.

> **Try This Yourself**:  
> In **Students**(StudentID, Advisor, Dept, DeptPhone) with:  
> - $ \text{StudentID} \rightarrow \text{Advisor} $  
> - $ \text{Advisor} \rightarrow \text{Dept} $  
> - $ \text{Dept} \rightarrow \text{DeptPhone} $  
>
> Identify the transitive dependencies.  
> How would you decompose?  
> ✅ Students(StudentID, Advisor), Advisors(Advisor, Dept), Departments(Dept, DeptPhone)

---

### Step 4: Boyce-Codd Normal Form (BCNF) — Strengthening the Key

**Learning Objective**: Apply BCNF to eliminate functional dependencies that violate key integrity.

> A relation is in **Boyce-Codd Normal Form (BCNF)** if:  
> For every non-trivial FD $ X \rightarrow Y $, $ X $ is a **superkey**.

BCNF is **stricter** than 3NF: every BCNF relation is in 3NF, but not vice versa.  
It ensures that **only superkeys determine other attributes**, preventing logically inconsistent implications.

#### The Gate Assignment Puzzle

> **Flights**(FlightNumber, Airline, Gate)  
> FDs:  
> - $ \text{FlightNumber} \rightarrow \text{Airline} $  
> - $ \text{Airline}, \text{Gate} \rightarrow \text{FlightNumber} $

Candidate keys: $ \{\text{FlightNumber}\} $, $ \{\text{Airline}, \text{Gate}\} $

Now suppose: $ \text{Gate} \rightarrow \text{Airline} $?  
Then Gate determines Airline—but Gate is not a superkey → violates BCNF.

This implies: if Gate 12 is assigned to Delta, then *any* flight at Gate 12 must be Delta.  
But what if United temporarily uses Gate 12?  
**The data model contradicts reality**.

> **Cross-Domain Insight**:  
> This is like a **type system in programming**.  
> In a statically typed language, you can’t assign a string to an integer field without conversion.  
> BCNF is the database’s type system: it prevents attributes from being “reinterpreted” via weak determinants.

#### Worked Example: Achieving BCNF

> **Teaching**(Course, Instructor, Time)  
> FDs:  
> - $ \text{Instructor}, \text{Time} \rightarrow \text{Course} $  
> - $ \text{Course} \rightarrow \text{Instructor} $

Find candidate keys:  
- $ \{\text{Instructor}, \text{Time}\} $: determines Course → all attributes → superkey  
- $ \{\text{Course}, \text{Time}\} $: from $ \text{Course} \rightarrow \text{Instructor} $, we get Instructor → all attributes → superkey  

Now check FDs:  
- $ \text{Course} \rightarrow \text{Instructor} $: Course is **not** a superkey (e.g., same course taught at different times by different instructors) → violates BCNF  

Decompose using $ \text{Course} \rightarrow \text{Instructor} $:

1. **CourseInstructor**(Course, Instructor)  
   Key: $ \{\text{Course}\} $  
2. **InstructorTime**(Instructor, Time)  
   Key: $ \{\text{Instructor}, \text{Time}\} $

In both relations, every FD has a superkey as determinant → BCNF achieved.

> **Try This Yourself**:  
> **Students**(StudentID, Major, Advisor) with:  
> - $ \text{StudentID} \rightarrow \text{Major} $  
> - $ \text{Major} \rightarrow \text{Advisor} $  
>
> Does this violate BCNF?  
> Yes—Major determines Advisor, but Major is not a superkey.  
> Decompose: Students(StudentID, Major), Majors(Major, Advisor)

---

### Step 5: Trade-Offs and Limitations — When to Normalize, When to Pause

**Learning Objective**: Evaluate practical trade-offs between normalization and performance.

Normalization reduces redundancy and update anomalies—but introduces costs.

#### The Price of Decomposition

- **Join Overhead**: Queries that previously accessed one table now require joins across multiple tables, increasing latency.  
- **Update vs. Read Frequency**:  
  - **Write-heavy systems** (e.g., banking): normalize to ensure consistency and prevent corruption.  
  - **Read-heavy systems** (e.g., analytics): denormalize for faster query execution.  
- **Complexity**: Highly normalized schemas can be difficult to understand and maintain.

#### Limitations of Normalization

1. **Lossless Join Requirement**:  
   A decomposition must be **lossless**—the natural join of the decomposed relations must reconstruct the original data without spurious tuples.  
   A sufficient condition: for decomposition into $ R_1 $ and $ R_2 $, check $ R_1 \cap R_2 \rightarrow R_1 $ or $ R_1 \cap R_2 \rightarrow R_2 $.  
   Example: Decomposing Enrollments into Students and Enrollments:  
   - $ R_1 = \text{Students}(StudentID, StudentName) $, $ R_2 = \text{Enrollments}(StudentID, Course) $  
   - $ R_1 \cap R_2 = \{StudentID\} $, and $ \text{StudentID} \rightarrow \text{StudentName} $ → lossless.

2. **Dependency Preservation**:  
   Some FDs may not be enforceable within individual decomposed relations.  
   Example: After decomposing Teaching, $ \text{Instructor}, \text{Time} \rightarrow \text{Course} $ may not be directly checkable.

3. **Higher NFs Are Not Always Necessary**:  
   BCNF eliminates more anomalies than 3NF—but may require more tables and complicate queries.  
   In practice, **3NF is often sufficient** and easier to manage.

#### Real-World Strategy: Controlled Denormalization

In **data warehousing**, denormalization is common:

> **Fact Table**:  
> | StudentName | Course | Instructor | Semester | EnrollmentCount |

This enables fast aggregation without joins—critical for reporting performance.

But if Instructor changes, historical data becomes inconsistent.

**Solution**: Use **Slowly Changing Dimensions (SCD)**—track changes over time in dimension tables.

> **Rule of Thumb**:  
> Normalize to **3NF by default**.  
> Denormalize **only when performance benchmarks justify it**, and implement consistency mechanisms (e.g., materialized views, triggers).

> **Try This Yourself**:  
> You’re designing a read-heavy analytics dashboard for course enrollments.  
> Should you use BCNF or denormalize?  
> ✅ Denormalize for speed—but use a **reporting view** built from normalized base tables to maintain consistency.  
> Hybrid approach: normalize source data, denormalize for