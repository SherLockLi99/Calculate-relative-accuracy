# encoding: utf-8
# 武汉大学遥感信息工程学院 LJL
# 开发时间 2024/3/13 14:39
import pandas as pd
import geopandas as gpd
import numpy as np
import time
import os
from tqdm import tqdm
from shapely.geometry import Point

data_path = r'output_data\data_aday'
output_path = r'output_data\errors_timeDifference'
def extract_obs_subsets(gdf,p,radius=15):
    '''
    使用geopandas中的索引来查询point指定圆形范围内的所有要素
    :param gdf: 指定的全部数据区域
    :param p: 目标点
    :param radius: 指定的圆形范围，默认是15米
    :return:返回搜索到对应范围内的gdf对象
    '''
    radius /= 111111
    boundary = Point(p[0], p[1]).buffer(radius)
    possible_matches_index = list(gdf.sindex.intersection(boundary.bounds))
    gdf_tmp = gdf.iloc[possible_matches_index]
    return gdf_tmp[gdf_tmp.intersects(boundary)]

def timestamp_2_BeijingStamp(timestamp):
    '''
    时间戳转换函数，将长安的时间戳转换为Timestamp对象，并且对应为北京时间。
    :param timestamp: 长安时间戳对象
    :return: 返回Timestamp对象，北京时间
    '''
    timestamp_temp = pd.Timestamp(timestamp,unit='us')
    beijing_timestamp =timestamp_temp + pd.Timedelta(hours=8)
    return beijing_timestamp
def compute_errors(point,nearest_feature_geometry):
    '''
    输入点和最近对象的几何对象，返回其横纵误差
    :param point: 点几何
    :param nearest_feature_geometry: 最近邻对象的几何
    :return: horizontal_error（横向误差）,vertical_error（纵向误差）
    '''
    if nearest_feature_geometry.geom_type == 'Point':
        horizontal_error = abs(point.x - nearest_feature_geometry.x)*111111
        vertical_error = abs(point.y - nearest_feature_geometry.y)*111111
    elif nearest_feature_geometry.geom_type == 'LineString':
        mid_point = nearest_feature_geometry.interpolate(0.5, normalized=True)
        horizontal_error = abs(point.x - mid_point.x) * 111111
        vertical_error = abs(point.y - mid_point.y) * 111111
    elif nearest_feature_geometry.geom_type == 'Polygon':
        min_rect = nearest_feature_geometry.minimum_rotated_rectangle
        center_point = min_rect.centroid
        horizontal_error = abs(point.x - center_point.x) * 111111
        vertical_error = abs(point.y - center_point.y) * 111111
    return horizontal_error,vertical_error

def find_neasrst_feature(feature,center_point,nearby_features):
    '''
    寻找feature对象的最近邻对象
    :param feature: 当前要素
    :param center_point: 可以当前要素位置的点
    :param nearby_features: 附近的所有要素组
    :return: 最近邻要素
    '''
    geom_type = feature.geometry.geom_type
    nearest_distance = np.inf
    nearest_feature = None
    for idx,nearby_feature in nearby_features.iterrows():
        if nearby_feature.geometry != feature.geometry:
            if geom_type == nearby_feature.geometry.geom_type:
                distance = center_point.distance(nearby_feature.geometry)*111111
                if distance < nearest_distance:
                    nearest_distance = distance
                    nearest_feature = nearby_feature
    return nearest_feature

def calculate_re_ca(area_gdf,output_name):
    '''
    计算相对横纵误差
    :param area_gdf: 对应的geopandas对象
    :param output_name: 文件输出路径名称
    :return:
    '''
    print(len(area_gdf))
    relative_horizontal_errors = []
    relative_vertical_errors = []
    time_difference = []
    oid_of_matching_feature = []
    for index, feature in tqdm(area_gdf.iterrows()):
        geom_type = feature.geometry.geom_type
        if geom_type == 'Point':
            oid,time_difference_m,relative_horizontal_error,relative_vertical_error = process_point_feature(feature, area_gdf)
        elif geom_type == 'LineString':
            oid,time_difference_m,relative_horizontal_error,relative_vertical_error = process_linestring_feature(feature, area_gdf)
        elif geom_type == 'Polygon':
            oid,time_difference_m,relative_horizontal_error,relative_vertical_error = process_polygon_feature(feature, area_gdf)
        oid_of_matching_feature.append(oid)
        time_difference.append(time_difference_m)
        relative_horizontal_errors.append(relative_horizontal_error)
        relative_vertical_errors.append(relative_vertical_error)

    area_gdf['Time_Difference'] = time_difference
    area_gdf['Relative_Horizontal_Error'] = relative_horizontal_errors
    area_gdf['Relative_Vertical_Error'] = relative_vertical_errors
    area_gdf['oid_of_matching_feature'] = oid_of_matching_feature

    area_gdf['Time_Difference'] = area_gdf['Time_Difference'].round(3)
    area_gdf['Relative_Horizontal_Error'] = area_gdf['Relative_Horizontal_Error'].round(3)
    area_gdf['Relative_Vertical_Error'] = area_gdf['Relative_Vertical_Error'].round(3)

    # 输出新的geojson文件
    area_gdf.to_file(output_name, driver='GeoJSON')

