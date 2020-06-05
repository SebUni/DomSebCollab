globals
[
  roads
  intersections
  blocks
  work
  activity
  land
  num-land
  chargerpatch
  grid-size-x              ;; Number of grids of streets in x direction
  grid-size-y              ;; Number of grids of streets in y direction
  grid-x-inc               ;; the amount of patches in between two roads in the x direction
  grid-y-inc               ;; the amount of patches in between two roads in the y direction
]

breed [houses house]
breed [BEVs BEV]
breed [chargers charger]

houses-own
[
  charge-rate
  energy-use
]

chargers-own
[
  charge-rate
]

BEVs-own
[
  homepatch
  workpatch
  my-house
  flag
  nav
  activity-choice
  goal
  max-capacity
  capacity
  desired-capacity
  SOC
  efficiency
  current-range
  max-range
  trip
  max-charge-rate
  charge-rate
  charge-state
  energy-use
  required-range
  nav-SOC
  parent
  child
  previous_goal
  prox-charger
  closest-charger
  ;
  chosen
  leave-home
  leave-work
  leave-activity
  errand
  counter
]

patches-own
[
  my-row
  my-column
]

to setup

  clear-all
  reset-ticks
  setup-globals
  setup-patches
  setup-houses
  setup-BEVs
  setup-chargers

end

to setup-globals
  ;;setup preferences
  ;;setup world size
  ;set watch-a-car-true? 0
  ;set num-passengers 0
  resize-world 0 49 0 49       ;; Default 0 49 0 49
  set grid-size-x 14           ;; road grid-size-x for enviornment | Default 14
  set grid-size-y 3            ;; road grid-size-y for enviornment | Default 3
  set grid-x-inc world-width / grid-size-x
  set grid-y-inc world-height / grid-size-y
  set land 0
end

to setup-patches

  ask patches
  [
    ;set my-row -1
    ;set my-column -1
    set pcolor brown + 3
  ]

  set roads patches with
  [                                    ;; Define road patches
    (floor ((pxcor + max-pxcor - floor (grid-x-inc - 1)) mod grid-x-inc) = 0) or
    (floor ((pycor + max-pycor - floor (grid-y-inc - 1)) mod grid-y-inc) = 0) or
    count neighbors != 8
  ]
  ask roads [ set pcolor white ]

  set intersections roads with
  [
    ((floor ((pxcor + max-pxcor - floor (grid-x-inc - 1)) mod grid-x-inc) = 0) and ;Identifies most intersections
    (floor ((pycor + max-pycor - floor (grid-y-inc - 1)) mod grid-y-inc) = 0))
    or
    ((floor ((pxcor + min-pxcor - floor (grid-x-inc - 0)) mod grid-x-inc) = 0) and ;Adds top most row
    (pycor = max-pycor))
    or
    ((floor ((pycor + min-pycor - floor (grid-y-inc - 0)) mod grid-y-inc) = 0) and ;Adds right most column
    (pxcor = max-pxcor))
    or
    ((pxcor = max-pxcor) and (pycor = max-pycor)) ;Adds missing top right intersection
  ]

  ;ask intersections [set pcolor green]

  ;; Identify major sections of the map, set to find the approximate middle of each block ;;
  set blocks patches with
  [
    (floor ((pxcor + max-pxcor - floor ((grid-x-inc / 2)) + 1) mod grid-x-inc) = 0) and
    (floor ((pycor + max-pycor - floor ((grid-y-inc / 2)) + 1) mod grid-y-inc) = 0) ;or
    ;(floor ((pxcor + max-pxcor - floor (grid-x-inc + 1)) mod grid-x-inc) = 0) and
    ;(floor ((pycor + max-pycor - floor (grid-y-inc + 1)) mod grid-y-inc) = 0)
  ]

  ;ask blocks [ set pcolor gray ]
  ask patch (max-pxcor / 2) (max-pycor / 2) [ask blocks in-radius 9 [set pcolor blue]] ;;Assign Work Block
  ask patch (min-pxcor + max-pxcor / 9) (max-pycor / 2) [ask blocks in-radius 7 [set pcolor orange]] ;;Assign Activity Block

  ;; Set Work patches to blue patches next to road patches ;;
  repeat 50[
  let tempwork patches with [pcolor = blue]
  ask tempwork
  [
    ask patches in-radius 1 with [pcolor = brown + 3] [set pcolor blue]
  ]
  ]
  ask roads[
    ask patches in-radius 1 with [pcolor = blue] [set pcolor black]
  ]

  let tempchargerpatch n-of 2 patches with
  [
    pycor = ceiling(max-pycor / 2) and pcolor = black
  ]
  ask tempchargerpatch [set pcolor gray]
  set work patches with [pcolor = black]
  ask work [set pcolor blue]

  ;; Set Activity patches to orange patches next to road patches ;;
  repeat 50[
  let tempactivity patches with [pcolor = orange]
  ask tempactivity
  [
    ask patches in-radius 1 with [pcolor = brown + 3] [set pcolor orange]
  ]
  ]
  ask roads[
    ask patches in-radius 1 with [pcolor = orange] [set pcolor black]
  ]

  let tempchargerpatch2 n-of 2 patches with
  [
    pycor = ceiling(max-pycor / 2) and pcolor = black
  ]
  ask tempchargerpatch2 [set pcolor gray]
  set chargerpatch patches with [pcolor = gray]
  set activity patches with [pcolor = black]
  ask activity [set pcolor orange]

  ;; Set valid land for houses to default patches next to road patches ;;
  ask roads[
    ;ask patches in-radius 1 [
    ;   set land patches with [pcolor = brown + 3]]
    ask patches in-radius 1 with [pcolor = brown + 3] [set pcolor black]
  ]
  set land patches with [pcolor = black]
  ask land [set pcolor brown + 3]
  set num-land count land ;;Returns the number of agents within agentset, instead of returning actual agentset
  ;show land

