# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** – State the definitions of 1NF, 2NF, 3NF, and BCNF in your own words.
2. **Understand** – Explain why each normal form addresses a specific type of redundancy anomaly.
3. **Apply** – Given a relation and a set of functional dependencies, determine which normal form the relation satisfies.
4. **Analyze** – Identify the precise functional dependency that violates a normal form and trace the resulting insertion, update, or deletion anomaly.
5. **Create** – Perform a lossless decomposition to bring a schema into 3NF or BCNF using the standard algorithms.

---

## 0. Prerequisites

We build on three concepts from earlier lectures. If any feel unclear, pause and review them now.

- **Relation schema** – A named set of attributes (columns). A *relation instance* is a table of tuples conforming to that schema.
- **Superkey** – A set of attributes whose values uniquely identify each tuple. Formally, if $SK$ is a superkey of $R$, then $SK \rightarrow R$ holds.
- **Candidate key** – A minimal superkey. Removing any attribute from it destroys uniqueness.

---

## 1. The Engine of Normalization: Functional Dependencies

### 1.1 Why This Matters: The Hidden Cost of "Just One More Column"

Imagine you run a small online bookstore. Every time an order ships, you record the `OrderID`, `CustomerID`, `CustomerName`, `ShippingAddress`, and `BookTitle`. It works fine—until a loyal customer moves. Now you must hunt through every order they ever placed and update their address. Miss one row, and the next shipment goes to the wrong house. Worse, when a new customer registers but hasn't ordered yet, you have nowhere to put their name. The database refuses to store facts you know are true.

These are not bugs in your application code. They are structural defects in your table design—defects that normalization systematically erases. The tool that reveals them is the functional dependency.

### 1.2 Intuition

Consider a university database. We know that a given `StudentID` always belongs to exactly one `StudentName`. Whenever two rows share the same `StudentID`, they must share the same `StudentName`. This is not a coincidence—it is a rule enforced by the real world. We capture such rules as **functional dependencies (FDs)**.

### 1.3 Formal Definition

Let $X$ and $Y$ be sets of attributes in a relation schema $R$. A **functional dependency** $X \rightarrow Y$ holds if, for every possible instance of $R$, whenever two tuples agree on all attributes in $X$, they also agree on all attributes in $Y$.

Think of $X \rightarrow Y$ as: "Given a value for $X$, you can look up exactly one value for $Y$."

### 1.4 Worked Example: Spotting an FD

Consider this `ENROLLMENT` table:

| StudentID | CourseID | Grade | StudentEmail     |
|-----------|----------|-------|------------------|
| S1        | C101     | A     | s1@univ.edu      |
| S1        | C102     | B     | s1@univ.edu      |
| S2        | C101     | A     | s2@univ.edu      |

- **FD1:** $\{\text{StudentID}\} \rightarrow \{\text{StudentEmail}\}$ holds. Every time S1 appears, the email is identical. S2 confirms it.
- **FD2:** $\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Grade}\}$ holds. The combination determines exactly one grade.
- **Does** $\{\text{CourseID}\} \rightarrow \{\text{Grade}\}$ hold? No—C101 appears with both A and B.

