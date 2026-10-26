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

Before we define any concepts formally, consider a concrete problem. Imagine a company spreadsheet that tracks employees and their projects:

| EmpID | EmpName | Dept | DeptPhone | ProjectID | ProjName |
|-------|---------|------|-----------|-----------|-----------|
| 101   | Alice   | Sales | 555-0100 | P1        | WidgetX  |
| 101   | Alice   | Sales | 555-0100 | P2        | WidgetY  |
| 102   | Bob     | Sales | 555-0100 | P1        | WidgetX  |
| 103   | Carol   | HR    | 555-0200 | P3        | Onboard  |

**What can go wrong?**

- *Update anomaly:* If the Sales department's phone number changes, we must update three rows. Miss one, and Sales now has two phone numbers.
- *Insertion anomaly:* We cannot record a new department (e.g., "Legal") with its phone number until an employee is assigned to it. The `EmpID` part of the key forces us to invent an employee.
- *Deletion anomaly:* If we remove Carol (the only HR employee), we lose the fact that HR's phone number is 555-0200. The department's phone number vanishes with the employee.

Normalization restructures the schema so each fact lives in exactly one place. The process is mechanical: we use functional dependencies to detect these problems and decomposition to fix them.

**A deeper lens: normalization as compression.** What we are really doing is lossless data compression for relations. Just as a zip file eliminates redundant byte patterns, normalization eliminates redundant fact patterns. The functional dependencies *are* the compression rules — they tell us which columns can be reconstructed from which other columns. The normal forms are quality guarantees: a BCNF schema promises that no fact is stored more than once, just as a well-compressed file promises no wasted bits. This perspective makes the trade-off in Section 6 sharper: sometimes we accept a small amount of redundancy (staying at 3NF) because the "decompression check" — verifying a cross-table constraint — is too expensive to perform at query time.

**Cross-domain connection: normalization as the database analogue of the Single Source of Truth principle in distributed systems.** In distributed systems design, the Single Source of Truth (SSOT) principle states that every piece of data should have exactly one authoritative source — all other representations are derived or cached copies. Normalization is SSOT applied at the schema level. A 3NF schema enforces that each non-key fact has exactly one home table; any query that needs that fact must join to that home. The connection runs deeper: both normalization and SSOT architectures face the same tension between consistency and performance. In microservices, you might denormalize by caching product prices in the order service to avoid a network call — exactly analogous to leaving a transitive dependency in 2NF to avoid a join. The difference is that database normalization gives you a formal, provable criterion (the normal form) for when denormalization has occurred, while distributed systems often rely on ad-hoc judgment. This is why database theory remains relevant even in a world of eventual consistency and CQRS: it provides a rigorous vocabulary for reasoning about redundancy that the broader software engineering field has only partially adopted.

**Cross-domain connection: functional dependencies as an information-theoretic channel.** In information theory, a communication channel has a capacity — the maximum rate at which information can be transmitted. An FD $X \rightarrow Y$ defines a noiseless channel from $X$ to $Y$ with zero entropy: given $X$, the value of $Y$ is completely determined, requiring zero additional bits to encode. When a schema violates 2NF or 3NF, it is effectively transmitting the same information through multiple channels (storing the same fact in multiple rows), which is information-theoretically wasteful. Shannon's source coding theorem tells us that optimal compression removes all redundancy; the normal forms are the database equivalent of a Huffman code — a systematic procedure for eliminating redundancy until each fact is stored exactly once. This connection explains why normalized schemas typically use less storage: they approach the entropy lower bound for the information they contain.

**Try this yourself:** Before reading further, look at the spreadsheet above and count how many distinct *facts* it contains. Now ask: if each fact were stored exactly once, how many separate tables would you need? Sketch your decomposition, then compare it with the formal process we develop below.

