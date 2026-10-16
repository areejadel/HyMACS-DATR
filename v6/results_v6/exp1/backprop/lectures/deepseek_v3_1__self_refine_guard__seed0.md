# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Define** the adjoint (error signal) \(\delta_i = \frac{\partial J}{\partial v_i}\) and state the backpropagation recurrence \(\delta_i = \sum_{j \in \text{Children}(i)} \delta_j \cdot \frac{\partial v_j}{\partial v_i}\).
2. **Explain** why naive gradient computation has exponential cost in branching networks, and how backpropagation’s dynamic programming reduces this to linear time.
3. **Apply** the backpropagation algorithm by hand to compute all parameter gradients for a two-layer neural network with sigmoid activation and mean squared error loss, and verify the results using finite-difference checks.
4. **Analyze** a computational graph to identify which forward-pass values must be stored for the backward pass and which gradient computations can be parallelized across independent branches.
5. **Evaluate** the risk of vanishing or exploding gradients given an architecture’s depth, activation functions, and weight initialization strategy, and propose appropriate mitigations.

---

## 1. Foundations: Why We Need Backpropagation

### 1.0 Opening Hook: The $100 Million Typo

In 2012, a team at Google trained a neural network on 10 million images from YouTube videos. Without anyone telling it what a cat looks like, the network learned to recognize cats with 74.8% accuracy — a breakthrough in unsupervised learning. The training required 16,000 CPU cores running for three days.

Now imagine a naive implementation of that same network. If gradients were computed by independently tracing every path from each neuron to the loss — expanding the chain rule along every branch — the computation would require evaluating more distinct paths than there are atoms in the observable universe. The training run would outlast the sun.

Yet 16,000 cores finished in three days. The difference between "heat death of the universe" and "three days" is backpropagation. What follows is the algorithm that makes that difference possible — not through approximation or shortcuts, but by recognizing that most of those paths share identical subcomputations that need only be evaluated once.

---

### 1.1 Prerequisites Review

We begin by recalling the essential tools used throughout this lecture.

**Linear Algebra Essentials**

- **Matrix multiplication shapes**: If \(A \in \mathbb{R}^{m \times n}\) and \(B \in \mathbb{R}^{n \times p}\), then \(AB \in \mathbb{R}^{m \times p}\). The inner dimensions must match (\(n\)); the result takes the outer dimensions (\(m \times p\)).
- **Transpose rule**: \((AB)^T = B^T A^T\). The reversal of order is important when propagating gradients backward.
- **Element-wise (Hadamard) product**: Denoted by \(\odot\). If \(u, v \in \mathbb{R}^n\), then \((u \odot v)_i = u_i v_i\). This product appears whenever we differentiate activation functions applied element-wise.

**Quick self-check**: If \(W \in \mathbb{R}^{5 \times 3}\) and \(x \in \mathbb{R}^3\), the shape of \(Wx\) is \(5 \times 1\) and the shape of \(x^T W^T\) is \(1 \times 5\).

**Multivariate Calculus Essentials**

