**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. **Identify** whether a relation is in 1NF, 2NF, 3NF, or BCNF by analyzing its attributes, candidate keys, and functional dependencies.  
2. **Explain** how partial and transitive dependencies lead to insertion, deletion, and update anomalies using step-by-step examples.  
3. **Apply** decomposition algorithms to convert a schema into 2NF, 3NF, and BCNF, and verify that the result is lossless and (where possible) dependency-preserving.  
4. **Analyze** a real-world database schema to detect normalization violations and justify appropriate normalization steps.  
5. **Evaluate** trade-offs between full normalization and practical design considerations like query performance and dependency preservation.

---

### Prerequisites: Functional Dependencies, Keys, and Attribute Closure

Normalization is not about cleaning data—it’s about **encoding knowledge without contradiction**. To do that, we must first understand how one piece of data *determines* another.

#### Functional Dependencies: The Grammar of Data

Imagine a spoken language where every noun has exactly one plural form. If you know the singular, you *must* know the plural. That’s a **functional dependency (FD)**: a rule that says: *Given this, you get that—no exceptions.*

Formally: Let $ R $ be a relation schema over attribute set $ \mathcal{A} $, and $ X, Y \subseteq \mathcal{A} $. The FD $ X \rightarrow Y $ holds on $ R $ if and only if, for every valid instance $ r $ of $ R $, and for all tuples $ t_1, t_2 \in r $:

$$
t_1[X] = t_2[X] \implies t_1[Y] = t_2[Y]
$$

- $ X $ is the **determinant**  
- $ Y $ is the **dependent**  
- An FD is **trivial** if $ Y \subseteq X $; otherwise, it is **nontrivial**

> **Worked Example: Validating Functional Dependencies**  
In `Flight(FlightNo, Airline, PlaneType)`:
- $ \text{FlightNo} \rightarrow \text{Airline} $: ✅ Each flight number belongs to one airline  
- $ \text{Airline} \rightarrow \text{FlightNo} $: ❌ One airline operates many flights  
- $ \text{PlaneType} \rightarrow \text{CrewSize} $: ✅ But `CrewSize` is not in this schema → suggests a new relation `Plane(PlaneType, CrewSize)`

> **Try This Yourself: The Hidden Rule**  
You’re given a table `Weather(City, Date, HighTemp, LowTemp, ForecastBy)`.  
Suppose `ForecastBy` is the meteorologist assigned to that city.  
- Is $ \text{City} \rightarrow \text{ForecastBy} $ likely to hold?  
- Is $ \text{Date} \rightarrow \text{HighTemp} $ likely? Why or why not?  
*Think before reading on.*

> **Quick Check**  
Given `Employee(SSN, Dept, Manager)`:
- $ \text{SSN} \rightarrow \text{Dept} $: Yes  
- $ \text{Dept} \rightarrow \text{Manager} $: Yes (each department has one manager)  
- $ \text{Manager} \rightarrow \text{Dept} $: No (a manager may oversee multiple departments)

> **Common Misconception**: Adding a surrogate primary key (e.g., `RecordID`) resolves functional dependency issues.  
❌ **False**. Normalization depends on **semantic dependencies**, not key choice. If `CourseName` depends on `CourseID`, that dependency persists regardless of whether `RecordID` is the primary key.

---

#### Candidate Keys and Prime Attributes: The DNA of Uniqueness

A **candidate key** is like a biological fingerprint: minimal, unique, and sufficient to identify an entity. You don’t need the whole genome—just the right markers.

Two conditions for $ K \subseteq \mathcal{A} $ to be a candidate key:
1. **Uniqueness**: $ K^+ = \mathcal{A} $ (the closure of $ K $ determines all attributes)  
2. **Minimality**: No proper subset of $ K $ is a superkey

One candidate key is designated the **primary key**; others remain semantically relevant.

An attribute is **prime** if it appears in **any** candidate key; otherwise, it is **non-prime**.

> **Analogy: Keys as Passwords**  
Think of a candidate key as a password that unlocks full access to a tuple.  
- If `StudentID` is a key, it’s like a master password.  
- If `(Course, Semester)` is also a key, it’s a different password to the same account.  
- Prime attributes are *part* of some password; non-prime are not.

> **Worked Example: Finding Candidate Keys**  
Given $ R(A,B,C) $ with FDs:
- $ A \rightarrow B $
- $ B \rightarrow C $

Compute $ A^+ $:
- Start: $ \{A\} $
- Apply $ A \rightarrow B $: $ \{A,B\} $
- Apply $ B \rightarrow C $: $ \{A,B,C\} $ ⇒ $ A^+ = \mathcal{A} $ ⇒ $ A $ is a superkey  
- Minimal? Yes ⇒ candidate key: $ \{A\} $