**Industry Case Study: Healthcare Claims Processing.** A health insurance company receives claims from hospitals. Each claim contains a procedure code (e.g., CPT-99213 for an office visit) and a diagnosis code (e.g., ICD-10-CM E11.9 for type 2 diabetes). The original operational schema stored everything in one `ClaimDetail` table:

```
ClaimDetail(ClaimID, PatientID, ProcedureCode, ProcDescription, ProcBaseFee,
            DiagnosisCode, DiagDescription, ProviderID, ProviderName, ProviderNPI)
```

The candidate key was `{ClaimID, ProcedureCode, DiagnosisCode}` — a claim can have multiple procedure–diagnosis line items. The FDs included:

- `ProcedureCode → ProcDescription, ProcBaseFee`
- `DiagnosisCode → DiagDescription`
- `ProviderID → ProviderName, ProviderNPI`

All three right-hand sides are nonprime attributes depending on proper subsets of the candidate key. The resulting 2NF violation caused real operational pain: when Medicare updated the `ProcBaseFee` for a common procedure code, the billing system had to touch tens of thousands of claim line items. A single missed update meant a claim paid at the wrong rate, triggering an audit finding. The decomposition to 2NF and then 3NF — separating `Procedure`, `Diagnosis`, and `Provider` into their own tables — reduced the update from an O(n) batch job touching millions of rows to a single-row update in a reference table. This is not a theoretical exercise; it is the difference between a database that scales and one that collapses under maintenance load.

**Industry Case Study: E-Commerce Order Management.** An online retailer stores orders in an `OrderLine` table with the schema:

```
OrderLine(OrderID, LineNumber, ProductSKU, ProductName, CategoryName,
          CustomerID, CustomerEmail, OrderDate, ShipAddr)
```

The candidate key is `{OrderID, LineNumber}`. The FDs include:

- `ProductSKU → ProductName, CategoryName`
- `CustomerID → CustomerEmail`
- `OrderID → CustomerID, OrderDate, ShipAddr`

Here, `CustomerEmail` is transitively dependent on the key: `OrderID → CustomerID` and `CustomerID → CustomerEmail`. The 3NF violation means that if a customer changes their email address, every historical order line for that customer must be updated — or the system must tolerate inconsistent email addresses across old orders. The 3NF decomposition separates `Customer(CustomerID, CustomerEmail)` and `Order(OrderID, CustomerID, OrderDate, ShipAddr)` from `OrderLine`. This is not merely elegant; it is the standard design in production systems at companies like Amazon and Shopify, where customer profile changes must not cascade into millions of historical order records. The join to retrieve the current email is trivial compared to the cost of maintaining redundant copies.

**Concrete Worked Example: Simulating the Healthcare Anomaly.** To make the cost of non-normalization tangible, consider a mid-sized claims processor handling 500,000 claims per month, each averaging 3 procedure codes. The `ClaimDetail` table holds roughly 1.5 million rows. A Medicare fee schedule update changes the `ProcBaseFee` for CPT-99213 from $92.47 to $94.12. In the unnormalized schema, this requires:

```sql
UPDATE ClaimDetail
SET ProcBaseFee = 94.12
WHERE ProcedureCode = 'CPT-99213';
```

This statement must scan and lock 1.5 million rows. On typical hardware with row-level locking, this takes 30–90 seconds during which concurrent claim insertions either block or proceed with the stale fee. If the transaction fails partway through (e.g., a timeout after updating 800,000 rows), the database contains a mix of old and new fees — a silent data corruption that persists until the next audit cycle, potentially causing six-figure payment errors. After normalization, the same update becomes:

```sql
UPDATE Procedure
SET ProcBaseFee = 94.12
WHERE ProcedureCode = 'CPT-99213';
```

This touches exactly one row in the `Procedure` table, completes in milliseconds, and is trivially atomic. The cost difference is not incremental — it is the difference between an operation that can run during business hours and one that requires a maintenance window.

**Concrete Worked Example: Simulating the E-Commerce Anomaly.** An e-commerce platform with 10 million customers and 500 million historical order lines faces a customer email update. In the unnormalized `OrderLine` table:

