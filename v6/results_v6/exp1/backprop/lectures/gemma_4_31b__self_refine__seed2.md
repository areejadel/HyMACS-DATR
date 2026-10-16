# Lecture: Backpropagation in Neural Networks

## Learning Objectives
By the end of this lecture, you will be able to:
1. **Understand** the "Credit Assignment Problem" and why the chain rule is the necessary solution for training deep networks.
2. **Apply** the chain rule to derive the local gradient for a single weight and bias.
3. **Analyze** the recursive nature of the error signal ($\delta$) to explain how gradients flow from the output layer back to the input.
4. **Evaluate** the impact of activation functions and weight initialization on the stability of gradients (vanishing/exploding gradients).
5. **Create** a step-by-step execution trace of the backpropagation algorithm for a multi-layer perceptron.

---

## 1. Prerequisites: The Forward Pass

**The Hook: The Black Box Paradox**
Imagine a network with 100 million parameters. When the network misclassifies a "dog" as a "cat," the cost function tells us *that* we are wrong, but it doesn't tell us *who* is responsible. Is it a weight in the final layer that misread the evidence? Or a weight in the first layer that failed to detect a whisker? This is the fundamental tension of deep learning: we have a global measure of failure (the Cost), but we need local instructions for every single parameter. To solve this, we first need a deterministic path from input to output.

### 1.1 Intuition: The Layered Transformation
A neural network operates as a series of filters. Each layer takes the features discovered by the previous layer, transforms them linearly via scaling and shifting, and applies a non-linear activation function to determine which information is passed to the subsequent stage.

### 1.2 Formalism: The Forward Pass
For any layer $l \in \{1, \dots, L\}$, the forward pass consists of two steps:

1. **Linear Transformation**: We compute the pre-activation (logit) $z^{(l)}$:
   $$z^{(l)} = W^{(l)}a^{(l-1)} + b^{(l)}$$
   where $W^{(l)}$ is the weight matrix, $a^{(l-1)}$ is the activation vector from the previous layer, and $b^{(l)}$ is the bias vector.

2. **Non-linear Activation**: We apply an element-wise activation function $\sigma$ to produce the output activation $a^{(l)}$:
   $$a^{(l)} = \sigma(z^{(l)})$$

### 1.3 Worked Example: Forward Pass Calculation
Consider a single neuron in layer 1 with the following parameters:
- **Inputs**: $a^{(0)} = [1.0, -0.5]^T$
- **Weights**: $W^{(1)} = \begin{pmatrix} 0.5 & 0.2 \\ -0.1 & 0.8 \end{pmatrix}$
- **Bias**: $b^{(1)} = [0.1, 0.1]^T$
- **Activation**: $\sigma(z) = \text{ReLU}(z) = \max(0, z)$

**Computation Steps:**
1. **Compute $z^{(1)}$**:
   $$z_1^{(1)} = (0.5 \times 1.0) + (0.2 \times -0.5) + 0.1 = 0.5$$
   $$z_2^{(1)} = (-0.1 \times 1.0) + (0.8 \times -0.5) + 0.1 = -0.4$$
2. **Apply ReLU**:
   $$a_1^{(1)} = \max(0, 0.5) = 0.5$$
   $$a_2^{(1)} = \max(0, -0.4) = 0$$
   **Result**: $a^{(1)} = [0.5, 0]^T$

**Try This Yourself**: Change the input $a^{(0)}$ to $[-1.0, 0.5]^T$. Calculate $z^{(1)}$ and $a^{(1)}$. How does the ReLU activation change the "information" flowing to the next layer compared to a linear activation?

---

## 2. The Credit Assignment Problem and the Chain Rule

### 2.1 Intuition: The Credit Assignment Problem
The Credit Assignment Problem is the challenge of determining how much a specific weight $w$ in an early layer contributed to the final cost $J$. 

**Analogy: The Corporate Hierarchy**
Think of a neural network as a corporate hierarchy. The CEO (Output Layer) makes a bad decision (High Cost). To fix it, the CEO doesn't just fire themselves; they identify which Vice Presidents (Hidden Layer) gave them bad data. Those VPs, in turn, identify which Managers (Early Layers) provided the faulty reports. The "blame" is passed backward, scaled by how much each person's input actually influenced the final decision.

### 2.2 Formalism: The Chain Rule
To find the gradient of the cost $J$ with respect to a weight $w$ ($\frac{\partial J}{\partial w}$), we decompose the dependency chain:
$$w \to z \to a \to \dots \to J$$

Using the chain rule, the gradient is calculated as:
$$\frac{\partial J}{\partial w} = \frac{\partial J}{\partial z} \cdot \frac{\partial z}{\partial w}$$

