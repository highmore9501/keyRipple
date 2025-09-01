import bpy  # type: ignore

"""
为物体批量添加发光自定义值
"""


def setup_selected_objects_emission():
    """
    为选中物体设置发射驱动
    1. 添加自定义属性 is_pressed
    2. 设置材质发射值驱动
    """

    # 保存当前活动物体
    original_active = bpy.context.view_layer.objects.active

    # 遍历所有选中的物体
    for obj in bpy.context.selected_objects:
        # 设置当前物体为活动物体（必须这样做才能正确添加属性）
        bpy.context.view_layer.objects.active = obj

        # 1. 为物体添加自定义属性 is_pressed
        obj["is_pressed"] = 0.0

        # 2. 检查物体是否有材质
        if not obj.data.materials:
            print(f"物体 {obj.name} 没有材质，跳过处理")
            continue

        # 获取第一个材质
        material = obj.data.materials[0]
        if material is None:
            print(f"物体 {obj.name} 的第一个材质为空，跳过处理")
            continue

        # 3. 分离材质，创建唯一副本
        # 检查材质是否被多个物体使用或物体是否有多个用户
        if material.users > 1 or obj.data.users > 1:
            # 创建材质的唯一副本
            new_material = material.copy()
            # 将新材质分配给当前物体
            obj.data.materials[0] = new_material
            # 更新当前使用的材质引用
            material = new_material
            print(f"为物体 {obj.name} 创建了材质 {material.name} 的唯一副本")

        # 4. 设置材质节点
        if not material.use_nodes:
            material.use_nodes = True

        # 查找 Principled BSDF 节点
        principled_node = None
        for node in material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled_node = node
                break

        if principled_node is None:
            # 如果没有找到Principled BSDF，尝试查找其他可能的发光节点
            emission_node = None
            for node in material.node_tree.nodes:
                if node.type == 'EMISSION':
                    emission_node = node
                    break

            if emission_node is None:
                print(
                    f"物体 {obj.name} 的材质中没有找到 Principled BSDF 或 Emission 节点，跳过处理")
                continue

            # 处理 Emission 节点
            try:
                # Emission节点的color输入
                color_input = emission_node.inputs["Color"]
            except KeyError:
                # 尝试通过索引获取（更安全）
                if len(emission_node.inputs) > 0:
                    color_input = emission_node.inputs[0]  # 通常是Color输入
                else:
                    print(f"物体 {obj.name} 的Emission节点没有可用输入，跳过处理")
                    continue

            # 为材质添加自定义属性 is_pressed（如果还没有）
            if "is_pressed" not in material:
                material["is_pressed"] = 0.0

            # 清除现有的驱动（如果有的话）
            color_input.driver_remove('default_value')

            # 添加驱动
            drivers = color_input.driver_add('default_value')
            new_driver = drivers[-1]
            new_driver.driver.type = 'SCRIPTED'

            # 添加变量
            var = new_driver.driver.variables.new()
            var.name = "is_pressed_value"
            var.type = 'SINGLE_PROP'

            # 设置变量目标为材质的 is_pressed 属性
            target = var.targets[0]
            target.id_type = 'MATERIAL'
            target.id = material
            target.data_path = '["is_pressed"]'

            # 设置驱动表达式
            new_driver.driver.expression = "is_pressed_value * 10"

            print(f"成功为物体 {obj.name} 的Emission节点设置发射驱动")
        else:
            # 处理 Principled BSDF 节点
            # 查找Emission Strength输入（而不是Emission Color）
            emission_strength_input = None

            # 尝试通过名称查找Emission Strength
            try:
                emission_strength_input = principled_node.inputs["Emission Strength"]
            except KeyError:
                # 如果找不到，尝试通过索引（通常在位置18左右）
                if len(principled_node.inputs) > 18:
                    emission_strength_input = principled_node.inputs[18]

            if emission_strength_input is None:
                print(
                    f"物体 {obj.name} 的Principled BSDF节点中找不到Emission Strength输入，跳过处理")
                continue

            # 为材质添加自定义属性 is_pressed（如果还没有）
            if "is_pressed" not in material:
                material["is_pressed"] = 0.0

            # 清除现有的驱动（如果有的话）
            emission_strength_input.driver_remove('default_value')

            # 添加驱动到Emission Strength
            new_driver = emission_strength_input.driver_add('default_value')
            new_driver.driver.type = 'SCRIPTED'

            # 添加变量
            var = new_driver.driver.variables.new()
            var.name = "is_pressed_value"
            var.type = 'SINGLE_PROP'

            # 设置变量目标为材质的 is_pressed 属性
            target = var.targets[0]
            target.id_type = 'OBJECT'
            target.id = obj
            target.data_path = '["is_pressed"]'

            # is_pressed * 10
            new_driver.driver.expression = "is_pressed_value * 10"

            print(f"成功为物体 {obj.name} 的Principled BSDF节点设置Emission Strength驱动")

    # 恢复原来的活动物体
    bpy.context.view_layer.objects.active = original_active
    print("处理完成")


# 运行函数
if __name__ == "__main__":
    setup_selected_objects_emission()
