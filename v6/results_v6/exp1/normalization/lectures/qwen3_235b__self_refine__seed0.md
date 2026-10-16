# Normalization Forms and Database Schema Design (1NF–BCNF)

By the end of this lecture, you will be able to:  
1. **Recall** the definitions and criteria for 1NF, 2NF, 3NF, and BCNF using functional dependencies and candidate keys.  
2. **Identify** partial, transitive, and non-superkey functional dependencies in a schema and **explain** how each leads to insertion, deletion, or update anomalies.  
3. **Apply** decomposition algorithms step-by-step to convert a schema into 2NF, 3NF, and BCNF, and **verify** whether the decomposition is lossless and preserves functional dependencies.  
4. **Analyze** a real-world schema for normalization violations and **justify** a design decision to normalize or denormalize based on use case requirements.  
5. **Evaluate** trade-offs between full normalization and denormalization in terms of data consistency, query performance, and system maintainability.

---

## Prerequisites: Functional Dependencies and Candidate Keys

Imagine you're debugging a hospital database where two patients with the same medical record number (MRN) have different birthdates. You check the logs—no recent edits. The system insists both records are valid. How is this possible?

The answer lies not in a software bug, but in **missing constraints**: the schema failed to enforce that MRN determines DOB. Without this functional dependency baked into the structure, the database treats them as unrelated facts.

This is why we begin not with tables, but with **dependencies**—the invisible laws that bind data together.

### Functional Dependency (FD)

A functional dependency $ X \rightarrow Y $ holds on a relation schema $ R $ if, for every valid instance of $ R $, any two tuples that agree on $ X $ must also agree on $ Y $. Formally:

Let $ R $ be a relation schema over attribute set $ \mathcal{A} $. For all tuples $ t_1, t_2 $ in any legal instance of $ R $,
$$
t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y].
$$
This condition must hold in **every possible legal state**, not just the current data.

> 🔍 **Clarification**:  
Functional dependencies are **deterministic constraints**, not statistical trends. A single violation invalidates an FD. For example, if $ \text{SSN} \rightarrow \text{Name} $ fails once (same SSN, different names), the dependency does not hold—regardless of frequency.

**Try this yourself**:  
Suppose $ \text{ISBN} \rightarrow \text{Author} $. You find one book with ISBN 978-0... listed under "Tolkien" and another under "Rowling". Does the FD hold?  
→ No. Even one counterexample breaks it. The dependency is either universally true or false.

### Armstrong’s Axioms and Attribute Closure

We use **Armstrong’s Axioms** to derive all FDs logically implied by a given set $ \mathcal{F} $:

1. **Reflexivity**: If $ Y \subseteq X $, then $ X \rightarrow Y $.  
2. **Augmentation**: If $ X \rightarrow Y $, then $ XZ \rightarrow YZ $.  
3. **Transitivity**: If $ X \rightarrow Y $ and $ Y \rightarrow Z $, then $ X \rightarrow Z $.

These axioms mirror how implications work in logic. Think of them as the **algebra of dependencies**—rules for manipulating what follows from what.

From these, we derive useful rules:
- **Union**: $ X \rightarrow Y $ and $ X \rightarrow Z $ imply $ X \rightarrow YZ $.  
- **Decomposition**: $ X \rightarrow YZ $ implies $ X \rightarrow Y $ and $ X \rightarrow Z $.

To determine whether a set of attributes determines all others (i.e., is a superkey), we compute its **attribute closure**.

#### Algorithm: Attribute Closure $ X^+ $

**Input**: Attribute set $ X $, FD set $ \mathcal{F} $  
**Output**: $ X^+ = \{ A \mid X \rightarrow A \text{ is implied by } \mathcal{F} \} $

1. Initialize $ X^+ \leftarrow X $.  
2. While changes occur:  
   - For each FD $ A \rightarrow B $ in $ \mathcal{F} $:  
     - If $ A \subseteq X^+ $, then $ X^+ \leftarrow X^+ \cup B $.  
3. Return $ X^+ $.

If $ X^+ = \mathcal{A} $, then $ X $ is a **superkey**. A **candidate key** is a minimal superkey: no proper subset of $ X $ is a superkey.

> 💡 **Analogy: Chemical Reaction Chain**  
Think of attribute closure like a chain reaction in chemistry. Each FD is a reagent: if its inputs (reactants) are present, it produces new outputs (products). You start with a seed set $ X $, and keep applying reactions (FDs) until no new attributes form. The final compound is $ X^+ $.

