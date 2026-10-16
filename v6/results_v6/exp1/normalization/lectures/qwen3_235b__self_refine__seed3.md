**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. *Remember* the defining criteria for 1NF, 2NF, 3NF, and BCNF by classifying schema violations using atomicity, functional dependencies, and key relationships.  
2. *Understand* the practical motivation for each normal form by identifying insertion, deletion, and update anomalies in unnormalized tables.  
3. *Apply* normalization step by step to decompose a relation into 3NF or BCNF, justifying each step using attribute closures, keys, and functional dependencies.  
4. *Analyze* whether a decomposition is lossless and preserves functional dependencies using intersection and closure tests.  
5. *Evaluate* design trade-offs between normalization and performance, choosing appropriate levels based on application needs.

---

### Prerequisites: Tools for Reasoning About Data Dependencies

Normalization is not about tidying data — it's about encoding truth. To do that, we need precise tools to reason about **what must be true**, not just what happens to be true in a given dataset.

A **relation** $ R $ is a table with a fixed schema, where:
- Each cell contains a single atomic value.
- Rows represent unique instances of the entity.

A **functional dependency (FD)** $ X \rightarrow Y $ holds in $ R $ if, for any two tuples in $ R $, equality on all attributes in $ X $ implies equality on all attributes in $ Y $. This expresses a semantic constraint, not an observation of current data.

Think of an FD as a **data contract**: if two rows agree on $ X $, they *must* agree on $ Y $ — or the database violates a business rule.

The **attribute closure** $ X^+ $ under a set of FDs $ F $ is the set of all attributes functionally determined by $ X $, computed using Armstrong’s axioms:
- **Reflexivity**: If $ Y \subseteq X $, then $ X \rightarrow Y $.
- **Augmentation**: If $ X \rightarrow Y $, then $ XZ \rightarrow YZ $ for any $ Z $.
- **Transitivity**: If $ X \rightarrow Y $ and $ Y \rightarrow Z $, then $ X \rightarrow Z $.

A **candidate key** $ K $ is a minimal set of attributes such that $ K^+ = R $. Minimality means no proper subset of $ K $ has closure equal to $ R $.

An attribute is **prime** if it is part of any candidate key; otherwise, it is **non-prime**.

> 💡 **Misconception Alert**:  
> “Functional dependencies describe how data appears.”  
> No. An FD represents a business rule. For example, $ \text{StudentID} \rightarrow \text{GPA} $ means each student has exactly one GPA — a semantic constraint, not a pattern in observed values.

> 🔁 **Quick Check: Prerequisites**  
> Given $ R(A,B,C) $ with FDs: $ A \rightarrow B $, $ B \rightarrow C $.  
> Is $ A $ a candidate key? Is $ B $ a prime attribute?

> > ✅ Yes, $ A $ is a candidate key.  
> > Compute $ A^+ $:  
> > - Start: $ A^+ = \{A\} $  
> > - Apply $ A \rightarrow B $: $ A^+ = \{A,B\} $  
> > - Apply $ B \rightarrow C $: $ A^+ = \{A,B,C\} = R $  
> > Since $ A^+ = R $ and $ A $ is a singleton, it is minimal → candidate key.  
> >  
> > $ B $ is **not** a prime attribute.  
> > $ B^+ = \{B,C\} \neq R $, so $ B $ is not a candidate key. The only candidate key is $ A $; hence, $ B $ is not part of any key → non-prime.

Now, let’s confront a deeper question: why does any of this matter?

---

### Motivation: The Silent Crisis of Redundant Truth

Imagine a medical database where a patient’s blood type is recorded in **every appointment record**. No error is raised. The system works — until the patient’s blood type is corrected in one record but not others.

Queries return conflicting answers. Algorithms trained on this data learn nonsense. And no one notices — because the database never crashes.

This is not a software failure. It’s a **truth failure**.

Redundancy allows the same fact to be stored in multiple places. That creates a **consistency hazard**: updates may be partial, delayed, or forgotten.

Normalization is the discipline of **anchoring each fact to its rightful owner** — the entity that determines it.

> 🔑 **Key Insight**:  
> Normalization is not about efficiency. It’s about **truth governance** — ensuring every fact has one, and only one, source of truth.

Let’s see what happens when we get this wrong.

---

### 1. First Normal Form (1NF): The Atomicity Threshold

**Hook: The Playlist That Broke the Recommendation Engine**  
A music app stores playlists as:

| UserID | Songs                     |
|--------|---------------------------|
| U5     | "Bohemian Rhapsody, Imagine" |

