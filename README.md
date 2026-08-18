# Football Paddle Challenge


A simple 2D football-themed arcade game built with Python and Pygame.


The player controls a paddle and tries to score as many goals as possible while dealing with moving defenders, increasing ball speed, power-ups, and limited misses.


## Features


- Football-themed 2D arcade gameplay
- Player-controlled paddle
- Increasing ball speed after scoring goals
- Moving defenders
- Defender collision and movement logic
- Multiple defensive rows as the score increases
- Goal and miss system
- Combo score system
- Five misses allowed per game
- Big Paddle power-up
- Slow Ball power-up
- Dynamic ball trail
- Particle effects
- Hit sparks and visual effects
- Screen shake effects
- Synthesized sound effects without external audio files
- Pause and restart functionality
- High score system
- High score saved locally in `highscore.json`
- Start menu and game-over screen
- Football-style graphics and goal net
- No external image or sound files required


## Requirements


You need Python 3 and the following Python packages:


- Pygame
- NumPy


Install the required packages with:


```bash
pip install pygame numpy
How to Run

Clone or download this repository.

Open a terminal in the project folder and run:

python "football paddle ver0.py"

On some systems, you may need to use:

python3 "football paddle ver0.py"
Controls
Key	Action
A / Left Arrow	Move paddle left
D / Right Arrow	Move paddle right
Up Arrow	Increase ball speed
Down Arrow	Decrease ball speed
P	Pause / Resume
R	Restart the game
Enter / Space	Start the game
Escape	Quit the game
Gameplay

The objective is to score as many goals as possible.

The ball starts near the bottom of the field and moves toward the goal. Use the paddle to hit the ball back toward the goal.

After each successful goal:

Your score increases.
Your combo increases.
The ball becomes faster.
New defenders can appear.
The difficulty gradually increases.

As more defenders are added, they form additional defensive rows and make it harder to reach the goal.

Missing the Ball

If the ball reaches the bottom of the field, you lose one life.

You have a maximum of 5 misses.

After five misses, the game ends.

Power-Ups

Power-ups randomly appear during gameplay.

Big Paddle

The B power-up temporarily increases the paddle size, making it easier to hit the ball.

Slow Ball

The S power-up temporarily slows down the ball, giving the player more time to react.

Power-ups are automatically activated when the paddle collects them.

Scoring

Every successful shot into the goal gives you one point.

Consecutive goals increase your combo:

Goal → Combo x1
Goal → Combo x2
Goal → Combo x3

Missing the ball resets the combo.

The highest score is stored locally and displayed as the best score.

High Score

The game automatically saves the highest score to:

highscore.json

The file is created in the same directory as the Python game.

Example:

{
    "highscore": 10
}

You do not need to create this file manually. The game creates it automatically when a new high score is achieved.

Sound System

The game generates its sound effects programmatically.

No external .wav or .mp3 files are required.

NumPy is used to generate short audio waveforms, which are then played through Pygame.

If NumPy or the Pygame mixer is unavailable, the game can still run without these generated sound effects.

Graphics

The game uses Pygame drawing functions to create the graphics.

The game includes:

A football field
Stadium-style borders
Goal with 3D-style depth
Goal net
Football with a pentagon/hexagon-style pattern
Gradient paddles
Moving defenders
Particle effects
Ball trail
Shadows
Power-up effects
Screen shake

No external graphic assets are required.

Project Structure
Football-Paddle/
│
├── football paddle ver0.py
├── README.md
└── highscore.json

highscore.json may not exist when you first download or clone the project. It will be generated automatically after achieving a new high score.

Dependencies

The project uses:

pygame
numpy

Python standard library modules are also used:

math
random
sys
os
json
Game Difficulty

The game becomes progressively harder.

The ball speed increases after successful goals, up to a maximum speed.

Defenders are also added as the score increases.

The current configuration adds defenders starting from the third goal and can create multiple defensive rows.

This makes longer runs increasingly challenging.

Version

Current version:

Version 0

This is an early version of the project and may receive gameplay, graphics, balancing, and performance improvements in future versions.

Future Improvements

Possible future features include:

More power-ups
More defender types
Improved AI
Different difficulty levels
Better animations
More sound effects
Music
More football fields
Main menu options
Settings menu
Multiple game modes
Local multiplayer
Online multiplayer
Improved scoring system
Additional visual effects
Improved ball physics
License

This project is currently a personal project.

You can modify and experiment with the code for learning and development purposes.

M.Yazdanpour

Created as a Python/Pygame game development project.

If you enjoy the project, feel free to ⭐ star the repository!