**Try this yourself**:  
In a library schema:  
- $ \text{CallNumber} \rightarrow \text{Author}, \text{Title} $  
- $ \text{Title} \rightarrow \text{Genre} $  
What is $ \text{CallNumber}^+ $?  
→ Start: {CallNumber} → apply first FD → {CallNumber, Author, Title} → apply second → {CallNumber, Author, Title, Genre}. Done.

> ✅ **Quick Check**:  
Is $ \text{CallNumber} $ a superkey? Only if these are all the attributes. If there's also "Publisher", then no.

> 🛑 **Misconception Alert**:  
$ \text{Course} \rightarrow \text{Instructor} $ does not make Course a key. Keys must determine **all** attributes.

> 💼 **Application in Healthcare**:  
In an EHR system, $ \text{PatientMRN} \rightarrow \text{DOB} $ must hold. If $ \text{PatientMRN}^+ $ does not include DOB, the schema fails to enforce this critical dependency—risking misidentification.

---

## First Normal Form (1NF): Atomicity and Structural Integrity

Here’s a paradox: you can have a perfectly consistent database—every rule followed, every transaction valid—and still be unable to answer a simple question: *"Which patients are allergic to penicillin?"*

Why? Because the data is trapped inside unstructured cells.

> 🧩 **Concrete Example First**:  
Suppose allergies are stored as comma-separated values:

| PatientID | Allergies             |
|-----------|------------------------|
| P001      | penicillin, peanuts    |

Can we reliably query patients allergic to penicillin?  
No—formatting variations ("penicillin; peanuts", "penicillin and peanuts") prevent consistent parsing.

Instead, represent each fact individually:

| PatientID | Allergen     |
|-----------|--------------|
| P001      | penicillin   |
| P001      | peanuts      |

Now each value is **atomic**: indivisible under the operations of the database.

### Formal Definition of 1NF

A relation is in **1NF** if:
1. All attribute values are **atomic** (no sets, lists, or composite structures),
2. There are no **repeating groups** (e.g., Phone1, Phone2, Phone3).

> 💡 **Note on Atomicity**:  
Atomicity is context-dependent.  
- For email routing, `alice@uni.edu` is atomic.  
- For domain analysis, splitting into username and domain may be appropriate.

> 🧠 **Cross-Domain Insight: Linguistics and Tokenization**  
In natural language processing, splitting text into words is called *tokenization*. 1NF is the database analog: **tokenizing compound data into discrete, addressable units**. Just as NLP fails if "New York" is split into "New" and "York", databases fail if atomicity is misjudged. The unit of meaning defines the atom.

### Worked Example: Medical Allergies

**Pre-1NF**:

| PatientID | Allergies             |
|-----------|------------------------|
| P001      | penicillin, peanuts    |

❌ Violates 1NF: multivalued cell.

**Post-1NF**:

| PatientID | Allergen     |
|-----------|--------------|
| P001      | penicillin   |
| P001      | peanuts      |

✅ Each fact is atomic. Benefits:
- Supports foreign key to an `Allergens` table,
- Enables reliable queries:  
  ```sql
  SELECT * FROM PatientAllergies WHERE Allergen = 'penicillin';
  ```
- Prevents parsing errors.

**Try this yourself**:  
You see a table `Employees` with `Skills` as "Java, Python, SQL". How do you bring it to 1NF?  
→ Create `EmployeeSkills(EmployeeID, Skill)` with one row per skill.

> ✅ **Quick Check**:  
Why is storing phone numbers as `"555-1234, 555-5678"` unacceptable in 1NF?  
Answer: It violates atomicity—individual numbers cannot be constrained or queried reliably.

> 🛑 **Misconception Alert**:  
Using `SPLIT()` in SQL or application code does **not** satisfy 1NF. The schema itself must enforce atomicity. Without constraints, inconsistent formatting breaks correctness.

> 💼 **Real-World Application (Finance)**:  
Storing currencies as `"USD, EUR"` prevents accurate aggregation. 1NF requires one row per currency, enabling correct FX conversion.

---

## Second Normal Form (2NF): Eliminating Partial Dependencies

Imagine a warehouse where every time a product is shipped from a location, the system records the warehouse manager’s name. Same warehouse, same manager—repeated across thousands of rows. Now the manager retires. How many rows must you update?

This isn’t just inefficiency—it’s **risk**. Miss one row, and your audit log claims a retired manager approved a shipment.

This happens because the manager depends not on the full key, but on part of it.

> 🧩 **Concrete Example First**:  
Consider a retail sales table:

> **Sales**(ItemID, ItemName, StoreID, StoreLocation, Quantity)  
> Key: $ \{\text{ItemID}, \text{StoreID}\} $

