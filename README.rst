******************
dance-cat-to-mouse
******************

Dance the cat to catch the mice.

.. image:: https://github.com/mristin/dance-cat-to-mouse/actions/workflows/ci.yml/badge.svg
    :target: https://github.com/mristin/dance-cat-to-mouse/actions/workflows/ci.yml
    :alt: Continuous integration

.. image:: https://media.githubusercontent.com/media/mristin/dance-cat-to-mouse/main/screenshot.png
    :alt: Screenshot

Exercise Ideas
==============
.. image:: https://media.githubusercontent.com/media/mristin/dance-cat-to-mouse/main/exercise-push-with-torso.png
    :alt: Push with the torso

Here are some ideas how you can enhance your training:

* Jump instead of stomping with your feet,
* Bind your feet with an elastic band and stomp,
* Push the elastic band with your torso,
* Push the elastic band with your hands,
* Pull the elastic band with your hands (from the front).
* Make it collaborative: each player is responsible for one of the buttons.
  Do not speak during the game for the extra thrills.

Installation
============
Download and unzip a version of the game from the `Releases`_.

.. _Releases: https://github.com/mristin/dance-cat-to-mouse/releases

Running
=======
You need to connect the dance mat *before* starting the game.

Run ``dance-cat-to-mouse.exe`` (in the directory where you unzipped the game).

If you have multiple joysticks attached, the first joystick is automatically selected, and assumed to be the dance mat.

If the first joystick does not correspond to your dance mat, list the available joysticks with the following command in the command prompt:

.. code-block::

    dance-cat-to-mouse.exe --list_joysticks

You will see the names and unique IDs (GUIDs) of your joysticks.
Select the joystick that you wish by providing its GUI.
For example:

.. code-block::

    dance-cat-to-mouse.exe -joystick 03000000790000001100000000000000

Which dance mat to use?
=======================
We used an unbranded dance mat which you can order, say, from Amazon:
https://www.amazon.com/OSTENT-Non-Slip-Dancing-Dance-Compatible-PC/dp/B00FJ2KT8M

Please let us know by `creating an issue`_ if you tested the game with other mats!

.. _creating an issue: https://github.com/mristin/dance-cat-to-mouse/issues/new

Acknowledgments
===============
Bell sound from: https://opengameart.org/content/pleasing-bell-sound-effect

Barking sound from: https://opengameart.org/content/dog-bark

Victory sound from: https://opengameart.org/content/victory-4

Cat, dog and mouse from: https://opengameart.org/content/lpc-rat-cat-and-dog
