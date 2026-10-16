# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember** the definition of an adjoint (error signal) and state the backpropagation recurrence.
2. **Understand** why naive gradient computation is exponentially expensive and how dynamic programming avoids this cost.
3. **Apply** the backpropagation algorithm by hand to compute all parameter gradients for a two-layer neural network with a given loss function.
4. **Analyze** a computational graph to identify which nodes require stored forward-pass values and which gradients can be computed in parallel.
5. **Evaluate** whether a given network architecture introduces gradient vanishing or exploding problems based on activation function choices.

---

## 1. What We Already Know and What We Need

### 1.1 Prerequisites

We assume you are comfortable with:

- **Matrix multiplication** and its shape rules: if \(A \in \mathbb{R}^{m \times n}\) and \(B \in \mathbb{R}^{n \times p}\), then \(AB \in \mathbb{R}^{m \times p}\).
- **Elementary calculus**: the derivative of \(x^{2}\) is \(2x\); the derivative of \(\sigma(z) = \frac{1}{1+e^{-z}}\) is \(\sigma(z)(1-\sigma(z))\); the chain rule \(\frac{d}{dx} f(g(x)) = f'(g(x))\, g'(x)\).
- **The purpose of training a neural network**: we have a dataset of input–target pairs, we feed inputs forward to obtain predictions, we measure the discrepancy between predictions and targets with a scalar cost \(J\), and we adjust the weights and biases to make \(J\) smaller.

### 1.2 The Core Problem

Consider a feedforward network with \(P\) parameters, where \(P\) can easily reach millions. We need \(\nabla_{\theta} J\), the vector of all \(P\) partial derivatives \(\frac{\partial J}{\partial \theta_{k}}\), so that we can update each parameter by a small step downhill:

\[
\theta_{k} \leftarrow \theta_{k} - \eta \frac{\partial J}{\partial \theta_{k}}
\]

Here is the tension that makes this problem worth studying carefully: the chain rule tells us *what* to compute — it is just a mechanical application of calculus. The challenge is *how* to compute it without wasting computation. If we are not careful, we will recompute the same intermediate derivatives repeatedly, making training impossibly slow. Backpropagation organizes this computation so that its cost is no more than a constant multiple of the forward pass. This is not a trick; it is the same algorithmic insight that powers dynamic programming in shortest-path algorithms, just dressed in calculus.

---

## 2. Intuition First: A Concrete Example with Three Functions

Before introducing graphs or summations, we trace through the simplest possible composition.

Let \(J\) be computed from a scalar input \(x\) through three functions:

\[
v_{1} = f_{1}(x), \qquad v_{2} = f_{2}(v_{1}), \qquad J = f_{3}(v_{2})
\]

**Forward pass.** Starting with \(x = 2\), we compute:

\[
v_{1} = f_{1}(2), \qquad v_{2} = f_{2}(v_{1}), \qquad J = f_{3}(v_{2})
\]

We record each intermediate value as we go.

**What we want.** \(\frac{dJ}{dx}\), the derivative of the final output with respect to the original input.

**Naive approach.** Expand the full expression symbolically:

\[
\frac{dJ}{dx} = f_{3}'(v_{2}) \cdot f_{2}'(v_{1}) \cdot f_{1}'(x)
\]

