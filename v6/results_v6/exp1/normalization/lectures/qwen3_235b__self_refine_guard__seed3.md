**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Define** each normal form (1NF–BCNF) using precise, testable criteria.  
2. **Explain** how functional and multivalued dependencies introduce redundancy and update, insertion, and deletion anomalies.  
3. **Apply** normalization rules to decompose a schema into BCNF or 4NF, step by step.  
4. **Analyze** a given schema for violations of 2NF, 3NF, and BCNF by identifying partial, transitive, and non-superkey dependencies.  
5. **Evaluate** when to denormalize for performance while managing the risks of inconsistency.

---

### Prerequisites: Functional Dependencies and Keys

Imagine a database that thinks your phone number is part of your name. That’s what happens without clear functional dependencies: data gets tangled, logic breaks, and queries return nonsense.  

A **functional dependency (FD)** $X \rightarrow Y$ holds in a relation if, for any two tuples, equality on all attributes in $X$ implies equality on all attributes in $Y$. Think of it like a mathematical function: same input, same output. For example, $\text{StudentID} \rightarrow \text{Email}$ means each student has exactly one email—no ambiguity.

A **candidate key** is a minimal set of attributes that functionally determines all other attributes in the relation. It’s the smallest “fingerprint” that uniquely identifies a row. A **superkey** is any superset of a candidate key. A **prime attribute** is an attribute that is part of *any* candidate key.

> ✅ **Try This Yourself: Identify the Key**  
> Given the relation `Enroll(StudentID, Course, Grade)` and the FD $\text{StudentID, Course} \rightarrow \text{Grade}$, which of the following is a candidate key?  
> A) `StudentID`  
> B) `Course`  
> C) `(StudentID, Course)`  
> D) `Grade`  
>  
> *(Answer: C — only the combination uniquely identifies a row.)*

Now, suppose we add $\text{Course} \rightarrow \text{Instructor}$. Does this change the candidate key? What if two instructors teach the same course? Pause and rethink.

---

### 1. First Normal Form (1NF): Atomic Values Only

**Motivation: The Spreadsheet Trap**  
You’ve seen it: a CSV with “tags” in one cell, separated by commas. It works—until you need to find all products tagged “fast” but not “wireless.” Suddenly, you’re parsing strings in SQL, and performance tanks. This is the cost of violating 1NF.

1NF forces us to treat data like atoms: indivisible units for the task at hand.

**Definition**  
A relation is in **1NF** if:  
- Each attribute value is atomic (cannot be further subdivided for the intended use),  
- There are no repeating groups (e.g., `Phone1`, `Phone2`),  
- Each cell contains exactly one value from the attribute’s domain.

> 🔍 **Atomicity Is Contextual**  
> Is `FullName` atomic? If you only display it, yes. If you query by last name, no—it’s a compound value masquerading as one. Like storing latitude and longitude in a single field: fine for display, broken for search.

**Analogy: Postal Address as a Composite Type**  
Think of a mailing address. You might store it as a single string, but that makes sorting by city impossible. 1NF says: break it into `Street`, `City`, `Zip`. Not because it’s “nicer,” but because the system must *reason* about parts independently.

**Example: Fixing Non-Atomic Tags**  
Initial schema:  
`ProductTag(ProductID, Tags)` with `Tags = "wireless, charger, fast"`

This violates 1NF because `Tags` is a list.

**Decomposition Steps**:  
1. Split the multivalued `Tags` into individual rows.  
2. Define a new relation: `ProductTag(ProductID, Tag)`.  
3. Enforce uniqueness with a composite key: $\text{ProductID, Tag}$.

Resulting relation:  

| ProductID | Tag     |
|-----------|---------|
| P1        | wireless|
| P1        | charger |
| P1        | fast    |

**Benefits**:  
- Enables indexing on `Tag` for fast filtering.  
- Supports referential integrity via a `ValidTags(Tag)` table.  
- Allows reliable queries: `WHERE Tag = 'fast'`.

> 🚫 **Misconception Alert**  
> “Using arrays or JSON in PostgreSQL satisfies 1NF.”  
> **Correction**: If the application logic treats the array as a collection (e.g., querying with `ANY(Tags)`), the data is *logically* non-atomic. True 1NF compliance requires decomposition into separate rows.

> ✅ **Try This Yourself: 1NF**  
> Is `Student(StudentID, Name, PhoneNumbers[])` in 1NF if individual numbers are queried?  
> A) Yes  
> B) No  
>  
> *(Answer: B — querying inside the array violates atomicity.)*

