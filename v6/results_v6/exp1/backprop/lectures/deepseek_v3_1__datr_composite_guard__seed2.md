## 4. Local Gradients: The Building Blocks

### The Key Abstraction

**The Hook: Why Should You Care?**

Here’s a puzzle: a single wrong connection in a neural network with 175 billion parameters (like GPT-3) causes a wrong prediction. How do you find which parameter to fix, and by how much, without testing all 175 billion one by one? The answer — backpropagation — lets you assign exact blame to every parameter using a single backward sweep. The magic that makes this possible is the *local gradient*.

Imagine you’re debugging a massive, tangled circuit — millions of wires, thousands of components. You find that the final output voltage is wrong. Do you need to understand the entire circuit to trace the error back to a single faulty resistor? No. You only need to know two things about that resistor: how it transforms its input voltage to its output voltage, and how a small change in its input would affect its output. You can then work backward, component by component, isolating the fault without ever grasping the whole.

This is precisely the promise of back-propagation. Every node in the computational graph is a function. To implement back-propagation for any architecture, we only need to know two things about each node type:

1.  **Forward:** Given inputs, compute the output.
2.  **Backward:** Given the gradient of the loss with respect to the *output* (\(\frac{\partial J}{\partial \text{out}}\)), compute the gradient with respect to each *input*.

The backward computation uses only the node's local derivative and the incoming gradient from above. It does not need to know anything about the rest of the graph. This modularity is what makes automatic differentiation frameworks (PyTorch, TensorFlow, JAX) possible: each operation defines its own `forward` and `backward` methods, and the framework composes them.

### Common Local Gradients

Here are the backward rules for operations you will encounter constantly. Commit these to memory — they are the atomic instructions of back-propagation.

| Operation | Forward | Backward (given \(\bar{g} = \frac{\partial J}{\partial \text{out}}\)) |
|----------|---------|----------------------------------------------------------------------|
| **Add:** \(z = x + y\) | \(z = x + y\) | \(\frac{\partial J}{\partial x} = \bar{g}\), \(\frac{\partial J}{\partial y} = \bar{g}\) |
| **Multiply:** \(z = x \cdot y\) | \(z = x \cdot y\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot y\), \(\frac{\partial J}{\partial y} = \bar{g} \cdot x\) |
| **Square:** \(z = x^2\) | \(z = x^2\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot 2x\) |
| **Exponential:** \(z = e^x\) | \(z = e^x\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot e^x = \bar{g} \cdot z\) |
| **Log:** \(z = \ln x\) | \(z = \ln x\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot \frac{1}{x}\) |
| **ReLU:** \(z = \max(0, x)\) | \(z = \max(0, x)\) | \(\frac{\partial J}{\partial x} = \begin{cases} \bar{g} & \text{if } x > 0 \\ 0 & \text{otherwise} \end{cases}\) |
| **Sigmoid:** \(z = \sigma(x)\) | \(z = \frac{1}{1+e^{-x}}\) | \(\frac{\partial J}{\partial x} = \bar{g} \cdot z(1-z)\) |

**Why the ReLU gradient is 0 when \(x \leq 0\):** A neuron that didn't fire contributed nothing to the output, so small changes to its input don't change the output at all. The gradient signal stops dead at that node. This is the "dying ReLU" phenomenon — and also the reason ReLU is cheap to compute gradients for.

### The Add and Multiply Rules: A Deeper Look

The add rule is a *gradient distributor*: it passes the incoming gradient unchanged to both inputs. If \(J\) changes by \(\bar{g}\) when \(z\) changes, and \(z = x + y\), then changing \(x\) alone by \(\epsilon\) changes \(z\) by \(\epsilon\), which changes \(J\) by \(\bar{g} \cdot \epsilon\). Same for \(y\). Think of it like a river splitting into two identical streams — the total water flow (the gradient) simply copies itself.

The multiply rule is a *gradient switcher*: the gradient with respect to \(x\) is \(\bar{g} \cdot y\). This is the value of the *other* input. Why? Because \(z = x \cdot y\), so \(\frac{\partial z}{\partial x} = y\). The incoming gradient \(\bar{g}\) gets scaled by \(y\). This means if \(y\) is large, \(x\) gets a proportionally larger gradient — a small change in \(x\) is amplified by \(y\).

**A physical analogy:** Think of \(z = x \cdot y\) as the area of a rectangle with sides \(x\) and \(y\). If you increase \(x\) by \(\Delta x\), the area increases by \(y \cdot \Delta x\). The longer side \(y\) is, the more a small change in \(x\) affects the area. The multiply rule captures exactly this: the gradient on one factor is proportional to the other factor.

