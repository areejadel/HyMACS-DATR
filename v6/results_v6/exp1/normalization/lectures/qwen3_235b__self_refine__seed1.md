By the end of this lecture, you will be able to:  
1. **Recall** the definitions and requirements of 1NF, 2NF, 3NF, and BCNF by identifying atomic values, partial dependencies, transitive dependencies, and superkey conditions in a given schema.  
2. **Explain** how insertion, update, and deletion anomalies arise due to poor schema design using real-world examples.  
3. **Apply** a step-by-step decomposition process to convert a relation into higher normal forms (up to BCNF), ensuring lossless join and checking for dependency preservation.  
4. **Analyze** a database schema to determine its highest normal form and justify whether further normalization is needed.  
5. **Evaluate** the trade-offs between normalization and denormalization in terms of data integrity, query performance, and maintenance complexity in practical scenarios.

---

### Prerequisites

To follow this lecture, you must understand the following foundational concepts.

A **relation** $R$ is a table with rows (tuples) and columns (attributes), where each attribute takes values from a specified domain.  
A **functional dependency (FD)** $X \rightarrow Y$ holds in $R$ if, for any two tuples, equal values on $X$ imply equal values on $Y$. That is, $X$ functionally determines $Y$.  
A **candidate key** is a minimal set of attributes that functionally determines all other attributes in $R$. No proper subset of a candidate key is also a superkey.  
A **prime attribute** is an attribute that is part of *at least one* candidate key. All other attributes are **non-prime**.  
A **superkey** is any set of attributes that functionally determines all attributes in $R$. A candidate key is a minimal superkey.

> 🔍 **Quick Check**: In the relation *Enrollment*(StudentID, CourseID, Grade), suppose $(StudentID, CourseID)$ is the only candidate key.  
> - Which attributes are prime?  
> - Is *Grade* a prime attribute?  
>  
> *Answer: StudentID and CourseID are prime. Grade is non-prime.*

Having established these definitions, we now turn to the motivation for normalization.

---

### Motivation: The Cost of Redundancy — A Real-World Scenario

Imagine you’re analyzing a city’s public health data and discover something alarming: reported cases of measles have dropped 90% in one district. You celebrate—until you learn no vaccination campaign occurred. Curious, you dig deeper. The decline coincides with a clerical change: nurses at one clinic started abbreviating “Measles, Mumps, Rubella” as “MMR” instead of listing “Measles” individually.

The disease didn’t vanish. It was **erased by schema design**.

This isn’t a flaw in data entry. It’s a flaw in structure. The system stored diagnoses as a single text field, and queries filtered on exact matches. “Measles” disappeared not because it was cured, but because it was **encoded inconsistently**.

Now consider a hospital table:

| PatientID | Name     | Diagnosis           | Doctor       | DoctorPhone     |
|----------|----------|---------------------|--------------|-----------------|
| P001     | Alice    | Hypertension        | Dr. Lee      | 555-0123        |
| P001     | Alice    | Diabetes            | Dr. Lee      | 555-0123        |
| P002     | Bob      | Asthma              | Dr. Kim      | 555-0456        |

This schema hides a deeper problem: every time Dr. Lee’s phone number appears, it risks drifting out of sync. You can’t fix this with better training. You need a **different schema**.

> 🧩 **Analogy (Circuit Board Design)**: In electronics, placing the same resistor in ten parallel circuits works—but if one fails, the system behaves unpredictably. Better to use a single, shared power source. Similarly, normalization ensures each fact—like a doctor’s phone number—is sourced from one place.

> 🔥 **Tension**: How can a database guarantee consistency when the same fact is repeated across rows?  
> The answer isn’t discipline. It’s **design**.

This table conflates **three independent facts**:
1. A patient’s diagnosis,
2. Which doctor treats a patient,
3. A doctor’s contact information.

Normalization separates these concerns, ensuring **each fact is stored once, with a clear owner**.

> 🧠 **Try This Yourself**: Sketch two alternative tables that would eliminate the repetition of Dr. Lee’s phone number. What keys would each have? What functional dependencies would they enforce?

---

### 1. First Normal Form (1NF): Enforce Atomic Values

#### Intuition: Can the Database Access Individual Values?

Suppose a student’s courses are stored as `"CS101, CS202"`.  
Can you reliably query for students taking CS101?  
- `WHERE Courses = 'CS101'` → fails.  
- `LIKE '%CS101%'` → may match `"CS1010"`.

The database **cannot reason** about components of a non-atomic value. This limits query correctness and constraint enforcement.

**First Normal Form (1NF)** requires that every attribute value be **atomic**—indivisible and accessible as a single unit.

