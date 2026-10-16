# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember** – State the definitions of 1NF, 2NF, 3NF, and BCNF, including the conditions each imposes.
2.  **Understand** – Explain the redundancy anomaly each normal form addresses and articulate the trade-off between normalization and query performance using concrete examples.
3.  **Apply** – Given a relation and a set of functional dependencies, determine the highest normal form the relation satisfies by systematically testing each condition.
4.  **Analyze** – Identify the functional dependency that violates a given normal form and trace the resulting insertion, update, or deletion anomaly through a worked scenario.
5.  **Create** – Perform a lossless, dependency-preserving decomposition to bring a schema into 3NF or BCNF using standard algorithms, and verify the result.
6.  **Evaluate** – Assess when controlled denormalization is justified despite violating normal forms, weighing performance gains against anomaly risks.

---

## Opening: The Database That Corrupted Itself

In 2012, a university registration system silently corrupted thousands of student records. The cause wasn't a hardware failure or a security breach. It was a single update operation that a developer assumed would touch one row—but the schema forced the same fact to be stored in 847 different places. The developer updated 846 of them.

The database now contained an impossible state: a professor simultaneously assigned to two departments, a course listed with two different credit counts, and students enrolled in sections that didn't exist. The application logic assumed consistency. The schema guaranteed nothing.

This failure mode has a name: an **update anomaly**. And it is not a rare edge case—it is the inevitable consequence of a schema design that violates normalization principles. Every database you will ever design or inherit either respects these principles or silently accumulates corruption over time.

The question this lecture answers is not "what are the normal forms?" but rather: **"Given a real-world domain with real constraints, how do I design a schema that makes inconsistency structurally impossible?"**

By the end, you will be able to look at any table design and diagnose exactly which anomalies it permits, which functional dependency causes each one, and how to decompose the schema to eliminate them—or, in rare cases, why you might deliberately choose not to.

---

## 0. Prerequisites: The Toolbox for Normalization

We build on four concepts from earlier lectures. These are the tools for diagnosing and repairing flawed schemas.

### 0.1 Relation Schema and Instance

A **relation schema** \(R\) is a named set of attributes—the blueprint. A **relation instance** \(r\) is a set of tuples conforming to that schema—the actual data at a given moment. We denote the set of attributes of \(R\) as \(\operatorname{att}(R)\).

**Why this distinction matters:** Normalization concerns the schema, not the instance. A schema can be poorly designed even if its current data appears clean. We reason about all possible legal instances.

**Analogy — Blueprint vs. Building:** A relation schema is to a database what a building's structural plan is to the actual building. You can walk through a building and see no cracks today, but if the blueprint places a load-bearing wall on an unsupported beam, collapse is inevitable under the right conditions. Similarly, a schema that violates normalization may appear functional with current data—until an insertion, update, or deletion triggers the anomaly that was always latent in the design.

### 0.2 Superkey and Candidate Key

- A **superkey** \(SK\) of \(R\) is a set of attributes whose values uniquely identify each tuple. Formally, the functional dependency \(SK \to R\) holds, meaning \(SK \to A\) for every attribute \(A \in \operatorname{att}(R)\).
- A **candidate key** \(K\) is a *minimal* superkey: removing any attribute from \(K\) destroys the uniqueness property. That is, for every proper subset \(K' \subset K\), the FD \(K' \to R\) does *not* hold. A relation may have multiple candidate keys. We designate one as the **primary key** for implementation, but this choice has no theoretical significance.

**Example:** In \(\text{STUDENT}(\text{StudentID}, \text{Email}, \text{SSN}, \text{Name})\), both \(\{\text{StudentID}\}\) and \(\{\text{SSN}\}\) are candidate keys. \(\{\text{StudentID}, \text{Name}\}\) is a superkey but not a candidate key, because \(\text{Name}\) is unnecessary for unique identification. The set \(\{\text{Email}\}\) is also a candidate key if the university enforces unique email addresses.

> **Quick Check 0.2:** In \(\text{BOOK}(\text{ISBN}, \text{Title}, \text{Edition}, \text{PublisherID})\), assuming each ISBN uniquely identifies a book, what is a candidate key? Is \(\{\text{ISBN}, \text{Title}\}\) a candidate key?
>
> *(Answer: \(\{\text{ISBN}\}\) is a candidate key. \(\{\text{ISBN}, \text{Title}\}\) is a superkey but not a candidate key, because \(\text{Title}\) is unnecessary—removing it still yields a superkey.)*

