## Prerequisites: Functional Dependencies, Keys, and Decomposition

To understand normalization, we must first establish key concepts: functional dependencies, candidate keys, prime attributes, and lossless decomposition.

A **functional dependency (FD)** $X \rightarrow Y$ holds in a relation $R$ if, for any two tuples in $R$, equality on all attributes in $X$ implies equality on all attributes in $Y$. This means $X$ uniquely determines $Y$. For example, if $EmpID \rightarrow Name$, then no two employees with the same ID can have different names.

To find **candidate keys**, compute the **closure** $X^+$ of an attribute set $X$: start with $X$, then repeatedly add attributes determined by known FDs until no more can be added. If $X^+ = U$, where $U$ is the set of all attributes in $R$, then $X$ is a superkey. A **candidate key** is a minimal superkey—no proper subset is also a superkey.

An attribute is **prime** if it appears in any candidate key; otherwise, it is **non-prime**.

A **lossless decomposition** of $R$ into $R_1$ and $R_2$ ensures that the original data can be exactly reconstructed via natural join:  
$$
r = \pi_{R_1}(r) \bowtie \pi_{R_2}(r)
$$  
This condition holds if the common attributes between $R_1$ and $R_2$ form a superkey in at least one of the decomposed relations.

> **Try This Yourself**  
Given $R(A,B,C)$ with FDs: $A \rightarrow B$, $B \rightarrow C$.  
Is $A$ a candidate key? Is $B$ prime?  
*Pause and compute $A^+$ and $B^+$ before reading on.*  
*Solution*: $A^+ = \{A, B, C\}$, so $A$ is a superkey and minimal → candidate key. $B$ is not part of any candidate key → non-prime.

> **Common Misconception**  
“More FDs mean better normalization.”  
Only **true** functional dependencies—those reflecting real-world semantics—should guide schema design. Introducing false dependencies over-constrains the schema; omitting real ones leads to anomalies.

---

## 1. First Normal Form (1NF): Atomicity as a Foundation

Imagine you're building a medical records system. A nurse enters a patient’s allergies as `"penicillin, peanuts, none"`—wait, does “none” negate the list or replace it? This ambiguity arises from **non-atomic data**, the very problem 1NF was designed to eliminate.

### Why Atomicity Matters

In the pre-relational era, data was often stored in repeating groups or nested lists—like a spreadsheet cell containing `"Python, SQL"`. But how do you query “Which employees know Python?” without string parsing? And what if one writes `"python"` (lowercase), or duplicates like `"Python,Python"`? Without atomicity, queries become brittle and inconsistent.

This motivates **atomicity**, the core requirement of 1NF.

### Formal Definition

A relation $R$ is in **First Normal Form (1NF)** if and only if:
1. Each attribute contains **atomic values** (indivisible units).
2. Each tuple has **exactly one value** per attribute.
3. The order of rows and columns is **not semantically meaningful**.

These conditions ensure predictable behavior under relational operations such as selection, projection, and join.

### Worked Example: From Denormalized to 1NF

Start with:

```
Employees(EmpID, Name, Skills)
```

Sample data:  
(E01, "Sam", {"Python", "SQL"})

This violates 1NF because `Skills` is multivalued.

**Step 1: Identify non-atomic attributes**  
→ `Skills` is composite.

**Step 2: Decompose**  
Create two relations:

```
Employee(EmpID, Name)
EmployeeSkill(EmpID, Skill)
```

Now all attributes are atomic. Querying for Python skills is unambiguous:  
$$
\sigma_{Skill = \text{'Python'}}(\text{EmployeeSkill})
$$

**Step 3: Verify losslessness**  
Common attribute: $EmpID$. Since $EmpID$ is a key in `Employee`, the decomposition is lossless.

> **Try This Yourself**  
Can you store multiple skills for one employee in the new design? How?  
*Answer*: Yes—by having multiple rows in `EmployeeSkill` with the same $EmpID$. Each row is a single fact.

