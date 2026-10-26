## 3. Computational Graphs: A Visual Language for Function Composition

### 3.1 Intuition Before Formalism

Here’s a puzzle: you have a function with a million knobs, and you need to know exactly how much to turn each one to make the output improve. You can’t turn all the knobs at once and see what happens — that would take forever. So how do we assign credit to each knob?

A neural network is a composition of operations: matrix multiply, add bias, apply activation, repeat. We can represent this composition as a **directed acyclic graph** (DAG) where:

- **Nodes** are variables (inputs, intermediate results, parameters, and the final cost).
- **Edges** point from inputs to the operation that consumes them.

For a simple linear layer \( \mathbf{z} = \mathbf{W}\mathbf{x} + \mathbf{b} \), the graph looks like:

\[
\mathbf{x} \rightarrow [\text{matmul with } \mathbf{W}] \rightarrow \mathbf{W}\mathbf{x} \rightarrow [\text{add } \mathbf{b}] \rightarrow \mathbf{z}
\]

Here \( \mathbf{W}\mathbf{x} \) and \( \mathbf{z} \) are nodes; \( \mathbf{W} \) and \( \mathbf{b} \) are also nodes (parameters we will eventually differentiate with respect to). The operations live on the edges.

### 3.2 Analogy: A River Network

Think of the computational graph as a river system flowing downstream. Water (data) starts at mountain springs (inputs and parameters), merges at confluences (addition, multiplication), and eventually reaches the ocean (the cost function). The forward pass is water flowing downstream — we measure and record the flow rate at every junction.

The backward pass asks: "If I add one drop of water at the ocean, how much did each upstream spring contribute?" We work upstream from the ocean, and at every river split (where one upstream node feeds multiple downstream nodes), we divide our investigation along all branches. The chain rule is our conservation law: the total contribution must account for every path water could have taken.

This analogy captures the key insight: a single upstream node (like an early weight) can influence the final cost through many downstream routes, and backpropagation systematically traces every route exactly once.

**Try this yourself:** Before reading further, sketch what happens when a single upstream node feeds into *three* separate branches that later recombine. How many distinct paths connect that node to the final output? The answer will tell you how many terms the chain rule must sum over — and why deep networks amplify certain signals while diluting others.

### 3.3 Formal Definition

Let the graph have nodes \( \{u^{(1)}, u^{(2)}, \ldots, u^{(n)}\} \) sorted in **topological order**: every edge goes from an earlier node to a later node. The final node \( u^{(n)} \) is the scalar cost \( J \).

For any node \( u^{(i)} \), its value is computed by applying an operation to its **parents** — the nodes with edges pointing into it. We write:

\[
u^{(i)} = f^{(i)}\bigl(\text{Pa}(u^{(i)})\bigr)
\]

where \( \text{Pa}(u^{(i)}) \) denotes the set of parent nodes of \( u^{(i)} \). The function \( f^{(i)} \) is the operation associated with node \( i \), such as addition, multiplication, or element-wise application of \( \sigma \).

The gradient we ultimately want is \( \frac{\partial u^{(n)}}{\partial u^{(i)}} \) for every node that is a parameter.

### 3.4 The Chain Rule on the Graph

The chain rule tells us how a change in node \( u^{(i)} \) propagates to the final cost. It flows **forward through the children** of \( u^{(i)} \). Formally:

\[
\frac{\partial u^{(n)}}{\partial u^{(i)}} = \sum_{j: u^{(i)} \in \text{Pa}(u^{(j)})} \frac{\partial u^{(n)}}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

**Interpretation:** The gradient of the final cost with respect to node \( i \) is the sum, over all immediate children \( j \) of node \( i \), of (the gradient signal coming into child \( j \)) times (the local derivative of child \( j \) with respect to node \( i \)). This is a direct application of the multivariate chain rule: the total derivative is the sum of contributions along all paths from \( u^{(i)} \) to \( u^{(n)} \), and each path decomposes into a product of local Jacobians.

**Why the sum?** Node \( i \) can influence the final cost through multiple downstream paths. The chain rule adds up all those influences. Mathematically, if \( u^{(i)} \) is an input to multiple functions, the total derivative is the sum of partial derivatives through each function.

---

### Quick Check 1

Draw the computational graph for \( z = (x + y) \cdot (x - y) \). Label nodes for \( x, y, x+y, x-y, z \). Write the chain-rule expression for \( \frac{\partial z}{\partial x} \) by summing over the paths through the two children of \( x \). Compute it.

<details>
<summary>Solution</summary>

Graph: \( x \) and \( y \) are leaf nodes. \( u_1 = x+y \) and \( u_2 = x-y \) are children of both \( x \) and \( y \). \( z = u_1 \cdot u_2 \) is the final node.

\[
\frac{\partial z}{\partial x} = \frac{\partial z}{\partial u_1} \cdot \frac{\partial u_1}{\partial x} + \frac{\partial z}{\partial u_2} \cdot \frac{\partial u_2}{\partial x} = u_2 \cdot 1 + u_1 \cdot 1 = (x-y) + (x+y) = 2x
\]
</details>

---

## 4. The Backpropagation Algorithm in Two Phases

### 4.1 Phase 1 — Forward Propagation: Compute and Store

We traverse the graph in topological order (input to output). For each node \( u^{(i)} \):

1. Retrieve the current values of its parents (already computed and stored).
2. Compute \( u^{(i)} \) using its operation.
3. **Store \( u^{(i)} \)** in memory.

At the end, we have the scalar cost \( J = u^{(n)} \) and every intermediate activation stored.

**Why store everything?** Because during the backward pass, we need these values to evaluate local derivatives. For example, the derivative of \( \sigma(z) \) with respect to \( z \) is \( \sigma(z)(1 - \sigma(z)) \), which depends on the value of \( z \) that we computed in the forward pass. Without storing \( z \), we would need to recompute it — precisely the redundancy we aim to avoid.

### 4.2 Phase 2 — Backward Propagation: Accumulate Gradients

We now traverse the graph in **reverse topological order** (output back to inputs). We maintain a gradient accumulator for each node:

\[
\bar{u}^{(i)} \equiv \frac{\partial u^{(n)}}{\partial u^{(i)}}
\]

**Initialization:** At the output node, \( \bar{u}^{(n)} = \frac{\partial J}{\partial J} = 1 \).

**For each node \( u^{(i)} \) in reverse order:**

We already know the gradient signals \( \bar{u}^{(j)} \) for all its **children** (since children come later in topological order, they are processed earlier in reverse order). We compute:

\[
\bar{u}^{(i)} = \sum_{j \in \text{children}(i)} \bar{u}^{(j)} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

**Key detail:** The local Jacobian \( \frac{\partial u^{(j)}}{\partial u^{(i)}} \) is evaluated using the **stored values** from the forward pass. This is what prevents redundant recomputation. Note that \( \frac{\partial u^{(j)}}{\partial u^{(i)}} \) may be a scalar, vector, or matrix depending on the shapes of \( u^{(i)} \) and \( u^{(j)} \); the product \( \bar{u}^{(j)} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}} \) must respect matrix multiplication rules and produce a result with the same shape as \( u^{(i)} \).

### 4.3 Handling Parameters

Parameters like \( \mathbf{W} \) and \( \mathbf{b} \) are leaf nodes with no parents. Their gradients are computed exactly as above: they receive gradient signals from their children. Once we have \( \bar{\mathbf{W}} \) and \( \bar{\mathbf{b}} \), we can update them with an optimizer. The parameter nodes themselves do not require gradient computation in the backward pass (since they have no parents), but their gradients are accumulated from their children exactly as described.

### 4.4 The Two-Phase Algorithm: A Concrete Walkthrough

Let's trace through a tiny network to see the algorithm in action.

**Network:**
- Input: \( x \in \mathbb{R} \) (scalar for simplicity)
- Hidden: \( h = \sigma(w_1 x + b_1) \), where \( w_1, b_1 \in \mathbb{R} \)
- Output: \( \hat{y} = w_2 h + b_2 \), where \( w_2, b_2 \in \mathbb{R} \)
- Cost: \( J = \frac{1}{2}(\hat{y} - y)^2 \) (MSE with target \( y \))

**Step 1: Build the computational graph.** Nodes: \( x, w_1, b_1, a_1 = w_1 x + b_1, h = \sigma(a_1), w_2, b_2, \hat{y} = w_2 h + b_2, J \).

**Step 2: Forward pass.** Compute and store each node's value in topological order:
- \( a_1 = w_1 x + b_1 \)
- \( h = \sigma(a_1) \)
- \( \hat{y} = w_2 h + b_2 \)
- \( J = \frac{1}{2}(\hat{y} - y)^2 \)

**Step 3: Backward pass.** Start at \( J \), work backwards.

