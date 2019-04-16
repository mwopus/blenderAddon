import bpy, time
from math import *
from mathutils import Vector
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        FloatVectorProperty,
        IntProperty,
        IntVectorProperty,
        StringProperty,
        PointerProperty
        )

def addObject( obj ):
    bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)

def activeObject( obj ):
    bpy.context.view_layer.objects.active = obj

def copyObject(obj, sameData = False):
    newobj = obj.copy()
    if not sameData:
        newobj.data = obj.data.copy()
        newobj.animation_data_clear()
    return newobj

def focusObject(obj):
    # unselect all of object, and then can join my own object
    for obj in bpy.context.view_layer.objects:
        obj.select_set(False)
    obj.select_set(True)
    activeObject(obj)

class vic_procedural_stair_save(bpy.types.Operator):
    bl_idname = 'vic.vic_procedural_stair_save'
    bl_label = 'Collapse Mesh'
    bl_description = ''

    data = StringProperty()

    def execute(self, context):

        # wallName = ''
        # try:
        #     wallName = bpy.context.scene['cwn']
        #     #wallName = eval(self.data)[0]
        # except:
        #     print("not have myname")
        
        # print( 'select_name:', wallName )
        # if wallName != '':
        #     objs = []
        #     for b in bpy.data.objects:
        #         find_str = b.name.find( wallName )
        #         print( 'find_str:', find_str )
        #         b.select_set( False )
        #         if find_str != -1:
        #             b.hide_viewport = False
        #             b.select_set( True )
        #             objs.append(b)
        #             print("add")
        #     print( len(objs))
        #     if len(objs) > 0:
        #         activeObject(objs[0])
        #         bpy.ops.object.join()

        return {'FINISHED'}