> **Analogy: The Library Catalog**  
Think of 1NF like a library catalog: each book has one title, one author, one call number. You wouldn’t list “Tolstoy, Dostoevsky” in one author field. Instead, you’d have separate entries for *War and Peace* and *Crime and Punishment*. Atomicity ensures each piece of data is a single, verifiable claim.

> **Common Misconception**  
“Modern databases support arrays, so 1NF is outdated.”  
While PostgreSQL allows `ARRAY` types, doing so **bypasses 1NF semantics**. Queries become more complex, indexing is less efficient, and constraints (e.g., uniqueness per skill) are harder to enforce. Use sparingly—only when the trade-off is justified.

---

## 2. Second Normal Form (2NF): Eliminating Partial Dependencies

Now consider a hospital’s surgical schedule: `(SurgeryID, SurgeonID, SurgeryDate, SurgeonSpecialty)`. The key is `(SurgeryID, SurgeonID)`, but `SurgeonSpecialty` depends only on `SurgeonID`. If Dr. Lee is a neurosurgeon, why repeat that fact in every surgery row? This redundancy isn’t just wasteful—it’s dangerous. What if one entry mistakenly says “cardiology”?

This is a **partial dependency**, and it’s what 2NF targets.

### The Problem with Composite Keys

Suppose a relation stores order line items with key $(OrderID, ProductID)$, and includes $ProductName$. If $ProductID \rightarrow ProductName$, then $ProductName$ depends only on part of the key—$ProductID$. This suggests $ProductName$ belongs with product data, not order data.

Such a dependency is called a **partial dependency**, and it leads to redundancy.

### Formal Definition

A relation $R$ is in **Second Normal Form (2NF)** if:
1. $R$ is in 1NF.
2. Every non-prime attribute is **fully functionally dependent** on every candidate key—i.e., no non-prime attribute depends on a proper subset of any candidate key.

> **Analogy: The DNA Blueprint**  
A gene isn’t defined by half a chromosome. Just as a complete chromosome pair is needed to determine a trait, a full candidate key is needed to determine a non-prime attribute. A partial match (like `ProductID` alone) isn’t enough—it’s like reading only one strand of DNA.

### Worked Example: Fixing a Partial Dependency

Given:

```
OrderItems(OrderID, ProductID, ProductName, Quantity)
```

FDs:  
- $(OrderID, ProductID) \rightarrow Quantity$  
- $ProductID \rightarrow ProductName$

Candidate key: $(OrderID, ProductID)$  
$ProductName$ is non-prime and depends only on $ProductID$, a proper subset of the key → **partial dependency** → violates 2NF.

**Step 1: Identify the cause**  
$ProductID \rightarrow ProductName$, but $ProductID$ is not a superkey in `OrderItems`.

**Step 2: Decompose**  
Create:

```
OrderItems(OrderID, ProductID, Quantity)
Products(ProductID, ProductName)
```

Now:
- In `Products`, $ProductID$ is a key → $ProductID \rightarrow ProductName$ is valid.
- Decomposition is lossless: common attribute $ProductID$, which is a key in `Products`.

> **Try This Yourself**  
After decomposition, how do you find the product name for order line (O100, P20)?  
*Answer*: Join `OrderItems` and `Products` on $ProductID$.

> **Common Misconception**  
“If a relation has a single-attribute key, it’s automatically in 2NF.”  
Yes—because no proper subset of a singleton key exists. But always **verify the candidate key** first. Misidentifying keys leads to incorrect normalization.

---

## 3. Third Normal Form (3NF): Eliminating Transitive Dependencies

Now suppose we track employee departments and department managers. If `EmpID → Dept` and `Dept → Manager`, then changing a manager requires updating every employee in that department. This **transitive dependency** is like a daisy chain: pull one link, and the whole chain moves.

### The Chain Reaction Problem

Suppose:  
- $EmpID \rightarrow Dept$  
- $Dept \rightarrow Manager$

Then $EmpID \rightarrow Manager$ indirectly. If the manager changes, all employees in that department must be updated—an **update anomaly**. Worse, deleting the last employee in a department could erase the manager information—a **deletion anomaly**.

