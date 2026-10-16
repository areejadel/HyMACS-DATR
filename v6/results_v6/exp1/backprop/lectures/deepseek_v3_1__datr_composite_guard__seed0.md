## 1. What We Already Know and What We Need

### 1.1 Prerequisites

We assume you are comfortable with:

- **Matrix multiplication** and its shape rules: if \(A \in \mathbb{R}^{m \times n}\) and \(B \in \mathbb{R}^{n \times p}\), then \(AB \in \mathbb{R}^{m \times p}\).
- **Elementary calculus**: the derivative of \(x^{2}\) is \(2x\); the derivative of \(\sigma(z) = \frac{1}{1+e^{-z}}\) is \(\sigma(z)(1-\sigma(z))\); the chain rule \(\frac{d}{dx} f(g(x)) = f'(g(x))\, g'(x)\).
- **The purpose of training a neural network**: we have a dataset of input–target pairs, we feed inputs forward to obtain predictions, we measure the discrepancy between predictions and targets with a scalar cost \(J\), and we adjust the weights and biases to make \(J\) smaller.

### 1.2 The Core Problem

Here is a puzzle that should bother you: you have a function with millions of knobs (the parameters), and you need to figure out which way to turn each knob to make the output slightly better. Calculus gives you the answer — the gradient — but if you compute it the obvious way, you will spend more time recalculating the same things than actually training. The cost explodes exponentially with depth.

Consider a feedforward network with \(P\) parameters, where \(P\) can easily reach millions. We need \(\nabla_{\theta} J\), the vector of all \(P\) partial derivatives \(\frac{\partial J}{\partial \theta_{k}}\), so that we can update each parameter by a small step downhill:

\[
\theta_{k} \leftarrow \theta_{k} - \eta \frac{\partial J}{\partial \theta_{k}}
\]

Here is the tension that makes this problem worth studying carefully: the chain rule tells us *what* to compute — it is just a mechanical application of calculus. The challenge is *how* to compute it without wasting computation. If we are not careful, we will recompute the same intermediate derivatives repeatedly, making training impossibly slow. Backpropagation organizes this computation so that its cost is no more than a constant multiple of the forward pass. This is not a trick; it is the same algorithmic insight that powers dynamic programming in shortest-path algorithms, just dressed in calculus.

**Concrete real-world motivation.** Consider training a ResNet-50 image classifier on the ImageNet dataset. This network has approximately 25.5 million parameters. The forward pass for a single 224×224 RGB image involves roughly 4 billion floating-point operations (4 GFLOPs). If we computed the gradient of the loss with respect to each parameter independently using finite differences — perturbing one parameter at a time and running the forward pass again — we would need 25.5 million forward passes, costing over \(10^{17}\) FLOPs per image. That is roughly the computational capacity of a modern exascale supercomputer for several minutes, just to process a single training example. Backpropagation computes the full gradient in approximately 8 GFLOPs — roughly twice the forward pass — making it feasible to train on millions of images. This factor of roughly two between forward and backward cost is not accidental; it is a direct consequence of the dynamic programming structure we will study.

**Another practical lens: training large language models.** When training a model like GPT-3 (175 billion parameters) on a corpus of hundreds of billions of tokens, the gradient computation must scale linearly with model size. Without backpropagation, the cost would be quadratic or exponential in depth, rendering the entire enterprise impossible. The fact that training such models is merely extremely expensive, rather than physically impossible, is a direct consequence of the algorithm we analyze in this lecture. Every time you read about a new large model release, you are seeing backpropagation's practical impact: it is the algorithmic engine that makes gradient-based learning tractable at scale.

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

**Think of it this way:** If you were hiking down from a mountain peak and wanted to know how a small nudge at the trailhead changes your summit elevation, you wouldn't climb the whole mountain once for each possible nudge. You'd walk down once, recording how each segment of trail responds to the terrain above it. Backpropagation is exactly that: one downward pass that records sensitivities, reusing every observation.

**Backpropagation approach.** We work backward, one step at a time, storing each derivative as we compute it.

