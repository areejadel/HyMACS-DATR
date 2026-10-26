You

1. **Remember**: Identify the purpose of backpropagation and its role in training neural networks.  
2. **Understand**: Explain how the chain rule is applied in reverse mode to compute gradients efficiently in a computational graph.  
3. **Apply**: Compute gradients step by step using backpropagation for a simple feedforward network with one hidden layer.  
4. **Analyze**: Diagnose common issues such as vanishing gradients and dead neurons by inspecting activation functions and gradient flow.  
5. **Create**: Implement a correct and numerically stable backpropagation procedure for a given network architecture.

---

### Prerequisites: Required Background

Before proceeding, ensure familiarity with the following concepts:  
- **Vectors and matrices**: Matrix-vector multiplication, transposition, and dimension compatibility.  
- **Basic calculus**: Partial derivatives and the multivariable chain rule.  
- **Forward pass in neural networks**: Computation of outputs via weighted sums, biases, and activation functions.

> 💡 *Quick Check (Prerequisites)*:  
> Given $ z = Wx + b $ and $ h = \text{ReLU}(z) $, write the expression for $ h_i $. Then compute $ \frac{\partial h_i}{\partial z_j} $.  
> *(Answer: $ h_i = \max(0, z_i) $; the derivative is $ \delta_{ij} $ if $ z_i > 0 $, and 0 otherwise, where $ \delta_{ij} $ is the Kronecker delta.)*

If this is unfamiliar, review vector calculus and ReLU properties before continuing.

> ✅ *Formative Check (Prerequisites)*:  
> Suppose $ x = [1, -2]^\top $, $ W = \begin{bmatrix} 1 & 0 \\ 1 & -1 \end{bmatrix} $, $ b = [0, 1]^\top $. Compute $ z = Wx + b $, then $ h = \text{ReLU}(z) $.  
> *(Answer: $ z = [1, 4]^\top $, $ h = [1, 4]^\top $.)*

---

### A Puzzle: Why Can’t We Just “See” the Right Weights?

Imagine you're tuning a high-precision telescope with hundreds of interdependent dials. Each dial slightly shifts the image, but none directly controls focus, brightness, or alignment. You can see the final image and measure its sharpness—but how do you decide which dial to turn, and by how much?

You could tweak each one randomly and hope for improvement. But with 100 dials, that’s impossibly slow. Or, you could ask: *How much did this dial contribute to the blur?* That’s the core challenge in training neural networks.

**Backpropagation is the calculus of contribution.** It answers: *If I nudged this weight, how would the loss change—accounting for all the downstream effects through hidden layers?*  

But here’s the catch: the influence of an early weight ripples through many transformations before affecting the loss. Computing this naively would require evaluating thousands of partial derivatives. Backpropagation avoids this by **reusing sensitivity information** as it flows backward—like retracing your steps through a maze with a trail of breadcrumbs.

> 🔥 *Try This Yourself (Conceptual)*:  
> Suppose a network misclassifies a cat as a dog. The final layer made the wrong decision—but was it because:  
> - The last weights were off?  
> - The hidden layer didn’t extract the right features?  
> - The first layer failed to detect edges?  
> How would you *quantify* each layer’s blame? Write down your intuition before reading on.

> 💡 *Interactive Exercise: Gradient Detective*  
> You’re given a 3-layer network that outputs a single number. The loss is high. You can inspect the gradient magnitude (averaged) at each layer:  
> - Layer 1: $ \|\nabla W^{(1)}\| \approx 10^{-6} $  
> - Layer 2: $ \|\nabla W^{(2)}\| \approx 10^{-3} $  
> - Layer 3: $ \|\nabla W^{(3)}\| \approx 10^{-1} $  
> Rank the layers by “responsibility” for poor performance. Is this ranking meaningful? What might explain the gradient pattern? Discuss with a peer.

> ✅ *Formative Check (Intuition)*:  
> In the telescope analogy, which dial should you adjust first: one with a large effect on sharpness or one with a small effect? Why might adjusting a dial with zero effect be wasteful?

---

### Network Definition and Forward Pass

Let’s start with a **concrete example** before generalizing.

Consider a two-layer multilayer perceptron (MLP) for classification. We define the following:

- Input: $ x \in \mathbb{R}^d $
- Hidden layer parameters:  
  - Weight matrix $ W^{(1)} \in \mathbb{R}^{h \times d} $  
  - Bias vector $ b^{(1)} \in \mathbb{R}^h $
- Output layer parameters:  
  - Weight matrix $ W^{(2)} \in \mathbb{R}^{k \times h} $  
  - Bias vector $ b^{(2)} \in \mathbb{R}^k $
- Activation function: $ g(z) = \text{ReLU}(z) = \max(0, z) $
- Output activation: $ \text{softmax}(a)_i = \frac{e^{a_i}}{\sum_{j=1}^k e^{a_j}} $
- Loss function: Cross-entropy, $ J = -\sum_{i=1}^k y_i \log \hat{y}_i $

The forward pass proceeds as follows:

$$
a^{(1)} = W^{(1)}x + b^{(1)}, \quad h = g(a^{(1)})
$$
$$
a^{(2)} = W^{(2)}h + b^{(2)}, \quad \hat{y} = \text{softmax}(a^{(2)})
$$

These operations form a **computational graph**, where each variable depends on prior computations.

> 🧠 *Analogy: Pipeline Inspection*  
> Think of the forward pass as sending a diagnostic drone through a pipeline. It records pressure (activations) at each station. The drone emerges with a final report: "Leak detected." But to fix the pipeline, you need to know *where* the problem started. Backpropagation is the reverse trip: analyzing how each station contributed to the final fault.

> ❗ *Common Misconception Alert*:  
> The network cannot learn without updating weights based on error. However, error must be propagated back through all layers—direct inspection of the output does not reveal how earlier weights should change. Gradients provide this link.

> 💡 *Interactive Exercise: Build the Graph*  
> Using paper or a whiteboard, draw the full computational graph for this network, including all scalar operations: matrix multiplies, bias adds, ReLU, softmax, and cross-entropy. Label each edge with the corresponding derivative. Now simulate the forward pass with the given values. This tactile step builds intuition for the backward flow.

> ✅ *Formative Check (Forward Pass)*:  
> Let $ x = [2, -1]^\top $, $ W^{(1)} = \begin{bmatrix} 1 & 0 \\ -1 & 2 \end{bmatrix} $, $ b^{(1)} = [0, 1]^\top $. Compute $ a^{(1)} $ and $ h $.  
> *(Answer: $ a^{(1)} = [2, 5]^\top $, $ h = [2, 5]^\top $, since ReLU preserves positive values.)*

---

### Core Mechanism: Reverse-Mode Differentiation

Let’s **start with a simple scalar example** to build intuition.

Suppose $ z = w x $, $ h = \text{ReLU}(z) $, $ J = h $. What is $ \frac{\partial J}{\partial w} $?  
We can’t compute this directly—we must go through $ z $. The chain rule gives:
$$
\frac{\partial J}{\partial w} = \frac{\partial J}{\partial h} \cdot \frac{\partial h}{\partial z} \cdot \frac{\partial z}{\partial w}
$$
We compute this **backward**, starting from $ J $:
- $ \frac{\partial J}{\partial h} = 1 $
- $ \frac{\partial h}{\partial z} = \mathbf{1}_{z > 0} $ (1 if $ z > 0 $, else 0)
- $ \frac{\partial z}{\partial w} = x $

So $ \frac{\partial J}{\partial w} = 1 \cdot \mathbf{1}_{z > 0} \cdot x $

Now generalize: in a network, we define the **error signal** at any node $ u $ as:
$$
\delta_u = \frac{\partial J}{\partial u}
$$

Using the chain rule, for any node $ u $ with successors $ v_j $:
$$
\delta_u = \sum_j \delta_{v_j} \cdot \frac{\partial v_j}{\partial u}
$$

We initialize $ \delta_J = 1 $ and propagate backward.

> 🧠 *Analogy: Blame Assignment in a Relay Race*  
> Imagine a 4-person relay race where the team performs poorly. You can’t just blame the last runner—you need to know how each leg affected the final time. But you don’t re-run the whole race four times. Instead, you start from the finish line and ask: *How much did the previous runner’s performance affect this one’s start?* Then repeat. Backpropagation does this for gradients: it assigns "blame" backward, reusing each runner’s sensitivity to their predecessor.

