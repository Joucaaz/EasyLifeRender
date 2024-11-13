# This file is part of Easy Life Render.
#
# Copyright (c) 2024 Joucaz
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


bl_info = {
    "name": "EasyLifeRender",
    "description": "Easy Life Render is a Blender addon that allows users to add lights and a camera around selected objects based on various presets",
    "author": "Joucaz",
    "version": (1, 1, 0),
    "blender": (2, 80, 0), 
    "location": "View3D > EasyLifeRender",
    "category": "Lighting"
}
import bpy
import math
import mathutils
from mathutils import Vector


class OBJECT_OT_add_lights(bpy.types.Operator):
    """Add lights around the selected object"""
    bl_idname = "object.add_lights"
    bl_label = "Add Lights"
    bl_options = {'REGISTER', 'UNDO'}
    
    bounding_cube_index = 1

    def execute(self, context):
        selected_objects = context.selected_objects
        preset = context.scene.my_properties.preset_enum_lights
        
        if preset in light_presets:
            light_settings = light_presets[preset]
        else:
            self.report({'WARNING'}, "Unknown preset")
            return {'CANCELLED'}
        
        if len(selected_objects) >= 1:
            bounding_cube = self.create_bounding_cube(selected_objects)            
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[bounding_cube.name].select_set(True)
            selected_objects = context.selected_objects
            self.add_lights_around_object(selected_objects[0], light_settings)
#        elif len(selected_objects) == 1:
#            self.add_lights_around_object(selected_objects[0], light_settings)
        else:
            self.report({'WARNING'}, "No object selected")
            return {'CANCELLED'}
    
        
        return {'FINISHED'}
    