end

to setup-houses
  ;ask roads[
  ;  set num-land num-land + count patches in-radius 1 with [pcolor = brown + 3]
  ;]

  create-houses num-land [set shape "house" move-to one-of land with [not any? houses-here]]
  ask houses
  [
    set charge-rate 2300
    set energy-use 0
  ]
  ask n-of floor(((%-houses-lvl-2-chargers) / 100) * num-land) houses
  [
    set charge-rate 6600
  ]


end

to setup-BEVs
  create-BEVs ceiling(num-land * 0.92) [set shape "car" move-to one-of houses with [not any? BEVs-here]] ;;92% figure sourced from ABS
  create-BEVs ceiling(num-land * 0.92 * 0.50674) [set shape "car" move-to one-of houses with [any? BEVs-here]] ;;multiple vehicle households
  ;create-BEVs 3 [set shape "car" move-to one-of houses with [not any? BEVs-here]]
  ask BEVs
  [
    set homepatch patch-here ;Set homepatch on the patch the BEV spawned at
    set my-house houses-here
    set workpatch one-of work ;Randomly allocates a workplace, persistent
    set flag 0 ;Flag used for navigation of intersections
    set goal 0 ; goal 1 = return home | 2 = go to work | 3 = go to an activity | 4 = go to nearest charger
    set max-capacity 40000   ;;kWh;; *** ;24kWh (1st Gen Nissan Leaf lack the range in some fringe cases)
    set capacity (max-capacity - (random (0.2 * max-capacity))) ;;kWh;; initialised randomly between 80-100%
    set SOC (capacity / max-capacity) ;; % ;;
    set efficiency 178 ;;Wh/km;; ***
    set current-range (capacity / efficiency) ;;km;; possible range of EV given current capacity
    set max-range (max-capacity / efficiency) ;;km;; ***
    set trip 0 ;;km;;
    set max-charge-rate 6600 ;;kW;;
    set charge-rate 0 ;;BEV will take on the charge-rate of the patch its on
    set charge-state 0 ;; charge-state 0 = not charging | charge-state 1 = charging
    set desired-capacity max-capacity ;;Desired charge is 100% by default, can be changed at a public station for calculated trip requirements
    set energy-use 0
    set activity-choice one-of activity
    ;; *** = static values

    ;; Setup for transitions
    set chosen 0 ;;Defines movement: 1 = Home -> Work -> Home | 0 =  Home -> Work -> Activity -> Home
    set leave-home (360 + random 120)
    set leave-work (960 + random 120)
    set leave-activity (1080 + random 90)
    set errand 0
    set counter (30 + random 60)
  ]



  ;ask n-of floor((num-land * 0.9) / 2) BEVs [set chosen 1] ;;Set 50% of BEV fleet to be chosen
  ;ask n-of (num-land * 0.9) BEVs [set chosen 1]
end

to setup-chargers
  ask chargerpatch
  [
    sprout-chargers 1
    [
      set shape "lightning"
      set color yellow
      set size 1.5
      set charge-rate 7000
    ]
  ]
end