**Try this yourself:** Consider a network that predicts house prices from square footage (\(x\)) and a location multiplier (\(y\)), with a loss function \(J\). If during training the location multiplier \(y = 0.8\) for suburban homes and \(y = 2.5\) for city-center homes, which type of home will produce larger gradient updates to the square-footage parameter? What does this imply about how the network learns from different data points?

**An unexpected cross-domain connection:** The multiply rule's gradient-switching behavior is identical to how leverage works in finance. If you invest with 5x leverage, a 1% move in the underlying asset produces a 5% move in your portfolio. Here, the "leverage ratio" is the other input \(y\). A large \(y\) amplifies the gradient on \(x\), just as high leverage amplifies returns (and losses). This isn't just an analogy — the mathematics is exactly the same: \(\frac{\partial}{\partial x}(x \cdot y) = y\). Understanding this connection gives you intuition for why careful weight initialization matters: if one layer's outputs are huge, the previous layer's gradients get amplified, potentially causing the exploding gradient problem. You're essentially trading with unbounded leverage.

### Industry Application: Gradient Flow in Transformer Attention

The local gradient rules find their most prominent industrial application in the self-attention mechanism of Transformer architectures, which underpin models like GPT-4, Claude, and Gemini. The core operation is the scaled dot-product attention:

\[
\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^T}{\sqrt{d_k}}\right)\mathbf{V}
\]

Here, the query \(\mathbf{Q}\) and key \(\mathbf{K}\) matrices are multiplied to produce an attention score matrix \(\mathbf{S} = \mathbf{Q}\mathbf{K}^T\). This is a matrix multiplication — a batched version of the multiply rule. During back-propagation, the gradient with respect to \(\mathbf{Q}\) is \(\bar{\mathbf{S}} \cdot \mathbf{K}\), and the gradient with respect to \(\mathbf{K}\) is \(\bar{\mathbf{S}}^T \cdot \mathbf{Q}\). The scaling factor \(1/\sqrt{d_k}\) is a multiply operation whose backward pass scales the incoming gradient by the same factor.

The softmax function is a composition of exponentiation, summation, and division. Its local gradient is the Jacobian matrix \(\text{diag}(\mathbf{p}) - \mathbf{p}\mathbf{p}^T\) where \(\mathbf{p}\) is the softmax output, which is computed and cached efficiently in frameworks like PyTorch's `torch.nn.functional.softmax`. In production training runs on thousands of GPUs, the memory footprint of storing these cached attention scores for the backward pass is a primary bottleneck. This has motivated research into memory-efficient attention (e.g., FlashAttention, which recomputes the softmax in the backward pass rather than storing the full attention matrix, trading computation for memory).

The practical consequences of these gradient flows are immense and span multiple industries. In **natural language processing**, OpenAI's GPT-4 and Google's Gemini models are trained on text corpora containing trillions of tokens. During training, the attention mechanism must compute gradients for sequences that can be hundreds of thousands of tokens long (e.g., processing entire legal documents or code repositories). The \(O(n^2)\) memory cost of storing the full attention matrix for back-propagation, where \(n\) is the sequence length, means that a single 100k-token sequence would require approximately 80 GB of memory just for the attention scores (assuming float32, \(100,000^2 \times 4\) bytes \(\approx\) 40 GB per attention head, with multi-head attention multiplying this). FlashAttention and its successors (FlashAttention-2, FlashAttention-3) reduce this memory footprint to \(O(n)\) by fusing the softmax computation with the matrix multiplication and recomputing attention scores block-by-block during the backward pass. This algorithmic innovation, driven directly by understanding the local gradient rules of softmax and matrix multiply, is what makes training on long sequences economically feasible. Without it, training GPT-4 on its full context window of 128k tokens would be prohibitively expensive, requiring hundreds of GPUs just to hold the attention matrices in memory.

**Try this yourself:** Before reading the next paragraph, estimate: if you have a sequence of 50,000 tokens and 12 attention heads, each computing attention in float32 (4 bytes per number), what is the raw memory required just to store the attention matrices for the backward pass? Now calculate what FlashAttention reduces this to if it uses \(O(n)\) memory with a block size of 128. The difference explains why FlashAttention is not just an optimization — it's an enabling technology.