```sql
UPDATE OrderLine
SET CustomerEmail = 'newemail@example.com'
WHERE CustomerID = 12345;
```

If customer 12345 has placed 50 orders averaging 3 line items each, this touches 150 rows scattered across a multi-terabyte table. Index fragmentation, write-ahead logging overhead, and replication lag make this disproportionately expensive. Worse, if the business rule is "the email on historical orders should reflect what the customer's email was *at the time of the order*," then the update is not just expensive — it is semantically wrong. The normalized design stores the current email in `Customer` and leaves historical orders pointing to `CustomerID`. A query retrieving an old order joins to `Customer` to get the current email; if the historical email is needed for audit purposes, it belongs in a separate `CustomerEmailHistory` table with effective-date tracking. This illustrates a deeper point: normalization not only prevents anomalies, it forces the designer to confront temporal semantics that denormalized schemas often paper over.

**Operational Metrics: Quantifying the Impact.** Industry post-mortems and database migration case studies provide concrete numbers that underscore the practical stakes. When a major U.S. health insurer decomposed their claims schema from 2NF to 3NF in a 2018 migration project (documented in a vendor case study for a leading relational database), they reported a 40% reduction in total storage footprint — from 12 TB to 7.2 TB — due to the elimination of redundant `ProcedureCode → ProcDescription` and `DiagnosisCode → DiagDescription` copies across hundreds of millions of claim lines. More critically, the batch window for fee schedule updates shrank from 4.5 hours to 8 minutes, eliminating the need for a Sunday-morning maintenance outage. In the e-commerce domain, Shopify's engineering blog has described their evolution from a denormalized orders table in the early 2010s to a normalized schema with separate `customer`, `product_variant`, and `order` relations. The trigger was not theoretical elegance but operational pain: a single merchant updating their store name caused a cascading write storm across millions of order records, saturating replication bandwidth and causing read-replica lag that degraded the customer-facing storefront. After normalization, the same update touched one row in the `merchant` table and propagated instantly. These are not edge cases — they are the predictable, mechanical consequences of the FD violations we analyze in this lecture.

---

## 1. Foundational Concepts: Keys and Functional Dependencies

### 1.1 Learning Objective for This Section

Given a relation schema and a set of business rules, you will identify candidate keys, classify attributes as prime or nonprime, and express the rules as functional dependencies.

---

### 1.2 Functional Dependencies: The Detective's Tool

**Intuition.** A functional dependency (FD) captures a statement of the form: "If I know X, then I know exactly one Y." It is a business rule, not a property of the current data.

**Formal Definition.** Given a relation schema $R$, an FD $X \rightarrow Y$ holds if, for every allowable instance $r(R)$, whenever two tuples agree on all attributes in $X$, they must also agree on all attributes in $Y$. $X$ and $Y$ are sets of attributes from $R$.

We write $X \rightarrow Y$ and read it as "$X$ functionally determines $Y$."

**Example.** In a university database, the rule "each instructor belongs to exactly one department" becomes:

$$\text{Instructor} \rightarrow \text{Department}$$

If two rows show `Instructor = 'Dr. Chen'`, they must both show the same `Department` value. If they do not, the business rule is violated.

**Important:** An FD is a constraint on *all possible future states* of the database, not just the current snapshot. You cannot verify an FD by looking at today's data alone; you must know the business rule.

**Cross-domain connection: FDs as mathematical functions.** An FD $X \rightarrow Y$ is exactly a function from the domain of $X$ to the domain of $Y$ — but stated backward from how mathematicians usually write it. In mathematics, $f: X \to Y$ means each $x$ maps to one $y$. In databases, $X \rightarrow Y$ means the same thing: given an $X$ value, the $Y$ value is determined. This is not just notation; it means normalization theory inherits properties from set theory and function composition. For instance, if $A \rightarrow B$ and $B \rightarrow C$, then $A \rightarrow C$ by transitivity — exactly function composition. The entire normal-form hierarchy is a systematic exploration of what happens when the "function" from key to non-key attributes factors through intermediate domains, and which factorizations cause redundancy.

