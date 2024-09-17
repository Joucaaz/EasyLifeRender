# This file is part of Easy Life Render.
#
# Copyright (c) 2024 Joucaz
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT


bl_info = {
    "name": "Easy Life Render",
    "description": "Easy Life Render is a Blender addon that allows users to add lights and a camera around selected objects based on various presets",
    "author": "Joucaz",
    "version": (1, 0, 0),
    "blender": (4, 20, 0), 
    "location": "View3D > EasyLifeRender",
    "warning": "",
    "category": "Lighting"
}

import bpy
import math
import mathutils


class OBJECT_OT_add_lights(bpy.types.Operator):
    """Ajouter des lumières autour de l'objet sélectionné"""
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
            self.report({'WARNING'}, "Préréglage inconnu")
            return {'CANCELLED'}
        
        if len(selected_objects) > 1:
            # Créer un cube englobant tous les objets sélectionnés
            bounding_cube = self.create_bounding_cube(selected_objects)
            bpy.ops.object.select_all(action='DESELECT')
            bpy.data.objects[bounding_cube.name].select_set(True)
            selected_objects = context.selected_objects
            self.add_lights_around_object(selected_objects[0], light_settings)
#            bpy.data.objects.remove(bounding_cube, do_unlink=True)
        elif len(selected_objects) == 1:
            self.add_lights_around_object(selected_objects[0], light_settings)
        else:
            self.report({'WARNING'}, "Aucun objet sélectionné")
            return {'CANCELLED'}
    
        
        return {'FINISHED'}
    
    def create_bounding_cube(self, objects):
        # Créer un cube englobant tous les objets sélectionnés
        min_x = min(obj.location.x - obj.dimensions.x * 0.5 for obj in objects)
        max_x = max(obj.location.x + obj.dimensions.x * 0.5 for obj in objects)
        min_y = min(obj.location.y - obj.dimensions.y * 0.5 for obj in objects)
        max_y = max(obj.location.y + obj.dimensions.y * 0.5 for obj in objects)
        min_z = min(obj.location.z - obj.dimensions.z * 0.5 for obj in objects)
        max_z = max(obj.location.z + obj.dimensions.z * 0.5 for obj in objects)
        
        center = ((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2)
        dimensions = (max_x - min_x, max_y - min_y, max_z - min_z)
        
#        base_name = f"Scene.{bpy.context.scene.my_properties.bounding_cube_index}"
#        bpy.context.scene.my_properties.bounding_cube_index += 1
        
        base_name = f"Scene.{self.bounding_cube_index}"
        self.bounding_cube_index += 1 
                 
        bpy.ops.mesh.primitive_cube_add(size=2, location=center)
        bounding_cube = bpy.context.object
        bounding_cube.name = base_name
        bounding_cube.dimensions = dimensions
        
        bounding_cube.display_type = 'WIRE'
        bounding_cube.hide_render = True
        
        return bounding_cube
    
    def add_lights_around_object(self, obj, light_settings):
        # Nom de la collection
        collection_name = f"{obj.name}_Lights"
        obj_dimensions = obj.dimensions
        obj_location = obj.location
    
        
        
        if collection_name in bpy.data.collections:
            light_collection = bpy.data.collections[collection_name]
#            for obj in list(light_collection.objects):
#                bpy.data.objects.remove(obj, do_unlink=True)
            
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
            bpy.context.scene.collection.objects.unlink(obj)
        
         # Calculer les positions des lumières autour de l'objet
        print(str(obj_location))
        max_dimension = max(obj.dimensions)  # Utiliser la plus grande dimension pour calculer la distance
        print(str(max_dimension))
        distance = max_dimension * 1.5  # Distance proportionnelle à la taille de l'objet
        
        # Calculer les énergies et tailles en fonction de la dimension
        base_energy = light_settings["base_energy"]
        key_light_energy = base_energy * (max_dimension ** 2)
        fill_light_energy = key_light_energy * 0.5
        back_light_energy = key_light_energy * 0.25
        
        light_size = max_dimension * 0.7  # La taille de la lumière est proportionnelle à la dimension de l'objet

        # Positions des lumières en fonction des angles et hauteurs spécifiés
        key_light_pos = (
            obj_location.x + distance * math.cos(math.radians(45)),
            obj_location.y + distance * math.sin(math.radians(45)),
            obj_location.z + distance * 0.5  # Key Light en hauteur
        )

        fill_light_pos = (
            obj_location.x + distance * math.cos(math.radians(-45)),
            obj_location.y + distance * math.sin(math.radians(-45)),
            obj_location.z + distance * 0.25  # Fill Light plus bas
        )

        back_light_pos = (
            obj_location.x - distance * 1.5,
            obj_location.y,
            obj_location.z + distance * 0.5  # Back Light à la même hauteur que la Key Light
        )
        
        camera_pos = (obj_location.x + distance * 1.5, obj_location.y + distance * math.sin(math.radians(45)), obj_location.z + distance)
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=camera_pos, rotation=(0, 0, 0))
        camera = bpy.context.object
        camera.name = f"Camera_{obj.name}"
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        direction = obj_location - camera.location
        rot_quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = rot_quat.to_euler()