We define the **error signal** $\delta$ as the sensitivity of the cost to the pre-activation:
$$\delta = \frac{\partial J}{\partial z}$$

### 2.3 Worked Example: Computing a Local Gradient
Assume a Mean Squared Error cost $J = \frac{1}{2}(a^{(L)} - y)^2$ and a Sigmoid activation $\sigma(z)$ where $\sigma'(z) = \sigma(z)(1-\sigma(z))$.
- **Given**: $a^{(L)} = 0.7$, Target $y = 1.0$, and $\sigma'(z^{(L)}) = 0.20$.

**Derivation Steps:**
1. **Cost Sensitivity**: Compute how $J$ changes relative to the output $a^{(L)}$:
   $$\frac{\partial J}{\partial a^{(L)}} = (a^{(L)} - y) = (0.7 - 1.0) = -0.3$$
2. **Activation Sensitivity**: Compute how $a^{(L)}$ changes relative to the logit $z^{(L)}$:
   $$\frac{\partial a^{(L)}}{\partial z^{(L)}} = \sigma'(z^{(L)}) = 0.20$$
3. **The Error Signal ($\delta^{(L)}$)**:
   $$\delta^{(L)} = \frac{\partial J}{\partial a^{(L)}} \cdot \frac{\partial a^{(L)}}{\partial z^{(L)}} = (-0.3) \times (0.20) = -0.06$$

**Technical Note**: $\delta$ is always defined relative to the pre-activation $z$, not the activation $a$. This is because weights $W$ directly influence $z$.

**Intellectual Tension**: If we have 100 layers, we could calculate the derivative for every single weight from scratch. But if we do that, we will calculate the derivative of the output layer 100 million times. Is there a way to "save" our work?

---

## 3. Efficiency via Dynamic Programming

### 3.1 Intuition: Avoiding Redundant Computation
Backpropagation is essentially an application of **Dynamic Programming**. Instead of re-calculating the chain for every weight, we calculate the error signal $\delta$ for the output layer and "cache" it, using it to compute the errors for the layer immediately preceding it.

### 3.2 The Error Signal Recursion
To compute the error signal for a hidden layer $\delta^{(l-1)}$, we aggregate the errors from all neurons in the subsequent layer $l$ that the current neuron feeds into.

**The Recursion Formula**:
$$\delta^{(l-1)} = \left( (W^{(l)})^T \delta^{(l)} \right) \odot \sigma'(z^{(l-1)})$$
where $\odot$ denotes the element-wise (Hadamard) product.

**Formula Components**:
1. $(W^{(l)})^T \delta^{(l)}$: Distributes the errors from the next layer back across the weights.
2. $\odot \sigma'(z^{(l-1)})$: Scales the error by the slope of the activation function at the current neuron.

**Cross-Domain Connection: Control Theory**
This recursion is strikingly similar to the **Adjoint State Method** used in optimal control (e.g., calculating the trajectory of a rocket). In both cases, we solve a "forward" problem to find the state and a "backward" (adjoint) problem to find the sensitivity of the goal to the initial parameters.

### 3.3 Memory Trade-off: Activation Caching
Computing $\delta^{(l-1)}$ requires $z^{(l-1)}$ and $a^{(l-1)}$, which are generated during the forward pass. In large-scale models, storing all intermediate activations consumes significant VRAM. To mitigate this, **Gradient Checkpointing** is used: only select activations are saved, and intermediate values are re-computed during the backward pass, trading compute time for memory efficiency.

---

## 4. The Full Backpropagation Algorithm

### 4.1 Algorithmic Sequence
The complete backpropagation process is executed in four primary steps.

**Step 1: Forward Pass**
For $l = 1 \dots L$:
- Compute $z^{(l)} = W^{(l)}a^{(l-1)} + b^{(l)}$ and $a^{(l)} = \sigma(z^{(l)})$.
- Cache $z^{(l)}$ and $a^{(l)}$ for use in the backward pass.

**Step 2: Output Error**
Compute the error signal for the final layer $L$:
$$\delta^{(L)} = \nabla_{a^{(L)}} J \odot \sigma'(z^{(L)})$$

**Step 3: Backward Pass**
For $l = L-1, L-2, \dots, 1$:
1. **Propagate Error**: $\delta^{(l)} = ((W^{(l+1)})^T \delta^{(l+1)}) \odot \sigma'(z^{(l)})$
2. **Compute Weight Gradient**: $\frac{\partial J}{\partial W^{(l)}} = \delta^{(l)} (a^{(l-1)})^T$
3. **Compute Bias Gradient**: $\frac{\partial J}{\partial b^{(l)}} = \delta^{(l)}$

