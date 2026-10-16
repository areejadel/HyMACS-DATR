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

**Pause and feel the tension:** Your table is doing something physically impossible in the real world—it's forcing you to store the same fact (a customer's address) in multiple places, and those copies can disagree. Every time you add a column to a table without checking its dependencies, you risk creating a miniature version of this chaos. The question normalization asks is brutally simple: *what determines what?* And if the answer is "not the whole key," you have a problem.

**Try this yourself — before we define anything formally:** Look at the bookstore table I just described. List every column. Now, for each column, ask: "If I know the value of this column, can I predict exactly one value for any other column?" For instance, if I tell you `CustomerID = 42`, do you know the `CustomerName`? The `ShippingAddress`? The `OrderID`? Write down your answers. You've just discovered functional dependencies without knowing the term yet. Hold onto that list — we'll check it against the formal definition in a moment.

### 1.2 Intuition

Consider a university database. We know that a given `StudentID` always belongs to exactly one `StudentName`. Whenever two rows share the same `StudentID`, they must share the same `StudentName`. This is not a coincidence—it is a rule enforced by the real world. We capture such rules as **functional dependencies (FDs)**.

Here's an analogy: think of an FD as a mathematical function in disguise. Just as $f(x) = x^2$ guarantees that input $3$ always yields output $9$, the FD $\text{StudentID} \rightarrow \text{StudentName}$ guarantees that student S1 always yields the same name. The table is just a set of input-output pairs, and the FD is the assertion that no input maps to two different outputs. If it does, the "function" is broken—and so is your schema.

**Cross-domain insight — database normalization meets control theory:** Functional dependencies are essentially *observability constraints* in reverse. In control theory, a system is observable if you can reconstruct its entire internal state from its outputs. An FD $X \rightarrow Y$ makes the opposite claim: knowing $X$ is *sufficient* to determine $Y$, but $Y$ tells you nothing you couldn't already infer. The anomalies we'll study are exactly what happens when your schema violates this observability-like property — the database loses the ability to maintain a single source of truth for each fact, just as an unobservable control system loses the ability to track its internal state from sensor readings. Both fields converge on the same principle: every piece of information must have exactly one authoritative source.

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

**Interactive exercise — design a counterexample:** Add exactly one row to the `ENROLLMENT` table above that breaks the FD $\{\text{StudentEmail}\} \rightarrow \{\text{StudentID}\}$. What scenario does this represent? *(Hint: think about shared mailboxes, or a student changing their email and another student claiming the old one.)* This exercise exposes the gap between "this table says so" and "the real world guarantees it." Only the latter counts as a functional dependency.

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

**Cross-domain insight — 1NF as the database equivalent of first-order logic's term restriction:** In first-order predicate logic, terms must be individual constants or variables — you cannot substitute an entire formula where a term is expected. This restriction is not arbitrary; it's what makes unification and automated reasoning decidable. 1NF imposes the identical constraint on the relational model: every cell must contain a single value from the domain, not a set, not a nested relation. Violate this, and relational algebra operators (selection, projection, join) lose their well-defined semantics, just as allowing formulas-as-terms would break unification in logic programming. The parallel runs deeper — both restrictions exist to guarantee that a finite set of primitive operations can compose correctly over all possible inputs.

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

**Interactive moment:** Look at the "After" table. You've just created a problem—Alice's name appears twice. If she changes her name, you must update two rows. But notice: you couldn't even express "Alice works on P1 and P2" in a query before. Now you can. This tradeoff—gain queryability, create redundancy, then eliminate redundancy systematically—is the entire game of normalization.

**Try this yourself — predict the anomaly:** Before we introduce 2NF, look at the "After" table and write down every functional dependency you can see. In particular, what determines `Name`? Is that determinant a superkey? If not, what concrete problem will this cause when Alice gets married and changes her surname? Write your prediction. We'll verify it when we reach 2NF.

### 2.4 Common Misconception

"1NF means no duplicate rows." That is false. 1NF concerns the atomicity of attribute values, not uniqueness of tuples. Uniqueness is guaranteed by keys, not by 1NF.

> **Quick Check 2:** Is a table with a JSON blob in a text column in 1NF?
>
> *(Answer: Technically the column holds a single string, so the relational model may consider it atomic. But the values inside are not accessible to standard relational operators without parsing—this is a design smell, not a 1NF violation per se.)*