#        bounding_box_diagonal = (obj_dimensions.x**2 + obj_dimensions.y**2 + obj_dimensions.z**2)**0.5
#        camera.data.lens = bounding_box_diagonal * 5
        
        bpy.ops.view3d.camera_to_view_selected()

        # Appliquer un décalage à la caméra
#        offset_vector = mathutils.Vector((-5, 5, 5))  # Définir un décalage (arrière et un peu en hauteur)
#        camera.location += offset_vector
        light_collection.objects.link(camera)
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
                    
            # Ajouter la lumière à la collection
            light_collection.objects.link(light)
            bpy.context.scene.collection.objects.unlink(light)  



def update_key_light_prop(self, context):
    my_properties = context.scene.my_properties
    
    if context.scene.get("updating_property", False):
        return
    
    print("Test 1 ---------------")
    context.scene["updating_property"] = True
    my_properties.show_fill_light = False
    my_properties.show_back_light = False
    my_properties.show_key_light = True
    context.scene["updating_property"] = False

def update_fill_light_prop(self, context):
    my_properties = context.scene.my_properties
    
    if context.scene.get("updating_property", False):
        return
    
    print("Test 2 ---------------")
    context.scene["updating_property"] = True
    my_properties.show_key_light = False
    my_properties.show_back_light = False
    my_properties.show_fill_light = True
    context.scene["updating_property"] = False

def update_back_light_prop(self, context):
    my_properties = context.scene.my_properties
    
    if context.scene.get("updating_property", False):
        return
    
    print("Test 3 ---------------")
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
#    if use_shadow_value:
#        layout.prop(my_properties, "shadow_key_light", text="Enable Shadow")
#    else:
#        layout.prop(my_properties, "shadow_key_light", text="Enable Shadow", invert_checkbox=True)

#    layout.prop()

def draw_camera_properties(layout, camera):
    layout.label(text="Camera Properties:")
    layout.prop(camera.data, "clip_start")
    layout.prop(camera.data, "clip_end")

#    layout.prop(camera.data, "dof")


class OBJECT_PT_preset_lights_panel(bpy.types.Panel):
    """Panneau pour ajouter les lumières"""
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
    """Panneau pour ajouter les lumières"""
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
            # Vérifier si la collection contient exactement trois lumières avec les noms spécifiques
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
                my_properties = scene.my_properties  # Accès à MyProperties depuis la scène
    
                row = layout.row(align=True)
                row.prop(my_properties, "show_key_light", text="Key Light", toggle=True)                
                row.prop(my_properties, "show_fill_light", text="Fill Light", toggle=True)
                row.prop(my_properties, "show_back_light", text="Back Light", toggle=True)

                if my_properties.show_key_light:
                    draw_light_properties(layout, key_light, "Key Light", "shadow_key_light")
                    
                if my_properties.show_fill_light:
                    draw_light_properties(layout, fill_light, "Fill Light", "shadow_fill_light")                    
                    fill_light.data.use_shadow = my_properties.shadow_fill_light
#                    layout.prop(my_properties, "shadow_fill_light",text="Enable Shadow")
                
                if my_properties.show_back_light:
                    draw_light_properties(layout, back_light, "Back Light", "shadow_back_light")
                    back_light.data.use_shadow = my_properties.shadow_back_light
                    
#            if camera_collection:
#                draw_camera_properties(layout, camera_collection)
                
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
        description = "Select a preset Light to apply to your object or scene",
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
        bpy.types.Scene.my_properties = bpy.props.PointerProperty(type = MyProperties)
        
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        del bpy.types.Scene.my_properties
    
if __name__ == "__main__":
    register()
