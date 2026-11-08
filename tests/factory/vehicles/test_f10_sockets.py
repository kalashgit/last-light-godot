"""Art proposal geometry checks only; not W05 gameplay acceptance."""
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[3]/"tools"/"vehicle_factory"))
from fleet_catalog import PROFILES
from fleet_sockets import proposed_sockets


def main():
    for model,profile in PROFILES.items():
        obj=proposed_sockets(model)
        L,W,H=profile["dimensions_m"]
        s=obj["sockets"]
        assert obj["status"]=="ART_PROPOSAL_NOT_ENGINE_ACCEPTED"
        assert obj["animation_state"]=="NO_VALIDATED_PANEL_RIG"
        assert len(s)==22 and len(set(s))==22
        assert s["front_axle"][0]>0>s["rear_axle"][0]
        for key,position in s.items():
            assert len(position)==3 and all(isinstance(v,(int,float)) for v in position)
            assert -L*.65<=position[0]<=L*.65,(model,key,position)
            assert -W*.8<=position[1]<=W*.8,(model,key,position)
            assert 0<=position[2]<=H,(model,key,position)
    print("F10_ART_SOCKETS_PASS",len(PROFILES),"profiles",22,"sockets each")


if __name__=="__main__":main()
