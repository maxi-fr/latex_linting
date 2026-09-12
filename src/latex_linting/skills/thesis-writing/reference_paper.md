# Exact Multiple-Step Predictions in Gaussian Process-based Model Predictive Control: Observations, Possibilities, and Challenges

Maik Pfefferkorn, Michael Maiworm and Rolf Findeisen

*Abstract*— Employing learned Gaussian process models in nonlinear model predictive control raises the problem of repeatedly propagating a probability distribution through a nonlinear mapping, which is a challenging task. Existing solutions are either computationally expensive or conservative. We propose to use Gaussian process models that directly yield the entire state sequence without repeated evaluations. As therefrom an exact Gaussian distribution is obtained in each step on the prediction horizon, an increased prediction quality is achieved when compared to employing iterated models. The proposed approach is illustrated in a simulation study, where we show the quality gain in the open-loop state predictions, as well as in the closed-loop performance.

## I. INTRODUCTION

Safety-critical constraints or performance requirements need to be robustly satisfied in many control and automation systems. For instance, robots must not collide with other objects in their environment or substance concentrations in (bio)chemical reactors should remain constant for product quality reasons, despite possible disturbances or uncertainties. Model predictive control (MPC), an advanced control scheme that is widely used nowadays, enables to deal with these challenging tasks [1]. Based on the repeated solution of a constrained finite horizon optimal control problem (OCP), the system of interest can be controlled to behave optimal w.r.t. a specified performance criterion. Rigorous guarantees on (robust) constraint satisfaction and stability, which allow to formulate safety conditions, can be achieved via specific, especially robust, problem formulations [2], [3].

The core element of a model predictive controller is a mathematical prediction model of the system. Initialized with the most recent available state information, it is used to predict the system's future behavior given a sequence of control inputs. This prediction is the basis on which the performance criterion is optimized to find the optimal control input sequence.

In practice, prediction models are traditionally derived using first principles. However, obtaining accurate models is often difficult and sometimes even impossible. If nonaccurate prediction models are employed, one remedy is to apply robust MPC schemes [4], [5], [6], which, however, require a-priori knowledge about the uncertainty and usually suffer from higher computational complexity and conservatism. If it is impossible (or too expensive) to obtain a prediction model with first principles, an alternative is to employ data-driven approaches. In particular, methods from machine learning are increasingly investigated and used to generate prediction models for MPC [7]. In this paper, we will focus on one particular approach, namely Gaussian process (GP) regression, to learn probabilistic prediction models of dynamical systems from data [8], [9]. Gaussian processes are able to learn a wide variety of different systems and naturally provide an uncertainty measure to evaluate the prediction quality, which can then be integrated in robust MPC schemes to provide probabilistic guarantees [10], [11].

The combination of Gaussian processes and model predictive control has been investigated extensively, see, e.g., [12], [13], [14], [15], [16]. In most works, the GP prediction models are trained to generate one-step ahead predictions and are then evaluated iteratively along the prediction horizon. This causes one major problem in GP-based MPC: a distribution (the GP output) is propagated several times through a nonlinear system (the GP), which results in non-Gaussian distributions [17], [18]. One consequence is that one cannot anymore trust the provided GP uncertainty measures and there exist several approaches to deal with this situation. The simplest approach is to propagate only the GP mean. However, this disregards the accumulation of prediction uncertainty along the horizon and can thus result in a low prediction quality [10]. More advanced approaches try to approximate the output distribution by a Gaussian, thereby increasing the computational complexity significantly [10], despite lacking information on the approximation quality. It is also possible to directly approximate the output distribution from samples, i.e., by using Monte-Carlo methods [17]. Another approach corrects the output distribution's variance by explicitly taking correlations between the iterated GP model evaluations into account [19].

Besides the previous approaches that focus on the approximation of the output distribution, other methods compute probabilistic error bounds of the GP model [20], [11], [21], [22], [23]. Such bounds enable the formulation of accurate confidence intervals that hold with high probability, so that robust and stochastic MPC schemes with high probability guarantees can be applied, e.g., [14], [16], [24], [25], [26]. Since the computation of such error bounds usually requires knowledge about the unknown function, which is not always available a-priori, one might use sampling-based techniques to acquire the lacking information, which is an essential drawback.

In this work, we present an alternative approach that computes exact multiple-step predictive distributions with GP-based models. The approach does not require to be evaluated iteratively but directly yields the entire state sequence from a single evaluation. In consequence, the predictive state distributions obtained from such models are exactly Gaussian, which is why the proposed approach does not require to compute approximate output distributions nor prediction error bounds. Thus, the approach allows to directly obtain accurate mean predictions and uncertainty information, which allow to apply standard stochastic MPC schemes. The main contributions of this work are

1) to establish an approach to derive direct GP-based models that do not require to be evaluated iteratively along the prediction horizon,
2) a comparative discussion of such direct GP-based models and conventional iterated $N$-step GP-based models, and
3) a comparative simulation study of employing direct and iterated GP-based models of nonlinear systems in MPC.

We do not focus on the issues of repeated feasibility and stability but rather outline the advantages and challenges of multiple-step GP predictions.

The remainder of this paper is structured as follows. We introduce Gaussian process regression and its application to dynamical systems in Section II. In Section III, we shortly introduce model predictive control. In Section IV, we outline the derivation of iterated and direct Gaussian process-based prediction models. The simulation results of applying both modeling approaches in MPC are presented in Section V. In Section VI, we draw conclusions.

## II. GAUSSIAN PROCESS REGRESSION

We outline the basics of Gaussian process regression, followed by a brief overview of hyperparameter optimization, and finish by showing how Gaussian processes can be applied to learn state space models of dynamical systems.

### A. Basics of Gaussian Process Regression