> 💡 **Cross-Domain Insight: NoSQL and the 1NF Trade-Off**  
> MongoDB stores arrays natively. But when you index `tags`, it creates an index entry per value—effectively *simulating* 1NF decomposition. The system does the work you’d do manually in SQL. The principle survives the paradigm.

---

### 2. Second Normal Form (2NF): Eliminate Partial Dependencies

**Motivation: The Inventory Paradox**  
Imagine a warehouse where every time you record a new shipment, you re-enter the supplier’s address. Same address, over and over. One typo, and now two suppliers exist. This isn’t just inefficient—it’s dangerous.

This happens when a non-key attribute depends on only *part* of a composite key.

**Prerequisite**  
2NF applies only when a relation has a composite candidate key. If all candidate keys are single-attribute, the relation is automatically in 2NF.

**Definition**  
A relation is in **2NF** if:  
- It is in 1NF, and  
- Every non-prime attribute is **fully functionally dependent** on every candidate key.

That is, no non-prime attribute depends on a proper subset of any candidate key.

**Analogy: Chemical Compounds and Elements**  
Think of a composite key as a molecule. If an attribute depends only on one atom in that molecule, it doesn’t belong in the compound. $\text{Supplier} \rightarrow \text{SupplierAddr}$? That’s a fact about the supplier alone—pull it into its own “element” table.

**Example: Fixing Partial Dependency**  
Schema: `Order(Item, Supplier, Qty, SupplierAddr)`  
- Candidate key: $(\text{Item}, \text{Supplier})$  
- FD: $\text{Supplier} \rightarrow \text{SupplierAddr}$  
- $\text{SupplierAddr}$ is non-prime and depends only on $\text{Supplier}$ → **violates 2NF**

**Decomposition Steps**:  
1. Identify the partial dependency: $\text{Supplier} \rightarrow \text{SupplierAddr}$.  
2. Decompose into:  
   - `Order(Item, Supplier, Qty)` — all attributes depend on the full key  
   - `Supplier(Supplier, SupplierAddr)` — $\text{Supplier}$ is now a key  
3. Add referential integrity: Foreign key from `Order.Supplier` to `Supplier.Supplier`.

**Benefits**:  
- $\text{SupplierAddr}$ stored once.  
- Address updates occur in one place.  
- Deleting an order does not remove supplier data.

> 🚫 **Misconception Alert**  
> “Supplier name is a reliable key.”  
> **Correction**: Names are not unique. Use a surrogate key like `SupplierID` to ensure uniqueness.

> ✅ **Try This Yourself: 2NF**  
> In `Enroll(Student, Course, Instructor, Room)` with key $(\text{Student}, \text{Course})$ and FD $\text{Course} \rightarrow \text{Room}$, which attribute causes a 2NF violation?  
> A) `Instructor`  
> B) `Room`  
> C) `Student`  
> D) None  
>  
> *(Answer: B — $\text{Room}$ depends only on $\text{Course}$, a subset of the key.)*

> 💡 **Practical Insight**  
> Walmart separates supplier metadata from transactional data, ensuring consistency across high-volume operations.

---

### 3. Third Normal Form (3NF): Eliminate Transitive Dependencies

**Motivation: The Domino Effect**  
You update a department name, and suddenly dozens of student records need changing. Why? Because the department is stored not as a fact about the department, but as a side effect of an advisor’s assignment. One change ripples through the system.

This is a **transitive dependency**: $\text{Key} \rightarrow A \rightarrow B$, where $B$ is non-prime.

**Definition**  
A relation is in **3NF** if:  
- It is in 2NF, and  
- For every non-trivial FD $X \rightarrow Y$:  
  - $X$ is a superkey, or  
  - $Y$ is a prime attribute.

This blocks chains of dependencies that aren’t anchored to keys.

**Analogy: Organizational Reporting Lines**  
In a company, if Employee → Manager → Department, then changing a manager’s department should *not* change every employee’s department. That’s a policy error. 3NF enforces that only direct, key-based facts are stored.

**Example: Fixing Transitive Dependency**  
Schema: `Student(ID, Advisor, Dept)`  
- Key: $\text{ID}$  
- FDs: $\text{ID} \rightarrow \text{Advisor}$, $\text{Advisor} \rightarrow \text{Dept}$  
- $\text{Dept}$ is non-prime, and $\text{Advisor}$ is not a superkey → **violates 3NF**

**Decomposition Steps**:  
1. Identify the transitive dependency: $\text{Advisor} \rightarrow \text{Dept}$.  
2. Decompose into:  
   - `StudentAdvisor(ID, Advisor)`  
   - `AdvisorDept(Advisor, Dept)`  