The app works — until users demand: “Show me everyone who listens to *Imagine*.”  
The database cannot answer. It sees one string, not two songs.

This is like storing a grocery list in a sealed envelope: you can carry it, but you can’t inspect or act on its contents.

**Analogy: The ZIP Code Paradox**  
A ZIP code like “90210-1234” is a single string. But if your application needs to route mail by region, you must split it — because **atomicity is purpose-dependent**.

Just as a chemist breaks molecules into atoms, a database designer breaks values into **semantically indivisible units** — those that cannot or should not be further decomposed *for the application’s needs*.

**Formal Definition**  
A relation is in **1NF** if:
- All attribute values are **atomic** (indivisible for the intended use).
- There are no repeating groups (e.g., $ \text{Song1}, \text{Song2} $).
- Each tuple has exactly one value per attribute.

This is foundational: **the database can only enforce constraints on data it can access**.

**Worked Example: Authors Table**  
Original:

| BookID | Authors                  |
|--------|--------------------------|
| B7     | Asimov; Clarke; Heinlein |

To achieve 1NF:
1. Split multi-valued entries into separate rows.
2. Preserve $ \text{BookID} $ to maintain association.

Result:

| BookID | Author       |
|--------|--------------|
| B7     | Asimov       |
| B7     | Clarke       |
| B7     | Heinlein     |

Now:
- Query: Find all books by Clarke → `SELECT BookID FROM Authors WHERE Author = 'Clarke'`.
- Enforce uniqueness: Define primary key $ (\text{BookID}, \text{Author}) $.
- Maintain referential integrity: $ \text{BookID} \rightarrow \text{Books(BookID)} $.

> 💡 **Misconception Alert**:  
> “Atomic means ‘no commas’.”  
> No. Atomicity is context-dependent. “Isaac Asimov” is atomic *unless* you need to query by last name. Then it should be split into $ \text{FirstName}, \text{LastName} $.

> 🔁 **Test Yourself: 1NF**  
> You’re designing a blog. Posts have multiple tags: “AI”, “Ethics”, “Tech”.  
> Should you store tags as a comma-separated string in the $ \text{Posts} $ table?

> > ❌ No. You cannot:  
> > - Efficiently find all posts tagged “AI”.  
> > - Enforce valid tag names (e.g., block “A.I.”).  
> > - Count tag frequency.  
> > ✅ Normalize: create $ \text{PostTags(post\_id, tag)} $ with primary key $ (\text{post\_id}, \text{tag}) $.  
> > Now tags are queryable, indexable, and consistent.

Having ensured atomicity, we now eliminate redundancy due to partial dependencies.

---

### 2. Second Normal Form (2NF): Full Dependency on the Key

**Hook: The Invoice That Can’t Remember Its Supplier**  
Consider:

| ItemID | SupplierID | Quantity | SupplierAddr     |
|--------|------------|----------|------------------|
| SSD    | S1         | 5        | 123 Tech St      |

Key: $ (\text{ItemID}, \text{SupplierID}) $  
FD: $ \text{SupplierID} \rightarrow \text{SupplierAddr} $

Here, $ \text{SupplierAddr} $ depends only on $ \text{SupplierID} $, not the full key. This is a **partial dependency**.

Now ask: *Who owns the supplier’s address?*  
The supplier does — not the item-supplier pair.

Storing it here is like putting your landlord’s phone number in every grocery receipt from their building.

**Analogy: The Shared Recipe with a Hidden Ingredient**  
A recipe says: “Ingredients: flour, sugar, and [butter from Sarah’s kitchen].”  
But Sarah might move. Or change her butter brand.  
The dependency is indirect and fragile.

Likewise, if a non-prime attribute depends on part of a key, its truth is **decoupled from its owner**.

**Formal Definition**  
A relation is in **2NF** if:
- It is in 1NF, and
- Every **non-prime attribute** is **fully functionally dependent** on every candidate key.

That is, no non-prime attribute depends on a proper subset of any candidate key.

> ⚠️ **Note**: If every candidate key is single-attribute, 2NF is automatically satisfied.

**Worked Example: Flight Assignments**  
$ \text{Flight}(PilotID, PlaneID, PilotName) $  
- Candidate key: $ (PilotID, PlaneID) $
- FD: $ PilotID \rightarrow PilotName $
- $ PilotName $ is non-prime, depends only on $ PilotID $ → **violates 2NF**

**Anomalies**:
- Update: Change pilot name → update all flight records.
- Insert: Cannot add a pilot without assigning a plane.
- Delete: Remove last flight → lose pilot name.

