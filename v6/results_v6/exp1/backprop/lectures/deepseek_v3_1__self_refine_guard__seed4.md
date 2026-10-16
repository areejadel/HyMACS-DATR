# Backpropagation in Neural Networks

---

## Learning Objectives

By the end of this lecture, you will be able to:

1. **Remember:** State the two phases of backpropagation and the purpose of each.
2. **Understand:** Explain why naive gradient computation repeats work and how backpropagation avoids it by reusing stored intermediate values.
3. **Apply:** Compute all partial derivatives for a single-hidden-layer network given a specific loss function and activation.
4. **Analyze:** Trace gradient flow through a computational graph, identifying which nodes contribute to the gradient of a given parameter.
5. **Create:** Construct the backpropagation rules for a novel network architecture by decomposing it into its computational graph.

---

## 1. Prerequisites

We assume you are comfortable with:

- **Matrix multiplication and broadcasting:** Multiplying a weight matrix by an input vector, adding a bias vector, and understanding the shapes involved.
- **The chain rule from calculus:** If \( y = g(u) \) and \( u = f(x) \), then \( \frac{dy}{dx} = \frac{dy}{du} \cdot \frac{du}{dx} \). For multivariate functions, the chain rule sums over all intermediate paths.
- **Elementary partial derivatives:** The identity \( \frac{\partial}{\partial \mathbf{W}} (\mathbf{W}\mathbf{x}) = \mathbf{x}^\top \) for a vector input, and the ability to differentiate common activation functions such as sigmoid, ReLU, or softmax.
- **The forward pass of a neural network:** Given an input, the network computes layer outputs sequentially to produce a prediction.

If any of these topics feel shaky, pause here and review them — they are the building blocks for everything that follows.

---

## 2. Motivation: The Gradient Computation Bottleneck

### 2.1 Why Gradients Matter

Training a neural network means adjusting its parameters \( \boldsymbol{\theta} \) to minimize a scalar cost function \( J(\boldsymbol{\theta}) \). The cost measures how wrong our predictions are. To improve, we need to know how each parameter influences the cost — that is, we need the gradient \( \nabla_{\boldsymbol{\theta}} J \).

Modern networks can have millions or billions of parameters. Computing each partial derivative individually by evaluating the network twice (once with a slightly perturbed parameter) is hopelessly slow. We need an algorithm that computes the entire gradient in roughly the same time it takes to compute the cost itself.

### 2.2 The Core Intuition: Don't Repeat Yourself

Consider evaluating a deeply nested mathematical expression:

\[
z = \bigl( f(w) \bigr)^2
\]

You want \( \frac{dz}{dw} \). The chain rule gives:

\[
\frac{dz}{dw} = 2 f(w) \cdot f'(w)
\]

