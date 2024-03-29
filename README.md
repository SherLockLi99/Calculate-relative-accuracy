# README

## data_preprocess.py

步骤一在==**data_preprocess.py**==脚本中完成

**1.  需要划分出不同时间范围的数据**

- 时间戳划分：
  - 1690171200000000(微秒) -> 2023-07-24 12:00:00
  - 1690200000000000(微秒) -> 2023-07-24 20:00:00
  - 1690257600000000(微秒) -> 2023-07-25 12:00:00
  - 1690286400000000(微秒) -> 2023-07-25 20:00:00
  - 1690344000000000(微秒) -> 2023-07-24 12:00:00
  - 1690372800000000(微秒) -> 2023-07-26 20:00:00

- 目前观察到的现象是一天（例如7-24日）应该是就只有2圈，面要素里面随便查的两套数据的误差。

  1.1 2023-07-24,16:01:47
  1.2 2023-07-24,17:44:27

  

  2.12023-07-24,16:01:46
  2.2 2023-07-24,17:44:25
  
  2023-07-24,15:50:57
  2023-07-24,17:34:36
  
  2023-07-24,16:18:17
  2023-07-24,17:58:58

- 需要注意的是，目前两趟之间可能有些许数据出入，也就是说第一趟跑的区域中第二趟没有。

## relative_accuracy_lib.py


步骤二和三在脚本==**relative_accuracy_lib.py**==中完成

**2. 需要进行半径15米范围内的所有要素查询**

- 按照之前轨迹的思路，使用geopandas的函数寻找固定圆形范围内的所有要素（以中心点为圆心，15m为半径的圆）
  1. 不同类型要素的中心点确认方式
     - 点：本身
     - 线：线的中点
     - 面：生成最小外接矩形，按照矩形中心点
  2. 返回该范围内检索到的所有要素

**3. 在查询的要素中找到最近的然后计算横纵误差**

- 首先找到最近的要素，目前寻找最近的方法是按照上面点线面的**代表点**来寻找的。

  ==并不是返回其最近的要素（这里可以考虑实现）==

- 目前的思路，同类型（点，线，面）分开计算

  - 点：直接计算整体的位置误差

  - 线：按照线的中点来计算相对位置误差

    ps：==目前长安那边是怎么计算的我不是很清楚，文档里面并没有说明线要素应该如何计算相对精度==

  - 面：生成最小外接矩形，按照矩形中心点来计算横纵误差

    ps:==长安那边是先生成外接矩形，确定角点对儿再进行计算，但是文档里面说的也是比较含糊，以及什么叫真值相对组和评测相对组之间的相对横纵误差==

## 输出文件

#### data：

data
│  └─L35									#原始长安提供数据（L35线路，2023-07-27数据）

#### output_data：

output_data 
    ├─data_aday  						#该数据是经过data_preprocess处理之后的每一天的数据          
    └─errors_timeDifference 	#该结果是relative_accuracy_lib计算之后的横纵误差数据