### 2.5 Practical Application Across Industries

The 1NF violation pattern—storing multiple values in a single column—appears across domains, each with distinct operational consequences. The following examples illustrate not merely the mechanical transformation to 1NF, but the concrete business processes that break under denormalized designs and the specific operational gains achieved through normalization.

**Healthcare: Patient Allergies and Clinical Decision Support.** A hospital's electronic health record system stores patient allergies in a `PATIENT` table as a comma-separated string: `PatientID=501, Allergies="penicillin,sulfa,latex"`. When a physician in the emergency department orders ceftriaxone (a cephalosporin antibiotic with cross-reactivity risk in penicillin-allergic patients), the clinical decision support system must check whether the patient has a penicillin allergy. The query `WHERE Allergies LIKE '%penicillin%'` performs a full table scan on every medication order — in a hospital processing 50,000 orders daily, this becomes a critical latency bottleneck. Worse, the substring match produces false negatives for misspellings ("pencillin") and false positives for substring coincidences. After 1NF decomposition into `PATIENT_ALLERGY(PatientID, AllergyCode, Severity, RecordedDate, RecordedBy)`, the system performs an indexed equality lookup `WHERE AllergyCode = 'J01.1'` (the ICD-10 code for penicillin allergy), returning in microseconds. Each allergy record now carries metadata — severity (mild anaphylaxis vs. fatal), recording date, and recording clinician — enabling differential alerting (warning for mild rash vs. hard stop for anaphylaxis history). The hospital's pharmacy and therapeutics committee can now audit allergy documentation completeness per clinician, a quality metric impossible to extract from the packed representation.

**E-commerce: Product Tags and Faceted Search.** A `PRODUCT` table stores tags as a JSON array: `ProductID=882, Tags=["wireless","noise-cancelling","bluetooth"]`. The faceted search engine must compute, for each category page, the count of products matching each tag to populate the "narrow by feature" sidebar. With the array storage, the query `WHERE JSON_CONTAINS(Tags, '"bluetooth"')` cannot use a standard B-tree index; the database must parse the JSON for every row in the category, decompressing and scanning — on a catalog of 2 million products, this runs in tens of seconds, unacceptable for interactive browsing. After 1NF normalization into `PRODUCT_TAG(ProductID, TagID)` with a foreign key to a `TAG` master table, the faceted count query becomes `SELECT TagID, COUNT(*) FROM PRODUCT_TAG WHERE ProductID IN (category_product_list) GROUP BY TagID`, exploiting a composite index on `(ProductID, TagID)` to return in milliseconds. The `TAG` master table enforces referential integrity — tag "bluetooh" is rejected at insert time with a foreign key violation, rather than silently proliferating across products and requiring a batch correction script that scans the entire table. The marketing team can now maintain a tag taxonomy with hierarchical relationships (parent tag "audio features" with children "noise-cancelling" and "spatial audio"), enabling drill-down navigation that was impossible when tags were opaque strings embedded in JSON.

**Finance: Multi-Leg Trade Processing and Exposure Aggregation.** An investment bank's `TRADE` table records swap transactions with multiple legs: `TradeID=T901, Counterparty=CS, TradeDate=2024-03-15, Legs="Equity:Bond:FX"`. The middle office risk team must compute, at 4 PM daily, the bank's aggregate notional exposure per leg type across all trading desks to monitor against regulatory limits. The delimited string requires `STRING_SPLIT` or equivalent table-valued functions that materialize the legs at query time — for 500,000 trades with an average of 3 legs each, this generates 1.5 million rows in a temporary structure, then performs the aggregation. The query takes 12 minutes, pushing the risk report past the regulatory submission deadline. After 1NF decomposition into `TRADE_LEG(TradeID, LegSequence, LegType, NotionalAmount, Currency, SettlementDate, FixedRate, FloatingRateIndex)`, the exposure aggregation becomes a direct `GROUP BY LegType` on a pre-indexed table, completing in under 10 seconds. Each leg now carries its own financial attributes: a cross-currency swap's EUR leg has a different notional and settlement date than its USD leg, information that was impossible to model in the packed representation without creating additional delimited columns (e.g., `LegNotionals="10M:8.5M:5M"` with implicit positional correspondence to `Legs`). The operations team can now schedule settlement instructions per leg — the EUR leg settles via CLS, the bond leg via Euroclear, the FX leg via continuous linked settlement — each with its own settlement date, a process that the denormalized design forced into manual reconciliation spreadsheets maintained outside the database entirely.

