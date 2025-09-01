from .key_ripple_config import KeyRipple, HandType, KeyType, PositionType
from bpy.types import (  # type: ignore
    Panel,
    Operator,
    PropertyGroup,
)
from bpy.props import (  # type: ignore
    IntProperty,
    StringProperty,
    PointerProperty,
    EnumProperty,
)
import os
import bpy  # type: ignore
bl_info = {
    "name": "KeyRipple Setup Tool",
    "author": "BigHippo78",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > KeyRipple",
    "description": "Setup tool for keyRipple",
    "category": "Animation",
}

# 全局变量用于存储KeyRipple实例
_key_ripple_instance = None
_last_params = None


def get_key_ripple_instance(props):
    """获取KeyRipple实例，如果参数相同则返回缓存的实例，否则创建新实例"""
    global _key_ripple_instance, _last_params

    current_params = (
        props.one_hand_finger_number,
        props.leftest_position,
        props.left_position,
        props.middle_left_position,
        props.middle_right_position,
        props.right_position,
        props.rightest_position
    )

    # 如果参数相同且实例存在，直接返回缓存的实例
    if _key_ripple_instance is not None and _last_params == current_params:
        return _key_ripple_instance

    # 否则创建新实例并缓存
    _key_ripple_instance = KeyRipple(
        props.one_hand_finger_number,
        props.leftest_position,
        props.left_position,
        props.middle_left_position,
        props.middle_right_position,
        props.right_position,
        props.rightest_position
    )
    _last_params = current_params

    return _key_ripple_instance

# 导入KeyRipple类


class KeyRippleProperties(PropertyGroup):
    # 初始化参数
    __annotations__ = {
        "one_hand_finger_number": IntProperty(
            name="Finger Number",
            description="Number of fingers per hand",
            default=5,
            min=1,
            max=10
        ),

        "leftest_position": IntProperty(
            name="Leftest Position",
            description="Leftmost position",
            default=28,
            min=0
        ),

        "left_position": IntProperty(
            name="Left Position",
            description="Left position",
            default=40,
            min=0
        ),

        "middle_left_position": IntProperty(
            name="Middle Left Position",
            description="Middle left position",
            default=52,
            min=0
        ),

        "middle_right_position": IntProperty(
            name="Middle Right Position",
            description="Middle right position",
            default=76,
            min=0
        ),

        "right_position": IntProperty(
            name="Right Position",
            description="Right position",
            default=88,
            min=0
        ),

        "rightest_position": IntProperty(
            name="Rightest Position",
            description="Rightmost position",
            default=100,
            min=0
        ),

        # 左手状态
        "left_hand_key_type": EnumProperty(
            name="Left Hand Key Type",
            description="Key type for left hand",
            items=[
                ('WHITE', "White Key", "White key"),
                ('BLACK', "Black Key", "Black key"),
            ],
            default='WHITE'
        ),

        "left_hand_position_type": EnumProperty(
            name="Left Hand Position Type",
            description="Position type for left hand",
            items=[
                ('HIGH', "High", "High position"),
                ('LOW', "Low", "Low position"),
                ('MIDDLE', "Middle", "Middle position"),
            ],
            default='HIGH'
        ),

        # 右手状态
        "right_hand_key_type": EnumProperty(
            name="Right Hand Key Type",
            description="Key type for right hand",
            items=[
                ('WHITE', "White Key", "White key"),
                ('BLACK', "Black Key", "Black key"),
            ],
            default='WHITE'
        ),

        "right_hand_position_type": EnumProperty(
            name="Right Hand Position Type",
            description="Position type for right hand",
            items=[
                ('HIGH', "High", "High position"),
                ('LOW', "Low", "Low position"),
                ('MIDDLE', "Middle", "Middle position"),
            ],
            default='HIGH'
        ),

        # 导出文件路径
        "export_file_path": StringProperty(
            name="Export File Path",
            description="Path to export recorder info",
            default="",
            subtype='FILE_PATH'
        )}