**Fix**: Decompose by functional dependency.
1. $ \text{FlightAssignments}(PilotID, PlaneID) $
2. $ \text{Pilots}(PilotID, PilotName) $

Now, pilot data is stored once. Changes are localized.

> 💡 **Misconception Alert**:  
> “2NF eliminates all redundancy.”  
> No. It only removes redundancy from **partial dependencies**. Transitive dependencies (e.g., $ Dept \rightarrow Manager $) remain.

> 🔁 **Test Yourself: 2NF**  
> Table: $ \text{Enrollment}(StudentID, CourseID, CourseName) $  
> Key: $ (StudentID, CourseID) $  
> FD: $ CourseID \rightarrow CourseName $  
>  
> Is this in 2NF? What happens if the course name changes?

> > ❌ No. $ CourseName $ depends only on $ CourseID $, a subset of the key → partial dependency.  
> > Update anomaly: renaming “Intro to CS” requires updating every enrollment row.  
> > ✅ Fix: decompose into:  
> > - $ \text{Enrollments}(StudentID, CourseID) $  
> > - $ \text{Courses}(CourseID, CourseName) $

With partial dependencies resolved, we now address transitive ones.

---

### 3. Third Normal Form (3NF): No Transitive Dependencies on Non-Prime Attributes

**Hook: The Employee Who Outlived the Department**  
$ \text{Employee}(EmpID, Dept, Manager) $  
- $ EmpID \rightarrow Dept $
- $ Dept \rightarrow Manager $
→ So $ EmpID \rightarrow Manager $, but indirectly.

Now, the manager is tied to the employee. But if the last employee quits, the department’s manager vanishes.

This is like storing a company’s CEO in the last active employee’s profile.

**Analogy: The Library Book with a Borrower’s Opinion**  
You catalog: “Book: *1984* — Borrower: Alice — Genre: Dystopian — Alice’s Rating: 5 stars.”  
But Alice’s rating belongs to Alice, not the book. When she returns it, should the rating disappear?

No. Data must be stored with its **determiner** — the entity that fixes its value.

In 3NF, we ban transitive dependencies where a non-prime attribute is determined by a non-superkey.

**Formal Definition**  
A relation is in **3NF** if:
- It is in 2NF, and
- For every non-trivial FD $ X \rightarrow Y $:
  - $ X $ is a **superkey**, or
  - $ Y $ is a **prime attribute**.

This prevents a non-prime attribute from being determined by a non-superkey.

**Worked Example: Banking Customers**  
$ \text{Customer}(CustID, Branch, Manager) $  
- Key: $ CustID $
- FDs: $ CustID \rightarrow Branch $, $ Branch \rightarrow Manager $
- $ Branch \rightarrow Manager $: $ Branch $ is not a superkey, $ Manager $ is not prime → **violates 3NF**

**Decompose**:
1. $ \text{CustBranch}(CustID, Branch) $
2. $ \text{BranchMgr}(Branch, Manager) $

Now:
- Manager stored once per branch.
- Update: one row.
- Delete last customer? Manager data remains.

**Check**:
- Dependency preserved? Yes — $ Branch \rightarrow Manager $ is in $ \text{BranchMgr} $.
- Lossless join? Yes — join on $ Branch $ reconstructs original.

> 💡 **Misconception Alert**:  
> “3NF eliminates all redundancy.”  
> False. 3NF allows redundancy if the dependent attribute is **prime**. It only blocks transitive dependencies on **non-prime** attributes.

> 🔁 **Test Yourself: 3NF**  
> $ \text{Student}(StudentID, Major, Advisor) $  
> FDs: $ StudentID \rightarrow Major $, $ Major \rightarrow Advisor $  
> Key: $ StudentID $  
>  
> Is this in 3NF? Can you record that “CS → Dr. Lee” if no CS student exists?

> > ❌ No. $ Major \rightarrow Advisor $: $ Major $ is not a superkey, $ Advisor $ is not prime → violates 3NF.  
> > Insertion anomaly: cannot record advisor for a major with no students.  
> > ✅ Fix: decompose into:  
> > - $ \text{StudentMajor}(StudentID, Major) $  
> > - $ \text{MajorAdvisor}(Major, Advisor) $

Having eliminated transitive dependencies on non-prime attributes, we now consider a stricter condition.

---

### 4. Boyce-Codd Normal Form (BCNF): Every Determinant Is a Superkey

**Hook: The Course That Forgot Its Professor**  
$ \text{CourseInstructor}(Course, Instructor, TA) $  
- $ Course \rightarrow Instructor $
- $ Instructor \rightarrow Course $ → both are candidate keys
- $ Instructor \rightarrow TA $

