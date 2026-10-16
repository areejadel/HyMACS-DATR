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

## Opening Challenge: The Database That Contradicted Reality

In 2018, a major hospital system discovered that over 1,200 patient records contained conflicting allergy information. A patient listed as "allergic to penicillin" in one table appeared as "no known allergies" in another — because the allergy status had been stored redundantly across multiple tables and updated inconsistently. The root cause was not a software bug or human error in data entry. It was a database schema that *permitted* the contradiction to exist.

This is the problem normalization solves. Not by adding more validation code or application-level checks, but by designing schemas where certain classes of contradiction become structurally impossible. By the end of this lecture, you will be able to look at a schema and say: "This design makes it possible to store two different allergy statuses for the same patient — and here is exactly which normal form would prevent that."

**Pause and predict:** Before we examine the solution, ask yourself: what specific property of a schema allows the same fact to be stored in two places with different values? Is it simply "redundancy," or is there a more precise structural condition? Hold your answer — we will make it surgically precise as we move through each normal form.

**Try this yourself:** Before we dive into formal definitions, look at this simple schema and identify what could go wrong:

`PATIENT_VISIT(PatientID, PatientName, VisitDate, DoctorID, DoctorName, Diagnosis)`

Suppose a patient sees the same doctor on multiple visits. What redundant information is stored? What happens if the doctor changes their name? What happens if we delete the last visit for a particular patient? Jot down your observations — we will return to this exact scenario as we progress through the normal forms.

---

## 1. Functional Dependencies and Keys: The Formal Foundation

### 1.1 Intuition: What is a Functional Dependency?

Imagine you are designing the database for a national election commission. Every registered voter is assigned to exactly one polling station based on their residential address. If two officials independently look up the same voter, they must arrive at the same polling station — otherwise someone has been disenfranchised. This is not a coincidence we hope holds; it is a constraint the system must enforce. The database equivalent is a **functional dependency (FD)**:

$$\text{VoterID} \rightarrow \text{PollingStation}$$

Read this as: "VoterID functionally determines PollingStation." The left-hand side (VoterID) is the **determinant**; the right-hand side (PollingStation) is the **dependent**.

This is a statement about the **rules of the application domain**, not a deduction from a single table snapshot. Even if the current table contains only one row per voter, the FD declares that any two valid rows with the same VoterID must have the same PollingStation. Violating this would mean the same voter is registered at two places — a logical contradiction in this domain.

**Why this matters beyond correctness:** FDs are not abstract formalism. They encode the business rules that prevent your database from silently contradicting reality. A table that permits two different polling stations for one voter has allowed an anomaly that could disenfranchise a real person. Normalization is the systematic removal of structures that make such contradictions possible.

**Thought experiment:** Suppose you inherit a database and discover that the same VoterID appears with two different PollingStations. Before you fix the data, what must you investigate? Is the FD wrong (perhaps voters *can* be assigned to multiple stations)? Or is the FD correct and the data corrupted? This diagnostic question — "is the constraint wrong, or is the data wrong?" — is one you will face repeatedly in real-world schema design, and it has no purely algorithmic answer. It requires domain knowledge.

**Industry Application — Financial Trading Systems:** In algorithmic trading platforms used by firms like Jane Street or Two Sigma, a core FD is $\text{TradeID} \rightarrow \{\text{Instrument, Quantity, Price, Counterparty, SettlementDate}\}$. This FD is not merely a design choice — it is a regulatory requirement enforced by bodies like the SEC and ESMA under MiFID II and Regulation NMS. If a trade execution record could associate one TradeID with two different settlement dates, the firm would fail its trade reconciliation audit, potentially incurring millions in fines and mandatory reporting to regulators. The FD is implemented as a primary key constraint on the `EXECUTIONS` table, but its semantic force comes from the legal obligation that each trade be uniquely and unambiguously identifiable for audit trails. When designing schemas for regulated financial systems, FDs are often derived directly from regulatory reporting standards (e.g., FIX protocol message specifications) rather than from internal business logic alone. This illustrates a broader principle: in compliance-heavy industries, your FDs are not yours to define — they are dictated by external authorities, and your schema either enforces them or exposes you to legal liability.