**Try this yourself:** Before reading on, scan the table and ask: does $\{\text{StudentEmail}\} \rightarrow \{\text{StudentID}\}$ hold? If two rows share the same email, must they share the same StudentID? (In this tiny instance, yes—but can you imagine a realistic scenario where it fails? That's the difference between an FD that holds in this instance and one that holds by the rules of the domain.)

### 1.5 Keys Revisited Through the Lens of FDs

- A **superkey** $SK$ satisfies $SK \rightarrow R$ (all attributes).
- A **candidate key** $K$ is a superkey such that no proper subset $K' \subset K$ satisfies $K' \rightarrow R$.

**Prime attribute:** An attribute that belongs to at least one candidate key.
**Nonprime attribute:** An attribute that belongs to no candidate key.

> **Quick Check 1:** In `ENROLLMENT`, what is a candidate key? Which attributes are prime, which are nonprime?
>
> *(Answer: $\{\text{StudentID}, \text{CourseID}\}$ is the only minimal superkey. Both are prime. `Grade` and `StudentEmail` are nonprime.)*

---

## 2. First Normal Form (1NF): The Starting Line

### 2.1 Why It Matters

The relational model assumes that every cell holds exactly one atomic value—no lists, no nested tables. If a column contains a set of values, we cannot write a simple FD about it, and we cannot index it or join on it reliably. 1NF is the baseline that makes all further normalization possible.

Think of it this way: a table not in 1NF is like a book where some "words" are actually whole paragraphs stuffed into a single character slot. You can't alphabetize it, you can't search it, and you certainly can't reason about what determines what.

### 2.2 Definition

A relation schema $R$ is in **First Normal Form (1NF)** if the domain of every attribute is atomic, and each tuple contains exactly one value from that domain per attribute.

### 2.3 Worked Example: Flattening a Multivalued Attribute

**Before (not 1NF):**

| EmpID | Name  | Projects    |
|-------|-------|-------------|
| 101   | Alice | {P1, P2}   |
| 102   | Bob   | {P3}        |

`Projects` is a set—not atomic.

**After (1NF, one row per project):**

| EmpID | Name  | Project |
|-------|-------|---------|
| 101   | Alice | P1      |
| 101   | Alice | P2      |
| 102   | Bob   | P3      |

Now every cell is single-valued. We have introduced redundancy (`Name` repeats for Alice), but that is exactly what higher normal forms will eliminate.

### 2.4 Common Misconception

"1NF means no duplicate rows." That is false. 1NF concerns the atomicity of attribute values, not uniqueness of tuples. Uniqueness is guaranteed by keys, not by 1NF.

> **Quick Check 2:** Is a table with a JSON blob in a text column in 1NF?
>
> *(Answer: Technically the column holds a single string, so the relational model may consider it atomic. But the values inside are not accessible to standard relational operators without parsing—this is a design smell, not a 1NF violation per se.)*

---

## 3. Second Normal Form (2NF): Eliminating Partial Dependencies

### 3.1 The Problem 2NF Solves

Imagine a table tracking which employee works on which project, and for how many hours. The key is composite: $\{\text{EmpID}, \text{ProjectID}\}$. But suppose we also store `EmpName` and `ProjectBudget`. `EmpName` depends only on `EmpID`—a part of the key. `ProjectBudget` depends only on `ProjectID`—another part. These are **partial dependencies**.

**Consequence:** If Alice changes her name, we must update every row where she appears. If we delete the last row linking an employee to a project, we lose the employee's name entirely. These are update and deletion anomalies.

Here is the tension: the table is trying to do two jobs at once. It records both "who is this employee?" and "who works on what project?" The composite key is perfect for the second job, but the first job only needs half the key. 2NF resolves this by splitting those responsibilities into separate relations.

### 3.2 Full Functional Dependency (Prerequisite Concept)

An FD $X \rightarrow Y$ is **full** if no proper subset $X' \subset X$ satisfies $X' \rightarrow Y$. Otherwise, it is **partial**.

### 3.3 Definition of 2NF

A relation schema $R$ is in **Second Normal Form (2NF)** if:
1. It is in 1NF, and
2. Every nonprime attribute is fully functionally dependent on every candidate key.

### 3.4 Worked Example: Decomposing to 2NF

Consider `EMP_PROJ` with attributes $\{\text{EmpID}, \text{ProjectID}, \text{EmpName}, \text{ProjectBudget}, \text{HoursWorked}\}$ and candidate key $\{\text{EmpID}, \text{ProjectID}\}$.

Given FDs:
- $\{\text{EmpID}\} \rightarrow \{\text{EmpName}\}$
- $\{\text{ProjectID}\} \rightarrow \{\text{ProjectBudget}\}$
- $\{\text{EmpID}, \text{ProjectID}\} \rightarrow \{\text{HoursWorked}\}$

**Step 1: Identify violations.** `EmpName` is nonprime and depends on $\{\text{EmpID}\}$ alone—a proper subset of the key. `ProjectBudget` is nonprime and depends on $\{\text{ProjectID}\}$ alone. Both are partial dependencies.

**Step 2: Decompose.** Create a new relation for each partial dependency, plus a relation for the fully dependent remainder:

- $R_1(\text{EmpID}, \text{EmpName})$ with candidate key $\{\text{EmpID}\}$
- $R_2(\text{ProjectID}, \text{ProjectBudget})$ with candidate key $\{\text{ProjectID}\}$
- $R_3(\text{EmpID}, \text{ProjectID}, \text{HoursWorked})$ with candidate key $\{\text{EmpID}, \text{ProjectID}\}$

Now every nonprime attribute in each relation depends on the whole key. Update Alice's name once in $R_1$; all references stay consistent.

**Try this yourself:** Before moving to 3NF, ask: in $R_2$, does `ProjectBudget` depend on `ProjectID` alone? Yes—that's the key. But what if each project has a `DepartmentID`, and each department has a fixed budget allocation? Then `ProjectBudget` might depend on `ProjectID` only transitively, through `DepartmentID`. That's exactly the 3NF violation we tackle next.

### 3.5 Common Misconception

"If a table has a single-attribute primary key, it is automatically in 2NF." This is true only because a single-attribute key has no proper subsets to cause partial dependencies. But 2NF is not automatic—you must still verify that no nonprime attribute depends on a subset of a different candidate key when multiple candidate keys exist.

> **Quick Check 3:** In $R_3$ above, is `HoursWorked` fully dependent on the key?
>
> *(Answer: Yes—no FD tells us `HoursWorked` from `EmpID` alone or `ProjectID` alone. It requires the pair.)*

---

## 4. Third Normal Form (3NF): Eliminating Transitive Dependencies

### 4.1 The Problem 3NF Solves

Even after 2NF, a nonprime attribute can still hold a hidden dependency chain. Consider a table `EMPLOYEE_DEPT` with attributes $\{\text{EmpID}, \text{EmpName}, \text{DeptID}, \text{DeptName}, \text{DeptBuilding}\}$. The candidate key is $\{\text{EmpID}\}$. We have:

- $\{\text{EmpID}\} \rightarrow \{\text{EmpName}, \text{DeptID}\}$ — full on the key, so 2NF is satisfied.
- $\{\text{DeptID}\} \rightarrow \{\text{DeptName}, \text{DeptBuilding}\}$ — a dependency between nonprime attributes.

Now `DeptName` and `DeptBuilding` depend on `EmpID` only because `EmpID` determines `DeptID`, and `DeptID` determines them. This is a **transitive dependency**: the key determines a nonprime attribute which, in turn, determines another nonprime attribute.

**The anomaly:** If department CSE moves to a new building, we must update every employee row in CSE. If we delete the last employee in CSE, we lose the department's name and building entirely—facts that exist independently of any employee.

This is the central tension of 3NF: the table mixes facts about employees with facts about departments. The key $\{\text{EmpID}\}$ is the right identifier for employee facts, but department facts should be keyed by $\{\text{DeptID}\}$.

### 4.2 Definition of 3NF

A relation schema $R$ is in **Third Normal Form (3NF)** if, for every non-trivial FD $X \rightarrow A$ (where $A$ is a single nonprime attribute), either:
1. $X$ is a superkey of $R$, or
2. $A$ is part of some candidate key of $R$.

Equivalently: no nonprime attribute depends transitively on a candidate key through another nonprime attribute.

### 4.3 Worked Example: Decomposing to 3NF

Starting from `EMPLOYEE_DEPT` above:

Given FDs:
- $\{\text{EmpID}\} \rightarrow \{\text{EmpName}, \text{DeptID}\}$
- $\{\text{DeptID}\} \rightarrow \{\text{DeptName}, \text{DeptBuilding}\}$

**Step 1: Identify the transitive violation.** `DeptName` and `DeptBuilding` are nonprime. They depend on `DeptID`, which is also nonprime. And `DeptID` depends on the key `EmpID`. So `EmpID` $\rightarrow$ `DeptID` $\rightarrow$ `DeptName` forms a transitive chain.

**Step 2: Decompose.** Break the transitive chain by pulling out the FD that crosses nonprime attributes:

- $R_1(\text{EmpID}, \text{EmpName}, \text{DeptID})$ with candidate key $\{\text{EmpID}\}$ and foreign key $\{\text{DeptID}\}$ referencing $R_2$.
- $R_2(\text{DeptID}, \text{DeptName}, \text{DeptBuilding})$ with candidate key $\{\text{DeptID}\}$.

Now in $R_1$, the only nonprime attributes are `EmpName` and `DeptID` (wait—`DeptID` is nonprime in $R_1$, but it is part of no candidate key in $R_1$. Yet the FD $\{\text{DeptID}\} \rightarrow \{\text{DeptName}\}$ no longer exists in $R_1$ because we moved those attributes out. The remaining FDs in $R_1$ are $\{\text{EmpID}\} \rightarrow \{\text{EmpName}\}$ and $\{\text{EmpID}\} \rightarrow \{\text{DeptID}\}$ — both have a superkey on the left. So $R_1$ is in 3NF. In $R_2$, the only FD is $\{\text{DeptID}\} \rightarrow \{\text{DeptName}, \text{DeptBuilding}\}$ — left side is a superkey. $R_2$ is in 3NF.

### 4.4 A Subtlety: The "Prime Attribute" Escape Hatch

Notice condition (2) in the definition: if $A$ *itself* is a prime attribute, the FD $X \rightarrow A$ is allowed even if $X$ is not a superkey. This is the 3NF "escape hatch" that BCNF will later close. It means a table can be in 3NF but still harbor a certain kind of redundancy—one we'll confront head-on in Section 5.

**Try this yourself:** Can you construct a table with two candidate keys where a non-superkey determines a prime attribute, and the table is in 3NF but not BCNF? Sketch it now—we'll validate it in the next section.

> **Quick Check 4:** Is `EMPLOYEE_DEPT` in 2NF before we decompose it?
>
> *(Answer: Yes—`EmpName` and `DeptID` both depend fully on the single-attribute key `EmpID`. The problem is the transitive dependency, which 2NF does not address.)*

---

## 5. Boyce-Codd Normal Form (BCNF): When 3NF Isn't Enough

### 5.1 The Problem BCNF Solves

3NF allows an FD $X \rightarrow A$ where $X$ is not a superkey, provided $A$ is prime. But if $A$ is prime, we can still have redundancy *among key attributes*. Consider this classic example:

`ENROLLMENT_ADVISOR` with attributes $\{\text{StudentID}, \text{CourseID}, \text{AdvisorID}\}$.

Suppose the business rules are:
- A student can take many courses.
- Each student has exactly one advisor.
- An advisor can advise many students but for a given course, only one advisor handles it (unrealistic, but it creates the violation).

So we have FDs:
- $\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{AdvisorID}\}$ (the key determines everything—this is a candidate key)
- $\{\text{AdvisorID}\} \rightarrow \{\text{CourseID}\}$ (each advisor specializes in exactly one course)
- $\{\text{StudentID}\} \rightarrow \{\text{AdvisorID}\}$ (each student has one advisor)

Wait—if $\{\text{StudentID}\} \rightarrow \{\text{AdvisorID}\}$ and $\{\text{AdvisorID}\} \rightarrow \{\text{CourseID}\}$, then $\{\text{StudentID}\} \rightarrow \{\text{CourseID}\}$ by transitivity. That makes $\{\text{StudentID}\}$ a candidate key on its own. But we also have $\{\text{StudentID}, \text{CourseID}\}$ as a candidate key. So `AdvisorID` is prime (it's part of no candidate key? Actually, check: candidate keys are $\{\text{StudentID}\}$ and $\{\text{StudentID}, \text{CourseID}\}$. `AdvisorID` is nonprime. But the FD $\{\text{AdvisorID}\} \rightarrow \{\text{CourseID}\}$ has a non-superkey left side determining `CourseID`, which is also nonprime. That's a straightforward 3NF violation. Let's construct a true BCNF-only violation instead.)

### 5.2 A Cleaner BCNF-Only Example

Consider `STUDENT_ADVISOR` with attributes $\{\text{StudentID}, \text{AdvisorEmail}, \text{AdvisorName}\}$.

Business rules:
- A student has one advisor: $\{\text{StudentID}\} \rightarrow \{\text{AdvisorEmail}\}$
- An advisor email uniquely identifies the advisor: $\{\text{AdvisorEmail}\} \rightarrow \{\text{AdvisorName}\}$
- An advisor name also uniquely identifies the advisor (no two advisors share a name): $\{\text{AdvisorName}\} \rightarrow \{\text{AdvisorEmail}\}$

So candidate keys are $\{\text{StudentID}\}$ and $\{\text{AdvisorName}\}$. All attributes are prime (every attribute belongs to at least one candidate key). So 3NF is automatically satisfied—there are no nonprime attributes to transitively depend on anything.

But look at the FD $\{\text{AdvisorEmail}\} \rightarrow \{\text{AdvisorName}\}$. The left side is **not** a superkey. Yet it holds. If we have two students with the same advisor, we store `AdvisorEmail`