This **transitive dependency** is what 3NF aims to eliminate.

> **Analogy: The Supply Chain**  
In logistics, a supplier doesn’t talk directly to a retail store—they go through a distributor. If the distributor changes, every store doesn’t need to be reconfigured. Similarly, in 3NF, non-prime attributes shouldn’t depend on other non-prime attributes. Cut the middleman when it causes ripple effects.

### Formal Definition

A relation $R$ is in **Third Normal Form (3NF)** if:
1. $R$ is in 2NF.
2. For every non-trivial functional dependency $X \rightarrow Y$, at least one of the following holds:
   - $X$ is a superkey, or
   - $Y$ is a prime attribute.

This prevents non-prime attributes from being determined by other non-prime attributes unless the determinant is a superkey.

### Worked Example: Normalizing a Transitive Dependency

Given:

```
Employee(EmpID, Dept, Manager)
```

FDs:  
- $EmpID \rightarrow Dept$  
- $Dept \rightarrow Manager$

Candidate key: $EmpID$  
$Dept$ and $Manager$ are non-prime.

Check $Dept \rightarrow Manager$:  
- $Dept$ is not a superkey → violates 3NF.

**Step 1: Identify the transitive dependency**  
$EmpID \rightarrow Dept \rightarrow Manager$, with $Manager$ non-prime.

**Step 2: Decompose**  
Create:

```
Employee(EmpID, Dept)
Department(Dept, Manager)
```

Now:
- In `Department`, $Dept$ is a key → $Dept \rightarrow Manager$ is valid.
- Both relations are in 3NF.
- All FDs are preserved.
- Lossless? Yes—$Dept$ is common and a key in `Department`.

> **Try This Yourself**  
Is $Manager$ now stored redundantly? Does that violate 3NF?  
*Answer*: Yes, $Manager$ repeats—but this is allowed in 3NF. Redundancy is acceptable if it avoids anomalies and preserves functional dependencies.

> **Common Misconception**  
“3NF eliminates all redundancy.”  
No—3NF eliminates **anomaly-causing** redundancy. Some repetition (like $Manager$) is tolerated to preserve dependencies and avoid joins.

---

## 4. Boyce-Codd Normal Form (BCNF): The Superkey Principle

Now imagine a university timetable: `(Professor, Course, Time)`. Suppose each professor teaches only one course, so $Professor \rightarrow Course$. But multiple professors can teach the same course at different times. Now, is $Professor$ a key? Not quite—it doesn’t determine $Time$. Yet it determines $Course$. This tension—where a non-key determines something important—is BCNF’s target.

### When Keys Overlap, Problems Arise

Suppose:
- $Professor \rightarrow Course$
- $Course, Time \rightarrow Professor$

Then both $(Professor, Time)$ and $(Course, Time)$ are candidate keys.

But $Professor \rightarrow Course$: is $Professor$ a superkey? No—it does not determine $Time$. So a non-superkey determines an attribute—a **BCNF violation**.

This can lead to contradictions: what if two professors teach the same course at the same time?

> **Analogy: The Two-Way Street**  
In 3NF, one-way dependencies are allowed as long as they don’t cause anomalies. But BCNF demands **two-way streets**: if $X$ determines $Y$, then $X$ must fully determine the row—no exceptions. It’s like requiring that any identifier you use must be a full license plate, not just the first three letters.

### Formal Definition

A relation $R$ is in **Boyce-Codd Normal Form (BCNF)** if and only if for every non-trivial functional dependency $X \rightarrow Y$, $X$ is a superkey.

This condition is **stronger** than 3NF: every BCNF schema is in 3NF, but not vice versa.

### Worked Example: Achieving BCNF

Given:

```
R(Professor, Course, Time)
```

FDs:  
- $Professor \rightarrow Course$  
- $Course, Time \rightarrow Professor$

Candidate keys: $(Course, Time)$, $(Professor, Time)$

Check $Professor \rightarrow Course$:  
- $Professor$ is not a superkey (does not determine $Time$) → violates BCNF.