### 0.3 Prime and Nonprime Attributes

- A **prime attribute** belongs to at least one candidate key.
- A **nonprime attribute** belongs to no candidate key.

In the \(\text{STUDENT}\) example, \(\text{StudentID}\), \(\text{Email}\), and \(\text{SSN}\) are prime (assuming \(\text{Email}\) is unique). \(\text{Name}\) is nonprime. This distinction is central to 2NF and 3NF: their conditions apply specifically to nonprime attributes.

> **Quick Check 0.3:** In \(\text{ENROLLMENT}(\text{StudentID}, \text{CourseID}, \text{Grade})\) with candidate key \(\{\text{StudentID}, \text{CourseID}\}\), which attributes are prime?
>
> *(Answer: Both \(\text{StudentID}\) and \(\text{CourseID}\) are prime because they belong to the only candidate key. \(\text{Grade}\) is nonprime.)*

### 0.4 Lossless Decomposition

A decomposition of \(R\) into \(R_1\) and \(R_2\) is **lossless** (or **non-additive**) with respect to a set of FDs \(F\) if, for every legal instance \(r\) of \(R\) that satisfies \(F\), the natural join of its projections satisfies:

\[
r = \pi_{R_1}(r) \bowtie \pi_{R_2}(r)
\]

We can split the table and reconstruct it perfectly—no spurious rows, no lost information. The term "lossless" refers to information preservation, not to tuple count: the join may produce the same number of tuples or more, but any additional tuples must have been present in the original relation.

**Sufficient Condition (The Practical Test):** Let \(R\) be decomposed into \(R_1\) and \(R_2\). The decomposition is lossless if the intersection \(R_1 \cap R_2\) is a superkey for at least one of \(R_1\) or \(R_2\). Formally, if \((R_1 \cap R_2) \to R_1\) or \((R_1 \cap R_2) \to R_2\) is in the closure \(F^+\).

The shared attributes serve as a unique identifier guaranteeing that each tuple in one relation joins with exactly one tuple in the other. Without this property, you get spurious tuples that look legitimate but represent facts that never existed.

**Analogy — Puzzle Pieces with Unique Tabs:** Imagine cutting a photograph into two puzzle pieces. If the cut follows a unique contour that matches exactly one way, reassembling the pieces reconstructs the original image perfectly—this is a lossless decomposition. But if you cut both pieces with identical straight edges, you can join either piece to either side of the other, creating four possible images where only one was real. The "unique contour" is the superkey in the intersection: it guarantees exactly one match per tuple.

**Example:** Decomposing \(\text{EMPLOYEE}(\text{EmpID}, \text{DeptID}, \text{DeptName})\) into \(R_1(\text{EmpID}, \text{DeptID})\) and \(R_2(\text{DeptID}, \text{DeptName})\) is lossless because the intersection \(\{\text{DeptID}\}\) is a superkey for \(R_2\) (assuming \(\text{DeptID} \to \text{DeptName}\) holds). Every department has exactly one name, so joining on \(\text{DeptID}\) cannot create spurious tuples.

**Common Misconception:** "Lossless" does not mean "no tuples are lost." It means "no information is lost." A lossy decomposition produces tuples that never existed in the original relation.

> **Quick Check 0.4:** Is decomposing \(\text{ENROLLMENT}(\text{StudentID}, \text{CourseID}, \text{Grade})\) into \(R_1(\text{StudentID}, \text{CourseID})\) and \(R_2(\text{CourseID}, \text{Grade})\) lossless?
>
> *(Answer: Only if \(\{\text{CourseID}\}\) is a superkey for \(R_2\), meaning \(\text{CourseID} \to \text{Grade}\) holds. In a typical enrollment scenario, \(\text{CourseID}\) alone does not determine \(\text{Grade}\)—different students earn different grades in the same course. Therefore the decomposition would be lossy. The join would incorrectly pair every grade for a course with every student in that course.)*

### 0.5 Dependency Preservation

A decomposition of \(R\) into \(\{R_1, R_2, \ldots, R_n\}\) is **dependency-preserving** with respect to a set of FDs \(F\) if the union of the projections of \(F\) onto each \(R_i\) logically implies all FDs in \(F\). Formally, let \(F_i = \{X \to Y \in F^+ \mid X, Y \subseteq \operatorname{att}(R_i)\}\). The decomposition is dependency-preserving if:

\[
\left(\bigcup_{i=1}^n F_i\right)^+ = F^+
\]

