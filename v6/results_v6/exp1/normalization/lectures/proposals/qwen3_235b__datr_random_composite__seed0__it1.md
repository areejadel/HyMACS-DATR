By the end of this lecture, you will be able to:  
1. **Define** the conditions for First Normal Form (1NF), Second Normal Form (2NF), Third Normal Form (3NF), and Boyce-Codd Normal Form (BCNF) using precise, measurable criteria.  
2. **Explain** how functional dependencies and candidate keys determine whether a relation violates a given normal form.  
3. **Apply** decomposition techniques to convert a relation into 2NF, 3NF, and BCNF, ensuring lossless joins.  
4. **Analyze** a database schema to identify insertion, deletion, and update anomalies caused by partial and transitive dependencies.  
5. **Evaluate** trade-offs between normalization (reducing redundancy) and denormalization (improving performance) in real-world design.

---

### The Anomaly That Broke the Registrar’s Office

Imagine this: a university registrar updates the instructor of a course from “Dr. Lee” to “Dr. Patel.” Simple change, right? But in their database, that single fact is repeated across hundreds of enrollment records. They update 98 rows… and accidentally skip two. Now the system claims CS101 has *two* instructors. Students are confused. Schedules conflict. The change log shows no trace of who made the error.

This isn’t a software bug. It’s a **design flaw**—a consequence of storing logically independent facts as duplicated data. And it’s entirely preventable.

Normalization is not about rigid rules. It’s about **isolating facts** so that each piece of information has a single, unambiguous home. When you change a fact, you change it *once*, and the truth propagates everywhere.

Let’s begin.

---

### Prerequisites: Functional Dependencies and Candidate Keys

Before proceeding, we establish key concepts. Let $ R $ be a relation schema over a set of attributes. A **functional dependency (FD)** $ X \rightarrow Y $ holds on $ R $ if, for any two tuples in $ R $, equality on all attributes in $ X $ implies equality on all attributes in $ Y $. That is, the value of $ X $ uniquely determines the value of $ Y $.

Think of an FD as a **promise** the database makes: *“If you know X, you can look up Y with certainty.”*  
For example, $ \text{StudentID} \rightarrow \text{StudentName} $ means that each student ID corresponds to exactly one name—no ambiguity.

A **candidate key** is a minimal set of attributes that functionally determines all other attributes in the relation. It must satisfy two properties:
- **Uniqueness**: No two distinct tuples can have the same values on the key attributes.
- **Minimality**: No proper subset of the key functionally determines all attributes.

We use the following running example throughout:

> **Enrollments**(StudentID, StudentName, Course, Instructor, CourseLevel)  
> With functional dependencies:  
> - $ \text{StudentID} \rightarrow \text{StudentName} $  
> - $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $  
> - $ \text{StudentID}, \text{Course} \rightarrow \text{StudentName}, \text{Instructor}, \text{CourseLevel} $

This schema records student enrollments and includes derived data such as instructor and course level.

> **Common Misconception Alert**:  
> Having a primary key does not guarantee normalization beyond 1NF. Redundancy and anomalies may persist due to functional dependencies involving non-key attributes.

> **Quick Check**:  
> In the `Enrollments` relation, is `StudentID` a candidate key?  
> No. While `StudentID` determines `StudentName`, it does not determine `Course`, `Instructor`, or `CourseLevel`. Thus, it fails to determine all attributes and is not a candidate key. The only candidate key is $ \{\text{StudentID}, \text{Course}\} $, which is both unique and minimal.

---

### Step 1: First Normal Form (1NF) — Atomic Values and No Repeating Groups

**Learning Objective**: Define and achieve 1NF by ensuring atomic attribute values and eliminating repeating groups.

Normalization begins with **First Normal Form (1NF)**, which ensures that the relation adheres to the basic tabular structure of the relational model.

> A relation is in **1NF** if and only if:
> - Every attribute contains **atomic (indivisible)** values.
> - There are **no repeating groups** (e.g., multiple values in a single cell).

#### Why Atomicity Is Non-Negotiable

Consider a denormalized version of `Enrollments`:

| StudentID | StudentName | Course           | Instructor | CourseLevel |
|-----------|-------------|------------------|------------|-------------|
| S001      | Alice       | CS101, CS102     | Dr. Lee    | Intro       |

