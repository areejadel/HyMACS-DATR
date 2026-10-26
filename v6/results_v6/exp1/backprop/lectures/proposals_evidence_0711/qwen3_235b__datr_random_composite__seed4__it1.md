### Learning Objectives
By the end of this lecture, you will be able to:
1. **Remember**: Identify the components of a computational graph and the role of cached values in backpropagation.
2. **Understand**: Explain how the chain rule applies to neural network gradients and why backpropagation proceeds backward.
3. **Apply**: Compute gradients step-by-step in a two-layer network using forward and backward passes.
4. **Analyze**: Diagnose vanishing gradients by inspecting activation derivatives and weight configurations.
5. **Create**: Propose architectural modifications (e.g., skip connections) to improve gradient flow in deep networks.

---

### Prerequisites
Before we begin, ensure you can:
- Compute derivatives of scalar functions using the chain rule.
- Perform matrix-vector multiplication and understand dimensions (e.g., $ Wx $, $ W^\top \delta $).
- Evaluate $ \tanh(z) $ and its derivative $ 1 - \tanh^2(z) $.

> **Quick Check (Prerequisites)**  
> Compute $ \frac{d}{dx} \tanh(2x) $ at $ x = 0 $.  
> *(Answer: $ 2(1 - \tanh^2(0)) = 2(1 - 0) = 2 $.)*

---

### Intuition First: A Concrete Example
Let’s start with a simple prediction task: estimating house prices.  
Suppose your model predicts $ \hat{y} = 250 $K, but the true price is $ y = 300 $K. The loss is high.  
Now ask: *Which weights are to blame?*  
- The output layer weights directly influenced the bad prediction.  
- But they only got bad input from the hidden layer.  
- So maybe the hidden weights are at fault? Or the activation function saturated?

Backpropagation answers this by tracing the error *backward*, assigning blame layer by layer—like a detective reconstructing a path from crime scene to suspect.

This process relies on the **chain rule**, applied efficiently through the network’s computational graph.

---

### Step 1: Forward Pass and the Computational Graph

We begin with a two-layer feedforward network:  
- Input: $ x \in \mathbb{R}^2 $  
- Hidden layer:  
  $$
  z^{(1)} = W^{(1)}x + b^{(1)}, \quad a^{(1)} = \tanh(z^{(1)})
  $$  
- Output layer:  
  $$
  z^{(2)} = W^{(2)}a^{(1)} + b^{(2)}, \quad \hat{y} = z^{(2)} \quad \text{(linear output)}
  $$  
- Loss:  
  $$
  J = \frac{1}{2}(y - \hat{y})^2
  $$

During the forward pass, each operation becomes a node in a **computational graph**—a directed acyclic graph where:
- Nodes represent functions (e.g., matrix multiply, tanh, loss).
- Edges represent data flow (e.g., $ x \to z^{(1)} \to a^{(1)} \to \cdots \to J $).

Crucially, we **cache** intermediate values ($ z^{(1)}, a^{(1)}, z^{(2)} $) during the forward pass.  
Why? Because derivatives depend on them. For example, $ \frac{d}{dz}\tanh(z) = 1 - \tanh^2(z) $—you can’t compute this without $ z $.

This is the **memory-speed tradeoff** of backpropagation: store intermediates to avoid recomputation.

> **Formative Check (Forward Pass)**  
> Given $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $, $ W^{(1)} = \begin{bmatrix}1 & 1 \\ -1 & 1\end{bmatrix} $, $ b^{(1)} = \begin{bmatrix}0 \\ 0\end{bmatrix} $, compute $ z^{(1)} $ and $ a^{(1)} $.  
> *(Answer: $ z^{(1)} = \begin{bmatrix}1 \\ -1\end{bmatrix} $, $ a^{(1)} = \begin{bmatrix}\tanh(1) \\ \tanh(-1)\end{bmatrix} \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix} $.)*

> **Misconception Alert**  
> *“We only need the final output to compute gradients.”*  
> False! Without caching $ z^{(1)} $, we cannot compute $ \tanh'(z^{(1)}) $, so we cannot propagate error backward. Memory matters.

