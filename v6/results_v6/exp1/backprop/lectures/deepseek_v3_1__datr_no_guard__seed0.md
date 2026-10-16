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

**Quick self-check — Prerequisites warm-up:**

1. If \(W \in \mathbb{R}^{3 \times 4}\) and \(x \in \mathbb{R}^{4 \times 1}\), what is the shape of \(Wx\)? (Answer: \(3 \times 1\))
2. Compute \(\frac{d}{dz}\sigma(z)\) for \(\sigma(z) = \frac{1}{1+e^{-z}}\). (Answer: \(\sigma(z)(1-\sigma(z))\))
3. If \(J(\theta)\) measures prediction error, what does \(\frac{\partial J}{\partial \theta_k} < 0\) tell you about how to update \(\theta_k\)? (Answer: increasing \(\theta_k\) will decrease \(J\))

If any of these was unclear, review the prerequisites before continuing.

### 1.2 The Core Problem

**Opening hook.** Imagine you are training a neural network with one million parameters. You need the gradient of the loss with respect to every single parameter. The obvious approach — perturb each parameter slightly, run the entire forward pass again, measure the change — would require one million forward passes. For a network that takes one second per forward pass, that's 11.5 days per gradient step. Training for 10,000 steps would take 315 years. This is not an exaggeration; it is the computational reality that made neural networks impractical before 1986.

**Pause and visualize.** Before proceeding, close your eyes for ten seconds and actually picture this: you are standing in front of a rack of servers. To get one gradient vector, you must press a button one million times. Each button press triggers a full forward computation through every layer of your network. The fans whir for one second. Then the next press. One million seconds. Now imagine doing this ten thousand times. What you are visualizing is the computational landscape that researchers faced in the early 1980s — a landscape where deep networks were theoretically interesting but practically impossible. The algorithm we are about to study collapses those 315 years into hours.

**Try this yourself:** Before reading further, estimate how long it would take to train a 100-million-parameter network using the perturbation method on your laptop. Assume each forward pass takes 10 milliseconds. You need at least 100 million forward passes per gradient step, and perhaps 100,000 gradient steps to converge. What is the total time? (Answer: \(10^8 \times 10^{-2} \times 10^5 = 10^{11}\) seconds, or about 3,170 years. Backpropagation does it in hours.)

In 1986, a paper by Rumelhart, Hinton, and Williams changed the trajectory of neural network research. But here is what makes their contribution surprising: they did not invent a new calculus rule, nor did they propose a fundamentally different kind of network. They solved a bookkeeping problem. The chain rule already told us *what* to compute — the partial derivative of a loss with respect to every parameter in the network. The unanswered question was *how* to compute it without the cost exploding exponentially with depth. Without a solution, training a network with more than a handful of layers was computationally hopeless. Backpropagation is that solution, and at its heart, it is dynamic programming applied to calculus.

Consider a feedforward network with \(P\) parameters, where \(P\) can easily reach millions. We need \(\nabla_{\theta} J\), the vector of all \(P\) partial derivatives \(\frac{\partial J}{\partial \theta_{k}}\), so that we can update each parameter by a small step downhill:

\[
\theta_{k} \leftarrow \theta_{k} - \eta \frac{\partial J}{\partial \theta_{k}}
\]

Here is the tension that makes this problem worth studying carefully: the chain rule tells us *what* to compute — it is just a mechanical application of calculus. The challenge is *how* to compute it without wasting computation. If we are not careful, we will recompute the same intermediate derivatives repeatedly, making training impossibly slow. Backpropagation organizes this computation so that its cost is no more than a constant multiple of the forward pass. This is not a trick; it is the same algorithmic insight that powers dynamic programming in shortest-path algorithms, just dressed in calculus.

**Pause and predict:** Before we derive the algorithm, ask yourself: if a value \(v\) is used by three different downstream computations, how many times should we compute \(\frac{\partial J}{\partial v}\)? Once, or three times? Why? The answer reveals exactly what backpropagation does differently from naive chain rule expansion.

**Real-world stakes.** Consider the following concrete deployment scenarios where backpropagation is the computational engine that makes training feasible:

1. **Large language models (GPT-style transformers).** Training a model like GPT-4 involves a network with hundreds of billions of parameters and a computational graph spanning thousands of tokens per sequence. A single forward pass through such a model costs millions of floating-point operations. Without backpropagation, computing the gradient with respect to every parameter by numerical finite differences would require one additional forward pass *per parameter* — roughly \(10^{11}\) forward passes for a single gradient vector. That is not merely slow; it is physically impossible on any existing hardware. Backpropagation computes the full gradient in a single backward pass whose cost is approximately equal to the forward pass. Every large language model in production today — from ChatGPT to Claude to Gemini — is trained using exactly the algorithm described in this lecture.