#### Definition

A relation $R$ is in **1NF** if:
1. All attribute values are atomic (no sets, lists, or composite values).
2. There are no repeating groups (e.g., Course1, Course2, Course3).

Atomicity enables indexing, constraint enforcement, and reliable querying.

> 📌 **Why it matters**: Without atomicity, you cannot enforce domain constraints or write precise queries.

#### Worked Example: Fixing a Non-Atomic Field

**Unnormalized Table** (*StudentCourses*):

| StudentID | Courses               |
|-----------|------------------------|
| S01       | CS101, CS202           |
| S02       | CS101                  |

The *Courses* column contains comma-separated values → violates 1NF.

**Step 1: Split into atomic values**  
Create one row per course:

| StudentID | Course  |
|-----------|--------|
| S01       | CS101  |
| S01       | CS202  |
| S02       | CS101  |

Each cell contains a single course → satisfies 1NF.

**Step 2: Test with a query**  
```sql
SELECT StudentID FROM StudentCourses WHERE Course = 'CS101';
```
Now correctly returns S01 and S02.

> ✅ **Another Worked Example (Healthcare)**:  
A lab stores test results as:  
| PatientID | Tests                     |  
|----------|----------------------------|  
| P001     | CBC, Lipid Panel, Urinalysis |  

Fix: Create *TestResults*(PatientID, Test) with rows:  
- (P001, CBC)  
- (P001, Lipid Panel)  
- (P001, Urinalysis)  

Now individual tests can be counted, indexed, and constrained.

> ⚠️ **Common Misconception**:  
“1NF requires no duplicate rows.”  
**Correction**: 1NF does **not** require row uniqueness. Duplicates are allowed—but should be prevented using keys. The core requirement is **atomicity**, not uniqueness.

> 🧩 **Analogy (Molecular Chemistry)**: A compound like H₂O can’t be used in a reaction unless its atoms are accessible. A non-atomic field is like storing “H₂O” as a single unbreakable unit—you can’t use just the oxygen. 1NF ensures every “atom” of data is individually addressable.

> 💡 **Quick Check**:  
In a JSON-enabled database, storing `{"skills": ["Java", "SQL"]}` in one field—does this satisfy 1NF?  
*Answer: No. The attribute contains a set, which violates atomicity. While NoSQL systems permit this, it breaks 1NF and limits declarative querying.*

Having ensured atomicity, we now eliminate partial dependencies.

---

### 2. Second Normal Form (2NF): Eliminate Partial Dependencies

#### Intuition: Does an Attribute Depend on Only Part of the Key?

Consider a delivery tracking table:

| DriverID | RouteID | DriverName | Miles |  
|---------|--------|------------|-------|  
| D01     | R01    | Alice      | 120   |  
| D01     | R02    | Alice      | 95    |

The candidate key is $(DriverID, RouteID)$. However, *DriverName* depends only on *DriverID*—not the full key. This is a **partial dependency**.

Storing *DriverName* in every route row is inefficient. The fact belongs to the driver, not the route.

> 🔥 **Tension**: Why should changing Alice’s name require updating every route she has driven?

This inefficiency stems from a partial dependency.

> 🧩 **Analogy (Genetic Inheritance)**: A child inherits genes from both parents, but eye color depends only on the mother’s contribution. If the child’s record stored the mother’s name redundantly, changing her name would require updating every child’s record. 2NF ensures attributes depend on the *whole* key, not just a genetic fragment.

#### Definition

A relation $R$ is in **2NF** if:
1. $R$ is in 1NF, **and**
2. Every **non-prime attribute** is **fully functionally dependent** on every candidate key.

That is, no non-prime attribute depends on a proper subset of any candidate key.

#### Worked Example: Decomposing to 2NF

**Table**: *Delivery*(DriverID, RouteID, DriverName, Miles)  
- FD: $DriverID \rightarrow DriverName$ → partial dependency

**Step 1: Identify the partial dependency**  
$DriverID \rightarrow DriverName$

**Step 2: Decompose**  
- **Driver**(DriverID, DriverName), key: $DriverID$  
- **RouteMileage**(DriverID, RouteID, Miles), key: $(DriverID, RouteID)$

Now:
- *DriverName* depends on the full key in *Driver*.
- *Miles* depends on both *DriverID* and *RouteID*.

Both relations are in 2NF.

> ✅ **Another Worked Example (Retail)**:  
*Inventory*(StoreID, ProductID, StoreCity, Quantity)  
- Key: $(StoreID, ProductID)$  
- FD: $StoreID \rightarrow StoreCity$

Decompose:
- **Store**(StoreID, StoreCity)
- **Inventory**(StoreID, ProductID, Quantity)

