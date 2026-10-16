# Backpropagation in Neural Networks

## Learning Objectives

By the end of this lecture, you will be able to:

- **Explain** why naive gradient computation is computationally prohibitive for deep networks and how backpropagation resolves this bottleneck.
- **Trace** the flow of gradient signals through a feedforward network’s computational graph using the chain rule in reverse topological order.
- **Derive** the full backpropagation update rules for a two-layer neural network with a scalar cost, including activation-function gating.
- **Diagnose and correct** shape mismatches in gradient computations using dimensional analysis.
- **Relate** hand-derived layerwise formulas to the automatic differentiation (reverse-mode AD) machinery used in modern frameworks.

---

## 1. Why We Need Backpropagation

### 1.1 The Optimization Problem

Imagine you’re training a network to recognize handwritten digits. You show it an image of a “7,” it confidently predicts “1,” and the cost function spikes. To fix this, you need to adjust millions of weights — but which ones, and by how much? Each weight is a tiny knob buried deep inside a machine with dozens of layers. Turning one knob changes the signal that flows through every subsequent layer, eventually moving the final prediction. You need the gradient: the precise sensitivity of the cost to each knob.

Training a neural network means finding weights and biases — collectively denoted \(\boldsymbol{\theta}\) — that minimize a scalar cost function \(J(\boldsymbol{\theta})\). For gradient-based optimizers such as SGD or Adam, we must compute the gradient \(\nabla_{\boldsymbol{\theta}} J\): a vector containing the partial derivative of \(J\) with respect to every parameter.

If the network has \(P\) parameters, a naive finite-difference approximation requires at least \(P+1\) forward passes to estimate the gradient — one per parameter perturbation. For a modern network with millions of parameters, this is impossible. We therefore need an **exact, efficient** gradient computation.

But here is the tension that makes this problem genuinely hard: the function we want to differentiate is a deeply nested composition of hundreds of simple operations. The chain rule guarantees we *can* compute the gradient exactly by multiplying local derivatives along every path from parameters to cost. Yet if we naively traverse all those paths independently, the sheer number of repeated subcomputations explodes. A weight matrix used in layer 1 might influence the cost through \(10^6\) distinct downstream routes — and without a strategy, we'd recompute its contribution \(10^6\) times.

**The resolution:** backpropagation reorganizes the computation so that every intermediate gradient is computed exactly once and reused everywhere upstream. It is not an approximation, not a new learning algorithm — it is the computational engine that makes gradient descent feasible in deep architectures.

**A concrete illustration of the scale involved:** Consider GPT-3, with 175 billion parameters. A single finite-difference gradient estimate would require 175 billion forward passes — at roughly 0.4 milliseconds per forward pass on a state-of-the-art GPU cluster, that is over 800 days of computation for *one* gradient step. Training GPT-3 required approximately \(10^5\) gradient steps. Without backpropagation, the total training time would exceed 200,000 years. Backpropagation reduces this to exactly two passes per step (one forward, one backward), making the entire training feasible in a matter of weeks on a large cluster. This is not a theoretical curiosity — it is the difference between impossible and routine.

### 1.2 The Core Idea: Reverse-Mode Computation

Consider a function built by composing many simple operations. The chain rule from calculus tells us we can compute the derivative of the final output with respect to any intermediate variable by multiplying local derivatives along the computation path. The question is: which order minimizes work?

Backpropagation answers: **start at the cost, and propagate gradients backward through the computation graph.** Every intermediate gradient is computed once and reused wherever it is needed upstream. This is the same algorithmic insight that powers reverse-mode automatic differentiation in every modern deep learning framework.

**Prerequisite Check.** We assume you are comfortable with:

- The chain rule for scalar and vector-valued functions (Section 2 will refresh this).
- Computational graphs as directed acyclic graphs where nodes are operations and edges are data flow.
- Matrix multiplication, transposition, and element-wise (Hadamard) products.
- The anatomy of a feedforward network: input layer, hidden layers with activation functions, output layer, and a scalar cost.

If any term above feels unfamiliar, review it before continuing — the rest of the lecture builds directly on these ideas.

---

## 2. The Chain Rule as the Backbone

### 2.1 Intuition: Local Derivatives and Signal Flow

Think of the computation as an electrical circuit flowing forward from inputs to cost. Each node holds a voltage — the numerical value computed during the forward pass. Now imagine we apply a unit current source at the cost node and ask: *what is the resulting current at each upstream node?* The chain rule answers by multiplying the **local conductance** (the derivative of a node’s output with respect to its input) by the **incoming signal** from downstream.

This is more than a metaphor. In circuit analysis, current divides across parallel branches and sums at junctions — exactly the behavior captured by the multivariable chain rule in Section 2.5. The same summation-over-paths principle governs how gradients accumulate when a node feeds multiple consumers.