Observe:
- $ \text{ItemID} \rightarrow \text{ItemName} $: item name depends only on ItemID.
- $ \text{StoreID} \rightarrow \text{StoreLocation} $: location depends only on StoreID.

But ItemName and StoreLocation do not depend on the **full key**—only parts of it. This causes anomalies.

> ❗ **Anomaly Demonstration**:
- **Update**: Changing `ItemName` in one row leads to inconsistency.
- **Insert**: Cannot add a new item without a sale.
- **Delete**: Removing the last sale erases item information.

These result from **partial dependencies**: non-key attributes depending on a proper subset of a candidate key.

### Formal Definition of 2NF

A relation is in **2NF** if:
1. It is in 1NF,
2. Every **non-prime** attribute is **fully functionally dependent** on every candidate key.

- **Prime attribute**: part of any candidate key.
- **Non-prime attribute**: not part of any candidate key.
- **Partial dependency**: non-prime attribute depends on a proper subset of a candidate key.

> 💡 **Analogy: Lock and Key Mechanism**  
A composite key is like a two-factor lock: both ItemID and StoreID are needed to "unlock" a sale. But if ItemName can be retrieved using only ItemID, it’s as if the lock is bypassed. 2NF ensures that **only the full key can open the box**.

### Worked Example: Retail Inventory

> **Sales**(ItemID, ItemName, StoreID, StoreLocation, Quantity)  
> FDs:
> - $ \text{ItemID} \rightarrow \text{ItemName} $
> - $ \text{StoreID} \rightarrow \text{StoreLocation} $
> - Key: $ \{\text{ItemID}, \text{StoreID}\} $

Identify:
- Prime attributes: ItemID, StoreID
- Non-prime attributes: ItemName, StoreLocation, Quantity
- Partial dependencies:
  - $ \text{ItemID} \rightarrow \text{ItemName} $: ItemID ⊂ key
  - $ \text{StoreID} \rightarrow \text{StoreLocation} $: StoreID ⊂ key

👉 Violates 2NF.

**Decomposition**:
1. **Items**(ItemID, ItemName) — key: ItemID  
2. **Stores**(StoreID, StoreLocation) — key: StoreID  
3. **Sales**(ItemID, StoreID, Quantity) — key: {ItemID, StoreID}

Now all non-prime attributes depend on full keys.

✅ **Lossless Join Check**:  
$$
\text{Sales} \bowtie \text{Items} \bowtie \text{Stores} = \text{Original}
$$
Yes—join keys are keys in their respective tables.

**Try this yourself**:  
Suppose `Projects(EmployeeID, ProjectID, ProjectLead, Hours)` with key {EmployeeID, ProjectID} and $ \text{ProjectID} \rightarrow \text{ProjectLead} $. Does it violate 2NF?  
→ Yes. ProjectLead depends only on ProjectID, a subset of the key.

> ✅ **Quick Check**:  
Is 2NF relevant if all candidate keys are single-attribute?  
Answer: No. With atomic keys, no proper subsets exist → no partial dependencies → 1NF implies 2NF.

> 🛑 **Misconception Alert**:  
2NF specifically targets **partial dependencies**, not general redundancy. If keys are single-attribute, proceed directly to 3NF.

> 💼 **Application in Logistics**:  
In a shipping manifest, if $ \text{TruckID}, \text{RouteID} \rightarrow \text{DriverName} $, but $ \text{TruckID} \rightarrow \text{DriverName} $, then DriverName depends only on TruckID → partial dependency → violates 2NF.

---

## Third Normal Form (3NF): Eliminating Transitive Dependencies

Suppose you update a manager’s email in an employee table. You change it in one row. But the same manager appears in 47 others. Are they all updated?

If not, you now have two truths: one manager, two emails. The system can’t tell which is correct.

This isn’t a user error. It’s a **design flaw**: the email is not directly tied to the key, but to an intermediate attribute.

> 🧩 **Concrete Example First**:  
> **Employees**(EmpID, Dept, Manager, ManagerEmail)  
> FDs:
> - $ \text{Dept} \rightarrow \text{Manager} $
> - $ \text{Manager} \rightarrow \text{ManagerEmail} $
> - Key: EmpID

So:  
EmpID → Dept → Manager → ManagerEmail

ManagerEmail is transitively determined by EmpID through Manager. If Manager changes, ManagerEmail must be updated in multiple rows.

👉 This is a **transitive dependency**: a non-prime attribute determined through another non-key attribute.

### Formal Definition of 3NF

