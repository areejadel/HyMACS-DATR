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

You’re standing in front of a massive, dark control panel with 10,000 switches. A single red light glows—your only signal. You’re told: *One combination of switches turns it off. Adjust them until it goes dark.*  
You flip one switch. Nothing. You run forward to check the light. Then another. Another forward pass. Another check.

With 10,000 switches, this brute-force search would take 10,000 steps—*per adjustment*. Now scale it: what if there are 100 million switches?  
This is the nightmare of training deep networks without backpropagation.

But here’s the insight:  
**You don’t need to test each switch individually.**  
If you could ask, *“How would flipping each switch affect the light?”*—all at once—you could move directly toward the solution.

That’s exactly what gradients give you: a vector of sensitivities.  
And backpropagation is the algorithm that computes this vector efficiently—not in 100 million forward passes, but in just **one forward and one backward sweep**.

Think of it like solving a crime not by interrogating every citizen, but by following a trail of evidence backward from the scene.  
Each clue leads to the next—until you find the culprit.

This efficiency isn’t just convenient.  
In 1986, when backpropagation was popularized, training even a modest network was on the edge of feasibility. Without this algorithm, deep learning would have remained a theoretical curiosity.

> **Try this yourself**: Suppose a network has 10 layers and 1 million parameters. Estimate how long it would take to compute gradients via finite differences if one forward pass takes 1 millisecond. Compare that to backpropagation.  
> *(Spoiler: Finite differences would take over 16 minutes per step. Backpropagation: ~2 milliseconds.)*

Now ask: *What would happen if the evidence trail went cold halfway back?*  
That’s the **vanishing gradient problem**—and we’ll see how it shapes the design of every modern architecture.

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

The forward pass is like assembling a Rube Goldberg machine:  
- Each component depends on the last.  
- The final action—dropping a ball into a cup—is the loss.

But to improve it, you don’t rebuild the whole machine.  
You **reverse** it: watch the ball pop out, and ask, *“Which lever, if adjusted, would most affect the final miss?”*

Each operation becomes a node in a **computational graph**, a directed acyclic graph where edges represent data flow and nodes represent functions.

Crucially: we **cache** intermediate values ($ z^{(1)}, a^{(1)}, z^{(2)} $) during the forward pass.  
Why? Because derivatives depend on them. For example, $ \frac{d}{dz}\tanh(z) = 1 - \tanh^2(z) $—you can’t compute this without $ z $.

This is the **memory-speed tradeoff** of backpropagation: store intermediates to avoid recomputation.

> **Formative Check (Forward Pass)**  
> Given $ x = \begin{bmatrix}1 \\ 0\end{bmatrix} $, $ W^{(1)} = \begin{bmatrix}1 & 1 \\ -1 & 1\end{bmatrix} $, $ b^{(1)} = \begin{bmatrix}0 \\ 0\end{bmatrix} $, compute $ z^{(1)} $ and $ a^{(1)} $.  
> *(Answer: $ z^{(1)} = \begin{bmatrix}1 \\ -1\end{bmatrix} $, $ a^{(1)} = \begin{bmatrix}\tanh(1) \\ \tanh(-1)\end{bmatrix} \approx \begin{bmatrix}0.762 \\ -0.762\end{bmatrix} $.)*

> **Try this yourself**: Suppose $ x_2 $ were 0 in every training example. What would happen to the second column of $ W^{(1)} $ during training? Why?  
> *(Hint: Look at how gradients depend on input values.)*

> **Case Study: Image Classification with Dead Inputs**  
> In early vision models, researchers noticed that some filters stopped learning entirely. Tracing back, they found that preprocessing steps (like mean subtraction) sometimes zeroed out entire input channels. Since gradients scale with input, those weights received no updates—like a microphone unplugged mid-recording. This silent failure is now avoided by monitoring gradient flow.

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

> **Try this yourself**: If $ a^{(1)}_j = 0 $ for a particular neuron, what happens to the gradient of all weights connected to it in $ W^{(2)} $? What does this imply about “silent” neurons during training?

> **Real-World Analogy: Blame in a Supply Chain**  
> Imagine a defective smartphone. The final inspection (output layer) detects the flaw and sends an alert back through the factory. Each station checks: *Did I contribute?*  
> The screen installer says: “My part passed.” But the battery team sees their component failed the test.  
> However, if the battery was never installed (activation ≈ 0), the alert never reaches them—their station gets no blame, no update.  
> Just like backpropagation: no activation, no gradient, no learning.

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

> **Backpropagation is like a hydroelectric dam system**:  
> - The loss is the reservoir—its level represents error.  
> - When you open the spillway, water (error signal) flows backward through turbines (layers).  
> - Each turbine’s output depends on the flow *and* the gate opening (activation derivative $ f'(z) $).  
> - If the gate is nearly shut ($ f'(z) \approx 0 $), no energy is extracted—no learning occurs downstream.  
> - The flow reaching earlier turbines depends on all gates in between.  
> - A broken turbine (dead ReLU) blocks the entire river.

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

> **Try this yourself**: If $ W^{(2)} $ were zero, what would happen to $ \delta^{(1)} $? What if $ W^{(2)} $ were very large? How does this relate to gradient explosion?

> **Case Study: Vanishing Gradients in Speech Recognition**  
> In the 1990s, RNNs failed to learn long-term dependencies in speech. Gradients from the final phoneme would vanish before reaching earlier layers—like a whisper lost down a long hallway.  
> This wasn’t fixed by more data or compute. It took a new architecture: **LSTM**, with its “constant error carousel” (a forget gate that preserves gradient flow).  
> The solution wasn’t better backprop—it was designing layers that *cooperate* with backpropagation.

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

> **Insight**: Notice that $ \frac{\partial J}{\partial W^{(1)}} $ only updates the first column of $ W^{(1)} $, because $ x_2 = 0 $. Inputs that