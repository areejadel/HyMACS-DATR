# Normalization Forms and Database Schema Design (1NF–BCNF)

## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Identify** functional dependencies from an application domain description and classify attributes as prime or nonprime given a set of candidate keys. (Bloom's: Apply)
2.  **Diagnose** whether a given relation schema violates 1NF, 2NF, 3NF, or BCNF by applying the formal definition of each normal form. (Bloom's: Analyze)
3.  **Decompose** a relation schema that violates a normal form into a lossless-join, dependency-preserving set of normalized relations using the standard decomposition algorithms. (Bloom's: Apply)
4.  **Evaluate** the trade-offs between full normalization (BCNF) and 3NF in terms of redundancy elimination versus dependency preservation, and make a reasoned design choice for a given scenario. (Bloom's: Evaluate)
5.  **Correct** common misconceptions about normalization, including the belief that 1NF alone yields a good design, that every decomposition is beneficial, and that a higher normal form always implies a better schema. (Bloom's: Evaluate)

---

## Opening Hook: The Database That Forgot Its Own Rules

In 2014, a European bank discovered that thousands of customer accounts had incorrect interest calculations. The cause was not a software bug, but a database schema that permitted contradictory facts to coexist. A customer's account type was stored redundantly, and when an account was upgraded, some rows were updated while others were not. The database had no mechanism to prevent this, leading to a single customer holding both a "Standard" and a "Premium" account simultaneously. The interest calculation then depended on which row the query happened to read.

**Pause and predict:** Before reading further, ask yourself—what kind of schema structure would even permit this? How could a database allow a single customer to have two contradictory account types without raising an error?

The answer: this is a **schema design error**. The bank's tables were in 1NF—every cell held a single value, with no repeating groups—yet they were catastrophically redundant. The schema lacked the structural discipline to enforce a simple business rule: one customer has exactly one account type. The redundancy meant the database could store the same fact multiple times, and nothing prevented those copies from diverging.

This pattern is not rare. In 2023, a major e-commerce platform discovered that product prices in their order history diverged from current catalog prices. The schema stored price as a non-key attribute dependent only on product ID within an order-lines table. When catalog prices updated, historical orders appeared to have always had the new price, corrupting financial audit trails. The root cause in both cases: a schema design that failed to enforce functional dependencies structurally.

Consider another example from healthcare informatics: a hospital system stored patient allergies redundantly across admission records, prescription orders, and nursing notes. When a patient's penicillin allergy was updated in one place but not others, a resident prescribed amoxicillin based on stale data, triggering a near-fatal anaphylactic event. The schema permitted the same medical fact to exist in multiple, independently mutable locations—a direct consequence of unnormalized design.

**Try this yourself:** You're designing a university registration database. A student's advisor is stored in the `ENROLLMENT` table alongside each course registration. A student switches advisors mid-semester. What could go wrong if the update is applied to only some of that student's rows? Write down one concrete scenario where this causes a real problem for the university. (We'll revisit this scenario later with formal tools to prevent it.)

Normalization is that discipline. It is a set of formal tests that expose hidden redundancy in your schema—redundancy that will, with mathematical certainty, produce anomalies when data is inserted, updated, or deleted. By the end of this lecture, you will be able to look at any table design and identify exactly which anomalies are lurking, why they occur, and how to eliminate them systematically.

---

## Prerequisites

Before we begin, ensure you are comfortable with:

- The relational model: relations (tables), tuples (rows), attributes (columns), and schema definitions.
- The concept of a **key**: what it means for a set of attributes to uniquely identify a tuple.
- Basic set notation and logical implication: if X determines Y, what constraint that places on the data.

We will build everything else from these foundations.

**Quick prerequisite check:**

Given a relation `EMPLOYEE(EmpID, Name, DeptID, Salary)`, and told that `EmpID` uniquely identifies every row, answer:

1.  Is `EmpID` a superkey? A candidate key?
2.  If `DeptID` was also unique per employee, could `{EmpID, DeptID}` be a candidate key?

<details>
<summary>Answer</summary>

1.  Yes, `EmpID` is both a superkey (it determines all attributes) and a candidate key (it is minimal—no proper subset of `{EmpID}` can be a superkey since removing `EmpID` leaves an empty set).
2.  No. `{EmpID, DeptID}` is a superkey, but not a candidate key because it is not minimal—you can remove `DeptID` and `EmpID` alone is still a superkey. A candidate key must be a minimal superkey.

</details>

---

## 1. Functional Dependencies and Keys: The Formal Foundation

### 1.1 Intuition: What is a Functional Dependency?

Consider designing a database for a national election commission. Every registered voter is assigned to exactly one polling station based on their residential address. If two officials independently look up the same voter, they must arrive at the same polling station. This is not a coincidence we hope holds; it is a constraint the system must enforce. The database equivalent is a **functional dependency (FD)**:

$$\text{VoterID} \rightarrow \text{PollingStation}$$

This reads: "VoterID functionally determines PollingStation." The left-hand side (`VoterID`) is the **determinant**; the right-hand side (`PollingStation`) is the **dependent**.

An FD is a statement about the rules of the application domain, not a deduction from a single table snapshot. Even if the current table contains only one row per voter, the FD declares that any two valid rows with the same `VoterID` must have the same `PollingStation`. Violating this would mean the same voter is registered at two places—a logical contradiction in this domain. FDs encode the business rules that prevent your database from silently contradicting reality. A table that permits two different polling stations for one voter has allowed an anomaly that could disenfranchise a real person. Normalization is the systematic removal of structures that make such contradictions possible.

**Cross-domain connection—physics analogy:** Think of an FD like a physical law, not an observation. Newton's law of gravitation, \(F = G\frac{m_1 m_2}{r^2}\), doesn't merely describe all measurements made so far; it constrains what measurements are *possible*. If you measured a gravitational force that violated the inverse-square relationship, you wouldn't say "the law changed"—you'd suspect measurement error or a new phenomenon requiring explanation. Similarly, an FD constrains what data states are *permissible*. You cannot verify an FD by inspecting current data any more than you can prove a physical law by noting that it hasn't been violated yet. Both are constraints on the space of all possible states. And just as physical laws can be refined when new evidence demands it (Newton → Einstein), FDs can be revised when domain rules change—but the revision is a deliberate act of analysis, not a passive observation of data.

**Why this precision matters—a concrete example:** Suppose you're designing a shipping database. You observe that in all current records, every `ZipCode` maps to exactly one `City`. You declare the FD `ZipCode → City`. But is this actually true? In reality, some zip codes span multiple cities. Your FD would forbid inserting a second city for an existing zip code—even though that's a legitimate real-world fact. The database would reject valid data because you confused a sample with a constraint. This is why domain analysis, not data inspection, must drive FD identification.

### 1.2 Formal Definition

Let \(R\) be a relation schema with attribute sets \(X\) and \(Y\). A functional dependency \(X \rightarrow Y\) holds if, for any two tuples \(t_1\) and \(t_2\) in any valid instance \(r(R)\):

\[t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]\]

The FD is **nontrivial** if \(Y \nsubseteq X\). We focus on nontrivial FDs because trivial ones (e.g., \(\text{VoterID} \rightarrow \text{VoterID}\)) hold automatically and convey no useful constraint.

The definition says "any valid instance," not "the current instance." An FD is a constraint on the set of all possible states the database can ever be in. You cannot prove an FD holds by inspecting today's data; you can only disprove one by finding a counterexample. Therefore, FDs must come from domain analysis—interviewing domain experts, studying business rules, and examining the real-world entities being modeled—not from data profiling.

**Common Misconception:** A common industry error is to run a query checking whether current data satisfies \(X \rightarrow Y\) and, finding no violations, declare the FD holds. This is logically invalid—absence of evidence is not evidence of absence. The FD is a constraint on the *domain*, not a property of the *data*.

**Test Yourself 1.2:**
You are given a table of current employee assignments:

| EmpID | Dept |
|-------|------|
| E1    | D1   |
| E2    | D1   |
| E3    | D2   |

A colleague says: "Look, no employee appears with two different departments. Therefore, `EmpID` \(\rightarrow\) `Dept` holds." Is your colleague's reasoning valid? Why or why not?

<details>
<summary>Answer</summary>
No, the reasoning is invalid. The FD `EmpID` \(\rightarrow\) `Dept` is a claim about *all possible* valid states of the database, not just the current one. The current data might coincidentally have no violations, but a future insertion could assign E1 to D2, creating a violation. The FD holds only if the business rule states that each employee belongs to exactly one department. You must determine FDs from domain knowledge, not data inspection.

Think of it this way: if you observed three coin flips all landing heads, would you conclude that the coin *must* always land heads? That's the logical error here—confusing a sample with a constraint.
</details>

### 1.3 Closure of a Set of Functional Dependencies

**Intuition:** Given a set \(F\) of FDs, other FDs are logically implied. For example, if \(A \rightarrow B\) and \(B \rightarrow C\) hold, then \(A \rightarrow C\) necessarily holds, even if not explicitly stated. The set of all FDs implied by \(F\) is called the **closure** of \(F\), denoted \(F^+\). Computing \(F^+\) directly is generally impractical (it can be exponentially large), but we can determine whether a specific FD \(X \rightarrow Y\) is in \(F^+\) using **Armstrong's Axioms**:

1.  **Reflexivity:** If \(Y \subseteq X\), then \(X \rightarrow Y\) (trivial FDs).
2.  **Augmentation:** If \(X \rightarrow Y\), then \(XZ \rightarrow YZ\) for any set \(Z\).
3.  **Transitivity:** If \(X \rightarrow Y\) and \(Y \rightarrow Z\), then \(X \rightarrow Z\).

These axioms are **sound** (they generate only valid FDs) and **complete** (they generate all implied FDs). A more practical tool is the **attribute closure** of \(X\) under \(F\), denoted \(X^+_F\), defined as the set of all attributes functionally determined by \(X\). The algorithm computes \(X^+_F\) iteratively:

1.  Start with \(X^+_F = X\).
2.  Repeat until no change: for each FD \(U \rightarrow V\) in \(F\), if \(U \subseteq X^+_F\), then add \(V\) to \(X^+_F\).

Then \(X \rightarrow Y\) is in \(F^+\) if and only if \(Y \subseteq X^+_F\). This is the standard method for testing whether a set of attributes is a superkey.

**Analogy—the chain reaction:** Attribute closure behaves like a chemical chain reaction. You start with a set of "activated" attributes (\(X\)). Each FD is a reaction rule: if all reactants on the left are activated, the products on the right become activated too. You keep applying rules until no new activations occur—this is the fixed point where the system reaches equilibrium. The final set of activated attributes is \(X^+_F\). If this set covers the entire relation, \(X\) is a superkey—it has enough "reactivity" to determine everything. This analogy is precise: the attribute closure algorithm is literally computing the fixed point of a monotonic set-transformer, exactly like reaching equilibrium in a reaction network.

**Cross-domain connection—graph reachability:** Attribute closure is also identical to computing reachability in a directed hypergraph. Each attribute is a node. Each FD \(U \rightarrow V\) is a hyperedge from the set of nodes \(U\) to each node in \(V\). Computing \(X^+_F\) answers: "Starting from nodes \(X\), what nodes can I reach by following hyperedges?" This connection is not merely metaphorical—several database systems implement FD reasoning using graph algorithms. If you've studied graph traversal, you already understand the computational structure of attribute closure.

**Worked Example: Computing Attribute Closure**

Let \(R(A, B, C, D, E)\) with \(F = \{A \rightarrow B, B \rightarrow C, CD \rightarrow E\}\). Compute \(\{A, D\}^+_F\).

We trace through the algorithm step by step:

- **Step 1:** Start with \(\{A, D\}\). We have our initial "activated" set.
- **Step 2:** Scan \(F\) for FDs where the left side is fully contained in our current set. We find \(A \rightarrow B\): \(A\) is in \(\{A, D\}\), so we add \(B\). Our set becomes \(\{A, D, B\}\).
- **Step 3:** Scan again. We find \(B \rightarrow C\): \(B\) is now in \(\{A, D, B\}\), so we add \(C\). Our set becomes \(\{A, D, B, C\}\).
- **Step 4:** Scan again. We find \(CD \rightarrow E\): both \(C\) and \(D\) are in \(\{A, D, B, C\}\), so we add \(E\). Our set becomes \(\{A, D, B, C, E\}\).
- **Step 5:** Scan again. No FD can add new attributes (all remaining FDs have been used, and no new attributes trigger them). Stop.

Result: \(\{A, D\}^+_F = \{A, B, C, D, E\}\), which is all attributes of \(R\). Therefore \(\{A, D\}\) is a superkey. To test whether it is a candidate key, we check minimality: \(\{A\}^+_F = \{A, B, C\}\) (not all attributes—\(D\) and \(E\) are missing), and \(\{D\}^+_F = \{D\}\) (only itself). Since neither subset is a superkey, \(\{A, D\}\) is a candidate key.

**Test Yourself 1.3:**
Given \(R(A, B, C, D, E, F)\) with \(F = \{A \rightarrow BC, B \rightarrow D, C \rightarrow E, E \rightarrow F\}\), compute \(\{A\}^+_F\). Is \(\{A\}\) a candidate key?

<details>
<summary>Answer</summary>
Let's trace through:

- Start: \(\{A\}\)
- Using \(A \rightarrow BC\): \(A\) is in the set, so add \(B\) and \(C\) → \(\{A, B, C\}\)
- Using \(B \rightarrow D\): \(B\) is now in the set, so add \(D\) → \(\{A, B, C, D\}\)
- Using \(C \rightarrow E\): \(C\) is in the set, so add \(E\) → \(\{A, B, C, D, E\}\)
- Using \(E \rightarrow F\): \(E\) is in the set, so add \(F\) → \(\{A, B, C, D, E, F\}\)

Result: \(\{A\}^+_F = \{A, B, C, D, E, F\}\), which is all attributes. \(\{A\}\) is a superkey. Since it has only one attribute, it is trivially minimal—no proper subset exists except \(\emptyset\), and \(\emptyset\) determines nothing. Therefore \(\{A\}\) is a candidate key.
</details>

### 1.4 Keys, Superkeys, and Prime Attributes

**Intuition:** An FD provides a precise way to define keys. We can now formalize the informal notion of "uniquely identifies" that we've been using:

- **Superkey:** A set of attributes \(SK\) such that \(SK\) functionally determines *all* attributes of \(R\). Equivalently, \(SK^+_F = R\). Every superset of a superkey is also a superkey.
- **Candidate key:** A **minimal** superkey. Remove any attribute from a candidate key, and it ceases to be a superkey. A relation may have multiple candidate keys.
- **Primary key:** One candidate key chosen by the designer as the principal identifier. This choice is arbitrary from a normalization perspective.
- **Prime attribute:** An attribute that belongs to *at least one* candidate key.
- **Nonprime attribute:** An attribute that belongs to *no* candidate key.

**Why this classification matters—a preview:** The distinction between prime and nonprime attributes is the fulcrum on which the higher normal forms pivot. 2NF and 3NF impose restrictions specifically on nonprime attributes' relationships to keys. BCNF goes further and restricts all attributes equally. Understanding which attributes are prime tells you exactly which normal forms will be relevant to your schema.

**Try this yourself—spot the pattern:** Before we work through the formal example below, look at the `ENROLLMENT` schema and try to predict: which attributes will be prime, and which nonprime? What's your reasoning? Then check your intuition against the worked solution.

**Worked Example: Classifying Attributes**

Consider the relation schema `ENROLLMENT(StudentID, CourseID, Semester, Grade, StudentEmail)`.

Suppose the domain rules state:
- A student has one email: \(\text{StudentID} \rightarrow \text{StudentEmail}\)
- A student takes a specific course in exactly one semester and receives one grade: \(\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Semester}, \text{Grade}\}\)