3. Add foreign key: `StudentAdvisor.Advisor` references `AdvisorDept.Advisor`.

**Benefits**:  
- Department data persists even if no student has that advisor.  
- Department updates are centralized.  
- No deletion anomaly.

> 🔍 **Why Prime Attributes Are Exempt**  
> 3NF allows $X \rightarrow Y$ when $Y$ is prime because prime attributes are tied to keys, limiting redundancy. For example, if `Advisor` is part of a key in another relation, storing it redundantly is less risky.

> 🚫 **Misconception Alert**  
> “3NF eliminates all redundancy.”  
> **Correction**: 3NF permits redundancy when the determinant is prime but not a superkey. BCNF eliminates this case.

> ✅ **Try This Yourself: 3NF**  
> In `Employee(EmpID, Dept, Manager)` with $\text{EmpID} \rightarrow \text{Dept}$, $\text{Dept} \rightarrow \text{Manager}$, and $\text{Manager}$ non-prime, does this violate 3NF?  
> A) Yes  
> B) No  
>  
> *(Answer: A — $\text{Dept} \rightarrow \text{Manager}$ with $\text{Dept}$ not a superkey and $\text{Manager}$ non-prime.)*

> 💡 **Cross-Domain Insight: Graph Databases and 3NF**  
> In Neo4j, you’d model `Advisor` → `Dept` as a direct relationship. The transitive path `Student` → `Advisor` → `Dept` is computed on read. 3NF forces this same separation in relational design—normalization as *schema-level path control*.

---

### 4. Boyce-Codd Normal Form (BCNF): Every Determinant Is a Superkey

**Motivation: The Hidden Key Problem**  
Suppose two courses have the same instructor, and two instructors teach the same course. You might think “Course → Instructor” is safe. But if Instructor → Course also holds, you’ve created a cycle where neither is a key. Now, adding a new course requires knowing the instructor—and vice versa.

BCNF breaks this circular dependency by insisting: **if X determines Y, X must be a superkey**.

**Definition**  
A relation is in **BCNF** if, for every non-trivial FD $X \rightarrow Y$, $X$ is a superkey.

BCNF is strictly stronger than 3NF: every BCNF schema is in 3NF, but not vice versa.

**Analogy: Two-Way Streets and Traffic Rules**  
In 3NF, one-way streets are allowed. In BCNF, every street that carries traffic (i.e., determines another attribute) must start from a major hub (a superkey). If a side road tries to control traffic, it’s not allowed—redirect it to the highway.

**Example: Decomposing to BCNF**  
Schema: `Enroll(Student, Course, Instructor)`  
- FDs: $\text{Course} \rightarrow \text{Instructor}$, $\text{Instructor} \rightarrow \text{Course}$  
- Candidate keys: $(\text{Student}, \text{Course})$, $(\text{Student}, \text{Instructor})$

Check FDs:  
- $\text{Course} \rightarrow \text{Instructor}$: $\text{Course}$ is not a superkey → **violates BCNF**  
- $\text{Instructor} \rightarrow \text{Course}$: $\text{Instructor}$ is not a superkey → also violates

**Decomposition Steps**:  
1. Use $\text{Course} \rightarrow \text{Instructor}$ to decompose:  
   - `CourseInstructor(Course, Instructor)` — now $\text{Course}$ is a key  
   - `Enrollment(Student, Course)` — key is $(\text{Student}, \text{Course})$  
2. Verify BCNF:  
   - In `CourseInstructor`, both FDs have superkeys as determinants.  
   - In `Enrollment`, only trivial FDs exist.  
3. **Lossless join**: Yes — natural join on `Course` reconstructs the original.  
4. **Dependency preservation**: Yes — both FDs are represented in the new schema.

> ⚠️ **Trade-off: Dependency Preservation**  
> BCNF does **not** guarantee that all FDs are preserved. Some decompositions require application-level constraints or triggers to enforce lost dependencies.

> 🚫 **Misconception Alert**  
> “BCNF always preserves functional dependencies.”  
> **Correction**: It often does not. Designers must verify and enforce dependencies externally when needed.

> ✅ **Try This Yourself: BCNF**  
> Given $R(A,B,C)$ with FDs $A \rightarrow B$, $B \rightarrow C$, and key $A$, is this in BCNF?  
> A) Yes  
> B) No  
>  
> *(Answer: B — $B \rightarrow C$ but $B$ is not a superkey.)*

> 💡 **Practical Insight**  
> Stanford stores course-instructor assignments in a separate table, supporting team teaching and clean updates.

