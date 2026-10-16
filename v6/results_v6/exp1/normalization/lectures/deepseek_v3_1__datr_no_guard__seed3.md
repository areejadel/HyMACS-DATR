# Normalization Forms and Database Schema Design (1NF–BCNF)

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** – State the definitions of 1NF, 2NF, 3NF, and BCNF, and identify the key property each form enforces.
2. **Understand** – Explain why partial dependencies, transitive dependencies, and non-superkey determinants cause update anomalies.
3. **Apply** – Given a relation schema and a set of functional dependencies, determine its normal form and decompose it to the next higher form.
4. **Analyze** – Diagnose a real-world schema for normalization violations and predict the specific anomalies that will occur.
5. **Evaluate** – Decide when to stop at 3NF versus BCNF based on dependency preservation and performance trade-offs.

---

## Prerequisites Check

We assume you can:

- Read a relation schema written as `R(attr1, attr2, ...)` with a primary key underlined.
- Write a basic SQL `SELECT` statement and recognize that a table is a set of tuples.
- Understand the idea of a constraint: a rule that limits what data is valid.

If the term "tuple" is unfamiliar: a tuple is a row in a table. We use "tuple" and "row" interchangeably.

---

## Intuition First: The Problem Normalization Solves

Here's a puzzle: you're building software for a veterinary clinic. You design a single table to store appointments. It works — until it doesn't.

| PetID | PetName | OwnerName | OwnerPhone | VetID | VetName | RoomNo |
|-------|---------|-----------|------------|-------|---------|--------|
| 201   | Max     | Sarah Lee | 555-1234   | V01   | Dr. Kim | 3      |
| 201   | Max     | Sarah Lee | 555-1234   | V02   | Dr. Rao | 7      |
| 202   | Luna    | Sarah Lee | 555-1234   | V01   | Dr. Kim | 3      |
| 203   | Oliver  | Tom Chen  | 555-5678   | V03   | Dr. Kim | 2      |

Now ask yourself: what happens when Sarah Lee changes her phone number? You must find and update three rows. Miss one, and your database now claims Sarah has two different phone numbers — a contradiction your application has no way to resolve. What happens when Dr. Kim moves to Room 5? Same problem, different column. What if Dr. Patel joins the clinic but hasn't seen any patients yet? You literally cannot record her existence without inventing a fake appointment. And if Oliver's appointment is cancelled and you delete his row, Tom Chen's phone number vanishes from the database entirely — not because Tom left, but because his only appearance was tied to an appointment that no longer exists.

These aren't bugs in your queries. They're flaws in the *structure* of the table itself. The table stores multiple independent facts — who owns which pet, which vet works in which room, who has which phone number — and tangles them together so that changing one fact forces you to touch many rows, or blocks you from recording a fact at all.

**Try this yourself:** Before reading further, look at that table and try to split it into smaller tables by hand. What groupings feel natural? Where do you get stuck? Keep your answer — by the end of this lecture, you'll have a mechanical procedure that either confirms your intuition or shows you what you missed.

Normalization is the systematic process of untangling these facts. It gives you a mechanical procedure: inspect the business rules (called *functional dependencies*), detect structural flaws, and decompose the table into smaller tables where each fact lives in exactly one place. By the end of this lecture, you'll be able to look at that veterinary table and know — without guessing — exactly how to split it apart so that every update, insertion, and deletion works correctly.

---

## 1. Foundational Concepts: Keys and Functional Dependencies

### 1.1 Learning Objective for This Section

Given a relation schema and a set of business rules, you will identify candidate keys, classify attributes as prime or nonprime, and express the rules as functional dependencies.

---

### 1.2 Functional Dependencies: The Detective's Tool

**Intuition.** A functional dependency (FD) captures a statement of the form: "If I know X, then I know exactly one Y." It is a business rule, not a property of the current data.

Think of it like a deterministic lookup table that the universe enforces. If I tell you a student's ID number, you can tell me their name — not because you've memorized the current roster, but because the university's rule is that each ID belongs to exactly one person. If two rows somehow showed different names for the same ID, the rule itself would be violated, regardless of what the data happens to contain today.

Here's a tighter analogy: an FD is like a mathematical function. When you write $f(x) = x^2$, you're asserting that each input $x$ produces exactly one output. An FD $\text{Instructor} \rightarrow \text{Department}$ makes the same claim: each instructor value maps to exactly one department value. Just as you can't have $f(3) = 9$ and $f(3) = 10$ simultaneously, you can't have Dr. Chen in both the Physics and Chemistry departments. The function is deterministic by definition.

