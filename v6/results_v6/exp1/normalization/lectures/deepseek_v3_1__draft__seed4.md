# Normalization Forms and Database Schema Design (1NF–BCNF)

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Identify** functional dependencies from an application domain description and classify attributes as prime or nonprime given a set of candidate keys.
2. **Diagnose** whether a given relation schema violates 1NF, 2NF, 3NF, or BCNF by applying the formal definition of each normal form.
3. **Decompose** a relation schema that violates a normal form into a lossless-join, dependency-preserving set of normalized relations using the standard decomposition algorithms.
4. **Explain** the trade-offs between full normalization (BCNF) and 3NF in terms of redundancy elimination versus dependency preservation, and make a reasoned design choice for a given scenario.
5. **Correct** common misconceptions about normalization, including the belief that 1NF alone yields a good design, that every decomposition is beneficial, and that a higher normal form always implies a better schema.

---

## Prerequisites

Before we begin, ensure you are comfortable with:

- The relational model: relations (tables), tuples (rows), attributes (columns), and schema definitions.
- The concept of a **key**: what it means for a set of attributes to uniquely identify a tuple.
- Basic set notation and logical implication: if $X$ determines $Y$, what constraint does that place on the data?

If any of these feel shaky, take a moment to review them. We will build everything else from these foundations.

---

## 1. Functional Dependencies and Keys: The Formal Foundation

### 1.1 Intuition: What is a Functional Dependency?

Imagine you are designing the database for a national election commission. Every registered voter is assigned to exactly one polling station based on their residential address. If two officials independently look up the same voter, they must arrive at the same polling station — otherwise someone has been disenfranchised. This is not a coincidence we hope holds; it is a constraint the system must enforce. The database equivalent is a **functional dependency (FD)**:

$$\text{VoterID} \rightarrow \text{PollingStation}$$

Read this as: "VoterID functionally determines PollingStation." The left-hand side (VoterID) is the **determinant**; the right-hand side (PollingStation) is the **dependent**.

This is a statement about the **rules of the application domain**, not a deduction from a single table snapshot. Even if the current table contains only one row per voter, the FD declares that any two valid rows with the same VoterID must have the same PollingStation. Violating this would mean the same voter is registered at two places — a logical contradiction in this domain.

**Why this matters beyond correctness:** FDs are not abstract formalism. They encode the business rules that prevent your database from silently contradicting reality. A table that permits two different polling stations for one voter has allowed an anomaly that could disenfranchise a real person. Normalization is the systematic removal of structures that make such contradictions possible.

### 1.2 Formal Definition

Let $R$ be a relation schema with attribute sets $X$ and $Y$. A functional dependency $X \rightarrow Y$ holds if, for any two tuples $t_1$ and $t_2$ in any valid instance $r(R)$:

$$t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]$$

The FD is **nontrivial** if $Y \not\subseteq X$. We focus on nontrivial FDs because trivial ones (e.g., $\text{VoterID} \rightarrow \text{VoterID}$) hold automatically and convey no useful information.

**A subtlety worth pausing on:** The definition says "any valid instance," not "the current instance." An FD is a constraint on the set of all possible states the database can ever be in. You cannot prove an FD holds by inspecting today's data; you can only disprove one by finding a counterexample. This is why FDs must come from domain analysis, not from data profiling.

### 1.3 Keys, Superkeys, and Prime Attributes

An FD provides a precise way to define keys:

- **Superkey:** A set of attributes $SK$ such that $SK$ functionally determines *all* attributes of $R$. Equivalently, no two distinct tuples can agree on $SK$. Every superset of a superkey is also a superkey.
- **Candidate key:** A **minimal** superkey. Remove any attribute from a candidate key, and it ceases to be a superkey. A relation may have multiple candidate keys.
- **Primary key:** One candidate key chosen by the designer as the principal identifier. This choice is arbitrary from a normalization perspective.
- **Prime attribute:** An attribute that belongs to *at least one* candidate key. **Nonprime attribute:** An attribute that belongs to *no* candidate key.

**Worked Example:**
Consider the relation schema `ENROLLMENT(StudentID, CourseID, Semester, Grade, StudentEmail)`.

Suppose the domain rules state:
- A student has one email: $\text{StudentID} \rightarrow \text{StudentEmail}$
- A student takes a specific course in exactly one semester and receives one grade: $\{\text{StudentID}, \text{CourseID}\} \rightarrow \{\text{Semester}, \text{Grade}\}$

