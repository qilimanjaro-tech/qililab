SEQUENCE DIAGRAMS GUIDE

Hello everyone, this is a quick guide on how to understand QiliLab Sequence Diagrams.

QUICK GUIDE:

Colours on rectangles mean depth of function calls. (White -> Purple -> Red -> Blue -> Purple -> Red -> Blue -> Purple ...)
Colours on notes mean different things:
	Yellowish: nothing special
	Purple: Method in another PNG
	Red: Abstract Method
	Blue: Recursive Method
Frames:
	loop: Loop across values in []
	opt: If condition between [] satisfied, execute. Otherwise, skip.
	alt: If [] do X, else if [] do Y, else if [] do Z, ... , else do A. Blocks separated by horizontal dotted line.


LENGTHY GUIDE:

Names of classes appear on the top and on the bottom of the diagram.

Vertical dotted lines represent a class not being "active" or not "working" at a certain moment in the flow of actions.
Whenever a class is active, a white rectangle appears on top of the vertical dotted line.

Classes can call methods on other classes, and that is represented by a horizontal continuous line, ending in an arrow. On top of the line we can see the name of the called method, as well as its parameters, if any. When the call to that method is finished, a horizontal dotted line ending in an arrow will go from the class which has executed the method to the class which called the method in the first place. Note that methods may return data as a result of their execution, and the name of that data appears on top of the doted line.

Note that a class can call a method of its own as well, which will be represented by a horizontal continuous line starting and ending in the same class. To represent this, a new activation rectangle appears on top of the previous one, meaning we are now inside the scope of the function that has been just called. These rectangles that form """"mountains"""" increasing in size to the right have different colours depending on the layer of depth of the call. The superficial layer is represented by a white rectangle, and the following layers of depth are represented by alternating colours: purple, red, blue, purple, red, blue, etc. These colours do NOT have any other meaning that to clearly represent the calls to methods of the same class.

EXAMPLE: A class X which receives a method foo1() is activated with a white rectangle. The first statement in this function is a call to foo2(), a method residing in class X, and thus class X is activated once again, with a purple rectangle. Inside foo2(), the first statement is a call to foo3(), which is also a method residing in class X, and thus it is activated once more, with a red rectangle this time. When foo3() finishes executing, it returns to foo2() (purple) and the red rectangle ends. Similarly, when foo2() finishes executing, it returns to foo1() (white) and the purple rectangle ends.

There are several notes to the right of many classes in almost all diagrams. Notes with a yellowish "post-it" tone do not represent anything else than the information they hold, which is usually an action taking place in the code, or an assignation, or something along those lines. Purple notes represent calls to methods which are too big to represent in the current viewing diagram, and imply that they reside in another PNG (which will be in a directory inside the current one). Red notes also represent calls to methods residing in other PNGs, but this time because the actual execution may vary depending on the subclass type of the object executing the method. These notes represent Abstract methods, which imply that they are different for each subclass of that parent class.
EXAMPLE: The class Instrument has a method setup(), which is executed differently by each of its subclasses: SignalGenerator will do one thing, AWG will do another, etc.
Finally, blue notes represent recursive calls, which represent calls to methods in the same level of depth (to the same function currently executing) or to methods in higher levels of depth, which means that to follow the flow of execution we must either remain on the same PNG, for the first case, or climb to a higher directory to go back to a previously called function.

Frames in sequence diagrams represent different things. The "loop" frame represents a loop for all values indicated in the statement between []. A yellow note with the "break" sentence indicates that the loop finishes iterating. The "opt" frame represents a block of code that is executed iff the condition between [] is satisfied. Otherwise, it is skipped. Finally, the "alt" frame represents blocks of code from which only (and exactly) one is executed. If the condition between [] next to the "alt" is satisfied, the first block of code will be executed and, once it finishes, it will jump to the end of the frame, skipping the following blocks of the frame. If the first condition is not satisfied, the condition between [] right after the first horizontal dotted line in the frame will be checked. If it is indeed satisfied, that block of code will be executed and skip to the end of the block once finished. This process of checking conditions until one is satisfied will continue until we reach the final block of the frame, which will have no condition, and will be executed in case all other previous conditions have not been satisfied.


											Marc Delgado
											23rd of August 2022