In **computational biology and drug discovery**, the same back-propagation principles power AlphaFold2 (DeepMind) and RoseTTAFold (University of Washington), which predict protein 3D structures from amino acid sequences. These models use a variant of the Transformer architecture where the attention mechanism operates over pairs of amino acid residues. The gradient flow through the softmax determines how strongly each residue's predicted position is influenced by every other residue. During training on the Protein Data Bank (over 200,000 experimentally determined structures), the backward pass computes how a prediction error at one residue should propagate back to update the representations of all other residues. The local gradient of the softmax — specifically, the off-diagonal terms of the Jacobian \(\text{diag}(\mathbf{p}) - \mathbf{p}\mathbf{p}^T\) — encodes the competitive interactions between attention weights: increasing the attention from residue \(i\) to residue \(j\) necessarily decreases attention to other residues. This gradient signal is what teaches the network to identify physically meaningful contacts (e.g., residues that are close in 3D space despite being far apart in the sequence). The practical impact is transformative: AlphaFold2 can predict protein structures with atomic accuracy in hours, a task that previously required months or years of experimental work using X-ray crystallography or cryo-electron microscopy at costs exceeding $100,000 per structure. Pharmaceutical companies including Novartis and Pfizer now routinely use these models to screen drug candidates against predicted protein structures, accelerating the drug discovery pipeline from target identification to lead optimization.

In **autonomous driving and robotics**, the multiply rule's gradient-switching behavior has direct safety implications. Consider a perception system processing LiDAR point clouds through a PointNet-style architecture. The network applies shared multi-layer perceptrons to each 3D point, using matrix multiplications where the weights are the model parameters and the inputs are point features. During back-propagation, the gradient with respect to the weights is \(\bar{\text{out}} \cdot \mathbf{x}^T\) (the batched multiply rule). If a LiDAR sensor returns a spurious point with an anomalously large coordinate value (e.g., \(x = 10^4\) meters due to a sensor glitch), that point will produce an enormous gradient update to the weight matrix, potentially corrupting the model in a single training step. This is why companies like Waymo and Cruise implement gradient clipping (typically \(|\mathbf{g}| \leq 1.0\) or similar) and outlier detection in their training pipelines — practical safeguards derived directly from understanding the multiply rule's sensitivity to input magnitudes. Furthermore, during online inference, the backward pass is not run, but the same architectures are increasingly being deployed with online adaptation (e.g., Test-Time Training), where a single gradient step is taken on a self-supervised loss to adapt to the current driving conditions. In these scenarios, the numerical stability of the backward pass — ensuring that the gradient of the ReLU does not zero out critical pathways, that the softmax does not saturate — is a matter of functional safety, not just training efficiency.

In **finance and algorithmic trading**, recurrent neural networks and their attention-based successors (e.g., Temporal Fusion Transformers) are used for time-series forecasting of asset prices, volatility surfaces, and macroeconomic indicators. The backward pass through these architectures computes how a forecast error at time \(t\) should influence the model's interpretation of market data at earlier times. The vanishing gradient problem (discussed in Section 5) is not merely an academic curiosity: in a trading system managing billions of dollars, a vanishing gradient means the model cannot learn long-range dependencies, such as the effect of an interest rate change six months ago on today's volatility. Conversely, an exploding gradient can cause a single volatile trading day to overwrite months of learned patterns. Quantitative hedge funds like Renaissance Technologies and Two Sigma invest heavily in custom recurrent architectures (e.g., LSTMs with gradient clipping, dilated convolutions for multi-scale temporal processing) precisely to control these gradient flow dynamics. The practical consequence is that a model with well-behaved gradients can capture multi-year economic cycles, while one with vanishing gradients is effectively blind to anything beyond a few weeks — a difference that translates directly to trading performance.

### Quick Check 4

*Question:* In the expression \(J = (a \cdot b) + c^2\), why is \(\frac{\partial J}{\partial a} = b\) and not something involving \(c\)?

*Answer:* Because \(a\) only affects \(J\) through the multiplication \(u_1 = a \cdot b\). The addition with \(u_2 = c^2\) is a separate path. The local derivative \(\frac{\partial u_1}{\partial a} = b\). The gradient from \(u_3\) flows through \(u_1\) but \(u_1\)'s local derivative with respect to \(a\) is \(b\), independent of \(c\). The paths are independent; the chain rule multiplies along each path, and the add node sums them — but here \(a\) only has one path.

---

## 5. The Back-Propagation Algorithm

### Pseudocode

**Algorithm: Back-Propagation**

**Input:** Computational graph with nodes \(u^{(1)}, \dots, u^{(n)}\) in topological order, root \(u^{(n)} = J\). All node values computed in forward pass and stored.

