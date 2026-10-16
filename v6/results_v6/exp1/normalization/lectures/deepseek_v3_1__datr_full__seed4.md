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

**Opening Hook — The Election Night Disaster (That Almost Happened):**

In 2018, a county elections office migrated voter records to a new database system. During testing, an engineer noticed something alarming: the same voter ID appeared twice — once linked to polling station A, once to station B. The system had silently accepted both rows. If this had gone live, thousands of voters could have been turned away at the wrong locations on election day.

The root cause? The database permitted a violation of a rule that should have been unbreakable: every voter ID determines exactly one polling station. This rule — that a specific input must always produce the same output — is the essence of a **functional dependency (FD)**:

$$\text{VoterID} \rightarrow \text{PollingStation}$$

Read this as: "VoterID functionally determines PollingStation." The left-hand side (VoterID) is the **determinant**; the right-hand side (PollingStation) is the **dependent**.

**Try this yourself:** Before reading further, think of three real-world rules from domains you know that fit the pattern "if you know X, you must know exactly one Y." (Examples: a book's ISBN determines its publisher; a flight number on a given date determines the departure gate; a chemical formula determines the molecular weight.) Notice that these are not statistical correlations — they are hard constraints. If your database allows them to be violated, it is lying about reality.

This is a statement about the **rules of the application domain**, not a deduction from a single table snapshot. Even if the current table contains only one row per voter, the FD declares that any two valid rows with the same VoterID must have the same PollingStation. Violating this would mean the same voter is registered at two places — a logical contradiction in this domain.

**Why this matters beyond correctness:** FDs are not abstract formalism. They encode the business rules that prevent your database from silently contradicting reality. A table that permits two different polling stations for one voter has allowed an anomaly that could disenfranchise a real person. Normalization is the systematic removal of structures that make such contradictions possible.

### 1.2 Formal Definition

Let $R$ be a relation schema with attribute sets $X$ and $Y$. A functional dependency $X \rightarrow Y$ holds if, for any two tuples $t_1$ and $t_2$ in any valid instance $r(R)$:

$$t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]$$

The FD is **nontrivial** if $Y \not\subseteq X$. We focus on nontrivial FDs because trivial ones (e.g., $\text{VoterID} \rightarrow \text{VoterID}$) hold automatically and convey no useful information.

**A subtlety worth pausing on:** The definition says "any valid instance," not "the current instance." An FD is a constraint on the set of all possible states the database can ever be in. You cannot prove an FD holds by inspecting today's data; you can only disprove one by finding a counterexample. This is why FDs must come from domain analysis, not from data profiling.

**Analogy — The building code vs. the building:** An FD is like a clause in the building code that says "every apartment must have exactly one front door." Walking through an existing building and observing that every apartment happens to have one front door does not prove the rule exists — maybe you just haven't found the illegal apartment with two doors yet. The rule is a constraint on what can be built, not a description of what was built. Similarly, an FD constrains what data can ever be stored, not what data happens to be stored today.

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

**Case Study — The Hospital Scheduling Crisis:**

A regional hospital system stored patient appointments in a table where one column, `Procedures`, contained comma-separated lists like "X-Ray, Blood Test, MRI." For years, the scheduling desk used a custom script to parse these strings when patients called to confirm individual procedures. When the hospital upgraded to a standard EHR system, the script broke — and suddenly, no one could answer the question "how many MRIs are scheduled for Tuesday?" without manually reading thousands of rows.

The fix was a 1NF decomposition: one row per patient per procedure. This tripled the row count but made the data queryable with standard SQL. The "information" that three procedures belonged to the same patient visit was preserved by a shared `AppointmentID` — explicit grouping replaced implicit grouping.

**The tension before the resolution:** 1NF feels destructive because it takes a compact, human-readable representation and explodes it into many rows. But the resolution is that relational databases are optimized for exactly this flat structure. The join operation, which we will rely on throughout normalization, exists precisely to reassemble related rows when needed. You are not losing structure; you are converting it from a format only custom code can read into a format the database engine can manipulate efficiently.