Here, `Course` contains a list. This looks convenient—until you try to answer: *“Which students are taking CS101?”*  
You can’t use equality. You must parse strings. What if one row says “CS101,CS102” and another “CS101, CS102”? Are they the same?

This is like storing a person’s phone numbers as a comma-separated string in a single field. If you ever need to validate, search, or update one number, you’re forced to manipulate the entire string—a fragile, error-prone process.

**Atomicity isn’t about neatness. It’s about computability.** Databases rely on exact matches. If a value isn’t atomic, it can’t participate reliably in joins, constraints, or queries.

#### Worked Example: Achieving 1NF

To satisfy 1NF, we decompose multivalued entries into separate rows.

**Original (violates 1NF)**:

| StudentID | StudentName | Course           | Instructor | CourseLevel |
|-----------|-------------|------------------|------------|-------------|
| S001      | Alice       | CS101, CS102     | Dr. Lee    | Intro       |

**Normalized to 1NF**:

| StudentID | StudentName | Course  | Instructor | CourseLevel |
|-----------|-------------|---------|------------|-------------|
| S001      | Alice       | CS101   | Dr. Lee    | Intro       |
| S001      | Alice       | CS102   | Dr. Lee    | Intro       |

Each cell now contains a single, atomic value. Operations such as querying, inserting, and updating individual enrollments are now well-defined.

> **Clarification**: 1NF does not formally require a candidate key. However, in practice, we define one to ensure tuple distinguishability. In this case, $ \{\text{StudentID}, \text{Course}\} $ serves as the candidate key.

> **Try This Yourself**:  
> Suppose a course can have multiple instructors, and we store them as "Dr. Lee, Dr. Smith" in the `Instructor` column. Does this violate 1NF?  
> Yes. The `Instructor` attribute would then contain a multivalued, non-atomic entry. To preserve 1NF, we must either split into separate rows or introduce a separate relation (e.g., `CourseInstructors(Course, Instructor)`).

---

### Step 2: Second Normal Form (2NF) — Eliminate Partial Dependencies

**Learning Objective**: Identify and eliminate partial dependencies to achieve 2NF.

Now that we’re in 1NF, we face a deeper issue: **redundant facts masquerading as independent data**.

> A relation is in **2NF** if and only if:
> - It is in 1NF, and  
> - Every **non-prime attribute** is **fully functionally dependent** on every candidate key.

- A **non-prime attribute** is an attribute not part of any candidate key.
- A **partial dependency** occurs when a non-prime attribute depends on a proper subset of a composite candidate key.

#### The Hidden Cost of Partial Dependencies

In the 1NF `Enrollments` table:

| StudentID | StudentName | Course  | Instructor   | CourseLevel |
|-----------|-------------|---------|--------------|-------------|
| S001      | Alice       | CS101   | Dr. Lee      | Intro       |
| S001      | Alice       | CS102   | Dr. Smith    | Advanced    |
| S002      | Bob         | CS101   | Dr. Lee      | Intro       |

Functional dependencies:
- $ \text{StudentID} \rightarrow \text{StudentName} $
- $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $
- Candidate key: $ \{\text{StudentID}, \text{Course}\} $

Here’s the problem:  
- `StudentName` depends only on `StudentID`, not the full key → partial dependency.  
- `Instructor` and `CourseLevel` depend only on `Course` → another partial dependency.

So when Bob enrolls in CS101, we record:
- That Bob’s name is Bob (already known),
- That CS101 is taught by Dr. Lee (already known),
- That CS101 is an Intro course (already known).

We’re **repeating known facts** just to record a new enrollment.

This is like mailing a full biography with every invoice—just to remind the recipient of your name.

> **Consequence**:  
> - **Update anomaly**: Change Dr. Lee to Dr. Patel? You must update every row with CS101. Miss one? Inconsistency.  
> - **Insertion anomaly**: Want to add a new course before any enrollments? Can’t—no StudentID to fill.  
> - **Deletion anomaly**: Remove the last student in CS101? You lose the course’s instructor and level.

The tension is clear: we’re storing **two kinds of facts** in one table:
1. *Who is enrolled in what?*  
2. *Who teaches which course, and at what level?*