2. **Medical image segmentation (U-Net architectures).** In clinical settings, convolutional neural networks like U-Net are trained to segment tumors in CT or MRI scans. These networks have skip connections that create complex branching patterns in the computational graph, where a single intermediate feature map influences the final loss through multiple parallel paths (the contracting path and the expanding path). Backpropagation automatically sums the gradient contributions from all paths via the recurrence \(\delta_i = \sum_{j \in \text{Children}(v_i)} \delta_j \cdot \frac{\partial v_j}{\partial v_i}\). A radiologist relying on this segmentation for treatment planning is, indirectly, depending on the correctness of the backpropagation algorithm that trained the model.

3. **Autonomous driving perception (multi-task networks).** A perception system in a self-driving car often uses a shared backbone network (e.g., ResNet) with multiple heads: one for object detection, one for lane segmentation, one for depth estimation. The total loss is a weighted sum \(J = \alpha J_{\text{det}} + \beta J_{\text{seg}} + \gamma J_{\text{depth}}\). During backpropagation, the gradient signals from all three heads flow backward into the shared backbone and are summed. This is the same branching-and-summing pattern we will work through by hand in Section 3.4. The gradient that updates the early convolutional filters reflects a compromise across all tasks — a compromise computed efficiently by backpropagation in a single backward pass rather than three separate ones.

4. **Smartphone keyboard autocomplete (recurrent neural networks).** When you type on a smartphone and see word suggestions, a recurrent neural network or small transformer is running locally on the device, trained on billions of typing events collected across users. Training this model involves backpropagation through time (BPTT), which unrolls the recurrent computation into a very deep computational graph — one layer per time step. The backward pass must propagate gradients through hundreds or thousands of time steps. The vanishing gradient problem (Section 5) is not an abstract concern here: if gradients vanish, the network cannot learn long-range dependencies like subject-verb agreement across a long sentence. Practical solutions like LSTMs and GRUs were developed specifically because backpropagation revealed this failure mode.

**What these examples share.** In every case, the computational graph of the model is large, deeply nested, and heavily branched. The forward pass computes predictions; the backward pass computes gradients. The efficiency of the backward pass — one traversal of the graph, each local derivative computed exactly once — is what makes training these models possible at all. When you understand backpropagation, you understand the algorithmic foundation of modern deep learning.

---

## 2. Intuition First: A Concrete Example with Three Functions

Before introducing graphs or summations, we trace through the simplest possible composition.

**A motivating analogy.** Imagine you are the manager of a factory with three sequential workstations. Station 1 takes raw material \(x\) and produces part \(v_{1}\). Station 2 transforms \(v_{1}\) into \(v_{2}\). Station 3 assembles \(v_{2}\) into the finished product \(J\). One day, a customer asks: "If I change the raw material slightly, how much does the final product change?" You could shut down the factory, feed in a slightly different \(x\), run the whole line again, and measure the difference. That is finite differences — one full factory run per parameter. Or you could walk backward through the factory with a clipboard. At Station 3, you ask: "If I hand you a slightly different \(v_{2}\), how much does \(J\) change?" The station manager gives you a number — the local sensitivity \(f_{3}'(v_{2})\). You write it down. You walk to Station 2 and ask the same question about \(v_{1}\). The manager gives you \(f_{2}'(v_{1})\), and you multiply it by the number you already have from Station 3. By the time you reach the loading dock, you have the full sensitivity \(\frac{dJ}{dx}\) without running the factory even once more. Backpropagation is walking backward through the factory with a clipboard, multiplying as you go.

**Try this yourself:** Extend the factory analogy to a branching production line where Station 2's output feeds into two parallel Station 3s (3a and 3b), and their outputs are combined at Station 4. How would the clipboard walk change? What do you do when you reach Station 2 and it has two children? (You'll need to collect numbers from both children and add them. This foreshadows the summation in the backpropagation recurrence.)

**A concrete industrial instantiation.** This factory analogy is not merely metaphorical. Consider a chemical engineering application: a distillation column for separating crude oil into fractions (gasoline, diesel, kerosene). The column is modeled as a sequence of theoretical plates, each described by nonlinear vapor-liquid equilibrium equations. The output purity \(J\) depends on the feed composition \(x\) through dozens of plates. Engineers need \(\frac{dJ}{dx}\) — the sensitivity of output purity to feed composition — to optimize the process. Before automatic differentiation tools became widespread, this derivative was computed by perturbing \(x\) and re-simulating the entire column, at substantial computational expense. Modern process simulators use exactly the backpropagation algorithm: they trace the computational graph of the column model backward, multiplying local Jacobians at each plate. The same algorithm that trains neural networks also optimizes oil refineries.

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