**Step 1: Choose violating FD**  
$Professor \rightarrow Course$

**Step 2: Decompose**  
Create:
- $R_1(Professor, Course)$ — includes $Professor \rightarrow Course$
- $R_2(Course, Time, Professor)$ — to preserve $Course, Time \rightarrow Professor$

Check losslessness: common attributes $(Course, Professor)$. In $R_1$, $Professor$ is a key → $(Professor, Course)$ determines all attributes. In $R_2$, $(Course, Time)$ is a candidate key → determines all attributes.

Thus, the decomposition is lossless and both relations are in BCNF.

> **Try This Yourself**  
Is the FD $Course, Time \rightarrow Professor$ preserved?  
*Answer*: Yes—it holds in $R_2$.

> **Common Misconception**  
“BCNF is always better than 3NF.”  
Not necessarily. BCNF may **lose functional dependencies**, requiring application-level checks. Use it only when anomaly prevention is critical (e.g., financial data).

---

## 5. Trade-Offs and Practical Considerations

Having defined the major normal forms, we now examine their trade-offs and practical implications.

### Learning Objectives

By the end of this section, you will be able to:
- Analyze the trade-offs between 3NF and BCNF.
- Evaluate when to stop normalizing.
- Create a normalization strategy based on use case.

### The 3NF vs. BCNF Dilemma

| Property | 3NF | BCNF |
|--------|-----|------|
| Lossless decomposition | ✅ | ✅ |
| Dependency preservation | ✅ | ❌ (not guaranteed) |
| Anomaly prevention | Strong | Complete (for FDs) |

**3NF** is often preferred in OLTP systems because it preserves all dependencies and supports efficient, declarative enforcement via constraints.

**BCNF** eliminates all FD-based anomalies but may require triggers or application logic to maintain lost constraints.

> **Cross-Domain Insight: Software Engineering**  
Normalization mirrors the principle of **single responsibility**: just as a class should have one reason to change, a table should depend on one key. But like over-engineering in code, over-normalization increases complexity. The goal isn’t maximal normal form—it’s **minimal surprises**.

### Worked Example: When BCNF Fails to Preserve Dependencies

Given $R(A,B,C)$ with FDs:  
- $A \rightarrow B$  
- $C \rightarrow B$  
Candidate key: $(A,C)$

Check BCNF:  
- $A \rightarrow B$: $A$ not a superkey → violates BCNF.
- $C \rightarrow B$: $C$ not a superkey → also violates.

Decompose using $A \rightarrow B$:  
- $R_1(A,B)$
- $R_2(A,C)$

Now $C \rightarrow B$ is lost—no relation contains both $C$ and $B$.

To enforce it, you would need a join or a trigger—not supported natively in SQL.

> **Try This Yourself**  
Could you decompose using $C \rightarrow B$ first? Would it help?  
*Answer*: Same issue—either way, one FD is lost. Some schemas **cannot** be decomposed into BCNF while preserving all FDs.

> **Common Misconception**  
“You should always aim for BCNF.”  
No—the goal is **anomaly-free design**, not maximal normal form. In practice, **3NF is often sufficient** and safer due to dependency preservation.

---

## Summary: The Normalization Ladder

| Normal Form | Requirement | Prevents | Preserves Dependencies? |
|-------------|-----------|---------|--------------------------|
| 1NF | Atomic attributes | Unstructured data | Yes |
| 2NF | No partial dependencies | Redundancy from composite keys | Yes |
| 3NF | No transitive dependencies on non-prime attributes | Indirect update anomalies | Yes |
| BCNF | Every determinant is a superkey | Key ambiguity and redundancy | Not guaranteed |

Normalization is a **diagnostic process**, not a rigid checklist. Start with 1NF, then climb the ladder—but **stop when anomalies are resolved** and dependencies are preserved.

> **Final Insight**  
Just as under-normalization risks data corruption, over-normalization harms performance and maintainability. The expert designer uses functional dependencies as a compass, balancing integrity, efficiency, and clarity.