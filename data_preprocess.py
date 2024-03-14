# encoding: utf-8
# 武汉大学遥感信息工程学院 LJL
# 开发时间 2024/3/11 14:51
'''
此脚本的功能是将数据按照粗略的时间戳进行分类，分类依据如下所示：

'''
import pandas as pd
import geopandas as gpd
import numpy as np
from tqdm import tqdm
import time
data_path = r'data\L35\VecPE_all_0727_intent_replace.geojson'

def read_data(path):
    area_gdf = gpd.read_file(path)
    return area_gdf
def group_data_by_intervals(data, intervals):
    """
    按照输入的数据和指定的间隔来切分数据
    :param data: 数据区域（geopandas）
    :param intervals: （余弦划分好的时间间隔）
    :return:返回分好的各个组别list对象
    """
    groups = []
    i = 0
    for start, end in intervals:
        if i < 3:
            group = data[(data['start_time'] >= np.int64(start.value//10**3)) & (data['start_time'] <= np.int64(end.value//10**3))]
            groups.append(group)
            i+=1
        else:
            group = data[(data['start_time'] < np.int64(start.value//10**3)) | (data['start_time'] > np.int64(end.value//10**3))]
            groups.append(group)
    return groups

if __name__ == '__main__':
    start_read_time = time.time()
    area_gdf = read_data(data_path)
    end_read_time = time.time()
    print(f'the lasted time:{end_read_time-start_read_time:.3f}')
    # print(area_gdf.head())
    # print('over!')

    # 数据按照时间戳分类
    intervals = [
        ('2023-7-24 12:00:00', '2023-7-24 20:00:00'),
        ('2023-7-25 12:00:00', '2023-7-25 20:00:00'),
        ('2023-7-26 12:00:00', '2023-7-26 20:00:00'),
    ]
    # 转换时间间隔为 Timestamp 对象
    intervals = [(pd.to_datetime(start) - pd.Timedelta(hours=8), pd.to_datetime(end) - pd.Timedelta(hours=8)) for start, end in intervals]
    # 调用函数，将数据分组
    grouped_data = group_data_by_intervals(area_gdf, intervals)
    # for i ,group in enumerate(grouped_data):
    #     print(f'2023年7月{24+i}日:')
    #     print(group)
    # 将每天的数据进行输出
    for i, group in enumerate(grouped_data):
        date = pd.to_datetime('2023-07-24') + pd.Timedelta(days=i)
        output_file = f'group_{date.strftime("%Y-%m-%d")}.geojson'
        group.to_file(output_file, driver='GeoJSON')
        print(f'Group for {date.strftime("%Y-%m-%d")} saved as {output_file}')