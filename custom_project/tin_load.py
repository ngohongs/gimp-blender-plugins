bl_info = {
    "name": "TIN mesh (DMR 5G)",
    "description": "Loads data from file in TIN format (triangulated irregular network) and creates mesh according to the data. Made specifically for DMR 5G from cuzk.cz",
    "author": "Hong Son Ngo",
    "version": (1, 0, 0),
    "blender": (2, 93, 5),
    "location": "Panel in Layout window",
    "warning": "BlenderGIS dependent",
    "wiki_url": "https://gitlab.fit.cvut.cz/sukkryst/pevnosti",
    "category": "Add Mesh"
}

import os 

import bpy
import bpy_extras

class TINFile(bpy.types.PropertyGroup):
    """File representation in TIN List"""   
    filename : bpy.props.StringProperty(name= 'Filename')
        
    abspath : bpy.props.StringProperty(name= 'Absolute path')

class LIST_OT_AddTINFile(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """Add a new TIN file to the list."""

    bl_idname = "tin_list.add_file"
    bl_label = "Add new TIN file to TIN list"

    files: bpy.props.CollectionProperty(
            type=bpy.types.OperatorFileListElement,
            options={'HIDDEN', 'SKIP_SAVE'},
        )
        
    def execute(self, context):
        for file in self.files:
            dirname = os.path.dirname(self.filepath)
            filename = file.name
            abspath = os.path.join(dirname, filename)
            
            item = context.scene.tin_list.add()
            item.filename = filename
            item.abspath = abspath

        return{'FINISHED'}
    
class LIST_OT_RemoveTINFile(bpy.types.Operator):
    """Delete the selected item from the list."""

    bl_idname = "tin_list.remove_file"
    bl_label = "Remove selected TIN file"

    @classmethod
    def poll(cls, context):
        return context.scene.tin_list

    def execute(self, context):
        tin_list = context.scene.tin_list
        index = context.scene.tin_index
        tin_list.remove(index)
        context.scene.tin_index = min(max(0, index - 1), len(tin_list) - 1)

        return{'FINISHED'}
    

class LIST_UL_TINFileList(bpy.types.UIList):
    """TIN List"""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):

        custom_icon = 'MESH_DATA'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.filename, icon = custom_icon)

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon = custom_icon)

class OBJECT_OT_TINMeshCreate(bpy.types.Operator):
    """
    Loads data in TIN format and creates a mesh from it.
    """                                
    
    bl_idname = "object.tin_mesh"        
    bl_label = "Create a TIN mesh"       
    bl_options = {'REGISTER', 'UNDO'} 
    
    @classmethod
    def poll(cls, context):
        return context.scene.tin_list
    
    def execute(self, context):
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode = 'OBJECT') 
              
        vertices = []
        edges = []
        faces = []

        for file in context.scene.tin_list:
            abspath = file.abspath
            with open(abspath, 'r') as f:
                for line in f:
                    vertices += [tuple([float(x) for x in line.split()])]
                    
                    
        mesh = bpy.data.meshes.new('Mesh')
        mesh.from_pydata(vertices, edges, faces)
        mesh.update()  
        object = bpy.data.objects.new('Point cloud', mesh)
        bpy.context.collection.objects.link(object)     
        
        bpy.ops.object.select_all(action='DESELECT')
        object.select_set(True)
        bpy.ops.tesselation.delaunay()
        
        mesh = bpy.context.active_object
        
        bpy.ops.object.select_all(action='DESELECT')
        object.select_set(True)
        bpy.ops.object.delete() 
    

        bpy.ops.object.select_all(action='DESELECT')
        mesh.select_set(True)

        # Needs to be recentered twice else the object is not centered
        for i in range(2):
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='MEDIAN')
            bpy.context.object.location = [0, 0, 0]     
        
        return {'FINISHED'}           

class OBJECT_PT_ZTopUVMap(bpy.types.Operator):
    """
    Map UV coordinates from top view projection.
    """
    bl_idname = 'object.ztop_uvmap'      
    bl_label = 'Project UV from top view'       
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        import bmesh
        import numpy as np
        from mathutils import Matrix, Vector
        object = context.selected_objects[0]
        mesh = object.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        x, y, z = np.array([v.co for v in bm.verts]).T
        S = Matrix.Diagonal(
            ( 
                1 / (x.max() - x.min()),
                1 / (y.max() - y.min())
            )
          )
        print(x.min(), x.max(), y.min(), y.max(),S)
        uv_layer = bm.loops.layers.uv.verify()
        
        offset = Vector((0.0,0.0))
        if x.min() != 0.0:
            offset[0] = -x.min()
        if y.min() != 0.0:
            offset[1] = -y.min()
            
        for face in bm.faces:
            for loop in face.loops:
                loop_uv = loop[uv_layer]
                # use xy position of the vertex as a uv coordinate
                loop_uv.uv = S @ (loop.vert.co.xy + offset)
        bm.to_mesh(mesh)
        mesh.update()
        
        return {'FINISHED'}
    
class OBJECT_PT_TINTex(bpy.types.Operator, bpy_extras.io_utils.ImportHelper):
    """
    Apply texture from top view.
    """
    bl_idname = 'object.tin_tex'        
    bl_label = 'Project texture'       
    bl_options = {'REGISTER', 'UNDO'} 
    
    def execute(self, context):
        import mathutils
        import math
        if len(context.selected_objects) != 1:
            self.report({'WARNING'}, 'Select one TIN mesh')
            return {'CANCELLED'}
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')   
            
        object = context.selected_objects[0]
        abspath = self.properties.filepath
        
        bpy.ops.object.ztop_uvmap()
    
        mat = bpy.data.materials.new(name="Texture")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()

        node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
        node_principled.location = 0,0

        node_tex = nodes.new('ShaderNodeTexImage')
        node_tex.image = bpy.data.images.load(abspath)
        node_tex.location = -400,0

        node_output = nodes.new(type='ShaderNodeOutputMaterial')   
        node_output.location = 400,0

        links = mat.node_tree.links
        link = links.new(node_tex.outputs["Color"], node_principled.inputs["Base Color"])
        link = links.new(node_principled.outputs["BSDF"], node_output.inputs["Surface"])
        
        if object.data.materials:
            object.data.materials[0] = mat
        else:
            object.data.materials.append(mat)
        
        return {'FINISHED'}

    
    
class OBJECT_PT_TINMeshPanel(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TIN Mesh'
    bl_label = 'Load'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.template_list('LIST_UL_TINFileList', 'TINFileList', scene, 'tin_list', scene, 'tin_index')
        
        row = layout.row(align = True)
        row.operator("tin_list.add_file", text = 'Add')
        row.operator("tin_list.remove_file", text = 'Remove')
        
        row = layout.row(align = True)
        row.operator("object.tin_mesh")
        
        row = layout.row(align = True)
        row.operator("object.tin_tex")
        
    
classes = [
            LIST_OT_AddTINFile, LIST_OT_RemoveTINFile, LIST_UL_TINFileList, TINFile, 
            OBJECT_OT_TINMeshCreate, OBJECT_PT_ZTopUVMap, OBJECT_PT_TINTex, OBJECT_PT_TINMeshPanel
          ]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.tin_list = bpy.props.CollectionProperty(type = TINFile)
    bpy.types.Scene.tin_index = bpy.props.IntProperty(default = 0)
   
def unregister():
    del bpy.types.Scene.tin_list
    del bpy.types.Scene.tin_index
    for cls in classes:
        bpy.utils.unregister_class(cls)
    

if __name__ == "__main__":
    register()