#    def create_bounding_cube(self, objects):
#        min_x = min(obj.location.x - obj.dimensions.x * 0.5 for obj in objects)
#        max_x = max(obj.location.x + obj.dimensions.x * 0.5 for obj in objects)
#        min_y = min(obj.location.y - obj.dimensions.y * 0.5 for obj in objects)
#        max_y = max(obj.location.y + obj.dimensions.y * 0.5 for obj in objects)
#        min_z = min(obj.location.z - obj.dimensions.z * 0.5 for obj in objects)
#        max_z = max(obj.location.z + obj.dimensions.z * 0.5 for obj in objects)
#        
#        center = ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
#        dimensions = (max_x - min_x, max_y - min_y, max_z - min_z)
#        
#        base_name = f"Scene.{self.bounding_cube_index}"
#        self.bounding_cube_index += 1 
#                 
#        bpy.ops.mesh.primitive_cube_add(size=2, location=center)
#        bounding_cube = bpy.context.object
#        bounding_cube.name = base_name
#        bounding_cube.dimensions = dimensions
#        
#        bounding_cube.display_type = 'WIRE'
#        bounding_cube.hide_render = True
#        
#        return bounding_cube

    def create_bounding_cube(self, objects):
        # Initialise les valeurs min/max pour les coordonnées globales
        min_x, min_y, min_z = float('inf'), float('inf'), float('inf')
        max_x, max_y, max_z = float('-inf'), float('-inf'), float('-inf')
        
        # Parcourt chaque objet et ajuste les min/max selon la bounding box globale
        for obj in objects:
            # Récupère les coordonnées des coins de la bounding box dans le système de coordonnées global
            for corner in obj.bound_box:
                world_corner = obj.matrix_world @ Vector(corner)
                min_x = min(min_x, world_corner.x)
                max_x = max(max_x, world_corner.x)
                min_y = min(min_y, world_corner.y)
                max_y = max(max_y, world_corner.y)
                min_z = min(min_z, world_corner.z)
                max_z = max(max_z, world_corner.z)
        
        # Calcule le centre et les dimensions du bounding cube
        center = ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
        dimensions = (max_x - min_x, max_y - min_y, max_z - min_z)
        
        # Crée le cube de bounding avec les nouvelles dimensions et positionne au centre
        base_name = f"Scene.{self.bounding_cube_index}"
        self.bounding_cube_index += 1 

        bpy.ops.mesh.primitive_cube_add(size=2, location=center)
        bounding_cube = bpy.context.object
        bounding_cube.name = base_name
        bounding_cube.dimensions = dimensions
        
        # Définit le cube comme fil de fer et invisible au rendu
        bounding_cube.display_type = 'WIRE'
        bounding_cube.hide_render = True
        
        return bounding_cube
    
    def add_lights_around_object(self, obj, light_settings):
        collection_name = f"{obj.name}_Lights"
        obj_dimensions = obj.dimensions
        obj_location = obj.location
        
        for collection in bpy.data.collections:
                if obj.name in collection.objects:
                    collection_object = collection
        
        if collection_name in bpy.data.collections:
            light_collection = bpy.data.collections[collection_name]
            
            remove_collection_objects = True

            coll = bpy.data.collections.get(collection_name)

            if coll:
                if remove_collection_objects:
                    obs = [o for o in coll.objects if o.users == 1]
                    while obs:
                        bpy.data.objects.remove(obs.pop())

                bpy.data.collections.remove(coll)
        
        light_collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(light_collection)            
        
        if obj.name.startswith("Scene"):
            
            light_collection.objects.link(obj)
            try:
                collection_object.objects.unlink(obj)
            except Exception as e:
                bpy.context.scene.collection.objects.unlink(obj)
                
        
        max_dimension = max(obj.dimensions)  
        print(str(max_dimension))
        distance = max_dimension * 1.5 
        
        base_energy = light_settings["base_energy"]
        key_light_energy = base_energy * (max_dimension ** 2)
        fill_light_energy = key_light_energy * 0.5
        back_light_energy = key_light_energy * 0.25
        
        light_size = max_dimension * 0.7 

        key_light_pos = (
            obj_location.x + distance * math.cos(math.radians(45)),
            obj_location.y + distance * math.sin(math.radians(45)),
            obj_location.z + distance * 0.5
        )

        fill_light_pos = (
            obj_location.x + distance * math.cos(math.radians(-45)),
            obj_location.y + distance * math.sin(math.radians(-45)),
            obj_location.z + distance * 0.25
        )

        back_light_pos = (
            obj_location.x - distance * 1.5,
            obj_location.y,
            obj_location.z + distance * 0.5
        )
        
        camera_pos = (obj_location.x + distance * 1.5, obj_location.y + distance * math.sin(math.radians(45)), obj_location.z + distance)
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=camera_pos, rotation=(0, 0, 0))
        
        # Récupération explicite de l'objet de caméra ajouté
        camera = bpy.context.view_layer.objects.active  # Récupère l'objet actif ajouté
        camera.name = f"Camera_{obj.name}"
        bpy.context.scene.camera = camera

        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        direction = obj_location - camera.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()
        
        bpy.ops.view3d.camera_to_view_selected()
        
        light_collection.objects.link(camera)
        try:
            collection_object.objects.unlink(camera)
        except Exception as e:
            bpy.context.scene.collection.objects.unlink(camera)
        
        positions = [key_light_pos, fill_light_pos, back_light_pos]
        names = [f"KeyLight_{obj.name}", f"FillLight_{obj.name}", f"BackLight_{obj.name}"]
        energies = [key_light_energy, fill_light_energy, back_light_energy]
        
        for i, pos in enumerate(positions):
            bpy.ops.object.light_add(type='AREA', location=pos)
            light = bpy.context.object
            light.name = names[i]
            direction = obj_location - light.location
            rot_quat = direction.to_track_quat('-Z', 'Y')
            light.rotation_euler = rot_quat.to_euler()
            light.data.color = light_settings[names[i].split('_')[0]]['color']
            light.data.energy = energies[i]
            light.data.size = light_settings[names[i].split('_')[0]]['size']
            
            light_collection.objects.link(light)
            try:
                collection_object.objects.unlink(light)
            except Exception as e:
                bpy.context.scene.collection.objects.unlink(light)  
        
        obj.hide_viewport = True      

def update_key_light_prop(self, context):
    my_properties = context.scene.my_properties
    
    if context.scene.get("updating_property", False):
        return
    
    context.scene["updating_property"] = True
    my_properties.show_fill_light = False
    my_properties.show_back_light = False
    my_properties.show_key_light = True
    context.scene["updating_property"] = False

def update_fill_light_prop(self, context):
    my_properties = context.scene.my_properties
    
    if context.scene.get("updating_property", False):
        return
    
    context.scene["updating_property"] = True
    my_properties.show_key_light = False
    my_properties.show_back_light = False
    my_properties.show_fill_light = True
    context.scene["updating_property"] = False

