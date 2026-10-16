# Lecture on Backpropagation in Neural Networks

## 1. Introduction

Backpropagation is a widely used method for training feedforward neural networks. It is a gradient-based algorithm that allows information to flow from the output layer back through the hidden layers, in order to compute the gradient of the cost function with respect to the network's parameters. This process is called backpropagation, and it is often simply called backprop.

## 2. Prerequisites

Before we dive into backpropagation, let's review some foundational concepts:

- The forward propagation process:
  - The network receives an input $ x $.
  - The information is propagated up through the hidden units at each layer.
  - An output $ y $ is produced.
  - The forward propagation process can be described by the following equation:
    $$ y = f(\sigma(W_1 x + b_1) \cdot W_2) $$
  - where:
    - $ W_1 $ and $ b_1 $ are the weights and biases of the first hidden layer.
    - $ W_2 $ and $ b_2 $ are the weights and biases of the output layer.
    - $ f(z) $ is the activation function applied to the weighted sum $ z $.
    - $ \sigma(z) $ is the sigmoid function.

## 3. Intuition

We can think of backpropagation as a way to adjust the weights and biases of each hidden unit in order to minimize the error between the predicted output $ y $ and the actual output $ y $.

## 4. Formal Definition and Derivation

During the training process, the network is exposed to a set of inputs and corresponding outputs. The backpropagation algorithm allows the information from the cost function to flow backwards through the network, in order to compute the gradient of the cost function with respect to the network's parameters.

$$ \delta = f'(y) \cdot g(z) $$

where:
- $ \delta $ is the error signal.
- $ f'(y) $ is the derivative of the activation function.
- $ g(z) $ is the derivative of the cost function with respect to the input $ z $.
- $ y $ is the output of the network.

## 5. Fully Worked Example

Let's walk through a step-by-step example of backpropagation for a simple neural network with one hidden layer.

1. For the output layer:
   - Compute the predicted output $ y $ using the forward propagation equation.
   - Compute the error signal $ \delta $ using the backpropagation equation.

2. For each hidden unit:
   - Compute the error signal $ \delta $ for the current hidden unit using the backpropagation equation.
   - Update the weights and biases of the current hidden unit using the following equation:
     $$ \Delta w_j = \alpha \cdot \delta_j \cdot f'(y) \cdot g(z) $$
     where:
     - $ \Delta w_j $ is the update to the weight $ w_j $.
     - $ \alpha $ is the learning rate.
     - $ \delta_j $ is the error signal for the current hidden unit.
     - $ f'(y) $ is the derivative of the activation function.
     - $ g(z) $ is the derivative of the cost function with respect to the input $ z $.

3. For the output layer:
   - Compute the error signal $ \delta $ for the current output unit using the backpropagation equation.
   - Update the weights and biases of the current output unit using the following equation:
     $$ \Delta b_j = \alpha \cdot \delta_j $$
     where:
     - $ \Delta b_j $ is the update to the bias $ b_j $.
     - $ \alpha $ is the learning rate.
     - $ \delta_j $ is the error signal for the current output unit.

## 6. Applications

Backpropagation is widely used in various applications, including:
- Image recognition: used to classify images of cats, dogs, and other objects.
- Text processing: used to analyze and classify text documents.
- Time-series prediction: used to forecast future values based on historical data.
- Recommendation systems: used to suggest products or services to users based on their preferences.

## 7. Common Pitfalls and Limitations

- Overfitting: The network may fit the training data too closely, leading to poor generalization to new data.
- Vanishing gradients: The gradient of the error signal may become too small, making it difficult to update the weights and biases.
- Learning rate: If the learning rate is too large, the network may converge too quickly, or if it is too small, the updates may be too small to make a significant impact.

By understanding the practical relevance of backpropagation in neural networks, students can better grasp how these algorithms work and how to apply them in various real-world applications.