---

### Step 2: Backward Pass — Gradient Computation via the Chain Rule

Now we disassemble the forward pass, starting at the loss and moving backward.  
Each step answers: *How did this value contribute to the final error?*

We define the **error signal** at layer $ l $:  
$$
\delta^{(l)} = \frac{\partial J}{\partial z^{(l)}}
$$  
This measures how sensitive the loss is to changes in the pre-activation $ z^{(l)} $. It tells us: *If I tweak $ z^{(l)} $, how much does $ J $ change?*

We compute $ \delta^{(l)} $ recursively, from output to input—like tracing a spill back to its source.

#### Output Layer ($ l = 2 $)

Start here:  
$$
\delta^{(2)} = \frac{\partial J}{\partial z^{(2)}}
$$  
Since $ \hat{y} = z^{(2)} $ and $ J = \frac{1}{2}(y - \hat{y})^2 $,  
$$
\frac{\partial J}{\partial z^{(2)}} = \frac{\partial J}{\partial \hat{y}} \cdot \frac{\partial \hat{y}}{\partial z^{(2)}} = (-(y - \hat{y})) \cdot 1 = \hat{y} - y
$$  
Thus,  
$$
\delta^{(2)} = \hat{y} - y
$$

Now compute gradients for output parameters:  
$$
\frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} (a^{(1)})^\top, \quad \frac{\partial J}{\partial b^{(2)}} = \delta^{(2)}
$$

> **Why $ (a^{(1)})^\top $?**  
> Think of it as *responsibility assignment*: each weight $ W^{(2)}_{ij} $ connects neuron $ j $ in layer 1 to neuron $ i $ in layer 2. The gradient $ \frac{\partial J}{\partial W^{(2)}_{ij}} = \delta^{(2)}_i \cdot a^{(1)}_j $—so the full matrix gradient is the outer product.  
> This is **credit assignment** in action: blame is shared between the incoming activation and the error it helped produce.

> **Quick Check (Output Layer)**  
> If $ \delta^{(2)} = 0.3 $ and $ a^{(1)} = \begin{bmatrix}0.5 \\ -0.2\end{bmatrix} $, compute $ \frac{\partial J}{\partial W^{(2)}} $.  
> *(Answer: $ 0.3 \cdot \begin{bmatrix}0.5 & -0.2\end{bmatrix} = \begin{bmatrix}0.15 & -0.06\end{bmatrix} $.)*

---

#### Hidden Layer ($ l = 1 $)

Now the key challenge: propagate error *through* the activation function and *back through* the linear layer.

We want $ \delta^{(1)} = \frac{\partial J}{\partial z^{(1)}} $.  
But $ z^{(1)} $ doesn’t directly affect $ J $. It affects $ a^{(1)} $, which affects $ z^{(2)} $, which affects $ J $.

So we chain:  
$$
\frac{\partial J}{\partial z^{(1)}} = \frac{\partial J}{\partial a^{(1)}} \cdot \frac{\partial a^{(1)}}{\partial z^{(1)}}
$$

First, $ \frac{\partial a^{(1)}}{\partial z^{(1)}} $ is diagonal: $ \text{diag}(1 - \tanh^2(z^{(1)})) $.  
Second, $ \frac{\partial J}{\partial a^{(1)}} = (W^{(2)})^\top \delta^{(2)} $—because $ z^{(2)} = W^{(2)}a^{(1)} + b^{(2)} $, so each component of $ a^{(1)} $ influences $ J $ through all outputs via the weights.

