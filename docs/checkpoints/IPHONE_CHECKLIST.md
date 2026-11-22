# iPhone / Xogot manual verification checklist

Automated tests cannot stand in for a thumb on glass. Nothing below has been run on a physical device yet. Please tick through it in Xogot and note anything that fails; until then V0.4–V0.8 are **implemented and machine-tested, not device-validated**.

Turn on **II → Performance overlay** while testing; it shows FPS, frame and sim time, zombie counts and AI states.

## 1. Boot
- [ ] Project opens in Xogot with no script errors in the Output panel.
- [ ] Loading bar completes (note the seconds it takes on your phone: ____ s).
- [ ] Title screen appears; text is readable; buttons are comfortably tappable.
- [ ] Nothing important sits under the notch / Dynamic Island / home indicator, in portrait **and** landscape.

## 2. Movement and multi-touch
- [ ] Dragging in the lower-left moves the survivor in the direction of the drag (up = up the screen).
- [ ] The stick follows your thumb if you drag far; lifting stops movement immediately.
- [ ] While moving, a second finger on ATTACK swings without interrupting movement.
- [ ] While moving, tapping USE opens a door; holding USE (~½ s) opens the options list.
- [ ] RUN and SNEAK toggle and show their lit state. Running drains the thin stamina bar.
- [ ] Pinch zoom works; + / − work.
- [ ] No stuck input after opening and closing any panel, or after rotating the phone.
- [ ] Rotating the phone re-lays out the HUD and menus at the same physical size.

## 3. World and rendering
- [ ] Inside a house: the roof disappears and walls in front of you drop to stubs; furniture is visible.
- [ ] Walking out: the roof returns. Standing behind a building you can still see a faint survivor.
- [ ] Characters pass correctly in front of and behind walls, fences, trees and cars.
- [ ] No visible seams between ground tiles at any zoom level.
- [ ] Walking several minutes in one direction: no hitching when new areas load (note worst stutter: ____).
- [ ] Night is dark but playable; the LIGHT button (with a flashlight) lights the area ahead.
- [ ] Rain and fog appear and do not tank the frame rate.
- [ ] FPS downtown with a dozen infected on screen: ____ (target 60, minimum acceptable 30).

## 4. Survival loop
- [ ] BAG: tapping an item on the left takes it; tapping one of yours shows actions; lists scroll with a finger.
- [ ] Eat, drink, equip a weapon, wear a backpack.
- [ ] Get hurt, then BODY → Bandage stops the bleeding icon.
- [ ] MAKE → rip a sheet; build a campfire or crate (the BUILD / CANCEL placement buttons appear).
- [ ] Sleep in a bed: screen dims, clock runs fast, you wake rested or when disturbed.
- [ ] MAP shows where you have been, oriented like the game view.

## 5. The infected
- [ ] They notice you by sight in daylight from a street away, less at night and when sneaking.
- [ ] A gunshot or smashed window draws them from well off screen.
- [ ] They batter a closed door and eventually break it; they climb through a broken window.
- [ ] Combat registers reliably: hits stagger, some knock down, kills leave lootable corpses.

## 6. Persistence
- [ ] II → Save, then force-quit Xogot's player and relaunch: Continue restores position, inventory, wounds, time, opened doors, barricades, dropped items and built structures.
- [ ] Switch to another app mid-game and come back after a while: nothing lost (autosave on background).
- [ ] Die: the death screen appears; a new game starts cleanly.

## 7. Audio
- [ ] Footsteps, hits, doors, glass, groans and gunshots are audible and not harsh. (Generated sounds have only been checked for errors, never listened to.)

## 8. Added in the final pass (vehicles, fire, survivors, upper floors)
- [ ] Hotbar slots under the top buttons draw the tapped weapon; they do not cover any text you need.
- [ ] SHOVE (with a weapon out) pushes without swinging; CALL whispers while sneaking and shouts otherwise.
- [ ] The 1x button cycles 2x / 4x and snaps back to 1x when something chases you.
- [ ] USE on a car → Drive (or Hotwire / Install battery / Refuel first). The HUD switches to BRAKE / EXIT with speed and fuel.
- [ ] Steering with the stick feels controllable: pushing along the car's heading accelerates, across it turns a quarter, against it reverses. Note how it feels: ____
- [ ] The car sorts correctly in front of / behind buildings and trees while moving.
- [ ] Hitting infected knocks them down; hitting a wall stops the car and hurts the engine. EXIT refuses while moving.
- [ ] Headlights light the road at night. Engine sound is audible and not unpleasant.
- [ ] Set a fire (hold USE on a corpse with a lighter → Burn): flames animate, spread to grass/furniture, light the night, go out on their own. Frame rate with ~50 burning tiles: ____
- [ ] Find a house with stairs: Go upstairs / Go downstairs both work; the upper room is visible (roof cut away) and walkable.
- [ ] Meet a survivor (some houses): Talk, "Come with me", "Wait here", Give food. They follow through doors and fight beside you.
- [ ] Die → "Wake up as someone else in this world" starts a new survivor; the old body/gear can be found again.
- [ ] Farm: the chicken coop gives eggs; the well gives water after the mains fail.