- **Chain rule for scalar functions of vectors**: If \(J = f(g(x))\) with \(x \in \mathbb{R}^n\), \(g: \mathbb{R}^n \rightarrow \mathbb{R}^m\), and \(f: \mathbb{R}^m \rightarrow \mathbb{R}\), then \(\nabla_x J = (\nabla_x g)^T \nabla_g J\), where \(\nabla_x g\) is the \(m \times n\) Jacobian matrix of partial derivatives.
- **Sigmoid derivative**: For \(\sigma(z) = \frac{1}{1+e^{-z}}\), we have \(\sigma'(z) = \sigma(z)(1-\sigma(z))\). This form lets us compute the derivative directly from the function value stored during the forward pass, avoiding recomputation of exponentials.
- **MSE gradient**: For scalar mean squared error \(J = \frac{1}{2}(\hat{y} - y)^2\), we have \(\frac{\partial J}{\partial \hat{y}} = \hat{y} - y\).

**Worked warm-up**: Let \(J = \frac{1}{2}(\sigma(wx + b) - y)^2\) with \(w=2, b=1, x=0.5, y=1\).

Forward pass:
- \(z = 2(0.5) + 1 = 2\)
- \(\hat{y} = \sigma(2) \approx 0.8808\)
- \(J = \frac{1}{2}(0.8808 - 1)^2 \approx 0.0071\)

Backward pass (chain rule):
- \(\frac{\partial J}{\partial \hat{y}} = 0.8808 - 1 = -0.1192\)
- \(\frac{\partial \hat{y}}{\partial z} = 0.8808(1-0.8808) \approx 0.1050\)
- \(\frac{\partial J}{\partial z} = (-0.1192)(0.1050) \approx -0.0125\)
- \(\frac{\partial J}{\partial w} = \frac{\partial J}{\partial z} \cdot x = (-0.0125)(0.5) = -0.00625\)
- \(\frac{\partial J}{\partial b} = \frac{\partial J}{\partial z} \cdot 1 = -0.0125\)

**Try it yourself**: Recompute with \(w=1, b=0, x=1, y=2\). Verify that \(\frac{\partial J}{\partial w} \approx 0.149\) and \(\frac{\partial J}{\partial b} \approx 0.149\).

**Neural Network Training Loop**

We assume familiarity with the standard training procedure: given a dataset of input–target pairs \(\{(x^{(i)}, y^{(i)})\}_{i=1}^{N}\), a parameterized model \(f_\theta\), and a scalar loss \(J(\theta) = \frac{1}{N}\sum_i \mathcal{L}(f_\theta(x^{(i)}), y^{(i)})\), we update parameters via gradient descent: \(\theta \leftarrow \theta - \eta \nabla_\theta J\). The challenge we address today is computing \(\nabla_\theta J\) efficiently when \(f_\theta\) is a deep neural network with millions of parameters.

---

### 1.2 The Computational Challenge

**Why the naive approach fails**

Consider a deeply nested function \(J = f_{100}(f_{99}(\dots f_1(x)\dots))\). The chain rule gives:

\[
\frac{dJ}{dx} = f_{100}'(v_{99}) \cdot f_{99}'(v_{98}) \cdot \dots \cdot f_1'(x)
\]

For a simple chain, this product can be evaluated directly. Neural networks, however, are branching structures. When one neuron’s output fans out to \(K\) neurons in the next layer, a naive expansion of the chain rule must trace every path from that neuron to the loss. With \(L\) layers and branching factor \(K\), there are \(K^L\) distinct paths. Computing each independently requires exponential time.

**Analogy: The Fibonacci recurrence**

This is the same problem as computing Fibonacci numbers via naive recursion:

```
fib(n):
    if n <= 1: return n
    return fib(n-1) + fib(n-2)
```

This approach recomputes `fib(2)` exponentially many times. The solution is dynamic programming: compute each subproblem once, store the result, and reuse it. Computing bottom-up — `fib(0), fib(1), fib(2), …, fib(n)` — takes \(O(n)\) time instead of \(O(2^n)\).

**Backpropagation as dynamic programming for derivatives**

Backpropagation applies the same insight to gradient computation. Derivatives are computed in reverse order from the output, and each intermediate derivative (called an **adjoint**) is stored exactly once. When a value influences the loss through multiple paths, the gradient contributions from all paths are accumulated by summing them; each local derivative is evaluated exactly once. The total computation is proportional to the forward-pass cost.

**Pause and predict**: Before reading further, consider a network with 3 layers, each containing 4 neurons, fully connected. Each neuron in layer \(i\) connects to all 4 neurons in layer \(i+1\). How many distinct paths exist from a single neuron in layer 1 to the loss? How many times would a naive chain-rule expansion evaluate the derivative of the activation function in layer 3?

---

### 1.3 Warm-Up: Three Functions in Sequence

Consider \(J\) computed from a scalar input \(x\) through three differentiable functions:

\[
v_1 = f_1(x), \qquad v_2 = f_2(v_1), \qquad J = f_3(v_2)
\]

**Forward pass** (with \(x = 2\)): Compute \(v_1 = f_1(2)\), \(v_2 = f_2(v_1)\), \(J = f_3(v_2)\), storing each intermediate value for the backward pass.

**Backpropagation**: Work backward from the output, computing how much \(J\) changes with respect to each intermediate value:

1. **Initialize**: \(\delta_3 = \frac{\partial J}{\partial J} = 1\).
2. **Step to \(v_2\)**: \(\delta_2 = \frac{\partial J}{\partial v_2} = \delta_3 \cdot f_3'(v_2)\).
3. **Step to \(v_1\)**: \(\delta_1 = \frac{\partial J}{\partial v_1} = \delta_2 \cdot f_2'(v_1)\).
4. **Step to \(x\)**: \(\delta_x = \frac{\partial J}{\partial x} = \delta_1 \cdot f_1'(x)\).

Each local derivative \(f_k'\) is evaluated exactly once and multiplied by the incoming adjoint. The total number of derivative evaluations equals the number of function evaluations in the forward pass.

**Worked verification**: Let \(f_1(x) = x^2\), \(f_2(v) = \exp(v)\), \(f_3(v) = \log(v)\), with \(x = 3\).

Forward pass:
- \(v_1 = 3^2 = 9\)
- \(v_2 = \exp(9) = e^9\)
- \(J = \log(e^9) = 9\)

Backward pass:
- \(\delta_3 = 1\)
- \(\delta_2 = 1 \cdot \frac{1}{v_2} = \frac{1}{e^9}\)
- \(\delta_1 = \frac{1}{e^9} \cdot \exp(v_1) = \frac{1}{e^9} \cdot e^9 = 1\)
- \(\delta_x = 1 \cdot 2x = 1 \cdot 6 = 6\)

Direct verification: \(J = \log(\exp(x^2)) = x^2\), so \(\frac{dJ}{dx} = 2x = 6\). The results match.

Notice that at step 3, we needed \(v_1 = 9\) to evaluate \(f_2'(v_1) = \exp(9)\). This is why intermediate values are stored during the forward pass: the backward pass needs them to compute local derivatives.

**A revealing observation**: In this example, \(f_2\) and \(f_3\) are inverses, so they cancel analytically. Yet backpropagation mechanically computed \(\frac{1}{e^9} \cdot e^9 = 1\) without recognizing the simplification. This illustrates a key property: backpropagation is a *syntactic* procedure — it applies derivative rules locally without any algebraic insight into the function being differentiated. It works correctly regardless of whether the function simplifies, which is why it scales to arbitrary computation graphs.

**Test yourself**: Let \(f_1(x) = \sin(x)\), \(f_2(v) = v^3\), \(f_3(v) = 2v\), with \(x = \pi/2\). Compute forward and backward passes. Verify that \(\frac{dJ}{dx} = 0\). (Hint: \(\sin(\pi/2) = 1\), and \(\cos(\pi/2) = 0\).)

---

## 2. The Computational Graph and the Generalized Chain Rule

### 2.1 Graphs as Universal Representations of Computation

Every computation in a neural network can be represented as a node in a **directed acyclic graph (DAG)**. This graph-based perspective is the foundation of automatic differentiation frameworks such as PyTorch and TensorFlow.

**A cross-domain connection: electrical circuit analysis**

This graph representation is not unique to machine learning. In electrical engineering, circuit simulators like SPICE construct an identical DAG structure to analyze how voltages and currents propagate through components. When you ask SPICE to compute the sensitivity of an output voltage to a particular resistor value, it traverses the circuit graph backward — accumulating partial derivatives through each component — using precisely the same reverse-mode differentiation algorithm. The resistor, capacitor, and transistor models are just nodes with different local Jacobians. The mathematical structure is identical; only the node functions differ.

This connection is not merely an interesting parallel. It explains why automatic differentiation frameworks are sometimes called "computational graph engines" rather than "neural network libraries": they are general-purpose engines for composing differentiable functions, and neural networks are simply one family of graphs you can build with them.

**Building the graph**: For each operation in the computation, create a node. Edges point from inputs to outputs: if \(v_j\) is computed directly from \(v_i\), draw \(v_i \rightarrow v_j\). The graph is acyclic because feedforward networks contain no cycles. (Recurrent networks are handled via backpropagation through time, which unrolls the recurrence into a DAG.)

**Example**: The graph for \(J = (w \cdot x) + b\):
- \(v_1 = w\) (leaf node — parameter)
- \(v_2 = x\) (leaf node — input)
- \(v_3 = v_1 \cdot v_2\) (multiplication)
- \(v_4 = b\) (leaf node — parameter)
- \(v_5 = v_3 + v_4\) (addition; this is the output \(J\))

Edges: \(v_1 \rightarrow v_3\), \(v_2 \rightarrow v_3\), \(v_3 \rightarrow v_5\), \(v_4 \rightarrow v_5\).

The graph makes dependencies explicit. During the forward pass, nodes are evaluated in **topological order** (each node after all its parents). During the backward pass, nodes are processed in reverse topological order, ensuring that when the gradient for a node is computed, gradients for all nodes that depend on it have already been computed.

### 2.2 The Backpropagation Recurrence

Define:

- \(\text{Children}(v_i)\): the set of nodes \(v_j\) such that there exists an edge \(v_i \rightarrow v_j\) (nodes that depend directly on \(v_i\)).
- \(\text{Parents}(v_j)\): the set of nodes \(v_i\) such that \(v_i \rightarrow v_j\) (nodes that \(v_j\) directly depends on).
- **Adjoint** (error signal): \(\delta_i = \frac{\partial J}{\partial v_i}\). This is the total derivative, accounting for all paths from \(v_i\) to the loss \(J\).

**The recurrence**: From the multivariate chain rule:

\[
\delta_i = \frac{\partial J}{\partial v_i} = \sum_{j \in \text{Children}(v_i)} \frac{\partial J}{\partial v_j} \cdot \frac{\partial v_j}{\partial v_i} = \sum_{j \in \text{Children}(v_i)} \delta_j \cdot \frac{\partial v_j}{\partial v_i}
\]

To compute how much the loss changes when \(v_i\) is perturbed, examine every node \(v_j\) that \(v_i\) feeds into. For each such child, \(\delta_j\) is already known from the backward traversal. Multiply by \(\frac{\partial v_j}{\partial v_i}\) (how much \(v_j\) changes when \(v_i\) is perturbed) to obtain the contribution through that path. Summing over all children accounts for all downstream paths.

The summation solves the branching problem. If \(v_i\) fans out to \(K\) downstream computations, the naive chain rule would trace \(K\) separate paths, recomputing shared derivatives. Backpropagation computes each \(\delta_j\) once, then accumulates the \(K\) contributions to \(\delta_i\) via summation; each local Jacobian \(\frac{\partial v_j}{\partial v_i}\) is evaluated exactly once.

**A subtle but critical distinction**: The chain rule tells us *what* to compute; backpropagation is the *algorithm* for computing it efficiently. The chain rule states the mathematical identity \(\frac{\partial J}{\partial v_i} = \sum_j \frac{\partial J}{\partial v_j} \frac{\partial v_j}{\partial v_i}\). It says nothing about evaluation order. Backpropagation's key algorithmic insight is the order of evaluation (reverse topological) and the accumulation of gradients via summation, which avoids the exponential blowup of naive expansion. The same chain rule, evaluated in a different order, produces the exponential algorithm we rejected in Section 1.2.

**Try this yourself**: Draw the computational graph for \(J = (v_1 + v_2) \cdot (v_1 - v_3)\), where \(v_1, v_2, v_3\) are leaf nodes. Identify all children of \(v_1\). Write the recurrence for \(\delta_1\). How many terms appear in the sum? Why does this number match the number of edges leaving \(v_1\)?

### 2.3 The Algorithm

**Forward pass**:
1. Topologically sort all nodes in the computational graph.
2. For each node \(v_j\) in topological order:
   - Compute \(v_j = f_j(\text{Parents}(v_j))\) using the values of its parent nodes.
   - Store \(v_j\) in memory.

**Backward pass**:
1. Initialize the adjoint of the output node: \(\delta_{\text{output}} = 1\). Set all other adjoints to zero.
2. For each node \(v_j\) in reverse topological order:
   - For each parent \(v_i \in \text{Parents}(v_j)\):
     - Compute the local Jacobian \(\frac{\partial v_j}{\partial v_i}\) using the stored forward-pass values.
     - Accumulate: \(\delta_i \leftarrow \delta_i + \delta_j \cdot \frac{\partial v_j}{\partial v_i}\).

When the backward pass completes, every node \(v_i\) holds \(\delta_i = \frac{\partial J}{\partial v_i}\). Parameter nodes contain their gradients, ready for the optimizer.

**Complexity**: The backward pass performs one local Jacobian evaluation per edge. In typical architectures, each node has bounded in-degree, so the number of edges is proportional to the number of nodes. The backward-pass cost is therefore \(O(\text{forward-pass cost})\) — typically 2–3× the forward pass in practice. Memory cost is \(O(\text{number of nodes})\), since all forward-pass values needed for local Jacobian computations must be stored.

### 2.4 Worked Example: Shared Input with Branching

This example demonstrates the accumulation mechanism for branching computations.

**Problem**: Compute gradients for \(J = (a \cdot b) + (a \cdot c)\) where \(a, b, c\) are scalars. The input \(a\) is shared across two multiplication branches.

**Step 1: Build the computational graph**:
- Leaf nodes: \(v_1 = a\), \(v_2 = b\), \(v_3 = c\)
- Operation nodes: \(v_4 = v_1 \cdot v_2\), \(v_5 = v_1 \cdot v_3\)
- Output node: \(v_6 = v_4 + v_5 = J\)

**Step 2: Forward pass** (with \(a=2, b=3, c=4\)):
- \(v_1 = 2\), \(v_2 = 3\), \(v_3 = 4\)
- \(v_4 = 2 \cdot 3 = 6\)
- \(v_5 = 2 \cdot 4 = 8\)
- \(v_6 = 6 + 8 =