**A Cross-Domain Connection: FDs as Type Signatures in Programming Languages.** If you've worked with statically typed functional languages like Haskell or ML, you've seen type signatures like `lookupInstructor :: Instructor -> Department`. This signature declares that `lookupInstructor` is a function — given an `Instructor`, it returns exactly one `Department`. An FD `Instructor → Department` makes precisely the same claim about your data: the `Instructor` value *determines* the `Department` value, just as a function's input determines its output. This isn't merely an analogy — Codd's original formulation of the relational model explicitly drew on mathematical function theory. When we later decompose tables to satisfy normal forms, we are effectively refactoring a schema so that every stored fact behaves like a pure function from key to non-key attributes, eliminating the "side effects" (update anomalies) that arise when one stored value implicitly determines another without an explicit key constraint.

**Formal Definition.** Given a relation schema $R$, an FD $X \rightarrow Y$ holds if, for every allowable instance $r(R)$, whenever two tuples agree on all attributes in $X$, they must also agree on all attributes in $Y$. $X$ and $Y$ are sets of attributes from $R$.

We write $X \rightarrow Y$ and read it as "$X$ functionally determines $Y$."

**Example.** In a university database, the rule "each instructor belongs to exactly one department" becomes:

$$\text{Instructor} \rightarrow \text{Department}$$

If two rows show `Instructor = 'Dr. Chen'`, they must both show the same `Department` value. If they do not, the business rule is violated.

**Important:** An FD is a constraint on *all possible future states* of the database, not just the current snapshot. You cannot verify an FD by looking at today's data alone; you must know the business rule. This is the same distinction as checking whether "every employee has a unique ID" is a policy versus observing that no duplicates happen to exist in today's spreadsheet.

---

### 1.3 Superkeys and Candidate Keys

**Superkey (Intuition).** A set of attributes that, taken together, uniquely identifies every row. No two rows can have the same combination of values for a superkey.

**Formal Definition.** A set of attributes $SK \subseteq R$ is a superkey of relation schema $R$ if, for any two tuples $t_1, t_2$ in any valid instance $r(R)$, whenever $t_1[SK] = t_2[SK]$, then $t_1 = t_2$.

**Worked Example.** In a table `Employee(EmpID, SSN, Name, Dept)`:

- $\{\text{EmpID}\}$ is a superkey: no two employees share the same EmpID.
- $\{\text{SSN}\}$ is a superkey: SSN is unique per person.
- $\{\text{EmpID}, \text{Name}\}$ is a superkey, but it is *redundant*—we do not need `Name` to guarantee uniqueness.

**Candidate Key.** A candidate key is a *minimal* superkey. Remove any attribute from it, and it stops being a superkey.

In the example above:

- $\{\text{EmpID}\}$ is a candidate key (minimal).
- $\{\text{SSN}\}$ is a candidate key (minimal).
- $\{\text{EmpID}, \text{Name}\}$ is *not* a candidate key because we can drop `Name` and still have a superkey.

A schema may have multiple candidate keys. We designate one as the *primary key* for physical implementation; the others are *alternate keys*.

---

### 1.4 Prime vs. Nonprime Attributes

**Definition.** An attribute is **prime** if it belongs to at least one candidate key. Otherwise it is **nonprime**.

This distinction is where a surprising amount of normalization theory pivots. An attribute being prime is like having diplomatic immunity — certain FD violations that would be fatal for a nonprime attribute are tolerated when the attribute sits inside a key.

**Worked Example.** Consider `Enrollment(StudentID, CourseID, Grade)`. Candidate key: $\{\text{StudentID}, \text{CourseID}\}$.

- `StudentID` is prime (it is in the key).
- `CourseID` is prime (it is in the key).
- `Grade` is nonprime (it is not in any candidate key).

---

### 1.5 Full vs. Partial Functional Dependencies

**Intuition.** A full dependency means the entire left-hand side is needed to determine the right-hand side. A partial dependency means a piece of the left-hand side already does the job.

**Formal Definition.** An FD $X \rightarrow Y$ is **full** if removing any attribute $A$ from $X$ causes the dependency to fail. That is, there is no proper subset $X' \subset X$ such that $X' \rightarrow Y$ holds.

If such an $X'$ does exist, the dependency is **partial**.