1. Start at the output: \(\delta_{3} = \frac{dJ}{dJ} = 1\).
2. Move to \(v_{2}\): \(\delta_{2} = \frac{dJ}{dv_{2}} = \delta_{3} \cdot f_{3}'(v_{2})\).
3. Move to \(v_{1}\): \(\delta_{1} = \frac{dJ}{dv_{1}} = \delta_{2} \cdot f_{2}'(v_{1})\).
4. Move to \(x\): \(\delta_{x} = \delta_{1} \cdot f_{1}'(x)\).

Notice: each local derivative \(f_{k}'\) is evaluated *once* and multiplied by the incoming signal from above. The total number of derivative evaluations equals the number of function evaluations in the forward pass. We never recompute anything.

**Check your understanding.** Suppose \(f_{1}(x) = x^{2}\), \(f_{2}(v) = \exp(v)\), \(f_{3}(v) = \log(v)\), and \(x = 3\). Compute \(\frac{dJ}{dx}\) by both the naive method and the backpropagation method. Verify they give the same result. (Tracing: \(v_{1} = 9\), \(v_{2} = e^{9}\), \(J = \ln(e^{9}) = 9\). \(\delta_{3} = 1\), \(\delta_{2} = 1 \cdot 1/e^{9}\), \(\delta_{1} = (1/e^{9}) \cdot e^{9} = 1\), \(\delta_{x} = 1 \cdot 6 = 6\).)

**A practical application: sensitivity analysis in engineering design.** The backpropagation pattern we just traced — computing the derivative of a scalar output with respect to a scalar input through a chain of functions — appears far beyond neural networks. In computational fluid dynamics, engineers designing aircraft wings compute how the lift-to-drag ratio (a scalar output) changes with respect to a shape parameter (a scalar input) through a chain of mesh generation, flow solving, and post-processing steps. Using what is called the *adjoint method* — which is mathematically identical to backpropagation — they compute this derivative in time proportional to one forward simulation, rather than one simulation per design parameter. This has been a standard tool in aerodynamic shape optimization since the 1980s, independently developed from neural network backpropagation but sharing the identical dynamic programming insight. The same adjoint approach is used in seismic inversion (oil exploration), climate model tuning, and any domain where a scalar loss depends on many parameters through a deterministic chain of computations.

---

## 3. The Computational Graph and the Generalized Chain Rule

### 3.1 Representing Computation as a Graph

We now make the structure explicit. Every computation in the network is a node in a directed acyclic graph (DAG). Edges point from inputs to outputs: if \(v_{j}\) is computed directly from \(v_{i}\), we draw \(v_{i} \rightarrow v_{j}\).

**A concrete analogy before we abstract:** Think of the computational graph as a circuit board. Each node is a component — a multiplier, an adder, a sigmoid — with input pins and output pins. The forward pass is applying voltage to the inputs and measuring what appears at each component's output. The backward pass is asking: "If I wiggle the voltage at this output pin by 1 millivolt, how much does the final output wiggle?" That sensitivity propagates backward through each component according to its own local behavior, exactly like an electrical engineer computing small-signal sensitivity in a nonlinear circuit. The math is identical.

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

**Practical impact: automatic differentiation frameworks.** The computational graph abstraction is not just a pedagogical device — it is the operational model underlying every modern deep learning framework. PyTorch's `autograd` engine and TensorFlow's `GradientTape` both construct a dynamic computational graph during the forward pass, recording each operation and its inputs. When `.backward()` is called, they execute exactly the reverse topological traversal we just described. Understanding this graph structure directly explains why certain operations break gradient flow (in-place mutations that overwrite saved forward values), why `detach()` prevents gradient propagation (it severs the graph edge), and why checkpointing works (it trades recomputation of forward values for memory by discarding and recomputing selected nodes). When you debug a `RuntimeError: Trying to backward through the graph a second time`, you are seeing the consequence of the graph being freed after one backward pass to save memory — a design choice that follows directly from the one-shot nature of the algorithm.

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

**Real-world manifestation: shared weights in convolutional networks.** The branching pattern we just analyzed — where one value fans out to multiple downstream computations and its gradient sums contributions from each path — is not a toy example. In a convolutional neural network, each filter weight is applied at every spatial location of the input feature map. If you have a \(3 \times 3\) convolution operating on a \(224 \times 224\) input, that single weight value is used in approximately 50,000 distinct multiply-add operations. During backpropagation, the gradient for that weight is the *sum* of 50,000 local gradient contributions — exactly the pattern we computed for \(a\) with two branches, scaled up by four orders of magnitude. This is why frameworks implement convolution backward passes as highly optimized kernels: naively looping over all 50,000 contributions would be correct but impractically slow. The same summation-over-branches pattern appears in recurrent neural networks (where a hidden state feeds into itself at the next time step, creating a chain of contributions through time) and in attention mechanisms (where each query interacts with all keys).

---

## 4. Backpropagation for a Two-Layer Neural Network

### 4.1 Architecture and Notation

We now move from scalar toy examples to the vectorized setting that actual training code uses. Consider a two-layer network:

\[
z^{[1]} = W^{[1]} x + b^{[1]}, \quad a^{[1]} = \sigma(z^{[1]})
\]
\[
z^{[2]} = W^{[2]} a