Check $ B^+ $: $ \{B\} \rightarrow \{B,C\} \neq \mathcal{A} $ ⇒ not a superkey  
Thus, only candidate key is $ \{A\} $; prime: $ A $; non-prime: $ B, C $

> **Try This Yourself: Two Keys Are Better Than One**  
Given $ R(X,Y,Z) $ with FDs:
- $ XY \rightarrow Z $
- $ Z \rightarrow Y $

Compute closures:
- $ XY^+ $: $ XY \rightarrow Z $ ⇒ $ \{X,Y,Z\} $ ⇒ superkey  
- $ X^+ = \{X\} $, $ Y^+ = \{Y\} $ ⇒ neither alone suffices  
- $ Z^+ = \{Z,Y\} $, so $ XZ^+ = \{X,Z,Y\} = \mathcal{A} $ ⇒ $ \{X,Z\} $ is a superkey  
- Minimality: $ X $ and $ Z $ individually not superkeys ⇒ candidate keys: $ \{X,Y\}, \{X,Z\} $  
- Prime attributes: $ X, Y, Z $ (each appears in at least one candidate key)

> **Common Misconception**: Only the primary key matters in normalization.  
❌ **False**. All candidate keys define prime attributes. An attribute may be prime even if it is not in the primary key.

---

#### Algorithm: Computing Attribute Closure

To test whether a set $ X $ is a superkey, compute its **attribute closure** $ X^+ $ under the given set of FDs $ F $.

**Algorithm: Attribute Closure $ X^+ $**  
Input: Attribute set $ X $, set of FDs $ F $  
Output: $ X^+ $

1. Initialize $ X^+ := X $  
2. Repeat until no change:  
   For each FD $ A \rightarrow B $ in $ F $:  
   If $ A \subseteq X^+ $, then add $ B $ to $ X^+ $  
3. Return $ X^+ $

> **Analogy: Closure as a Chain Reaction**  
Think of FDs as dominoes. If $ A \rightarrow B $ and $ B \rightarrow C $, then knowing $ A $ tips $ B $, which tips $ C $.  
Attribute closure is the full set of dominoes that fall starting from $ X $.

> **Worked Example: Closure and Superkeys**  
Given $ R(A,B,C,D) $ with FDs:
- $ A \rightarrow B $
- $ B \rightarrow C $
- $ C \rightarrow D $

Compute $ A^+ $:
- Start: $ \{A\} $
- $ A \rightarrow B $: $ \{A,B\} $
- $ B \rightarrow C $: $ \{A,B,C\} $
- $ C \rightarrow D $: $ \{A,B,C,D\} $ ⇒ $ A^+ = \mathcal{A} $ ⇒ $ A $ is a superkey  
- Minimal? Yes ⇒ candidate key: $ \{A\} $

> **Quick Check**  
Given $ R(P,Q,R) $ with FDs:
- $ P \rightarrow Q $
- $ Q \rightarrow R $

Then:
- $ P^+ = \{P,Q,R\} $ ⇒ $ \{P\} $ is a candidate key  
- $ Q^+ = \{Q,R\} $ ⇒ not a superkey  
- Prime: $ P $; non-prime: $ Q, R $

---

### 1. First Normal Form (1NF): Atomic Values Only

#### The Explosion of Ambiguity

Imagine a medical alert system where a patient’s allergies are stored as a comma-separated string: `"Peanuts, Penicillin"`.  
Now, a doctor searches for patients allergic to `"Penicillin"`.  
But what if the entry says `"Penicillin, Shellfish"` vs. `"Penicillin"` vs. `"Penicillin (severe)"`?  
The system **cannot reliably parse meaning from structure**.

This is not a data entry problem—it’s a **logical design failure**. The database has outsourced reasoning to string parsing, violating the relational model’s foundation.

> **Analogy: 1NF is Like a Spreadsheet Cell**  
In a well-designed spreadsheet, each cell holds one fact. You wouldn’t put “Meeting: 3 PM, Location: Room 5” in one cell and parse it later.  
1NF enforces this: **one fact per cell**.

#### Formal Definition of 1NF

A relation is in **First Normal Form (1NF)** if:
- Every attribute contains **atomic (indivisible) values**
- There are **no repeating groups** (e.g., `Course1`, `Course2`, `Course3`)

This ensures data can be uniquely accessed, indexed, and constrained.

#### Worked Example: Achieving 1NF

Given:

| BookID | Authors         |
|--------|------------------|
| B001   | Smith, Jones     |
| B002   | Lee              |

**Violation**: `Authors` is multi-valued.

**Fix**: Decompose into `BookAuthors(BookID, Author)`:

| BookID | Author |
|--------|--------|
| B001   | Smith  |
| B001   | Jones  |
| B002   | Lee    |

- Candidate key: $ (\text{BookID}, \text{Author}) $
- Benefits:
  - Enforce referential integrity to `Author` table
  - Index on `Author`
  - Prevent duplicates via key constraint

> **Try This Yourself: The Hidden Repeating Group**  
You’re designing a `Course` table. Should you include `Prerequisites` as a comma-separated list?  
What if you need to:
- Find all courses that list `CS101` as a prerequisite?
- Ensure `CS101` exists before adding it?
*Sketch a normalized alternative.*

> **Quick Check**  
`Patient(PatientID, Name, Allergies)` with `Allergies = "Peanuts, Penicillin"`  
- ❌ Violates 1NF  
- ✅ Fix: `PatientAllergies(PatientID, Allergy)` with key $ (\text{PatientID}, \text{Allergy}) $

> **Common Misconception**: Using arrays or JSON (e.g., PostgreSQL `TEXT[]`) satisfies 1NF.  
❌ **False**. If application logic must parse the field (e.g., search for "Penicillin"), the value is **not atomic**. True 1NF requires decomposition into base relations.

---

### 2. Second Normal Form (2NF): Eliminate Partial Dependencies

#### The Hidden Cost of Composite Keys

You’re building a university database. The `Enrollment` table stores:

| StudentID | CourseID | CourseName | Grade |
|----------|----------|------------|-------|
| S001     | C101     | Calculus   | A     |
| S002     | C101     | Calculus   | B     |

The key is $ (\text{StudentID}, \text{CourseID}) $. But `CourseName` depends only on `CourseID`.  
So every time "Calculus" appears, it’s a **copy**—not a reference.

> **Analogy: 2NF is Like a Library Catalog**  
A library doesn’t write “Title: Calculus” on every copy of the book. It has a **catalog entry** (the `Course` table) and a **loan record** (the `Enrollment` table).  
Mixing them is like printing the book’s title on every checkout slip.

This is a **partial dependency**: a non-prime attribute functionally dependent on a **proper subset** of a candidate key.

**Anomalies**:
- **Update**: Renaming "Calculus" requires updating multiple rows
- **Insert**: Cannot add a course without a student
- **Delete**: Dropping the last student erases course information

> Real-world impact: E-commerce systems storing `ProductName` in `OrderItem` repeat product names across thousands of orders.

#### Formal Definition of 2NF

A relation is in **Second Normal Form (2NF)** if:
- It is in 1NF
- Every **non-prime attribute** is **fully functionally dependent** on **every candidate key**

Equivalently: no non-prime attribute depends on a proper subset of any candidate key.

#### Worked Example: Decomposing to 2NF

Schema: `Enrollment(StudentID, CourseID, CourseName, Grade)`  
FD: $ \text{CourseID} \rightarrow \text{CourseName} $  
Key: $ (\text{StudentID}, \text{CourseID}) $ ⇒ non-prime: `CourseName`, `Grade`

Check: `CourseName` depends only on `CourseID` ⊂ key ⇒ **partial dependency** ⇒ not in 2NF

**Decomposition**:
1. `Courses(CourseID, CourseName)` — key: $ \text{CourseID} $
2. `Enrollments(StudentID, CourseID, Grade)` — key: $ (\text{StudentID}, \text{CourseID}) $

Now `CourseName` is stored once. All anomalies resolved.

> **Try This Yourself: The Order Item Trap**  
`OrderItem(OrderID, ProductID, ProductName, Qty)`  
- Key: $ (\text{OrderID}, \text{ProductID}) $
- FD: $ \text{ProductID} \rightarrow \text{ProductName} $
- Is this in 2NF?  
- If not, decompose it.  
*Write the resulting schemas and keys.*

> **Quick Check**  
`OrderItem(OrderID, ProductID, ProductName, Qty)`  
- Key: $ (\text{OrderID}, \text{ProductID}) $
- FD: $ \text{ProductID} \rightarrow \text{ProductName} $
- Partial dependency ⇒ not in 2NF  
- Fix: `Products(ProductID, ProductName)`, `OrderItems(OrderID, ProductID, Qty)`

> **Common Misconception**: Adding a surrogate key (e.g., `OrderItemID`) fixes 2NF violations.  
❌ **False**. The FD $ \text{ProductID} \rightarrow \text{ProductName} $ still causes redundancy. Decomposition is required.