A relation is in **3NF** if:
1. It is in 2NF,
2. For every non-trivial FD $ X \rightarrow Y $, at least one holds:
   - $ X $ is a superkey, or
   - $ Y $ is a **prime attribute**.

This allows $ X \rightarrow Y $ even if $ X $ is not a superkey—**provided $ Y $ is part of a candidate key**.

> 💡 **Analogy: Information Telephony**  
Transitive dependencies are like playing "telephone" with data. EmpID whispers "Dept" to Manager, who whispers "ManagerEmail" to the system. Each handoff introduces risk of corruption. 3NF cuts the chain: every attribute must hear the truth directly from the key—or not at all.

### Worked Example: Hospital Staffing

> **Employees**(EmpID, Dept, Manager, ManagerEmail)  
> FDs:
> - $ \text{Dept} \rightarrow \text{Manager} $
> - $ \text{Manager} \rightarrow \text{ManagerEmail} $
> - Key: EmpID

Check $ \text{Manager} \rightarrow \text{ManagerEmail} $:
- $ \text{Manager} $ is not a superkey,
- $ \text{ManagerEmail} $ is not prime → ❌ violates 3NF.

**Decomposition**:
1. **Departments**(Dept, Manager) — key: Dept  
2. **Managers**(Manager, ManagerEmail) — key: Manager  
3. **Employees**(EmpID, Dept) — key: EmpID

Now:
- ManagerEmail stored once,
- Updates propagate correctly,
- Join recovers original data.

✅ All FDs preserved? Yes.  
✅ Lossless join? Yes.

**Try this yourself**:  
In `Orders(OrderID, CustomerID, CustomerCity, Total)` with $ \text{CustomerID} \rightarrow \text{CustomerCity} $, and key OrderID:  
- Is CustomerCity prime? No.  
- Is CustomerID a superkey? No.  
→ Violates 3NF.

> ✅ **Quick Check**:  
Why doesn’t $ \text{Dept} \rightarrow \text{Manager} $ violate 3NF in **Departments**?  
Answer: Dept is a superkey → satisfies 3NF condition.

> 🛑 **Misconception Alert**:  
3NF **allows** $ X \rightarrow Y $ if $ Y $ is prime—even if $ X $ is not a superkey. This can still cause anomalies if $ Y $ is updated inconsistently.

> 💼 **Application in E-Commerce**:  
In `Orders(OrderID, Product, Supplier, SuppPhone)`:
- $ \text{Product} \rightarrow \text{Supplier} $
- $ \text{Supplier} \rightarrow \text{SuppPhone} $
- Key: OrderID

Then $ \text{Supplier} \rightarrow \text{SuppPhone} $: Supplier not superkey, SuppPhone not prime → violates 3NF.  
Fix: Split into `Products(Product, Supplier)`, `Suppliers(Supplier, SuppPhone)`.

---

## Boyce-Codd Normal Form (BCNF): Every Determinant Is a Superkey

Here’s a riddle:  
A university database enforces that no instructor teaches two courses at the same time.  
It also enforces that each course has exactly one instructor.  
You enter data carefully.  
Yet, the system allows one instructor to teach two courses at the same time.

How?

> 🧩 **Concrete Example First**:  
> **Teaching**(Course, Instructor, Time)  
> FDs:
> - $ \text{Instructor}, \text{Time} \rightarrow \text{Course} $: prevents double-booking
> - $ \text{Course} \rightarrow \text{Instructor} $: each course has one instructor

Candidate keys:
- $ \{\text{Instructor}, \text{Time}\} $
- $ \{\text{Course}, \text{Time}\} $

Now, $ \text{Course} \rightarrow \text{Instructor} $:  
- Course is **not** a superkey (does not determine Time),
- But Instructor is **prime** → allowed in 3NF.

But consider:
- (CS101, Dr. Lee, 10:00)
- (CS102, Dr. Lee, 10:00)

Both satisfy $ \text{Instructor}, \text{Time} \rightarrow \text{Course} $? No—same instructor, same time, two courses → violates FD.

Yet the database allows it because the FD isn't enforced—it's not on a superkey.

Thus, 3NF is insufficient—we require BCNF.

> 💡 **Analogy: Legal Jurisdiction**  
In a legal system, anyone can report a crime, but only a judge can issue a warrant. In BCNF, **any attribute can determine another**, but only a **superkey** (the judge) can legally do so. 3NF is more lenient: even non-judges can issue warrants if the outcome is "important" (prime). BCNF removes that exception.

### Formal Definition of BCNF

A relation is in **BCNF