# leap-battleship
## Description
A battleship game with Leap enabled motion controls and haptic feedback.

video demonstration:
https://vimeo.com/117256668

For the course DT2140, we created a simple battleship prototype using a Leap Motion controller for gesture controls and a DIY haptic glove for haptic feedback. The glove vibrates whenever the player scores a hit.
We implemented two game modes. The one you see in this video is the classic turn based mode. In the second one, the haptic glove vibrates in different intensities depending how close the cursor is to an enemy ship. That way, the player can "feel out" the location of the enemy ships, similar to a sonar. Since the game would be too easy this way, the computer drops bombs in certain intervals instead of waiting for its turn.

## How to play
Simply run the run.sh script in the root directory.
Note that vibration is turned off by default as you most likely don't have the required hardware setup running. This implies that the default game mode is the turn based mode because the time based mode requires vibration to be turned on.
The settings can be altered in the /src/settings.py file.

## Prerequisites
- Python 2.7
- Pygame 1.9.1 (http://www.pygame.org/)
- To enable haptics you obviously need the appropriate hardware as well as pyserial 2.7 (https://pypi.python.org/pypi/pyserial)