**A real-world case study to ground this intuition:** In 2017, a team at Google Brain trained a neural machine translation model (the Transformer) to convert English sentences to French. During backpropagation through the self-attention layers, each word’s representation receives gradient signals from every other word in the sentence through the attention weights. If the French word "chien" should have been predicted but wasn't, the error signal flows backward through the attention mechanism, distributing blame across all English words that contributed to the incorrect prediction — with "dog" receiving the strongest corrective signal. This is the multivariable chain rule in action: the gradient at each English word embedding is the sum of contributions from every French output position it influenced. Without this summation-over-paths, the model could never learn which input words matter for which output words. This exact mechanism underlies every modern translation system, from Google Translate to DeepL.

### 2.2 Scalar Chain Rule (Refresher)

If \(y = f(x)\) and \(z = g(y)\), then:

\[
\frac{dz}{dx} = \frac{dz}{dy} \cdot \frac{dy}{dx}
\]

The term \(\frac{dz}{dy}\) is the signal arriving at \(y\), and \(\frac{dy}{dx}\) is the local sensitivity of \(y\) to \(x\).

### 2.3 Vector-Jacobian Product: The Workhorse

In neural networks, intermediates are rarely scalars. Let \(\mathbf{x} \in \mathbb{R}^m\), \(\mathbf{y} = f(\mathbf{x}) \in \mathbb{R}^n\), and \(z = g(\mathbf{y}) \in \mathbb{R}\). The gradient of \(z\) with respect to \(\mathbf{x}\) is:

\[
\nabla_{\mathbf{x}} z = \left( \frac{\partial \mathbf{y}}{\partial \mathbf{x}} \right)^\top \nabla_{\mathbf{y}} z
\]

where \(\frac{\partial \mathbf{y}}{\partial \mathbf{x}}\) is the \(n \times m\) **Jacobian matrix** whose \((i,j)\) entry is \(\partial y_i / \partial x_j\).

**Why the transpose?** The incoming gradient \(\nabla_{\mathbf{y}} z\) is a column vector of shape \(n \times 1\). To map it back to the input space of dimension \(m\), we multiply by the \(m \times n\) transposed Jacobian. This product transforms a downstream gradient into an upstream gradient — it is the **vector-Jacobian product (VJP)**.

**Try this yourself:** Before reading further, take a minute to verify the dimensional logic. If \(\mathbf{x} \in \mathbb{R}^m\) and \(z\) is a scalar, \(\nabla_{\mathbf{x}} z\) must have shape \(m \times 1\). The incoming gradient \(\nabla_{\mathbf{y}} z\) has shape \(n \times 1\). What shape must the matrix multiplying it have to produce an \(m \times 1\) output? This simple check — \(m \times 1 = (m \times n)(n \times 1)\) — catches the majority of transpose errors before they propagate.

**Practical application — debugging a PyTorch model:** A common error when implementing custom autograd functions is a shape mismatch in the `backward()` method. Suppose you have a layer that maps from dimension 256 to dimension 10. The incoming gradient `grad_output` has shape `[batch_size, 10]`. You compute the gradient with respect to the input as `grad_input = weight @ grad_output` — but this fails because `weight` is `10 x 256` and `grad_output` is `batch_size x 10`. The dimensional analysis above immediately reveals the fix: you need `weight.T @ grad_output`, yielding shape `256 x batch_size`. Without this check, the error manifests as an opaque runtime exception; with it, you catch the transpose bug before running a single line of code.

### 2.4 Worked Scalar-to-Vector Example

Let \(\mathbf{x} = [x_1, x_2]^\top\). Define \(y_1 = 3x_1 + x_2\), \(y_2 = x_1^2\), and \(z = y_1 + 2y_2\). We want \(\nabla_{\mathbf{x}} z\).

*Forward values:* Suppose \(x_1 = 2, x_2 = -1\). Then \(y_1 = 5\), \(y_2 = 4\), \(z = 13\).

*Downstream gradient:* \(\nabla_{\mathbf{y}} z = [\partial z/\partial y_1, \; \partial z/\partial y_2]^\top = [1, 2]^\top\).

*Jacobian of \(\mathbf{y}\) w.r.t. \(\mathbf{x}\):*
\[
\frac{\partial \mathbf{y}}{\partial \mathbf{x}} =
\begin{bmatrix}
\frac{\partial y_1}{\partial x_1} & \frac{\partial y_1}{\partial x_2} \\
\frac{\partial y_2}{\partial x_1} & \frac{\partial y_2}{\partial x_2}
\end{bmatrix}
= \begin{bmatrix} 3 & 1 \\ 2x_1 & 0 \end{bmatrix}
= \begin{bmatrix} 3 & 1 \\ 4 & 0 \end{bmatrix}
\]