> 💡 **Quick Check**:  
In *ProjectAssignment*(EmpID, ProjectID, EmpName, Hours), with key $(EmpID, ProjectID)$ and $EmpID \rightarrow EmpName$:  
- Is this in 2NF?  
- If not, decompose it.  
*Answer: No. Decompose into Employee(EmpID, EmpName) and Assignment(EmpID, ProjectID, Hours).*

> ⚠️ **Common Misconception**:  
“2NF is irrelevant because 3NF covers it.”  
**Correction**: While 3NF implies 2NF, skipping 2NF may cause you to overlook partial dependencies early in analysis. Always verify normal forms in order.

> 🧠 **Try This Yourself**: Suppose a table *FlightCrew*(FlightID, CrewID, CrewName, Role) has key $(FlightID, CrewID)$ and $CrewID \rightarrow CrewName$. Is this in 2NF? If not, how would you decompose it?

Having eliminated partial dependencies, we now address transitive dependencies.

---

### 3. Third Normal Form (3NF): Eliminate Transitive Dependencies

#### Intuition: Is an Attribute Determined Indirectly?

Revisit the hospital example:

| PatientID | Doctor     | DoctorPhone     |  
|----------|------------|-----------------|  
| P001     | Dr. Lee    | 555-0123        |  
| P002     | Dr. Lee    | 555-0123        |

Functional dependencies:  
- $PatientID \rightarrow Doctor$  
- $Doctor \rightarrow DoctorPhone$

Thus, $PatientID \rightarrow Doctor \rightarrow DoctorPhone$: a **transitive dependency**.

> 🔥 **Tension**: Why does changing Dr. Lee’s phone number require scanning every patient?

This redundancy arises because *DoctorPhone* is indirectly determined by *PatientID*.

> 🧩 **Analogy (Supply Chain Logistics)**: A warehouse orders a widget from a supplier. The supplier’s address is stored in the order. If the supplier moves, every past order must be updated. But if the address is stored in a *Supplier* table, one change propagates everywhere. 3NF breaks indirect chains—just as supply chain systems decouple suppliers from individual orders.

#### Definition

A relation $R$ is in **3NF** if:
1. $R$ is in 2NF, **and**
2. For every non-trivial functional dependency $X \rightarrow Y$:  
   - $X$ is a **superkey**, or  
   - $Y$ is a **prime attribute**.

This condition allows dependencies on non-superkeys only when the determined attribute is prime.

> 📌 **Why allow prime attributes?** This exception helps preserve dependencies during decomposition. Without it, some valid schemas would be rejected.

#### Worked Example: Decomposing to 3NF

**Table**: *PatientCare*(PatientID, Doctor, DoctorPhone)  
- FD: $Doctor \rightarrow DoctorPhone$ violates 3NF

**Step 1: Identify the violating FD**  
$Doctor \rightarrow DoctorPhone$: $Doctor$ is not a superkey, and $DoctorPhone$ is non-prime.

**Step 2: Decompose**  
- **DoctorInfo**(Doctor, DoctorPhone), key: $Doctor$  
- **PatientCare**(PatientID, Doctor), key: $PatientID$

Now $DoctorPhone$ is stored once.

> ✅ **Another Worked Example (E-commerce)**:  
*Product*(SKU, Brand, BrandCountry, Price)  
- $SKU \rightarrow Brand$, $Brand \rightarrow BrandCountry$

Decompose:
- **BrandInfo**(Brand, BrandCountry)
- **Product**(SKU, Brand, Price)

> 💡 **Quick Check**:  
In *Employee*(EmpID, Dept, DeptMgr, Salary), with $EmpID \rightarrow Dept$, $Dept \rightarrow DeptMgr$, and key $EmpID$:  
- Does this violate 3NF?  
- If yes, decompose.  
*Answer: Yes. Decompose into Department(Dept, DeptMgr) and Employee(EmpID, Dept, Salary).*

> ⚠️ **Common Misconception**:  
“3NF eliminates all redundancy.”  
**Correction**: 3NF allows redundancy when a non-superkey determines a prime attribute. For stricter control, we use BCNF.

> 🧠 **Try This Yourself**: In a table *CourseOffering*(Semester, Course, Instructor, Office), with $Instructor \rightarrow Office$ and key $(Semester, Course)$, is this in 3NF? If not, decompose it.

Having removed transitive dependencies, we now enforce that only superkeys determine attributes.

---

### 4. Boyce-Codd Normal Form (BCNF): Only Superkeys Determine Attributes

#### Intuition: Should Any Non-Key Determine an Attribute?

Consider a university teaching table:

