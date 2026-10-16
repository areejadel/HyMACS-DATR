## 1. Prerequisites and the Problem Setting

### The Core Problem

Consider training a neural network to recognize handwritten digits. The network makes a prediction, compares it to the true label, and computes a single scalar cost \(J\) representing the prediction error. The goal is to adjust the network’s millions of parameters to make \(J\) smaller on subsequent examples.

These parameters — the weights and biases — are denoted collectively by \(\boldsymbol{\theta}\). Gradient-based optimizers require \(\nabla_{\boldsymbol{\theta}} J\), the vector of partial derivatives that indicates how each parameter influences the cost. Parameters with large positive gradients should be decreased; those with large negative gradients should be increased.

**The naive approach fails catastrophically.** Computing \(\frac{\partial J}{\partial \theta_k}\) for a single parameter requires tracing the chain rule from \(\theta_k\) all the way to \(J\) through the entire network. For a network with one million parameters, this demands one million complete traversals. If one forward pass takes 10 ms, a single gradient step would take roughly three hours. Training a modern network for 100,000 steps would be infeasible.

**The escape.** What if we could compute *all* one million gradients in roughly the time of just *two* passes through the network — one forward, one backward? That is back-propagation. The million gradient paths massively overlap; they share subcomputations like branches of a tree share roots. Back-propagation computes each shared subcomputation once and reuses it everywhere, turning an exponential disaster into a linear miracle.

**Try this yourself:** Before reading further, estimate: if your network has \(10^6\) parameters and a forward pass takes 10 ms, how long would naive gradient computation take? How long would back-propagation take? (Answer below.)

*Answer:* Naive: \(10^6 \times 10\text{ ms} = 10{,}000\) seconds (≈ 3 hours) per gradient step. Back-propagation: roughly 20 ms (one forward + one backward pass). That is a speedup of about 500,000×. This is not an optimization trick — it is the difference between impossible and routine.

**Interactive exploration — Simulate the speedup:** Open a Python interpreter and time the difference yourself. Write a function that computes gradients naively by looping over parameters and calling `autograd.grad` separately for each one. Compare its runtime to a single `autograd.grad` call that computes all gradients at once. On a small network with 10,000 parameters, you will already see a 100–1,000× speedup. The gap grows quadratically with parameter count — try it with 50,000 parameters and watch the naive version time out. This hands-on experiment makes the theoretical 500,000× speedup visceral: you experience the moment where naive gradient computation becomes physically impossible, and back-propagation becomes the only viable path forward.

### Required Background

We assume familiarity with:

- **Matrix multiplication and broadcasting:** products \(\mathbf{A}\mathbf{B}\), transposes, and sums over rows/columns.
- **Partial derivatives and the chain rule:** for scalar functions, \(\frac{\partial}{\partial x} f(g(x)) = f'(g(x))\, g'(x)\). We extend this to vectors and matrices.
- **Feedforward neural network structure:** input → hidden layers → output → loss.
- **Gradient-based optimization:** the idea that we update parameters via \(\boldsymbol{\theta} \leftarrow \boldsymbol{\theta} - \eta \nabla_{\boldsymbol{\theta}} J\).

If any of these feel shaky, pause and review them — they are the substrate on which back-propagation is built.

**Summary:** Training a network requires the gradient of the cost \(J\) with respect to all parameters \(\boldsymbol{\theta}\). Naive per-parameter gradient computation is exponentially expensive. Back-propagation exploits shared subcomputations to compute the full gradient in roughly the time of one forward and one backward pass, making deep network training tractable.

---

## 2. Computational Graphs: the Universal Language

### Intuition: A Recipe, Not a Formula

Think of a neural network not as a fixed equation but as a *recipe* — a sequence of operations. Each operation takes some inputs and produces an output. Some outputs become inputs to later operations. We can draw this as a directed graph.

**Example (before formalism):** Consider the simple expression \(J = (a \cdot b) + c^2\). We decompose it into operations:

1. \(u_1 = a \cdot b\) (multiply)
2. \(u_2 = c^2\) (square)
3. \(u_3 = u_1 + u_2\) (add)
4. \(J = u_3\) (identity for the root)

The graph has nodes \(\{a, b, c, u_1, u_2, u_3, J\}\). Edges: \(a \to u_1\), \(b \to u_1\), \(c \to u_2\), \(u_1 \to u_3\), \(u_2 \to u_3\), \(u_3 \to J\). The leaf nodes are \(a, b, c\) (inputs/parameters). The root is \(J\).

### Formal Definition

A **computational graph** is a directed acyclic graph (DAG) where:

- **Nodes** represent operations (variables or functions).
- **Edges** represent data flow: an edge from \(u^{(i)}\) to \(u^{(j)}\) means \(u^{(i)}\) is an input to the operation that produces \(u^{(j)}\).