> 🔥 *Try This Yourself (Chain Rule Flow)*:  
> Draw the computational graph for $ z = Wx + b $, $ h = \text{ReLU}(z) $, $ a = Wh + b $, $ J = \|a - y\|^2 $. Now, trace the path from $ J $ back to $ W^{(1)} $. At each node, write down what derivative you’d compute. Don’t calculate—just map the flow.

> 💡 *Interactive Exercise: The Gradient Tape*  
> Simulate automatic differentiation using a “gradient tape.” Write down every operation in the forward pass. Then, during backprop, walk backward through the tape, computing and storing each local gradient. For each operation (e.g., matrix multiply, ReLU), write the corresponding gradient rule. This mirrors how frameworks like PyTorch implement autograd.

> ❗ *Common Misconception Alert*:  
> Backpropagation computes **numerical gradients** given current activations—it does not perform symbolic differentiation. The method is automatic and exact for the current parameter values.

> ✅ *Formative Check (Chain Rule)*:  
> Let $ z = wx $, $ h = \text{ReLU}(z) $, $ J = h $, with $ w = 2 $, $ x = 3 $. Compute $ \frac{\partial J}{\partial w} $.  
> *(Answer: $ z = 6 $, $ h = 6 $, $ \frac{\partial J}{\partial z} = 1 $, $ \frac{\partial z}{\partial w} = x = 3 $, so $ \frac{\partial J}{\partial w} = 3 $.)*

---

### Worked Example: Step-by-Step Backpropagation

We now compute gradients for a two-layer MLP using concrete values.

#### Problem Setup

- Input: $ x = [1, 2]^\top $
- True label: $ y = [0, 1]^\top $ (class 2)
- Parameters:
  $$
  W^{(1)} = \begin{bmatrix} 1 & -1 \\ 0 & 2 \end{bmatrix},\quad
  b^{(1)} = \begin{bmatrix} 1 \\ 0 \end{bmatrix},\quad
  W^{(2)} = \begin{bmatrix} 1 & 1 \\ -1 & 2 \end{bmatrix},\quad
  b^{(2)} = \begin{bmatrix} 0 \\ -1 \end{bmatrix}
  $$

#### Step 1: Forward Pass

Compute hidden layer pre-activation:
$$
a^{(1)} = W^{(1)}x + b^{(1)} = 
\begin{bmatrix} 1 & -1 \\ 0 & 2 \end{bmatrix}
\begin{bmatrix} 1 \\ 2 \end{bmatrix} +
\begin{bmatrix} 1 \\ 0 \end{bmatrix} =
\begin{bmatrix} 1 - 2 + 1 \\ 0 + 4 + 0 \end{bmatrix} =
\begin{bmatrix} 0 \\ 4 \end{bmatrix}
$$

Apply ReLU:
$$
h = \text{ReLU}(a^{(1)}) = \begin{bmatrix} 0 \\ 4 \end{bmatrix}
$$

Compute output pre-activation:
$$
a^{(2)} = W^{(2)}h + b^{(2)} = 
\begin{bmatrix} 1 & 1 \\ -1 & 2 \end{bmatrix}
\begin{bmatrix} 0 \\ 4 \end{bmatrix} +
\begin{bmatrix} 0 \\ -1 \end{bmatrix} =
\begin{bmatrix} 4 \\ 8 - 1 \end{bmatrix} =
\begin{bmatrix} 4 \\ 7 \end{bmatrix}
$$

Apply softmax:
$$
\hat{y} = \text{softmax}(a^{(2)}) = \frac{1}{e^4 + e^7} \begin{bmatrix} e^4 \\ e^7 \end{bmatrix} \approx \frac{1}{54.6 + 1096.6} \begin{bmatrix} 54.6 \\ 1096.6 \end{bmatrix} \approx \begin{bmatrix} 0.047 \\ 0.953 \end{bmatrix}
$$

Compute cross-entropy loss:
$$
J = -y^\top \log \hat{y} = - (0 \cdot \log 0.047 + 1 \cdot \log 0.953) \approx -(-0.0481) = 0.0481
$$

#### Step 2: Backward Pass

**Output layer error signal**:  
For softmax with cross-entropy, the gradient simplifies:
$$
\delta^{(2)} = \frac{\partial J}{\partial a^{(2)}} = \hat{y} - y \approx \begin{bmatrix} 0.047 \\ 0.953 \end{bmatrix} - \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} 0.047 \\ -0.047 \end{bmatrix}
$$

