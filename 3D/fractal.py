bl_info = {
    "name": "Fractal",
    "description": "Creates an approximation of a fractal from a source object",
    "author": "Hong Son Ngo",
    "version": (1, 0, 0),
    "blender": (2, 93, 5),
    "location": "View3D > Object > Fractal",
    "warning": "Computers with lower specifications should not generate fractals above the depth of recursion of 4",
    "wiki_url": "https://gitlab.fit.cvut.cz/BI-PGA/b211/ngohongs/tree/master/3D",
    "category": "Object"
}

import bpy

class Fractal(bpy.types.Operator):
    """
    Creates an approximation of a fractal from a source object.
    """                                 

    bl_idname = "object.fractal"      
    bl_label = "Fractal"             
    bl_options = {'REGISTER', 'UNDO'}   
    
    
    iteration : bpy.props.IntProperty(
        name = 'Iteration',
        description = 'Upper limit of the recursion',
        default = 1, min = 1, step = 1,
        options={'SKIP_SAVE'}
    )

    factor : bpy.props.FloatProperty(
        name = 'Factor',
        description = 'Scale factor of the next generated object',
        default = 0.4, min = 0.0, max = 1.0,
        options={'SKIP_SAVE'}
    )
    
    distance : bpy.props.FloatProperty(
        name = 'Distance',
        description = 'Distance of the newly generated object from its source',
        default = 0.0, min = 0.0,
        options={'SKIP_SAVE'}
    )
    
    
    def init(self, context):
        self.context = context
        self.src_objs = context.selected_objects
        
        
        if len(self.src_objs) < 1:
            self.report({'WARNING'}, 'No object was selected! Select only one object.')
            return False
        
        if len(self.src_objs) > 1:
            self.report({'WARNING'}, 'More than one object were selected! Select only one object.')
            return False
        
        self.collection = bpy.data.collections.new('Fractal')
        self.context.scene.collection.children.link(self.collection)
        
        self.orig_obj = self.src_objs[0]
        
        return True
    
    
    def join_objects(self):
        print('Fractalizing...joining')
        
        bpy.ops.object.select_all(action='DESELECT')
        
        self.orig_obj.select_set(True)
        for obj in self.collection.all_objects:
            obj.select_set(True)
    
        self.context.view_layer.objects.active = self.orig_obj
        bpy.ops.object.join()
        
        self.context.scene.collection.children.unlink(self.collection)
        
        
    def fractalize(self):
        new_objs = []
        
        print('Fractalizing...0%')
        for i in range(self.iteration): 
            for src_obj in self.src_objs:
                src_loc = src_obj.location
                
                mesh = src_obj.data
                vertices = mesh.vertices
                verts_world = (src_obj.matrix_world @ v.co for v in vertices.values())
                
                for coord in verts_world:
                    cpy_obj = src_obj.copy()
                    cpy_obj.data = src_obj.data.copy()
                    cpy_obj.location = coord + self.distance * (coord - src_loc)
                    cpy_obj.scale = self.factor * src_obj.scale
                    self.collection.objects.link(cpy_obj)
                    new_objs.append(cpy_obj)
            
                src_obj.select_set(False) 
                
            bpy.context.view_layer.update()
            self.src_objs = self.context.selected_objects
            print('Fractalizing...' + '%.1f%%' % (100 * float(i + 1)/self.iteration))   
    
    
    def execute(self, context): 
        if not self.init(context):
            return {'CANCELLED'}
        
        self.fractalize()
        
        self.join_objects()
        
        print('Fractalizing...finished')
        
        return {'FINISHED'}           


def menu_func(self, context):
    self.layout.operator(Fractal.bl_idname)


def register():
    bpy.utils.register_class(Fractal)
    bpy.types.VIEW3D_MT_object.append(menu_func)  # Adds the new operator to an existing menu.


def unregister():
    bpy.utils.unregister_class(Fractal)


if __name__ == "__main__":
    register()