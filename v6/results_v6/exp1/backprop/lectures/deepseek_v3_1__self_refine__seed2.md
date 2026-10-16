## Learning Objectives

By the end of this lecture, you will be able to:

1.  **Remember:** State the computational complexity of naive gradient computation versus backpropagation for a network with *P* parameters.
2.  **Understand:** Explain why summing gradient contributions from multiple children is mathematically required, and identify a common misconception about this rule.
3.  **Apply:** Given a simple arithmetic expression or a 1-2 layer network, construct its computational graph and manually execute the forward and backward passes to compute all gradients.
4.  **Analyze:** Decompose a given neural network layer (e.g., Linear + ReLU) into its primitive operations and write the local derivative for each.
5.  **Create:** Design a memory-efficient backpropagation strategy for a network that exceeds available RAM, by trading off recomputation and storage.

---

## 1. Prerequisites and the Problem Setting

### 1.1 Opening Hook: The Gradient Wall

In 2015, the European Centre for Medium-Range Weather Forecasts explored neural networks for hurricane path prediction. A prototype with 50 million parameters required gradient computation. Using finite differences, one gradient step would demand 50 million forward passes. At 3 seconds per pass, a single parameter update would take approximately 4.75 years. The model would become meteorologically obsolete before the first optimization step completed.

The bottleneck was algorithmic, not hardware-related. Computing the gradient of a scalar loss with respect to millions of parameters by treating each partial derivative independently scales quadratically in the number of parameters. The question that toppled this wall was: *can we obtain the full gradient in time proportional to a single forward pass?*

Backpropagation answered yes. It did not merely accelerate training — it made training feasible for networks beyond trivial sizes. This algorithm is the computational engine that moved deep learning from 1980s research demonstrations to modern systems deployed in medical imaging, machine translation, autonomous navigation, and numerical weather prediction.

But this story reveals a deeper tension: backpropagation achieves its miraculous speedup by storing every intermediate result during the forward pass. When your network is larger than your GPU's memory, you face a brutal trade-off between time and space. We'll confront this tension head-on in Section 5. For now, consider this: *how would you compute the gradient of a function with millions of inputs without storing every intermediate value?* Keep that question in your back pocket.

### 1.2 Required Background

We assume working knowledge of:

-   **Matrix algebra:** products \(\mathbf{A}\mathbf{B}\), transposes \(\mathbf{A}^\top\), element-wise operations, and broadcasting semantics. The gradient of a scalar with respect to a matrix is a matrix of the same shape, with entries \((\nabla_{\mathbf{A}} J)_{ij} = \partial J / \partial A_{ij}\).
-   **Multivariate calculus:** the chain rule for scalar functions, \(\frac{\partial}{\partial x} f(g(x)) = f'(g(x))\, g'(x)\), extended to vector-valued intermediate quantities. For \(\mathbf{y} = g(\mathbf{x})\) and \(J = f(\mathbf{y})\), the gradient obeys \(\nabla_{\mathbf{x}} J = (\frac{\partial \mathbf{y}}{\partial \mathbf{x}})^\top \nabla_{\mathbf{y}} J\), where \(\frac{\partial \mathbf{y}}{\partial \mathbf{x}}\) is the Jacobian matrix.
-   **Feedforward neural network structure:** composition of affine transformations \(\mathbf{W}^{(\ell)} \mathbf{h}^{(\ell-1)} + \mathbf{b}^{(\ell)}\) and element-wise nonlinearities \(\sigma^{(\ell)}\), terminating in a scalar loss \(J\).
-   **Gradient-based optimization:** parameters are updated via \(\boldsymbol{\theta} \leftarrow \boldsymbol{\theta} - \eta \nabla_{\boldsymbol{\theta}} J\), with learning rate \(\eta > 0\). We focus on computing \(\nabla_{\boldsymbol{\theta}} J\); the optimizer that consumes it is secondary.

### 1.3 The Core Problem

Consider a feedforward network mapping input \(\mathbf{x} \in \mathbb{R}^d\) to prediction \(\hat{\mathbf{y}}\) through a composition of \(L\) layers. Let \(\boldsymbol{\theta}\) denote the collection of all weight matrices \(\mathbf{W}^{(\ell)}\) and bias vectors \(\mathbf{b}^{(\ell)}\) for \(\ell = 1,\dots,L\). Let \(J(\boldsymbol{\theta})\) be a scalar cost function measuring the discrepancy between predictions and targets.

**The learning task** is to adjust \(\boldsymbol{\theta}\) to minimize \(J\). First-order optimization methods require the gradient \(\nabla_{\boldsymbol{\theta}} J\) — the vector of partial derivatives of \(J\) with respect to every scalar parameter.

