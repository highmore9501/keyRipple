from enum import Enum
import bpy  # type: ignore


class HandType(Enum):
    LEFT = 'L'
    RIGHT = 'R'


class KeyType(Enum):
    WHITE = 'white'
    BLACK = 'black'


class PositionType(Enum):
    HIGH = 'high'
    LOW = 'low'
    MIDDLE = 'middle'


class KeyRipple:
    """
    当前blender中使用的配置文件
    """

    def __init__(self, one_hand_finger_number: int, leftest_position: int, left_position: int, middle_left_position: int, middle_right_position: int, right_position: int, rightest_position: int):
        # 键盘的基本设置，包括手指的数量，左右边界，以及左右手中间位置
        self.one_hand_finger_number = one_hand_finger_number
        self.leftest_position = leftest_position
        self.left_position = left_position
        self.middle_left_position = middle_left_position
        self.middle_right_position = middle_right_position
        self.right_position = right_position
        self.rightest_position = rightest_position

        # 手指控制器信息
        self.finger_controllers = {}
        for finger_number in range(one_hand_finger_number):
            self.finger_controllers[finger_number] = f"{finger_number}_L"

        for finger_number in range(one_hand_finger_number, 2*one_hand_finger_number):
            self.finger_controllers[finger_number] = f"{finger_number}_R"

        # 手指记录器信息
        self.finger_recorders = {
            "left_finger_recorders": [],
            "right_finger_recorders": []
        }

        for finger_number in range(one_hand_finger_number):
            for key_type in [KeyType.WHITE, KeyType.BLACK]:
                for position_type in [PositionType.HIGH, PositionType.LOW, PositionType.MIDDLE]:
                    recorder_name = f"{position_type.value}_{key_type.value}_{finger_number}_L"
                    self.finger_recorders['left_finger_recorders'].append(
                        recorder_name)

        for finger_number in range(one_hand_finger_number, 2*one_hand_finger_number):
            for key_type in [KeyType.WHITE, KeyType.BLACK]:
                for position_type in [PositionType.HIGH, PositionType.LOW, PositionType.MIDDLE]:
                    recorder_name = f"{position_type.value}_{key_type.value}_{finger_number}_R"
                    self.finger_recorders['right_finger_recorders'].append(
                        recorder_name)

        # 手掌控制器信息
        self.hand_controllers = {
            "left_hand_controller": "H_L",
            "left_hand_pivot_controller": "HP_L",
            "left_hand_rotation_controller": "H_rotation_L",
            "right_hand_controller": "H_R",
            "right_hand_pivot_controller": "HP_R",
            "right_hand_rotation_controller": "H_rotation_R",
        }

        # 手掌记录器信息
        self.hand_recorders = {
            "left_hand_recorders": [],
            "right_hand_recorders": []
        }
        for hand_controller_name, controller_name in self.hand_controllers.items():
            for key_type in [KeyType.WHITE, KeyType.BLACK]:
                for position_type in [PositionType.HIGH, PositionType.LOW, PositionType.MIDDLE]:
                    recorder_name = f"{position_type.value}_{key_type.value}_{controller_name}"
                    if controller_name.endswith("_L"):
                        self.hand_recorders['left_hand_recorders'].append(
                            recorder_name)
                    else:
                        self.hand_recorders['right_hand_recorders'].append(
                            recorder_name)

        # 键盘基准点信息
        self.key_board_positions = {
            "black_key_position": "black_key",
            "highest_white_key_position": "highest_white_key",
            "lowest_white_key_position": "lowest_white_key",
            "normal_hand_expand_position": "normal_hand_expand_position",
            "wide_expand_hand_position": "wide_expand_hand_position"
        }

        # 接下来是一些辅助线
        self.guidelines = {
            "press_key_direction": "press_key_direction",
        }

        # 辅助目标点
        self.target_points = {
            "body_target": "Tar_Body",
            "chest_target": "Tar_Chest",
            "butt_taget": "Tar_Butt"
        }

    def add_controllers(self):
        # 确保在对象模式下操作
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 创建或获取主集合
        main_collection = self.get_or_create_collection("addons")

        # 创建控制器集合
        controllers_collection = self.get_or_create_collection(
            "Controllers", main_collection)

        # 创建左右手子集合
        left_hand_controller_collection = self.get_or_create_collection(
            "Left_Hand_Controllers", controllers_collection)
        right_hand_controller_collection = self.get_or_create_collection(
            "Right_Hand_Controllers", controllers_collection)

        # 创建手指控制器
        for finger_number, controller_name in self.finger_controllers.items():
            if finger_number < self.one_hand_finger_number:
                # 判断是否为旋转控制器
                if "rotation" in controller_name.lower():
                    self.create_or_update_object(
                        controller_name, "cone", left_hand_controller_collection)
                else:
                    self.create_or_update_object(
                        controller_name, "cube", left_hand_controller_collection)
            else:
                # 判断是否为旋转控制器
                if "rotation" in controller_name.lower():
                    self.create_or_update_object(
                        controller_name, "cone", right_hand_controller_collection)
                else:
                    self.create_or_update_object(
                        controller_name, "cube", right_hand_controller_collection)

        # 创建手掌控制器
        for hand_controller_name, controller_name in self.hand_controllers.items():
            # 确定所属集合
            if controller_name.endswith("_L"):
                collection = left_hand_controller_collection
            else:
                collection = right_hand_controller_collection

            # 判断是否为旋转控制器
            if "rotation" in controller_name.lower():
                self.create_or_update_object(
                    controller_name, "cone", collection)
            else:
                self.create_or_update_object(
                    controller_name, "cube", collection)

        # 创建特殊的目标控制器

        taget_obj_collection = self.get_or_create_collection(
            "Target_Controllers", controllers_collection)

        for target, taget_obj_name in self.target_points.items():
            taget_obj = self.create_or_update_object(
                taget_obj_name, "cube", taget_obj_collection)
            self.add_target_driver(taget_obj)

    def add_recorders(self):
        # 确保在对象模式下操作
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 创建或获取主集合
        main_collection = self.get_or_create_collection("addons")

        # 创建记录器集合
        recorders_collection = self.get_or_create_collection(
            "Recorders", main_collection)

        # 创建左右手子集合
        left_hand_recorder_collection = self.get_or_create_collection(
            "Left_Hand_Recorders", recorders_collection)
        right_hand_recorder_collection = self.get_or_create_collection(
            "Right_Hand_Recorders", recorders_collection)

        # 创建手指记录器
        for recorder_list_name in self.finger_recorders:
            for recorder_name in self.finger_recorders[recorder_list_name]:
                # 确定所属集合
                if recorder_list_name == "left_finger_recorders":
                    collection = left_hand_recorder_collection
                else:
                    collection = right_hand_recorder_collection

                # 判断是否为旋转记录器
                if "rotation" in recorder_name.lower():
                    self.create_or_update_object(
                        recorder_name, "cone_empty", collection)
                else:
                    self.create_or_update_object(
                        recorder_name, "sphere", collection)

        # 创建手掌记录器
        for recorder_list_name in self.hand_recorders:
            for recorder_name in self.hand_recorders[recorder_list_name]:
                # 确定所属集合
                if recorder_list_name == "left_hand_recorders":
                    collection = left_hand_recorder_collection
                else:
                    collection = right_hand_recorder_collection

                # 判断是否为旋转记录器
                if "rotation" in recorder_name.lower():
                    self.create_or_update_object(
                        recorder_name, "cone_empty", collection)
                else:
                    self.create_or_update_object(
                        recorder_name, "sphere", collection)

        # 创建键盘基准点
        positions_collection = self.get_or_create_collection(
            "Positions", main_collection)
        for position_name, obj_name in self.key_board_positions.items():
            self.create_or_update_object(
                obj_name, "sphere", positions_collection)

        # 创建辅助线
        guidelines_collection = self.get_or_create_collection(
            "Guidelines", main_collection)
        for guideline_name, obj_name in self.guidelines.items():
            self.create_or_update_object(
                obj_name, "single_arrow", guidelines_collection)

    def add_target_driver(self, target_obj):
        """
        为 Target 控制器的 X 轴添加驱动，使其 X 值为 H_L 和 H_R 的 X 值的中间值

        :param target_obj: 控制器对象
        """
        # 确保对象存在
        if not target_obj:
            print("错误: Tar_B 对象不存在")
            return

        # 检查是否已经存在X轴驱动
        if target_obj.animation_data and target_obj.animation_data.drivers:
            for driver in target_obj.animation_data.drivers:
                # 检查是否是X轴位置驱动
                if driver.data_path == "location" and driver.array_index == 0:
                    print(f"提示: {target_obj.name} 的 X 轴驱动已存在，跳过添加")
                    return

        # 获取 H_L 和 H_R 控制器对象名称
        h_l_name = self.hand_controllers["left_hand_controller"]  # H_L
        h_r_name = self.hand_controllers["right_hand_controller"]  # H_R

        # 为 Tar_B 的 X 轴位置添加驱动
        driver = target_obj.driver_add("location", 0).driver  # 0 表示 X 轴
        driver.type = 'SCRIPTED'

        # 添加 H_L 的变量
        var1 = driver.variables.new()
        var1.name = "h_l_x"
        var1.type = 'TRANSFORMS'

        target1 = var1.targets[0]
        target1.id = bpy.data.objects.get(h_l_name)
        target1.transform_type = 'LOC_X'
        target1.transform_space = 'WORLD_SPACE'

        # 添加 H_R 的变量
        var2 = driver.variables.new()
        var2.name = "h_r_x"
        var2.type = 'TRANSFORMS'

        target2 = var2.targets[0]
        target2.id = bpy.data.objects.get(h_r_name)
        target2.transform_type = 'LOC_X'
        target2.transform_space = 'WORLD_SPACE'

        # 设置驱动表达式为两个值的平均值
        driver.expression = "(h_l_x + h_r_x) / 2"

        print(f"已为 {target_obj.name} 控制器添加 X 轴驱动，表达式: (h_l_x + h_r_x) / 2")

    def get_or_create_collection(self, name, parent_collection=None):
        """
        获取或创建集合
        """
        if name in bpy.data.collections:
            collection = bpy.data.collections[name]
        else:
            collection = bpy.data.collections.new(name)
            if parent_collection:
                parent_collection.children.link(collection)
            else:
                # 如果没有指定父集合，链接到场景主集合
                bpy.context.scene.collection.children.link(collection)

        # 如果指定了父集合，则确保该集合在父集合中
        if parent_collection and collection.name not in [c.name for c in parent_collection.children]:
            parent_collection.children.link(collection)

        return collection

    def create_or_update_object(self, obj_name, obj_type="cube", collection=None, rotation_mode='QUATERNION'):
        """
        创建或更新物体的通用方法

        :param obj_name: 物体名称
        :param obj_type: 物体类型 ("cube", "cone", "sphere", "single_arrow")
        :param collection: 物体所属集合
        :param rotation_mode: 旋转模式，默认为四元数
        :return: 物体对象
        """
        # 从pre_obj_names中移除同名物体
        if hasattr(self, 'pre_obj_names') and obj_name in self.pre_obj_names:
            self.pre_obj_names.remove(obj_name)

        # 如果物体已存在
        if obj_name in bpy.data.objects:
            obj = bpy.data.objects[obj_name]
            # 将物体移动到指定集合
            if collection and obj.name not in collection.objects:
                self.move_object_to_collection(obj, collection)
            # 直接返回
            return bpy.data.objects[obj_name]

        # 根据类型创建不同的物体
        if obj_type == "cube":
            bpy.ops.mesh.primitive_cube_add(
                size=0.2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(0.1, 0.1, 0.1))
        elif obj_type == "cone":
            bpy.ops.mesh.primitive_cone_add(
                enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(0.01, 0.01, 0.01))
        elif obj_type == "sphere":
            bpy.ops.object.empty_add(type='SPHERE', radius=0.01)
        elif obj_type == "cone_empty":
            bpy.ops.object.empty_add(type='CONE', radius=0.01)
        elif obj_type == "single_arrow":
            bpy.ops.object.empty_add(type='SINGLE_ARROW', radius=1.0)

        # 设置物体名称
        obj = bpy.context.active_object
        obj.name = obj_name

        # 设置旋转模式（如果适用）
        if obj_type in ["cone", "cone_empty"] or (hasattr(obj, 'rotation_mode') and rotation_mode):
            obj.rotation_mode = rotation_mode

        # 将物体移动到指定集合
        if collection:
            self.move_object_to_collection(obj, collection)

        return obj

    def copy_transfer(self, source_obj, target_obj, direction: str = "set", transfer_type: str = "location"):
        """
        在两个对象之间传输数据的通用方法

        :param source_obj: 源对象
        :param target_obj: 目标对象
        :param direction: 传输方向，"set"表示控制器到记录器，"load"表示记录器到控制器
        :param transfer_type: 传输类型，"location"表示位置，"rotation"表示旋转
        """
        if transfer_type == "location":
            if direction == "set":
                # 解锁记录器位置
                self.unlock_object_location(target_obj)
            # 复制位置
            target_obj.location = source_obj.location
        elif transfer_type == "rotation":
            if direction == "set":
                # 解锁记录器旋转
                self.unlock_object_rotation(target_obj)

            # 复制旋转值
            if source_obj.rotation_mode == target_obj.rotation_mode:
                if source_obj.rotation_mode == 'QUATERNION':
                    target_obj.rotation_quaternion = source_obj.rotation_quaternion
                else:
                    target_obj.rotation_euler = source_obj.rotation_euler
            else:
                # 如果旋转模式不同，先将目标对象的旋转模式设置为与源对象相同
                target_obj.rotation_mode = source_obj.rotation_mode
                # 然后复制旋转值
                if source_obj.rotation_mode == 'QUATERNION':
                    target_obj.rotation_quaternion = source_obj.rotation_quaternion
                else:
                    target_obj.rotation_euler = source_obj.rotation_euler

    def unlock_object_location(self, obj):
        """
        解锁对象的位置锁定
        """
        obj.lock_location[0] = False  # X
        obj.lock_location[1] = False  # Y
        obj.lock_location[2] = False  # Z

    def unlock_object_rotation(self, obj):
        """
        解锁对象的旋转锁定
        """
        obj.lock_rotation[0] = False  # X
        obj.lock_rotation[1] = False  # Y
        obj.lock_rotation[2] = False  # Z

    def move_object_to_collection(self, obj, collection):
        """
        将对象移动到指定集合
        """
        # 从所有现有集合中移除对象
        for coll in obj.users_collection:
            coll.objects.unlink(obj)

        # 将对象链接到目标集合
        collection.objects.link(obj)

    def setup_all_objects(self):
        """
        一次性设置所有控制器和记录器
        """
        # 记录添加控件前addons集合及其子集合中的所有物体名称
        self.pre_obj_names = []
        if "addons" in bpy.data.collections:
            addons_collection = bpy.data.collections["addons"]
            # 收集addons集合及其所有子集合中的物体
            collections_to_check = [addons_collection]
            for coll in addons_collection.children_recursive:
                collections_to_check.append(coll)

            for coll in collections_to_check:
                for obj in coll.objects:
                    self.pre_obj_names.append(obj.name)

        # 添加控制器和记录器
        self.add_controllers()
        self.add_recorders()

        # 打印未使用的控件名称
        if self.pre_obj_names:
            print("\n未使用的控件:")
            for obj_name in self.pre_obj_names:
                print(f"  • {obj_name}")
        else:
            print("\n没有发现未使用的控件")

    def check_objects_status(self):
        """
        检查Blender场景中所有控制器和记录器的状态，输出存在和缺失对象的报告
        """
        # 收集所有应该存在的对象名称
        expected_objects = set()

        # 收集所有控制器名称
        for controller_name in self.finger_controllers.values():
            expected_objects.add(controller_name)

        for controller_name in self.hand_controllers.values():
            expected_objects.add(controller_name)

        # 收集所有记录器名称
        for recorder_list in self.finger_recorders.values():
            for recorder_name in recorder_list:
                expected_objects.add(recorder_name)

        for recorder_list in self.hand_recorders.values():
            for recorder_name in recorder_list:
                expected_objects.add(recorder_name)

        # 收集键盘基准点和辅助线名称
        for obj_name in self.key_board_positions.values():
            expected_objects.add(obj_name)

        for obj_name in self.guidelines.values():
            expected_objects.add(obj_name)

        # 添加特殊控件Tar_B
        expected_objects.add("Tar_B")

        # 只获取 addons 集合及其子集合中的对象
        actual_objects = set()
        if "addons" in bpy.data.collections:
            addons_collection = bpy.data.collections["addons"]
            # 收集 addons 集合及其所有子集合中的物体
            collections_to_check = [addons_collection]
            collections_to_check.extend(addons_collection.children_recursive)

            for coll in collections_to_check:
                for obj in coll.objects:
                    actual_objects.add(obj.name)

        # 计算存在的和缺失的对象
        existing_objects = expected_objects.intersection(actual_objects)
        missing_objects = expected_objects.difference(actual_objects)
        unexpected_objects = actual_objects.difference(expected_objects)

        # 输出报告
        print("=" * 50)
        print("KeyRipple 对象状态报告")
        print("=" * 50)

        print(f"\n✓ 存在的对象: {len(existing_objects)}/{len(expected_objects)}")
        if existing_objects:
            # 按类型分组显示存在的对象
            finger_controllers_exist = []
            hand_controllers_exist = []
            finger_recorders_exist = []
            hand_recorders_exist = []
            positions_exist = []
            guidelines_exist = []

            for obj_name in existing_objects:
                if obj_name in self.finger_controllers.values():
                    finger_controllers_exist.append(obj_name)
                elif obj_name in self.hand_controllers.values():
                    hand_controllers_exist.append(obj_name)
                elif any(obj_name in recorders for recorders in self.finger_recorders.values()):
                    finger_recorders_exist.append(obj_name)
                elif any(obj_name in recorders for recorders in self.hand_recorders.values()):
                    hand_recorders_exist.append(obj_name)
                elif obj_name in self.key_board_positions.values():
                    positions_exist.append(obj_name)
                elif obj_name in self.guidelines.values():
                    guidelines_exist.append(obj_name)

            if finger_controllers_exist:
                print(f"  手指控制器 ({len(finger_controllers_exist)}):")
                for obj_name in sorted(finger_controllers_exist):
                    print(f"    • {obj_name}")

            if hand_controllers_exist:
                print(f"  手掌控制器 ({len(hand_controllers_exist)}):")
                for obj_name in sorted(hand_controllers_exist):
                    print(f"    • {obj_name}")

            if finger_recorders_exist:
                print(f"  手指记录器 ({len(finger_recorders_exist)}):")
                for obj_name in sorted(finger_recorders_exist):
                    print(f"    • {obj_name}")

            if hand_recorders_exist:
                print(f"  手掌记录器 ({len(hand_recorders_exist)}):")
                for obj_name in sorted(hand_recorders_exist):
                    print(f"    • {obj_name}")

            if positions_exist:
                print(f"  键盘基准点 ({len(positions_exist)}):")
                for obj_name in sorted(positions_exist):
                    print(f"    • {obj_name}")

            if guidelines_exist:
                print(f"  辅助线 ({len(guidelines_exist)}):")
                for obj_name in sorted(guidelines_exist):
                    print(f"    • {obj_name}")

        print(f"\n✗ 缺失的对象: {len(missing_objects)}")
        if missing_objects:
            # 按类型分组显示缺失的对象
            finger_controllers_missing = []
            hand_controllers_missing = []
            finger_recorders_missing = []
            hand_recorders_missing = []
            positions_missing = []
            guidelines_missing = []

            for obj_name in missing_objects:
                if obj_name in self.finger_controllers.values():
                    finger_controllers_missing.append(obj_name)
                elif obj_name in self.hand_controllers.values():
                    hand_controllers_missing.append(obj_name)
                elif any(obj_name in recorders for recorders in self.finger_recorders.values()):
                    finger_recorders_missing.append(obj_name)
                elif any(obj_name in recorders for recorders in self.hand_recorders.values()):
                    hand_recorders_missing.append(obj_name)
                elif obj_name in self.key_board_positions.values():
                    positions_missing.append(obj_name)
                elif obj_name in self.guidelines.values():
                    guidelines_missing.append(obj_name)

            if finger_controllers_missing:
                print(f"  手指控制器 ({len(finger_controllers_missing)}):")
                for obj_name in sorted(finger_controllers_missing):
                    print(f"    • {obj_name}")

            if hand_controllers_missing:
                print(f"  手掌控制器 ({len(hand_controllers_missing)}):")
                for obj_name in sorted(hand_controllers_missing):
                    print(f"    • {obj_name}")

            if finger_recorders_missing:
                print(f"  手指记录器 ({len(finger_recorders_missing)}):")
                for obj_name in sorted(finger_recorders_missing):
                    print(f"    • {obj_name}")

            if hand_recorders_missing:
                print(f"  手掌记录器 ({len(hand_recorders_missing)}):")
                for obj_name in sorted(hand_recorders_missing):
                    print(f"    • {obj_name}")

            if positions_missing:
                print(f"  键盘基准点 ({len(positions_missing)}):")
                for obj_name in sorted(positions_missing):
                    print(f"    • {obj_name}")

            if guidelines_missing:
                print(f"  辅助线 ({len(guidelines_missing)}):")
                for obj_name in sorted(guidelines_missing):
                    print(f"    • {obj_name}")

        print(f"\n? 额外的对象: {len(unexpected_objects)}")
        if unexpected_objects:
            print("  以下对象不在配置中定义:")
            for obj_name in sorted(unexpected_objects)[:20]:  # 限制显示数量
                print(f"    • {obj_name}")
            if len(unexpected_objects) > 20:
                print(f"    ... 还有 {len(unexpected_objects) - 20} 个对象")

        print("\n" + "=" * 50)

    def export_recorder_info(self, file_name: str) -> None:
        """
        :param file_name: 输出文件名
        :usage: 这个方法用于将所有记录器的信息以及配置参数输出到json文件
        """
        import json
        from collections import defaultdict

        def nested_dict():
            return defaultdict(nested_dict)

        result = nested_dict()

        # 保存配置参数
        print("导出配置参数信息...")
        result['config']['one_hand_finger_number'] = self.one_hand_finger_number
        result['config']['leftest_position'] = self.leftest_position
        result['config']['left_position'] = self.left_position
        result['config']['middle_left_position'] = self.middle_left_position
        result['config']['middle_right_position'] = self.middle_right_position
        result['config']['right_position'] = self.right_position
        result['config']['rightest_position'] = self.rightest_position

        # 导出手指记录器信息
        print("导出手指记录器信息...")
        for recorder_list_name in self.finger_recorders:
            for recorder_name in self.finger_recorders[recorder_list_name]:
                if recorder_name in bpy.data.objects:
                    obj = bpy.data.objects[recorder_name]

                    # 确定记录器类型（位置或旋转）
                    is_rotation_recorder = "rotation" in recorder_name.lower()

                    # 添加到结果中
                    if is_rotation_recorder:
                        # 旋转记录器
                        if obj.rotation_mode == 'QUATERNION':
                            result['finger_recorders'][recorder_list_name][recorder_name] = {
                                'rotation_mode': obj.rotation_mode,
                                'rotation_quaternion': obj.rotation_quaternion
                            }
                        else:
                            result['finger_recorders'][recorder_list_name][recorder_name] = {
                                'rotation_mode': obj.rotation_mode,
                                'rotation_euler': obj.rotation_euler
                            }
                    else:
                        # 位置记录器
                        result['finger_recorders'][recorder_list_name][recorder_name] = {
                            'location': obj.location
                        }

        # 导出手掌记录器信息
        print("导出手掌记录器信息...")
        for recorder_list_name in self.hand_recorders:
            for recorder_name in self.hand_recorders[recorder_list_name]:
                if recorder_name in bpy.data.objects:
                    obj = bpy.data.objects[recorder_name]

                    # 确定记录器类型（位置或旋转）
                    is_rotation_recorder = "rotation" in recorder_name.lower()

                    # 添加到结果中
                    if is_rotation_recorder:
                        # 旋转记录器
                        if obj.rotation_mode == 'QUATERNION':
                            result['hand_recorders'][recorder_list_name][recorder_name] = {
                                'rotation_mode': obj.rotation_mode,
                                'rotation_quaternion': obj.rotation_quaternion
                            }
                        else:
                            result['hand_recorders'][recorder_list_name][recorder_name] = {
                                'rotation_mode': obj.rotation_mode,
                                'rotation_euler': obj.rotation_euler
                            }
                    else:
                        # 位置记录器
                        result['hand_recorders'][recorder_list_name][recorder_name] = {
                            'location': obj.location
                        }

        # 导出键盘基准点信息
        print("导出键盘基准点信息...")
        for position_key, obj_name in self.key_board_positions.items():
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                result['key_board_positions'][position_key] = {
                    'name': obj_name,
                    'location': obj.location
                }

        # 导出辅助线信息
        print("导出辅助线信息...")
        for guideline_key, obj_name in self.guidelines.items():
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                result['guidelines'][guideline_key] = {
                    'name': obj_name,
                    'location': obj.location
                }

                # 如果是箭头类型的辅助线，也保存旋转信息
                if obj.type == 'EMPTY' and obj.empty_display_type == 'SINGLE_ARROW':
                    if obj.rotation_mode == 'QUATERNION':
                        result['guidelines'][guideline_key]['rotation_mode'] = obj.rotation_mode
                        result['guidelines'][guideline_key]['rotation_quaternion'] = obj.rotation_quaternion
                    else:
                        result['guidelines'][guideline_key]['rotation_mode'] = obj.rotation_mode
                        result['guidelines'][guideline_key]['rotation_euler'] = obj.rotation_euler

        # 写入文件
        data = json.dumps(result, default=list, indent=4)

        with open(file_name, 'w') as f:
            f.write(data)
            print(f'记录器信息已导出到 {file_name}')

    def transfer_finger_state(self, hand_type: HandType, finger_number: int, key_type: KeyType, position_type: PositionType, direction: str = "set"):
        """
        在手指控制器和记录器之间传输状态数据

        :param hand_type: 手类型 (LEFT, RIGHT)
        :param finger_number: 手指编号
        :param key_type: 按键类型 (WHITE, BLACK)
        :param position_type: 位置类型 (HIGH, LOW, MIDDLE)
        :param direction: 传输方向，"set"表示控制器到记录器，"load"表示记录器到控制器
        :return: 操作是否成功
        """
        if direction == "set":
            print(
                f"设置{hand_type.value}手第{finger_number}根手指状态: {key_type.value}键, {position_type.value}位置")
        else:
            print(
                f"加载{hand_type.value}手第{finger_number}根手指状态: {key_type.value}键, {position_type.value}位置")

        # 构造控制器和记录器名称
        controller_name = f"{finger_number}_{hand_type.value}"
        recorder_name = f"{position_type.value}_{key_type.value}_{finger_number}_{hand_type.value}"

        # 检查控制器和记录器是否存在
        if controller_name not in bpy.data.objects:
            print(f"  ✗ 控制器 {controller_name} 不存在")
            return False

        if recorder_name not in bpy.data.objects:
            print(f"  ✗ 记录器 {recorder_name} 不存在")
            return False

        # 获取源对象和目标对象
        source_obj = bpy.data.objects[controller_name] if direction == "set" else bpy.data.objects[recorder_name]
        target_obj = bpy.data.objects[recorder_name] if direction == "set" else bpy.data.objects[controller_name]

        # 传输位置数据
        self.copy_transfer(source_obj, target_obj, direction, "location")
        print(f"  ✓ 位置 {controller_name} -> {recorder_name}" if direction == "set"
              else f"  ✓ 位置 {recorder_name} -> {controller_name}")

        print(f"\n{hand_type.value}手第{finger_number}根手指{'设置' if direction == 'set' else '加载'}完成: {key_type.value}键, {position_type.value}位置")
        return True

    def transfer_hand_state(self, hand_type: HandType, key_type: KeyType, position_type: PositionType, direction: str = "set"):
        """
        在手掌控制器和记录器之间传输状态数据

        :param hand_type: 手类型 (LEFT, RIGHT)
        :param key_type: 按键类型 (WHITE, BLACK)
        :param position_type: 位置类型 (HIGH, LOW, MIDDLE)
        :param direction: 传输方向，"set"表示控制器到记录器，"load"表示记录器到控制器
        :return: 操作是否成功
        """
        if direction == "set":
            print(
                f"设置{hand_type.value}手状态: {key_type.value}键, {position_type.value}位置")
        else:
            print(
                f"加载{hand_type.value}手状态: {key_type.value}键, {position_type.value}位置")

        # 获取对应手部的控制器名称
        hand_controller_names = {}
        if hand_type == HandType.LEFT:
            hand_controller_names = {
                "main": self.hand_controllers["left_hand_controller"],
                "pivot": self.hand_controllers["left_hand_pivot_controller"],
                "rotation": self.hand_controllers["left_hand_rotation_controller"]
            }
        else:
            hand_controller_names = {
                "main": self.hand_controllers["right_hand_controller"],
                "pivot": self.hand_controllers["right_hand_pivot_controller"],
                "rotation": self.hand_controllers["right_hand_rotation_controller"]
            }

        success_count = 0
        total_count = len(hand_controller_names)

        # 处理每个手部控制器
        for controller_role, controller_name in hand_controller_names.items():
            # 构造记录器名称
            recorder_name = f"{position_type.value}_{key_type.value}_{controller_name}"

            # 检查控制器和记录器是否存在
            if controller_name not in bpy.data.objects:
                print(f"  ✗ 控制器 {controller_name} 不存在")
                continue

            if recorder_name not in bpy.data.objects:
                print(f"  ✗ 记录器 {recorder_name} 不存在")
                continue

            # 获取源对象和目标对象
            source_obj = bpy.data.objects[controller_name] if direction == "set" else bpy.data.objects[recorder_name]
            target_obj = bpy.data.objects[recorder_name] if direction == "set" else bpy.data.objects[controller_name]

            # 传输位置数据（除了旋转控制器只传输旋转数据）
            if "rotation" not in controller_role:
                self.copy_transfer(source_obj, target_obj,
                                   direction, "location")
                print(f"  ✓ 位置 {controller_name} -> {recorder_name}" if direction == "set"
                      else f"  ✓ 位置 {recorder_name} -> {controller_name}")

            # 传输旋转数据
            self.copy_transfer(source_obj, target_obj, direction, "rotation")
            print(f"  ✓ 旋转 {controller_name} -> {recorder_name}" if direction == "set"
                  else f"  ✓ 旋转 {recorder_name} -> {controller_name}")

            success_count += 1

        print(f"\n{hand_type.value}手{'设置' if direction == 'set' else '加载'}完成: {key_type.value}键, {position_type.value}位置 "
              f"({success_count}/{total_count} 控制器处理成功)")
        return success_count > 0

    def import_recorder_info(self, file_name: str) -> bool:
        """
        从JSON文件中读取记录器信息并应用到相应的对象上

        :param file_name: 输入文件名
        :return: 导入是否成功
        """
        import json

        try:
            # 读取JSON文件
            with open(file_name, 'r') as f:
                data = json.load(f)
            print(f"成功读取记录器信息文件: {file_name}")

            # 检查必要的键是否存在
            if 'finger_recorders' not in data or 'hand_recorders' not in data:
                print("错误: JSON文件格式不正确，缺少必要的记录器信息")
                return False

            # 导入手指记录器信息
            print("导入手指记录器信息...")
            finger_recorders_data = data.get('finger_recorders', {})
            for recorder_list_name, recorders in finger_recorders_data.items():
                for recorder_name, recorder_info in recorders.items():
                    if recorder_name in bpy.data.objects:
                        obj = bpy.data.objects[recorder_name]

                        # 设置位置信息
                        if 'location' in recorder_info:
                            obj.location = recorder_info['location']
                            print(
                                f"  ✓ 设置 {recorder_name} 位置: {recorder_info['location']}")

                        # 设置旋转信息
                        if 'rotation_mode' in recorder_info:
                            obj.rotation_mode = recorder_info['rotation_mode']
                            if recorder_info['rotation_mode'] == 'QUATERNION' and 'rotation_quaternion' in recorder_info:
                                obj.rotation_quaternion = recorder_info['rotation_quaternion']
                                print(f"  ✓ 设置 {recorder_name} 四元数旋转")
                            elif 'rotation_euler' in recorder_info:
                                obj.rotation_euler = recorder_info['rotation_euler']
                                print(f"  ✓ 设置 {recorder_name} 欧拉旋转")
                    else:
                        print(f"  ✗ 跳过 {recorder_name} (对象不存在)")

            # 导入手掌记录器信息
            print("导入手掌记录器信息...")
            hand_recorders_data = data.get('hand_recorders', {})
            for recorder_list_name, recorders in hand_recorders_data.items():
                for recorder_name, recorder_info in recorders.items():
                    if recorder_name in bpy.data.objects:
                        obj = bpy.data.objects[recorder_name]

                        # 设置位置信息
                        if 'location' in recorder_info:
                            obj.location = recorder_info['location']
                            print(
                                f"  ✓ 设置 {recorder_name} 位置: {recorder_info['location']}")

                        # 设置旋转信息
                        if 'rotation_mode' in recorder_info:
                            obj.rotation_mode = recorder_info['rotation_mode']
                            if recorder_info['rotation_mode'] == 'QUATERNION' and 'rotation_quaternion' in recorder_info:
                                obj.rotation_quaternion = recorder_info['rotation_quaternion']
                                print(f"  ✓ 设置 {recorder_name} 四元数旋转")
                            elif 'rotation_euler' in recorder_info:
                                obj.rotation_euler = recorder_info['rotation_euler']
                                print(f"  ✓ 设置 {recorder_name} 欧拉旋转")
                    else:
                        print(f"  ✗ 跳过 {recorder_name} (对象不存在)")

            # 导入键盘基准点信息
            print("导入键盘基准点信息...")
            key_board_positions_data = data.get('key_board_positions', {})
            for position_key, position_info in key_board_positions_data.items():
                obj_name = position_info.get('name')
                if obj_name and obj_name in bpy.data.objects:
                    obj = bpy.data.objects[obj_name]
                    obj.location = position_info['location']
                    print(f"  ✓ 设置 {obj_name} 位置: {position_info['location']}")
                else:
                    print(f"  ✗ 跳过 {obj_name} (对象不存在)")

            # 导入辅助线信息
            print("导入辅助线信息...")
            guidelines_data = data.get('guidelines', {})
            for guideline_key, guideline_info in guidelines_data.items():
                obj_name = guideline_info.get('name')
                if obj_name and obj_name in bpy.data.objects:
                    obj = bpy.data.objects[obj_name]
                    obj.location = guideline_info['location']
                    print(
                        f"  ✓ 设置 {obj_name} 位置: {guideline_info['location']}")

                    # 如果有旋转信息也设置旋转
                    if 'rotation_mode' in guideline_info:
                        obj.rotation_mode = guideline_info['rotation_mode']
                        if guideline_info['rotation_mode'] == 'QUATERNION' and 'rotation_quaternion' in guideline_info:
                            obj.rotation_quaternion = guideline_info['rotation_quaternion']
                            print(f"  ✓ 设置 {obj_name} 四元数旋转")
                        elif 'rotation_euler' in guideline_info:
                            obj.rotation_euler = guideline_info['rotation_euler']
                            print(f"  ✓ 设置 {obj_name} 欧拉旋转")
                else:
                    print(f"  ✗ 跳过 {obj_name} (对象不存在)")

            print(f"记录器信息已从 {file_name} 成功导入")
            return True

        except FileNotFoundError:
            print(f"错误: 找不到文件 {file_name}")
            return False
        except json.JSONDecodeError:
            print(f"错误: {file_name} 不是有效的JSON文件")
            return False
        except Exception as e:
            print(f"导入过程中发生错误: {str(e)}")
            return False