Dependency preservation means we can enforce all original constraints by checking FDs locally within individual relations, without computing expensive joins. If a decomposition is not dependency-preserving, the DBMS must join tables together just to verify that certain FDs still hold globally. We always prefer dependency-preserving decompositions when they exist.

**Cross-Domain Connection — Distributed Systems and Local Validation:** Dependency preservation is the relational analog of a principle in distributed systems design: a constraint that can be validated locally (within a single node) is dramatically cheaper to enforce than one requiring coordination across nodes. When you decompose without preserving dependencies, you are effectively forcing the DBMS to perform a distributed join—even on a single machine—every time it must verify that a business rule still holds. The performance penalty is analogous to a microservice that cannot validate its own data without calling three other services.

**Example:** Consider \(R(A, B, C)\) with \(F = \{A \to B, B \to C\}\). Decompose into \(R_1(A, B)\) and \(R_2(B, C)\). The projection onto \(R_1\) gives \(\{A \to B\}\). The projection onto \(R_2\) gives \(\{B \to C\}\). The union \(\{A \to B, B \to C\}\) has closure that includes \(A \to C\) (by transitivity). This matches \(F^+\), so the decomposition is dependency-preserving.

---

## 1. The Engine of Normalization: Functional Dependencies

### 1.1 Motivation: The Hidden Cost of a Single Table

Imagine designing a university's course registration system. A colleague proposes storing everything in one table: student IDs, names, emails, course IDs, titles, instructor names, offices, and grades—all in a single relation.

Consider this instance of \(\text{UNIVERSITY}(\text{StudentID}, \text{StudentName}, \text{CourseID}, \text{CourseTitle}, \text{Instructor}, \text{Office}, \text{Grade})\):

| StudentID | StudentName | CourseID | CourseTitle | Instructor    | Office | Grade |
|-----------|-------------|----------|-------------|---------------|--------|-------|
| S1        | Alice       | C101     | Databases   | Dr. Martinez  | Rm 301 | A     |
| S1        | Alice       | C102     | Algorithms  | Dr. Chen      | Rm 402 | B     |
| S2        | Bob         | C101     | Databases   | Dr. Martinez  | Rm 301 | B     |
| S3        | Carol       | C101     | Databases   | Dr. Martinez  | Rm 301 | A     |

Now consider this scenario: Dr. Martinez changes offices from Room 301 to Room 402. How many rows must you update? Every row for every student in every course Dr. Martinez has ever taught. In this instance, three rows. In a real university database, if Dr. Martinez has taught five courses with 30 students each, that is 150 updates. Miss one row, and the database claims Dr. Martinez is in two places simultaneously.

A new professor, Dr. Chen, is hired but has not been assigned courses yet. You try to insert her office location. The database refuses—no \(\text{CourseID}\) exists, and the primary key demands one. You cannot represent a fact about an instructor independently of a fact about a course assignment. If the last student drops the last course Dr. Chen teaches, her office location vanishes from the database entirely, even though she still works at the university.