**Why naive computation fails.** Let \(P = |\boldsymbol{\theta}|\) be the total number of scalar parameters. Computing \(\partial J / \partial \theta_k\) via the chain rule from scratch for each \(k\) independently requires traversing the computational graph from input to output for each parameter. A single forward pass costs \(O(P)\) because each parameter participates in at least one operation. Repeating this \(P\) times yields \(O(P^2)\) total cost. For \(P = 10^7\), this is \(10^{14}\) operations — intractable.

**Analogy: factory auditing.** Imagine auditing a factory with \(P\) machines, where each machine's contribution to total profit depends on all downstream machines it feeds into. The naive approach — sending one auditor per machine to trace the entire production line — requires \(P\) auditors each walking the full factory floor. Backpropagation is like sending one auditor forward to record every machine's output, then walking backward once, updating each machine's "marginal profit contribution" by combining the contributions already computed for its downstream consumers. One forward pass, one backward pass, all \(P\) audits complete.

**The backpropagation insight.** The network's computation is a directed acyclic graph (DAG) where intermediate quantities are reused across many downstream computations. By traversing this graph in reverse topological order and caching intermediate gradients, we compute all \(P\) partial derivatives in \(O(P)\) time — the cost of roughly one forward pass plus one backward pass. The reduction from \(O(P^2)\) to \(O(P)\) is the algorithmic contribution of backpropagation.

**The memory tension.** The \(O(P)\) time complexity requires storing every intermediate activation computed during the forward pass, because the backward pass needs them to evaluate local derivatives. For a network with \(P\) parameters and a mini-batch of size \(B\), this storage is \(O(B \cdot P)\). When this exceeds available memory, we face a trade-off: recompute intermediates on demand, trading time for memory, or reduce batch size, potentially degrading optimization. Section 5 addresses this tension explicitly.

**Pause and consider:** Given a DAG with \(n\) nodes where each node's output depends on its parents, and a scalar function \(J\) evaluated at the root, how would you compute \(\partial J / \partial u^{(i)}\) for every node \(u^{(i)}\) without redundant computation? What information must you cache, and in what order must you traverse the graph?

### 1.4 Quick Check 1

*Question:* A network has \(P = 10^6\) parameters. A single forward pass takes 10 ms. Estimate the time for one gradient computation using (a) naive independent chain-rule evaluations and (b) backpropagation.

<details>
<summary>Click for answer</summary>

(a) Naive: approximately \(10^6 \times 10 \text{ ms} = 10^4\) seconds ≈ 2.8 hours per gradient step.

(b) Backpropagation: one forward pass (10 ms) + one backward pass (roughly 10–20 ms) ≈ 20–30 ms total — a speedup factor of roughly \(10^6\).
</details>

**Summary of Section 1.** We formalized the gradient computation problem: given a scalar loss \(J\) depending on \(P\) parameters through a DAG of operations, compute all \(P\) partial derivatives efficiently. Naive per-parameter evaluation costs \(O(P^2)\). Backpropagation achieves \(O(P)\) by exploiting the graph structure. We now develop the computational graph abstraction that makes this possible.

---

## 2. Computational Graphs: The Universal Abstraction

### 2.1 Motivation: From Equations to Graphs

A neural network is a composition of operations. Rather than treating it as a monolithic formula, we decompose it into a sequence of primitive operations — addition, multiplication, element-wise nonlinearities, matrix products — each producing an intermediate result consumed by subsequent operations. This decomposition yields a directed graph.

**Why this abstraction is powerful.** Once a network is expressed as a DAG, backpropagation becomes a graph traversal algorithm: propagate gradients from the root (the loss) to the leaves (the parameters and inputs) by reversing the edges. This algorithm is independent of the specific architecture. Feedforward networks, convolutional networks, recurrent networks unrolled through time, and transformers all yield DAGs. PyTorch's `autograd` and TensorFlow's `GradientTape` are literal implementations of this graph-based backpropagation.

**Analogy: electrical circuit analysis.** A computational graph is to backpropagation what a circuit diagram is to Kirchhoff's laws. Just as current flowing through a resistor network can be computed by solving a linear system derived from the graph topology, gradients flowing backward through a neural network are computed by a recurrence derived from the DAG structure. In both cases, the graph abstraction decouples the solution algorithm from the specific components connected.

**Example: a simple arithmetic expression.** Let \(J = (a \cdot b) + c^2\). Decompose into primitives:

1.  \(u_1 = a \cdot b\)    (multiply)
2.  \(u_2 = c^2\)        (square)
3.  \(u_3 = u_1 + u_2\)  (add)
4.  \(J = u_3\)          (identity)

The graph has nodes \(\{a, b, c, u_1, u_2, u_3, J\}\). Directed edges represent data flow: \(a \to u_1\), \(b \to u_1\), \(c \to u_2\), \(u_1 \to u_3\), \(u_2 \to u_3\), \(u_3 \to J\).