---

### 5. Fourth Normal Form (4NF): Eliminate Independent Multivalued Dependencies

**Motivation: The Cartesian Catastrophe**  
You add one textbook to a course. Suddenly, the number of rows doubles because it pairs with every instructor. This isn’t a bug—it’s a design flaw from treating independent facts as a single table.

4NF targets **independent multivalued dependencies**: when two sets of values vary independently of each other.

**Definition**  
A relation is in **4NF** if, for every non-trivial multivalued dependency (MVD) $X \twoheadrightarrow Y$, $X$ is a superkey.

An MVD $X \twoheadrightarrow Y$ means that for a fixed $X$, the set of $Y$ values is independent of other attributes.

**Analogy: Independent Dimensions in a Cube**  
Think of a data cube: time, product, region. Each dimension varies independently. Storing all combinations in one table is wasteful. 4NF says: store dimensions separately, join on demand. It’s normalization for combinatorial data.

**Example: Fixing Combinatorial Redundancy**  
Schema: `Course(CourseID, Textbook, Instructor)`  
- MVDs: $\text{CourseID} \twoheadrightarrow \text{Textbook}$, $\text{CourseID} \twoheadrightarrow \text{Instructor}$  
- No FD between `Textbook` and `Instructor` → values are independent

Sample data: 2 textbooks × 2 instructors = 4 rows. Adding one textbook doubles the count.

**Decomposition Steps**:  
1. Recognize the independent MVDs.  
2. Decompose into:  
   - `CourseText(CourseID, Textbook)`  
   - `CourseInst(CourseID, Instructor)`  
3. Reconstruct via join when needed.

**Benefits**:  
- Adding a textbook or instructor requires only one new row.  
- No redundant combinations.  
- Updates are localized.

> 🔍 **When Is an MVD Not Independent?**  
> If $\text{Textbook} \rightarrow \text{Instructor}$ (e.g., the author teaches the course), the values are dependent, and 4NF does not require decomposition.

> 🚫 **Misconception Alert**  
> “4NF is about repeating values.”  
> **Correction**: It is about **independence** of multivalued facts. If one determines the other, 4NF may not apply.

> ✅ **Try This Yourself: 4NF**  
> In `Movie(Title, Actor, Genre)` with independent actors and genres per movie, which normal form is violated?  
> A) 2NF  
> B) 3NF  
> C) 4NF  
>  
> *(Answer: C — independent MVDs from $\text{Title}$.)*

> 💡 **Cross-Domain Insight: NoSQL and 4NF**  
> In Firestore, you’d store `actors` and `genres` as separate arrays in a document. But if they’re independent, updating one risks inconsistency with the other. 4NF’s lesson transcends models: **independent facts belong in independent structures**.

---

### 6. Fifth Normal Form (5NF): Eliminate Join Dependencies

**Motivation: The Missing Triple**  
Suppose a supplier supplies a part, and that part is used in a project, and the supplier works on that project. Does it follow that the supplier supplies the part to that project? Only if business rules say so. If yes, your schema must *enforce* that the triple exists—5NF ensures this.

**Definition**  
A relation is in **5NF** (Project-Join Normal Form) if every non-trivial join dependency $\bowtie(R_1, R_2, \dots, R_k)$ is implied by the candidate keys.

**Analogy: Chemical Reaction Constraints**  
In chemistry, just because you have hydrogen, oxygen, and heat doesn’t mean water forms—conditions matter. Similarly, just because pairs $(S,P)$, $(P,J)$, $(S,J)$ exist doesn’t mean $(S,P,J)$ should. 5NF encodes the “reaction conditions” in the schema.

**Example: Supplier–Part–Project Rule**  
Schema: `SPJ(Supplier, Part, Project)`  
Rule: If supplier $S$ supplies part $P$, part $P$ is used in project $J$, and supplier $S$ works on project $J$, then $S$ must supply $P$ to $J$.  
This implies: $SPJ = SP \bowtie PJ \bowtie SJ$

Current data:  

| S  | P  | J  |
|----|----|----|
| S1 | P1 | J1 |
| S1 | P1 | J2 |
| S1 | P2 | J1 |
| S2 | P1 | J1 |

Is $(S1, P2, J2)$ required? Only if $(S1,P2)$, $(P2,J2)$, and $(S1,J2)$ all exist. $(P2,J2)$ is missing → no requirement.

**Decomposition into 5NF**:  
1. `SP(Supplier, Part)`  
2. `PJ(Part, Project)`  
3. `SJ(Supplier, Project)`  

Reconstruction:  
$$
SPJ