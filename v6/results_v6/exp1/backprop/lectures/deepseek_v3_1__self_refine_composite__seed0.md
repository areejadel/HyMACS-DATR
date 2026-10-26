# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** the definition of the adjoint (error signal) and state the backpropagation recurrence for a directed acyclic computation graph.
2. **Understand** why naive gradient computation is exponentially expensive, and explain how dynamic programming in backpropagation achieves linear-time complexity.
3. **Apply** the backpropagation algorithm to compute all parameter gradients for a two-layer neural network with cross-entropy loss, and verify selected gradients numerically.
4. **Analyze** a given computational graph to determine which intermediate values must be stored during the forward pass for use in the backward pass.
5. **Evaluate** how activation functions, weight initialization, and skip connections affect gradient flow, and diagnose vanishing or exploding gradients in a simple network.

---

## 1. Foundations: Why We Need Backpropagation

**Opening Challenge.** Imagine you are a sculptor carving a statue from a block of marble. Every tap of the chisel affects the final form, but the effect of any single tap depends on every tap that came before it. Now replace the chisel with 175 billion taps — one for each parameter in GPT-3 — and replace the block of marble with a computation graph containing a trillion intermediate values. How do you figure out which tap to adjust, and by how much, to make the final statue match your vision? This is the gradient computation problem at the heart of training neural networks. The naive approach — tracing every path from every tap to the final form — would take longer than the age of the universe. Backpropagation solves it in seconds.

### 1.1 Prerequisites

We begin by reviewing the core tools used throughout this lecture.

**Linear Algebra**

- **Matrix multiplication shapes:** If \(A\) is \(m \times n\) and \(B\) is \(n \times p\), then \(AB\) is \(m \times p\). The inner dimensions must match.
- **Transpose rule:** \((AB)^T = B^T A^T\).
- **Element-wise (Hadamard) product:** Denoted \(\odot\). For vectors \(\mathbf{a}\) and \(\mathbf{b}\) of the same size, \((\mathbf{a} \odot \mathbf{b})_i = a_i b_i\).

**Multivariate Calculus**

- **Gradient vector:** For a scalar function \(J(\theta)\) with parameters \(\theta \in \mathbb{R}^P\), the gradient \(\nabla_\theta J\) is a vector of all \(P\) partial derivatives:
  \[
  \nabla_\theta J = \left[\frac{\partial J}{\partial \theta_1}, \frac{\partial J}{\partial \theta_2}, \dots, \frac{\partial J}{\partial \theta_P}\right]^T.
  \]
- **Chain rule (scalar):** If \(J = f(g(h(\theta)))\), then
  \[
  \frac{\partial J}{\partial \theta} = \frac{\partial J}{\partial f} \cdot \frac{\partial f}{\partial g} \cdot \frac{\partial g}{\partial h} \cdot \frac{\partial h}{\partial \theta}.
  \]
- **Chain rule (vector):** When propagating gradients through \(\mathbf{v} = f(\mathbf{u})\), we use the Jacobian matrix \(\frac{\partial \mathbf{v}}{\partial \mathbf{u}}\) with entries \(\left[\frac{\partial \mathbf{v}}{\partial \mathbf{u}}\right]_{ij} = \frac{\partial v_i}{\partial u_j}\). The gradient of a downstream scalar \(J\) with respect to \(\mathbf{u}\) is
  \[
  \nabla_{\mathbf{u}} J = \left(\frac{\partial \mathbf{v}}{\partial \mathbf{u}}\right)^T \nabla_{\mathbf{v}} J.
  \]
  This pattern recurs throughout the derivation.

**Neural Network Training Loop**

- We have a dataset \(\mathcal{D} = \{(\mathbf{x}^{(i)}, \mathbf{y}^{(i)})\}_{i=1}^N\).
- We define a scalar loss
  \[
  J(\theta) = \frac{1}{N}\sum_{i=1}^N L(f(\mathbf{x}^{(i)}; \theta), \mathbf{y}^{(i)})
  \]
  that measures prediction error.
- We update parameters iteratively via gradient descent:
  \[
  \theta^{(t+1)} = \theta^{(t)} - \eta \nabla_\theta J(\theta^{(t)}),
  \]
  where \(\eta\) is the learning rate.

> **Quick Check 1: Prerequisites**
>
> Given \(\mathbf{z} = W \mathbf{x} + \mathbf{b}\) where \(W \in \mathbb{R}^{3 \times 4}\), \(\mathbf{x} \in \mathbb{R}^4\), and \(\mathbf{b} \in \mathbb{R}^3\):
> 1. What is the shape of \(\mathbf{z}\)?
> 2. If \(J\) is a scalar and \(\nabla_{\mathbf{z}} J \in \mathbb{R}^3\), what is \(\nabla_{\mathbf{x}} J\) in terms of \(W\) and \(\nabla_{\mathbf{z}} J\)?
>
> *(Answers: 1. \(\mathbf{z} \in \mathbb{R}^3\). 2. \(\nabla_{\mathbf{x}} J = W^T \nabla_{\mathbf{z}} J\). We derive this pattern in Section 3.)*