to go

  ask BEVs
  [
    if (ticks < leave-home)
    [move-to-home]
    if ((ticks > leave-home) and (ticks < leave-work))
    [
      (ifelse
      ((errand = 0) or (errand = 2))
        [move-to-work]
      (errand = 1)
        [
          move-to-activity
          if(patch-here = activity-choice)
          [
            set counter (counter - 1)
            if(counter <= 0)
            [
              if(random 100 <= 50)
              [
                set errand 2
                set activity-choice one-of activity
              ]
            ]
          ]
        ])

      if ((random 100 <= 10) and (errand < 1) and (patch-here = workpatch) and (ticks mod 3 = 0))
      [set errand 1]
    ]

    if ((ticks > leave-work) and (ticks < leave-activity))
    [
      ifelse(chosen = 1)
      [
        if ((random 100 <= 30) and ((ticks mod 3 = 0)))
        [move-to-home]
      ]
      [move-to-activity]
    ]
    if (ticks > leave-activity)
    [move-to-home]
  ]

  tick

;  ask BEVs
;  [
;   ; if ticks = 0
;   ; [enter-road]
;    if ticks < 540
;    [move-to-work]
;
;    if ticks = 540
;    [enter-road]
;    if ((ticks < 840) and (ticks > 540))
;    [move-to-activity]
;
;    if ticks = 840
;    [enter-road]
;    if ((ticks < 1440) and (ticks > 840))
;    [move-to-home]
;  ]
;  tick
;  ;set activity-choice one-of activity

end

to move-to-home
  if ((goal = 2) or (goal = 3)) ;Checks if previous goal was reached or if interrupted mid-journey
  [set flag 0]                  ;Resets navigation flag
  if (goal = 4)
  [move-to-charger]
  if((patch-here != homepatch) and (goal != 4))
  [set goal 1]
  if (nav != 1)
  [if(not member? patch-here roads)[navigate]]
  if (goal != 4)
  [
  set goal 1
  (ifelse (patch-here != homepatch)
  [
    face next-patch
    fd 1
    update
    if (member? patch-here [neighbors4] of homepatch)
    [face homepatch move-to homepatch]
  ]
  (patch-here = homepatch)
      [set flag 0 set goal 0 charge])
  ]
end

to move-to-work
  if ((goal = 1) or (goal = 3))
  [set flag 0]
  if (goal = 4)
  [move-to-charger]
  set goal 2
  if (nav != 1)
  [if(not member? patch-here roads)[navigate]]
  if (goal != 4)
  [
  set goal 2
  (ifelse (patch-here != workpatch)
  [
    face next-patch
    fd 1
    update
    if (member? patch-here [neighbors4] of workpatch)
    [face workpatch move-to workpatch]
  ]
  (patch-here = workpatch)
  [set flag 0 set goal 0])
  ]
end

to move-to-activity
  if ((goal = 1) or (goal = 2))
  [set flag 0]
  if (goal = 4)
  [move-to-charger]
  set goal 3
  if (nav != 1)
  [if(not member? patch-here roads)[navigate]]
  if (goal != 4)
  [
;  if (goal != 3)
;  [set activity-choice one-of activity set goal 3]
  (ifelse (patch-here != activity-choice)
  [
    face next-patch
    fd 1
    update
    if (member? patch-here [neighbors4] of activity-choice)
    [face activity-choice move-to activity-choice]
  ]
  (patch-here = activity-choice)
  [set flag 0 set goal 0])
  ;[set flag 0])
  ]
end

to move-to-charger
;  if ((previous_goal = 1) or (previous_goal = 2) or (previous_goal = 3))
;  [set flag 0]
  set goal 4

  if (prox-charger != 1)
  [
    let target-patch min-one-of chargerpatch [distance myself]
    set closest-charger target-patch
    set prox-charger 1
  ]

  (ifelse (patch-here != closest-charger)
  [
    face next-patch
    fd 1
    update
    if (member? patch-here [neighbors4] of closest-charger)
    [face closest-charger move-to closest-charger]
  ]
  (patch-here = closest-charger)
    [
      set flag 0
      charge
      if (charge-state = 0)
      [
        set prox-charger 0
        ifelse(previous_goal != 4)
        [set goal previous_goal]
        [set goal 0]
        enter-road
      ]
    ]
  )
end

to enter-road ;Checks to see if vehicle is on a patch or road
  if (patch-here = homepatch) or (patch-here = workpatch) or (member? patch-here activity) or (member? patch-here chargerpatch)
  [
    let nearest-road min-one-of roads [distance myself] face nearest-road fd 1
  ]