These should be separate.

#### Worked Example: Achieving 2NF via Decomposition

To eliminate partial dependencies, decompose the relation based on the determining attributes.

**Step 1**: Identify partial dependencies:
- $ \text{StudentID} \rightarrow \text{StudentName} $
- $ \text{Course} \rightarrow \text{Instructor}, \text{CourseLevel} $

**Step 2**: Extract each dependency into a new relation.

Decompose `Enrollments` into:
1. **Students**(StudentID, StudentName)  
   Key: $ \{\text{StudentID}\} $
2. **Courses**(Course, Instructor, CourseLevel)  
   Key: $ \{\text{Course}\} $
3. **Enrollments**(StudentID, Course)  
   Key: $ \{\text{StudentID}, \text{Course}\} $

Now:
- `StudentName` depends fully on its key in `Students`.
- `Instructor` and `CourseLevel` depend fully on `Course` in `Courses`.
- `Enrollments` records only the relationship—no redundant data.

We’ve **isolated facts**: student identity, course metadata, and enrollment—all in their own homes.

> **Try This Yourself**:  
> Suppose we add `Department` to `Courses`, with $ \text{Course} \rightarrow \text{Department} $. Is `Courses` still in 2NF?  
> Yes—`Department` depends on the full key `Course`. No partial dependency.

---

### Step 3: Third Normal Form (3NF) — Eliminate Transitive Dependencies

**Learning Objective**: Identify and eliminate transitive dependencies to achieve 3NF.

We’ve removed partial dependencies. But redundancy can still hide **in chains**.

> A relation is in **3NF** if and only if:
> - It is in 2NF, and  
> - No **non-prime attribute** is transitively dependent on any candidate key.

That is, if $ K \rightarrow A $ and $ A \rightarrow B $, then $ B $ should not depend on $ K $ *through* $ A $, unless $ A $ is a superkey or $ B $ is prime.

#### The Domino Effect of Transitive Dependencies

Suppose we extend `Courses`:

> **Courses**(Course, Instructor, Office)  
> With FDs:  
> - $ \text{Course} \rightarrow \text{Instructor} $  
> - $ \text{Instructor} \rightarrow \text{Office} $

So:  
$ \text{Course} \rightarrow \text{Instructor} \rightarrow \text{Office} $  
This is a **transitive dependency**: `Office` depends on `Course` *through* `Instructor`.

Now, every time CS101 appears, we record Dr. Lee’s office. But Dr. Lee’s office hasn’t changed—it’s a fact about *Dr. Lee*, not about CS101.

If Dr. Lee moves offices, we must update every course they teach. Miss one? Inconsistency.

This is like storing a professor’s office in every syllabus. When they move, every syllabus must be revised—even if the course content hasn’t changed.

The issue? **Indirect determination**. We’re using `Course` to indirectly determine `Office`, even though `Office` is really determined by `Instructor`.

#### Worked Example: Achieving 3NF

Decompose to break the chain.

From:
- **Courses**(Course, Instructor, Office)  
  With $ \text{Course} \rightarrow \text{Instructor} $, $ \text{Instructor} \rightarrow \text{Office} $

We see:
- `Office` is transitively dependent on `Course` via `Instructor`.
- `Instructor` is not a superkey (it doesn’t determine all attributes in `Courses`).
- `Office` is non-prime.

So we decompose:
1. **Courses**(Course, Instructor)  
   Key: $ \{\text{Course}\} $
2. **Instructors**(Instructor, Office)  
   Key: $ \{\text{Instructor}\} $

Now:
- `Office` depends directly on its owner: `Instructor`.
- Changing an office requires one update—ever.

> **Analogy**:  
> Think of transitive dependencies like forwarding mail through a chain:  
> *Student → Professor → Department → Building → Room*  
> If you store the final room in the student record, updating the room means updating every student. Break the chain: store the room with the building, the department with the building, etc.

> **Try This Yourself**:  
> In `Students`(StudentID, Advisor, Dept, DeptPhone), with:  
> - $ \text{StudentID} \rightarrow \text{Advisor} $  
> - $ \text{Advisor} \rightarrow \text{Dept} $  
> - $ \text{Dept} \rightarrow \text{DeptPhone} $  
> What transitive dependencies exist? How would you decompose?