*Upstream gradient:*
\[
\nabla_{\mathbf{x}} z =
\begin{bmatrix} 3 & 4 \\ 1 & 0 \end{bmatrix}
\begin{bmatrix} 1 \\ 2 \end{bmatrix}
= \begin{bmatrix} 3\cdot1 + 4\cdot2 \\ 1\cdot1 + 0\cdot2 \end{bmatrix}
= \begin{bmatrix} 11 \\ 1 \end{bmatrix}
\]

Check via direct differentiation: \(z = 3x_1 + x_2 + 2x_1^2\), so \(\partial z/\partial x_1 = 3 + 4x_1 = 11\), \(\partial z/\partial x_2 = 1\). Matches.

### 2.5 The Multivariable Chain Rule (Sum Over Paths)

In a computational graph, a node \(u^{(j)}\) may influence the final cost \(u^{(n)}\) through multiple downstream consumers. The gradient must sum contributions from all such paths:

\[
\frac{\partial u^{(n)}}{\partial u^{(j)}} = \sum_{i:\, j \in \text{Parents}(u^{(i)})} \frac{\partial u^{(n)}}{\partial u^{(i)}} \frac{\partial u^{(i)}}{\partial u^{(j)}}
\]

This is the **multivariable chain rule**: a node receives gradient signals from every operation that directly uses it, and those signals add.

**Misconception Alert.** A common error is to apply the single-path chain rule when a node feeds into multiple downstream operations. Omitting the sum silently drops entire pathways of influence. Always ask: “Which nodes directly consume this intermediate?” Sum over all of them.

**Quick Check.** In the graph \(a \to b \to d\), \(a \to c \to d\) with \(d = b + c\), write the formula for \(\partial d / \partial a\). *(Answer: \(\frac{\partial d}{\partial a} = \frac{\partial d}{\partial b}\frac{\partial b}{\partial a} + \frac{\partial d}{\partial c}\frac{\partial c}{\partial a}\).)*

**Real-world manifestation — ResNet skip connections:** In a ResNet-50 trained on ImageNet, each residual block computes \(\mathbf{y} = \mathcal{F}(\mathbf{x}) + \mathbf{x}\), where \(\mathcal{F}\) is a small subnetwork and \(\mathbf{x}\) is the identity skip connection. During backpropagation, the gradient at \(\mathbf{x}\) receives contributions from *two* paths: one through \(\mathcal{F}\) (carrying the gradient of the residual branch) and one through the identity connection (carrying the gradient unchanged). The multivariable chain rule tells us these add: \(\frac{\partial J}{\partial \mathbf{x}} = \frac{\partial J}{\partial \mathbf{y}} \cdot \frac{\partial \mathcal{F}}{\partial \mathbf{x}} + \frac{\partial J}{\partial \mathbf{y}}\). This summation is precisely what prevents vanishing gradients in very deep networks — even if \(\frac{\partial \mathcal{F}}{\partial \mathbf{x}}\) becomes very small, the identity path guarantees that \(\frac{\partial J}{\partial \mathbf{y}}\) still reaches earlier layers. Without this additive property, ResNets deeper than 20 layers would fail to train, just as plain networks did before the residual connection was introduced in 2015.

---

## 3. Dynamic Programming: Fill the Table Once

### 3.1 The Problem with Naive Recursion

If we recursively applied the chain rule from the cost back to the inputs without caching, we would recompute the gradient at a node every time it is encountered on a different path. In a graph with many shared subexpressions (e.g., a weight matrix used in multiple forward passes), the number of redundant computations grows exponentially with depth.

Think of it like computing Fibonacci numbers recursively without memoization: Fib(100) calls Fib(99) and Fib(98), but Fib(99) independently calls Fib(98) again. The same subproblem is solved exponentially many times. In a neural network, a weight matrix in layer 1 is the "Fib(98)" — reused by every downstream path, yet naively recomputed for each one.

### 3.2 Reverse Topological Ordering

Backpropagation avoids this by treating gradient accumulation as a **dynamic programming** problem. Each node in the computational graph has a memory slot storing its gradient \(\frac{\partial J}{\partial u}\). We fill these slots in **reverse topogical order** — from the cost node backward to the inputs. Because a node is processed only after all its consumers have been processed, each local gradient is computed exactly once and then reused wherever it is needed upstream.

**Analogy.** Imagine filling out a spreadsheet where each cell depends on cells to its right. If you fill columns from right to left, every formula references already-computed values. Backpropagation does the same for the computational graph: process nodes in reverse dependency order, and every gradient you need is already in memory. The cost? One forward pass to compute and store all intermediate values, then one backward pass to accumulate gradients — \(O(\text{number of operations})\) total, versus exponential for naive recursion.