This is a structural defect. The single-table design forces the database to represent independent facts (who teaches which course, where each professor's office is) as if they were one fact. The result is **redundancy**—the same piece of information stored multiple times—which creates three categories of anomalies:

- **Insertion anomaly:** Cannot insert a fact about one entity without simultaneously inserting a fact about another entity.
- **Update anomaly:** Changing one fact requires updating multiple rows; inconsistency arises if any row is missed.
- **Deletion anomaly:** Deleting the last row that mentions a fact removes that fact entirely, even if it remains true in the real world.

Normalization is the systematic method for detecting and eliminating these defects by enforcing a principle: **each independent fact should be stored in exactly one place**. The diagnostic tool that reveals violations of this principle is the **functional dependency**.

> **Test Yourself 1.1:** In the \(\text{UNIVERSITY}\) table above, identify one insertion anomaly, one update anomaly, and one deletion anomaly. Be specific about which attributes are involved.
>
> *(Answer: Insertion anomaly—cannot insert a new instructor's office without a StudentID and CourseID. Update anomaly—changing Dr. Martinez's office requires updating multiple rows. Deletion anomaly—if S3 drops C101, we lose the fact that Dr. Martinez teaches Databases. If all students drop all of Dr. Chen's courses, we lose Dr. Chen's office entirely.)*

### 1.2 Intuition: "If I Know X, I Know Y"

A functional dependency (FD) is a deterministic function. In programming, if you write `def get_name(student_id):`, you are expressing that \(\text{student\_id} \to \text{name}\). An FD \(X \to Y\) means that \(Y\) is a function of \(X\) within the domain of discourse.

**Cross-Domain Connection — Hash Maps and Determinism:** An FD is the relational model's equivalent of a pure function in programming: given the same input (the determinant \(X\)), you always get the same output (the dependent \(Y\)). Just as a hash map guarantees that `map.get(key)` returns at most one value, an FD guarantees that for each value of \(X\), there is at most one corresponding value of \(Y\). And just as a hash map can have multiple keys mapping to the same value (collisions in the value space are fine), an FD allows many \(X\) values to map to the same \(Y\). What it forbids is one \(X\) mapping to multiple \(Y\)s—that would be a non-deterministic function, and the relational model rejects it as a structural violation.

**Key insight:** An FD is not a statistical pattern in the current data; it is a rule of the domain. Whenever two rows share the same \(X\), they must share the same \(Y\)—by constraint, not by coincidence. Schema design requires domain semantics, not data inspection.

### 1.3 Formal Definition

Let \(X\) and \(Y\) be sets of attributes in a relation schema \(R\). A **functional dependency** \(X \to Y\) holds over \(R\) if, for every possible legal instance \(r\) of \(R\), whenever two tuples \(t_1, t_2 \in r\) satisfy \(t_1[X] = t_2[X]\), they also satisfy \(t_1[Y] = t_2[Y]\).

An FD is **trivial** if \(Y \subseteq X\). Trivial FDs always hold (by reflexivity) and provide no constraint. We are concerned only with non-trivial FDs. An FD is **completely non-trivial** if \(X \cap Y = \emptyset\).

The notation \(F \models X \to Y\) means that \(X \to Y\) is logically implied by the set of FDs \(F\). The **closure** of \(F\), denoted \(F^+\), is the set of all FDs logically implied by \(F\).

### 1.4 Worked Example: Spotting FDs from Domain Rules

Consider the \(\text{ENROLLMENT}\) instance:

| StudentID | CourseID | Grade | StudentEmail   |
|-----------|----------|-------|----------------|
| S1        | C101     | A     | s1@univ.edu    |
| S1        | C102     | B     | s1@univ.edu    |
| S2        | C101     | A     | s2@univ.edu    |

We evaluate candidate FDs based on domain rules, not just the data we see.

- **FD1:** \(\{\text{StudentID}\} \to \{\text{StudentEmail}\}\) holds. The domain rule: each student has exactly one university email.
- **FD2:** \(\{\text{StudentID}, \text{CourseID}\} \to \{\text{Grade}\}\) holds. A given student in a given course receives exactly one grade.
- **FD3:** Does \(\{\text{CourseID}\} \to \{\text{Grade}\}\) hold? In this instance, C101 maps only to A. But the domain rule is clear: different students earn different grades in the same course. This FD fails the domain test. The data was coincidental.

**Common Misconception:** "The data shows that every course has exactly one grade, so the FD holds." This is wrong. FDs are constraints on all possible instances, not observations about the current instance. Always ground FDs in domain semantics.

**Analogy — Speed Limits vs. Observed Speeds:** Inferring an FD from current data is like concluding that a road has no speed limit because you observed every car traveling at different speeds. The constraint (the FD) is a rule that holds over all possible states; the current data is merely one sample. A properly designed schema enforces FDs as constraints, just as a properly posted speed limit applies regardless of who is driving today.

> **Test Yourself 1.4:** Does \(\{\text{StudentEmail}\} \to \{\text{StudentID}\}\) hold as a domain-level FD?
>
> *(Answer: As a domain rule, it holds only if the university enforces unique emails. If it does, then \(\{\text{StudentEmail}\}\) is a candidate key and the FD holds. If not, it fails. Always clarify your domain assumptions before proceeding with normalization.)*

### 1.5 Keys Revisited Through FDs

FDs yield precise definitions:

- A **superkey** \(SK\) satisfies \(SK \to R\) (all attributes). Equivalently, \(SK^+ = \operatorname{att}(R)\).
- A **candidate key** \(K\) is a superkey such that no proper subset \(K' \subset K\) satisfies \(K' \to R\).

> **Test Yourself 1.5:** In \(\text{ENROLLMENT}\), what is a candidate key? Which attributes are prime?
>
> *(Answer: \(\{\text{StudentID}, \text{CourseID}\}\) is the only minimal superkey, assuming no other FDs hold. Both \(\text{StudentID}\)