**Example: a single neural network layer.** Consider \(\mathbf{h} = \text{ReLU}(\mathbf{W}\mathbf{x} + \mathbf{b})\) where \(\mathbf{W} \in \mathbb{R}^{m \times d}\), \(\mathbf{x} \in \mathbb{R}^d\), \(\mathbf{b} \in \mathbb{R}^m\):

1.  \(\mathbf{u}_1 = \mathbf{W}\mathbf{x}\)            (matrix-vector product)
2.  \(\mathbf{u}_2 = \mathbf{u}_1 + \mathbf{b}\)      (vector addition with broadcasting)
3.  \(\mathbf{h} = \max(\mathbf{u}_2, 0)\)            (element-wise ReLU)

Nodes: \(\{\mathbf{x}, \mathbf{W}, \mathbf{b}, \mathbf{u}_1, \mathbf{u}_2, \mathbf{h}\}\). Edges reflect dependencies: \(\mathbf{x} \to \mathbf{u}_1\), \(\mathbf{W} \to \mathbf{u}_1\), \(\mathbf{u}_1 \to \mathbf{u}_2\), \(\mathbf{b} \to \mathbf{u}_2\), \(\mathbf{u}_2 \to \mathbf{h}\).

### 2.2 Formal Definition

A **computational graph** is a directed acyclic graph (DAG) \(\mathcal{G} = (\mathcal{V}, \mathcal{E})\) where:

-   **Nodes** \(\mathcal{V} = \{u^{(1)}, u^{(2)}, \dots, u^{(n)}\}\) represent variables — the results of operations.
-   **Edges** \(\mathcal{E}\) represent direct data dependencies: a directed edge \(u^{(i)} \to u^{(j)}\) means \(u^{(i)}\) is an operand in the operation that produces \(u^{(j)}\).

We assume nodes are numbered in **topological order**: if \(u^{(i)} \to u^{(j)}\) is an edge, then \(i < j\). This ordering always exists because the graph is acyclic. The root node is \(u^{(n)} = J\), the scalar cost. Leaf nodes (in-degree zero) are inputs and parameters.

**Terminology:**

-   **Parents** of \(u^{(i)}\): the set \(\text{parents}(i) = \{u^{(k)} : u^{(k)} \to u^{(i)} \in \mathcal{E}\}\) — nodes whose outputs are direct inputs to the operation producing \(u^{(i)}\).
-   **Children** of \(u^{(i)}\): the set \(\text{children}(i) = \{u^{(j)} : u^{(i)} \to u^{(j)} \in \mathcal{E}\}\) — nodes that directly consume \(u^{(i)}\).
-   **Leaves:** nodes with \(\text{parents}(i) = \varnothing\).
-   **Root:** the unique node with \(\text{children}(i) = \varnothing\), which is \(J\).

### 2.3 Interactive Exercise: Graph Construction

Sketch the computational graph for \(z = (x + y) \cdot \max(x, 0)\). Label each node with its operation and identify all edges.

<details>
<summary>Click for solution</summary>

Nodes and operations:
1.  \(u_1 = x + y\)         (addition)
2.  \(u_2 = \max(x, 0)\)    (ReLU)
3.  \(u_3 = u_1 \cdot u_2\) (multiplication)
4.  \(z = u_3\)             (root)

Edges: \(x \to u_1\), \(y \to u_1\), \(x \to u_2\), \(u_1 \to u_3\), \(u_2 \to u_3\), \(u_3 \to z\).

**Critical observation:** Node \(x\) has out-degree 2 — it feeds into both \(u_1\) and \(u_2\). This branching means \(x\) influences \(z\) through two independent pathways. During backpropagation, the gradient w.r.t. \(x\) will receive contributions from both children, summed.
</details>

### 2.4 The Gradient Objective

For any node \(u^{(i)}\), we seek the **gradient** (also called the **adjoint** or **sensitivity**):

\[
\bar{u}^{(i)} \triangleq \frac{\partial J}{\partial u^{(i)}}
\]

For leaf nodes representing parameters, \(\bar{u}^{(i)}\) is the quantity required for gradient-based optimization. For intermediate nodes, these gradients are intermediate values that propagate toward the parameters.

### 2.5 Quick Check 2

*Question:* In the graph for \(J = (a \cdot b) + c^2\), list the children of node \(a\) and the parents of node \(u_3\).

<details>
<summary>Click for answer</summary>

Children of \(a\): \(\{u_1\}\) — \(a\) is an input only to the multiplication operation.

Parents of \(u_3\): \(\{u_1, u_2\}\) — the addition operation consumes both \(u_1\) and \(u_2\).
</details>