To find candidate keys, observe that $\{\text{StudentID}, \text{CourseID}\}$ determines all attributes: StudentID gives StudentEmail; together with CourseID they give Semester and Grade. Is it minimal? Removing CourseID leaves only StudentID, which does not determine Semester or Grade (a student takes many courses). Removing StudentID leaves only CourseID, which does not determine anything about a specific student. Therefore $\{\text{StudentID}, \text{CourseID}\}$ is the sole candidate key.

Consequently:
- Prime attributes: StudentID, CourseID
- Nonprime attributes: Semester, Grade, StudentEmail

**Test Yourself 1:**
Given a relation `CUSTOMER(CustID, Name, Address, Phone)` where CustID is the sole candidate key, and one customer can have multiple phone numbers (so Phone is not unique per customer), classify each attribute as prime or nonprime.

<details>
<summary>Answer</summary>
Candidate key: {CustID}. Prime: CustID. Nonprime: Name, Address, Phone.
</details>

---

## 2. First Normal Form (1NF)

### 2.1 Intuition: The Atomicity Requirement

The relational model is built on the idea that each attribute holds a single, indivisible value. A spreadsheet cell should contain one number, one string, or one date — not a list of values, not a nested mini-table. 1NF is the formal statement of this structural rule. It is the **baseline** assumption of the relational model; every relation we consider from now on is assumed to be in 1NF.

**Why this is not obvious:** Many real-world data formats are naturally nested. A medical record might list multiple diagnoses per patient; an invoice contains line items. The impulse to store these as lists inside a single column is intuitive — it mirrors the document structure. 1NF forces us to flatten this structure, which feels like we are "losing information" about the grouping. In fact, we are not losing information; we are converting implicit grouping (position within a list) into explicit grouping (a shared key value across multiple rows). This is a trade-off: we gain queryability with standard relational operators at the cost of more rows.

### 2.2 Definition

A relation schema is in First Normal Form (1NF) if:
1. The domain of each attribute includes only **atomic** (indivisible) values.
2. The value of each attribute in any tuple is a single value from that domain.

This prohibits:
- **Multivalued attributes:** A column that holds sets, lists, or repeating groups (e.g., a `Diagnoses` column storing `{Hypertension, Diabetes, Asthma}`).
- **Composite attributes:** Nested structures treated as a single column (e.g., an `Address` column storing `(Street, City, Zip)` as a unit when we need to query individual components).

1NF is a **structural** constraint, not a dependency-based one. It says nothing about redundancy or anomalies; it only enforces the flat-table format.

### 2.3 Worked Example: Flattening a Repeating Group

**Before (violates 1NF):**
`EMPLOYEE_PROJECTS(EmpID, Name, Projects)`

| EmpID | Name | Projects |
|-------|------|----------|
| E1 | Alice | {P1, P2, P3} |
| E2 | Bob | {P2, P4} |

The `Projects` attribute holds a set of values, which is not atomic. But notice what is really happening: the set notation `{P1, P2, P3}` is a miniature relation hiding inside a single cell. To query "which employees work on P2?" you cannot use a simple equality predicate; you need a set-membership operator, which most SQL dialects support but which breaks the uniform tuple-at-a-time model of the relational algebra.

**After (1NF):**
We flatten by creating one tuple per project assignment:
`ASSIGNMENT(EmpID, Name, Project)`

| EmpID | Name | Project |
|-------|------|---------|
| E1 | Alice | P1 |
| E1 | Alice | P2 |
| E1 | Alice | P3 |
| E2 | Bob | P2 |
| E2 | Bob | P4 |

Now every attribute value is atomic. Notice, however, that `Name` is repeated for every project of the same employee. 1NF alone does not fix this redundancy; that is the job of higher normal forms.

### 2.4 Common Misconceptions About 1NF

**Misconception 1: "1NF means my schema is well-designed."**
Reality: 1NF is the minimum structural requirement. A schema in 1NF can still be riddled with update anomalies and redundancy. It is the starting line, not the finish line. The flattened `ASSIGNMENT` table above is in 1NF, yet updating Alice's name requires changing multiple rows — a classic update anomaly.

**Misconception 2: "Always split composite attributes into atomic parts."**
Reality: Decompose a composite attribute only if the application needs to query or constrain its sub-parts independently. If a `Date` attribute is always used as a whole (for comparison or formatting), splitting it into `Year`, `Month`, `Day` introduces unnecessary complexity and join overhead without semantic benefit. The atomicity judgment depends on the application's usage patterns. A useful heuristic: an attribute is non-atomic if the application treats its internal structure as meaningful for queries or constraints.

