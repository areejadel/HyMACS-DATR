# Lecture: Backpropagation in Neural Networks

## Learning Objectives

1. Understand the definition and practical relevance of backpropagation in neural networks.
2. Apply the chain rule of differentiation to compute the gradient of the cost function with respect to the network's parameters.
3. Analyze the limitations and common pitfalls of backpropagation.

### Learning Check 1:

What is backpropagation?

Backpropagation is a fundamental algorithm used in training feedforward neural networks, enabling efficient computation of the gradient. Imagine learning a new skill and needing feedback on your performance to improve. Backpropagation helps neural networks learn by propagating error backwards through the layers of the network, similar to how a coach would provide constructive feedback.

### Learning Check 2:

Compute the gradient of the cost function $ J(θ) $ with respect to the weight matrix $ W $ for a feedforward network with a single hidden layer.

For a feedforward network with a single hidden layer, the gradient of the cost function $ J(θ) $ with respect to the weight matrix $ W $ is given by:

$$ \frac{\partial J(θ)}{\partial W} = f'(Wx + b) \cdot f(Wx + b) $$

### Learning Check 3:

Identify the limitations and common pitfalls of backpropagation.

Backpropagation is a fundamental algorithm used in training feedforward neural networks, enabling efficient computation of the gradient. However, like any tool, backpropagation has its limitations and common pitfalls, such as high computational cost, vanishing/exploding gradients, and local minima/saddle points. These issues can hinder the network's performance and require additional techniques to overcome.