def update_back_light_prop(self, context):
    my_properties = context.scene.my_properties
    
    if context.scene.get("updating_property", False):
        return
    
    context.scene["updating_property"] = True
    my_properties.show_fill_light = False
    my_properties.show_key_light = False
    my_properties.show_back_light = True
    context.scene["updating_property"] = False
    
def update_shadow_light(self, context):
    my_properties = context.scene.my_properties
    if my_properties.show_key_light:
        bpy.context.object.data.use_shadow = my_properties.shadow_key_light 
    elif my_properties.show_fill_light:
        bpy.context.object.data.use_shadow = my_properties.shadow_fill_light 
    elif my_properties.show_back_light:
        bpy.context.object.data.use_shadow = my_properties.shadow_back_light 

def draw_light_properties(layout, light, label, shadow):
    my_properties = bpy.context.scene.my_properties
    layout.label(text=f"{label} Properties:")
    layout.prop(light.data, "color")
    layout.prop(light.data, "energy")
    layout.prop(light.data, "size")
    use_shadow_value = bpy.context.object.data.use_shadow
    layout.prop(my_properties, f"{shadow}", text="Enable Shadow")

def draw_camera_properties(layout, camera):
    layout.label(text="Camera Properties:")
    layout.prop(camera.data, "clip_start")
    layout.prop(camera.data, "clip_end")

class OBJECT_PT_preset_lights_panel(bpy.types.Panel):
    """Panel to add lights"""
    bl_label = "Lights Preset"
    bl_idname = "OBJECT_PT_test_lights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EasyLifeRender'    
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        myProperties = scene.my_properties
        row = layout.row()  
        row.prop(myProperties, "preset_enum_lights")  
        row = layout.row()
        row.operator("wm.preset_operator")
        
class OBJECT_PT_add_lights_panel(bpy.types.Panel):
    """Panel to manage lights"""
    bl_label = "Change Lights Parameters"
    bl_idname = "OBJECT_PT_add_lights"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'EasyLifeRender'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        
        
        row.label(text="Choose a Lights Collection")
        selected_collection = bpy.context.collection
        selected_objects = bpy.context.selected_objects

        
        if selected_collection and not selected_objects:
            key_light = None
            fill_light = None
            back_light = None
            camera_collection = None
            
            for obj in selected_collection.objects:
                if obj.type == 'LIGHT':
                    if obj.name.startswith("KeyLight"):
                        key_light = obj
                    elif obj.name.startswith("FillLight"):
                        fill_light = obj
                    elif obj.name.startswith("BackLight"):
                        back_light = obj
                elif obj.type == 'CAMERA':
                    camera_collection = obj
            
            if key_light and fill_light and back_light:
#              
                my_properties = scene.my_properties
    
                row = layout.row(align=True)
                row.prop(my_properties, "show_key_light", text="Key Light", toggle=True)                
                row.prop(my_properties, "show_fill_light", text="Fill Light", toggle=True)
                row.prop(my_properties, "show_back_light", text="Back Light", toggle=True)

                if my_properties.show_key_light:
                    draw_light_properties(layout, key_light, "Key Light", "shadow_key_light")
                    
                if my_properties.show_fill_light:
                    draw_light_properties(layout, fill_light, "Fill Light", "shadow_fill_light")                    
                    fill_light.data.use_shadow = my_properties.shadow_fill_light
                
                if my_properties.show_back_light:
                    draw_light_properties(layout, back_light, "Back Light", "shadow_back_light")
                    back_light.data.use_shadow = my_properties.shadow_back_light
                
class EasyLifeLights_OT_PresetOperator(bpy.types.Operator):
    bl_label = "Add Preset Lights"
    bl_idname = "wm.preset_operator"
    
    def execute(self, context):
        scene = context.scene
        myProperties = scene.my_properties
        
        
        if myProperties.preset_enum_lights == "Basic3Point":
            bpy.ops.object.add_lights('INVOKE_DEFAULT')
        elif myProperties.preset_enum_lights == "French":
            bpy.ops.object.add_lights('INVOKE_DEFAULT')
        elif myProperties.preset_enum_lights == "Tamised":
            bpy.ops.object.add_lights('INVOKE_DEFAULT')
        elif myProperties.preset_enum_lights == "Caliente":
            bpy.ops.object.add_lights('INVOKE_DEFAULT')
        elif myProperties.preset_enum_lights == "SambaDoBrazil":
            bpy.ops.object.add_lights('INVOKE_DEFAULT')
            
        
        return {'FINISHED'}    
    
