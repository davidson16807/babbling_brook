<!-- HUMAN WRITTEN -->

The "view" folder stores `*Program` classes.

A `*Program` is a proper object oriented class 
that seals off access to resources relating to an 
OpenGL shader program within an OpenGL Context, 
allowing view state to be managed statelessly elsewhere. 

It guarantees the following:
* all internal resources are created on initialization to minimize state transitions (RAII)
* all internal resources are strictly encapsulated
* the program can be in only one of two states: "created" and "disposed"
* the disposed state can be entered at any time but never exited
* all methods will continue to produce sensible, well defined behavior in the disposed state
* the output that draw() sends to the currently bound framebuffer is 
  a pure function of its input

Its internal state transitions can be described with the following diagram:

initialized
    ↓        release()
 released
    ↻        release()

Any attempt to relax guarantees made here will severely cripple 
your ability to reason with the code base. 

`*Program`s are the lowest level of abstraction in the graphics architecture used here.
As such they are extremely general purpose. `*Program`s should never introduce restrictive assumptions 
about the objects they render unless there is a strong performance reason.
Valid assumptions that can be introduced at this layer include:
* how the projection matrix is applied (e.g. whether it is a HUD, billboard, or regular 3d object)
* how the user will supply vertex data (e.g. winding order, backface culling, how they will specify color, whether they can control transparency, etc.)
* whether the `*Program` renders points, triangles, volumetrics, etc.
* whether the `*Program` renders facsimiles of the real world vs. abstract concepts such as arrows, points, etc.
* how a surface will be depicted stylistically (e.g. cell shader, photorealistic, etc.)

`*Program`s have two methods, `draw()` and `release()`.
`draw()` adds a depiction of a scalar field to the framebuffer that is currently 
bound to the program's context using options from a given view state.
The only state that is allowed to be modified is that of the framebuffer,
so the state of the framebuffer after invocation is a strict function 
of its current state and the arguments passed to `draw()`

# Terminology
When implementing `*Programs`, we use the same terminology that's standard for OpenGl.
We attempt definitions for them as follows:

* fragment   the smallest entity considered by a fragment shader
* vertex     the smallest entity considered by a geometry shader
* point      a vertex that is rendered in isolation
* line       a duple:  (vertex, vertex)
* triangle   a triple: (vertex, vertex, vertex)
* primitive  a point, line, triangle, or triangle strip
* element    a duple: (vertex, primitive), it is a specific usage of a vertex in a primitive
* instance   a collection of primitives that are intended for reuse
* uniform    aspects that do not vary over the course of a `draw()` call
* model      the uniform set of all graphics
* view       the uniform orientation of a camera
* projection the uniform aspects of perspective
* attribute  aspects that are not uniform, either across elements, vertices, or instances
* static     something that is not intended to change once per frame
* dynamic    something that is expected to change once per frame

We also introduce or coopt the following terms:

* graphic    either a primitive or an instance
* indicator  a graphic that is only meant to represent an abstract concept, such as an arrow or point
* cloud      a static set of graphics where primitives do not share vertices, it either features instances or does not distinguish vertices and elements
* swarm      a dynamic set of graphics where primitives do not share vertices, it either features instances or does not distinguish vertices and elements
* surface    a set of graphics where primitives share vertices and vice versa, it features an element buffer object