Putting it together:  
$$
\delta^{(1)} = \left( (W^{(2)})^\top \delta^{(2)} \right) \odot f^{(1)'}(z^{(1)})
$$

This equation is the **heartbeat of backpropagation**.  
Let’s dissect it with an analogy:

> **Backpropagation is like a plumbing system under pressure**:  
> - The loss creates pressure (error signal).  
> - The weights are pipes connecting tanks (neurons).  
> - The activation function is a valve with resistance $ f'(z) $.  
> - When you open the drain (compute loss), pressure flows backward.  
> - The amount reaching each pre-activation $ z^{(l)} $ depends on the pipe size (weight) and how open the valve is (derivative).  
> - If the valve is nearly closed ($ f'(z) \approx 0 $), pressure doesn’t propagate—this is the *vanishing gradient* problem.

This explains why sigmoid/tanh networks struggle to train: in saturated regions, $ f'(z) \approx 0 $, so error signals vanish as they propagate backward.

> **Try this yourself**: Suppose $ z^{(1)} = 5 $. What is $ \tanh'(z^{(1)}) $? What if $ z^{(1)} = 0 $? How does this affect gradient flow?  
> *(Answer: $ \tanh'(5) \approx 0.004 $ — nearly zero; $ \tanh'(0) = 1 $. So neurons with large pre-activations block error flow.)*

Then compute:  
$$
\frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top, \quad \frac{\partial J}{\partial b^{(1)}} = \delta^{(1)}
$$

> **Clarification**: The transpose $ W^{(2)\top} $ ensures dimensional compatibility and reflects how each neuron in layer 1 influences all neurons in layer 2 through the weights.

> **Formative Check (Backward Pass)**  
> Given $ \delta^{(2)} = 0.5 $, $ W^{(2)} = \begin{bmatrix}2 & -1\end{bmatrix} $, $ z^{(1)} = \begin{bmatrix}0 \\ 1\end{bmatrix} $, compute $ \delta^{(1)} $.  
> *(Answer: $ (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix}1.0 \\ -0.5\end{bmatrix} $, $ f^{(1)'}(z^{(1)}) = \begin{bmatrix}1 \\ 1 - \tanh^2(1)\end{bmatrix} \approx \begin{bmatrix}1 \\ 0.42\end{bmatrix} $, so $ \delta^{(1)} \approx \begin{bmatrix}1.0 \\ -0.21\end{bmatrix} $.)*

> **Misconception Alert**  
> *“Gradients flow equally through all layers.”*  
> False! Gradients depend on $ f'(z) $ and weight magnitudes. In deep networks, repeated multiplication by small values causes vanishing gradients—especially with sigmoid/tanh.

---

### Worked Example: Complete Forward and Backward Pass

We now execute a full forward and backward pass.

**Given:**  
- $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $, $ y = 1 $  
- $ W^{(1)} = \begin{bmatrix}1 & 1 \\ -1 & 1\end{bmatrix} $, $ b^{(1)} = \begin{bmatrix}0 \\ 0\end{bmatrix} $  
- $ W^{(2)} = \begin{bmatrix}2 & -1\end{bmatrix} $, $ b^{(2)} = 0 $  
- $ f^{(1)} = \tanh $, $ f^{(2)} = \text{linear} $, $ J = \frac{1}{2}(y - \hat{y})^2 $

#### Forward Pass

1. $ z^{(1)} = W^{(1)}x = \begin{bmatrix}1\cdot1 + 1\cdot0 \\ -1\cdot1 + 1\cdot0\end{bmatrix} = \begin{bmatrix}1 \\ -1\end{bmatrix} $  
2. $ a^{(1)} = \tanh(z^{(1)}) = \begin{bmatrix}\tanh(1) \\ \tanh(-1)\end{bmatrix} \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix} $  
3. $ z^{(2)} = W^{(2)}a^{(1)} + b^{(2)} = 2(0.762) + (-1)(-0.762) = 1.524 + 0.762 = 2.286 $  
4. $ \hat{y} = z^{(2)} = 2.286 $  
5. $ J = \frac{1}{2}(1 - 2.286)^2 = \frac{1}{2}(1.651)^2 \approx 0.825 $

#### Backward Pass

1. $ \delta^{(2)} = \hat{y} - y = 2.286 - 1 = 1.286 $  
2. $ \frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} (a^{(1)})^\top = 1.286 \cdot \begin{bmatrix}0.762 & -0.762\end{bmatrix} \approx \begin{bmatrix}0.980 & -0.980\end{bmatrix} $  
3. $ \frac{\partial J}{\partial b^{(2)}} = \delta^{(2)} = 1.286 $  
4. $ (W^{(2)})^\top \delta^{(2)} = \begin{bmatrix}2 \\ -1\end{bmatrix} \cdot 1.286 = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix} $  
5. $ f^{(1)'}(z^{(1)}) = 1 - \tanh^2(z^{(1)}) = \begin{bmatrix}1 - \tanh^2(1) \\ 1 - \tanh^2(-1)\end{bmatrix} \approx \begin{bmatrix}0.420 \\ 0.420\end{bmatrix} $  
6. $ \delta^{(1)} = \begin{bmatrix}2.572 \\ -1.286\end{bmatrix} \odot \begin{bmatrix}0.420 \\ 0.420\end{bmatrix} \approx \begin{bmatrix}1.080 \\ -0.540\end{bmatrix} $  
7. $ \frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = \begin{bmatrix}1.080 \\ -0.540\end{bmatrix} \begin{bmatrix}1 & 0\end{bmatrix} = \begin{bmatrix}1.080 & 0 \\ -0.540 & 0\end{bmatrix} $  
8. $ \frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} \approx \begin{bmatrix}1.080 \\ -0.540\end{bmatrix} $

This completes the backward pass. Every gradient is now available for optimization.

> **Insight**: Notice that $ \frac{\partial J}{\partial W^{(1)}} $ only updates the first column of $ W^{(1)} $, because $ x_2 = 0 $. Inputs that are zero don’t contribute to gradients—another form of *selective credit assignment*.

> **Interactive Check**  
> Use the above network. Change $ x_2 $ from 0 to 1. Recompute $ \frac{\partial J}{\partial W^{(1)}} $. What changes? Why?  
> *(Answer: Now both columns of $ W^{(1)} $ receive gradient, since both inputs are active.)*

---

### Beyond the Mechanics: Architectural Implications

Backpropagation isn’t just an algorithm—it shapes design.

Consider **residual connections** in ResNet:  
$$
a^{(l+1)} = a^{(l)} + F(a^{(l)})
$$  
In backprop, the error signal splits: one path through $ F $, one direct path backward.  
This is like adding a *wire* that bypasses a potentially leaky valve—ensuring that even if $ F $’s gradient vanishes, some signal gets through.

Similarly, **batch normalization** reduces internal covariate shift, but it also *stabilizes gradients* by keeping $ z^{(l)} $ in the sensitive region of $ f' $, where gradients don’t vanish.

And **ReLU**? It’s not just computationally cheap. Its derivative is 1 for $ z > 0 $—like a wide-open valve. No saturation, no vanishing—until you hit dying ReLUs.

> **Cross-domain connection: Electrical circuits**  
> Backpropagation through a residual block is like a parallel circuit: error flows through both the nonlinear transformation $ F $ and the skip connection. The skip connection acts as a *short circuit*—a zero-resistance path—ensuring that gradient magnitude doesn’t decay with depth.  
> This is not metaphorical: in fact, the gradient through a residual block is provably bounded below by 1 in norm, just as current prefers the path of least resistance.

> **Cross-domain connection: Evolutionary biology**  
> Backpropagation mirrors natural selection in a surprising way. In evolution, mutations are "tested" by survival and reproduction—the fitness signal propagates backward in time, shaping which genes persist. Similarly, in backprop, the loss is the fitness metric; gradients are the mechanism that "selects" which weights should change, and by how much.  
> Just as evolution doesn't try every possible mutation (which would be combinatorially impossible), backprop avoids brute-force search by computing *directional sensitivity*—a local approximation of what works.  
> This is *not* analogy for decoration: both are **gradient-free in forward pass, gradient-based in update**, and both rely on a delayed global signal to shape incremental change.

> **Final Prompt**  
> Design a 3-layer network where the second layer uses sigmoid, and initialize weights large. Predict what happens during backpropagation. Then simulate it.  
> What do you observe? How would you fix it?  
> *(Expected: Gradients vanish in early layers due to $ f'(z) \approx 0 $ in saturation. Fix: Use smaller weights, batch norm, or ReLU.)*

Backpropagation reveals not just gradients—but the hidden physics of learning.