**Industry Application — E-Commerce Order Processing:**

Consider an online retailer like Amazon or Shopify. When a customer places an order containing multiple products, the natural document representation is a JSON object with a nested `line_items` array:

```json
{
  "order_id": 48291,
  "customer_email": "j.smith@email.com",
  "order_date": "2025-03-15",
  "line_items": [
    {"sku": "B017", "quantity": 2, "unit_price": 24.99},
    {"sku": "C342", "quantity": 1, "unit_price": 89.50}
  ]
}
```

A developer might be tempted to store this JSON blob directly in a single `orders` table column. This is fast to insert and mirrors the frontend data structure exactly. But the moment the business needs to answer questions like "what is the total revenue from SKU B017 across all orders this quarter?" or "which products are most frequently purchased together?", the nested structure becomes a liability. Each such query requires parsing every JSON blob in the table — an operation that cannot use standard B-tree indexes and scales linearly with table size.

The 1NF decomposition splits this into two tables:

`ORDERS(OrderID, CustomerEmail, OrderDate)`
`ORDER_LINES(OrderID, SKU, Quantity, UnitPrice)`

Now a simple indexed query on `ORDER_LINES.SKU` answers the revenue question in milliseconds regardless of table size. The trade-off is that reconstructing the original nested view requires a join — but this is exactly what relational databases are engineered to do efficiently. In e-commerce systems processing millions of orders, this normalization is not optional; it is the difference between a dashboard that loads in under a second and one that times out.

**Industry Application — Insurance Claims Processing:**

Insurance companies manage claims that involve multiple claimants, adjusters, policies, and payouts. A legacy system at a mid-sized property insurer stored claim notes as free-text fields where adjusters typed narrative updates like "Spoke with claimant John Doe, estimate revised to $4,200, adjuster Sarah Chen assigned." When the company needed to analyze average settlement amounts by adjuster or detect claims with unusually high revision counts, they discovered that critical structured data — dollar amounts, adjuster names, claimant identifiers — was buried inside unstructured text.

The 1NF remediation required extracting structured attributes into separate columns: `ClaimID`, `AdjusterID`, `ClaimantID`, `EstimateAmount`, `NoteTimestamp`. Each narrative update became a separate row rather than a concatenated paragraph. This increased storage volume by roughly 4× but enabled actuarial analysis that previously required weeks of manual spreadsheet work. The key insight: what the business initially perceived as "convenient narrative" was actually multiple distinct facts (who spoke to whom, what was the new estimate, when did this happen) forced into a single attribute. 1NF separated them into queryable atomic values.

**Industry Application — Banking Transaction Reconciliation:**

A commercial bank's wire transfer system stored beneficiary details as a composite `BeneficiaryInfo` column containing strings like "ACME Corp|Routing:021000021|Acct:987654321|Ref:INV-4521". Each component was separated by a delimiter. For years, the reconciliation department used a Perl script written by a developer who had since left the bank. When a regulatory audit required the bank to demonstrate that no transfers had been sent to sanctioned entities, the script proved inadequate — it could not handle edge cases where the reference field contained the delimiter character, and there was no way to index individual components for efficient screening.

The 1NF decomposition split `BeneficiaryInfo` into `BeneficiaryName`, `RoutingNumber`, `AccountNumber`, and `ReferenceCode` as separate atomic columns. This enabled the compliance team to join the wire transfer table against the OFAC sanctions list on `BeneficiaryName` using standard indexed queries, reducing screening time from overnight batch processing to near-instantaneous. More importantly, it eliminated the dependency on a single developer's undocumented script — a classic operational risk that 1NF directly addresses by moving structure from application code into the database schema where it is visible, documented, and enforceable.

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

**Industry Application — Logistics and Supply Chain:**