class vic_procedural_stair(bpy.types.Operator):
    bl_idname = 'vic.vic_procedural_stair'
    bl_label = 'Create Stair'
    bl_description = ''
    bl_options = {'REGISTER', 'UNDO'}

    width:FloatProperty(
        name='Width',
        min=1.0,
        default=3.0
    )

    height:FloatProperty(
        name='Height',
        min=1.0,
        default=5.0
    )

    wallHeight:FloatProperty(
        name='Wall Height',
        min=0.0,
        default=1.0
    )

    wallOffsetY:FloatProperty(
        name='Wall OffsetY',
        default=0.0
    )

    wallUvCenter:FloatProperty(
        name='Wall UV Center',
        min=0.0,
        max=1.0,
        default=.5
    )

    wallUvScaleX:FloatProperty(
        name='Wall UV Scale X',
        default=1.0
    )

    wallSideUvScale:FloatProperty(
        name='Wall Side UV Scale',
        default=1.0
    )

    count:IntProperty(
        name='Step Count',
        min=1,
        max=50,
        default=10
    )

    stepDepth:FloatProperty(
        name='Step Depth',
        min=.1,
        default=1.
    )

    showWall:BoolProperty(
        name='Show Wall',
        default=True
    )

    editMode:BoolProperty(
        name='Edit Mode',
        default=True,
        description='Turn off and press [Create Stair] again to get result mesh!'
    )

    wallMesh:StringProperty(
        name='Pick Mesh',
        description='DO NOT Pick Self!',
        default=''
    )

    # def scene_mychosenobject_poll(self, object):
    #     return object.type == 'CURVE'

    # wallMeshj = bpy.props.PointerProperty(
    #     type=bpy.types.Object,
    #     poll=scene_mychosenobject_poll
    # )

    def addUV(self, line, offset, uvs, scale=1):
        anotherLine = []
        for v in line:
            offsetVert = (  v[0] + offset[0],
                            v[1] + offset[1])
            anotherLine.append(offsetVert)
        line.extend(anotherLine)

        for v in line:
            uvs.append(
                (
                    v[0] * scale,
                    v[1] * scale
                )
            )

    # 給定一條綫上的點，再給定一個偏移向量，用程式產生偏移過後的第二條綫段的點
    # 用兩條綫上的點來產生面
    def addVertexAndFaces(self, line, offset, matId, verts, faces, matIds, flip = False, close = False):
        anotherLine = []
        startId = len(verts)
        for i, v in enumerate(line):
            offsetVert = (  v[0] + offset[0],
                            v[1] + offset[1],
                            v[2] + offset[2])
            anotherLine.append(offsetVert)

            # 收集面id
            v1 = startId+i
            v2 = v1+len(line)
            v3 = v2+1
            v4 = v1+1

            isLastFace = (i == len(line)-1)
            if isLastFace:
                if close:
                    if flip:
                        f = (v1,startId,startId+len(line),v2)
                    else:
                        f = (v1,v2,startId+len(line),startId)
            else:
                if flip:
                    f = (v1, v4, v3, v2)
                else:
                    f = (v1, v2, v3, v4)
            faces.append(f)
            matIds.append(matId)

        line.extend(anotherLine)
        verts.extend(line)

    def createOneWall(self, mesh, scaleFactor, tanRadian, startPos, wallPos, offsetY):
        for m in mesh.data.polygons:
            vs = []
            currentVertexCount = len(self.verts)
            for vid in m.vertices:
                vs.append(vid + currentVertexCount)
            self.faces.append(tuple(vs))
        
        for vid,v in enumerate(mesh.data.vertices):
            pos = v.co
            newpos = (
                pos.x * scaleFactor + wallPos.x + startPos.x, 
                pos.y + wallPos.y + startPos.y + offsetY, 
                pos.z + tanRadian * (pos.x * scaleFactor) + wallPos.z + startPos.z + self.wallHeight
            )
            self.verts.append( newpos )

    def addMaterial(self, name):
        if not name in bpy.data.materials:
            bpy.data.materials.new(name=name)

    def assignMaterial(self, obj):
        self.addMaterial('StairMaterial')
        self.addMaterial('StairSideMaterial')

        obj.data.materials.append(bpy.data.materials.get("StairMaterial"))
        obj.data.materials.append(bpy.data.materials.get("StairSideMaterial"))
        obj.data.uv_layers.new()

    def createWall(self, mesh):
        stepHeight = self.height / self.count
        totalLength = self.count * self.stepDepth
        startPos = Vector((self.stepDepth / 2, 0, stepHeight))
        endPos = Vector((totalLength - self.stepDepth / 2, 0, self.height))
        connect = endPos - startPos

        count = round(connect.x / mesh.dimensions.x)
        targetWidth = connect.x / count
        scaleFactor = targetWidth / mesh.dimensions.x

        wallSingle = connect / count
        radian = Vector((1,0,0)).angle(connect.normalized())
        tanRadian = tan(radian)

        #create mesh in the same object
        # for i in range(count):
        #     wallPos = wallSingle * (i + .5)
        #     self.createOneWall(mesh, scaleFactor, tanRadian, startPos, wallPos, self.width/2-self.wallOffsetY)
        #     self.createOneWall(mesh, scaleFactor, tanRadian, startPos, wallPos, -self.width/2+self.wallOffsetY)

        # create mesh for every wall
        wallPrototype = copyObject(mesh)
        for v in wallPrototype.data.vertices:
            pos = v.co
            v.co = (
                pos.x * scaleFactor, 
                pos.y, 
                pos.z + tanRadian * (pos.x * scaleFactor)
            )

        wallObj = []
        for i in range(count):
            wallPos = wallSingle * (i + .5)
            cloneWall = copyObject(wallPrototype, True)
            cloneWall.location.x = wallPos.x + startPos.x
            cloneWall.location.y = wallPos.y + startPos.y + self.width/2-self.wallOffsetY
            cloneWall.location.z = wallPos.z + startPos.z + self.wallHeight
            addObject(cloneWall)
            wallObj.append(cloneWall)

            cloneWall = copyObject(wallPrototype, True)
            cloneWall.location.x = wallPos.x + startPos.x
            cloneWall.location.y = wallPos.y + startPos.y + -self.width/2+self.wallOffsetY
            cloneWall.location.z = wallPos.z + startPos.z + self.wallHeight
            addObject(cloneWall)
            wallObj.append(cloneWall)

        bpy.data.objects.remove(wallPrototype, do_unlink=True)

        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)
        for wall in wallObj:
            wall.select_set(True)
        self.startObject.select_set(True)
        activeObject(self.startObject)

        # 因爲不能動態join，所以只能利用打開這個功能時的預設值來決定要不要join
        if not self.editMode:
            bpy.ops.object.join()

        # 好像沒辦法動態join
        # for obj in bpy.context.view_layer.objects:
        #     obj.select_set(False)
        # for wall in wallObj:
        #     wall.select_set(True)
        # self.startObject.select_set(True)
        # activeObject(self.startObject)
        # bpy.ops.object.join()

    def execute(self, context):
        self.verts = []
        self.faces = []
        self.uvs = []
        self.matIds = []

        # unselect all of object, and then can join my own object
        for obj in bpy.context.view_layer.objects:
            obj.select_set(False)

        x = self.width / 2
        stepHeight = self.height / self.count
        stepDepth = self.stepDepth

        line = []
        uv = []
        for i in range(self.count):
            line.append((i*stepDepth,-x,i*stepHeight))
            line.append((i*stepDepth,-x,i*stepHeight+stepHeight))
            line.append((i*stepDepth+stepDepth,-x,i*stepHeight+stepHeight))

            uv.append((0,0))
            uv.append((0,self.wallUvCenter))
            uv.append((0,1))

        lastVertex = line[len(line)-1]

        # 階梯的點及uv
        self.addVertexAndFaces(line, (0, self.width, 0), 0, self.verts, self.faces, self.matIds, flip=True)
        self.addUV(uv, (self.wallUvScaleX,0), self.uvs)

        # 背面的點及uv
        self.addVertexAndFaces([lastVertex, (lastVertex[0],lastVertex[1],0)], (0, self.width, 0), 1, self.verts, self.faces, self.matIds, flip=True)
        self.addUV([(0,lastVertex[2]),(0,0)], (self.width,0), self.uvs, self.wallSideUvScale)

        for i in range(self.count):
            self.addVertexAndFaces([
                (i*stepDepth,-x, i*stepHeight+stepHeight),
                (i*stepDepth,-x,0),
                (i*stepDepth,x,0),
                (i*stepDepth,x,i*stepHeight+stepHeight)
                ], (stepDepth, 0, 0), 1, self.verts, self.faces, self.matIds, flip=True)
            self.addUV([
                (i*stepDepth,i*stepHeight+stepHeight),
                (i*stepDepth,0),
                (i*stepDepth,0),
                (i*stepDepth,i*stepHeight+stepHeight)
            ], (stepDepth,0), self.uvs, self.wallSideUvScale)
        
        mesh = bpy.data.meshes.new("Stair")
        obj = bpy.data.objects.new("Stair", mesh)
        self.startObject = obj
        mesh.from_pydata(self.verts, [], self.faces)
        addObject(obj)

        self.assignMaterial(obj)

        # assign uv
        for i, face in enumerate(obj.data.polygons):
            for vert_idx, loop_idx in zip(face.vertices, face.loop_indices):
                obj.data.uv_layers.active.data[loop_idx].uv = self.uvs[vert_idx]
            face.material_index = self.matIds[i]
            
        # check the name of object in the scene! if not, set value to empty
        try:
            bpy.context.view_layer.objects[self.wallMesh]
        except:
            self.wallMesh = ''
        meshName = self.wallMesh
        if (self.showWall and meshName != ''):
            wallMesh = bpy.context.view_layer.objects[meshName]
            if wallMesh.type == 'MESH':
                self.createWall(wallMesh)
            else:
                print('Please Select Mesh Object!')

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        box = layout.box()
        box.label(text='Stair Setting')
        row = box.row()
        row.prop(self, 'width')
        row.prop(self, 'height')
        row = box.row()
        row.prop(self, 'count')
        row.prop(self, 'stepDepth')

        box = layout.box()
        box.label(text='Wall Setting')
        row = box.row()
        row.prop(self, 'showWall')
        row.prop(self, 'editMode')
        box.prop_search(self, "wallMesh", scene, "objects")
        
        row = box.row()
        row.prop(self, 'wallHeight')
        row.prop(self, 'wallOffsetY')
        
        row = box.row()
        row.prop(self, 'wallUvCenter')
        row.prop(self, 'wallUvScaleX')
        box.prop(self, 'wallSideUvScale')

        #row.operator('vic.vic_procedural_stair')
        #row.operator('vic.vic_procedural_stair_save').data = repr([self.wallMesh])

        box = layout.box()
        box.label(text='Pile')