The quantity \( f(w) \) appears in two places: as the factor \( 2f(w) \) and inside \( f'(w) \). If you compute \( f(w) \) from scratch each time it appears, you do redundant work. The same redundancy explodes in a deep network: a single early parameter influences many downstream nodes, and each of those nodes recomputes the same intermediate values when we apply the chain rule naively.

**Backpropagation eliminates this redundancy** by computing every intermediate value once during the forward pass, storing it, and then reusing those stored values during the backward pass. The runtime becomes proportional to one forward pass plus one backward pass — a small constant factor overhead.

---

## 3. Computational Graphs: A Visual Language for Function Composition

### 3.1 Intuition Before Formalism

A neural network is a composition of operations: matrix multiply, add bias, apply activation, repeat. We can represent this composition as a **directed acyclic graph** (DAG) where:

- **Nodes** are variables (inputs, intermediate results, parameters, and the final cost).
- **Edges** point from inputs to the operation that consumes them.

For a simple linear layer \( \mathbf{z} = \mathbf{W}\mathbf{x} + \mathbf{b} \), the graph looks like:

\[
\mathbf{x} \rightarrow [\text{matmul with } \mathbf{W}] \rightarrow \mathbf{W}\mathbf{x} \rightarrow [\text{add } \mathbf{b}] \rightarrow \mathbf{z}
\]

Here \( \mathbf{W}\mathbf{x} \) and \( \mathbf{z} \) are nodes; \( \mathbf{W} \) and \( \mathbf{b} \) are also nodes (parameters we will eventually differentiate with respect to). The operations live on the edges.

### 3.2 Formal Definition

Let the graph have nodes \( \{u^{(1)}, u^{(2)}, \ldots, u^{(n)}\} \) sorted in **topological order**: every edge goes from an earlier node to a later node. The final node \( u^{(n)} \) is the scalar cost \( J \).

For any node \( u^{(i)} \), its value is computed by applying an operation to its **parents** — the nodes with edges pointing into it. We write:

\[
u^{(i)} = f^{(i)}\bigl(\text{Pa}(u^{(i)})\bigr)
\]

The gradient we ultimately want is \( \frac{\partial u^{(n)}}{\partial u^{(i)}} \) for every node that is a parameter.

### 3.3 The Chain Rule on the Graph

The chain rule tells us how a change in node \( u^{(i)} \) propagates to the final cost. It flows **forward through the children** of \( u^{(i)} \). Formally:

\[
\frac{\partial u^{(n)}}{\partial u^{(i)}} = \sum_{j: u^{(i)} \in \text{Pa}(u^{(j)})} \frac{\partial u^{(n)}}{\partial u^{(j)}} \cdot \frac{\partial u^{(j)}}{\partial u^{(i)}}
\]

**Interpretation:** The gradient of the final cost with respect to node \( i \) is the sum, over all immediate children \( j \) of node \( i \), of (the gradient signal coming into child \( j \)) times (the local derivative of child \( j \) with respect to node \( i \)).

**Why the sum?** Node \( i \) can influence the final cost through multiple downstream paths. The chain rule adds up all those influences.

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

**Why store everything?** Because during the backward pass, we need these values to evaluate local derivatives. For example, the derivative of \( \sigma(z) \) depends on the value of \( z \) that we computed in the forward pass.

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

**Key detail:** The local Jacobian \( \frac{\partial u^{(j)}}{\partial u^{(i)}} \) is evaluated using the **stored values** from the forward pass. This is what prevents redundant recomputation.

### 4.3 Handling Parameters

Parameters like \( \mathbf{W} \) and \( \mathbf{b} \) are leaf nodes with no parents. Their gradients are computed exactly as above: they receive gradient signals from their children. Once we have \( \bar{\mathbf{W}} \) and \( \bar{\mathbf{b}} \), we can update them with an optimizer.

### 4.4 The Two-Phase Algorithm: A Concrete Walkthrough

Let's trace through a tiny network to see the algorithm in action.

**Network:**
- Input: \( x \)
- Hidden: \( h = \sigma(w_1 x + b_1) \)
- Output: \( \hat{y} = w_2 h + b_2 \)
- Cost: \( J = \frac{1}{2}(\hat{y} - y)^2 \) (MSE)

**Step 1: Build the computational graph.** Nodes: \( x, w_1, b_1, a_1 = w_1 x + b_1, h = \sigma(a_1), w_2, b_2, \hat{y} = w_2 h + b_2, J \).

**Step 2: Forward pass.** Compute and store each node's value in topological order.

**Step 3: Backward pass.** Start at \( J \), work backwards.

\[
\bar{J} = 1
\]
\[
\bar{\hat{y}} = \frac{\partial J}{\partial \hat{y}} = \hat{y} - y
\]
\[
\bar{w}_2 = \bar{\hat{y}} \cdot \frac{\partial \hat{y}}{\partial w_2} = (\hat{y} - y) \cdot h
\]
\[
\bar{b}_2 = \bar{\hat{y}} \cdot \frac{\partial \hat{y}}{\partial b_2} = (\hat{y} - y) \cdot 1
\]
\[
\bar{h} = \bar{\hat{y}} \cdot \frac{\partial \hat{y}}{\partial h} = (\hat{y} - y) \cdot w_2
\]
\[
\bar{a}_1 = \bar{h} \cdot \frac{\partial h}{\partial a_1} = \bar{h} \cdot \sigma'(a_1)
\]
\[
\bar{w}_1 = \bar{a}_1 \cdot \frac{\partial a_1}{\partial w_1} = \bar{a}_1 \cdot x
\]
\[
\bar{b}_1 = \bar{a}_1 \cdot \frac{\partial a_1}{\partial b_1} = \bar{a}_1 \cdot 1
\]

**Observe the pattern:** Each step multiplies an incoming gradient signal by a local derivative evaluated on stored forward-pass values. No node's value is recomputed.

---

## 5. The Memory-Time Tradeoff: Why We Don't Recompute

### 5.1 The Tension

The algorithm we've described stores every intermediate activation. For a network with a million hidden units across ten layers, that's tens of millions of floating-point numbers. This is the memory cost of backpropagation.

**Why not just recompute intermediates during the backward pass?** That would save memory but cost time — potentially a lot of it. Imagine recomputing the activations of layer 1 for every gradient that flows through it. In a deep network, layer 1's activations would be recomputed once per downstream path, leading to a runtime that scales quadratically or worse with depth.

### 5.2 The Resolution: Checkpointing

There is a spectrum between "store everything" and "recompute everything." **Gradient checkpointing** (also called "activation recomputation") stores only a subset of activations — say, one per layer — and recomputes the rest on demand during the backward pass. This trades a modest increase in compute for a large reduction in memory. The backpropagation framework we're building generalizes cleanly to this: the same local derivative formulas apply, but some stored values are replaced by recomputed ones.

### 5.3 Analogy: A Chef's Mise en Place

Think of the forward pass as a chef preparing every ingredient for a complex dish — chopping, measuring, arranging. The backward pass is the final assembly, where each ingredient is used exactly when needed. A chef who stores everything (mise en place) works fast but needs a large counter. A chef who recomputes (chops each vegetable right before it hits the pan) saves counter space but risks burning the dish. Checkpointing is the chef who preps only the most-used ingredients and chops the rest on the fly — a deliberate tradeoff.

---

## 6. Backpropagation as a Special Case of Automatic Differentiation

### 6.1 A Broader View

Backpropagation is not a neural-network-specific algorithm. It is an instance of **reverse-mode automatic differentiation** (reverse-mode AD) applied to the computational graph of a neural network. Reverse-mode AD computes the gradient of a scalar output with respect to all inputs in one backward pass, regardless of the number of inputs. This is exactly what we need for training: many parameters, one scalar loss.

### 6.2 Forward-Mode vs. Reverse-Mode

**Forward-mode AD** propagates derivatives forward through the graph: given one input, it computes the derivative of every node with respect to that input. For \( n \) parameters, you'd need \( n \) forward passes. Reverse-mode needs only one backward pass for a scalar output. This is why backpropagation dominates neural network training.

### 6.3 Try This Yourself: The Two-Mode Thought Experiment

Consider a function \( f: \mathbb{R}^{1000} \to \mathbb{R} \). You want all 1000 partial derivatives \( \frac{\partial f}{\partial x_i} \). Which mode of AD is more efficient? Why?

<details>
<summary>Answer</summary>

Reverse-mode. You have many inputs (1000) and one output. Reverse-mode computes the full gradient in one backward pass. Forward-mode would require 1000 separate passes, one per input direction.
</details>

---

## 7. Common Pitfalls and Debugging Strategies

### 7.1 Vanishing and Exploding Gradients

When gradients flow through many layers, they are multiplied by local derivatives at each step. If these local derivatives are consistently less than 1 (e.g., sigmoid saturates at 0 or 1, giving derivatives near 0), the gradient signal shrinks exponentially with depth — **vanishing gradient**. If they are consistently greater than 1 (e.g., large unnormalized weights), the signal explodes — **exploding gradient**.

This is not a bug in backpropagation; it's a consequence of the architecture. Backpropagation faithfully delivers the true gradient — if that gradient is near zero or enormous, the algorithm still works correctly. The fix lies in architecture design (ReLU, residual connections, layer normalization) and optimization (gradient clipping), not in the differentiation algorithm itself.

### 7.2 Shape Mismatches

The most common implementation bug: a gradient has shape \( (d_1, d_2) \) but the parameter it should update has shape \( (d_2, d_1) \). Always check that \( \frac{\partial J}{\partial \mathbf{W}} \) has the same shape as \( \mathbf{W} \). The identity \( \frac{\partial}{\partial \mathbf{W}} (\mathbf{W}\mathbf{x}) = \mathbf{x}^\top \) is your shape-checking friend.

### 7.3 Forgetting the Sum

When a node has multiple children, the gradient is the **sum** of the incoming signals — not the average, not the maximum. Forgetting this sum is like hearing only one voice in a choir. The chain rule demands it.

### 7.4 Debugging with Finite Differences

The ultimate sanity check: for a small network, compute the gradient via backpropagation and compare it to the numerical gradient from finite differences:

\[
\frac{\partial J}{\partial \theta_i} \approx \frac{J(\theta_i + \epsilon) - J(\theta_i - \epsilon)}{2\epsilon}
\]

If these agree to within \( 10^{-5} \) or so, your backpropagation is correct. If not, something is wrong — check each local derivative individually.

---

## 8. Summary

Backpropagation is two phases:

1. **Forward:** Compute and store every node's value in topological order.
2. **Backward:** Propagate gradient signals from the output backward, multiplying each incoming signal by the local derivative evaluated on stored forward-pass values, and summing over children.

It computes the full gradient of a scalar cost with respect to all parameters in time proportional to one forward pass, by eliminating redundant recomputation. The algorithm generalizes to any computational graph — it is reverse-mode automatic differentiation, not a neural-network trick.

---

## 9. Looking Ahead

In the next lecture, we will implement backpropagation in code for a multi-layer perceptron and see how modular design (layers as objects with `.forward()` and `.backward()` methods) maps exactly onto the computational graph abstraction. We will also introduce automatic differentiation frameworks (PyTorch, JAX) that automate the backward pass, freeing you to design architectures without manually deriving gradients.

---

## 10. Practice Problems

1. **Single-neuron gradient:** Given input \( x \in \mathbb{R} \), weight \( w \), bias \( b \), activation \( \sigma \), output \( \hat{y} = \sigma(wx + b) \), and loss \( J = \frac{1}{2}(\hat{y} - y)^2 \), derive \( \frac{\partial J}{\partial w} \) and \( \frac{\partial J}{\partial b} \) by hand. Verify with finite differences.

2. **Two-layer network:** Add a second neuron: \( \hat{y} = w_2 \sigma(w_1 x + b_1) + b_2 \). Draw the computational graph. Label all nodes. Compute \( \frac{\partial J}{\partial w_1} \) and \( \frac{\partial J}{\partial w_2} \). Notice how \( \sigma'(a_1) \) appears in the gradient for \( w_1 \).

3. **Shared weights:** Consider a network where the same weight matrix \( \mathbf{W} \) is used in two different layers. How does the computational graph change? How does the gradient for \( \mathbf{W} \) change?

4. **Checkpointing thought experiment:** For a 100-layer network, you store only every 10th layer's activations. During the backward pass, how many extra forward recomputations do you perform for a single layer's activations? Express in terms of the checkpoint interval.

5. **Design challenge:** Propose a new activation function \( \phi(z) \). Derive its local derivative \( \phi'(z) \). Write the backpropagation rule for a layer using \( \phi \). What property of \( \phi' \) would help avoid vanishing gradients?