We number nodes \(u^{(1)}, u^{(2)}, \dots, u^{(n)}\) in topological order (every node appears after its inputs). The root is \(u^{(n)} = J\), the scalar cost.

**Why this matters:** Every neural network architecture — feedforward, convolutional, recurrent, transformer — can be expressed as a computational graph. By developing back-propagation on the *graph*, we obtain an algorithm that works for all architectures uniformly. This is the insight that powers PyTorch, TensorFlow, and JAX: they do not hardcode backprop for each architecture; they build the graph dynamically and run the same backward-pass algorithm on whatever graph emerges.

**Concrete example — Convolutional Neural Network (CNN):** A 2D convolution layer \(\mathbf{Z} = \mathbf{W} \ast \mathbf{X} + \mathbf{b}\) (where \(\ast\) denotes convolution) unpacks into a computational subgraph: an `im2col` operation reshapes the input tensor \(\mathbf{X}\) into a matrix, a matrix multiply with the flattened filter bank \(\mathbf{W}\) produces the convolved output, and a broadcast add incorporates the bias \(\mathbf{b}\). The backward pass through this subgraph applies the transpose convolution (often implemented as `col2im` with rotated filters) to propagate gradients to \(\mathbf{X}\) and standard matrix derivative rules for \(\mathbf{W}\) and \(\mathbf{b}\). The same modular back-propagation framework handles this seamlessly — no special-case code needed.

**Real-world scenario — Image classification with ResNet-50:** When a ResNet-50 model classifies a 224×224 image into one of 1000 ImageNet categories, the computational graph contains approximately 50 convolutional layers, each with its own `im2col` → matmul → batch-norm → ReLU subgraph. During back-propagation, the gradient of the cross-entropy loss flows backward through all 50 layers. The `im2col` backward pass reconstructs the spatial gradient map that highlights which pixels in the original image most influenced the classification decision. This gradient map is the foundation of *saliency maps* and *class activation mapping (CAM)*, used to visually explain model predictions in medical imaging (e.g., highlighting tumors in X-rays) and autonomous driving (e.g., showing which road signs triggered a steering decision). Without efficient back-propagation through the convolution subgraph, computing these explanations for a single image would take minutes instead of milliseconds.

**Concrete example — Recurrent Neural Network (RNN):** An RNN unrolled over \(T\) time steps, \(\mathbf{h}_t = \tanh(\mathbf{W}_{hh} \mathbf{h}_{t-1} + \mathbf{W}_{xh} \mathbf{x}_t + \mathbf{b}_h)\), forms a computational graph with repeated weight-sharing nodes. The back-propagation through time (BPTT) algorithm is simply standard back-propagation applied to this unrolled graph. The gradient with respect to \(\mathbf{W}_{hh}\) accumulates contributions from every time step: \(\frac{\partial J}{\partial \mathbf{W}_{hh}} = \sum_{t=1}^{T} \frac{\partial J}{\partial \mathbf{h}_t} \cdot \frac{\partial \mathbf{h}_t}{\partial \mathbf{W}_{hh}}\), where each term flows through the chain \(\mathbf{h}_t \to \mathbf{h}_{t-1} \to \dots \to \mathbf{h}_1\). This reveals the vanishing/exploding gradient problem directly: the product of Jacobians \(\prod_{k=1}^{t} \frac{\partial \mathbf{h}_k}{\partial \mathbf{h}_{k-1}}\) can decay or explode exponentially with \(t\).

**Real-world scenario — Machine translation with LSTM:** Google's Neural Machine Translation system (GNMT) uses deep LSTMs to translate sentences from English to French. During training, an English sentence of 50 words is fed in, and the model predicts French words one by one. The computational graph unrolls across 50 time steps for the encoder and another 50 for the decoder. Back-propagation through time must carry gradient signals across all 100 steps. The LSTM's gating mechanism (forget gate \(f_t\), input gate \(i_t\), output gate \(o_t\)) is specifically designed to make the backward pass stable: the cell state \(c_t\) receives an additive update \(c_t = f_t \odot c_{t-1} + i_t \odot \tilde{c}_t\), so the gradient \(\frac{\partial c_t}{\partial c_{t-1}} = f_t\) is element-wise and bounded. When \(f_t \approx 1\), gradients flow unimpeded across dozens of time steps, enabling the model to learn long-range dependencies like subject-verb agreement across clauses. This design emerged directly from analyzing the back-propagation dynamics in the computational graph of vanilla RNNs.