### 1.2 The Problem: Gradients at Scale

Consider a neural network with \(P\) parameters, where \(P\) can reach hundreds of billions. Training requires \(\nabla_\theta J\) — all \(P\) partial derivatives. The chain rule decomposes each \(\frac{\partial J}{\partial \theta_k}\) into a product of local Jacobians along every path from parameter \(\theta_k\) to the loss \(J\). A deep network with branching factor \(B\) and depth \(L\) can have \(B^L\) distinct paths. Evaluating each path independently costs exponential time, which is infeasible for any realistic network.

**Try this yourself:** Draw a small network with just 3 layers, each containing 3 neurons, fully connected. Count how many distinct paths connect a single weight in layer 1 to the output loss. Now imagine doing this for a 100-layer network. This combinatorial explosion is what makes the naive approach impossible.

The solution is dynamic programming. Many paths share intermediate sub-expressions. If we compute \(\frac{\partial J}{\partial \mathbf{a}^{[l]}}\) (the gradient with respect to activations at layer \(l\)), we can reuse it for all parameters in earlier layers. This is the key insight of backpropagation: compute gradients from the output backward, cache each intermediate gradient exactly once, and accumulate contributions from all downstream paths.

**Analogy: Electrical grid load balancing.** Imagine you need to determine how much each of thousands of power plants contributes to the total current flowing through a single transmission line in a complex electrical grid. You could trace every possible path from each plant to that line — an exponential nightmare. Or you could start at the transmission line and work backward, applying Kirchhoff's current law at each junction: the current entering a junction equals the current leaving it. By traversing the grid once in reverse, you decompose the total current into each plant's contribution in linear time. Backpropagation does the same thing for gradients: the loss is your "total current," the adjoints are the "currents" flowing backward through the computation graph, and the local Jacobians are the "conductance ratios" at each node.

Training GPT-3 (175 billion parameters) requires computing \(\nabla_\theta J\) over a computation graph with roughly \(10^{12}\) nodes per batch. Backpropagation guarantees the backward pass costs only 2–3× the forward pass, regardless of depth. Without this algorithm, deep learning at scale would not exist.

