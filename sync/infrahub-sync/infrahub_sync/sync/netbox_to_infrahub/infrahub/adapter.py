from infrahub_sync.adapters.infrahub import InfrahubAdapter

from .models import Location, Rack, Role, Tag


# -------------------------------------------------------
# AUTO-GENERATED FILE, DO NOT MODIFY
#  This file has been generated with the command `infrahub-sync generate`
#  All modifications will be lost the next time you reexecute this command
# -------------------------------------------------------
class InfrahubSync(InfrahubAdapter):
    location = Location
    rack = Rack
    role = Role
    tag = Tag
