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

**Before we continue, try this thought experiment:** You're the DBA for that bookstore at 11 PM on a Friday. The CEO's personal account shows an old address. You update it. Monday morning, a $2,000 special order shipped to his previous apartment. The error wasn't a typo—it was a design choice made six months ago when someone said "just add the address column to the orders table."

**Now here's the real question:** What *exactly* made that design choice wrong? Was it the redundancy? The update cost? Or something deeper—something about what the table was trying to represent? Hold onto your answer. We'll test it against each normal form.

But the bookstore is only one story. The same structural defect manifests across industries, and recognizing the pattern—not just the specific example—is what makes normalization a transferable skill.

**Healthcare:** A hospital's `PATIENT_VISIT` table records `VisitID`, `PatientID`, `PatientName`, `PrimaryPhysicianID`, `PhysicianPhone`, and `WardNumber`. A physician changes her phone number after moving offices. The update must touch every row for every patient she has ever seen—hundreds of thousands of rows across years of visits. One missed row means a critical referral call goes to a dead number. Worse, when a new physician joins the hospital but hasn't yet been assigned a patient, her contact information cannot be stored at all. The table conflates two independent facts: "which physician treated this visit" and "what is this physician's phone number."

**Logistics and supply chain:** A `SHIPMENT_TRACKING` table records `TrackingNumber`, `PackageID`, `SenderID`, `SenderAddress`, `RecipientAddress`, and `CurrentHub`. A business customer relocates their warehouse. Their `SenderAddress` appears on thousands of shipments. The update is not only expensive—it is dangerous. If the address change is applied mid-transaction while new shipments are being inserted, return labels may print with a mix of old and new addresses. The root cause: `SenderAddress` depends on `SenderID`, not on the full key `TrackingNumber`.

**Financial services:** A `LOAN_PAYMENT` table records `PaymentID`, `LoanID`, `CustomerID`, `CustomerCreditScore`, `PaymentAmount`, and `PaymentDate`. A customer's credit score is updated monthly by an external bureau feed. If the score is stored redundantly on every payment row, a single bureau refresh requires updating every historical payment—or worse, only future payments get the new score, creating inconsistent views of the same customer's creditworthiness across different reports. The table is trying to be both a payment ledger and a customer profile.

**The common thread:** In every case, a single table is moonlighting—serving multiple real-world entities simultaneously. One attribute depends on only part of the key, or on another non-key attribute entirely. The anomalies are identical in structure: update propagation across redundant copies, insertion blockage when one entity exists without the other, and deletion side-effects that erase facts you intended to keep. Normalization gives you the vocabulary and the algorithms to detect and resolve this pattern regardless of the domain.

**Pause and reflect:** Look back at the four scenarios. Can you identify, in each one, which attribute depends on something other than the full key? If you can spot that pattern intuitively, you're already thinking in functional dependencies—even before we define them formally.

### 1.2 Intuition

Consider a university database. We know that a given `StudentID` always belongs to exactly one `StudentName`. Whenever two rows share the same `StudentID`, they must share the same `StudentName`. This is not a coincidence—it is a rule enforced by the real world. We capture such rules as **functional dependencies (FDs)**.

**Think of an FD as a guarantee, not a pattern.** If I tell you a student's ID, you can give me back exactly one name—every time, with no exceptions, now and forever. That's the contract. If the university allows a student to have multiple names on file, the contract breaks, and so does any design built on it.

### 1.3 Formal Definition

Let $X$ and $Y$ be sets of attributes in a relation schema $R$. A **functional dependency** $X \rightarrow Y$ holds if, for every possible instance of $R$, whenever two tuples agree on all attributes in $X$, they also agree on all attributes in $Y$.

Think of $X \rightarrow Y$ as: "Given a value for $X$, you can look up exactly one value for $Y$."

**A non-obvious framing:** Functional dependencies are not discovered by looking at your data. They are statements about the *rules of the domain* that your data must obey. If your current table happens to have unique emails per student but the university's policy allows shared emails, then $\{\text{StudentEmail}\} \rightarrow \{\text{StudentID}\}$ does *not* hold—even if every row today satisfies it. This distinction between "true in this instance" and "true by the rules of reality" is the single most common source of normalization errors in practice.

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

**Real-world scar tissue:** A logistics company once stored delivery stops as comma-separated lists in a `Route` column. "Find all packages going to ZIP code 90210" required a full table scan with string parsing—a query that took 45 minutes instead of 200 milliseconds. The fix was 1NF: one row per stop. Normalization isn't academic; it's what stands between you and a query that times out during peak hours.

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

**Try this yourself:** The redundancy we just introduced—Alice's name appearing twice—should feel uncomfortable. Which normal form will eliminate it, and what dependency causes the problem? (If you're thinking "Alice's name depends only on EmpID, not on the full key," you're already anticipating 2NF.)

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

**The root conflict:** This table is moonlighting. It's trying to be both an employee directory ("who is this person?") and a project assignment log ("who's working on what?"). The composite key is perfect for the second job, but the first job only needs half of it. 2NF resolves this by splitting those responsibilities into separate relations—each table gets one clear purpose.

**A useful analogy:** Think of a table like a function in code. A well-designed function does one thing and has a clear signature. A table not in 2NF is like a function that takes two arguments but only uses one of them for half its return values—the coupling is wrong, and when you change the unused argument, you get unexpected behavior in the output. Decomposition to 2NF is refactoring: extract the helper function that only needs the one argument.

**Cross-industry manifestation:** A telecommunications company maintains a `CALL_RECORD` table with attributes $\{\text{CallID}, \text{SubscriberID}, \text{SubscriberName}, \text{PlanID}, \text{PlanName}, \text{CallDuration}\}$. The composite key is $\{\text{CallID}, \text{SubscriberID}\}$. But `SubscriberName` depends only on `SubscriberID`, and `PlanName` depends only on `PlanID`. When a subscriber upgrades their plan from "Basic" to "Premium," the `PlanName` must be updated on every historical call record—millions of rows—or the billing system will show inconsistent plan names on past invoices. The table conflates call detail records with subscriber profiles and plan catalogs. Decomposition separates these into three relations, each with a single responsibility.

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

**The tension, laid bare:** This table is really two separate stories stitched together. One story is "which employee belongs to which department?" — properly keyed by `EmpID`. The other story is "what do we know about each department?" — properly keyed by `DeptID`. When you force both stories into one table, you create a chain of dependencies that snaps when you try to change just one link.

**A revealing question:** Why does 2NF miss this problem entirely? Because 2NF only looks *backward* from nonprime attributes to the key—it checks whether they depend on the whole key. 3NF looks *forward* from the key through other nonprime attributes—it checks whether the dependency chain continues past the first hop. Think of 2NF as checking direct connections, and 3NF as checking for hidden intermediaries.

**Cross-industry manifestation: E-commerce inventory.** An `INVENTORY_ITEM` table records $\{\text{SKU}, \text{ProductName}, \text{SupplierID}, \text{SupplierName}, \text{SupplierCountry}, \text{QuantityOnHand}\}$. The candidate key is $\{\text{SKU}\}$. The table satisfies 2NF because every nonprime attribute depends on the full single-attribute key. But observe: $\{\text{SupplierID}\} \rightarrow \{\text{