> **Misconception Alert: "Backpropagation is just the chain rule."**
>
> The chain rule specifies *what* to compute. Backpropagation specifies *how to organize the computation* to avoid exponential redundancy. It is an algorithm for efficiently evaluating the chain rule on a DAG using dynamic programming — structurally identical to the Viterbi algorithm for HMMs and the sum-product algorithm for factor graphs. The same design pattern appears in reinforcement learning (temporal difference learning) and optimal control (the adjoint method for Pontryagin's maximum principle): propagate a "costate" backward through a dynamical system to compute sensitivities in linear time.

---

## 2. Computational Graphs and the Backpropagation Recurrence

### 2.1 Representing Computation as a Graph

Every neural network computation can be drawn as a **directed acyclic graph (DAG)** \(\mathcal{G} = (\mathcal{V}, \mathcal{E})\):

- **Nodes** \(v_i \in \mathcal{V}\) represent variables: inputs, parameters, intermediate results, and the final loss.
- **Directed edges** \(v_i \to v_j\) mean "\(v_i\) is an immediate input to the function that produces \(v_j\)."
- Each node \(v_j\) with parents \(\text{Pa}(v_j)\) is computed as \(v_j = f_j(\text{Pa}(v_j))\).

**Example:** Let \(J = (w \cdot x) + b\).

- \(v_1 = w\) (parameter)
- \(v_2 = x\) (input)
- \(v_3 = v_1 \cdot v_2\) (multiplication)
- \(v_4 = b\) (parameter)
- \(v_5 = v_3 + v_4 = J\) (addition, output)

Edges: \(v_1 \to v_3\), \(v_2 \to v_3\), \(v_3 \to v_5\), \(v_4 \to v_5\).

The **forward pass** evaluates nodes in topological order (parents before children): \(v_1, v_2, v_3, v_4, v_5\). We store each node's value for use in the backward pass.

**Why this matters beyond neural networks:** The same DAG formalism describes how compilers optimize expressions (common subexpression elimination), how database query planners organize joins, and how spreadsheets propagate updates (Excel's dependency graph is a DAG). In each case, the insight is identical: represent computation as a graph, then exploit its structure to avoid redundant work.

### 2.2 The Adjoint and the Backpropagation Recurrence

Define the **adjoint** (error signal) of node \(v_i\) as:

\[
\delta_i = \frac{\partial J}{\partial v_i}.
\]

For the output node \(v_{\text{out}} = J\), we have \(\delta_{\text{out}} = \frac{\partial J}{\partial J} = 1\).

For any other node \(v_i\), the multivariate chain rule states that \(v_i\) influences \(J\) through all its children. Each child \(v_j\) contributes its adjoint \(\delta_j\) multiplied by the local Jacobian \(\frac{\partial v_j}{\partial v_i}\):

\[
\delta_i = \sum_{j \in \text{Children}(v_i)} \frac{\partial J}{\partial v_j} \cdot \frac{\partial v_j}{\partial v_i}
        = \sum_{j \in \text{Children}(v_i)} \delta_j \cdot \frac{\partial v_j}{\partial v_i}.
\]

The adjoint \(\delta_i\) answers: "If I perturb \(v_i\) by a tiny amount, how much does the final loss \(J\) change?" The answer sums the influence through every downstream path. Because we traverse nodes in *reverse* topological order, when we process \(v_i\), all its children have already computed their adjoints \(\delta_j\). We multiply by the local Jacobian \(\frac{\partial v_j}{\partial v_i}\) (which depends only on \(f_j\) and the stored forward-pass values) and sum.

When \(v_i\) and \(v_j\) are vectors, \(\delta_i\) and \(\delta_j\) are vectors, and \(\frac{\partial v_j}{\partial v_i}\) is a matrix. The contribution from child \(v_j\) is \(\left(\frac{\partial v_j}{\partial v_i}\right)^T \delta_j\), which propagates a column vector backward through the transpose of the Jacobian.

**Cross-domain connection — the postal service model of gradient flow.** Think of the forward pass as mailing a package through a network of sorting facilities. Each facility (node) processes the package and sends it to the next facility. The backward pass is like tracing the package's route in reverse to figure out which facilities contributed to a delay. At each facility, you look at the incoming delay report (the adjoint from downstream) and use the facility's local processing rules (the Jacobian) to determine how much of that delay traces to each incoming shipment. The key realization: you don't need to trace every possible package path from the origin — you just need to walk backward through the facilities once, splitting the delay attribution at each stop.

### 2.3 The Algorithm

**Forward Pass:**
1. Topologically sort all nodes.
2. For each node \(v_j\) in order:
   - Compute \(v_j = f_j(\text{Pa}(v_j))\).
   - Store \(v_j\) in memory.

**Backward Pass:**
1. Initialize \(\delta_{\text{out}} = 1\) (assuming scalar output \(J\)).
2. For each node \(v_j\) in **reverse** topological order:
   - For each parent \(v_i \in \text{Pa}(v_j)\):
     - Compute the local Jacobian \(\frac{\partial v_j}{\partial v_i}\) using stored forward values.
     - Accumulate: \(\delta_i \leftarrow \delta_i + \left(\frac{\partial v_j}{\partial v_i}\right)^T \delta_j\).

After the backward pass, every parameter node holds its gradient: \(\delta_k = \frac{\partial J}{\partial v_k}\).

**Time complexity:** Each edge's local Jacobian is computed exactly once. If the forward pass costs \(F\) operations, the backward pass costs \(O(F)\) — typically 2–3× the forward pass.

**Try this yourself:** Before reading the worked example below, take the expression \(J = (a \cdot b) + (a \cdot c)\) and try writing down what you think the backward pass should compute. Where does the gradient for \(a\) get contributions from? This exercise reveals the accumulation pattern that makes backpropagation work.

### 2.4 Worked Example: Shared Inputs and Gradient Accumulation

We now examine a case where one input feeds into multiple operations — a pattern that appears whenever weights or activations are reused (e.g., convolutional kernels, recurrent connections, attention).

**Setup:** \(J = (a \cdot b) + (a \cdot c)\) with \(a=2, b=3, c=4\).

**Step 1: Build the computation graph.**

- \(v_1 = a = 2\)
- \(v_2 = b = 3\)
- \(v_3 = c = 4\)
- \(v_4 = v_1 \cdot v_2 = 6\)
- \(v_5 = v_1 \cdot v_3 = 8\)
- \(v_6 = v_4 + v_5 = 14 = J\)

Edges: \(v_1 \to v_4\), \(v_2 \to v_4\), \(v_1 \to v_5\), \(v_3 \to v_5\), \(v_4 \to v_6\), \(v_5 \to v_6\).

**Step 2: Forward pass.** Compute and store each node's value (shown above).

**Step 3: Backward pass.** Traverse in reverse topological order: \(v_6, v_5, v_4, v_3, v_2, v_1\).

- **Process \(v_6\) (output):** \(\delta_6 = \frac{\partial J}{\partial v_6} = 1\).

- **Process \(v_6\)'s parents (\(v_4, v_5\)):** \(v_6 = v_4 + v_5\), so \(\frac{\partial v_6}{\partial v_4} = 1\) and \(\frac{\partial v_6}{\partial v_5} = 1\).
  - \(\delta_4 = \delta_6 \cdot 1 = 1\)
  - \(\delta_5 = \delta_6 \cdot 1 = 1\)

- **Process \(v_5\):** \(v_5 = v_1 \cdot v_3\). Local derivatives: \(\frac{\partial v_5}{\partial v_1} = v_3 = 4\), \(\frac{\partial v_5}{\partial v_3} = v_1 = 2\).
  - \(\delta_1 \leftarrow \delta_1 + \delta_5 \cdot 4 = 0 + 4 = 4\) *(first contribution to \(\delta_1\))*
  - \(\delta_3 = \delta_5 \cdot 2 = 2\)

- **Process \(v_4\):** \(v_4 = v_1 \cdot v_2\). Local derivatives: \(\frac{\partial v_4}{\partial v_1} = v_2 = 3\), \(\frac{\partial v_4}{\partial v_2} = v_1 = 2\).
  - \(\delta_1 \leftarrow \delta_1 + \delta_4 \cdot 3 = 4 + 3 = 7\) *(second contribution, accumulated)*
  - \(\delta_2 = \delta_4 \cdot 2 = 2\)

- **Process \(v_3, v_2, v_1\):** Leaf nodes; no further accumulation.

**Step 4: Verify analytically.** \(J = ab + ac\), so:
- \(\frac{\partial J}{\partial a} = b + c = 3 + 4 = 7\) ✓
- \(\frac{\partial J}{\partial b} = a = 2\) ✓
- \(\frac{\partial J}{\partial c} = a = 2\) ✓

**Key takeaway:** The gradient for \(a\) received contributions from both paths (\(v_1 \to v_4 \to v_6\) and \(v_1 \to v_5 \to v_6\)). The accumulation at node \(v_1\) correctly sums them. This is why we initialize adjoints to zero and use `+=` — shared parameters accumulate gradients from all their uses.

> **Quick Check 2: Graph Tracing**
>
> Draw the computation graph for \(J = (x + y) \cdot z\). Identify all nodes and edges. Using the recurrence, compute \(\frac{\partial J}{\partial x}\), \(\frac{\partial J}{\partial y}\), and \(\frac{\partial J}{\partial z}\) for \(x=1, y=2, z=3\). Verify analytically.
>
> *(You should obtain \(\frac{\partial J}{\partial x} = z = 3\), \(\frac{\partial J}{\partial y} = z = 3\), \(\frac{\partial J}{\partial z} = x+y = 3\).)*

---

## 3. Full Derivation: Two-Layer Network with Cross-Entropy Loss

Having established the backpropagation recurrence, we now apply it to a realistic classification network.

### 3.1 Architecture and Notation

We consider a two-layer network for \(K\)-class classification:

\[
\begin{aligned}
\mathbf{z}^{[1]} &= W^{[1]} \mathbf{x} + \mathbf{b}^{[1]} \quad &\text{(hidden pre-activation)} \\
\mathbf{a}^{[1]} &= \sigma(\mathbf{z}^{[1]}) \quad &\text{(hidden activation)} \\
\mathbf{z}^{[2]} &= W^{[2]} \mathbf{a}^{[1]} + \mathbf{b}^{[2]} \quad &\text{(output pre-activation)} \\
\hat{\mathbf{y}} &= \text{softmax}(\mathbf{z}^{[2]}) \quad &\text{(predicted probabilities)} \\
J &= -\sum_{k=1}^{K} y_k \log(\hat{y}_k) \quad &\text{(cross-entropy loss)}
\end{aligned}
\]

**Dimensions:**

- Input: \(\mathbf{x} \in \mathbb{R}^d\)
- Hidden layer: \(W^{[1]} \in \mathbb{R}^{h \times d}\), \(\mathbf{b}^{[1]} \in \mathbb{R}^h\), so \(\mathbf{z}^{[1]}, \mathbf{a}^{[1]} \in \mathbb{R}^h\)
- Output layer: \(W^{[2]} \in \mathbb{R}^{K \times h}\), \(\mathbf{b}^{[2]} \in \mathbb{R}^K\), so \(\mathbf{z}^{[2]}, \hat{\mathbf{y}} \in \mathbb{R}^K\)