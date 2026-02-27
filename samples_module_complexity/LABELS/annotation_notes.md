# Module complexity labels (cohesion & coupling)

This bundle contains small Python projects intended to demonstrate classic *module-level* cohesion/coupling categories.

## Cohesion categories (high-level)
- coincidental: unrelated responsibilities grouped together
- logical: operations grouped by a "kind/mode" selector
- temporal: operations grouped because they happen at the same time (startup/shutdown)
- procedural: operations grouped because they follow a sequence of steps
- communicational: operations grouped because they act on the same data set
- sequential: output of one part is the input to the next part
- functional: focused on a single well-defined task

## Coupling categories (high-level)
- content: one module reaches into another module's internal implementation details
- common: modules share global state
- control: a module influences another by passing flags/modes
- stamp: modules pass around composite structures and depend on their shape
- data: modules pass simple values and do not depend on internal representation
- message: modules communicate through interfaces/protocols rather than concrete modules

The JSON file `module_complexity_labels.json` records the intended primary label per project and per module.