**Concrete example — Transformer attention:** The scaled dot-product attention \(\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\!\left(\frac{\mathbf{Q}\mathbf{K}^\top}{\sqrt{d_k}}\right)\mathbf{V}\) decomposes into matrix multiplies, a scalar divide, a softmax (itself a subgraph of exponentials, sum-reduction, and division), and a final multiply. The backward pass computes gradients through the softmax Jacobian \(\mathbf{J}_{\text{softmax}} = \text{diag}(\mathbf{p}) - \mathbf{p}\mathbf{p}^\top\) (where \(\mathbf{p}\) is the attention weight vector), then propagates them to \(\mathbf{Q}\), \(\mathbf{K}\), and \(\mathbf{V}\) via standard matrix derivative rules. Modern frameworks handle this automatically — the user writes only the forward attention formula, and back-propagation constructs the backward graph.

**Real-world scenario — Large language model pretraining:** Training GPT-4 or Llama-3 on trillions of tokens involves computing self-attention over sequences of 8,000–128,000 tokens. The attention matrix \(\mathbf{A} = \text{softmax}(\mathbf{Q}\mathbf{K}^\top / \sqrt{d_k})\) is \(T \times T\), which for \(T = 128{,}000\) would require 64 GB of memory in float32 — infeasible on current GPUs. This forces *memory-efficient attention* algorithms like FlashAttention, which restructure the computation to avoid materializing the full attention matrix. FlashAttention tiling computes attention in blocks, and its backward pass *recomputes* the softmax attention weights on-the-fly rather than storing them from the forward pass. This is a practical realization of the memory–time trade-off discussed later: by trading extra computation (re-running the softmax during backward) for memory savings (not storing the \(T \times T\) matrix), FlashAttention enables training transformers on sequences 8–16× longer than naive implementations. The back-propagation algorithm's structure — specifically, which intermediate values must be saved for the backward pass — directly determines the memory bottleneck that FlashAttention solves.

**Try this yourself:** Before continuing, sketch the computational graph for \(z = (x + y) \cdot \max(x, 0)\). Label each node with its operation. Notice how the \(\max\) operation introduces a branch — this will matter for gradients.

### What We Want to Compute

For any node \(u^{(i)}\), we want:

\[
\frac{\partial J}{\partial u^{(i)}}
\]

This is the gradient of the final cost with respect to that node's output. For parameter nodes (leaves), this is exactly the gradient we need for optimization. For intermediate nodes, these gradients are stepping stones to reach the parameters.

### Quick Check 2

*Question:* In the graph for \(J = (a \cdot b) + c^2\), list the children of node \(a\).

*Answer:* Node \(a\) has one child: \(u_1\) (the multiplication node), because \(a\) is an input to the operation that computes \(u_1\).

**Summary:** A computational graph represents any neural network as a DAG of operations. This uniform representation allows back-propagation to be developed once on the graph and applied to all architectures. The goal is to compute \(\frac{\partial J}{\partial u^{(i)}}\) for every node, which gives the parameter gradients needed for optimization.

---

## 3. The Chain Rule Decomposition

### Intuition: "Messages Flowing Backward"

Imagine standing at the output \(J\) of the network, holding a small perturbation \(\Delta\). You want to know: if you inject this perturbation, how does it distribute backward through the network to each parameter?

At the root \(J\), the answer is trivial: a perturbation of \(\Delta\) at \(J\) changes \(J\) by exactly \(\Delta\). So the "message" — the gradient signal — starts as 1.

Now walk backward. At each node, ask: given that my output changing by \(\bar{g}\) causes \(J\) to change by \(\bar{g}\), how much does \(J\) change when each of my *inputs* changes? The answer depends on the node's local operation.

**A plumbing analogy:** Think of the network as a system of pipes. The forward pass sends water from inputs to outputs. The backward pass is like injecting dye at the output and watching it flow backward. At a T-junction (an add node), the dye splits equally into both incoming pipes. At a valve controlled by another pipe (a multiply node), the dye concentration gets amplified by the flow in the other pipe. The dye reaching each input tells you how much that input contributes to the output. This is exactly what gradients measure: the *sensitivity* of the output to each input.

Now, how does a node \(u^{(i)}\) compute its message? It looks at all nodes that *directly* used \(u^{(i)}\) — its **children**. Each child \(u^{(j)}\) already has its message \(\frac{\partial J}{\partial u^{(j)}}\). The child also knows its *local* sensitivity to \(u^{(i)}\): the partial derivative \(\frac{\partial u^{(j)}}{\partial u^{(i)}}\).

The total effect of \(u^{(i)}\) on \(J\) is the sum over all paths through its children:

\[
\text{message}(u^{(i)}) = \sum_{\text{children } j} \text{message}(u^{(j)}) \times (\text{local sensitivity of } u^{(j)} \text{ to } u^{(i)})
\]

This is exactly the multivariate chain rule.

