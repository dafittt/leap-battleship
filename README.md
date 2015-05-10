# leap-battleship
## Description
A battleship game with Leap enabled motion controls and haptic feedback.

video demonstration:
https://vimeo.com/117256668

For the course DT2140, we created a simple battleship prototype using a Leap Motion controller for gesture controls and a DIY haptic glove for haptic feedback. The glove vibrates whenever the player scores a hit.
We implemented two game modes. The one you see in this video is the classic turn based mode. In the second one, the haptic glove vibrates in different intensities depending how close the cursor is to an enemy ship. That way, the player can "feel out" the location of the enemy ships, similar to a sonar. Since the game would be too easy this way, the computer drops bombs in certain intervals instead of waiting for its turn.

## Prerequisites
- Python 2.7
- Pygame 1.9.1 (http://www.pygame.org/)