end

to-report next-patch
  let choices neighbors4 with [pcolor = white]
  let choice min-one-of choices [distance [workpatch] of myself]

  (ifelse (goal = 1)
    [
      let choices-inter1 intersections in-radius (grid-size-x + 2)
      let closest-inter-home min-one-of choices-inter1 [distance [homepatch] of myself]
      let choices1 neighbors4 with [pcolor = white]
      let choice1 min-one-of choices1 [distance [closest-inter-home] of myself]
      (ifelse ((patch-here = closest-inter-home) or (flag = 1))
      [let choice_1 min-one-of choices1 [distance [homepatch] of myself] set flag 1 report choice_1]
      [report choice1])
    ]

  (goal = 2)
    [
      let choices-inter2 intersections in-radius (grid-size-x + 2)
      let closest-inter-work min-one-of choices-inter2 [distance [workpatch] of myself]
      let choices2 neighbors4 with [pcolor = white]
      let choice2 min-one-of choices2 [distance [closest-inter-work] of myself]
      (ifelse ((patch-here = closest-inter-work) or (flag = 1))
      [let choice_2 min-one-of choices2 [distance [workpatch] of myself] set flag 1 report choice_2]
      [report choice2])
    ]

  (goal = 3)
    [
      let choices-inter3 intersections in-radius (grid-size-x + 2)
      let closest-inter-activity min-one-of choices-inter3 [distance [activity-choice] of myself]
      let choices3 neighbors4 with [pcolor = white]
      let choice3 min-one-of choices3 [distance [closest-inter-activity] of myself]
      (ifelse ((patch-here = closest-inter-activity) or (flag = 1))
      [let choice_3 min-one-of choices3 [distance [activity-choice] of myself] set flag 1 report choice_3]
      [report choice3])
    ]

    (goal = 4)
    [
      let choices-inter4 intersections in-radius (grid-size-x + 2)
      let closest-inter-charger min-one-of choices-inter4 [distance [closest-charger] of myself]
      let choices4 neighbors4 with [pcolor = white]
      let choice4 min-one-of choices4 [distance [closest-inter-charger] of myself]
      (ifelse ((patch-here = closest-inter-charger) or (flag = 1))
      [let choice_4 min-one-of choices4 [distance [closest-charger] of myself] set flag 1 report choice_4]
      [report choice4])
    ])

end

to update
  set capacity (capacity - (efficiency / 4))
  set SOC (capacity / max-capacity)
  set current-range (capacity / efficiency)
  set trip (trip + 0.25)
end

to charge
  (ifelse ((capacity < desired-capacity) and ((patch-here = homepatch) or (member? patch-here chargerpatch)))
  [
    set charge-state 1
  ]
    ((capacity = desired-capacity) or (capacity > desired-capacity) ) ;or (member? patch-here roads)
  [set charge-state 0 set energy-use 0])

  if (charge-state = 1)
  [
    (ifelse
      (patch-here = homepatch)
      [
        ;set charge-rate ((item 0 [charge-rate] of my-house) / 60)
        let charge-rate-here (item 0 [charge-rate] of my-house)
        ifelse (charge-rate-here > max-charge-rate)
        [set charge-rate (max-charge-rate / 60)]
        [set charge-rate (charge-rate-here / 60)]
        set desired-capacity (max-capacity - charge-rate)
        set capacity (capacity + charge-rate)
        set energy-use (charge-rate * 60)
        set SOC (capacity / max-capacity)
        set current-range (capacity / efficiency)
      ]

      (member? patch-here chargerpatch)
      [
        ;let charge-rate-here (item 0 [charge-rate] of patch-here)
        ifelse (charger-here? > max-charge-rate)
        [set charge-rate (max-charge-rate / 60)]
        [set charge-rate (charger-here? / 60)]
        ;set desired-capacity (desired-capacity - charge-rate)
        ;set desired-capacity max-capacity
        set capacity (capacity + charge-rate)
        ;set energy-use (charge-rate * 60) ;;
        set SOC (capacity / max-capacity)
        set current-range (capacity / efficiency)
      ]
    [set charge-state 0 set energy-use 0])
  ]

  ask my-house [set energy-use [energy-use] of myself]
end

to-report charger-here?
  report (item 0 [charge-rate] of chargers-on patch-here)
end