class EasyLifeRender_OT_KeyLIghtOperator(bpy.types.Operator):
    bl_label = "KeyLight"
    bl_idname = "wm.key_light_operator"
    
    def execute(self, context):
        scene = context.scene
        myProperties = scene.my_properties
        draw_light_properties(layout, key_light, "Key Light")
            
        
        return {'FINISHED'}  
                

class MyProperties(bpy.types.PropertyGroup):
    
    show_key_light: bpy.props.BoolProperty(
        name="Show Key Light",
        description="Toggle visibility of the key light",
        default=False,
        update=update_key_light_prop
    )
    
    show_fill_light: bpy.props.BoolProperty(
        name="Show Fill Light",
        description="Toggle visibility of the fill light",
        default=False,
        update=update_fill_light_prop
    )
    
    show_back_light: bpy.props.BoolProperty(
        name="Show Back Light",
        description="Toggle visibility of the back light",
        default=False,
        update=update_back_light_prop
    )
    
    shadow_key_light: bpy.props.BoolProperty(
        name="Shadow of the Key Light",
        description="Toggle shadow of the key light",
        default=True,
        update=update_shadow_light
    )
    
    shadow_fill_light: bpy.props.BoolProperty(
        name="Shadow of the Fill Light",
        description="Toggle shadow of the fill light",
        default=True,
        update=update_shadow_light
    )
    
    shadow_back_light: bpy.props.BoolProperty(
        name="Shadow of the Back Light",
        description="Toggle shadow of the back light",
        default=True,
        update=update_shadow_light
    )
    
    preset_enum_lights : bpy.props.EnumProperty(
        name = "Preset",
        description = "Select a preset Light to apply to your objects",
        items = [
            ('Basic3Point', "Basic 3 point Lights", "Add basic 3 point lights"),
            ('Tamised', "Tamised Lights", "Add 3 point lights with tamised energy"),
            ('French', "French Lights", "Add normal 3 point lights with french color"),
            ('Caliente', "Caliente Lights", "Add 3 point lights with caliente color"),
            ('SambaDoBrazil', "Samba Do Brazil Lights", "Add 3 point lights with brazil color")        
        ]
    )


light_presets = {
    "Basic3Point": {
        "base_energy": 30,
        "KeyLight": {"color": (1, 1, 1), "size": 5},
        "FillLight": {"color": (1, 1, 1), "size": 5},
        "BackLight": {"color": (1, 1, 1), "size": 5},
    },
    "French": {
        "base_energy": 30,
        "KeyLight": {"color": (0.91, 0.000317968, 0), "size": 5},
        "FillLight": {"color": (0.0035659, 0.00158721, 0.91), "size": 5},
        "BackLight": {"color": (1, 1, 1), "size": 5},
    },
    "Tamised": {
        "base_energy": 5,
        "KeyLight": {"color": (1, 1, 1), "size": 5},
        "FillLight": {"color": (1, 1, 1), "size": 5},
        "BackLight": {"color": (1, 1, 1), "size": 5},
    },
    "Caliente": {
        "base_energy": 30,
        "KeyLight": {"color": (1, 0.255307, 0), "size": 5},
        "FillLight": {"color": (1, 0, 0.00404397), "size": 5},
        "BackLight": {"color": (1, 0.848015, 0), "size": 5},
    },
    "SambaDoBrazil": {
        "base_energy": 30,
        "KeyLight": {"color": (0.963882, 0.660907, 0), "size": 5},
        "FillLight": {"color": (0.0387532, 0.471952, 0), "size": 5},
        "BackLight": {"color": (0.0268262, 0.019082, 0.571701), "size": 5},
    },
    
}

classes = [MyProperties, OBJECT_PT_preset_lights_panel, OBJECT_OT_add_lights, OBJECT_PT_add_lights_panel, EasyLifeLights_OT_PresetOperator]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        if not hasattr(bpy.types.Scene, "my_properties"):
            bpy.types.Scene.my_properties = bpy.props.PointerProperty(type=MyProperties)
        else:
            print("Propriété 'my_properties' déjà existante.")
        
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        del bpy.types.Scene.my_properties
    
if __name__ == "__main__":
    register()