---

### 3. Third Normal Form (3NF): Eliminate Transitive Dependencies

#### The Domino Effect of Non-Key Dependencies

| DoctorID | Specialty   | HeadNurse     |
|----------|-------------|---------------|
| D001     | Cardiology  | Nurse Smith   |
| D002     | Cardiology  | Nurse Smith   |
| D003     | Neurology   | Nurse Jones   |

FDs:
- $ \text{DoctorID} \rightarrow \text{Specialty} $
- $ \text{Specialty} \rightarrow \text{HeadNurse} $

So $ \text{DoctorID} \rightarrow \text{HeadNurse} $—but only through `Specialty`.  
“Nurse Smith” repeats for all cardiologists.

> **Analogy: 3NF is Like a Corporate Hierarchy**  
In a company, employees report to managers, and managers belong to departments.  
If you store `Department` in the `Employee` table based on their manager, then changing a manager’s department forces updates to all their reports.  
The dependency **cascades** through the chain.

This is a **transitive dependency**: a non-prime attribute determines another non-prime attribute.

**Anomalies**:
- **Update**: Changing the head nurse for Cardiology requires updating all cardiologists
- **Insert**: Cannot record a specialty’s head nurse without a doctor
- **Delete**: Last doctor in a specialty erases head nurse info

#### Formal Definition of 3NF

A relation $ R $ is in **Third Normal Form (3NF)** if for every nontrivial FD $ X \rightarrow Y $:
1. $ X $ is a **superkey**, or  
2. $ Y $ is a **prime attribute**

This prevents non-prime attributes from being determined by non-superkeys—unless the dependent is part of a candidate key.

> Why allow $ Y $ prime? To avoid unnecessary decomposition. If $ \text{Specialty} \rightarrow \text{DoctorID} $ and `DoctorID` is prime, no redundancy in non-key data ⇒ acceptable.

#### Worked Example: Decomposing to 3NF

Schema: `Doctor(DoctorID, Specialty, HeadNurse)`  
Key: $ \{\text{DoctorID}\} $ ⇒ prime: `DoctorID`; non-prime: `Specialty`, `HeadNurse`  
FD: $ \text{Specialty} \rightarrow \text{HeadNurse} $

Check:
- $ \text{Specialty} $ is not a superkey
- $ \text{HeadNurse} $ is not prime ⇒ violates 3NF

**Decomposition**:
1. `SpecialtyNurse(Specialty, HeadNurse)` — key: $ \text{Specialty} $
2. `DoctorSpecialty(DoctorID, Specialty)` — key: $ \text{DoctorID} $

Now `HeadNurse` is stored once per specialty.

> **Try This Yourself: The Student Advisor Chain**  
`Student(StudentID, AdvisorEmail, Dept, DeptPhone)`  
FDs:
- $ \text{StudentID} \rightarrow \text{AdvisorEmail} $
- $ \text{AdvisorEmail} \rightarrow \text{Dept} $
- $ \text{Dept} \rightarrow \text{DeptPhone} $

Key: $ \text{StudentID} $ ⇒ non-prime: `AdvisorEmail`, `Dept`, `DeptPhone`

Identify all 3NF violations and decompose.  
*Write the final schemas and verify each is in 3NF.*

> **Quick Check**  
`Student(StudentID, AdvisorEmail, Dept, DeptPhone)`  
FDs:
- $ \text{StudentID} \rightarrow \text{AdvisorEmail} $
- $ \text{AdvisorEmail} \rightarrow \text{Dept} $
- $ \text{Dept} \rightarrow \text{DeptPhone} $

Key: $ \text{StudentID} $ ⇒ non-prime: `AdvisorEmail`, `Dept`, `DeptPhone`

Violations:
- $ \text{AdvisorEmail} \rightarrow \text{Dept} $: not superkey, `Dept` non-prime
- $ \text{Dept} \rightarrow \text{DeptPhone} $: not superkey, `DeptPhone` non-prime

**Decomposition**:
1. `AdvisorDept(AdvisorEmail, Dept)` — key: $ \text{AdvisorEmail} $
2. `DeptPhone(Dept, DeptPhone)` — key: $ \text{Dept} $
3. `StudentAdvisor(StudentID, AdvisorEmail)` — key: $ \text{StudentID} $

All resulting relations are in 3NF. All FDs are preserved.

> **Common Misconception**: 3NF eliminates all redundancy.  
❌ **False**. 3NF only prevents non-prime attributes from being determined by non-superkeys. Redund