**Cross-domain insight — FDs as information-theoretic constraints:** There is a deeper way to understand what an FD actually constrains. Consider the VoterID → PollingStation dependency. Before you know a voter's ID, the polling station is uncertain — it could be any of hundreds of locations. The moment you learn the VoterID, that uncertainty collapses to exactly one value. An FD, then, is a statement about information flow: the determinant carries enough information to resolve the dependent completely. This perspective connects database theory to information theory and machine learning — a functional dependency is essentially a claim that the mutual information between determinant and dependent is maximal given the determinant. When you encounter a table that violates an expected FD, you are witnessing a situation where the determinant does *not* fully resolve the dependent, meaning there is additional hidden context (perhaps time, perhaps a missing attribute) that the schema fails to capture. This reframing — FDs as measurements of how much one set of attributes tells you about another — will recur throughout normalization as we discover that anomalies arise precisely when the schema forces you to store the same informational relationship multiple times.

### 1.2 Formal Definition

Let $R$ be a relation schema with attribute sets $X$ and $Y$. A functional dependency $X \rightarrow Y$ holds if, for any two tuples $t_1$ and $t_2$ in any valid instance $r(R)$:

$$t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]$$

The FD is **nontrivial** if $Y \not\subseteq X$. We focus on nontrivial FDs because trivial ones (e.g., $\text{VoterID} \rightarrow \text{VoterID}$) hold automatically and convey no useful information.

**A subtlety worth pausing on:** The definition says "any valid instance," not "the current instance." An FD is a constraint on the set of all possible states the database can ever be in. You cannot prove an FD holds by inspecting today's data; you can only disprove one by finding a counterexample. This is why FDs must come from domain analysis, not from data profiling.

**Analogy — Laws of physics vs. experimental observations:** You cannot prove "all electrons have the same charge" by measuring a million electrons and finding they all match. You might simply not have encountered the exception yet. The statement is a theoretical constraint on what is physically possible — just as an FD is a constraint on what database states are semantically valid. Data profiling shows you what *has* happened; FDs declare what *can* happen. This distinction is why normalization is a design-time activity, not something you retroactively apply by scanning your production data.

**Try this yourself:** Open a dataset you have worked with recently — perhaps a CSV from a data science project. Pick two columns and ask: does the first functionally determine the second? Now ask the harder question: *should* it? What domain rule would justify that constraint? If you cannot articulate the domain rule, you are guessing, not designing.

**Industry Application — Data Governance and Compliance:** This distinction between empirical observation and domain-level constraint has direct regulatory consequences. Under GDPR Article 5(1)(d), organizations must ensure personal data is accurate and kept up to date. A schema that permits contradictory address records for the same data subject violates this principle at the architectural level. Data governance teams at companies like Deutsche Bank and BNP Paribas now conduct schema reviews where functional dependencies are explicitly documented and cross-referenced against regulatory requirements. If an FD like $\text{CustomerID} \rightarrow \text{LegalEntityIdentifier}$ is identified during domain analysis but not enforced by a key constraint, the schema is flagged as a compliance risk — regardless of whether today's data happens to be clean. The audit process asks not "does the data violate the rule?" but "could the schema ever permit a violation?" This shift from data-quality monitoring to schema-level prevention is a direct application of normalization theory in regulatory compliance frameworks.

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

**Provocative question:** If 1NF is so fundamental, why do document databases like MongoDB and Firebase — which explicitly embrace nested structures — exist and thrive? What problems do they solve that 1NF compliance makes harder? The answer reveals that 1NF is not a universal law of data management; it is a design choice optimized for query flexibility and integrity enforcement. When your access patterns are always "load the entire document by ID," nesting is more efficient. When you need to query across documents by nested field values, the pain of non-1NF structures becomes acute. This tension — document model vs. relational model — is one of the most consequential architectural decisions in modern system design, and understanding 1NF gives you the vocabulary to reason about it precisely.

### 2.2 Definition

A relation schema is in First Normal Form (1NF) if:
1. The domain of each attribute includes only **atomic** (indivisible) values.
2. The value of each attribute in any tuple is a single value from that domain.

