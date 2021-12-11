from os import replace
import bpy
import math

class Hologram:
    def __init__(self, holo_id, model, pos, ang, scale) -> None:
        self.holo_id = holo_id
        self.model = model
        self.pos = pos
        self.ang = ang
        self.scale = scale


class BE:
    def __init__(self) -> None:
        self.e2_code = ""
        self.holograms_init = []
        self.keyframes_table = {}
        self.debug("Started !")

    def debug(self, text):
        print(f"[BLENDER TO E2 HOLO] {text}")

    def push_code(self, code):
        self.e2_code += f"{code}\n"

    def register_hologram(self, holo_id = 0, model = "cube", color = "vec(255)"):
        self.holograms_init.append({
            "holo_id": holo_id,
            "model": model,
            "color": color
        })
        self.debug(f"Added hologram n°{holo_id} ({model})")

    def register_keyframe(self, frame_number = 0, holo_id = 0, local_pos = "vec(0)", ang = "ang(0)", scale = "vec(1)"):
        parts = f'table('
        parts += f'"id" = {holo_id}, '
        parts += f'"pos" = {local_pos}, '
        parts += f'"ang" = {ang}, '
        parts += f'"scale" = {scale}'
        parts += ')'

        if not frame_number in self.keyframes_table:
            self.keyframes_table[frame_number] = []
            self.debug(f"Created Keyframe {frame_number}")

        self.keyframes_table[frame_number].append(parts)

    def init_generation(self):
        #Creating Holograms
        for i, ob in enumerate(bpy.data.objects):
            mesh_name = ob.data.name.lower()
            ret_model = ""
            ret_color = "vec4(255)"

            #Trying to get object color ...
            if ob.active_material != None:
                print("Color changed")
                material = ob.material_slots[0].material
                # Get the nodes in the node tree
                nodes = material.node_tree.nodes
                # Get a principled node
                principled = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
                base_color = principled.inputs['Base Color'] #Or principled.inputs[0]
                # Get its default value (not the value from a possible link)
                v = base_color.default_value

                ret_color = f"vec4({v[0] * 255}, {v[1] * 255}, {v[2] * 255}, {v[3] * 255})"

            #Models
            if "cube" in mesh_name:
                ret_model = "cube"
                self.debug("Cube found !")

            elif "sphere" in mesh_name:
                ret_model = "hqsphere"
                self.debug("Sphere found !")

            elif "cylinder" in mesh_name:
                ret_model = "hqcylinder"
                self.debug("Cylinder found !")

            elif "torus" in mesh_name:
                ret_model = "hqtorus"
                self.debug("Torus found !")

            elif "cone" in mesh_name:
                ret_model = "cone"
                self.debug("Cone found !")

            self.register_hologram(i, ret_model, ret_color)
            self.register_ob(0, i, ob)
        
        self.register_keyframes()

    def register_keyframes(self):
        sce = bpy.context.scene

        for f in range(sce.frame_start, sce.frame_end + 1):
            sce.frame_set(f)
            for i, ob in enumerate(bpy.data.objects):
                self.register_ob(f, i, ob)

    def register_ob(self, frame_number, i, ob):
        rp = ob.location
        px = str(rp.x).replace("e-", "")
        py = str(rp.y).replace("e-", "")
        pz = str(rp.z).replace("e-", "")
        ret_pos = f"vec({px}, {py}, {pz})"

        rs = ob.scale
        ret_scale = f"vec({rs.x}, {rs.y}, {rs.z})"

        r = [math.degrees(a) for a in ob.rotation_euler]
        r[0] = str(r[0]).replace("e-", "")
        r[1] = str(r[1]).replace("e-", "")
        r[2] = str(r[2]).replace("e-", "")
        ret_ang = f"ang({r[0]}, {r[1]}, {r[2]})"

        self.register_keyframe(frame_number, i, local_pos=ret_pos, scale=ret_scale, ang=ret_ang)

    def generate(self):
        self.push_code("#By K3CR4FT.:DLL - 2021")
        self.push_code("@name TEST")
        self.push_code("@persist BASE:entity")
        self.push_code("@persist FRAME_INDEX:number FRAMES:table")
        self.push_code("interval(1)")
        self.push_code("if(first()){")
        self.push_code("BASE = entity()")

        self.push_code("#Generating Holograms :")
        for h in self.holograms_init:
            holo_id = h['holo_id']
            model = h['model']
            color = h['color']
            self.push_code(f'#[ Holo {holo_id} ]# holoCreate({holo_id}) holoModel({holo_id}, "{model}") holoColor({holo_id}, {color})')

        self.push_code("\n#Adding Frames : ")

        self.push_code("FRAMES = table(")
        for i, e in enumerate(self.keyframes_table):
            self.e2_code += f"#[ FRAME {i} ]# table("
            content = self.keyframes_table[e]
            for j, frame in enumerate(content):
                comma = "" if j == len(content) - 1 else ","
                self.e2_code += f"{frame}{comma} "
            self.e2_code += ")"
            if i < len(self.keyframes_table) - 1: self.push_code(",")

        self.push_code(")")
        self.push_code("}")

        """
        function playFrame(FrameNumber:number){
    
            #We get the frame at the index
            local GFRAME = FRAMES[FrameNumber, table]
            
            #We get all the keys
            for(I = 1, GFRAME:count()){
                local Frame = GFRAME[I, table]
                local Id = Frame["id", number]
                printTable(Frame)
                holoPos(Id, BASE:toWorld(Frame["pos", vector] * 10))
                holoAng(Id, Frame["ang", angle])
                holoScaleUnits(Id, Frame["scale", vector] * 10 * 2)
            }
        }

        """
        self.push_code("#Playing Frames : ")
        self.push_code("function playFrame(FrameNumber:number){")
        self.push_code("local GFRAME = FRAMES[FrameNumber, table]")
        self.push_code("for(I = 1, GFRAME:count()){")
        self.push_code("local Frame = GFRAME[I, table]")
        self.push_code('local Id = Frame["id", number]')
        self.push_code('holoPos(Id, BASE:toWorld(Frame["pos", vector] * 10))')
        self.push_code('holoAng(Id, BASE:angles() + Frame["ang", angle])')
        self.push_code('holoScaleUnits(Id, Frame["scale", vector] * 10 * 2)')
        self.push_code("}}")
        self.push_code('timer("_", 0)')

        self.push_code('if(clk("_")){')
        self.push_code(f'playFrame(1 + (FRAME_INDEX % {len(self.keyframes_table)}))')
        self.push_code('FRAME_INDEX++')
        self.push_code('timer("_", 50)')
        self.push_code('}')


be = BE()
be.init_generation()
be.generate()

print(" ")
print(be.e2_code)

f = open("E:\\Program Files (x86)\\Steam\\steamapps\\common\\GarrysMod\\garrysmod\\data\\expression2\\TEST.txt", "w")
f.write(be.e2_code)
f.close()