def process_point_feature(feature, area_gdf):
    '''
    点要素横纵误差计算方法
    :param feature: 当前要素
    :param area_gdf: 对应的数据范围
    :return: oid：最近邻要素id
            time_difference_m：当前要素与最近邻要素的时间差（分钟为单位）
             horizontal_error：横向误差
             vertical_error：纵向误差
    '''
    point = feature.geometry
    nearby_features = extract_obs_subsets(area_gdf, point.coords[0])
    nearest_feature = find_neasrst_feature(feature,point,nearby_features)
    if nearest_feature is not None:
        time_difference = timestamp_2_BeijingStamp(feature.start_time) - timestamp_2_BeijingStamp(nearest_feature.start_time)
        time_difference_m = abs(time_difference.total_seconds() / 60)
        if time_difference_m > 20:
            horizontal_error, vertical_error = compute_errors(point, nearest_feature.geometry)
            # print(f'当前要素: {feature.oid}, 最近要素: {nearest_feature.oid}, 横向误差: {horizontal_error}, 纵向误差: {vertical_error}\n')
            return nearest_feature.oid, time_difference_m, horizontal_error, vertical_error
        else:
            time_difference_m = -1
            horizontal_error = -1
            vertical_error = -1
            oid = -1
            return oid, time_difference_m, horizontal_error, vertical_error
    else:
        time_difference_m = -1
        horizontal_error = -1
        vertical_error = -1
        oid = -1
        return oid, time_difference_m, horizontal_error, vertical_error


def process_linestring_feature(feature, area_gdf):
    '''
    线要素横纵误差计算方法
    :param feature: 当前要素
    :param area_gdf: 对应的数据范围
    :return: oid：最近邻要素id
            time_difference_m：当前要素与最近邻要素的时间差（分钟为单位）
             horizontal_error：横向误差
             vertical_error：纵向误差
    '''
    linestring = feature.geometry
    mid_point = linestring.interpolate(0.5, normalized=True)
    nearby_features = extract_obs_subsets(area_gdf, mid_point.coords[0])
    nearest_feature = find_neasrst_feature(feature,mid_point,nearby_features)
    if nearest_feature is not None:
        time_difference = timestamp_2_BeijingStamp(feature.start_time) - timestamp_2_BeijingStamp(nearest_feature.start_time)
        time_difference_m = abs(time_difference.total_seconds() / 60)
        if time_difference_m > 20:
            horizontal_error, vertical_error = compute_errors(mid_point, nearest_feature.geometry)
            # print(f'当前要素: {feature.oid}, 最近要素: {nearest_feature.oid}, 横向误差: {horizontal_error}, 纵向误差: {vertical_error}\n')
            return nearest_feature.oid, time_difference_m, horizontal_error,  vertical_error
        else:
            time_difference_m = -1
            horizontal_error = -1
            vertical_error = -1
            oid = -1
            return oid, time_difference_m, horizontal_error, vertical_error
    else:
        time_difference_m = -1
        horizontal_error = -1
        vertical_error = -1
        oid = -1
        return oid, time_difference_m, horizontal_error, vertical_error

def process_polygon_feature(feature, area_gdf):
    '''
    面要素横纵误差计算方法
    :param feature: 当前要素
    :param area_gdf: 对应的数据范围
    :return: oid：最近邻要素id
            time_difference_m：当前要素与最近邻要素的时间差（分钟为单位）
             horizontal_error：横向误差
             vertical_error：纵向误差
    '''
    polygon = feature.geometry
    min_rect = polygon.minimum_rotated_rectangle
    center_point = min_rect.centroid
    nearby_features = extract_obs_subsets(area_gdf, center_point.coords[0])
    nearest_feature = find_neasrst_feature(feature,center_point,nearby_features)
    if nearest_feature is not None:
        time_difference = timestamp_2_BeijingStamp(feature.start_time) - timestamp_2_BeijingStamp(nearest_feature.start_time)
        time_difference_m = abs(time_difference.total_seconds() / 60)
        if time_difference_m > 20:
            horizontal_error, vertical_error = compute_errors(center_point, nearest_feature.geometry)
            # print(f'当前要素: {feature.oid}, 最近要素: {nearest_feature.oid}, 横向误差: {horizontal_error}, 纵向误差: {vertical_error}\n')
            return nearest_feature.oid, time_difference_m, horizontal_error, vertical_error
        else:
            time_difference_m = -1
            horizontal_error = -1
            vertical_error = -1
            oid = -1
            return oid, time_difference_m, horizontal_error, vertical_error
    else:
        time_difference_m = -1
        horizontal_error = -1
        vertical_error = -1
        oid = -1
        return oid, time_difference_m, horizontal_error, vertical_error

if __name__ == '__main__':
    '''单文件处理方式'''
    # # 读取数据
    # start_time = time.time()
    # data_name_path = r'output_data/data_aday/group_2023-07-24.geojson'
    # output_name_path = r'output_data/errors_timeDifference/group_2023-07-24_with_errors_timeDifference.geojson'
    # area_gdf_724 = gpd.read_file(data_name_path,output_name_path)
    # end_time = time.time()
    # print(f'the loding time:{end_time - start_time:.3f}s\n')
    # # 数据处理
    # start_time = time.time()
    # calculate_re_ca(area_gdf_724)
    # end_time = time.time()
    # print(f'the calculating time:{end_time-start_time:.3f}s\n')
    '''单文件处理方式'''

    '''多文件处理方式'''
    start_time = time.time()
    input_names = os.listdir(data_path)
    for input_name in tqdm(input_names):
        if input_name.endswith('.geojson'):
            input_name_path = os.path.join(data_path,input_name)
            area_gdf = gpd.read_file(input_name_path)
            output_name = os.path.splitext(input_name)[0]
            output_name_path = os.path.join(output_path,output_name + '_errors_timeDifference.geojson')
            calculate_re_ca(area_gdf,output_name_path)
    end_time = time.time()
    print(f'the calculating time:{end_time - start_time:.3f}s\n')
    '''多文件处理方式'''