Now, if Dr. Lee changes TAs, **every row with Dr. Lee must be updated**, even for different courses.

Yet 3NF **allows** this: $ Instructor $ is a **prime attribute** (part of a key), so $ Instructor \rightarrow TA $ satisfies 3NF.

But update anomalies persist.

This is like a two-way street where both ends claim ownership — but only one can assign the streetlight.

**Analogy: The Marriage Certificate with a Third Signature**  
A document says: “Married: Alice and Bob. Officiant: Rev. Smith.”  
But Rev. Smith also determines the marriage — and Rev. Smith can marry others.  
Now, if Rev. Smith retires, every marriage they officiated must be re-signed.

The determinant (Rev. Smith) is not the full key — but they determine an attribute. That’s unstable.

In BCNF, **every determinant must be a superkey** — only full keys may determine other attributes.

**Formal Definition**  
A relation is in **BCNF** if:
For every non-trivial FD $ X \rightarrow Y $,  
- $ X $ is a **superkey**.

There are no exceptions. If $ X $ determines any attribute, $ X $ must identify the entire tuple.

**Worked Example 1: Real Estate LOTS**  
$ \text{LOTS1A}(PropertyID, Area, County\_name, Price) $  
- FDs:  
  - $ PropertyID \rightarrow Area $  
  - $ Area \rightarrow County\_name $  
  - $ Area \rightarrow Price $  
- Key: $ PropertyID $

Check FDs:
- $ Area \rightarrow County\_name $: $ Area $ is not a superkey → **violates BCNF**

**Decompose using $ Area \rightarrow County\_name $**:
1. $ \text{LOTS1A1}(Area, County\_name) $
2. $ \text{LOTS1A2}(PropertyID, Area, Price) $

In $ \text{LOTS1A2} $: $ Area \rightarrow Price $, but $ Area $ is not a superkey → **still violates BCNF**

**Decompose again**:
1. $ \text{LOTS1A3}(Area, Price) $
2. $ \text{LOTS1A4}(PropertyID, Area) $

Now all relations are in BCNF.

But: $ PropertyID \rightarrow Price $ is **lost** — must be enforced externally.

**Worked Example 2: Academic Scheduling**  
$ \text{Enroll}(Student, Course, Instructor) $  
- FDs: $ Course \rightarrow Instructor $, $ Instructor \rightarrow Course $
- Candidate keys: $ (Student, Course) $, $ (Student, Instructor) $

Both FDs have non-superkey determinants → **violates BCNF**

**Decompose using $ Course \rightarrow Instructor $**:
1. $ \text{CourseInst}(Course, Instructor) $
2. $ \text{EnrollOnly}(Student, Course) $

Now:
- $ \text{CourseInst} $: $ Course $ is a key → BCNF
- $ \text{EnrollOnly} $: $ (Student, Course) $ is a key → BCNF
- $ Instructor \rightarrow Course $ is preserved via symmetry

**Dependency Preservation**: Yes  
**Lossless Join**: Yes — join on $ Course $

> 💡 **Misconception Alert**:  
> “BCNF is always better than 3NF.”  
> Not necessarily. BCNF may **lose functional dependencies** or require more joins. Use it when anomalies are unacceptable (e.g., finance, healthcare).

> 🔁 **Test Yourself: BCNF**  
> Given $ R(A,B,C) $ with FDs: $ A \rightarrow B $, $ B \rightarrow C $, key $ A $.  
> 1. Is it in 3NF?  
> 2. Is it in BCNF?  
> 3. Can you decompose into BCNF while preserving all FDs?

> > 1. ❌ Not in 3NF: $ B \rightarrow C $, $ B $ not superkey, $ C $ not prime → violates 3NF.  
> > 2. ❌ Not in BCNF: same reason — $ B $ not superkey.  
> > 3. Decompose:  
> >    - $ R1(A,B) $ with $ A \rightarrow B $, key $ A $ → BCNF  
> >    - $ R2(B,C) $ with $ B \rightarrow C $, key $ B $ → BCNF  
> >    Join on $ B $ is lossless.  
> >    But $ A \rightarrow C $ is **not preserved** — requires a join to enforce.  
> >    ✅ So: BCNF possible, but **dependency preservation not guaranteed**.

---

### Cross-Domain Insight: Normalization as a Law of Conservation of Fact

Here’s a framing rarely seen in textbooks: **normalization is the database analog of the conservation of mass**.

In physics, mass cannot be created or destroyed — only transformed.  
In databases, **facts** cannot be duplicated or erased —