| Course     | Professor | Textbook         |  
|------------|-----------|------------------|  
| Databases  | Dr. Smith | DB-Design 3rd    |  
| Web Dev    | Dr. Smith | Web-Dev Guide    |  

Functional dependencies:  
- $Course \rightarrow Professor$  
- $Professor \rightarrow Textbook$  

Candidate key: $Course$

Now $Professor \rightarrow Textbook$: $Professor$ is not a superkey → violates **BCNF**.

Is it in 3NF? Only if $Textbook$ is prime—which it is not. So it violates both.

> 🔥 **Tension**: Dr. Smith uses one textbook across all courses. If she teaches 10 courses, the textbook is repeated 10 times. Updating it requires 10 changes. Missing one causes inconsistency.

This is a limitation of 3NF. BCNF addresses it by removing the exception for prime attributes.

> 🧩 **Analogy (Legal Precedent)**: In law, a ruling must be based on the full constitution, not a single amendment. If a judge rules based on a clause that doesn’t cover the case, the decision is invalid. BCNF says: if an attribute determines another, it must be a “constitutional” superkey—not a partial authority.

#### Definition

A relation $R$ is in **BCNF** if and only if, for every non-trivial functional dependency $X \rightarrow Y$, $X$ is a **superkey**.

> 📌 **BCNF vs 3NF**: BCNF removes the “$Y$ is prime” exception. It is stricter: **only superkeys can determine any attribute**.

#### Worked Example: Decomposing to BCNF

**Table**: *Teaching*(Course, Professor, Textbook)  
- FD: $Professor \rightarrow Textbook$ violates BCNF

**Step 1: Find a violating FD**  
$Professor \rightarrow Textbook$: $Professor$ is not a superkey.

**Step 2: Decompose using the FD**  
- **TextAssignment**(Professor, Textbook), key: $Professor$  
- **CourseProf**(Course, Professor), key: $Course$

Now all functional dependencies are on superkeys → both relations are in BCNF.

**Check dependency preservation**:  
- $Course \rightarrow Professor$: yes (in *CourseProf*)  
- $Professor \rightarrow Textbook$: yes (in *TextAssignment*)  
→ Dependencies are preserved.

> ✅ **Another Worked Example (Airline)**:  
*Flight*(FlightNum, Airline, Gate)  
- $FlightNum \rightarrow Airline$  
- $Airline \rightarrow Gate$  
- Key: $FlightNum$

$Airline \rightarrow Gate$: $Airline$ is not a superkey → violates BCNF.

Decompose:
- **AirlineGate**(Airline, Gate)
- **Flight**(FlightNum, Airline)

Now in BCNF. However, a new airline cannot be added without a flight → insertion anomaly. This trade-off is accepted to ensure data integrity.

> 💡 **Quick Check**:  
In *R*(A, B, C) with FDs $A \rightarrow B$, $B \rightarrow C$, and key $A$:  
- Is this in BCNF?  
- If not, decompose.  
*Answer: No. $B \rightarrow C$ violates BCNF. Decompose into R1(A, B) and R2(B, C).*

> ⚠️ **Common Misconception**:  
“BCNF always preserves all functional dependencies.”  
**Correction**: BCNF decomposition may **lose** some dependencies. For example, if $A \rightarrow B$ and $B \rightarrow C$, decomposing into $R1(A,B)$ and $R2(B,C)$ preserves the two FDs, but $A \rightarrow C$ is no longer directly enforceable. Application logic may be required to maintain such indirect dependencies.

> 🧠 **Try This Yourself**: In a table *Research*(Project, Scientist, Lab), with $Scientist \rightarrow Lab$ and key $Project$, is this in BCNF? If not, decompose it. Does the decomposition preserve $Project \rightarrow Lab$?

Having achieved the highest normal form, we now consider when to relax these constraints.

---

### 5. Trade-offs and Denormalization: When to Break the Rules

#### Intuition: Sometimes Speed Beats Perfection

You’ve normalized all tables. Then a dashboard query—joining six tables—takes five seconds. Users complain.

You now face a **dilemma**: perfect data integrity or acceptable performance?

This is analogous to **caching** in software: redundancy is introduced to improve speed. In databases, we *remove* redundancy for safety—but sometimes *add it back* for performance.

> 🔥 **Tension**: Can we *design* redundancy intelligently—so it speeds things up without sacrificing consistency?

Yes. But only after normalization.

> 🧩 **Analogy (Library Reshelving)**: A library could keep books in perfect Dewey Decimal order (normalized), but place frequently borrowed titles near the front desk (denormalized). The system remains correct, but access is faster. The key is intentional placement—not chaos.