**Try this yourself:** Draw a simple computational graph — say \(x \to a = x^2\), \(x \to b = \sin(x)\), and \(y = a + b\). Identify the reverse topological order. Which node must you process first: \(y\), \(a\), \(b\), or \(x\)? Convince yourself that processing \(y\) first gives you the gradient signal needed to compute \(\partial y/\partial a\) and \(\partial y/\partial b\), which then flow to \(x\).

**A case study in computational savings — neural style transfer:** In 2016, the popular artistic style transfer algorithm (Gatys et al.) used a pretrained VGG-19 network as a fixed feature extractor. The optimization loop updated *pixels* of a generated image, not network weights. Each iteration required backpropagating through all 19 layers of VGG — roughly 144 million parameters. Because the computation graph contains extensive weight sharing (the same convolutional filters are applied at every spatial position), a naive path-enumeration approach would trace gradients through each of the ~\(10^5\) spatial positions separately for each filter, yielding on the order of \(10^{11}\) subcomputations per iteration. The dynamic programming approach of backpropagation computes each filter's gradient exactly once, summing spatial contributions via the multivariable chain rule, reducing the work to approximately \(10^8\) operations. On a 2016 GPU, this meant 200 milliseconds per iteration instead of an estimated 3 minutes — the difference between an interactive creative tool and a batch process that runs overnight.

---

## 4. Backpropagation Through a Two-Layer Network

### 4.1 Network Architecture and Notation

We now make everything concrete. Consider a two-layer network:

- **Input:** \(\mathbf{x} \in \mathbb{R}^d\)
- **Hidden layer:** \(\mathbf{h} = \sigma(W^{[1]}\mathbf{x} + \mathbf{b}^{[1]})\), where \(W^{[1]} \in \mathbb{R}^{h \times d}\), \(\mathbf{b}^{[1]} \in \mathbb{R}^h\), and \(\sigma\) is an element-wise activation (e.g., ReLU, sigmoid).
- **Output layer:** \(\hat{\mathbf{y}} = W^{[2]}\mathbf{h} + \mathbf{b}^{[2]} \in \mathbb{R}^k\)
- **Scalar cost:** \(J = \ell(\hat{\mathbf{y}}, \mathbf{y}_{\text{true}})\) for some loss function \(\ell\) (e.g., mean squared error, cross-entropy).

**A real-world case study to ground this:** In 2012, AlexNet classified 1.2 million images into 1,000 categories using a deep convolutional network. Each training step required computing gradients through 60 million parameters across eight layers. Without backpropagation, estimating those gradients via finite differences would require 60 million forward passes per image — roughly 200 years of GPU time per training epoch. Backpropagation reduced this to exactly two passes (one forward, one backward), making the entire training feasible in under a week. The architecture above is a simplified two-layer cousin of that network, but the gradient-flow logic is identical.

**Another concrete example — spam detection in production:** A two-layer network with 10,000 input features (bag-of-words), 500 hidden units, and 1 output (spam probability) is a common baseline for email filtering at scale. With \(d = 10,000\), \(h = 500\), and \(k = 1\), the network has \(W^{[1]}\) of size \(500 \times 10,000 = 5\) million weights, plus \(W^{[2]}\) of size \(1 \times 500 = 500\) weights. Training on 1 million emails with mini-batch SGD (batch size 100) requires 10,000 gradient steps per epoch. Without backpropagation, a finite-difference estimate of the gradient would need 5 million forward passes per step — 50 billion forward passes per epoch. On a single CPU doing 1,000 forward passes per second, that is roughly 580 days per epoch. Backpropagation computes the exact gradient in two passes per step — 20,000 forward-equivalent operations per epoch — completing in about 20 seconds. This is the operational difference that makes spam filters, recommendation systems, and fraud detectors economically viable to train and retrain daily.

### 4.2 Forward Pass: Store Everything

During the forward pass, we compute and **store** every intermediate: \(\mathbf{x}\), the linear combination \(\mathbf{z}^{[1]} = W^{[1]}\mathbf{x} + \mathbf{b}^{[1]}\), the activation \(\mathbf{h} = \sigma(\mathbf{z}^{[1]})\), \(\mathbf{z}^{[2]} = W^{[2]}\mathbf{h} + \mathbf{b}^{[2]}\), and \(\hat{\mathbf{y}} = \mathbf{z}^{[2]}\) (for simplicity; the output may also pass through an activation, but we absorb it into the loss).

Why store? Because the backward pass needs the *numerical values* of these intermediates to evaluate local derivatives. For instance, if \(\sigma\) is ReLU, its derivative at \(\mathbf{z}^{[1]}\) depends on which entries were positive during the forward pass. Without the cached \(\mathbf{z}^{[1