**Cross-domain connection: FDs as type-level constraints in programming languages.** In statically-typed functional programming languages like Haskell or OCaml, a type signature like `f :: X -> Y` guarantees that every value of type `X` maps to exactly one value of type `Y`. An FD $X \rightarrow Y$ is the database analogue of this type signature — it is a compile-time (schema-level) guarantee about the shape of data, not a runtime observation. Database normalization is thus the schema-design equivalent of refactoring a program to eliminate type-level duplication: if you see the same `(X, Y)` mapping repeated in multiple data constructors, you factor it out into its own type, just as normalization factors a partial dependency into its own relation. The difference is that database systems enforce FDs at runtime through constraint checking (or, more commonly, through application logic and hope), while type systems enforce type signatures at compile time. This gap — the lack of compile-time FD enforcement in SQL — is a major source of data corruption in production systems, and it explains the rise of schema-on-write architectures and tools like Prisma and dbt that reintroduce type-level thinking into database design.

**Practical Application: Discovering FDs from Business Rules.** In industry, FDs are rarely handed to you as a formal list. You extract them by interviewing domain experts and reading business requirement documents. For a banking application, you might ask: "Can one account number belong to two different customers?" The answer — "No, each account has exactly one primary owner" — gives you `AccountNumber → CustomerID`. For a logistics system: "Can one shipment tracking number be associated with two different carriers?" The answer gives you `TrackingNumber → CarrierID`. The discipline is to ask: "Given value X, do I know exactly one value Y, as a rule of the business, not just by coincidence in today's data?" This skill is what separates a database designer who merely copies a spreadsheet from one who understands the underlying domain.

**Worked Example: Eliciting FDs in a Ride-Sharing Application.** Consider a ride-sharing platform like Uber or Lyft. You are designing the `Trip` table and sit down with the operations manager. The conversation proceeds:

- *Designer:* "Can one trip ID be associated with two different riders?"
- *Ops:* "No, each trip has exactly one rider."
- *FD:* $\text{TripID} \rightarrow \text{RiderID}$

- *Designer:* "Can one driver operate two trips at the same time?"
- *Ops:* "No, a driver can only accept one trip at a time."
- *FD:* $\{\text{DriverID}, \text{PickupTime}\} \rightarrow \text{TripID}$ (this is a candidate key, not just an FD)

- *Designer:* "Is the fare determined solely by the trip ID?"
- *Ops:* "Yes, we calculate the fare once when the trip ends and it never changes."
- *FD:* $\text{TripID} \rightarrow \text{Fare}$

- *Designer:* "Can the same vehicle be used in two different cities?"
- *Ops:* "No, each vehicle is registered in exactly one city."
- *FD:* $\text{VehicleID} \rightarrow \text{City}$

If the designer skips this elicitation step and just builds a table matching the app's JSON response — `Trip(TripID, RiderID, DriverID, VehicleID, City, Fare, ...)` — they have already baked in a 3NF violation: `VehicleID → City` is a transitive dependency through a non-prime attribute, and every trip for that vehicle redundantly stores the city. The fix is to recognize `Vehicle(VehicleID, City)` as a separate relation. This example is not hypothetical: early versions of several ride-sharing startups made exactly this mistake and paid for it in database migration projects once their trip volume reached tens of millions.

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

**Industry Practice: Surrogate vs. Natural Keys.** In production databases, you will encounter two philosophies for choosing the primary key. A *natural key* uses business-meaningful attributes — `SSN`, `Email`, `ProductCode`. A *surrogate key* introduces an artificial identifier — an auto-incrementing integer or a UUID — that has no business meaning. Surrogate keys simplify normalization because they are always minimal (single-attribute) and never change, eliminating cascading updates when business