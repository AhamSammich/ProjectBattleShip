# Project BattleShip
## The Project
This is the second iteration of my battleship project made using Python and Pygame.
This project was developed independently for learning purposes.


## The Game
This game is classic BattleShip against an AI opponent with some extra features.
Running the script in bsmain.py will start the game.

### Ships
Each player has five ships, each with a specific feature/skill:
- Carrier
  - Skill: EM Railgun
    - Fires across an entire row/column depending on the ship's orientation
- Cruiser
  - Skill: Missile Salvo
    - Fires a volley of missiles a chance for up to 5 successive shots
- Destroyer
  - Skill: Sonar Blast
    - Chance of locating an enemy submarine upon being hit
- Submarine
  - Skill: Countermeasures
    - Chance of evading detection upon being hit (reposition ship and wipe enemy's tracked misses)
- Frigate
  - Skill: Depth Charge
    - Deploys charge with (10 * number charges deployed)% chance to hit an enemy submarine

### Main Game Flow

![main_game_flow](./Images/bs_main_flow.svg "Main Game Flow")

### AI Targeting Flow

![ai_target_flow](./Images/bs_comp_target_flow.svg "AI Targeting Flow")

## Assets
<div>Icons made by <a href="https://www.freepik.com" title="Freepik">Freepik</a> from <a href="https://www.flaticon.com/" title="Flaticon">www.flaticon.com</a></div>
<div>Ship images made by <a href="https://opengameart.org/content/sea-warfare-set-ships-and-more" title="Sea Warfare set">Lowder2</a> from <a href="https://www.opengameart.org/" title="OpenGameArt">www.opengameart.org</a></div>
<a href="/Sounds/ATTRIBUTION.md">Sound attributions</a>

## License
This project is licensed under the MIT license.