to navigate
  if (((goal = 1) and (patch-here != homepatch)) or ((goal = 2) and (patch-here != workpatch)) or ((goal = 3) and (patch-here != activity-choice)) or
    ((goal = 4) and ((patch-here != homepatch) or (patch-here != workpatch) or (patch-here != activity-choice))))
  [
  hatch 1
  [
    hide-turtle
    set capacity (capacity * 5) ;;Create a scenario with a turtle that has 5 times the capacity
    set nav 1
    set trip 0
    (ifelse  ;;Repeat action no. of times which scales with the world/distance
    (goal = 1)
      [
        repeat (2 * (max-pxcor + max-pycor)) [move-to-home]
      ]
    (goal = 2)
      [
        repeat (2 * (max-pxcor + max-pycor)) [move-to-work]
      ]
    (goal = 3)
      [
        repeat (2 * (max-pxcor + max-pycor)) [move-to-activity]
      ])
    set parent myself
    set required-range [trip] of self
    ;set nav-SOC [SOC] of self
  ]
  set child BEVs with [parent = myself]
  set required-range (item 0 [required-range] of child) ;;required-range is a list, index to first (and only) item
  ask child [die]
  if((required-range * 1.5) > current-range) ;;built in 50% threshold
    [
      set previous_goal goal
      set goal 4
      set desired-capacity ((required-range * 1.6) * efficiency) ;;extra 10% to account for any pathfinding mishaps
      ;set desired-capacity max-capacity
    ]

  ]
end


;;Useful Commands
;; ask patches with [pcolor = blue] [show count neighbors]
;; ask patch 0 0 [ask patches in-radius 3 [set pcolor red] ]
;; ask patch (max-pxcor / 2) (max-pycor / 2) [ask blocks in-radius 10 [set pcolor green]]
;; ask roads [ask patches in-radius 1 with [pcolor = brown + 3] [set pcolor black]]
;to-report next-patch
;      let choices-inter intersections in-radius (grid-size-x + 2)
;      let closest-inter-work min-one-of choices-inter [distance [workpatch] of myself]
;      let choices neighbors4 with [pcolor = white]
;      let choice min-one-of choices [distance [closest-inter-work] of myself]
;      ifelse ((patch-here = closest-inter-work) or (flag = 1))
;      [let choice2 min-one-of choices [distance [workpatch] of myself] set flag 1 report choice2]
;      [report choice]
;end
;; show [who] of BEVs with [SOC < 0]
;; show count BEVs with [patch-here = homepatch and goal = 0]

;;Temporal Dimension
;; If 1 tick = 1 minute, travelling 1 patch and incrementing at a tick rate of 1 equates to roughly 60km/h
;; Therefore 60 ticks = 60 minutes (1 hour)
;; For a charge rate of 2.4kW, a battery with a capacity of 24kWh will take approximately 10 hours to charge
;; Capacity should therefore be incremented by the charge rate after every 60 ticks has pass
;; This equates to: 2400/60 = 40W/minute (40 energy added by tick)

;;Notes
;; move-to-work /
;; move-to-home /
;; move-to-activity /
;; charge (perhaps group this as an action that occurs as part of "move-to-home")
;; inability to move when SOC = 0
;; implement public charger at work/activity zones
;; ability to navigate roads /

;; each BEV should have: SOC - range, efficiency/consumption (Wh/km), specific work & house patches /
;; each house should have: charge rate (kW)

;;BehaviourSpace
@#$#@#$#@
GRAPHICS-WINDOW
706
12
1364
671
-1
-1
13.0
1
10
1
1
1
0
0
0
1
0
49
0
49
1
1
1
ticks
30.0

BUTTON
20
43
83
76
NIL
setup
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

TEXTBOX
136
68
286
86
NIL
11
0.0
1

BUTTON
90
43
153
76
NIL
go
NIL
1
T
OBSERVER
NIL
NIL
NIL
NIL
1

PLOT
18
90
322
339
Average SOC of fleet
Time (ticks)
SOC
0.0
10.0
0.0
1.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" "plot mean [SOC] of BEVs"

PLOT
18
353
321
498
Min Mean Max of Distance Travelled
Time (ticks)
km
0.0
10.0
0.0
70.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" "plot max [trip] of BEVs"
"pen-1" 1.0 0 -7500403 true "" "plot min [trip] of BEVs"
"pen-2" 1.0 0 -2674135 true "" "plot mean [trip] of BEVs"

PLOT
348
89
680
339
Total Demand from Household Chargers
Time (ticks)
kW
0.0
10.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" "plot sum [energy-use] of houses"