**Step 4: Parameter Update**
Update weights using gradient descent with learning rate $\eta$:
$$W_{new} = W_{old} - \eta \frac{\partial J}{\partial W}$$

### 4.2 Worked Example: Full Trace
**Setup**: 1 input $\to$ 1 hidden neuron $\to$ 1 output neuron.
- $a^{(0)}=1, W^{(1)}=0.5, b^{(1)}=0, \sigma(z)=z$ (Identity)
- $W^{(2)}=0.8, b^{(2)}=0, \sigma(z)=z$ (Identity)
- Target $y=1$, Cost $J = \frac{1}{2}(a^{(2)}-y)^2$

**Execution Trace**:
1. **Forward Pass**:
   $z^{(1)} = 0.5(1)+0 = 0.5 \implies a^{(1)} = 0.5$
   $z^{(2)} = 0.8(0.5)+0 = 0.4 \implies a^{(2)} = 0.4$
2. **Output Error**:
   $\frac{\partial J}{\partial a^{(2)}} = (0.4 - 1) = -0.6$. Since $\sigma' = 1$, $\delta^{(2)} = -0.6$.
3. **Backward Pass**:
   $\delta^{(1)} = (W^{(2)})^T \delta^{(2)} \cdot \sigma'(z^{(1)}) = (0.8 \times -0.6) \times 1 = -0.48$
   $\frac{\partial J}{\partial W^{(1)}} = \delta^{(1)} \cdot a^{(0)} = -0.48 \times 1 = -0.48$
4. **Update**:
   With $\eta=0.1$, $W^{(1)}_{new} = 0.5 - (0.1 \times -0.48) = 0.548$.

**Try This Yourself**: If the target $y$ was $0.4$ instead of $1$, what would happen to the update of $W^{(1)}$? Why does this make intuitive sense?

---

## 5. Stability and Advanced Dynamics

### 5.1 Vanishing and Exploding Gradients
The error signal $\delta^{(l)}$ is a product of weights and derivatives: $\delta^{(l)} \approx \prod (W \cdot \sigma')$.

**The Mathematical Trap**: If you multiply a number by $0.9$ one hundred times, it vanishes toward zero. If you multiply by $1.1$ one hundred times, it explodes.
- **Vanishing Gradients**: If $\sigma'$ is small (e.g., Sigmoid maxes at 0.25) or weights are $< 1$, the product shrinks exponentially. Early layers cease to learn as their gradients approach zero.
- **Exploding Gradients**: If weights are large ($> 1$), the product grows exponentially, often resulting in `NaN` values.

**Mitigation Strategies**:
- **ReLU Activation**: $\sigma'(z) = 1$ for $z>0$, preventing the shrinkage associated with Sigmoid.
- **He/Xavier Initialization**: Initializing weights such that the variance of activations remains constant across layers, preventing the product from drifting toward $0$ or $\infty$.
- **Gradient Clipping**: Capping the gradient magnitude to a maximum threshold.

### 5.2 Regularization (Weight Decay)
To prevent overfitting, a penalty term is added to the cost:
$$J_{total} = J_{data} + \frac{\lambda}{2} \sum \|w\|^2$$
The resulting gradient is:
$$\frac{\partial J_{total}}{\partial w} = \frac{\partial J_{data}}{\partial w} + \lambda w$$
**Analogy**: This penalty acts as a "physical spring" attached to every weight, constantly pulling it back toward zero. This prevents any single weight from becoming an "outlier" that over-fits a specific training example.

### 5.3 Modern Implementations: Autograd
Modern frameworks (PyTorch, TensorFlow) utilize **Reverse-Mode Automatic Differentiation**:
1. A **Computational Graph** is constructed during the forward pass (essentially a map of every operation).
2. Each node stores its own local derivative.
3. The engine traverses the graph backward, multiplying these stored local derivatives to compute the total gradient.

---

## 6. Summary of Common Pitfalls
- **Dimension Mismatch**: $\delta^{(l)}$ must match the number of neurons in layer $l$, and $\frac{\partial J}{\partial W^{(l)}}$ must match the dimensions of $W^{(l)}$.
- **The Dying ReLU**: If a weight update causes $z < 0$ for all training samples, the neuron outputs $0$ and its gradient becomes $0$. This neuron is effectively "dead" and cannot be revived by standard backpropagation. **Fix**: Use Leaky ReLU, where $\sigma(z) = 0.01z$ for $z < 0$.
- **Learning Rate $\eta$**: An excessively high $\eta$ leads to divergence (overshooting), while an excessively low $\eta$ leads to stagnation (slow convergence).