**Why a sum?** Because \(u^{(i)}\) can influence \(J\) through multiple downstream paths. If \(u^{(i)}\) feeds into two different children that both eventually reach \(J\), a small change in \(u^{(i)}\) perturbs both paths simultaneously. The total effect is the sum of the individual path effects. This is the same principle as a river splitting into two tributaries: the total downstream flow is the sum of the flows in each branch.

**Try this yourself — Interactive gradient trace:** Implement a tiny computational graph in PyTorch for \(J = (a \cdot b) + c^2\) with `a=3, b=4, c=2`. Call `J.backward()` and inspect `a.grad`, `b.grad`, `c.grad`. Now modify the graph to \(J = (a \cdot b) + c^2 + a\) — note how `a` now has two paths to \(J\) (through the multiplication and directly). Print `a.grad` again. The gradient is now \(b + 1 = 5\) instead of just \(b = 4\). This live experiment makes the sum rule concrete: PyTorch automatically sums gradients from all paths, and you can verify it by hand in seconds. Try adding more paths and predicting the gradient before running `.backward()` — this turns the abstract sum rule into a game of gradient prediction.

**Practical example — Residual connections (ResNet):** In a residual block, the output is \(\mathbf{y} = \mathcal{F}(\mathbf{x}, \{\mathbf{W}_i\}) + \mathbf{x}\), where \(\mathcal{F}\) is the residual mapping (typically two or three convolutional layers with batch normalization and ReLU) and \(\mathbf{x}\) is the skip connection. The computational graph has \(\mathbf{x}\) feeding into both \(\mathcal{F}\) and the final addition. During back-propagation, the gradient with respect to \(\mathbf{x}\) receives contributions from two paths: \(\frac{\partial J}{\partial \mathbf{y}} \cdot \frac{\partial \mathcal{F}}{\partial \mathbf{x}}\) (through the residual branch) and \(\frac{\partial J}{\partial \mathbf{y}} \cdot 1\) (through the skip connection). The skip connection provides a direct gradient highway, mitigating vanishing gradients even when \(\frac{\partial \mathcal{F}}{\partial \mathbf{x}}\) becomes small. This is precisely why ResNets with hundreds of layers remain trainable: the additive gradient path ensures that \(\frac{\partial J}{\partial \mathbf{x}}\) never collapses to zero solely due to depth.

**Real-world scenario — Training a 152-layer ResNet on ImageNet:** When training ResNet-152, the deepest residual blocks are 152 layers away from the loss. Without skip connections, the gradient magnitude at early layers would be attenuated by the product of 152 Jacobian matrices, each with singular values typically less than 1, causing the gradient to vanish to near zero. In practice, the skip connection's gradient contribution of \(\frac{\partial J}{\partial \mathbf{y}} \cdot 1\) ensures that even if the residual branch gradient \(\frac{\partial J}{\partial \mathbf{y}} \cdot \frac{\partial \mathcal{F}}{\partial \mathbf{x}}\) is tiny, the total gradient \(\frac{\partial J}{\partial \mathbf{x}} = \frac{\partial J}{\partial \mathbf{y}} \cdot \left(1 + \frac{\partial \mathcal{F}}{\partial \mathbf{x}}\right)\) remains at least as large as the output gradient. This property enabled the first successful training of networks deeper than 100 layers, reducing the ImageNet top-5 error from 7.3% (VGG-19, 19 layers) to 3.57% (ResNet-152). The back-propagation sum rule is not just a mathematical formality — it is the direct reason residual connections work.

**Practical example — Multi-task learning:** Consider a shared feature extractor \(\mathbf{h} = f(\mathbf{x}; \boldsymbol{\theta}_{\text{shared}})\) feeding two task-specific heads: \(J_1 = g_1(\mathbf{h}; \boldsymbol{\phi}_1)\) and \(J_2 = g_2(\mathbf{h}; \boldsymbol{\phi}_2)\), with total loss \(J = J_1 + J_2\). The gradient with respect to the shared features \(\mathbf{h}\) is the sum: \(\frac{\partial J}{\partial \mathbf{h}} = \frac{\partial J_1}{\partial \mathbf{h}} + \frac{\partial J_2}{\partial \mathbf{h}}\). If task 1's gradient dominates, task 2's learning signal gets drowned out. This motivates gradient normalization techniques (e.g., GradNorm, PCGrad) that rescale or project conflicting gradients before summing. The back-propagation sum rule makes the interaction explicit and diagnosable.

**Real-world scenario — Autonomous driving perception:** A self-driving car's perception system must simultaneously detect lane markings (task 1: semantic segmentation), identify traffic signs (task 2: object detection), and estimate depth to obstacles (task 3: monocular depth estimation). These three tasks share a common backbone (e.g., ResNet-50 feature extractor) with three separate heads. During training,