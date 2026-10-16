**Learning Objectives**  
By the end of this lecture, you will be able to:  
1. Recall the forward and backward pass equations in a feedforward neural network.  
2. Understand how the chain rule propagates gradients through a computational graph.  
3. Apply the backpropagation algorithm to compute gradients in a multilayer perceptron.  
4. Analyze common issues such as vanishing gradients and numerical instability, and explain how architectural choices affect them.  
5. Construct a step-by-step backward pass for a given network by combining local derivatives and error signals.

---

### Prerequisites

Before proceeding, ensure familiarity with the following concepts:  
- **Partial derivatives and the chain rule**: For a composite function $ z = f(g(x)) $, the derivative is $ \frac{dz}{dx} = \frac{dz}{dg} \cdot \frac{dg}{dx} $.  
- **Vector calculus**: The gradient of a scalar loss $ J $ with respect to a vector $ w $ is denoted $ \nabla_w J $, and contains partial derivatives $ \frac{\partial J}{\partial w_i} $.  
- **Matrix operations**: Matrix multiplication and transposition, particularly how $ W^\top $ enables backward gradient routing.  
- **Element-wise operations**: The Hadamard (element-wise) product $ \odot $, used when applying activation function derivatives.

These tools form the foundation for deriving gradient flow in neural networks.

> **Formative Check (Prerequisites)**  
> Let $ a = \tanh(z) $, $ z = Wx + b $, and $ J = a^2 $. Compute $ \frac{\partial J}{\partial z} $ using the chain rule.  
> *(Answer: $ \frac{\partial J}{\partial z} = 2a \cdot (1 - \tanh^2(z)) = 2\tanh(z)(1 - \tanh^2(z)) $.)*

---

### Intuition: The Purpose of Backpropagation

Imagine you're debugging a complex circuit with hundreds of adjustable knobs—each slightly influencing the final output. You observe that the output is wrong, but you don’t know which knob to turn, or in which direction. Turning each one individually to test its effect would take forever.

Now imagine the circuit is a neural network with millions of parameters. The **loss** is your only measurement of error. You need to know: *How does each weight affect the loss?*  
A brute-force approach—nudging each weight and re-running the forward pass—is computationally catastrophic. For $ n $ weights, it requires $ n+1 $ forward passes. With a million weights, that’s a million extra evaluations—every single step.

But there’s a better way.  
Backpropagation is to gradients what the Fast Fourier Transform is to signal processing: an algorithm that turns an intractable problem into a routine one.  
> It computes *all* gradients in just *one* forward and *one* backward pass—thanks to the chain rule and smart reuse of intermediate values.

Here’s the paradox:  
**The gradient with respect to every parameter—no matter how deep—can be computed using only local operations and a reverse flow of error signals.**  
No global probing. No redundancy. Just disciplined bookkeeping.

This isn’t just efficient—it’s *necessary*. Without backpropagation, deep learning wouldn’t exist.

> **Try this yourself**: Suppose a network has 10 layers and 1 million parameters. Estimate how long it would take to compute gradients via finite differences if one forward pass takes 1 millisecond. Compare that to backpropagation.  
> *(Spoiler: Finite differences would take over 16 minutes per step. Backpropagation: ~2 milliseconds.)*

---

### Step 1: Forward Pass and the Computational Graph

Consider a two-layer feedforward network:  
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

The forward pass is like assembling a car:  
- Each layer adds a component.  
- The final product is the loss.

But unlike a car factory, we’ll later *disassemble* the product in reverse, not to recycle parts, but to assign *blame*—how much each part contributed to the final defect.

Each operation becomes a node in a **computational graph**, a directed acyclic graph where edges represent data flow and nodes represent functions.

Crucially: we **cache** intermediate values ($ z^{(1)}, a^{(1)}, z^{(2)} $) during the forward pass.  
Why? Because derivatives depend on them. For example, $ \frac{d}{dz}\tanh(z) = 1 - \tanh^2(z) $—you can’t compute this without $ z $.

This is the **memory-speed tradeoff** of backpropagation: store intermediates to avoid recomputation.

> **Formative Check (Forward Pass)**  
> Given $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $, $ W^{(1)} = \begin{bmatrix}1 & 1 \\ -1 & 1\end{bmatrix} $, $ b^{(1)} = \begin{bmatrix}0 \\ 0\end{bmatrix} $, compute $ z^{(1)} $ and $ a^{(1)} $.  
> *(Answer: $ z^{(1)} = \begin{bmatrix}1 \\ -1\end{bmatrix} $, $ a^{(1)} = \begin{bmatrix}\tanh(1) \\ \tanh(-1)\end{bmatrix} \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix} $.)*

---

### Step 2: Backward Pass — Gradient Computation via the Chain Rule

Now comes the disassembly.  
We start at the loss and ask: *How did we get here?*  
Each step backward answers: *Who contributed to this error, and how much?*

We define the **error signal** at layer $ l $:  
$$
\delta^{(l)} = \frac{\partial J}{\partial z^{(l)}}
$$  
This is the sensitivity of the loss to the pre-activation $ z^{(l)} $. It answers: *If I tweak the input to layer $ l $’s activation, how does the loss change?*

We compute $ \delta^{(l)} $ recursively, from output to input—like tracing a spill back to its source.

#### Output Layer ($ l = 2 $)

We begin with:  
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
> Think of it as a *responsibility assignment*: each weight $ W^{(2)}_{ij} $ connects neuron $ j $ in layer 1 to neuron $ i $ in layer 2. The gradient $ \frac{\partial J}{\partial W^{(2)}_{ij}} = \delta^{(2)}_i \cdot a^{(1)}_j $—so the full matrix gradient is the outer product.  
> This is the **credit assignment** in action: blame is shared between the incoming activation and the error it helped produce.

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

> **Final Prompt**: Design a 3-layer network where the second layer uses sigmoid, and initialize weights large. Predict what happens during backpropagation. Then simulate it.  
> What do you observe? How would you fix it?

Backpropagation reveals not just gradients—but the hidden physics of learning.