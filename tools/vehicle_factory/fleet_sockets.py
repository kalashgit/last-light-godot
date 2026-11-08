"""F10 art-only interaction socket proposals for the parametric passenger fleet.

These positions are chassis-local metres (x forward, y right, z upward).
They are NOT a W05 gameplay schema and do not imply animated doors exist.
"""
import json
from fleet_catalog import PROFILES


def proposed_sockets(model):
    profile=PROFILES[model]
    length,width,height=profile["dimensions_m"]
    wheelbase=profile["wheelbase_m"]
    radius=.315 if profile["geometry"] in ("sedan","hatchback","wagon","coupe") else .36
    front=wheelbase/2
    rear=-wheelbase/2
    door_front=length*.11
    door_rear=-length*.16
    hinges={}
    for side,label in ((-1,"L"),(1,"R")):
        y=side*width*.44
        hinges[f"front_door_hinge_{label}"]=[round(length*.275,3),round(y,3),.80]
        hinges[f"front_door_access_{label}"]=[round(door_front,3),round(side*width*.72,3),.05]
        hinges[f"rear_door_hinge_{label}"]=[round(-length*.025,3),round(y,3),.80]
        hinges[f"rear_door_access_{label}"]=[round(door_rear,3),round(side*width*.72,3),.05]
        for axle,x in (("front",front),("rear",rear)):
            hinges[f"{axle}_wheel_hub_{label}"]=[round(x,3),round(side*width*.405,3),.34]
    sockets={
        "ground_center":[0,0,0],"front_axle":[round(front,3),0,.34],
        "rear_axle":[round(rear,3),0,.34],
        "hood_hinge":[round(length*.300,3),0,.86],
        "engine_socket":[round(length*.370,3),0,.67],
        "trunk_hinge":[round(-length*.360,3),0,.87],
        "trunk_access":[round(-length*.540,3),0,.35],
        "fuel_port":[round(-length*.310,3),round(-width*.45,3),.72],
        "seat_driver":[round(length*.058,3),round(-width*.23,3),.56],
        "cargo_socket":[round(-length*.370,3),0,.52],
        **hinges,
    }
    return {
        "schema_version":1,"status":"ART_PROPOSAL_NOT_ENGINE_ACCEPTED",
        "model":model,"coordinate_system":"x_forward_y_right_z_up_m",
        "body_dimensions_m":profile["dimensions_m"],
        "wheelbase_m":wheelbase,"proposed_tire_radius_m":radius,
        "collision_footprint_m":[round(length*.98,3),round(width*.95,3)],
        "sockets":sockets,
        "animation_state":"NO_VALIDATED_PANEL_RIG",
        "review_owners":["W01","W05","W07","W09"],
    }


if __name__=="__main__":
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser()
    parser.add_argument("--model",choices=sorted(PROFILES),required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(proposed_sockets(args.model),indent=2)+"\n")
    print("F10_SOCKETS_PROPOSED",args.model,len(proposed_sockets(args.model)["sockets"]))