**Practical takeaway for real networks.** In a 100-layer ResNet trained on ImageNet (1.2 million images, 1000 classes), the forward pass evaluates approximately \(10^8\) intermediate activations. Finite-difference gradient estimation would require \(10^8\) additional forward passes per gradient step — roughly \(10^{16}\) operations per step. Backpropagation computes all gradients in a single backward pass of comparable cost to the forward pass. This is the difference between training for one hour on 8 GPUs and training for longer than the age of the universe.

---

## 3. The Computational Graph and the Generalized Chain Rule

### 3.1 Representing Computation as a Graph

We now make the structure explicit. Every computation in the network is a node in a directed acyclic graph (DAG). Edges point from inputs to outputs: if \(v_{j}\) is computed directly from \(v_{i}\), we draw \(v_{i} \rightarrow v_{j}\).

**A cross-domain connection worth pausing on.** If you have ever used a spreadsheet, you already understand computational graphs. When you write `=A1*B1` in cell C1, you create a node whose value depends on two parent cells. When you change A1, the spreadsheet does not recompute the entire workbook from scratch — it traces the dependency graph and recomputes only the cells downstream of A1. Now imagine a *reverse* spreadsheet: instead of asking "if I change A1, which cells update?" you ask "if I want cell Z100 to decrease, how should I nudge A1?" That reverse spreadsheet needs to propagate sensitivity backward through the same dependency graph, multiplying local rates of change along each edge. That is backpropagation. The computational graph of a neural network is a spreadsheet formula, and backpropagation is the "Goal Seek" feature run in reverse.

**Real-world spreadsheet example.** Financial analysts routinely build multi-sheet workbooks where cell Z100 (net present value of a project) depends on thousands of intermediate calculations — revenue projections, discount rates, tax assumptions, depreciation schedules. When an analyst asks, "Which assumption has the largest impact on NPV?" they are asking for the gradient. Excel's built-in "Data Table" and "Solver" tools compute sensitivity by finite differences: perturb one input, recalculate the entire workbook, measure the change in Z100. For a workbook with 500 input assumptions, this requires 500 full recalculations. If the workbook takes 2 seconds to recalculate, the sensitivity analysis takes 1000 seconds (over 15 minutes). Backpropagation would compute all 500 sensitivities in a single backward pass of approximately 2 seconds — a 500× speedup. This is not hypothetical: tools like Google Sheets' "Explore" feature and modern probabilistic programming languages use automatic differentiation (backpropagation) for exactly this reason. The computational graph of a neural network is structurally identical to a spreadsheet dependency graph; the backpropagation algorithm is the same in both domains.

**Example graph.** Consider \(J = (w \cdot x) + b\). The nodes are:

- \(v_{1} = w\)
- \(v_{2} = x\)
- \(v_{3} = v_{1} \cdot v_{2}\) (multiplication)
- \(v_{4} = b\)
- \(v_{5} = v_{3} + v_{4}\) (addition, output \(J\))

Edges: \(v_{1} \rightarrow v_{3}\), \(v_{2} \rightarrow v_{3}\), \(v_{3} \rightarrow v_{5}\), \(v_{4} \rightarrow v_{5}\).

The forward pass evaluates nodes in topological order: \(v_{1}, v_{2}, v_{3}, v_{4}, v_{5}\). Each node stores its value.

**Try this yourself:** Draw the computational graph for \(J = (a + b) \cdot (a + c)\). Notice that \(a\) appears twice. Identify where the branching occurs and where the paths rejoin. This graph structure directly determines which adjoints get summed during backpropagation.

### 3.2 The Backpropagation Recurrence

Let \(\text{Pa}(v_{i})\) denote the parents of \(v_{i}\) (the nodes whose values are inputs to the function that computes \(v_{i}\)). Let \(\text{Children}(v_{i})\) denote the nodes that depend directly on \(v_{i}\).

The chain rule for a scalar output \(J\) and an intermediate node \(v_{i}\) is:

\[
\frac{\partial J}{\partial v_{i}} = \sum_{j \in \text{Children}(v_{i})} \frac{\partial J}{\partial v_{j}} \cdot \frac{\partial v_{j}}{\partial v_{i}}
\]

We define the **adjoint** (or **error signal**) \(\delta_{i} = \frac{\partial J}{\partial v_{i}}\).

The recurrence becomes:

\[
\delta_{i} = \sum_{j \in \