**Worked Example.** In `EMP_PROJ(EmpID, ProjID, Hours, EmpName)` with candidate key $\{\text{EmpID}, \text{ProjID}\}$:

- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{Hours}$ is full: you need both the employee and the project to know the hours worked.
- $\{\text{EmpID}, \text{ProjID}\} \rightarrow \text{EmpName}$ is partial: $\text{EmpID} \rightarrow \text{EmpName}$ already holds. `EmpName` depends on only part of the key.

Partial dependencies are the defect that 2NF eliminates. Notice the pattern: a nonprime attribute depending on a proper subset of a candidate key.

**A Cross-Domain Connection: Partial Dependencies as Feature Redundancy in Machine Learning.** In data science, when you perform feature selection for a predictive model, you check for *multicollinearity* — predictors that are strongly correlated with each other rather than independently contributing to the target. A partial dependency is the relational equivalent: `EmpName` is "multicollinear" with `EmpID` alone, making the full key `{EmpID, ProjID}` redundant for predicting `EmpName`. Just as a data scientist drops redundant features to avoid inflating variance and wasting computation, 2NF decomposition drops the redundant part of the key, storing the `EmpID → EmpName` mapping exactly once. The same mathematical instinct — identify what a value *actually* depends on and eliminate redundant predictors — drives both practices.

---

### Quick Check 1

Given `Order(OrderID, ProductID, CustomerID, CustomerName)` with candidate key $\{\text{OrderID}, \text{ProductID}\}$ and the FD $\text{CustomerID} \rightarrow \text{CustomerName}$:

1. Is `CustomerName` prime or nonprime?
2. Is $\{\text{OrderID}, \text{ProductID}\} \rightarrow \text{CustomerName}$ full or partial?

*(Answers: `CustomerName` is nonprime—it is not in the key. The FD is partial because `CustomerName` depends on `CustomerID` alone, which is a proper subset of the key.)*

**Try this yourself:** Before moving on, take the veterinary clinic table from the introduction. Write down every FD you can infer from the business rules. Which attributes are prime? Which FDs are partial? Keep your answers — we'll verify them as we progress through the normal forms.

---

## 2. First Normal Form (1NF)

### 2.1 Learning Objective for This Section

Determine whether a schema satisfies 1NF, and if not, transform it into 1NF by eliminating multi-valued attributes and nested relations.

---

### 2.2 Intuition

1NF is the starting line. It states: "Every cell in the table holds exactly one atomic value." No lists, no sets, no tables inside tables. The relational model cannot operate on a column that contains a comma-separated list—`WHERE` clauses, joins, and aggregates all assume atomicity.

The tension here is practical, not theoretical. A column storing `'555-0100, 555-0200'` might seem convenient, but the moment you need to find "every employee with phone number 555-0200," your query becomes a string-parsing nightmare. The relational algebra operates on sets of atomic values — give it a set, and it works. Give it a bag of encoded sets, and it breaks.

**A Cross-Domain Connection: 1NF as Data Tidying.** In data science, Hadley Wickham's concept of "tidy data" mandates that each column contain exactly one variable and each row exactly one observation. A column holding comma-separated phone numbers violates the "one variable per column" rule — it's the database equivalent of a messy spreadsheet where a single cell encodes multiple measurements. Data scientists spend a disproportionate amount of project time "tidying" such data before analysis. 1NF enforcement ensures the database never creates the mess in the first place. The transformation from `Employee(EmpID, PhoneNumbers)` to `EmployeePhone(EmpID, PhoneNumber)` is exactly the "gather" or "melt" operation in tidy data workflows — unpivoting a wide, multi-value column into a tall, atomic format suitable for relational operations and statistical computation alike.

---

### 2.3 Formal Definition

A relation schema $R$ is in 1NF if the domain of each attribute contains only *atomic* (indivisible) values, and the value of each attribute in any tuple is a single element from that domain.

---

### 2.4 Violations and Remedies

**Typical Violation.** A column stores multiple values, such as a comma-separated list of phone numbers or a nested table of line items.

**Remedy.** Decompose the multi-valued attribute into a separate relation linked by a foreign key, or expand the list into multiple rows, one per value.

**Example.** Transform `Employee(EmpID, Name, PhoneNumbers)` where `PhoneNumbers` holds a set of values into:

```sql
Employee(EmpID, Name)
EmployeePhone(EmpID, PhoneNumber)
```