---

### Step 4: Boyce-Codd Normal Form (BCNF) — Strengthening the Key

**Learning Objective**: Apply BCNF to eliminate cases where functional dependencies violate key integrity.

We’ve removed partial and transitive dependencies. But a subtle flaw can remain—one that 3NF tolerates but BCNF forbids.

> A relation is in **BCNF** if and only if:
> For every non-trivial functional dependency $ X \rightarrow Y $, $ X $ is a **superkey**.

That is, only keys can determine other attributes—not subsets, not non-keys, not even parts of composite keys.

#### When 3NF Isn’t Enough

Consider a new schema:

> **Teaching**(Course, Instructor, Time)  
> With FDs:  
> - $ \text{Instructor}, \text{Time} \rightarrow \text{Course} $ (An instructor can only teach one course at a time)  
> - $ \text{Course} \rightarrow \text{Instructor} $ (Each course has one instructor)

Candidate keys?  
- $ \{\text{Instructor}, \text{Time}\} $ determines all attributes.  
- $ \{\text{Course}, \text{Time}\} $ also determines all (since `Course` → `Instructor`).

So two candidate keys.

Now, $ \text{Course} \rightarrow \text{Instructor} $.  
Is this OK in 3NF?  
- `Course` is a prime attribute (part of a candidate key), so yes—3NF allows this.

But is it safe?

Suppose we insert:
- (CS101, Dr. Lee, M9am)
- (CS101, Dr. Patel, T9am)

We’ve recorded CS101 with two instructors. But $ \text{Course} \rightarrow \text{Instructor} $ says it should have only one.

The problem: `Course` determines `Instructor`, but `Course` is *not* a superkey. So multiple rows with the same `Course` can exist—and they can disagree on `Instructor`.

This is a **key violation in disguise**. The FD $ \text{Course} \rightarrow \text{Instructor} $ should force `Course` to be a key, but it isn’t.

#### Worked Example: Achieving BCNF

Decompose based on the violating FD: $ \text{Course} \rightarrow \text{Instructor} $

1. **CourseInstructor**(Course, Instructor)  
   Key: $ \{\text{Course}\} $
2. **InstructorTime**(Instructor, Time)  
   Key: $ \{\text{Instructor}, \text{Time}\} $

Now:
- In `CourseInstructor`, `Course` is a superkey—so $ \text{Course} \rightarrow \text{Instructor} $ is allowed.
- In `InstructorTime`, we record when instructors teach, without duplicating course assignments.

We’ve elevated the rule: *“Course determines Instructor”* to first-class status by making `Course` a key.

> **Analogy**:  
> BCNF is like constitutional law: every functional dependency must be backed by sovereign authority (a superkey). If a non-sovereign (non-superkey) makes a decree (determines an attribute), the schema is invalid.

> **Try This Yourself**:  
> Is `Students`(StudentID, Major, Advisor) with:  
> - $ \text{StudentID} \rightarrow \text{Major} $  
> - $ \text{Major} \rightarrow \text{Advisor} $  
> in BCNF?  
> No. $ \text{Major} \rightarrow \text{Advisor} $, but `Major` is not a superkey. Decompose.

---

### Step 5: Trade-Offs — When to Normalize, When to Pause

**Learning Objective**: Evaluate when normalization helps and when it hinders.

We’ve seen how normalization prevents anomalies. But each decomposition adds **joins**.

Querying “Which students are in CS101, and who teaches it?” now requires joining `Enrollments`, `Students`, `Courses`, and `Instructors`.

In high-throughput systems—say, a live course registration portal—joins can slow responses.

This is the **normalization trade-off**:  
- **Normalized**: Safe, consistent, easy to update.  
- **Denormalized**: Fast to read, but risks inconsistency.

Real-world designs often stop at 3NF—safe from most anomalies, but not over-fragmented.

Data warehouses, however, often **denormalize intentionally** for reporting speed, using techniques like materialized views to manage consistency.

> **Rule of Thumb**:  
> Normalize by default. Denormalize only when performance is proven to be a bottleneck—and document the redundancy clearly.

> **Try This Yourself**:  
> In a read-heavy analytics database tracking course enrollments over time, would you recommend full BCNF or controlled denormalization? Why?