class KEYRIPPLE_OT_check_status(Operator):
    bl_idname = "keyripple.check_status"
    bl_label = "Check Objects Status"
    bl_description = "Check the status of all KeyRipple objects"

    def execute(self, context):
        props = context.scene.keyripple_props
        key_ripple = get_key_ripple_instance(props)

        key_ripple.check_objects_status()
        return {'FINISHED'}


class KEYRIPPLE_OT_setup_objects(Operator):
    bl_idname = "keyripple.setup_objects"
    bl_label = "Setup All Objects"
    bl_description = "Create all KeyRipple controllers and recorders"

    def execute(self, context):
        props = context.scene.keyripple_props
        key_ripple = get_key_ripple_instance(props)

        key_ripple.setup_all_objects()
        return {'FINISHED'}


class KEYRIPPLE_OT_save_state(Operator):
    bl_idname = "keyripple.save_state"
    bl_label = "Save State"
    bl_description = "Save current hand states to recorders"

    def execute(self, context):
        props = context.scene.keyripple_props
        key_ripple = get_key_ripple_instance(props)

        # 保存左手状态
        left_key_type = KeyType.WHITE if props.left_hand_key_type == 'WHITE' else KeyType.BLACK
        left_position_type = PositionType.HIGH if props.left_hand_position_type == 'HIGH' else \
            PositionType.LOW if props.left_hand_position_type == 'LOW' else PositionType.MIDDLE

        # 保存左手手掌状态
        key_ripple.transfer_hand_state(
            HandType.LEFT, left_key_type, left_position_type, "set")

        # 保存左手手指状态
        for finger_number in range(props.one_hand_finger_number):
            key_ripple.transfer_finger_state(
                HandType.LEFT, finger_number, left_key_type, left_position_type, "set")

        # 保存右手状态
        right_key_type = KeyType.WHITE if props.right_hand_key_type == 'WHITE' else KeyType.BLACK
        right_position_type = PositionType.HIGH if props.right_hand_position_type == 'HIGH' else \
            PositionType.LOW if props.right_hand_position_type == 'LOW' else PositionType.MIDDLE

        # 保存右手手掌状态
        key_ripple.transfer_hand_state(
            HandType.RIGHT, right_key_type, right_position_type, "set")

        # 保存右手手指状态
        for finger_number in range(props.one_hand_finger_number):
            key_ripple.transfer_finger_state(
                HandType.RIGHT, finger_number + props.one_hand_finger_number, right_key_type, right_position_type, "set")

        return {'FINISHED'}


class KEYRIPPLE_OT_load_state(Operator):
    bl_idname = "keyripple.load_state"
    bl_label = "Load State"
    bl_description = "Load hand states from recorders"

    def execute(self, context):
        props = context.scene.keyripple_props
        key_ripple = get_key_ripple_instance(props)

        # 加载左手状态
        left_key_type = KeyType.WHITE if props.left_hand_key_type == 'WHITE' else KeyType.BLACK
        left_position_type = PositionType.HIGH if props.left_hand_position_type == 'HIGH' else \
            PositionType.LOW if props.left_hand_position_type == 'LOW' else PositionType.MIDDLE

        # 加载左左手手掌状态
        key_ripple.transfer_hand_state(
            HandType.LEFT, left_key_type, left_position_type, "load")

        # 加载左手手指状态
        for finger_number in range(props.one_hand_finger_number):
            key_ripple.transfer_finger_state(
                HandType.LEFT, finger_number, left_key_type, left_position_type, "load")

        # 加载右手状态
        right_key_type = KeyType.WHITE if props.right_hand_key_type == 'WHITE' else KeyType.BLACK
        right_position_type = PositionType.HIGH if props.right_hand_position_type == 'HIGH' else \
            PositionType.LOW if props.right_hand_position_type == 'LOW' else PositionType.MIDDLE

        # 加载右手手掌状态
        key_ripple.transfer_hand_state(
            HandType.RIGHT, right_key_type, right_position_type, "load")

        # 加载右手手指状态
        for finger_number in range(props.one_hand_finger_number):
            key_ripple.transfer_finger_state(
                HandType.RIGHT, finger_number + props.one_hand_finger_number, right_key_type, right_position_type, "load")

        self.report(
            {"INFO"}, f"State left position: {left_position_type.value},{left_key_type.value};right position: {right_position_type.value},{right_key_type.value} loaded.")
        return {'FINISHED'}