Each phone number occupies its own row in `EmployeePhone`. The schema is now in 1NF.

**Practical Application: E-Commerce Product Catalog.** Consider an online marketplace where each product can belong to multiple categories. A naive design stores categories as a comma-separated list in a `Product` table:

```
Product(ProductID, Name, Price, Categories)
Sample row: (P001, "Wireless Mouse", 29.99, "Electronics, Computer Accessories, Office Supplies")
```

This violates 1NF. The business needs to answer queries like "show all products in the Office Supplies category" or "count products per category." With a comma-separated column, these require `LIKE '%Office Supplies%'` patterns — slow, error-prone, and unable to use indexes. Worse, renaming a category (e.g., "Computer Accessories" to "PC Accessories") requires string replacements across all rows, risking partial updates.

The 1NF-compliant design uses a separate junction table:

```sql
Product(ProductID, Name, Price)
ProductCategory(ProductID, CategoryName)
```

Now finding all Office Supplies products is a simple indexed join. Renaming a category becomes a single update to all matching rows in `ProductCategory` — still touching multiple rows, but now structurally explicit and transactionally safe. This design also enables category-level analytics (e.g., average price per category) using standard aggregation, impossible with the comma-separated approach without application-level parsing.

**Practical Application: Healthcare — Patient Allergies.** A hospital system tracks patient allergies. A non-1NF design might store:

```
Patient(PatientID, Name, DOB, Allergies)
Sample row: (1001, "Maria Garcia", 1985-03-12, "Penicillin, Latex, Sulfa")
```

The clinical implications of this violation are severe. When a physician prescribes a medication, the system must check whether the patient has a contraindicated allergy. With a comma-separated `Allergies` column, the check requires substring matching — `WHERE Allergies LIKE '%Penicillin%'` — which can produce false positives (matching "Non-Penicillin") and false negatives (misspelled entries). Moreover, allergy lists often need structured metadata: reaction severity, date of onset, confirming test results. A 1NF design separates this into:

```sql
Patient(PatientID, Name, DOB)
Allergy(AllergyCode, AllergyName, Category)
PatientAllergy(PatientID, AllergyCode, Severity, OnsetDate, ConfirmedBy)
```

Now allergy cross-checking uses exact matching on `AllergyCode`, a foreign key to a controlled vocabulary (e.g., RxNorm or SNOMED CT). Severity and onset date become queryable fields, enabling clinical decision support rules like "warn if patient has a severe allergy to any medication in the penicillin class." The atomicity enforced by 1NF here is not merely a data cleanliness concern — it directly impacts patient safety and regulatory compliance with standards like HL7 FHIR.

---

## 3. Second Normal Form (2NF)

### 3.1 Learning Objective for This Section

Given a 1NF schema, identify partial dependencies on candidate keys and decompose the schema to eliminate them, achieving 2NF.

---

### 3.2 Intuition

2NF targets the problem: "A nonprime attribute depends on only part of a candidate key." When that happens, the attribute describes a subset of the key's components, not the whole key. This duplication leads to update anomalies.

Here's the core insight: a partial dependency is a signal that your table is secretly trying to store two independent facts. In the veterinary clinic, `PetName` depends only on `PetID`, not on the full `{PetID, VetID}` key. This means the table is simultaneously recording "what is this pet's name" and "which vet sees this pet" — two separate facts that happen to share a table. Every time Max sees a new vet, you must repeat his name. That's the structural flaw 2NF fixes.

Think of it like a library catalog card that lists both the book's title and the borrower's address. The title belongs to the book (depends on BookID alone), while the address belongs to the borrower (depends on BorrowerID alone). Jamming both onto one card means every time the same borrower checks out a different book, you must copy their address again. 2NF says: separate the book facts from the borrower facts.

**A Cross-Domain Connection: 2NF as the Single Responsibility Principle.** In software engineering, the Single Responsibility Principle (the "S" in SOLID) states that a class or module should have exactly one reason to change. A table violating 2NF has at least two reasons to change: one when the entity identified by the partial key changes, and another when the association captured by the full key changes. The `EMP_PROJ` table changes both when an employee gets a new name and when hours are logged for a project. Decomposing into `Employee`, `Project`, and `Assignment` gives each table exactly one reason to change — the same refactoring instinct that drives class extraction in object-oriented design. The mechanics differ (relations vs. objects), but the diagnostic question is identical: "What single concept does this structure represent, and does any attribute describe something