A Gaussian process $g(\xi) \sim \mathcal{GP}(m(\xi), k(\xi, \xi'))$ models an uncertain function $f : \mathbb{R}^d \to \mathbb{R}, \; \xi \mapsto f(\xi)$ by defining a Gaussian probability distribution over a function space. Formally, it is defined as *a collection of random variables, any finite subset of which has a joint Gaussian distribution* [8]. This means, loosely speaking, that it is an infinite-dimensional, multivariate Gaussian distribution of the function values $f(\xi)$ at location $\xi$ with any sample drawn from it being a possible realization of $f$. The mean function $m : \mathbb{R}^d \to \mathbb{R}, \; \xi \mapsto \mathbb{E}[g(\xi)]$ and the covariance function $k : \mathbb{R}^d \times \mathbb{R}^d \to \mathbb{R}, \; (\xi, \xi') \mapsto \mathrm{Cov}[g(\xi), g(\xi')]$ are design parameters of the model and fully specify the GP [8].

The objective is to learn the underlying function $f$ in terms of computing a predictive (or posterior) distribution for so-far unobserved function values (test targets) $f_* = f(\Xi_*)$, where $\Xi_* \in \mathbb{R}^{n_* \times d}$, $\Xi_* = \begin{bmatrix} \xi_*^{(1)} & \dots & \xi_*^{(n_*)} \end{bmatrix}^T$.$^1$ This distribution can be inferred from a set of noisy training observations (training targets) $\gamma = f(\Xi) + \varepsilon$, where $\Xi \in \mathbb{R}^{n \times d}$, $\Xi = \begin{bmatrix} \xi^{(1)} & \dots & \xi^{(n)} \end{bmatrix}^T$ and $\varepsilon \sim \mathcal{N}(0, \tilde{\sigma}_n^2 I)$, with $0$ denoting the zero vector and $I$ the identity matrix, models independent and identically distributed (i.i.d.) Gaussian noise with variance $\tilde{\sigma}_n^2$.

By definition, the GP must specify the joint Gaussian distribution of training and test targets, which is the so-called joint prior distribution [8]. To derive the predictive distribution, the prior distribution has to be restricted to contain only those functions that are consistent with the training data $\{\Xi, \gamma\}$. This is achieved by conditioning the prior distribution on the training data, yielding the posterior distribution $f_* \mid \Xi, \gamma, \Xi_* \sim \mathcal{N}(m^+(\Xi_*), k^+(\Xi_*))$ with

$$m^+(\Xi_*) = m(\Xi_*) + k(\Xi_*, \Xi) k_\gamma^{-1} (\gamma - m(\Xi)) \quad (1a)$$

$$k^+(\Xi_*) = k(\Xi_*, \Xi_*) - k(\Xi_*, \Xi) k_\gamma^{-1} k(\Xi, \Xi_*) , \quad (1b)$$

where $k_\gamma = k(\Xi, \Xi) + \tilde{\sigma}_n^2 I$. The posterior mean function (1a) is an estimator for the unknown function $f$. The posterior variances (the diagonal elements of the posterior covariance matrix (1b)) quantify the uncertainty of approximating $f$ by (1a) [8].

### B. Hyperparameter Adaptation

The predictive equations (1a) and (1b) depend on the mean function $m(\cdot)$ and the covariance function $k(\cdot, \cdot)$ of the GP prior. These functions depend themselves on a set of free parameters $\theta$, the so-called hyperparameters. Hence, a meaningful predictive distribution required suitable hyperparameters.

One way to obtain (locally) optimal hyperparameters is to maximize the GP's capability of explaining the training data, which is formally expressed by the logarithmic likelihood [8]

$$\log(p(\gamma \mid \Xi, \theta)) = -\frac{1}{2}\gamma_0^T k_\gamma^{-1} \gamma_0 - \frac{1}{2}\log|k_\gamma| - \frac{n}{2}\log(2\pi) ,$$

where $p(\cdot)$ denotes a probability density function, $|\cdot|$ denotes the determinant and $\gamma_0 = \gamma - m(\Xi)$. Then, the optimal hyperparameters are determined by

$$\theta^* = \arg\max_\theta \{\log(p(\gamma \mid \Xi, \theta))\} . \quad (2)$$

### C. Learning of Gaussian Process State Space Models

We consider the time-invariant time-discrete dynamical system$^2$

$$x_{k+1} = f(x_k, u_k) \quad (3a)$$

$$y_k = h(x_k, u_k) , \quad (3b)$$

with state $x \in \mathbb{R}^{n_x}$, control input $u \in \mathbb{R}^{n_u}$, output $y \in \mathbb{R}^{n_y}$, and functions $f : \mathbb{R}^{n_x} \times \mathbb{R}^{n_u} \to \mathbb{R}^{n_x}$ and $h : \mathbb{R}^{n_x} \times \mathbb{R}^{n_u} \to \mathbb{R}^{n_y}$, where $k \in \mathbb{N}_0$ denotes the discrete time variable. We assume access to full state measurements, i.e., $y_k = x_k + \varepsilon$, where $\varepsilon \sim \mathcal{N}(0, \sigma_n^2 I)$ models i.i.d. Gaussian noise.

For employing Gaussian process regression to vector-valued functions such as $f$, their component functions have to be modeled individually by independent GPs. By slight reformulation of (3a), the complete GP model of system (3), under the assumption of full state measurements, reads

$$\hat{x}_{k+1} = \hat{f}(x_k, u_k) = x_k + \tilde{f}(\xi_k) , \quad \text{where} \quad (4a)$$

$$\forall j \in \mathcal{I}_{1:n_x} : \tilde{f}_j(\xi_k) \sim \mathcal{GP}(m_j^+(\xi_k), k_j^+(\xi_k)) \quad (4b)$$

$$y_k = x_k + \varepsilon, \quad \varepsilon \sim \mathcal{N}(0, \sigma_n^2 I) , \quad (4c)$$

where the GPs' input $\xi_k := \begin{bmatrix} x_k^T & u_k^T \end{bmatrix}^T$ is the concatenation of the state and input at time $k$ and $\hat{\cdot}$ denotes an estimate (prediction). Note that in the way (4a) is formulated, the GPs are trained on the state differences $\Delta \hat{x}_{k+1} = \hat{x}_{k+1} - x_k$ and not on the states $\hat{x}_{k+1}$ directly. This formulation allows to efficiently exploit zero-mean priors and the fact that the state differences vary usually less than the states [27], [28].

---
$^1$With a slight abuse of notation, we overload functions $f$, $m$ and $k$ and mean by $f(\Xi)$ and $m(\Xi)$ column vectors with $[f(\Xi)]_i = f(\xi^{(i)})$ and $[m(\Xi)]_i = m(\xi^{(i)})$ and by $k(\Xi, \Xi)$ a matrix with $[k(\Xi, \Xi)]_{ij} = k(\xi^{(i)}, \xi^{(j)})$, where $\xi^{(i)}, \xi^{(j)}$ are the $i$-th and $j$-th row of $\Xi$.  
$^2$This can be also a sampled-data version of a time-continuous system with sampling period $T_s > 0$ and sampling times $t_k = k T_s$.

## III. MODEL PREDICTIVE CONTROL

In this section, we first outline the control problem considered in this paper, followed by an overview of the basic MPC algorithm, and finish by showing the specific adaptions required for employing stochastic GP models in MPC.

### A. Problem Formulation

We consider a time-discrete system of the form (3) with full state measurements, i.e., $y_k = x_k + \varepsilon$, where $\varepsilon \sim \mathcal{N}(0, \sigma_n^2 I)$ models i.i.d. Gaussian measurement noise.

The considered control objective is optimal set-point change from $(x_0, u_0)$ to $(x_{\text{ref}}, u_{\text{ref}})$, while satisfying input and state constraints and stabilizing the target point. Given these requirements, we employ model predictive control that requires a prediction model

$$\hat{x}_{k+1} = \hat{f}(x_k, u_k) , \quad \hat{y}_k = x_k + \varepsilon \quad (5)$$

of the system (3). We outline two different approaches of deriving and employing Gaussian process state space models of the form (4) as prediction models in MPC.

### B. Basic MPC Formulation and Algorithm

Given a prediction model (5), we consider at any time step $k$ the constrained finite-horizon OCP

$$\begin{aligned}
\min_{\hat{\mathbf{u}}_k} \quad & \left\{ V_N = \sum_{i=0}^{N-1} \ell \left( \hat{x}_{i|k}, \hat{u}_{i|k} \right) + V_f \left( \hat{x}_{N|k} \right) \right\} \quad &(6a) \\
\text{s.\,t.} \quad & \forall i \in \mathcal{I}_{0:N-1} : \hat{x}_{i+1|k} = \hat{f}(\hat{x}_{i|k}, \hat{u}_{i|k}) \quad &(6b) \\
& \hat{x}_{0|k} = x_k \quad &(6c) \\
& \forall i \in \mathcal{I}_{0:N-1} : \hat{u}_{i|k} \in \mathcal{U}_{i|k} , \quad &(6d)
\end{aligned}$$

where $N < \infty$ is the prediction horizon, $\hat{\cdot}_{i|k}$ denotes the $i$-step ahead prediction, and $\mathcal{I}_{a:b} := \{z \in \mathbb{N}_0 \mid a \le z \le b\}$. The optimization is performed over the control input sequence $\hat{\mathbf{u}}_k = \begin{bmatrix} \hat{u}_{0|k} & \dots & \hat{u}_{N-1|k} \end{bmatrix}$ [2], [3].

The cost function $V_N$ in (6a) consists of a stage cost $\ell(\cdot, \cdot)$ and a terminal cost $V_f(\cdot)$. Since the system state is constrained to follow the dynamics (6b), initialized at the current state (6c), $V_N = V_N(x_k, \hat{\mathbf{u}}_k)$ is a function of the initial condition $x_k$ and the input sequence $\hat{\mathbf{u}}_k = \begin{bmatrix} \hat{u}_{0|k} & \dots & \hat{u}_{N-1|k} \end{bmatrix}$ [2], [3].

In this work, we use a quadratic stage cost extended by a barrier term to account for soft state constraints,

$$\begin{aligned}
\ell(\hat{x}_{i|k}, \hat{u}_{i|k}) &= \|\hat{x}_{i|k} - x_{i|k}^{\text{ref}}\|_Q^2 + \|\hat{u}_{i|k} - u_{i|k}^{\text{ref}}\|_R^2 \\
&\quad + \|\hat{u}_{i-1|k} - \hat{u}_{i|k}\|_S^2 + \lambda \left(1 - \exp\left(-d(\hat{x}_{i|k}, \mathcal{X}_{i|k})\right)\right) , \quad (7)
\end{aligned}$$

where $Q \in \mathbb{R}^{n_x \times n_x}, Q \succeq 0$, $R \in \mathbb{R}^{n_u \times n_u}, R \succeq 0$, $S \in \mathbb{R}^{n_u \times n_u}, S \succeq 0$, $\hat{u}_{-1|k} = u_{k-1}$, $\lambda > 0$ and $d(\hat{x}_{i|k}, \mathcal{X}_{i|k}) := \inf_{w \in \mathcal{X}_{i|k}} \|\hat{x}_{i|k} - w\|^2$ is the distance of $\hat{x}_{i|k}$ to the safe set $\mathcal{X}_{i|k} = \{x \in \mathbb{R}^{n_x} \mid H_{i|k}^x x \le b_{i|k}^x\}$. We employ a terminal cost function

$$V_f(\hat{x}_{N|k}) = \|\hat{x}_{N|k} - x_{N|k}^{\text{ref}}\|_P^2 , \quad (8)$$

where $P \in \mathbb{R}^{n_x \times n_x}, P \succeq 0$ is computed from the solution of the linear-quadratic regulator (LQR) applied to the linearization of the model around the reference point [16], [29], [30]. Furthermore, we impose the polytopic input constraints $\mathcal{U}_{i|k} = \{u \in \mathbb{R}^{n_u} \mid H_{i|k}^u u \le b_{i|k}^u\}$ in (6d).

In MPC, the solution $\hat{\mathbf{u}}_k^*$ of (6) is now repeatedly computed at each time point $k$. The first element of $\hat{\mathbf{u}}_k^*$ is then implemented as the control input in the next sampling period.

### C. Gaussian Process-based MPC

If the prediction model (5) is derived by employing Gaussian process regression, its evaluations yield probability distributions. Thus, the OCP can be adapted to take the stochastic nature of the state predictions into account. By employing standard stochastic formulations, the stochastic MPC optimization problem derived from (6) reads

$$\begin{aligned}
\min_{\hat{\mathbf{u}}_k} \quad & \left\{ \mathbb{E} \left[ \sum_{i=0}^{N-1} \ell \left( \hat{x}_{i|k}, \hat{u}_{i|k} \right) + V_f \left( \hat{x}_{N|k} \right) \right] \right\} \quad &(9a) \\
\text{s.\,t.} \quad & \forall i \in \mathcal{I}_{0:N-1} : \hat{x}_{i+1|k} = \hat{f}(\hat{x}_{i|k}, \hat{u}_{i|k}) \quad &(9b) \\
& \hat{x}_{0|k} = x_k \quad &(9c) \\
& \forall i \in \mathcal{I}_{0:N-1} : \hat{u}_{i|k} \in \mathcal{U}_{i|k} , \quad &(9d)
\end{aligned}$$

where the expected cost accounts for the stochasticity involved in the state predictions [10], [28].

In addition, deterministic state constraints cannot be guaranteed to hold at all times. To this end, the soft state constraints $\hat{x}_{i|k} \in \mathcal{X}_{i|k} = \{x \in \mathbb{R}^{n_x} \mid x_{i|k}^{\min} \le x \le x_{i|k}^{\max}\}$, as imposed in (7), need to be reformulated as chance constraints, yielding $\mathrm{Pr}(\hat{x}_{i|k} \in \mathcal{X}_{i|k}) \ge p$, where $p \in (0, 1)$ is the prescribed minimum probability of constraint satisfaction. To again derive meaningful expressions therefrom, we can equivalently formulate the chance constraints in terms of deterministic confidence intervals,

$$\mu_{i|k}^{\hat{x}} \in \mathcal{M}_{i|k} := \left\{ z \ \middle|\ H_{i|k}^x z \le b_{i|k}^x - H_{i|k}^x Q_{i|k}^{\hat{x}} \left( 1 - \frac{1-p}{n_H} \right) \sqrt{\mathrm{diag} \left( \Sigma_{i|k}^{\hat{x}} \right)} \right\} , \quad (10)$$

where $\mu_{i|k}^{\hat{x}}$ and $\Sigma_{i|k}^{\hat{x}}$ denote the state distribution's mean and covariance matrix, $Q_{i|k}^{\hat{x}}(\cdot)$ is its quantile function, $\sqrt{\mathrm{diag}(\Sigma_{i|k}^{\hat{x}})}$ is the vector of the marginal state distributions' standard deviations and $n_H$ is the number of individual constraints [10]. Therewith, and given the specific structure of (7) and (8), the expected cost can be derived as

$$\mathbb{E}[V_N] = \sum_{i=0}^{N-1} \left( \ell(\mu_{i|k}^{\hat{x}}, \hat{u}_{i|k}) + \mathrm{tr}(Q \Sigma_{i|k}) \right) + V_f(\mu_{N|k}^{\hat{x}}) + \mathrm{tr}(P \Sigma_{N|k}) , \quad (11)$$

where $\mathrm{tr}(\cdot)$ denotes the trace [10], [28].

## IV. ITERATED AND DIRECT $N$-STEP GAUSSIAN PROCESS MODELS FOR MPC

GP models employed in MPC can be designed in two different ways, namely to predict the system evolution iteratively or directly [17]. We start this section by outlining both modeling approaches and finish by a comparative discussion.

### A. Iterated $N$-step GP Models

When employing an iterated $N$-step GP model (4) in MPC for predicting the state sequence $\hat{\mathbf{x}}_k = \begin{bmatrix} \hat{x}_{0|k} & \dots & \hat{x}_{N|k} \end{bmatrix}$, the model has to be recursively evaluated $N$ times, starting from the deterministic initial condition $\hat{x}_{0|k} = x_k$. The computation of the state prediction $\hat{x}_{i+1|k} = \hat{x}_{i|k} + \Delta \hat{x}_{i+1|k}$, $i \in \mathcal{I}_{0:N-1}$ thus involves the evaluation of the GPs at $\xi_{i|k} = \begin{bmatrix} \hat{x}_{i|k}^T & \hat{u}_{i|k}^T \end{bmatrix}^T$ to obtain the one-step state difference $\Delta \hat{x}_{i+1|k}$. As for $i \ge 1$, $\hat{x}_{i|k}$ is a random variable, so is $\xi_{i|k}$ and the GP has to be evaluated at a stochastic input. The exact predictive distribution of $\hat{x}_{i+1|k}$, $i \in \mathcal{I}_{1:N-1}$ is then obtained by marginalizing over the input distribution,

$$p(\hat{x}_{i+1|k}) = p(\hat{x}_{i|k}) + \int p(\Delta \hat{x}_{i+1|k} \mid \xi_{i|k}) p(\xi_{i|k})\, d\xi_{i|k} , \quad (12)$$

where $p(\Delta \hat{x}_{i+1|k} \mid \xi_{i|k})$ is the GP posterior distribution with mean and variance according to (1a) and (1b) and $p(\xi_{i|k})$ is the input distribution [27], [18]. In general, the integral in (12) is analytically intractable because the input distribution is mapped through a nonlinear GP model$^3$. The predictive distribution $p(\hat{x}_{i+1|k})$ is thus usually approximated again by a Gaussian distribution [10], [27].

---
$^3$The GP model is linear only if the linear kernel (cf. [8]) is employed. In this case, the predictive distribution can be computed analytically.

### B. Direct $N$-step GP Models

As an alternative to iterated $N$-step GP models, we propose to use *direct* $N$-step GP models to predict the state sequence $\hat{\mathbf{x}}_k = \begin{bmatrix} \hat{x}_{0|k} & \dots & \hat{x}_{N|k} \end{bmatrix}$ in a noniterative manner. To this end, we employ for each time step $i \in \mathcal{I}_{1:N}$ on the horizon an independent GP model with inputs $\xi_{i|k} = \begin{bmatrix} x_k^T & \hat{u}_{0:i-1|k}^T \end{bmatrix}^T$,

$$\begin{aligned}
\hat{x}_{i|k} &= \hat{f}(x_{i-1|k}, u_{i-1|k}) \\
&= \hat{f}(\hat{f}(x_{i-2|k}, u_{i-2|k}), u_{i-1|k}) \\
&\ \ \vdots \\
&= x_k + \tilde{f}^{(i)}(x_k, \hat{\mathbf{u}}_{0:i-1|k}) \quad &(13a) \\
\tilde{f}_j^{(i)}(x_k, \hat{\mathbf{u}}_{0:i-1|k}) &\sim \mathcal{GP}(m_{i,j}^+(\xi_{i|k}), k_{i,j}^+(\xi_{i|k})) , \quad &(13b)
\end{aligned}$$

that maps from the initial condition $\hat{x}_{0|k} = x_k$ and the input subsequence $\hat{\mathbf{u}}_{0:i-1|k} = \begin{bmatrix} \hat{u}_{0|k} & \dots & \hat{u}_{i-1|k} \end{bmatrix}$ to the $i$-step ahead state $\hat{x}_{i|k} = x_k + \Delta \hat{x}_{i|k}$. Again, each component $j \in \mathcal{I}_{1:n_x}$ of $\tilde{f}^{(i)}$ is modeled by an independent GP.

By this model design, each state prediction is represented by an exact Gaussian distribution $\hat{x}_{i|k} \sim \mathcal{N}(x_k + \mu_{i|k}^\Delta, \Sigma_{i|k}^\Delta)$, where

$$\mu_{i|k}^\Delta = \begin{bmatrix} m_{i,1}^+(\xi_{i|k}) \\ \vdots \\ m_{i,n_x}^+(\xi_{i|k}) \end{bmatrix}, \quad \Sigma_{i|k}^\Delta = \begin{bmatrix} k_{i,1}^+(\xi_{i|k}) & \cdots & 0 \\ \vdots & \ddots & \vdots \\ 0 & \cdots & k_{i,n_x}^+(\xi_{i|k}) \end{bmatrix} .$$

### C. Comparison of Iterated and Direct GP Models in MPC

Gaussian process-based MPC approaches, as presented in the literature, usually focus on the employment of iterated $N$-step GP models, e.g., [12], [13], [14], [15], [16], [10], [22]. This trend is motivated by the easier and more straightforward design of iterated models: only one model of the form (4) is required to represent a dynamical system completely. Furthermore, iterated models can be applied flexibly for different set-ups because they are independent of any horizon. In contrast, the design of direct models requires to derive several independent GP-based component models (13), namely one for each time step on the horizon. Clearly, this increases the computational burden associated with the computation of direct models: on the one hand, a larger number of GPs has to be trained, which is also accompanied by an increased effort for data preprocessing. On the other hand, the computational cost for evaluating the GP component models increases along the horizon as their inputs contain increasingly longer control input subsequences. Furthermore, if the system is nonlinear, the complexity of the mappings that are learned by the GPs also increases along the horizon as they are iterates of the system's nonlinear dynamics function [17], [18]. Thus, with proceeding horizon, the GPs require increasingly more data points or better informed prior models to achieve an appropriate prediction quality. This restricts the application of direct models to systems with moderate nonlinearities and to short or intermediate prediction horizons.

However, the main advantage of direct $N$-step models is that they evaluate for each time step on the horizon to an exact Gaussian distribution. In contrast, the output distributions of iterated $N$-step models are in general non-Gaussian and analytically intractable and have therefore to be approximated. These approximations, in turn, tend to fail in certain situations [22] and significantly increase the computational complexity [10]. In addition, the recursive propagation of prediction errors by iterated $N$-step models might significantly deteriorate their multiple-step prediction quality. To avoid this effect, iterated $N$-step models require usually more training data points than direct $N$-step models to achieve a similar $N$-step prediction performance [18], which as well increases their computational complexity. In consequence, we expect direct $N$-step models to provide more accurate uncertainty information that can be efficiently exploited by a controller. Furthermore, for validating direct $N$-step models, it suffices to employ standard cross-validation techniques (cf. [8]) to each component model to assess the overall model quality while it is essential to also consider multiple-step predictions when validating iterated $N$-step models [31].

## V. SIMULATIVE COMPARISON

In this section we compare iterated and direct $N$-step prediction models in simulations. To this end, we consider the second-order nonlinear two-tank system

$$\begin{bmatrix} \dot{x}_1 \\ \dot{x}_2 \end{bmatrix} = \begin{bmatrix} \frac{1}{A_1} (u - \sqrt{2gx_1}A_{\text{out},1}) \\ \frac{1}{A_2} (\sqrt{2gx_1}A_{\text{out},1} - \sqrt{2gx_2}A_{\text{out},2}) \end{bmatrix} \quad (14a)$$

$$y = x + \varepsilon, \quad \varepsilon \sim \mathcal{N}(0, \sigma_n^2 I), \quad \sigma_n = 0.008 \text{ m} \quad (14b)$$

with tank cross section areas $A_1 = \pi r_1^2$ and $A_2 = \pi r_2^2$ for radii $r_1 = 1.5\text{ m}$ and $r_2 = 0.9\text{ m}$, outlet cross section areas $A_{\text{out},1} = \pi r_{\text{out},1}^2$ and $A_{\text{out},2} = \pi r_{\text{out},2}^2$ for radii $r_{\text{out},1} = 0.034\text{ m}$ and $r_{\text{out},2} = 0.040\text{ m}$ and where $g = 35\,316\text{ m min}^{-2}$ is the gravitational acceleration. The state vector $x$ represents the filling heights of the tanks and the control input $u$ is the inflow in tank 1.

We first outline the generation of training data sets, based on which we afterwards derive an iterated and a direct GP-based model of (14). Thereafter, we briefly explain how the iterated multiple-step state distributions are approximated, followed by the design of the MPC problem. We finish this section by comparing the open-loop prediction quality along the controller's horizon, as well as the closed-loop performance for both the iterated and the direct model.

### A. Training Data Generation

To generate training data, we simulate a run of (14), initialized at the origin, for a specific training input trajectory. We design this input trajectory to be piecewise constant with 200 values drawn from a uniform distribution over the interval $[0, 7]$, where each value is held for 5 sampling periods $T_s = 1\text{ min}$. To achieve a better data coverage of the system's operating region, we modify the designed input trajectory and set 60 % of its values (randomly selected) to zero. During simulation, we shut off the input for the next sampling period when the filling heights reached a critical level to prevent the tanks from overflowing. From the resulting sampled data, denoted by $y_k = y(t_k)$ and $u_k = u(t_k)$ for $t_k = k T_s, \; k = 0, \dots, n$, we derive the GP training data sets

$$\begin{aligned}
\forall i \in \mathcal{I}_{1:N}: \forall j \in \mathcal{I}_{1:n_x}: \mathcal{D}_j^{(i)} &= \left\{ (\xi_{i|k}, \gamma_{i|k}^j) \ \middle|\ \gamma_{i|k}^j = y_{k+i}^j - y_k^j, \right. \\
&\quad \left. \xi_{i|k} = \begin{bmatrix} y_k & u_k & \dots & u_{k+i-1} \end{bmatrix}, \ k = 0, \dots, n-i \right\} , \quad (15)
\end{aligned}$$

where $y_k^j$ is the $j$-th dimension of $y_k$.

Afterwards, we reduce the data sets (15) by removing data points $(\xi_{i|k}, \gamma_{i|k}^j)$ that provide no new information given the remaining data points. To this end, we exclude all data points $q > p$ with $\|\xi_{i|p} - \xi_{i|q}\|^2 \le \tau_j^{(i)}$ for a given data point $p$ and a threshold $\tau_j^{(i)}$ from the data set $\mathcal{D}_j^{(i)}$, yielding the reduced set $\tilde{\mathcal{D}}_j^{(i)}$.$^4$ This reduction of the training data sets is done to decrease the computational burden of the associated GPs, as well as for preventing numerical ill-conditioning of the training covariance matrix.

---
$^4$The distance thresholds have been selected such that cross-validating the models on the data not used for training yields low, unbiased prediction errors and accurate confidence intervals. In this work, we use $\forall j \in \mathcal{I}_{1:n_x}: \tau_j^{(1)} = 0.9$ and $\forall j \in \mathcal{I}_{1:n_x} : \tau_j^{(i)} = 0.9 \bar{d}_j^{(i)} / \bar{d}_j^{(1)}$ for $i > 1$, where $\bar{d}_j^{(i)}$ is the average distance between the inputs in $\mathcal{D}_j^{(i)}$.

### B. Derivation of an Iterated and a Direct Model

We define the GP prior models with the zero-mean function $m_{i,j}(\xi_{i|k}) = 0$ and the squared exponential kernel

$$k_{i,j}(\xi_{i|k}, \xi'_{i|k}) = \sigma_{f,i,j}^2 \exp\left(-\frac{1}{2}(\xi_{i|k} - \xi'_{i|k})^T \Lambda_{i,j}^{-1}(\xi_{i|k} - \xi'_{i|k})\right) ,$$

where $\Lambda_{i,j} = \mathrm{diag}(\ell_{1,i,j}^2, \dots, \ell_{d,i,j}^2)$ is the diagonal matrix of squared length scale hyperparameters and $\sigma_{f,i,j}^2$ is the signal variance hyperparameter. Given the reduced training data sets, we associate the $j$-th GP at stage $i$ (cf. (13)) with the data set $\tilde{\mathcal{D}}_j^{(i)}$ and derive the GP posterior models involved in (13) according to (1). Therein, we have that $\tilde{\sigma}_n^2 = 2\sigma_n^2$ because the training targets $\gamma_{i|k} \sim \mathcal{N}(\Delta x_{i|k}, 2\sigma_n^2 I)$ are noisy versions of the actually desired values $\Delta x_{i|k}$. Based on the reduced training data set, we furthermore compute the optimal covariance hyperparameters for each GP according to (2). The iterated model is, in accordance with (4), given by the first component ($i = 1$) of the direct model.

As discussed in Sec. IV-C, the computational load for training the direct model is higher than that for training the iterated model. This is because the derivation of the direct model involves to compute several GP-based component models with increasing input dimension along the horizon, which we set to $N = 10$. Furthermore, these component models require increasingly more training data points due to the increasing complexity of the learned mapping. While 21 training data points are sufficient for the one-step model to perform well in cross-validation, the ten-step model requires 393 training data points to yield comparable results. The iterated model is derived within 0.6 s, whereas training the direct model takes 11.7 s when all its components are computed sequentially. However, as the direct model's components are independent of each other, the training process can be parallelized, decreasing the computation time to 6.9 s.$^5$

---
$^5$The presented computation times are the average of three runs on a PC with 16 GB RAM and an Intel Core i7-6700 CPU.

### C. Multiple-Step Predictions Along the Horizon

While the direct model evaluates for each step on the horizon to an exact Gaussian distribution (Sec. IV-B), the iterated model evaluates to analytically intractable distributions for each but the first step (Sec. IV-A). We therefore apply an approximation to the iterated model and compute the state distribution $p(\hat{x}_{i+1|k}), \; i \in \mathcal{I}_{1:N-1}$ by only propagating the mean $\mu_{i|k}^{\hat{x}}$ of the state distribution $p(\hat{x}_{i|k})$ [10]. Then, the GP's output distribution is again Gaussian, $\Delta \hat{x}_{i+1|k} \sim \mathcal{N}(\mu_{i+1|k}^\Delta, \Sigma_{i+1|k}^\Delta)$, and thus $\hat{x}_{i+1|k} \sim \mathcal{N}(\mu_{i|k}^{\hat{x}} + \mu_{i+1|k}^\Delta, \Sigma_{i|k}^{\hat{x}} + \Sigma_{i+1|k}^\Delta)$. As this approximation assumes independence of the random variables $\hat{x}_{i|k}$ and $\hat{x}_{i+1|k}$, it tends to underestimate the prediction uncertainty [19]. However, we use this approximation scheme for two reasons of practicability. First, more advanced approaches that aim for approximating the GP's output distribution are computationally more involved and do anyhow not provide formal guarantees on the approximation quality. And secondly, mathematically rigorous, high-probability model error bounds, as provided by another class of approaches, are hard to compute when the underlying function is unknown.

### D. Control Task and MPC Design

The considered control task is steering system (14) from the initial set-point $(x_0, u_0) = (\begin{bmatrix} 0.96\text{ m} & 0.50\text{ m} \end{bmatrix}^T, 0.94\text{ m}^3\,\text{min}^{-1})$ to the target point $(x_{\text{ref}}, u_{\text{ref}}) = (\begin{bmatrix} 2.87\text{ m} & 1.50\text{ m} \end{bmatrix}^T, 1.64\text{ m}^3\,\text{min}^{-1})$, while satisfying input and state constraints. Given the iterated and the direct $N$-step GP-based model, we design a model predictive controller according to (9) and (11) with horizon $N = 10$, cost function parameters

$$Q = \begin{bmatrix} 0.1 & 0 \\ 0 & 2 \end{bmatrix}, \quad R = 0.1, \quad \lambda = 10^2, \quad \text{and} \quad S = 0 ,$$

box constraints on the control input according to (6d),

$$\forall i \in \mathcal{I}_{0:N-1} : H_{i|k}^u = \begin{bmatrix} -1 \\ 1 \end{bmatrix}, \quad b_{i|k}^u = \begin{bmatrix} 0 \\ 7 \end{bmatrix} ,$$

and probabilistic constraints on the state according to (10),

$$\forall i \in \mathcal{I}_{1:N-1} : H_{i|k}^x = \begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}, \quad b_{i|k}^x = \begin{bmatrix} 3 \\ 2 \end{bmatrix}, \quad p = 0.95 .$$

The terminal penalty matrix is model-dependent and computed as described in Sec. III-B$^6$.

---
$^6$The model is linearized numerically by evaluating the mean prediction at $(x_{\text{ref}}, u_{\text{ref}})$ and $(x_{\text{ref}} \pm \delta x, u_{\text{ref}} \pm \delta u)$ with $\delta x = \begin{bmatrix} 0.001 & 0.001 \end{bmatrix}^T$ and $\delta u = 0.001$. For the direct model, the computation is based on the $N$-th component model.

### E. Closed-Loop Comparison

We start by illustrating the effect of propagating a Gaussian probability distribution repeatedly through the nonlinear iterated $N$-step model of system (14). To this end, we sample from an initially Gaussian distribution $x \sim \mathcal{N}(x_0, 0.03 I)$ and propagate each sample $N - 1 = 9$ times through the iterated model to compute the non-Gaussian output distribution$^7$ (Fig. 1).

![](_page_5_Figure_0.jpeg)

*Fig. 1. State distribution after iterated nine-step propagation of the initial distribution $x \sim \mathcal{N}(x_0, 0.03 I)$ through the nonlinear one-step GP model. The distribution is represented by 2000 samples. The shaded areas show the 68.3 %, 95.4 % and 99.7 % confidence regions of the Gaussian approximations obtained using the sample mean and sample covariance.*

Next, we compare the quality of the iterated and the direct $N$-step state predictions along the control horizons. To this end, we use the open-loop input sequences $\hat{\mathbf{u}}_k^{\text{itGP}}$ and $\hat{\mathbf{u}}_k^{\text{dirGP}}$ determined by the controller based on the iterated and the direct model, respectively, and compute the state sequences $\hat{\mathbf{x}}_k^{\text{itGP}}$ and $\hat{\mathbf{x}}_k^{\text{dirGP}}$ for each horizon using the initial conditions $x_k^{\text{itGP}}$ and $x_k^{\text{dirGP}}$.$^8$ We compare the state sequences $\hat{\mathbf{x}}_k^{\text{itGP}}$ and $\hat{\mathbf{x}}_k^{\text{dirGP}}$ each with the nominal state sequence obtained from evaluating (14) for the same input sequence and initial condition and show the resulting mean prediction errors in Fig. 2. Furthermore, from the state distributions $\hat{x}_{i|k}^{\text{itGP}} \sim \mathcal{N}(\mu_{i|k}^{\text{itGP}}, \Sigma_{i|k}^{\text{itGP}})$ and $\hat{x}_{i|k}^{\text{dirGP}} \sim \mathcal{N}(\mu_{i|k}^{\text{dirGP}}, \Sigma_{i|k}^{\text{dirGP}})$, we compute the mean prediction error distributions $(\hat{x}_{i|k}^{\text{itGP}} - \mu_{i|k}^{\text{itGP}}) \sim \mathcal{N}(0, \Sigma_{i|k}^{\text{itGP}})$ and $(\hat{x}_{i|k}^{\text{dirGP}} - \mu_{i|k}^{\text{dirGP}}) \sim \mathcal{N}(0, \Sigma_{i|k}^{\text{dirGP}})$. Therefrom, we obtain for each horizon additionally the bounds of the 95.4 % confidence interval on the mean prediction error (Fig. 2). We observe that the direct model yields significantly more accurate predictions, i.e., significantly lower mean prediction errors, along the control horizons than the iterated model. Furthermore, the direct model yields additionally more accurate uncertainty information in terms of the confidence interval bounds than the iterated model: While the 95.4 % confidence interval bounds on the errors of the iterated predictions are violated in most of the cases, the ones on the errors of the direct predictions hold exactly. Additionally the uncertainty tubes obtained from the direct model are narrower than those obtained from the iterated model. It is worth noting that while the uncertainty tube of the iterated model has to expand along the horizon due to the accumulation of uncertainty, this is not the case for the uncertainty tube of the direct model as the prediction at stage $i$ is, by design, independent of all previous predictions.

![](_page_5_Figure_11.jpeg)

*Fig. 2. Open-loop predictions errors (blue lines) w.r.t. the true dynamics and corresponding 95.4 % confidence interval bounds (black lines) of the iterated (left column) and the direct (right column) $N$-step model for each control horizon computed during the closed-loop simulation.*

Finally, we present the closed-loop results when employing the iterated and the direct $N$-step GP-based prediction models in MPC (Fig. 3). For comparability, we also show the closed-loop results when employing the nominal model (14) as prediction model in the controller. It is observed that the closed-loop trajectories resulting from employing the direct $N$-step model in the controller almost coincide with nominal trajectories, while the trajectories obtained from employing the iterated $N$-step model show clear deviations to the nominal ones. Furthermore, we observe that the controller based on the iterated $N$-step model takes significantly longer to steer the system to the desired set-point. This effect is most prominent for $x_2$, although its deviations from the reference $x_2^{\text{ref}}$ are, according to the choice of $Q$ and $R$, the dominating component in the nominal cost function. Those results indicate that the controller with the direct $N$-step prediction model outperforms the one with the iterated $N$-step prediction model and are consistent with the presented results on the open-loop predictive capabilities of both GP-based models. To confirm our observations, we additionally compute the root mean square errors as well as the maximum absolute errors of the closed-loop inputs and states w.r.t. the nominal case for employing the iterated and direct $N$-step GP model in MPC, respectively (Tab. I).

![](_page_6_Figure_1.jpeg)

*Fig. 3. Comparison of the closed-loop performance of nominal MPC, iterated $N$-step GP-MPC and direct $N$-step GP-MPC.*

![](_page_6_Figure_0.jpeg)

*Fig. 4. Comparison of the OCP computation times of nominal, iterated $N$-step and direct $N$-step GP-MPC.*

However, we observe that using the direct model in the controller is associated with the highest computational load for solving the OCP (Fig. 4). Furthermore, the controller based on the direct model is, unlike the others, not real-time capable as the OCP-solution time exceeds the sampling time in some cases. The reasons have been discussed in Sec. IV-C. As shown, the controller based on the iterated $N$-step model performs worse than the one based on the direct model. With an increasing number of active training data points in the iterated $N$-step model, it is expected to improve its prediction capability and in consequence the closed-loop performance. However, its real-time capability will decrease with an increasing number of active training data points and will further be lost if this number exceeds a certain threshold.

---
$^7$To compute the GP's inputs as in (4), we use the first open-loop control sequence obtained from employing the iterated $N$-step model in MPC.  
$^8x_k^{\text{itGP}}$ and $x_k^{\text{dirGP}}$ denote the closed-loop states at time point $k$ when the controller based on the iterated and direct model is employed, respectively.

#### TABLE I
ROOT MEAN SQUARE ERRORS AND MAXIMUM ABSOLUTE ERRORS FOR THE CLOSED-LOOP CONTROL INPUTS ($\text{m}^3\,\text{min}^{-1}$) AND THE STATES ($\text{m}$) OF ITERATED AND DIRECT GP-MPC W.R.T. NOMINAL MPC.

| | RMSE | | | Max. Abs. Error | | |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| | $u$ | $x_1$ | $x_2$ | $u$ | $x_1$ | $x_2$ |
| Iterated GP-MPC | 0.205 | 0.151 | 0.065 | 0.549 | 0.299 | 0.110 |
| Direct GP-MPC | 0.017 | 0.009 | 0.003 | 0.040 | 0.016 | 0.005 |

## VI. CONCLUSIONS AND OUTLOOK

In this work, we presented an approach to derive Gaussian process (GP) models for model predictive control (MPC) that do not require to be evaluated iteratively but yield the entire state sequence from a single evaluation. In consequence, and in contrast to employing conventional iterative GP models, the presented approach yields for each time step on the horizon an exact Gaussian distribution. Therefore, accurate mean predictions and uncertainty information are directly obtained without the requirement for computing approximate distributions or prediction error bounds.

We showed the derivation of such direct GP models from system data and their application in MPC. Based on a simulation study, we illustrated the changes in the output distribution's shape along the prediction horizon when computing iterated multiple-step predictions with conventional GP models. Furthermore, we compared the quality of iterated and direct multiple-step predictions along the prediction horizon. Thereby, we also illustrated the increasing deterioration in the quality of naive iterated multiple-step predictions with increasing number of performed iterations. Finally, we showed the performance gain that can be achieved by employing direct models instead of iterative model in MPC.

Future steps will focus on deriving formal guarantees on the performance, stability and recursive feasibility of iterated and direct $N$-step GP models employed in MPC. This includes also a more detailed numerical analysis and comparison of the modeling approaches. Furthermore, future research will be dedicated towards efficient implementations of direct $N$-step GP models for achieving real-time applicability of hereon based controllers. Consecutively, the proposed approach will be tested in real-world experiments.

## REFERENCES

[1] M. Schwenzer, M. Ay, T. Bergs, and D. Abel, "Review on model predictive control: an engineering perspective," *The International Journal of Advanced Manufacturing Technology*, 2021.

[2] J. B. Rawlings, D. Q. Mayne, and M. M. Diehl, *Model Predictive Control: Theory, Computation, and Design*. Nob Hill Publishing, LLC, 2 ed., 2019.

[3] L. Grüne and J. Pannek, *Nonlinear Model Predictive Control*. Springer International Publishing, 2 ed., 2017.

[4] B. T. Lopez, J.-J. E. Slotine, and J. P. How, "Dynamic tube MPC for nonlinear systems," in *American Control Conference*, pp. 1655–1662, 2019.

[5] J. Köhler, E. Andina, R. Soloperto, M. A. Müller, and F. Allgöwer, "Linear robust adaptive model predictive control: Computational complexity and conservatism," in *IEEE 58th Conference on Decision and Control*, pp. 1383–1388, 2019.

[6] S. V. Raković, "Robust model predictive control," in *Encyclopedia of Systems and Control*, pp. 1–11, Springer London, 2019.

[7] B. Huang, B. Gopaluni, A. Tulsyan, B. Chachuat, J. Lee, F. Amjad, S. Damarla, J. Woo, and N. Lawrence, "Modern machine learning tools for monitoring and control of industrial processes: A survey," in *IFAC World Congress*, 2020.

[8] C. E. Rasmussen and C. K. I. Williams, *Gaussian Processes for Machine Learning*. The MIT Press, 2006.

[9] J. Kocijan, *Modelling and Control of Dynamic Systems Using Gaussian Process Models*. Springer International Publishing, 2016.

[10] L. Hewing, J. Kabzan, and M. M. Zeilinger, "Cautious model predictive control using Gaussian process regression," *IEEE Transactions on Control Systems Technology*, vol. 28, no. 6, pp. 2736–2743, 2019.

[11] A. Capone, A. Lederer, and S. Hirche, "Confidence regions for predictions of online learning-based control," in *21st IFAC World Congress*, pp. 1007–1012, 2020.

[12] J. Kocijan, R. Murray-Smith, C. E. Rasmussen, and B. Likar, "Predictive control with Gaussian process models," in *The IEEE Region 8 EUROCON. Computer as a Tool*, pp. 352–356, IEEE, 2003.

[13] X. Yang and J. M. Maciejowski, "Fault tolerant control using Gaussian processes and model predictive control," *International Journal of Applied Mathematics and Computer Science*, vol. 25, no. 1, pp. 133–148, 2015.

[14] J. Umlauft, T. Beckers, and S. Hirche, "Scenario-based optimal control for Gaussian process state space models," in *European Control Conference*, pp. 1386–1392, 2018.

[15] J. Matschek, A. Himmel, K. Sundmacher, and R. Findeisen, "Constrained Gaussian process learning for model predictive control," in *21st IFAC World Congress*, pp. 971–976, 2020.

[16] M. Maiworm, D. Limón, and R. Findeisen, "Online learning-based model predictive control with Gaussian process models and stability guarantees," *International Journal of Robust and Nonlinear Control*, pp. 1–28, 2021.

[17] J. Quiñonero-Candela, A. Girard, and C. E. Rasmussen, "Prediction at an uncertain input for Gaussian processes and relevance vector machines - application to multiple-step ahead time-series forecasting," tech. rep., Max Planck Institute for Biological Cybernetics, Tübingen, Germany, 2003.

[18] J. Quiñonero-Candela, A. Girard, J. Larsen, and C. E. Rasmussen, "Propagation of uncertainty in Bayesian kernel models - application to multiple-step ahead forecasting," in *IEEE International Conference on Acoustics, Speech and Signal Processing*, vol. 2, pp. II–701–II–704, 2003.

[19] L. Hewing, E. Arcari, L. P. Fröhlich, and M. N. Zeilinger, "On simulation and trajectory prediction with Gaussian process dynamics," *Proceedings of Machine Learning Research*, vol. 120, pp. 424–434, 2020.

[20] A. Lederer, J. Umlauft, and S. Hirche, "Uniform error bounds for Gaussian process regression with application to safe control," in *33rd Conference on Neural Information Processing Systems*, pp. 657–667, 2019.

[21] A. Lederer, M. Kessler, and S. Hirche, "GP3: A sampling-based analysis framework for Gaussian processes," in *21st IFAC World Congress*, pp. 983–988, 2020.

[22] K. Polymenakos, L. Laurenti, A. Patane, J.-P. Calliess, L. Cardelli, M. Kwiatkowska, A. Abate, and S. Roberts, "Safety guarantees for planning based on iterative Gaussian processes," in *IEEE 59th Conference on Decision and Control*, pp. 3187–3193, 2020.

[23] N. Srinivas, A. Krause, S. M. Kakade, and M. W. Seeger, "Information-theoretic regret bounds for Gaussian process optimization in the bandit setting," *IEEE Transactions on Information Theory*, vol. 6, no. 5, pp. 3250–3265, 2012.

[24] T. Koller, F. Berkenkamp, M. Turchetta, and A. Krause, "Learning-based model predictive control for safe exploration," in *IEEE 57th Conference on Decision and Control*, pp. 6059–6066, 2018.

[25] D. Limón, J.-P. Calliess, and J. M. Maciejowski, "Learning-based nonlinear model predictive control," *IFAC PapersOnLine*, vol. 50, no. 1, pp. 7769–7776, 2017.

[26] J. M. Manzano, D. Limón, D. M. de la Peña, and J. Calliess, "Robust data-based model predictive control for nonlinear constrained systems," *IFAC PapersOnLine*, vol. 51, no. 20, pp. 505–510, 2018.

[27] M. P. Deisenroth, *Efficient Reinforcement Learning Using Gaussian Processes*. PhD thesis, Intelligent Sensor-Actuator-Systems Laboratory, Karlsruhe Institute of Technology, Karlsruhe, Germany, 2010.

[28] G. Cao, E. M.-K. Lai, and F. Alam, "Gaussian process based model predictive control for linear time varying systems," in *IEEE 14th International Workshop on Advanced Motion Control*, pp. 251–256, 2016.

[29] M. Maiworm, D. Limón, J. M. Manzano, and R. Findeisen, "Stability of Gaussian process learning based output feedback model predictive control," in *6th IFAC Conference on Nonlinear Model Predictive Control*, pp. 551–557, 2018.

[30] B. Kouvaritakis and M. Cannon, *Model Predictive Control - Classical, Robust and Stochastic*. Springer International Publishing, 2016.

[31] J. Kocijan, A. Girard, B. Banko, and R. Murray-Smith, "Dynamic system identification with Gaussian processes," *Mathematical and Computer Modelling of Dynamical Systems*, vol. 11, no. 4, pp. 411–424, 2003.