Let's find the candidate keys. We compute the closure of \(\{ \text{StudentID}, \text{CourseID} \}\):
- Start: \(\{ \text{StudentID}, \text{CourseID} \}\)
- Using \(\text{StudentID} \rightarrow \text{StudentEmail}\): add `StudentEmail` → \(\{ \text{StudentID}, \text{CourseID}, \text{StudentEmail} \}\)
- Using \(\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Semester}, \text{Grade}\}\): add `Semester`, `Grade` → \(\{ \text{StudentID}, \text{CourseID}, \text{StudentEmail}, \text{Semester}, \text{Grade} \}\)

All attributes are determined. Is it minimal? Removing `CourseID` leaves only \(\{\text{StudentID}\}\), whose closure is \(\{ \text{StudentID}, \text{StudentEmail} \}\)—not all attributes (a student takes many courses). Removing `StudentID` leaves only \(\{\text{CourseID}\}\), whose closure is \(\{ \text{CourseID} \}\)—this does not determine anything about a specific student. Therefore \(\{\text{StudentID}, \text{CourseID}\}\) is the sole candidate key.

Consequently:
- Prime attributes: `StudentID`, `CourseID`
- Nonprime attributes: `Semester`, `Grade`, `StudentEmail`

**Test Yourself 1.4a:**
Given a relation `CUSTOMER(CustID, Name, Address, Phone)` where `CustID` is the sole candidate key, and one