\[
\bar{J} = \frac{\partial J}{\partial J} = 1
\]
\[
\bar{\hat{y}} = \frac{\partial J}{\partial \hat{y}} = \hat{y} - y \quad \text{(since } \frac{\partial}{\partial \hat{y}} \frac{1}{2}(\hat{y} - y)^2 = \hat{y} - y \text{)}
\]
\[
\bar{w}_2 = \bar{\hat{y}} \cdot \frac{\partial \hat{y}}{\partial w_2} = (\hat{y} - y) \cdot h \quad \text{(since } \frac{\partial}{\partial w_2}(w_2 h + b_2) = h \text{)}
\]
\[
\bar{b}_2 = \bar{\hat{y}} \cdot \frac{\partial \hat{y}}{\partial b_2} = (\hat{y} - y) \cdot 1 = \hat{y} - y \quad \text{(since } \frac{\partial}{\partial b_2}(w_2 h + b_2) = 1 \text{)}
\]
\[
\bar{h} = \bar{\hat{y}} \cdot \frac{\partial \hat{y}}{\partial h} = (\hat{y} - y) \cdot w_2 \quad \text{(since } \frac{\partial}{\partial h}(w_2 h + b_2) = w_2 \text{)}
\]
\[
\bar{a}_1 = \bar{h} \cdot \frac{\partial h}{\partial a_1} = \bar{h} \cdot \sigma'(a_1) \quad \text{(since } h = \sigma(a_1) \text{)}
\]
\[
\bar{w}_1 = \bar{a}_1 \cdot \frac{\partial a_1}{\partial w_1} = \bar{a}_1 \cdot x \quad \text{(since } \frac{\partial}{\partial w_1}(w_1 x + b_1) = x \text{)}
\]
\[
\bar{b}_1 = \bar{a}_1 \cdot \frac{\partial a_1}{\partial b_1} = \bar{a}_1 \cdot 1 = \bar{a}_1 \quad \text{(since } \frac{\partial}{\partial b_1}(w_1 x + b_1) = 1 \text{)}
\]

**Observe the pattern:** Each step multiplies an incoming gradient signal by a local derivative evaluated on stored forward-pass values. No node's value is recomputed. The gradient with respect to each parameter is a scalar (since all quantities are scalars here), but the pattern generalizes directly to vector and matrix cases.

### 4.5 The Surprising Symmetry: Forward Stores, Backward Reads

Notice something elegant: the forward pass writes values in order (1, 2, 3, ..., n), and the backward pass reads those stored values in exactly reverse order (n, n-1, ..., 1). This is not a coincidence — it's a deep structural property. The forward pass is building a stack of intermediate results, and the backward pass is popping that stack. This is why backpropagation feels like "unrolling" the computation: you're literally retracing your steps, using the footprints you left on the way forward.

**Try this yourself:** Take the tiny network from Section 4.4 and deliberately corrupt one stored value (say, set \( a_1 \) to zero after the forward pass but before the backward pass). Which gradients change, and which remain correct? This exercise reveals exactly which local derivatives depend on which stored values — and why selective recomputation (checkpointing, Section 5.2) can work.

---

## 5. The Memory-Time Tradeoff: Why We Don't Recompute

### 5.1 The Tension

The algorithm we've described stores every intermediate activation. For a network with a million hidden units across ten layers, that's tens of millions of floating-point numbers. This is the memory cost of backpropagation.

**Why not just recompute intermediates during the backward pass?** That would save memory but cost time — potentially a lot of it. Imagine recomputing the activations of layer 1 for every gradient that flows through it. In a deep network, layer 1's activations would be recomputed once per downstream path, leading to a runtime that scales quadratically or worse with depth.

### 5.2 The Resolution: Checkpointing

There is a spectrum between "store everything" and "recompute everything." **Gradient checkpointing** (also called "activation recomputation") stores only a subset of activations — say, one per layer — and recomputes the rest on demand during the backward pass. This trades a modest increase in compute for a large reduction in memory. The backpropagation framework we're building generalizes cleanly to this: the same local derivative formulas apply, but some stored values are replaced by recomputed ones. For a network with \( L \) layers, storing activations at every \( \sqrt{L} \) layers reduces memory from \( O(L) \) to \( O(\sqrt{L}) \) while increasing computation by at most a factor of 2.

---

## 6. Advanced Variants of Backpropagation