class KEYRIPPLE_OT_export_info(Operator):
    bl_idname = "keyripple.export_info"
    bl_label = "Export Recorder Info"
    bl_description = "Export all recorder information to JSON file"

    def execute(self, context):
        props = context.scene.keyripple_props
        key_ripple = get_key_ripple_instance(props)

        if not props.export_file_path:
            self.report({'ERROR'}, "Please select export file path")
            return {'CANCELLED'}

        # 确保文件扩展名为 .avatar
        file_path = props.export_file_path
        if not file_path.endswith('.avatar'):
            file_path = os.path.splitext(file_path)[0] + '.avatar'

        key_ripple.export_recorder_info(file_path)
        self.report(
            {'INFO'}, f"Recorder info exported successfully to {file_path}")

        return {'FINISHED'}


class KEYRIPPLE_PT_main_panel(Panel):
    bl_label = "KeyRipple Animation Tool"
    bl_idname = "KEYRIPPLE_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "KeyRipple"

    def draw(self, context):
        layout = self.layout
        props = context.scene.keyripple_props

        # 初始化区
        box = layout.box()
        box.label(text="Initialization", icon='SETTINGS')
        col = box.column(align=True)
        col.prop(props, "one_hand_finger_number")
        col.prop(props, "leftest_position")
        col.prop(props, "left_position")
        col.prop(props, "middle_left_position")
        col.prop(props, "middle_right_position")
        col.prop(props, "right_position")
        col.prop(props, "rightest_position")

        row = box.row(align=True)
        row.operator("keyripple.check_status")
        row.operator("keyripple.setup_objects")

        # 左手状态选择区
        box = layout.box()
        box.label(text="Left Hand State", icon='TRIA_LEFT')
        box.prop(props, "left_hand_key_type")
        box.prop(props, "left_hand_position_type")

        # 右手状态选择区
        box = layout.box()
        box.label(text="Right Hand State", icon='TRIA_RIGHT')
        box.prop(props, "right_hand_key_type")
        box.prop(props, "right_hand_position_type")

        # 信息记录/加载区
        box = layout.box()
        box.label(text="Hand State Transfer", icon='FILE_REFRESH')
        row = box.row(align=True)
        row.operator("keyripple.save_state", text="Save", icon='IMPORT')
        row.operator("keyripple.load_state", text="Load", icon='EXPORT')

        # 全部信息导出区
        box = layout.box()
        box.label(text="Export Recorder Info", icon='EXPORT')
        box.prop(props, "export_file_path", text="")
        row = box.row(align=True)
        row.operator("keyripple.export_info", text="Export", icon='EXPORT')


def register():
    bpy.utils.register_class(KeyRippleProperties)
    bpy.utils.register_class(KEYRIPPLE_OT_check_status)
    bpy.utils.register_class(KEYRIPPLE_OT_setup_objects)
    bpy.utils.register_class(KEYRIPPLE_OT_save_state)
    bpy.utils.register_class(KEYRIPPLE_OT_load_state)
    bpy.utils.register_class(KEYRIPPLE_OT_export_info)
    bpy.utils.register_class(KEYRIPPLE_PT_main_panel)

    bpy.types.Scene.keyripple_props = PointerProperty(type=KeyRippleProperties)


def unregister():
    bpy.utils.unregister_class(KeyRippleProperties)
    bpy.utils.unregister_class(KEYRIPPLE_OT_check_status)
    bpy.utils.unregister_class(KEYRIPPLE_OT_setup_objects)
    bpy.utils.unregister_class(KEYRIPPLE_OT_save_state)
    bpy.utils.unregister_class(KEYRIPPLE_OT_load_state)
    bpy.utils.unregister_class(KEYRIPPLE_OT_export_info)
    bpy.utils.unregister_class(KEYRIPPLE_PT_main_panel)

    del bpy.types.Scene.keyripple_props

    # 清理全局变量
    global _key_ripple_instance, _last_params
    _key_ripple_instance = None
    _last_params = None


if __name__ == "__main__":
    register()