**Insurance: Policy Coverage Decomposition and Reinsurance Treaty Calculation.** A property and casualty insurer's `POLICY` table stores coverage types as a pipe-delimited string: `PolicyID=3141, Coverages="Liability|Collision|Comprehensive|UninsuredMotorist"`. The actuarial department must calculate, quarterly, the aggregate exposure per coverage type across all policies in hurricane-prone ZIP codes to determine the appropriate excess-of-loss reinsurance attachment point. The delimited format forces a query that splits the string for every policy row, then joins against a ZIP code table, then aggregates — for a book of 3 million policies, this query runs for over an hour and is scheduled as an overnight batch job, meaning the Chief Risk Officer sees exposure estimates that are 24 hours stale. After 1NF decomposition into `POLICY_COVERAGE(PolicyID, CoverageType, CoverageLimit, Deductible, PremiumComponent)`, the exposure calculation becomes a standard `GROUP BY CoverageType` with a `WHERE` clause filtering by geographic region, completing in under 30 seconds and enabling intraday what-if analysis. Each coverage now carries its own financial attributes: the liability coverage has a $500,000 limit with a $1,000 deductible, while the collision coverage has a $50,000 limit with a $500 deductible, and each contributes a separately calculated premium component. The underwriting team can now perform coverage-level profitability analysis — the comprehensive coverage in Florida policies has a 140% loss ratio, driving a rate increase, while the same coverage in Midwest policies has a 65% loss ratio — an analysis impossible when coverage types were undifferentiated elements in a delimited string. Reinsurance treaty negotiation now uses precise, coverage-level exposure data rather than broad-stroke estimates derived from sampling the denormalized table.

**Telecommunications: Call Detail Records and Convergent Billing.** A mobile network operator's `CALL_RECORD` table stores supplementary services invoked during a call: `CallID=9981, CallingParty=+15551234, CalledParty=+15559876, Services="CallWaiting,ThreeWayCalling,CallForwarding"`. The billing system must rate each service invocation separately against the subscriber's tariff plan — call waiting is $0.00, three-way calling is $0.25 per invocation, and call forwarding is $0.10 per minute to the forwarded destination. The packed representation makes per-service rating impossible without parsing the `Services` string, extracting each service code, and looking up its rate in the `SERVICE_CATALOG` table — a process that must be implemented in application code rather than declarative SQL, adding complexity and fragility to the billing pipeline that processes 200 million call records daily. After 1NF decomposition into `CALL_SERVICE(CallID, ServiceCode, InvocationTimestamp, DurationSeconds, ForwardedToNumber)`, each service invocation is an independent row that can be joined directly against `SERVICE_CATALOG` for rate lookup. The billing system now correctly handles complex scenarios: a call that starts as a two-party call, invokes three-way calling at $t = 30\text{s}$, then the original called party drops off at $t = 120\text{s}$ while the third party remains — the three-way calling charge applies only from $t = 30\text{s}$ to $t = 120\text{s}$, and the subsequent two-party segment is rated at the standard rate. Network operations can now analyze service usage patterns: call forwarding invocations peak at 5 PM on weekdays as subscribers forward office phones to mobile numbers, informing capacity planning for the call forwarding application server. The fraud detection system can flag anomalous patterns — a subscriber who invokes call forwarding to a premium-rate number in a foreign country 50 times in an hour — by joining `CALL_SERVICE` against a watchlist of high-risk destination numbers, a cross-reference impossible in the denormalized design.

**Manufacturing: Bill of Materials with Alternate Components and Supply Chain Resilience.** An aerospace manufacturer's `ASSEMBLY` table stores alternate part numbers for components: `AssemblyID=445, ComponentID=C17, PrimaryPart=P738, AlternateParts=["P738A","P738B","P738C"]`. When the primary part P738 is out of stock at the assembly plant's warehouse, the procurement system must find an