**Output:** \(\frac{\partial J}{\partial u^{(i)}}\) for all nodes.

```
# Initialize gradient table
grad[u^{(n)}] = 1  # base case

# Traverse in reverse topological order
for i = n-1 down to 1:
    grad[u^{(i)}] = 0
    for each child j of u^{(i)}:
        # grad[u^{(j)}] already computed (j > i in topological order)
        # local_grad(u^{(j)}, u^{(i)}) = ∂u^{(j)} / ∂u^{(i)}
        grad[u^{(i)}] += grad[u^{(j)}] * local_grad(u^{(j)}, u^{(i)})

return grad
```

**Key invariant:** After processing node \(u^{(i)}\), \(\text{grad}[u^{(i)}]\) contains the exact \(\frac{\partial J}{\partial u^{(i)}}\). The base case ensures the root is correct; the loop ensures each node aggregates over all its children. By induction in reverse topological order, all gradients are correct.

**Why reverse topological order?** Here's the intellectual tension: you might wonder why we can't just compute gradients in any order. The answer reveals the algorithm's core constraint. Each node's gradient depends on the gradients of all nodes that come after it in the computation (its children). If we process a node before its children, we'd be using uninitialized gradient values — effectively guessing. The reverse topological order guarantees that when we reach node \(u^{(i)}\), every node that depends on it has already been processed, so \(\text{grad}[u^{(j)}]\) is already exact. This is the same principle as dynamic programming: solve subproblems in an order that ensures dependencies are resolved before they're needed. The forward pass computes values from inputs to output; the backward pass computes gradients from output to inputs. The symmetry is elegant and exact.

### Worked Example: Back-Propagation in a Convolutional Neural Network (CNN)

To illustrate back-propagation in a fundamentally different architecture, consider a simple 1D convolutional layer. This example demonstrates how the same back-propagation principles apply, but the local gradient computations differ from fully-connected layers.

**Architecture:** A 1D convolutional layer with input \(\mathbf{x} \in \mathbb{R}^4\), a single filter \(\mathbf{w} \in \mathbb{R}^3\), stride 1, and no padding. The output \(\mathbf{z} \in \mathbb{R}^2\) is computed as:

\[
z_1 = w_1 x_1 + w_2 x_2 + w_3 x_3
\]
\[
z_2 = w_1 x_2 + w_2 x_3 + w_3 x_4
\]

A scalar loss \(J\) is computed from \(\mathbf{z}\) (e.g., via a sum: \(J = z_1 + z_2\)).

**Concrete values:** \(\mathbf{x} = [2, 1, 3, 0]\), \(\mathbf{w} = [1, -1, 2]\).

**Forward pass:**
- \(z_1 = 1 \cdot 2 + (-1) \cdot 1 + 2 \cdot 3 = 2 - 1 + 6 = 7\)
- \(z_2 = 1 \cdot 1 + (-1) \cdot 3 + 2 \cdot 0 = 1 - 3 + 0 = -2\)
- \(J = z_1 + z_2 = 5\)

**Backward pass:** Assume \(\frac{\partial J}{\partial J} = 1\). Since \(J = z_1 + z_2\), the add gate distributes the gradient: \(\frac{\partial J}{\partial z_1} = 1\), \(\frac{\partial J}{\partial z_2} = 1\).

Now, compute gradients for the filter weights. Each weight \(w_k\) appears in both \(z_1\) and \(z_2\), so its gradient is the sum of contributions through each path (by the multivariate chain rule, Equation (1)):

\[
\frac{\partial J}{\partial w_1} = \frac{\partial J}{\partial z_1} \cdot \frac{\partial z_1}{\partial w_1} + \frac{\partial J}{\partial z_2} \cdot \frac{\partial z_2}{\partial w_1} = 1 \cdot x_1 + 1 \cdot x_2 = 2 + 1 = 3
\]
\[
\frac{\partial J}{\partial w_2} = \frac{\partial J}{\partial z_1} \cdot \frac{\partial z_1}{\partial w_2} + \frac{\partial J}{\partial z_2} \cdot \frac{\partial z_2}{\partial w_2} = 1 \cdot x_2 + 1 \cdot x_3 = 1 + 3 = 4
\]
\[
\frac{\partial J}{\partial w_3} = \frac{\partial J}{\partial z_1} \cdot \frac{\partial z_1}{\partial w_3} + \frac{\partial J}{\partial z_2} \cdot \frac{\partial z_2}{\partial w_3} = 1 \cdot x_3 + 1 \cdot x_4 = 3 + 0 = 3
\]

For the input \(\mathbf