**Summary of Section 2.** We defined the computational graph as a DAG where nodes are variables and edges encode data dependencies. This abstraction is architecture-agnostic and serves as the substrate for backpropagation. We now derive the chain rule decomposition that computes all node gradients in a single reverse traversal.

---

## 3. The Chain Rule Decomposition

### 3.1 Intuition: Messages Propagating Backward

Consider the root \(J\). A perturbation \(\Delta\) in \(J\) changes \(J\) by exactly \(\Delta\), so \(\partial J / \partial J = 1\). This is the initial "message."

Now consider any node \(u^{(i)}\). A small change in \(u^{(i)}\) affects \(J\) only through the nodes that directly consume \(u^{(i)}\) — its children. Each child \(u^{(j)}\) already knows its own message \(\partial J / \partial u^{(j)}\), computed earlier in the reverse traversal. The child also knows its local sensitivity to \(u^{(i)}\): the partial derivative \(\partial u^{(j)} / \partial u^{(i)}\).

If \(u^{(i)}\) had exactly one child, the chain rule would give:

\[
\frac{\partial J}{\partial u^{(i)}} = \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}.
\]

But \(u^{(i)}\) can have multiple children — its output can fan out to several downstream operations, each eventually contributing to \(J\). A perturbation in \(u^{(i)}\) simultaneously perturbs all children. The total effect on \(J\) is the sum of effects through each child:

\[
\frac{\partial J}{\partial u^{(i)}} = \sum_{j \in \text{children}(i)} \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}.
\]

**Why a sum?** This is the multivariate chain rule. If \(J = f(u^{(j_1)}, u^{(j_2)}, \dots)\) and each \(u^{(j_k)} = g_k(u^{(i)}, \dots)\), then the total derivative is:

\[
\frac{d J}{d u^{(i)}} = \sum_{k} \frac{\partial f}{\partial u^{(j_k)}} \cdot \frac{\partial g_k}{\partial u^{(i)}}.
\]

Each term is the contribution along one outgoing edge. The sum aggregates independent causal pathways.

**Analogy: river deltas.** A river's flow splits into multiple distributaries before reaching the ocean. The total discharge into the ocean equals the sum of the discharges through each distributary. Similarly, the total sensitivity of \(J\) to \(u^{(i)}\) is the sum of sensitivities propagated along each outgoing edge.

**Analogy: supply chain attribution.** A silicon supplier provides material to both a solar panel factory and a microchip foundry. Both products contribute to total corporate revenue. To compute the marginal revenue per kilogram of raw silicon, one multiplies the silicon-to-product conversion rate at each factory by that product's product-to-revenue rate, and then sums the two contributions. The pathways are independent; their effects add.

**Analogy: ecological trophic cascades.** In a food web, removing a species affects all its predators, and through them, the entire ecosystem. The total impact on top predator biomass is the sum of impacts through each consumption pathway. Ecologists compute these "indirect effects" by multiplying edge sensitivities along each food chain and summing across chains — exactly the backpropagation recurrence, applied to an ecosystem graph rather than a computational one.

### 3.2 Formal Statement

Let \(\text{children}(i) = \{j : u^{(i)} \to u^{(j)} \in \mathcal{E}\}\). The **backpropagation rule** is:

\[
\boxed{\frac{\partial J}{\partial u^{(i)}} = \sum_{j \in \text{children}(i)} \frac{\partial J}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}} \tag{1}
\]

This is a recurrence: to compute the gradient at node \(i\), we require the gradients at all its children. The base case is the root:

\[
\frac{\partial J}{\partial J} = 1. \tag{2}
\]

Processing nodes in reverse topological order (from \(n\) down to 1) ensures that when we compute \(\partial J / \partial u^{(i)}\), all \(\partial J / \partial u^{(j)}\) for \(j > i\) have already been computed.

### 3.3 Common Misconception: Sum vs. Product

**Error:** Some students multiply gradients along all paths and then multiply the path-products together.

**Correction:** The chain rule multiplies along each path (sequentially) and then *sums* across paths (in parallel). Each path from \(u^{(i)}\) to \(J\) represents an independent causal mechanism. Their effects are additive, not multiplicative.

**Example of the error:** If \(u^{(i)}\) feeds into two children with local derivatives 2 and 3, and both children have downstream gradient 5, the correct total gradient is \(5 \cdot 2 + 5 \cdot 3 = 25\). The erroneous multiplication \(5 \cdot 2 \cdot 5 \cdot 3 = 150\) is dimensionally inconsistent and conceptually wrong.

**Try this yourself:** Before reading further, compute the gradient \(\partial J / \partial x\) for \(J = x^2 + x^3\) at \(x = 2\) using two methods: (1) differentiate the expression directly, and (2