**Try this yourself:** Consider an attribute `PhoneNumber` that stores `+1-555-123-4567`. Would you split it into `CountryCode`, `AreaCode`, `Exchange`, `LineNumber`? The answer depends entirely on whether your application ever needs to query "all customers in area code 555" or validate country-code formats. If the application treats phone numbers as opaque identifiers for dialing, keeping them atomic is correct. If it needs to filter by geographic region, the composite structure matters and should be decomposed.

---

## 3. Second Normal Form (2NF)

### 3.1 Motivation: Partial Dependencies Cause Redundancy

Having established 1NF as the baseline, we now address the first source of redundancy: partial dependencies. Consider the 1NF relation `ASSIGNMENT(EmpID, Name, Project)` from our earlier example. Its candidate key is `{EmpID, Project}` — together they uniquely identify a row. But observe the FD: `EmpID → Name`. This FD's determinant (`EmpID`) is a *proper subset* of the candidate key. This is a **partial dependency**: a nonprime attribute (`Name`) depends on part of the key, not the whole key.

**Why this is a problem:** Think of the candidate key as the "atomic unit of identification" for a fact. If `Name` depends only on `EmpID`, then the fact "Alice is the name of employee E1" is independent of which project we are talking about. Yet in our 1NF table, that fact is stored redundantly — once for every project Alice is assigned to. If Alice changes her name, we must update three rows. If we delete Alice's last project assignment, we lose her name entirely. These are **update anomalies** and **delete anomalies**, respectively.

**Analogy — The filing cabinet:** Imagine a filing cabinet where each folder is labeled by both Employee ID and Project ID. Inside each folder you record the employee's name. But the employee's name does not depend on which project folder you open; it depends only on the employee. So you are copying the same name into every project folder for that employee. When the employee changes their name, you must find and update every folder — and if you miss one, the cabinet now contains a contradiction. 2NF says: store each fact in exactly one place, determined by the minimal set of attributes it depends on.

### 3.2 Definition

A relation schema is in Second Normal Form (2NF) if:
1. It is in 1NF, and
2. **Every nonprime attribute is fully functionally dependent on every candidate key.** Equivalently: no nonprime attribute depends on a proper subset of any candidate key.

**Worked Example:**
`ASSIGNMENT(EmpID, Name, Project)` with candidate key `{EmpID, Project}` and FD `EmpID → Name`.
- `Name` is nonprime (it is not part of any candidate key).
- `EmpID` is a proper subset of the candidate key `{EmpID, Project}`.
- Therefore `Name` depends on a proper subset of the key — a partial dependency. Violation of 2NF.

**Decomposition to 2NF:**
We separate the fact about employees from the fact about assignments:
- `EMPLOYEE(EmpID, Name)` — candidate key: `{EmpID}`. Now `Name` depends on the whole key.
- `PROJECT_ASSIGNMENT(EmpID, Project)` — candidate key: `{EmpID, Project}`. No nonprime attributes at all, so 2NF is trivially satisfied.

This decomposition is **lossless**: joining these two tables on `EmpID` reconstructs the original `ASSIGNMENT` table exactly. No rows are lost, no spurious rows are created.

**Test Yourself 2:**
Consider the 1NF relation `ORDER_ITEMS(OrderID, ProductID, ProductName, Quantity, OrderDate)` with candidate key `{OrderID, ProductID}`. Suppose the FDs are: `{OrderID, ProductID} → Quantity`, `ProductID → ProductName`, and `OrderID → OrderDate`. Is this relation in 2NF? If not, identify the violating partial dependency and propose a decomposition.

<details>
<summary>Answer</summary>
Nonprime attributes: ProductName, Quantity, OrderDate.
- `ProductID → ProductName`: determinant `ProductID` is a proper subset of the candidate key. Violation.
- `OrderID → OrderDate`: determinant `OrderID` is a proper subset of the candidate key. Violation.

Decomposition:
- `PRODUCT(ProductID, ProductName)` — key: `{ProductID}`
- `ORDER(OrderID, OrderDate)` — key: `{OrderID}`
- `ORDER_ITEM(OrderID, ProductID, Quantity)` — key: `{OrderID, ProductID}`
</details>

---

## 4. Third Normal Form (3NF)

### 4.1 Motivation: Transitive Dependencies — When Nonprime Attributes Determine Other Nonprime Attributes