> 🔍 *Why this shortcut?*  
> The derivative of cross-entropy loss with respect to pre-softmax logits $ a_i $ is $ \hat{y}_i - y_i $. This arises from combining the softmax Jacobian with the log-likelihood gradient. It’s a rare gift: a clean, stable gradient expression that avoids numerical pitfalls.

Now propagate backward to hidden layer:

$$
\delta^{(1)} = \frac{\partial J}{\partial h} \cdot \frac{\partial h}{\partial a^{(1)}} = \left( (W^{(2)})^\top \delta^{(2)} \right) \odot g'(a^{(1)})
$$

First, compute:
$$
(W^{(2)})^\top \delta^{(2)} = 
\begin{bmatrix} 1 & -1 \\ 1 & 2 \end{bmatrix}
\begin{bmatrix} 0.047 \\ -0.047 \end{bmatrix} =
\begin{bmatrix} 0.047 + 0.047 \\ 0.047 - 0.094 \end{bmatrix} =
\begin{bmatrix} 0.094 \\ -0.047 \end{bmatrix}
$$

Now apply ReLU derivative: $ g'(a^{(1)}) = [0, 1]^\top $ since $ a^{(1)} = [0, 4]^\top $

Thus:
$$
\delta^{(1)} = \begin{bmatrix} 0.094 \\ -0.047 \end{bmatrix} \odot \begin{bmatrix} 0 \\ 1 \end{bmatrix} = \begin{bmatrix} 0 \\ -0.047 \end{bmatrix}
$$

> 🧠 *Analogy: Gradient as a Voltage Drop*  
> Think of each neuron as a node in an electrical circuit. The error signal $ \delta $ is like voltage: it drives current (weight updates). But ReLU acts like a diode—it only allows backward "current" if the neuron was active (positive during forward pass). Here, the first neuron was off ($ a_1 = 0 $), so no gradient flows through it. It’s *electrically isolated* in the backward pass.

Now compute gradients:

**Output weights:**
$$
\frac{\partial J}{\partial W^{(2)}} = \delta^{(2)} h^\top = 
\begin{bmatrix} 0.047 \\ -0.047 \end{bmatrix}
\begin{bmatrix} 0 & 4 \end{bmatrix} =
\begin{bmatrix} 0 & 0.188 \\ 0 & -0.188 \end{bmatrix}
$$

**Output bias:**
$$
\frac{\partial J}{\partial b^{(2)}} = \delta^{(2)} = \begin{bmatrix} 0.047 \\ -0.047 \end{bmatrix}
$$

**Hidden weights:**
$$
\frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} x^\top = 
\begin{bmatrix} 0 \\ -0.047 \end{bmatrix}
\begin{bmatrix} 1 & 2 \end{bmatrix} =
\begin{bmatrix} 0 & 0 \\ -0.047 & -0.094 \end{bmatrix}
$$

**Hidden bias:**
$$
\frac{\partial J}{\partial b^{(1)}} = \delta^{(1)} = \begin{bmatrix} 0 \\ -0.047 \end{bmatrix}
$$

> 🔥 *Try This Yourself (Interpretation)*:  
> Look at $ \frac{\partial J}{\partial W^{(1)}} $. Which weights are getting zero gradient? Why? What would happen if this pattern persisted over many training steps?

> 💡 *Interactive Exercise: Perturb and Observe*  
> Take the trained weights and apply a tiny perturbation: add $ 10^{-4} $ to $ W^{(1)}_{11} $. Recompute the forward pass and loss. Compare the observed change in $ J $ to the predicted change using $ \frac{\partial J}{\partial W^{(1)}_{11}} $. This validates your gradient computation and builds trust in backprop.

> ✅ *Formative Check (Backward Pass)*:  
> Suppose $ \delta^{(1)} = [0, -0.047]^\top $. What is $ \frac{\partial J}{\partial b^{(1)}_1} $? What about $ \frac{\partial J}{\partial W^{(1)}_{21}} $?  
> *(Answer: $ -0.047 $; $ 0 $, since $ x_1 = 1 $, so $ \partial J / \partial W^{(1)}_{21} = \delta^{(1)}_2 x_1 = -0