The standard backpropagation algorithm described above computes exact gradients for the full batch of training data. Several advanced variants have been developed to address specific computational, numerical, or structural challenges.

### 6.1 Truncated Backpropagation Through Time (TBPTT)

When training recurrent neural networks (RNNs) on long sequences, applying standard backpropagation through time (BPTT) — which unrolls the network over the entire sequence length — becomes computationally prohibitive. A sequence of length \( T \) produces a computational graph of depth \( T \), and the memory required to store all intermediate hidden states scales as \( O(T) \).

**Truncated BPTT** addresses this by splitting the sequence into subsequences of fixed length \( k \) (e.g., \( k = 20 \) or \( 50 \)). The forward and backward passes are performed over each subsequence independently. Crucially, the final hidden state from one subsequence is passed as the initial state to the next subsequence, but gradients are not propagated across subsequence boundaries. Formally, for a subsequence spanning time steps \( t \) to \( t+k-1 \), the gradient of the loss \( L \) with respect to a parameter \( \theta \) is:

\[
\frac{\partial L}{\partial \theta} \approx \sum_{\tau = t}^{t+k-1} \frac{\partial L_\tau}{\partial \mathbf{h}_\tau} \cdot \frac{\partial \mathbf{h}_\tau}{\partial \theta}
\]

where \( \mathbf{h}_\tau \) is the hidden state at time \( \tau \), and the dependence of \( \mathbf{h}_\tau \) on \( \mathbf{h}_{t-1} \) is treated as constant (gradients are truncated). This approximation discards long-range dependencies beyond the truncation window, which can prevent the network from learning dependencies spanning more than \( k \) steps. However, it bounds memory and computation to \( O(k) \) per subsequence, making training on long sequences feasible.

### 6.2 Gradient Accumulation for Large Effective Batch Sizes

When GPU memory is insufficient to process a desired batch size in a single forward-backward pass, **gradient accumulation** simulates a larger batch by splitting it into micro-batches. For a target batch size \( B \) split into \( m \) micro-batches of size \( B/m \), the procedure is:

1. For each micro-batch \( i \), perform a forward pass, compute the loss \( L_i \), and perform a backward pass to obtain the gradient \( \nabla_{\boldsymbol{\theta}} L_i \).
2. Accumulate the gradient: \( \mathbf{g} \leftarrow \mathbf{g} + \nabla_{\boldsymbol{\theta}} L_i \).
3. After processing all \( m \) micro-batches, update the parameters: \( \boldsymbol{\theta} \leftarrow \boldsymbol{\theta} - \eta \cdot \frac{1}{m} \mathbf{g} \).

This works because the gradient of the sum of losses over a batch equals the sum of the gradients of the individual losses (by linearity of differentiation). The effective batch size is \( B \), but the peak memory footprint is that of a single micro-batch. Note that this is not an approximation — it computes the exact batch gradient, provided the loss is averaged appropriately. However, operations like Batch Normalization, which compute statistics over the batch dimension, will use micro-batch statistics rather than full-batch statistics, introducing a discrepancy.

### 6.3 Synthetic Gradients and Decoupled Neural Interfaces

Standard backpropagation requires the forward pass to complete (producing the loss) before the backward pass can begin, creating a **backward locking** constraint: no layer can update its parameters until all subsequent layers have finished both their forward and backward computations. This sequential dependency limits parallelism.

**Synthetic gradients** break this dependency by training each layer (or module) to predict its own gradient signal locally, without waiting for the true gradient from downstream. For a layer with output \( \mathbf{h}_i \), a synthetic gradient model \( M_i \) predicts \( \hat{\mathbf{g}}_i \approx \frac{\partial L}{\partial \mathbf{h}_i} \). The layer can then update its parameters immediately using \( \hat{\mathbf{g}}_i \), while the true gradient \( \mathbf{g}_i \) (computed later via backpropagation) is used only to train the synthetic gradient model \( M_i \), minimizing \( \| M_i(\mathbf{h}_i) - \mathbf{g}_i \|^2 \).

This **decoupled neural interface** allows layers to be updated asynchronously and in parallel, potentially accelerating training on distributed systems. However, the quality of the synthetic gradient model is critical: poor predictions introduce bias and noise, potentially destabilizing training. In practice, synthetic gradients are an active research area and are not yet a standard replacement for true backpropagation.

### 6.4 Second-Order Backpropagation (Hessian-Vector Products)

While standard backpropagation computes first-order gradients \( \nabla