2NF eliminates redundancy from partial dependencies. But consider this 2NF relation:

`EMPLOYEE_DEPT(EmpID, Name, DeptID, DeptName, DeptLocation)`

With candidate key `{EmpID}` and FDs:
- `EmpID → {Name, DeptID}`
- `DeptID → {DeptName, DeptLocation}`

This relation is in 2NF: the only candidate key is `{EmpID}`, which is a single attribute, so no partial dependency can exist (a proper subset of a single-attribute key is impossible). Yet redundancy persists: `DeptName` and `DeptLocation` are repeated for every employee in the same department. If the department moves to a new location, we must update every employee row in that department.

**The structural pattern:** `EmpID → DeptID` and `DeptID → DeptName`. So `EmpID → DeptName` holds transitively through `DeptID`. A nonprime attribute (`DeptName`) depends on another nonprime attribute (`DeptID`), which in turn depends on the key. This is a **transitive dependency**: the key determines a nonprime attribute, which then determines another nonprime attribute.

**Analogy — The chain of command:** In a military unit, a soldier's squad designation determines their platoon, and the platoon determines the company headquarters location. If you store the headquarters location directly with each soldier's record, you have committed to updating every soldier's record when the headquarters moves — even though the location is a fact about the company, not about the individual soldier. The dependency chain `SoldierID → Squad → Platoon → CompanyHQ` means that `SoldierID → CompanyHQ` is transitive, not direct. 3NF says: break the chain so that each fact depends directly on the key, nothing but the key.

### 4.2 Definition

A relation schema is in Third Normal Form (3NF) if, for every nontrivial FD $X \rightarrow A$ (where $A$ is a single attribute), at least one of the following holds:
1. $X$ is a superkey of $R$, or
2. $A$ is a prime attribute.

**Equivalent formulation:** No nonprime attribute depends transitively on a candidate key via another nonprime attribute. In other words, every nonprime attribute must depend directly on a candidate key, not on some intermediate nonprime attribute.

**Why the "prime attribute" escape clause?** If $A$ is prime (part of some candidate key), then even if $X$ is not a superkey, the dependency does not create the same kind of redundancy. Prime attributes are part of the identification machinery; they are expected to appear in multiple places as part of foreign keys. The formal definition acknowledges this as an acceptable exception — this will become critical when we compare 3NF to BCNF.

### 4.3 Worked Example: Decomposing a Transitive Dependency

**Before (violates 3NF):**
`EMPLOYEE_DEPT(EmpID, Name, DeptID, DeptName, DeptLocation)`
- Candidate key: `{EmpID}`
- FDs: `EmpID → {Name, DeptID}`, `DeptID → {DeptName, DeptLocation}`
- `DeptName` and `DeptLocation` are nonprime. They depend on `DeptID`, which is nonprime. So `EmpID → DeptName` is a transitive dependency through `DeptID`. Violation.

**After (3NF decomposition):**
- `EMPLOYEE(EmpID, Name, DeptID)` — key: `{EmpID}`. `DeptID` is a foreign key referencing the department.
- `DEPARTMENT(DeptID, DeptName, DeptLocation)` — key: `{DeptID}`. Now `DeptName` and `DeptLocation` depend directly on the key of their own relation.

This decomposition is **dependency-preserving**: the FDs `EmpID → {Name, DeptID}` and `DeptID → {DeptName, DeptLocation}` are both enforced within their respective relations. No FD spans across relations in a way that requires a join to check.

**Test Yourself 3:**
Consider `STUDENT_ADVISOR(StudentID, StudentName, AdvisorID, AdvisorName, AdvisorOffice)` with candidate key `{StudentID}`. Suppose `StudentID → {StudentName, AdvisorID}` and `AdvisorID → {AdvisorName, AdvisorOffice}`. Is this in 3NF? If not, decompose it.

<details>
<summary>Answer</summary>
Nonprime attributes: StudentName, AdvisorID, AdvisorName, AdvisorOffice.
`AdvisorID → {AdvisorName, AdvisorOffice}` is a nontrivial FD where the LHS (`AdvisorID`) is not a superkey and the RHS attributes are nonprime. Violation of 3NF.

Decomposition:
- `STUDENT(StudentID, StudentName, AdvisorID)` — key: `{StudentID}`, FK: `AdvisorID`
- `ADVISOR(AdvisorID, AdvisorName, AdvisorOffice)` — key: `{