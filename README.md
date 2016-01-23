# ecsCompiler
Compiles from a DSL for ECS to JS.

This is currently hacked together for the game that I'm currently working on, and so is pretty ugly and hard-coded.

The structure of the entities and the components are defined in .ecs files and parameters for specific instances are defined in .csv files. A user can thus define new structures and associated parameters without writing any actual code

This compiles to javascript right now, but can be extended to compile to JSON instead fairly easily.

Examples are in the examples folder.