A freight logistics company tracks shipments through a `SHIPMENTS` table where each row represents one container. A column `StopSequence` stored the route as a pipe-delimited list: "Port of Shanghai|Port of Busan|Port of Long Beach|Kansas City Railyard|Chicago Distribution Center". Operations managers needed to answer questions like "how many containers pass through Kansas City Railyard each month?" and "what is the average dwell time at Port of Long Beach for containers originating in Shanghai?"

The non-atomic `StopSequence` column made these queries impossible with standard SQL. The company's workaround was a weekly export to a Python script that parsed the strings and produced summary reports — a process that took four hours and was two days stale by the time managers saw it.

The 1NF decomposition created a `SHIPMENT_STOPS` table:

| ContainerID | StopNumber | Location | ArrivalTimestamp | DepartureTimestamp |
|-------------|------------|----------|------------------|---------------------|
| C8942 | 1 | Port of Shanghai | 2025-02-01 08:00 | 2025-02-01 20:00 |
| C8942 | 2 | Port of Busan | 2025-02-03 14:00 | 2025-02-04 06:00 |
| C8942 | 3 | Port of Long Beach | 2025-02-14 09:00 | 2025-02-15 17:00 |
| C8942 | 4 | Kansas City Railyard | 2025-02-18 22:00 | 2025-02-19 10:00 |
| C8942 | 5 | Chicago Distribution Center | 2025-02-20 15:00 | NULL |

This transformation enabled real-time dashboards showing container volumes by location, dwell time analytics with simple date arithmetic (`DepartureTimestamp - ArrivalTimestamp`), and route optimization queries that joined `SHIPMENT_STOPS` against historical transit time averages. The row count increased by a factor equal to the average number of stops per shipment (roughly 6×), but the business value — real-time visibility into the supply chain — was transformative. The implicit sequence information (which stop came first) became an explicit `StopNumber` column, making the ordering queryable and sortable.

### 2.4 Common Misconceptions About 1NF

**Misconception 1: "1NF means my schema is well-designed."**
Reality: 1NF is the minimum structural requirement. A schema in 1NF can still be riddled with update anomalies and redundancy. It is the starting line, not the finish line. The flattened `ASSIGNMENT` table above is in 1NF, yet updating Alice's name requires changing multiple rows — a classic update anomaly.

**Misconception 2: "Always split composite attributes into atomic parts."**
Reality: Decompose a composite attribute only if the application needs to query or constrain its sub-parts independently. If a `Date` attribute is always used as a whole (for comparison or formatting), splitting it into `Year`, `Month`, `Day` introduces unnecessary complexity and join overhead without semantic benefit. The atomicity judgment depends on the application's usage patterns. A useful heuristic: an attribute is non-atomic if the application treats its internal structure as meaningful for queries or constraints.

**Try this yourself:** Consider an attribute `PhoneNumber` that stores `+1-555-123-4567`. Would you split it into `CountryCode`, `AreaCode`, `Exchange`, `LineNumber`? The answer depends entirely on whether your application ever needs to query "all customers in area code 555" or validate country-code formats. If the application treats phone numbers as opaque identifiers for dialing, keeping them atomic is correct. If it needs to filter by geographic region, the composite structure matters and should be decomposed.

**Industry Application — Telecommunications Subscriber Management:**

A mobile network operator stores subscriber identifiers using the IMSI (International Mobile Subscriber Identity), a 15-digit number structured as `MCC-MNC-MSIN` where MCC is the 3-digit mobile country code, MNC is the 2-3 digit mobile network code, and MSIN is the remaining digits identifying the subscriber within that network. Initially, the operator stored this as a single `IMSI` column.

When the company needed to implement roaming charge differentiation — charging different rates based on whether a subscriber's home network was in the same country (MCC) or a different one — the single-column design forced every query to use substring operations: `WHERE SUBSTRING(IMSI,