To evaluate this, we need \(v_{2}\) and \(v_{1}\). We already computed them in the forward pass, so we can simply substitute them. This appears fine for a chain of three. However, consider a network with many layers and *branches*. If \(v_{2}\) influences \(J\) through five distinct paths, the naive symbolic expansion would contain \(f_{3}'(v_{2})\) five times, each requiring us to recompute \(v_{2}\) and everything downstream of it. The cost explodes.

**Why does this matter?** Imagine a network where one intermediate value fans out to hundreds of downstream computations. A naive expansion duplicates the derivative of that value for every path, turning a linear computation into an exponential one. This is the same kind of blowup you would see if you tried to compute Fibonacci numbers by expanding the full recursion tree instead of memoizing — and backpropagation is the memoization.

**Backpropagation approach.** We work backward, one step at a time, storing each derivative as we compute it.

1. Start at the output: \(\delta_{3} = \frac{dJ}{dJ} = 1\).
2. Move to \(v_{2}\): \(\delta_{2} = \frac{dJ}{dv_{2}} = \delta_{3} \cdot f_{3}'(v_{2})\).
3. Move to \(v_{1}\): \(\delta_{1} = \frac{dJ}{dv_{1}} = \delta_{2} \cdot f_{2}'(v_{1})\).
4. Move to \(x\): \(\delta_{x} = \delta_{1} \cdot f_{1}'(x)\).

Notice: each local derivative \(f_{k}'\) is evaluated *once* and multiplied by the incoming signal from above. The total number of derivative evaluations equals the number of function evaluations in the forward pass. We never recompute anything.

**Check your understanding.** Suppose \(f_{1}(x) = x^{2}\), \(f_{2}(v) = \exp(v)\), \(f_{3}(v) = \log(v)\), and \(x = 3\). Compute \(\frac{dJ}{dx}\) by both the naive method and the backpropagation method. Verify they give the same result. (Tracing: \(v_{1} = 9\), \(v_{2} = e^{9}\), \(J = \ln(e^{9}) = 9\). \(\delta_{3} = 1\), \(\delta_{2} = 1 \cdot 1/e^{9}\), \(\delta_{1} = (1/e^{9}) \cdot e^{9} = 1\), \(\delta_{x} = 1 \cdot 6 = 6\).)

---

## 3. The Computational Graph and the Generalized Chain Rule

### 3.1 Representing Computation as a Graph

We now make the structure explicit. Every computation in the network is a node in a directed acyclic graph (DAG). Edges point from inputs to outputs: if \(v_{j}\) is computed directly from \(v_{i}\), we draw \(v_{i} \rightarrow v_{j}\).

**Example graph.** Consider \(J = (w \cdot x) + b\). The nodes are:

- \(v_{1} = w\)
- \(v_{2} = x\)
- \(v_{3} = v_{1} \cdot v_{2}\) (multiplication)
- \(v_{4} = b\)
- \(v_{5} = v_{3} + v_{4}\) (addition, output \(J\))

Edges: \(v_{1} \rightarrow v_{3}\), \(v_{2} \rightarrow v_{3}\), \(v_{3} \rightarrow v_{5}\), \(v_{4} \rightarrow v_{5}\).

The forward pass evaluates nodes in topological order: \(v_{1}, v_{2}, v_{3}, v_{4}, v_{5}\). Each node stores its value.

### 3.2 The Backpropagation Recurrence

Let \(\text{Pa}(v_{i})\) denote the parents of \(v_{i}\) (the nodes whose values are inputs to the function that computes \(v_{i}\)). Let \(\text{Children}(v_{i})\) denote the nodes that depend directly on \(v_{i}\).

The chain rule for a scalar output \(J\) and an intermediate node \(v_{i}\) is:

\[
\frac{\partial J}{\partial v_{i}} = \sum_{j \in \text{Children}(v_{i})} \frac{\partial J}{\partial v_{j}} \cdot \frac{\partial v_{j}}{\partial v_{i}}
\]

We define the **adjoint** (or **error signal**) \(\delta_{i} = \frac{\partial J}{\partial v_{i}}\).

The recurrence becomes:

\[
\delta_{i} = \sum_{j \in \text{Children}(v_{i})} \delta_{j} \cdot \frac{\partial v_{j}}{\partial v_{i}}
\]

**Interpretation.** To compute the derivative of \(J\) with respect to \(v_{i}\), we examine every node \(v_{j}\) that \(v_{i}\) directly feeds into. We already know \(\delta_{j}\) (the derivative of \(J\) with respect to that node). We multiply it by the local derivative \(\frac{\partial v_{j}}{\partial v_{i}}\) (how much \(v_{j}\) changes when \(v_{i}\) changes) and sum over all such children. This is exactly what we did in the three-function chain: \(v_{1}\) had one child \(v_{2}\), so \(\delta_{1} = \delta_{2} \cdot f_{2}'(v_{1})\).

**A non-obvious framing worth pausing on:** This recurrence is structurally identical to message-passing in graphical models — specifically, the sum-product algorithm for belief propagation on factor graphs. In that context, messages flow from observed variables outward, carrying partial beliefs. Here, adjoints flow backward, carrying partial derivatives. The computational graph of a neural network *is* a factor graph where the factors are the local functions \(f_{k}\), and backpropagation is exactly the sum-product algorithm run in reverse topological order with the "product" being the chain rule. If you have seen belief propagation before, backpropagation is the same engine under a different hood.

### 3.3 The Algorithm

1. **Forward pass:** Traverse the graph in topological order. Compute and store every node value \(v_{i}\).
2. **Backward pass:** Initialize \(\delta_{\text{output}} = 1\). Traverse the graph in *reverse* topological order. For each node \(v_{j}\), for each of its parents \(v_{i}\), add \(\delta_{j} \cdot \frac{\partial v_{j}}{\partial v_{i}}\) to \(\delta_{i}\).

When the backward pass finishes, every node (including the parameter nodes) holds its \(\delta_{i} = \frac{\partial J}{\partial v_{i}}\).

**Why this is efficient.** Each edge's local derivative \(\frac{\partial v_{j}}{\partial v_{i}}\) is computed exactly once. Each \(\delta_{j}\) is computed once and then reused for all its parents. No subexpression is ever recomputed. This is dynamic programming: we fill the table of \(\delta\) values in an order that guarantees each entry is computed from already-known entries.

### 3.4 Worked Example: Graph with a Branch

We now compute gradients for \(J = (a \cdot b) + (a \cdot c)\), where \(a, b, c\) are inputs. This graph has a shared input \(a\). This is where the naive approach would start to hurt: \(a\) appears in two different products, so its derivative must combine contributions from both paths.

**Graph nodes:**
- \(v_{1} = a\), \(v_{2} = b\), \(v_{3} = c\)
- \(v_{4} = v_{1} \cdot v_{2}\)
- \(v_{5} = v_{1} \cdot v_{3}\)
- \(v_{6} = v_{4} + v_{5} = J\)

**Forward pass** (with concrete values \(a=2, b=3, c=4\)):
- \(v_{1} = 2\), \(v_{2} = 3\), \(v_{3} = 4\)
- \(v_{4} = 2 \cdot 3 = 6\)
- \(v_{5} = 2 \cdot 4 = 8\)
- \(v_{6} = 6 + 8 = 14 = J\)

**Backward pass:**
- Initialize: \(\delta_{6} = \frac{\partial J}{\partial v_{6}} = 1\)
- Node \(v_{6}\) has parents \(v_{4}\) and \(v_{5}\). Local derivatives: \(\frac{\partial v_{6}}{\partial v_{4}} = 1\), \(\frac{\partial v_{6}}{\partial v_{5}} = 1\).
  - \(\delta_{4} = \delta_{6} \cdot 1 = 1\)
  - \(\delta_{5} = \delta_{6} \cdot 1 = 1\)
- Node \(v_{4}\) has parents \(v_{1}\) and \(v_{2}\). Local derivatives: \(\frac{\partial v_{4}}{\partial v_{1}} = v_{2} = 3\), \(\frac{\partial v_{4}}{\partial v_{2}} = v_{1} = 2\).
  - Contribution to \(\delta_{1}\) from this path: \(\delta_{4} \cdot 3 = 3\)
  - \(\delta_{2} = \delta_{4} \cdot 2 = 2\)
- Node \(v_{5}\) has parents \(v_{1}\) and \(v_{3}\). Local derivatives: \(\frac{\partial v_{5}}{\partial v_{1}} = v_{3} = 4\), \(\frac{\partial v_{5}}{\partial v_{3}} = v_{1} = 2\).
  - Contribution to \(\delta_{1}\) from this path: \(\delta_{5} \cdot 4 = 4\)
  - \(\delta_{3} = \delta_{5} \cdot 2 = 2\)
- Sum contributions to \(v_{1}\): \(\delta_{1} = 3 + 4 = 7\)

**Final gradients:** \(\frac{\partial J}{\partial a} = 7\), \(\frac{\partial J}{\partial b} = 2\), \(\frac{\partial J}{\partial c} = 2\).

**Check your understanding.** Verify the result by direct differentiation: \(J = ab + ac\), so \(\frac{\partial J}{\partial a} = b + c = 7\), \(\frac{\partial J}{\partial b} = a = 2\), \(\frac{\partial J}{\partial c} = a = 2\). The numbers match.

**Try this yourself.** Before reading further, draw the computational graph for \(J = (w_{1}x + w_{2}x) + b\) where \(x\) appears in two products with different weights. Run the forward pass with \(x=1, w_{1}=2, w_{2}=3, b=4\). Then execute the backward pass. Confirm that the gradient for \(x\) receives contributions from both paths. This is the same pattern you will see in every shared-weight scenario — including convolution kernels and recurrent connections.

---

## 4. Backpropagation for a Two-Layer Neural Network

### 4.1 Architecture and Notation

We now move from scalar toy examples to the vectorized setting that actual training code uses. Consider a two-layer network:

\[
z^{[1]} = W^{[1]} x + b^{[1]}, \quad a^{[1]} = \sigma(z^{[1]})
\]
\[
z^{[2]} = W^{[2]} a^{[1]} + b^{[2]}, \quad \hat{y} = a^{[2]} = \sigma(z^{[2]})
\]

Loss: \(J = \frac{1}{2} \|\hat{y} - y\|^{2}\) (mean squared error, scalar).

Here \(x \in \mathbb{R}^{d}\), \(W^{[1]} \in \mathbb{R}^{h \times d}\), \(b^{[1]} \in \mathbb{R}^{h}\), \(W^{[2]} \in \mathbb{R}^{1 \times h}\), \(b^{[2]} \in \mathbb{R}\). The activation \(\sigma\) is the sigmoid function.

### 4.2 Forward Pass

We compute and store:

\[
z^{[1]} = W^{[1]} x + b^{[1]}, \quad a^{[1]} = \sigma(z^{[1]})
\]
\[
z^{[2]} = W^{[2]} a^{[1]} + b^{[2]}, \quad \hat{y} = \sigma(z^{[2]})
\]
\[
J = \frac{1}{2} (\hat{y} - y)^{2}
\]

### 4.3 Backward Pass

We work backward from \(J\).

**Step 1: Gradient of the loss w.r.t. output.**

\[
\delta_{\hat{y}} = \frac{\partial J}{\partial \hat{y}} = \hat{y} - y
\]

**Step 2: Gradient through the output activation.**

\[
\frac{\partial \hat{y}}{\partial z^{[2]}} = \sigma(z^{[2]}) (1 - \sigma(z^{[2]})) = \hat{y}(1 - \hat{y})
\]
\[
\delta_{z^{[2]}} = \delta_{\hat{y}} \cdot \hat{y}(1 - \hat{y})
\]

**Step 3: Gradients for \(W^{[2]}\) and \(b^{[2]}\).**

\[
\frac{\partial z^{[2]}}{\partial W^{[2]}} = (a^{[1]})^{T}, \quad \frac{\partial z^{[2]}}{\partial b^{[2]}} = 1
\]
\[
\frac{\partial J}{\partial W^{[2]}} = \delta_{z^{[2]}} \cdot (a^{[1]})^{T}, \quad \frac{\partial J}{\partial b^{[2]}} = \delta_{z^{[2]}}
\]

**Step 4: Gradient through the hidden activation.**

\[
\delta_{a^{[1]}} = (W^{[2]})^{T} \delta_{z^{[2]}}
\]

**Step 5: Gradient through the hidden layer pre-activation.**

\[
\frac{\partial a^{[1]}}{\partial z^{[1]}} = a^{[1]} \odot (1 - a^{[1]}) \quad \text{(element-wise sigmoid derivative)}
\]
\[
\delta_{z^{[1]}} = \delta_{a^{[1]}} \odot a^{[1]} \odot (1 - a^{[1]})
\]

**Step 6: Gradients for \(W^{[1]}\) and \(b^{[1]}\).**

\[
\frac{\partial J}{\partial W^{[1]}} = \delta_{z^{[1]}} \cdot x^{T}, \quad \frac{\partial J}{\partial b^{[1]}} = \delta_{z^{[1]}}
\]

**Try this yourself.** Take \(x = [1, 2]^{T}\), \(y = 1\), \(W^{[1]} = [[0.5, -0.2], [0.1, 0.3]]\), \(b^{[1]} = [0, 0]^{T}\), \(W^{[2]} = [0.4, -0.5]\), \(b^{[2]} = 0\). Run the forward pass by hand (use a calculator for the sigmoids). Then execute Steps 1–6 in order. Verify that the gradient with respect to \(W^{[1]}_{11}\) matches a finite-difference check: perturb \(W^{[1]}_{11}\) by \(10^{-4}\), recompute \(J\), and compare \(\Delta J / 10^{-4}\) to your computed gradient. This exercise will cement the algorithm in a way that reading alone cannot.

---

## 5. The Memory-Time Tradeoff and Why We Store Forward Values

### 5.1 What Must Be Stored

Look back at the local derivatives in Section 4.3. To compute \(\frac{\partial \hat{y}}{\partial z^{[2]}}\), we needed \(\hat{y} = \sigma(z^{[2]})\), which is a forward-pass value. To compute \(\frac{\partial a^{[1]}}{\partial z^{[1]}}\), we needed \(a^{[1]}\), also a forward-pass value. In general, the derivative of an activation function with respect to its input depends on the activation value itself. Backpropagation therefore requires that we store the forward-pass activations.