PLOT
348
355
682
494
SOC
Time (ticks)
SOC
0.0
10.0
0.0
1.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" "plot [SOC] of BEV 1000"

SLIDER
183
44
371
77
%-houses-lvl-2-chargers
%-houses-lvl-2-chargers
0
100
20.0
1
1
NIL
HORIZONTAL

PLOT
349
501
683
688
Mean Energy Use
NIL
NIL
0.0
10.0
0.0
10.0
true
false
"" ""
PENS
"default" 1.0 0 -16777216 true "" "plot mean [energy-use] of houses"

@#$#@#$#@
## WHAT IS IT?

(a general understanding of what the model is trying to show or explain)

## HOW IT WORKS

(what rules the agents use to create the overall behavior of the model)

## HOW TO USE IT

(how to use the model, including a description of each of the items in the Interface tab)

## THINGS TO NOTICE

(suggested things for the user to notice while running the model)

## THINGS TO TRY

(suggested things for the user to try to do (move sliders, switches, etc.) with the model)

## EXTENDING THE MODEL

(suggested things to add or change in the Code tab to make the model more complicated, detailed, accurate, etc.)

## NETLOGO FEATURES

(interesting or unusual features of NetLogo that the model uses, particularly in the Code tab; or where workarounds were needed for missing features)

## RELATED MODELS

(models in the NetLogo Models Library and elsewhere which are of related interest)

## CREDITS AND REFERENCES

