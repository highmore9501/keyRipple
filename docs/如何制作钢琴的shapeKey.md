# 如何为钢琴键制作 shapeKey

## 搞到一个钢琴模型

这一步没什么好说的，在网上下载一个就行

## 分离出钢琴键的部分

把非钢琴键的模型分到一个 collection 里面
钢琴键的模型在 blender 里使用`p`，然后用`loose parts`的选项，把它们一个个分成独立的物体

## 重命名钢琴键

使用`key_ripple_addon\tools\rename_all_key.py`脚本，将所有的琴键依据它们在 x 轴上的分布位置，重新命名。命名的结果是最低键的为`key_21`,最高键的为`key_108`。当然这是假设我们用的是标准的 88 键钢琴

## 重新设置钢琴键的轴心

- 先把所有琴键的轴心设为它们几何的中心点，在 blender 里是先全选，然后右键选择`Set Origin`，再选择`origin to geometry`
- 添加两个空的箭头(SINGLE_ARROW)，一个命名为`white_keys_pivot`,另一个命名为`black_keys_pivot`，设置箭头刚刚好穿过它们对应的黑白键的旋转轴
- 选中所有白键，打开`key_ripple_addon\tools\chang_object_piovt_by_arrow.py`脚本，将里面的`arrow_name`修改为`white_keys_pivot`,然后运行脚本
- 选中所有黑键，将上述脚本里面的`arrow_name`修改为`black_keys_pivot`,然后运行脚本

## 为键添加 shapeKey

选中所有键，将视角设置成侧面看着所有钢琴键，然后运行`key_ripple_addon\tools\make_shape_keys.py`这个脚本，这个脚本会自动将所有键的 shapeKey 添加到所有键上。
