# Git Commit Message Convention

This repository uses commit message prefixes to categorize code changes. The goal is to make the project history easier to read, maintain, search, and review.

## Format

Use the following format:

```text
[type] short description
```

Example:

```text
[feat] add transformer-based architecture
```

Keep the description concise and write it in the imperative style when possible.

## Types

### feat

A new feature for the model, such as a new architecture, experiment setup, or functionality.

```text
[feat] add transformer-based architecture
```

### fix

A bug fix or troubleshooting change, such as fixing a logic error or incorrect preprocessing behavior.

```text
[fix] fix data preprocessing bug
```

### refactor

A code change that neither fixes a bug nor adds a feature, such as restructuring code or routine hyperparameter tuning.

```text
[refactor] modify learning rate schedule
```

### style

Changes that do not affect code behavior, such as formatting, whitespace, import ordering, renaming, or readability-only edits.

```text
[style] reformat code for readability
```

### docs

Documentation-only changes.

```text
[docs] update model training instructions
```

### test

Adding or modifying tests, such as unit tests for model components or evaluation metrics.

```text
[test] add unit tests for model accuracy metrics
```

### chore

Changes to the build process, dependencies, auxiliary tools, generated files, or repository maintenance tasks.

```text
[chore] update Python dependencies
```

## Refactor vs Style

The difference between `refactor` and `style` can be confusing:

- `refactor`: Use this when changing the internal structure of the code without changing external behavior or functionality. The focus is improving organization, readability, performance, or maintainability while preserving the same outcome.
- `style`: Use this for changes that do not affect behavior at all, such as formatting, renaming variables, reordering imports, or fixing typos in comments.

## Examples

### Changed Directory Structure

Use `refactor`.

Changing the directory structure affects the organization of the codebase and may affect imports or execution paths, but it does not directly change functionality.

```text
[refactor] reorganize directory structure for better modularity
```

### Changed Argument or Variable Names

Use `style`.

Renaming arguments or variables usually improves readability or consistency without changing behavior.

```text
[style] rename variables for clarity and consistency
```

### Tuned Hyperparameters for Experiments

Use `refactor` or `feat`, depending on the context.

Use `refactor` when adjusting hyperparameters as part of routine experimentation or optimization without introducing a new capability.

```text
[refactor] adjust hyperparameters for improved model performance
```

Use `feat` when the change introduces a significant new model variation, experiment setup, or capability.

```text
[feat] tune hyperparameters for new experiment setup
```