This prohibits:
- **Multivalued attributes:** A column that holds sets, lists, or repeating groups (e.g., a `Diagnoses` column storing `{Hypertension, Diabetes, Asthma}`).
- **Composite attributes:** Nested structures treated as a single column (e.g., an `Address` column storing `(Street, City, Zip)` as a unit when we need to query individual components).

1NF is a **structural** constraint, not a dependency-based one. It says nothing about redundancy or anomalies; it only enforces the flat-table format.

**Cross-domain analogy — Normalization as lossless compression:** There is a productive way to think about the entire normalization ladder, starting with 1NF, that connects database design to signal processing and data compression. When you take a nested structure like a JSON document with repeating groups and flatten it into 1NF, you are performing an operation analogous to unpacking a compressed representation. The original nested form uses structure — position within a list, nesting depth — to encode relationships implicitly, much like a run-length encoding uses position to encode repetition. Flattening to 1NF makes all relationships explicit as foreign key references, trading structural compactness for queryability. The higher normal forms then remove the redundancy that this unpacking introduces — exactly as a compression algorithm would identify and eliminate repeated patterns. The end goal of full normalization is a schema where every fact is stored exactly once: maximum compression without loss of information, achieved not through bit-level tricks but through dependency analysis. This framing reveals why denormalization (intentionally violating normal forms for performance) is not "undoing" normalization but rather choosing a different point on the space-versus-access-time trade-off curve — exactly the same design decision faced in choosing between compressed and uncompressed data formats.

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

**Try this yourself:** Before reading on, look at the flattened `ASSIGNMENT` table above. Alice's name appears three times. What concrete problem does this cause? Write down at least two specific anomalies — one involving an update, one involving a deletion — then continue. We will formalize these anomaly types when we reach 2NF and 3NF.

### 2.4 Common Misconceptions About 1NF

**Misconception 1: "1NF means my schema is well-designed."**
Reality: 1NF is the minimum structural requirement. A schema in 1NF can still be riddled with update anomalies and redundancy. It is the starting line, not the finish line. The flattened `ASSIGNMENT` table above is in 1NF, yet updating Alice's name requires changing multiple rows — a classic update anomaly.

**Misconception 2: "Always split composite attributes into atomic parts."**
Reality: Decompose a composite attribute only if the application needs to query or constrain its sub-parts independently. If a `Date` attribute is always used as a whole (for comparison or formatting), splitting it into `Year`, `Month`, `Day` introduces unnecessary complexity and join overhead without semantic benefit. The atomicity judgment depends on the application's usage patterns. A useful heuristic: an attribute is non-atomic if the application treats its internal structure as meaningful for queries or constraints.

**Try this yourself:** Consider an attribute `PhoneNumber` that stores `+1-555-123-4567`. Would you split it into `CountryCode`, `AreaCode`, `Exchange`, `LineNumber`? The answer depends entirely on whether your application ever needs to query "all customers in area code 555" or validate country-code formats. If the application treats phone numbers as opaque identifiers for dialing, keeping them atomic is correct. If it needs to filter by geographic region, the composite structure matters and should be decomposed.

**Case Study — The JSON Trap:** A startup built their product catalog with a `ProductSpecs` column storing JSON blobs like `{"weight_kg": 2.3, "voltage": "110V", "color": "black"}`. This was "atomic" in the SQL sense (a single string value) and technically 1NF. But when they needed to query "all products compatible with 110V," every query required a full table scan with JSON parsing. They had achieved structural atomicity while losing queryability — a reminder that 1NF is a necessary condition for good design, not a sufficient one. The real question is not "is this atomic?" but "will I need to query inside this value?"

**Industry Application — E-Commerce Order Processing:** Consider an e-commerce platform processing thousands of orders daily. An `Orders` table initially stores shipping addresses as a single `ShippingAddress` column containing comma-separated values like `"123 Main St, Springfield, IL, 62701, USA"`. This design is in 1NF (the column holds one string), but it creates practical problems when the logistics team needs to route packages by ZIP code or the marketing team needs to analyze sales by state. Every report requires string parsing in application code, which is slow,