(a reference to the model's URL on the web if it has one, as well as any other necessary credits, citations, and links)
@#$#@#$#@
default
true
0
Polygon -7500403 true true 150 5 40 250 150 205 260 250

airplane
true
0
Polygon -7500403 true true 150 0 135 15 120 60 120 105 15 165 15 195 120 180 135 240 105 270 120 285 150 270 180 285 210 270 165 240 180 180 285 195 285 165 180 105 180 60 165 15

arrow
true
0
Polygon -7500403 true true 150 0 0 150 105 150 105 293 195 293 195 150 300 150

box
false
0
Polygon -7500403 true true 150 285 285 225 285 75 150 135
Polygon -7500403 true true 150 135 15 75 150 15 285 75
Polygon -7500403 true true 15 75 15 225 150 285 150 135
Line -16777216 false 150 285 150 135
Line -16777216 false 150 135 15 75
Line -16777216 false 150 135 285 75

bug
true
0
Circle -7500403 true true 96 182 108
Circle -7500403 true true 110 127 80
Circle -7500403 true true 110 75 80
Line -7500403 true 150 100 80 30
Line -7500403 true 150 100 220 30

butterfly
true
0
Polygon -7500403 true true 150 165 209 199 225 225 225 255 195 270 165 255 150 240
Polygon -7500403 true true 150 165 89 198 75 225 75 255 105 270 135 255 150 240
Polygon -7500403 true true 139 148 100 105 55 90 25 90 10 105 10 135 25 180 40 195 85 194 139 163
Polygon -7500403 true true 162 150 200 105 245 90 275 90 290 105 290 135 275 180 260 195 215 195 162 165
Polygon -16777216 true false 150 255 135 225 120 150 135 120 150 105 165 120 180 150 165 225
Circle -16777216 true false 135 90 30
Line -16777216 false 150 105 195 60
Line -16777216 false 150 105 105 60

car
false
0
Polygon -7500403 true true 300 180 279 164 261 144 240 135 226 132 213 106 203 84 185 63 159 50 135 50 75 60 0 150 0 165 0 225 300 225 300 180
Circle -16777216 true false 180 180 90
Circle -16777216 true false 30 180 90
Polygon -16777216 true false 162 80 132 78 134 135 209 135 194 105 189 96 180 89
Circle -7500403 true true 47 195 58
Circle -7500403 true true 195 195 58

circle
false
0
Circle -7500403 true true 0 0 300

circle 2
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240

cow
false
0
Polygon -7500403 true true 200 193 197 249 179 249 177 196 166 187 140 189 93 191 78 179 72 211 49 209 48 181 37 149 25 120 25 89 45 72 103 84 179 75 198 76 252 64 272 81 293 103 285 121 255 121 242 118 224 167
Polygon -7500403 true true 73 210 86 251 62 249 48 208
Polygon -7500403 true true 25 114 16 195 9 204 23 213 25 200 39 123

cylinder
false
0
Circle -7500403 true true 0 0 300

dot
false
0
Circle -7500403 true true 90 90 120

face happy
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 255 90 239 62 213 47 191 67 179 90 203 109 218 150 225 192 218 210 203 227 181 251 194 236 217 212 240

face neutral
false
0
Circle -7500403 true true 8 7 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Rectangle -16777216 true false 60 195 240 225

face sad
false
0
Circle -7500403 true true 8 8 285
Circle -16777216 true false 60 75 60
Circle -16777216 true false 180 75 60
Polygon -16777216 true false 150 168 90 184 62 210 47 232 67 244 90 220 109 205 150 198 192 205 210 220 227 242 251 229 236 206 212 183

fish
false
0
Polygon -1 true false 44 131 21 87 15 86 0 120 15 150 0 180 13 214 20 212 45 166
Polygon -1 true false 135 195 119 235 95 218 76 210 46 204 60 165
Polygon -1 true false 75 45 83 77 71 103 86 114 166 78 135 60
Polygon -7500403 true true 30 136 151 77 226 81 280 119 292 146 292 160 287 170 270 195 195 210 151 212 30 166
Circle -16777216 true false 215 106 30

flag
false
0
Rectangle -7500403 true true 60 15 75 300
Polygon -7500403 true true 90 150 270 90 90 30
Line -7500403 true 75 135 90 135
Line -7500403 true 75 45 90 45

flower
false
0
Polygon -10899396 true false 135 120 165 165 180 210 180 240 150 300 165 300 195 240 195 195 165 135
Circle -7500403 true true 85 132 38
Circle -7500403 true true 130 147 38
Circle -7500403 true true 192 85 38
Circle -7500403 true true 85 40 38
Circle -7500403 true true 177 40 38
Circle -7500403 true true 177 132 38
Circle -7500403 true true 70 85 38
Circle -7500403 true true 130 25 38
Circle -7500403 true true 96 51 108
Circle -16777216 true false 113 68 74
Polygon -10899396 true false 189 233 219 188 249 173 279 188 234 218
Polygon -10899396 true false 180 255 150 210 105 210 75 240 135 240

house
false
0
Rectangle -7500403 true true 45 120 255 285
Rectangle -16777216 true false 120 210 180 285
Polygon -7500403 true true 15 120 150 15 285 120
Line -16777216 false 30 120 270 120

leaf
false
0
Polygon -7500403 true true 150 210 135 195 120 210 60 210 30 195 60 180 60 165 15 135 30 120 15 105 40 104 45 90 60 90 90 105 105 120 120 120 105 60 120 60 135 30 150 15 165 30 180 60 195 60 180 120 195 120 210 105 240 90 255 90 263 104 285 105 270 120 285 135 240 165 240 180 270 195 240 210 180 210 165 195
Polygon -7500403 true true 135 195 135 240 120 255 105 255 105 285 135 285 165 240 165 195

lightning
false
0
Polygon -7500403 true true 120 135 90 195 135 195 105 300 225 165 180 165 210 105 165 105 195 0 75 135

line
true
0
Line -7500403 true 150 0 150 300

line half
true
0
Line -7500403 true 150 0 150 150

pentagon
false
0
Polygon -7500403 true true 150 15 15 120 60 285 240 285 285 120

person
false
0
Circle -7500403 true true 110 5 80
Polygon -7500403 true true 105 90 120 195 90 285 105 300 135 300 150 225 165 300 195 300 210 285 180 195 195 90
Rectangle -7500403 true true 127 79 172 94
Polygon -7500403 true true 195 90 240 150 225 180 165 105
Polygon -7500403 true true 105 90 60 150 75 180 135 105

plant
false
0
Rectangle -7500403 true true 135 90 165 300
Polygon -7500403 true true 135 255 90 210 45 195 75 255 135 285
Polygon -7500403 true true 165 255 210 210 255 195 225 255 165 285
Polygon -7500403 true true 135 180 90 135 45 120 75 180 135 210
Polygon -7500403 true true 165 180 165 210 225 180 255 120 210 135
Polygon -7500403 true true 135 105 90 60 45 45 75 105 135 135
Polygon -7500403 true true 165 105 165 135 225 105 255 45 210 60
Polygon -7500403 true true 135 90 120 45 150 15 180 45 165 90

sheep
false
15
Circle -1 true true 203 65 88
Circle -1 true true 70 65 162
Circle -1 true true 150 105 120
Polygon -7500403 true false 218 120 240 165 255 165 278 120
Circle -7500403 true false 214 72 67
Rectangle -1 true true 164 223 179 298
Polygon -1 true true 45 285 30 285 30 240 15 195 45 210
Circle -1 true true 3 83 150
Rectangle -1 true true 65 221 80 296
Polygon -1 true true 195 285 210 285 210 240 240 210 195 210
Polygon -7500403 true false 276 85 285 105 302 99 294 83
Polygon -7500403 true false 219 85 210 105 193 99 201 83

square
false
0
Rectangle -7500403 true true 30 30 270 270

square 2
false
0
Rectangle -7500403 true true 30 30 270 270
Rectangle -16777216 true false 60 60 240 240

star
false
0
Polygon -7500403 true true 151 1 185 108 298 108 207 175 242 282 151 216 59 282 94 175 3 108 116 108

target
false
0
Circle -7500403 true true 0 0 300
Circle -16777216 true false 30 30 240
Circle -7500403 true true 60 60 180
Circle -16777216 true false 90 90 120
Circle -7500403 true true 120 120 60

tree
false
0
Circle -7500403 true true 118 3 94
Rectangle -6459832 true false 120 195 180 300
Circle -7500403 true true 65 21 108
Circle -7500403 true true 116 41 127
Circle -7500403 true true 45 90 120
Circle -7500403 true true 104 74 152

triangle
false
0
Polygon -7500403 true true 150 30 15 255 285 255

triangle 2
false
0
Polygon -7500403 true true 150 30 15 255 285 255
Polygon -16777216 true false 151 99 225 223 75 224

truck
false
0
Rectangle -7500403 true true 4 45 195 187
Polygon -7500403 true true 296 193 296 150 259 134 244 104 208 104 207 194
Rectangle -1 true false 195 60 195 105
Polygon -16777216 true false 238 112 252 141 219 141 218 112
Circle -16777216 true false 234 174 42
Rectangle -7500403 true true 181 185 214 194
Circle -16777216 true false 144 174 42
Circle -16777216 true false 24 174 42
Circle -7500403 false true 24 174 42
Circle -7500403 false true 144 174 42
Circle -7500403 false true 234 174 42

turtle
true
0
Polygon -10899396 true false 215 204 240 233 246 254 228 266 215 252 193 210
Polygon -10899396 true false 195 90 225 75 245 75 260 89 269 108 261 124 240 105 225 105 210 105
Polygon -10899396 true false 105 90 75 75 55 75 40 89 31 108 39 124 60 105 75 105 90 105
Polygon -10899396 true false 132 85 134 64 107 51 108 17 150 2 192 18 192 52 169 65 172 87
Polygon -10899396 true false 85 204 60 233 54 254 72 266 85 252 107 210
Polygon -7500403 true true 119 75 179 75 209 101 224 135 220 225 175 261 128 261 81 224 74 135 88 99

wheel
false
0
Circle -7500403 true true 3 3 294
Circle -16777216 true false 30 30 240
Line -7500403 true 150 285 150 15
Line -7500403 true 15 150 285 150
Circle -7500403 true true 120 120 60
Line -7500403 true 216 40 79 269
Line -7500403 true 40 84 269 221
Line -7500403 true 40 216 269 79
Line -7500403 true 84 40 221 269

wolf
false
0
Polygon -16777216 true false 253 133 245 131 245 133
Polygon -7500403 true true 2 194 13 197 30 191 38 193 38 205 20 226 20 257 27 265 38 266 40 260 31 253 31 230 60 206 68 198 75 209 66 228 65 243 82 261 84 268 100 267 103 261 77 239 79 231 100 207 98 196 119 201 143 202 160 195 166 210 172 213 173 238 167 251 160 248 154 265 169 264 178 247 186 240 198 260 200 271 217 271 219 262 207 258 195 230 192 198 210 184 227 164 242 144 259 145 284 151 277 141 293 140 299 134 297 127 273 119 270 105
Polygon -7500403 true true -1 195 14 180 36 166 40 153 53 140 82 131 134 133 159 126 188 115 227 108 236 102 238 98 268 86 269 92 281 87 269 103 269 113

x
false
0
Polygon -7500403 true true 270 75 225 30 30 225 75 270
Polygon -7500403 true true 30 75 75 30 270 225 225 270
@#$#@#$#@
NetLogo 6.1.1
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
@#$#@#$#@
default
0.0
-0.2 0 0.0 1.0
0.0 1 1.0 0.0
0.2 0 0.0 1.0
link direction
true
0
Line -7500403 true 150 150 90 180
Line -7500403 true 150 150 210 180
@#$#@#$#@
0
@#$#@#$#@
